"""Cupos de llamadas configurables, acotados y con valor por defecto seguro."""

import importlib
import os
import unittest
from unittest import mock


class CallLimitTests(unittest.TestCase):
    def setUp(self):
        self.pai = importlib.import_module("pai_setup")

    def entorno(self, **valores):
        limpio = {k: v for k, v in os.environ.items()
                  if k not in {"PAIDEIA_CALLS_PER_MINUTE", "PAIDEIA_CALLS_PER_DAY"}}
        limpio.update(valores)
        return mock.patch.dict(os.environ, limpio, clear=True)

    def test_defaults(self):
        with self.entorno():
            self.assertEqual(self.pai._calls_per_minute(), 6)
            self.assertEqual(self.pai._calls_per_day(), 60)

    def test_reads_the_environment(self):
        with self.entorno(PAIDEIA_CALLS_PER_MINUTE="20", PAIDEIA_CALLS_PER_DAY="400"):
            self.assertEqual(self.pai._calls_per_minute(), 20)
            self.assertEqual(self.pai._calls_per_day(), 400)

    def test_rejects_garbage_and_negatives(self):
        for valor in ("abc", "0", "-5", "", "3.5"):
            with self.subTest(valor=valor):
                with self.entorno(PAIDEIA_CALLS_PER_DAY=valor):
                    self.assertEqual(self.pai._calls_per_day(), 60, valor)

    def test_absurd_values_are_capped(self):
        with self.entorno(PAIDEIA_CALLS_PER_MINUTE="9999", PAIDEIA_CALLS_PER_DAY="999999"):
            self.assertEqual(self.pai._calls_per_minute(), 60)
            self.assertEqual(self.pai._calls_per_day(), 5000)

    def test_status_reports_the_configured_quota(self):
        app = importlib.import_module("app")
        import http.client
        import json
        import threading
        with self.entorno(PAIDEIA_CALLS_PER_DAY="400", PAIDEIA_GROQ_ENABLED="1", GROQ_API_KEY="clave-de-prueba"):
            server = app.create_server(port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conexion = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conexion.request("GET", "/api/status",
                                 headers={"Host": f"127.0.0.1:{server.server_port}"})
                cuerpo = json.loads(conexion.getresponse().read().decode("utf-8"))
                conexion.close()
                self.assertEqual(cuerpo["ai"]["quota"]["calls_per_day"], 400)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
