"""La comparación adjunta las condiciones documentadas de cada candidato.

Antes devolvía solo metadatos y el estado quedaba en «pending»: la biblioteca y
la comparación parecían vacías aunque la ficha tuviera condiciones con fuente.
"""

import importlib
import json
import os
import threading
import unittest
from http.client import HTTPConnection
from unittest import mock


class CompareConditionsTests(unittest.TestCase):
    def setUp(self):
        self.app = importlib.import_module("app")
        self.patch = mock.patch.dict(os.environ, {"PAIDEIA_GROQ_ENABLED": "0"})
        self.patch.start()
        self.server = self.app.create_server(port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.patch.stop()

    def compare(self, ids):
        conexion = HTTPConnection("127.0.0.1", self.server.server_port, timeout=20)
        try:
            conexion.request(
                "POST", "/api/compare",
                body=json.dumps({"product_ids": ids}),
                headers={"Content-Type": "application/json",
                         "Origin": f"http://127.0.0.1:{self.server.server_port}"})
            respuesta = conexion.getresponse()
            return respuesta.status, json.loads(respuesta.read())
        finally:
            conexion.close()

    def test_items_carry_documented_conditions_and_state(self):
        estado, datos = self.compare(["DEP-01", "ETF-01"])
        self.assertEqual(estado, 200)
        por_id = {item["id"]: item for item in datos["items"]}
        self.assertEqual(por_id["DEP-01"]["conditions_state"], "documented")
        self.assertTrue(por_id["DEP-01"]["conditions"], "DEP-01 debe llevar sus condiciones")
        self.assertTrue(any(c.get("metric") == "annual_rate_percent"
                            for c in por_id["DEP-01"]["conditions"]))
        self.assertIn(por_id["ETF-01"]["conditions_state"], {"documented", "partial"})

    def test_comparison_stays_educational_for_mixed_families(self):
        estado, datos = self.compare(["DEP-01", "ETF-01"])
        self.assertEqual(estado, 200)
        self.assertFalse(datos["quantitative_ready"])
        self.assertEqual(datos["comparison_kind"], "educational_metadata_only")
        self.assertTrue(datos["reasons"])


if __name__ == "__main__":
    unittest.main()
