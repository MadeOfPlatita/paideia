"""B6: paridad de mensajes y diagnóstico entre el servidor local y el WSGI empaquetado."""

from __future__ import annotations

import http.client
import importlib.util
import io
import json
import sys
import threading
import unittest
from pathlib import Path

import app

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_REASONS = [
    "Candidatos internos no publicables; solo se comparan metadatos de identidad y fuente.",
    "Las familias tienen distinta naturaleza; no se ordenan numéricamente.",
    "Persisten conflictos o campos desconocidos pendientes de revisión.",
]


def _load_bundled_wsgi():
    source = ROOT / "api" / "index.py"
    spec = importlib.util.spec_from_file_location("b6_bundled_index", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _wsgi_post(module, path, payload):
    body = json.dumps(payload).encode("utf-8")
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": io.BytesIO(body),
    }
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    chunks = module.app(environ, start_response)
    return captured["status"], json.loads(b"".join(chunks).decode("utf-8"))


class CompareParityTests(unittest.TestCase):
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
        cls.thread.join(timeout=5)

    def local_post(self, path, payload):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            connection.request(
                "POST",
                path,
                body=json.dumps(payload),
                headers={"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{self.port}"},
            )
            response = connection.getresponse()
            return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()

    def test_metadata_reasons_and_items_match(self):
        payload = {"product_ids": ["ACC-01", "DEP-02", "DEP-SELF-12"]}
        local_status, local = self.local_post("/api/compare", payload)
        wsgi_status, wsgi = _wsgi_post(self.wsgi, "/api/compare", payload)
        self.assertEqual(local_status, 200)
        self.assertEqual(wsgi_status, "200 OK")
        self.assertEqual(local["reasons"], wsgi["reasons"])
        self.assertEqual(local["reasons"], EXPECTED_REASONS)
        self.assertEqual(
            [(item["id"], item["name"], item["as_of"]) for item in local["items"]],
            [(item["id"], item["name"], item["as_of"]) for item in wsgi["items"]],
        )
        self.assertFalse(local["quantitative_ready"])
        self.assertFalse(wsgi["quantitative_ready"])

    def test_quantitative_diagnosis_matches(self):
        payload = {"product_ids": ["DEP-EBN-12", "DEP-SELF-12"], "criterion": "deposit_tae_12m_eur"}
        local_status, local = self.local_post("/api/compare", payload)
        wsgi_status, wsgi = _wsgi_post(self.wsgi, "/api/compare", payload)
        self.assertEqual(local_status, 200)
        self.assertEqual(wsgi_status, "200 OK")
        self.assertEqual(local["reasons"], wsgi["reasons"])
        self.assertEqual(local["comparability"], wsgi["comparability"])
        self.assertTrue(local["quantitative_ready"])
        self.assertEqual(local["comparison_kind"], "quantitative_metric_only")


if __name__ == "__main__":
    unittest.main()
