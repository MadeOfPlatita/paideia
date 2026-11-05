"""Origen declarado para un despliegue público (detrás de un proxy HTTPS).

Sin `PAIDEIA_PUBLIC_ORIGIN` la app sigue siendo solo local: escucha en 127.0.0.1
y rechaza cualquier otro Host u Origin. Con la variable, se acepta exactamente el
origen declarado y nada más.
"""

import importlib
import json
import os
import threading
import unittest
from http.client import HTTPConnection
from unittest import mock

PUBLIC = "https://paideia-demo.onrender.com"


class DeclaredOriginTests(unittest.TestCase):
    def setUp(self):
        self.app = importlib.import_module("app")
        self.patch = mock.patch.dict(os.environ, {"PAIDEIA_PUBLIC_ORIGIN": PUBLIC})
        self.patch.start()
        self.server = self.app.create_server(port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.patch.stop()
        self.assertFalse(self.thread.is_alive(), "el servidor de prueba no se detuvo")

    def request(self, headers):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(
                "POST", "/api/compare",
                body=json.dumps({"product_ids": ["ACC-01", "ACC-02"]}),
                headers={"Content-Type": "application/json; charset=utf-8", **headers},
            )
            response = connection.getresponse()
            return response.status, json.loads(response.read().decode("utf-8"))
        finally:
            connection.close()

    def test_accepts_the_declared_https_origin(self):
        status, body = self.request({"Host": "paideia-demo.onrender.com", "Origin": PUBLIC})
        self.assertEqual(status, 200, body)

    def test_rejects_a_different_origin(self):
        for origin in ("https://evil.example", "http://paideia-demo.onrender.com",
                       PUBLIC + "/path", PUBLIC + "?x=1", "null"):
            with self.subTest(origin=origin):
                status, body = self.request({"Host": "paideia-demo.onrender.com", "Origin": origin})
                self.assertEqual(status, 403)
                self.assertEqual(body["error"]["code"], "ORIGIN_REJECTED")

    def test_rejects_a_different_host(self):
        status, body = self.request({"Host": "evil.example", "Origin": PUBLIC})
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "ORIGIN_REJECTED")

    def test_rejects_missing_or_duplicated_origin(self):
        status, body = self.request({"Host": "paideia-demo.onrender.com"})
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "ORIGIN_REJECTED")

    def test_render_supplied_url_acts_as_declared_origin(self):
        with mock.patch.dict(os.environ, {"PAIDEIA_PUBLIC_ORIGIN": "", "RENDER_EXTERNAL_URL": PUBLIC}):
            status, body = self.request({"Host": "paideia-demo.onrender.com", "Origin": PUBLIC})
            self.assertEqual(status, 200, body)


class BindRulesTests(unittest.TestCase):
    def test_without_declared_origin_only_loopback_is_allowed(self):
        app = importlib.import_module("app")
        with mock.patch.dict(os.environ, {"PAIDEIA_PUBLIC_ORIGIN": ""}):
            with self.assertRaises(ValueError):
                app.create_server(host="0.0.0.0", port=0)
            server = app.create_server(host="127.0.0.1", port=0)
            server.server_close()

    def test_with_declared_origin_public_bind_is_allowed(self):
        app = importlib.import_module("app")
        with mock.patch.dict(os.environ, {"PAIDEIA_PUBLIC_ORIGIN": PUBLIC}):
            server = app.create_server(host="0.0.0.0", port=0)
            server.server_close()

    def test_main_binds_loopback_when_only_port_is_set(self):
        app = importlib.import_module("app")
        capturado = {}

        class Falso:
            server_port = 0
            def serve_forever(self): raise KeyboardInterrupt
            def server_close(self): pass

        def fake_create(host="127.0.0.1", port=8765, **kwargs):
            capturado["host"] = host
            return Falso()

        with mock.patch.dict(os.environ, {"PAIDEIA_PUBLIC_ORIGIN": "", "RENDER_EXTERNAL_URL": "", "PORT": "9001"}):
            with mock.patch.object(app, "create_server", fake_create):
                app.main([])
        self.assertEqual(capturado["host"], "127.0.0.1")

    def test_local_request_still_works_without_the_variable(self):
        app = importlib.import_module("app")
        with mock.patch.dict(os.environ, {"PAIDEIA_PUBLIC_ORIGIN": ""}):
            server = app.create_server(port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                connection.request(
                    "POST", "/api/compare",
                    body=json.dumps({"product_ids": ["ACC-01", "ACC-02"]}),
                    headers={"Content-Type": "application/json; charset=utf-8",
                             "Host": f"127.0.0.1:{server.server_port}",
                             "Origin": f"http://127.0.0.1:{server.server_port}"},
                )
                self.assertEqual(connection.getresponse().status, 200)
                connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
