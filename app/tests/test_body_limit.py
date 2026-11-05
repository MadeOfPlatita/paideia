"""El rechazo por cuerpo demasiado grande debe llegar como JSON legible.

Antes, el servidor respondia 413 sin consumir el cuerpo: el cliente recibia un
corte de conexion (`ConnectionAbortedError`) en vez del error, porque el socket
se cerraba con megabytes sin leer. Esta prueba fija el contrato.
"""

import importlib
import json
import os
import threading
import unittest
from http.client import HTTPConnection
from unittest import mock

CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
           "purpose": "free_chat", "approved_fields": []}


class BodyLimitTests(unittest.TestCase):
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

    def _post(self, cuerpo):
        conexion = HTTPConnection("127.0.0.1", self.server.server_port, timeout=15)
        try:
            conexion.request(
                "POST", "/api/chat", body=cuerpo,
                headers={"Content-Type": "application/json",
                         "Origin": f"http://127.0.0.1:{self.server.server_port}"})
            respuesta = conexion.getresponse()
            cabeceras = {clave.lower(): valor for clave, valor in respuesta.getheaders()}
            return respuesta.status, respuesta.read(), cabeceras
        finally:
            conexion.close()

    def test_large_body_returns_a_readable_json_error(self):
        cuerpo = json.dumps({"message": "x" * (2 * 1024 * 1024), "consent": CONSENT}).encode()
        estado, datos, cabeceras = self._post(cuerpo)
        self.assertEqual(estado, 413)
        self.assertEqual(cabeceras.get("connection"), "close")
        carga = json.loads(datos)
        self.assertEqual(carga["error"]["code"], "BODY_TOO_LARGE")

    def test_small_body_is_not_affected(self):
        cuerpo = json.dumps({"message": "hola", "consent": CONSENT}).encode()
        estado, datos, _ = self._post(cuerpo)
        self.assertIn(estado, (200, 503))
        self.assertTrue(datos)


if __name__ == "__main__":
    unittest.main()
