"""Fichas de productos curados y conflictos reales: paridad local/WSGI.

Dos defectos observados en la app real:

- `DEP-EBN-12` y `DEP-SELF-12` (los dos depósitos comparables a 12 meses) existen en
  `/api/conditions` y en el comparador, pero `/api/products/<id>` devuelve
  `product: null`: su ficha no existe. Un producto documentado no puede tener
  condiciones y carecer de ficha.
- Un conflicto documentado en el snapshot se sustituye por la frase genérica
  «Conflicto de fuentes o condiciones pendiente de revisión.», que oculta qué
  discrepa. El texto documentado es contenido del propio snapshot, no HTML.
"""

from __future__ import annotations

import http.client
import importlib.util
import io
import json
import threading
import unittest
from pathlib import Path

import app

ROOT = Path(__file__).resolve().parents[2]
CURATED_ONLY = ("DEP-EBN-12", "DEP-SELF-12")
CONFLICT_PRODUCT = "ACC-02"
CONFLICT_FRAGMENT = "1,25 %"


def _load_bundled_wsgi():
    source = ROOT / "api" / "index.py"
    spec = importlib.util.spec_from_file_location("curated_parity_wsgi", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _wsgi_get(module, path):
    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": path, "QUERY_STRING": "",
               "CONTENT_LENGTH": "0", "wsgi.input": io.BytesIO(b"")}
    captured = {}

    def start_response(status, headers):
        captured["status"] = status

    chunks = module.app(environ, start_response)
    return captured["status"], json.loads(b"".join(chunks).decode("utf-8"))


class CuratedProductRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port
        cls.wsgi = _load_bundled_wsgi()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def local_get(self, path):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()

    def test_curated_only_deposits_have_a_ficha_locally(self):
        for product_id in CURATED_ONLY:
            status, body = self.local_get(f"/api/products/{product_id}")
            self.assertEqual(status, 200, body)
            product = body.get("product")
            self.assertIsNotNone(product, f"{product_id} tiene condiciones pero no ficha")
            self.assertEqual(product["id"], product_id)
            self.assertTrue(product["name"])
            self.assertEqual(product["family"], "deposito")
            self.assertFalse(product["publication_ready"])
            self.assertTrue((product.get("primary_url") or "").startswith("https://"))

    def test_curated_only_deposits_have_a_ficha_in_wsgi(self):
        for product_id in CURATED_ONLY:
            status, body = _wsgi_get(self.wsgi, f"/api/products/{product_id}")
            self.assertEqual(status.split()[0], "200", body)
            product = body.get("product")
            self.assertIsNotNone(product, f"{product_id} sin ficha en la función pública")
            self.assertEqual(product["id"], product_id)
            self.assertTrue(product["name"])

    def test_local_and_wsgi_describe_the_same_curated_product(self):
        for product_id in CURATED_ONLY:
            _, local = self.local_get(f"/api/products/{product_id}")
            _, web = _wsgi_get(self.wsgi, f"/api/products/{product_id}")
            for key in ("id", "name", "family", "identity_state", "primary_url"):
                self.assertEqual(local["product"][key], web["product"][key], (product_id, key))

    def test_documented_conflict_is_not_replaced_by_a_placeholder(self):
        _, body = self.local_get(f"/api/products/{CONFLICT_PRODUCT}")
        conflicts = body["product"]["conflicts"]
        self.assertTrue(conflicts, "el conflicto documentado debe llegar a la ficha")
        joined = " ".join(conflicts)
        self.assertIn(CONFLICT_FRAGMENT, joined,
                      "la ficha debe decir qué discrepa, no una frase genérica")
        self.assertNotIn("pendiente de revisión.", joined.strip())

        _, web = _wsgi_get(self.wsgi, f"/api/products/{CONFLICT_PRODUCT}")
        self.assertEqual(web["product"]["conflicts"], conflicts,
                         "local y WSGI deben coincidir en el texto del conflicto")


if __name__ == "__main__":
    unittest.main()
