import importlib
import unittest


class BackendServerTests(unittest.TestCase):
    def test_server_factory_binds_only_to_loopback(self):
        try:
            app = importlib.import_module("app")
        except ModuleNotFoundError:
            app = None
        self.assertIsNotNone(app, "app.create_server is not implemented")
        server = app.create_server(host="127.0.0.1", port=0)
        try:
            self.assertEqual(server.server_address[0], "127.0.0.1")
        finally:
            server.server_close()

    def test_server_factory_rejects_non_loopback_and_cli_port_is_configurable(self):
        app = importlib.import_module("app")
        with self.assertRaises(ValueError):
            app.create_server(host="0.0.0.0", port=0)
        with self.assertRaises(ValueError):
            app.create_server(host="127.0.0.1", port=65536)
        self.assertEqual(app.parse_args([]).port, 8765)
        self.assertEqual(app.parse_args(["--port", "43210"]).port, 43210)
        import io
        from contextlib import redirect_stderr
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                app.parse_args(["--port", "0"])

    def test_status_exposes_only_local_unconfigured_services(self):
        app = importlib.import_module("app")
        server = app.create_server(port=0)
        thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = __import__("http.client", fromlist=["HTTPConnection"]).HTTPConnection(
                "127.0.0.1", server.server_port, timeout=3
            )
            connection.request("GET", "/api/status", headers={"Host": f"127.0.0.1:{server.server_port}"})
            response = connection.getresponse()
            payload = response.read()
            self.assertEqual(response.status, 200)
            body = __import__("json").loads(payload.decode("utf-8"))
            self.assertEqual(body["mode"], "local_prototype")
            self.assertEqual(body["ai"]["connected"], False)
            self.assertEqual(body["ai"]["status"], "not_configured")
            self.assertEqual(body["catalogue"]["publication_ready"], 0)
            self.assertEqual(body["storage"], "local_snapshot_not_postgresql")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive(), "test HTTP server did not stop")


class CatalogueApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading
        cls.app = importlib.import_module("app")
        cls.server = cls.app.create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        if cls.thread.is_alive():
            raise AssertionError("test HTTP server did not stop")

    def request(self, path):
        import http.client
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request("GET", path, headers={"Host": f"127.0.0.1:{self.server.server_port}"})
        response = connection.getresponse()
        payload = response.read()
        status = response.status
        headers = response.headers
        connection.close()
        return status, headers, payload

    def test_catalogue_returns_only_whitelisted_internal_metadata(self):
        status, headers, payload = self.request("/api/catalogue")
        body_text = payload.decode("utf-8")
        body = __import__("json").loads(body_text)
        self.assertEqual(status, 200)
        self.assertEqual(body["count"], 20)
        self.assertEqual(len(body["items"]), 20)
        self.assertTrue(body["not_for_publication"])
        product = body["items"][0]
        self.assertEqual(set(product), {
            "id", "name", "family", "issuer", "isin", "identity_state",
            "primary_url", "as_of", "publication_ready", "conditions_state",
            "conflicts", "unknown_fields",
        })
        self.assertTrue(all(item["publication_ready"] is False for item in body["items"]))
        self.assertTrue(all(item["conditions_state"] == "pending" for item in body["items"]))
        self.assertNotIn("available_fields", body_text)
        self.assertNotIn("promo_tae", body_text)
        self.assertNotIn("2,50 %", body_text)
        self.assertNotIn("NAV publicado", body_text)

    def test_catalogue_filters_are_closed_and_product_lookup_is_exact(self):
        status, headers, payload = self.request("/api/catalogue?family=etf_ucits")
        self.assertEqual(status, 200)
        family_body = __import__("json").loads(payload.decode("utf-8"))
        self.assertEqual(family_body["count"], 4)
        self.assertTrue(all(item["family"] == "etf_ucits" for item in family_body["items"]))
        status, headers, payload = self.request("/api/products/ACC-01")
        self.assertEqual(status, 200)
        self.assertEqual(__import__("json").loads(payload.decode("utf-8"))["product"]["id"], "ACC-01")
        status, headers, payload = self.request("/api/products/%2e%2e%2fACC-01")
        self.assertEqual(status, 404)
        status, headers, payload = self.request("/api/catalogue?family=etf_ucits&family=deposito")
        self.assertEqual(status, 400)
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_snapshot_returns_defensive_copies_without_mutating_source(self):
        import hashlib
        app = importlib.import_module("app")
        source = app.SNAPSHOT_PATH.read_bytes()
        before = hashlib.sha256(source).digest()
        repository = app.SnapshotRepository()
        product = repository.get_product("ACC-02")
        original_name = product["name"]
        product["name"] = "changed in caller"
        product["unknown_fields"].append("caller mutation")
        fresh = repository.get_product("ACC-02")
        self.assertEqual(fresh["name"], original_name)
        self.assertNotIn("caller mutation", fresh["unknown_fields"])
        self.assertEqual(hashlib.sha256(app.SNAPSHOT_PATH.read_bytes()).digest(), before)

    def test_root_serves_only_local_html_css_js_and_svg_assets(self):
        status, headers, payload = self.request("/")
        self.assertEqual(status, 200)
        html = payload.decode("utf-8")
        self.assertIn('src="./app.js"', html)
        self.assertIn('href="./styles.css"', html)
        self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
        self.assertNotIn("'unsafe-inline'", headers["Content-Security-Policy"])
        for path, content_type in [
            ("/app.js", "javascript"),
            ("/styles.css", "text/css"),
            ("/assets/pai-mark.svg", "image/svg+xml"),
        ]:
            status, asset_headers, asset = self.request(path)
            self.assertEqual(status, 200, path)
            self.assertIn(content_type, asset_headers["Content-Type"])
            self.assertTrue(asset)

    def test_static_traversal_never_reads_project_files(self):
        for path in (
            "/static/%2e%2e/CONTRATO-LOCAL.md",
            "/static/%2e%2e%5cCONTRATO-LOCAL.md",
        ):
            with self.subTest(path=path):
                status, headers, payload = self.request(path)
                self.assertEqual(status, 404)
                self.assertNotIn(b"Contrato local", payload)
                self.assertNotIn("Access-Control-Allow-Origin", headers)


class PostApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading
        cls.app = importlib.import_module("app")
        cls.server = cls.app.create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        if cls.thread.is_alive():
            raise AssertionError("test HTTP server did not stop")

    def request_json(self, path, document, extra_headers=None):
        import http.client
        import json
        port = self.server.server_port
        headers = {
            "Host": f"127.0.0.1:{port}",
            "Origin": f"http://127.0.0.1:{port}",
            "Content-Type": "application/json; charset=utf-8",
        }
        if extra_headers:
            headers.update(extra_headers)
        body = json.dumps(document, ensure_ascii=False).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.request("POST", path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        status = response.status
        response_headers = response.headers
        connection.close()
        return status, response_headers, payload

    def request_raw(self, path, raw_body, extra_headers=None, method="POST"):
        import http.client
        port = self.server.server_port
        headers = {
            "Host": f"127.0.0.1:{port}",
            "Origin": f"http://127.0.0.1:{port}",
            "Content-Type": "application/json; charset=utf-8",
        }
        if extra_headers:
            headers.update(extra_headers)
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.request(method, path, body=raw_body, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        status = response.status
        response_headers = response.headers
        connection.close()
        return status, response_headers, payload

    def request_without_content_length(self, path):
        import http.client
        port = self.server.server_port
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.putrequest("POST", path, skip_host=True, skip_accept_encoding=True)
        connection.putheader("Host", f"127.0.0.1:{port}")
        connection.putheader("Origin", f"http://127.0.0.1:{port}")
        connection.putheader("Content-Type", "application/json")
        connection.endheaders()
        response = connection.getresponse()
        payload = response.read()
        status = response.status
        response_headers = response.headers
        connection.close()
        return status, response_headers, payload

    def test_requires_explicit_content_length_for_post(self):
        status, headers, payload = self.request_without_content_length("/api/compare")
        self.assertEqual(status, 411)
        self.assertEqual(__import__("json").loads(payload.decode("utf-8"))["error"]["code"], "CONTENT_LENGTH_REQUIRED")
        import http.client
        port = self.server.server_port
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.putrequest("POST", "/api/compare", skip_host=True, skip_accept_encoding=True)
        connection.putheader("Host", f"127.0.0.1:{port}")
        connection.putheader("Origin", f"http://127.0.0.1:{port}")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", "2")
        connection.putheader("Content-Length", "2")
        connection.endheaders(b"{}")
        response = connection.getresponse()
        payload = response.read()
        self.assertEqual(response.status, 411)
        connection.close()

    def test_compare_is_read_only_and_never_claims_quantitative_readiness(self):
        status, headers, payload = self.request_json(
            "/api/compare", {"product_ids": ["ACC-01", "ACC-02"]}
        )
        body_text = payload.decode("utf-8")
        self.assertEqual(status, 200)
        body = __import__("json").loads(body_text)
        self.assertEqual(body["comparison_kind"], "educational_metadata_only")
        self.assertFalse(body["quantitative_ready"])
        self.assertFalse(body["hypothetical"])
        self.assertEqual([item["id"] for item in body["items"]], ["ACC-01", "ACC-02"])
        self.assertTrue(body["reasons"])
        self.assertNotIn("2,50 %", body_text)
        self.assertNotIn("rank", body_text.casefold())
        status, headers, payload = self.request_json(
            "/api/compare", {"product_ids": ["ACC-01", "DEBT-01"]}
        )
        self.assertEqual(status, 200)
        mixed = __import__("json").loads(payload.decode("utf-8"))
        self.assertTrue(any("distinta naturaleza" in reason for reason in mixed["reasons"]))
        self.assertFalse(mixed["quantitative_ready"])

    def test_rejects_cross_origin_requests_with_security_headers_and_no_cors(self):
        status, headers, payload = self.request_raw(
            "/api/compare",
            b'{"product_ids":["ACC-01","ACC-02"]}',
            {"Origin": "https://example.invalid"},
        )
        body = __import__("json").loads(payload.decode("utf-8"))
        self.assertEqual(status, 403)
        self.assertEqual(body["error"]["code"], "ORIGIN_REJECTED")
        self.assertFalse(body["error"]["retryable"])
        self.assertEqual(len(body["error"]["request_id"]), 32)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
        self.assertNotIn("'unsafe-inline'", headers["Content-Security-Policy"])
        port = self.server.server_port
        for headers_override in (
            {"Origin": ""},
            {"Host": f"evil.example:{port}", "Origin": f"http://evil.example:{port}"},
        ):
            status, response_headers, payload = self.request_raw(
                "/api/compare", b'{"product_ids":["ACC-01","ACC-02"]}', headers_override
            )
            self.assertEqual(status, 403)
            self.assertEqual(__import__("json").loads(payload.decode("utf-8"))["error"]["code"], "ORIGIN_REJECTED")

    def test_rejects_non_json_nan_duplicate_and_oversized_bodies_without_echo_or_logs(self):
        import io
        from contextlib import redirect_stderr
        sentinel = b"BODY_SENTINEL_PRIVATE"
        captured = io.StringIO()
        with redirect_stderr(captured):
            status, headers, payload = self.request_raw(
                "/api/compare",
                b'{"product_ids":["ACC-01","ACC-02"],"value":NaN,"note":"BODY_SENTINEL_PRIVATE"}',
            )
        body_text = payload.decode("utf-8")
        body = __import__("json").loads(body_text)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "INVALID_JSON")
        self.assertNotIn(sentinel.decode("ascii"), body_text)
        self.assertNotIn(sentinel.decode("ascii"), captured.getvalue())
        for constant in (b"NaN", b"Infinity", b"-Infinity"):
            raw = b'{"product_ids":["ACC-01","ACC-02"],"value":' + constant + b"}"
            status, headers, payload = self.request_raw("/api/compare", raw)
            self.assertEqual(status, 400)
            self.assertEqual(__import__("json").loads(payload.decode("utf-8"))["error"]["code"], "INVALID_JSON")
        status, headers, payload = self.request_raw(
            "/api/calculate",
            b'{"principal":1e9999,"annual_rate_percent":"0","years":1,"monthly_contribution":"0","method":"simple","inflation_percent":"0"}',
        )
        self.assertEqual(status, 400)
        status, headers, payload = self.request_raw(
            "/api/compare", b'{"product_ids":["ACC-01","ACC-02"]}',
            {"Content-Type": "text/plain"},
        )
        self.assertEqual(status, 415)
        status, headers, payload = self.request_raw(
            "/api/compare", b"", {"Transfer-Encoding": "chunked"}
        )
        self.assertEqual(status, 400)
        status, headers, payload = self.request_raw(
            "/api/compare", b'{"product_ids":["ACC-01","ACC-02"],"product_ids":[]}',
        )
        self.assertEqual(status, 400)
        self.assertEqual(__import__("json").loads(payload.decode("utf-8"))["error"]["code"], "INVALID_JSON")
        deeply_nested = b'{"extra":' + b"[" * 1200 + b"0" + b"]" * 1200 + b"}"
        status, headers, payload = self.request_raw("/api/compare", deeply_nested)
        self.assertEqual(status, 400)
        status, headers, payload = self.request_raw("/api/compare", b" " * 16385)
        self.assertEqual(status, 413)

    def test_compare_rejects_extras_duplicates_and_unknown_candidates(self):
        status, headers, payload = self.request_json("/api/compare", {
            "product_ids": ["ACC-01", "ACC-02"], "extra": True,
        })
        self.assertEqual(status, 400)
        status, headers, payload = self.request_json("/api/compare", {
            "product_ids": ["ACC-01", "ACC-01"],
        })
        self.assertEqual(status, 400)
        status, headers, payload = self.request_json("/api/compare", {
            "product_ids": ["ACC-01", "FAKE-01"],
        })
        self.assertEqual(status, 404)
        status, headers, payload = self.request_json("/api/compare", {
            "product_ids": ["A" * 100, "ACC-01"],
        })
        self.assertEqual(status, 400)

    def test_calculate_rejects_unbounded_values_and_extra_fields(self):
        invalid_documents = [
            {"principal": "NaN", "annual_rate_percent": "0", "years": 1,
             "monthly_contribution": "0", "method": "simple", "inflation_percent": "0"},
            {"principal": "1", "annual_rate_percent": "-100", "years": 1,
             "monthly_contribution": "0", "method": "compound", "inflation_percent": "0"},
            {"principal": "1", "annual_rate_percent": "0", "years": True,
             "monthly_contribution": "0", "method": "compound", "inflation_percent": "0"},
            {"principal": "1", "annual_rate_percent": "0", "years": 1,
             "monthly_contribution": "0", "method": "compound", "inflation_percent": "0",
             "unexpected": "no"},
        ]
        for document in invalid_documents:
            with self.subTest(document=document):
                status, headers, payload = self.request_json("/api/calculate", document)
                self.assertEqual(status, 400)
                self.assertIn("error", __import__("json").loads(payload.decode("utf-8")))

    def test_chat_is_always_explicitly_unconfigured(self):
        status, headers, payload = self.request_json("/api/chat", {"message": "hola"})
        self.assertEqual(status, 503)
        body = __import__("json").loads(payload.decode("utf-8"))
        self.assertEqual(body["error"]["code"], "CHAT_NOT_CONFIGURED")
        self.assertFalse(body["error"]["retryable"])

    def test_context_preview_only_accepts_allowlisted_fixture_and_projects_selected_fields(self):
        fixture_request = {
            "synthetic_fixture": True,
            "fixture_id": "synthetic-full-profile-01",
            "purpose": "learn_basics",
            "selected_fields": ["objective"],
            "consent": {
                "notice_version": "synthetic-test-v1",
                "accepted_chat_processing": True,
                "purpose": "learn_basics",
                "approved_fields": ["objective"],
            },
        }
        status, headers, payload = self.request_json("/api/context-preview", fixture_request)
        self.assertEqual(status, 200)
        body = __import__("json").loads(payload.decode("utf-8"))
        self.assertFalse(body["external_sent"])
        self.assertEqual(body["projection"]["purpose"], "learn_basics")
        self.assertEqual(set(body["projection"]["fields"]), {"objective"})
        self.assertEqual(body["projection"]["fields"]["objective"]["state"], "known")
        unregistered = dict(fixture_request, fixture_id="unregistered-fixture")
        status, headers, payload = self.request_json("/api/context-preview", unregistered)
        self.assertEqual(status, 403)
        unflagged = dict(fixture_request, synthetic_fixture=False)
        status, headers, payload = self.request_json("/api/context-preview", unflagged)
        self.assertEqual(status, 400)
        real_profile = dict(fixture_request, profile={"income": "9000"})
        status, headers, payload = self.request_json("/api/context-preview", real_profile)
        self.assertEqual(status, 400)

    def test_only_declared_http_methods_are_available(self):
        status, headers, payload = self.request_raw("/api/status", b"", method="OPTIONS")
        self.assertEqual(status, 405)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertIn("error", __import__("json").loads(payload.decode("utf-8")))
        status, headers, payload = self.request_raw("/api/status", b"", method="DELETE")
        self.assertEqual(status, 405)
        status, headers, payload = self.request_raw("/api/status", b"", method="TRACE")
        self.assertEqual(status, 405)
        self.assertIn("error", __import__("json").loads(payload.decode("utf-8")))
        status, headers, payload = self.request_raw("/api/compare", b"", method="GET")
        self.assertEqual(status, 405)
        status, headers, payload = self.request_json("/api/status", {})
        self.assertEqual(status, 405)

    def test_calculate_returns_decimal_hypothetical_series(self):
        status, headers, payload = self.request_json("/api/calculate", {
            "principal": "1000.00",
            "annual_rate_percent": "12.00",
            "years": 1,
            "monthly_contribution": "100.00",
            "method": "compound",
            "inflation_percent": "2.00",
        })
        self.assertEqual(status, 200)
        body = __import__("json").loads(payload.decode("utf-8"))
        self.assertTrue(body["hypothetical"])
        self.assertTrue(body["not_prediction"])
        self.assertEqual(body["currency"], "EUR")
        self.assertEqual(body["summary"]["contributions"], "2200.00")
        self.assertEqual(body["summary"]["final_balance"], "2384.65")
        self.assertEqual(body["summary"]["inflation_adjusted"], "2337.89")
        self.assertEqual(body["series"][-1]["month"], 12)


if __name__ == "__main__":
    unittest.main()
