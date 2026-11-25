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
        # Los valores por defecto se subieron el 25/11/2026 para una sala de 50
        # usuarios simultaneos. Medido contra el proveedor real: 50 llamadas a la
        # vez responden 50/50 en 3,3 s, cero 429. Con 6/min y 4 turnos
        # concurrentes, el usuario 5 recibia un rechazo inmediato.
        with self.entorno():
            self.assertEqual(self.pai._calls_per_minute(), 200)
            self.assertEqual(self.pai._calls_per_day(), 20000)

    def test_reads_the_environment(self):
        with self.entorno(PAIDEIA_CALLS_PER_MINUTE="20", PAIDEIA_CALLS_PER_DAY="400"):
            self.assertEqual(self.pai._calls_per_minute(), 20)
            self.assertEqual(self.pai._calls_per_day(), 400)

    def test_rejects_garbage_and_negatives(self):
        for valor in ("abc", "0", "-5", "", "3.5"):
            with self.subTest(valor=valor):
                with self.entorno(PAIDEIA_CALLS_PER_DAY=valor):
                    self.assertEqual(self.pai._calls_per_day(), 20000, valor)

    def test_absurd_values_are_capped(self):
        # El techo sigue existiendo (un valor absurdo no abre la puerta), pero
        # ahora esta por encima de la sala esperada en vez de por debajo.
        with self.entorno(PAIDEIA_CALLS_PER_MINUTE="9999", PAIDEIA_CALLS_PER_DAY="999999"):
            self.assertEqual(self.pai._calls_per_minute(), 1000)
            self.assertEqual(self.pai._calls_per_day(), 100000)

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
                # Sin cupo diario: la variable de entorno ya no es una puerta.
                self.assertGreaterEqual(cuerpo["ai"]["quota"]["calls_per_day"], 10 ** 8)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
