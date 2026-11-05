"""HTTP integration tests. All provider replies and positive facts are TEST ONLY."""
import http.client
import json
import threading
import unittest
from contextlib import contextmanager

import app


@contextmanager
def running_server(**options):
    server = app.create_server(port=0, **options)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        if thread.is_alive():
            raise AssertionError("HTTP test server did not stop")


def request(server, path, payload=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    headers = {"Origin": f"http://127.0.0.1:{server.server_port}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    try:
        connection.request("GET" if payload is None else "POST", path,
                           body=None if payload is None else json.dumps(payload).encode(), headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


class SnapshotGrowthTests(unittest.TestCase):
    def test_twenty_is_a_first_milestone_not_a_repository_ceiling(self):
        import os
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        candidates = [{"candidate_id": f"SYN-{i:02d}", "name_literal": f"TEST ONLY candidate {i}",
                       "family": "deposito", "candidate_state": "proposed",
                       "primary_url": "https://example.invalid/test-only"} for i in range(1, 22)]
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR") or None) as directory:
            snapshot = Path(directory) / "test-only-candidates.json"
            snapshot.write_text(json.dumps({"candidates": candidates}), encoding="utf-8")
            with patch.object(app, "PROJECT_ROOT", Path(directory)), patch.object(app, "SNAPSHOT_PATH", snapshot):
                try:
                    repository = app.SnapshotRepository()
                except RuntimeError as error:
                    self.fail("A valid expanded test inventory must load: " + str(error))
            self.assertEqual(repository.count, 21)
            with running_server(repository=repository) as server:
                status, body = request(server, "/api/catalogue")
            self.assertEqual(status, 200)
            self.assertEqual(body["count"], 21)
            self.assertTrue(all(not product["publication_ready"] for product in body["items"]))


class ComparabilityHttpTests(unittest.TestCase):
    def test_http_cannot_upload_facts_or_override_server_freshness_policy(self):
        with running_server() as server:
            for extra in ({"facts": []}, {"policy": {"max_retrieval_age": None}},
                          {"allow_synthetic": True}, {"criterion": {"field": "arbitrary"}}):
                status, body = request(server, "/api/compare", {
                    "product_ids": ["DEP-01", "DEP-02"], "criterion": "deposit_tae_12m_eur", **extra})
                self.assertEqual(status, 400)
                self.assertEqual(body["error"]["code"], "INVALID_REQUEST")

    def test_http_display_does_not_inherit_transform_permission(self):
        from backend_services import CatalogueComparisonService
        from test_catalogue_facts import synthetic_fact, deposit_policy, AS_OF
        facts = tuple(synthetic_fact(pid, "3.10") for pid in ("SYN-01", "SYN-02"))
        service = CatalogueComparisonService(facts=facts, policy=deposit_policy(permission_action="app_display"),
                                             allow_synthetic=True, clock=lambda: AS_OF)
        dto = service.compare([{"id": pid, "family": "deposito"} for pid in ("SYN-01", "SYN-02")],
                              "deposit_tae_12m_eur")
        self.assertFalse(dto["quantitative_ready"])
        self.assertTrue(all(item["value"] is None and "RIGHTS_UNRESOLVED" in item["reason_codes"] for item in dto["items"]))

    def test_unconfigured_policy_is_not_reported_as_a_missing_known_metric(self):
        from backend_services import CatalogueComparisonService
        from test_catalogue_facts import synthetic_fact
        facts = tuple(synthetic_fact(pid, "3.10") for pid in ("SYN-01", "SYN-02"))
        service = CatalogueComparisonService(facts=facts, allow_synthetic=True)
        dto = service.compare([{"id": pid, "family": "deposito"} for pid in ("SYN-01", "SYN-02")],
                              "deposit_tae_12m_eur")
        self.assertFalse(dto["quantitative_ready"])
        for item in dto["items"]:
            self.assertIsNone(item["value"])
            self.assertIn("FRESHNESS_POLICY_NOT_CONFIGURED", item["reason_codes"])
            self.assertNotIn("METRIC_MISSING", item["reason_codes"])

    def test_default_compare_exposes_missing_facts_without_approving_freshness_policy(self):
        with running_server() as server:
            status, body = request(server, "/api/compare", {
                "product_ids": ["DEP-01", "DEP-02"], "criterion": "deposit_tae_12m_eur"})
        self.assertEqual(status, 200)
        self.assertFalse(body["quantitative_ready"])
        diagnosis = body["comparability"]
        self.assertEqual(diagnosis["criterion"], "deposit_tae_12m_eur")
        self.assertFalse(diagnosis["quantitative_ready"])
        self.assertIsNone(diagnosis["policy_version"])
        self.assertEqual(diagnosis["basis"], "documented_conditions")
        self.assertTrue(diagnosis["not_for_publication"])
        by_id = {item["product_id"]: item for item in diagnosis["items"]}
        # DEP-01 documenta 3,24 % TAE a 12 meses desde su página oficial; DEP-02
        # documenta tasa, pero a 6 meses y el criterio exige 12.
        self.assertEqual(by_id["DEP-01"]["reason_codes"], [])
        self.assertTrue(by_id["DEP-01"]["eligible"])
        self.assertEqual(by_id["DEP-01"]["value"], "3.24")
        self.assertIn("PERIOD_MISMATCH", by_id["DEP-02"]["reason_codes"])
        self.assertIsNone(by_id["DEP-02"]["value"])


    def test_criterion_cannot_relabel_repository_family_as_a_deposit(self):
        from backend_services import CatalogueComparisonService
        from test_catalogue_facts import synthetic_fact, deposit_policy, AS_OF
        facts = tuple(synthetic_fact(pid, "3.10", permissions_by_action={"app_display": "allowed"})
                      for pid in ("SYN-01", "SYN-02"))
        service = CatalogueComparisonService(facts=facts, policy=deposit_policy(permission_action="app_display"),
                                             allow_synthetic=True, clock=lambda: AS_OF)
        for products in ([{"id": pid, "family": "etf_ucits"} for pid in ("SYN-01", "SYN-02")],
                         [{"id": "SYN-01", "family": "deposito"}, {"id": "SYN-02", "family": "etf_ucits"}]):
            dto = service.compare(products, "deposit_tae_12m_eur")
            self.assertFalse(dto["quantitative_ready"])
            self.assertIsNone(dto["items"][-1]["value"])
            self.assertIn("FAMILY_MISMATCH", dto["items"][-1]["reason_codes"])

    def test_synthetic_facts_are_excluded_without_explicit_test_mode(self):
        from backend_services import CatalogueComparisonService
        from test_catalogue_facts import synthetic_fact, deposit_policy, AS_OF
        facts = tuple(synthetic_fact(pid, "3.10", permissions_by_action={"app_display": "allowed"})
                      for pid in ("SYN-01", "SYN-02"))
        service = CatalogueComparisonService(facts=facts, policy=deposit_policy(permission_action="app_display"),
                                             clock=lambda: AS_OF)
        dto = service.compare([{"id": pid, "family": "deposito"} for pid in ("SYN-01", "SYN-02")],
                              "deposit_tae_12m_eur")
        self.assertFalse(dto["quantitative_ready"])
        self.assertTrue(all(item["value"] is None for item in dto["items"]))
        self.assertTrue(all("SYNTHETIC_FACT_REJECTED" in item["reason_codes"] for item in dto["items"]))

    def test_http_evaluates_only_explicit_server_side_synthetic_facts(self):
        from backend_services import CatalogueComparisonService
        from test_catalogue_facts import synthetic_fact, deposit_policy, AS_OF
        import copy

        class TestOnlyRepository(app.CatalogueRepository):
            count = 2
            def get_product(self, product_id):
                if product_id not in {"SYN-01", "SYN-02"}:
                    return None
                return copy.deepcopy({"id": product_id, "name": "TEST ONLY " + product_id,
                    "family": "deposito", "conflicts": [], "unknown_fields": [],
                    "publication_ready": False, "identity_state": "synthetic_test"})

        facts = tuple(synthetic_fact(pid, value, permissions_by_action={"app_display": "allowed"})
                      for pid, value in (("SYN-01", "3.10"), ("SYN-02", "3.25")))
        service = CatalogueComparisonService(facts=facts, policy=deposit_policy(permission_action="app_display"),
                                             allow_synthetic=True, clock=lambda: AS_OF)
        with running_server(repository=TestOnlyRepository(), comparison_service=service) as server:
            status, body = request(server, "/api/compare", {
                "product_ids": ["SYN-01", "SYN-02"], "criterion": "deposit_tae_12m_eur"})
        self.assertEqual(status, 200)
        self.assertTrue(body["quantitative_ready"])
        self.assertTrue(body["hypothetical"])
        self.assertEqual(body["comparison_kind"], "test_only_quantitative")
        self.assertTrue(body["comparability"]["not_for_publication"])
        self.assertEqual([item["value"] for item in body["comparability"]["items"]], ["3.10", "3.25"])
        self.assertTrue(all(item["source_refs"] for item in body["comparability"]["items"]))
        self.assertEqual(body["comparability"]["policy_version"], "test-only-freshness-v1")


class ChatHttpTests(unittest.TestCase):
    def test_client_cannot_override_context_provider_or_consent_scope(self):
        from backend_services import LocalChatService
        from structured_provider_adapter import FakeChatProvider
        from providers import ChatResult
        provider = FakeChatProvider(ChatResult('TEST ONLY', None, (), 'stop'), test_only=True)
        consent = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
                   "purpose": "free_chat", "approved_fields": []}
        with running_server(chat_service=LocalChatService(provider=provider, enabled=True, test_only=True)) as server:
            for extra in ({"profile": {"income": "TEST ONLY"}}, {"messages": []}, {"tools": []},
                          {"model": "arbitrary"}, {"system": "TEST ONLY"}, {"enabled": True}):
                status, body = request(server, "/api/chat", {"message": "Pregunta sintética", "consent": consent, **extra})
                self.assertEqual(status, 400)
            for update in ({"accepted_chat_processing": False}, {"accepted_chat_processing": 1},
                           {"notice_version": "outdated"}, {"approved_fields": ["monthly_income_eur"]},
                           {"purpose": "product_comparison"}, {"unexpected": True}):
                status, body = request(server, "/api/chat", {"message": "Pregunta sintética", "consent": {**consent, **update}})
                self.assertEqual(status, 403)
                self.assertEqual(body["error"]["code"], "CHAT_CONSENT_REQUIRED")
        self.assertEqual(provider.calls, 0)

    def test_chat_preserves_refusal_and_output_truncation_without_reasoning(self):
        from backend_services import LocalChatService
        from providers import ChatResult
        from structured_provider_adapter import FakeChatProvider
        consent = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
                   "purpose": "free_chat", "approved_fields": []}
        for result, answer, refused, truncated in (
            (ChatResult("TEST ONLY: salida incompleta", "PRIVATE REASONING", (), "length"),
             "TEST ONLY: salida incompleta", False, True),
            (ChatResult("", "PRIVATE REASONING", (), "stop", "TEST ONLY: rechazo del proveedor"),
             "TEST ONLY: rechazo del proveedor", True, False)):
            with self.subTest(refused=refused):
                with running_server(chat_service=LocalChatService(provider=FakeChatProvider(result, test_only=True), enabled=True, test_only=True)) as server:
                    status, body = request(server, "/api/chat", {"message": "Pregunta sintética", "consent": consent})
                self.assertEqual(status, 200)
                self.assertEqual(body["answer"], answer)
                self.assertEqual(body.get("refused"), refused)
                self.assertEqual(body.get("truncated"), truncated)
                self.assertNotIn("PRIVATE REASONING", json.dumps(body))

    def test_unsolicited_tools_are_rejected_without_execution_or_followup(self):
        from backend_services import LocalChatService
        from providers import GroqProvider, TransportResponse
        class TestOnlyToolTransport:
            test_only = True
            calls = 0
            def post(self, **kwargs):
                self.calls += 1
                return TransportResponse(200, json.dumps({"choices": [{"message": {"role": "assistant",
                    "content": None, "tool_calls": [{"id": "test-call-1", "type": "function", "function": {
                    "name": "execute_sql", "arguments": '{"sql":"TEST ONLY: MUST NOT EXECUTE"}'}}]},
                    "finish_reason": "tool_calls"}]}).encode())
        transport = TestOnlyToolTransport()
        provider = GroqProvider(transport, opt_in=True, environment={"GROQ_API_KEY": "TEST_ONLY_NOT_A_SECRET"})
        consent = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
                   "purpose": "free_chat", "approved_fields": []}
        from test_functional05_http import make_gate
        with running_server(chat_service=LocalChatService(provider=provider, enabled=True, admission=make_gate())) as server:
            status, body = request(server, "/api/chat", {"message": "Pregunta sintética", "consent": consent})
        self.assertEqual(status, 502)
        self.assertEqual(body["error"]["code"], "CHAT_TOOL_CALL_REJECTED")
        self.assertEqual(transport.calls, 1)
        self.assertNotIn("answer", body)
        self.assertNotIn("execute_sql", json.dumps(body))

    def test_provider_errors_have_safe_http_codes_and_no_retries(self):
        from backend_services import LocalChatService
        from providers import GroqProvider, TransportResponse
        class TestOnlyErrorTransport:
            test_only = True
            def __init__(self, status):
                self.status, self.calls = status, 0
            def post(self, **kwargs):
                self.calls += 1
                if self.status == "timeout":
                    raise TimeoutError("TEST_ONLY_PRIVATE_INTERNAL_EXCEPTION")
                return TransportResponse(self.status, b"TEST_ONLY_PRIVATE_PROVIDER_BODY")
        consent = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
                   "purpose": "free_chat", "approved_fields": []}
        for upstream, expected_status, expected_code in ((401, 503, "CHAT_AUTH_UNAVAILABLE"),
                (429, 429, "CHAT_RATE_LIMITED"), (503, 503, "CHAT_PROVIDER_UNAVAILABLE"),
                (200, 502, "CHAT_INVALID_RESPONSE"), ("timeout", 504, "CHAT_TIMEOUT")):
            with self.subTest(upstream=upstream):
                transport = TestOnlyErrorTransport(upstream)
                provider = GroqProvider(transport, opt_in=True, environment={"GROQ_API_KEY": "TEST_ONLY_NOT_A_SECRET"})
                from test_functional05_http import make_gate
                with running_server(chat_service=LocalChatService(provider=provider, enabled=True, admission=make_gate())) as server:
                    status, body = request(server, "/api/chat", {"message": "Pregunta sintética", "consent": consent})
                self.assertEqual(status, expected_status)
                self.assertEqual(body["error"]["code"], expected_code)
                self.assertFalse(body["error"]["retryable"])
                self.assertNotIn("TEST_ONLY_PRIVATE", json.dumps(body))
                self.assertEqual(transport.calls, 1)

    def test_enabled_adapter_roundtrip_requires_separate_remote_consent(self):
        from backend_services import LocalChatService
        from structured_provider_adapter import FakeChatProvider
        from providers import ChatResult, build_chat_request
        provider = FakeChatProvider(ChatResult("TEST ONLY: respuesta sintética.",
            "TEST ONLY: razonamiento privado no exponible", (), "stop"), test_only=True)
        service = LocalChatService(provider=provider, enabled=True, test_only=True)
        consent = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
                   "purpose": "free_chat", "approved_fields": []}
        with running_server(chat_service=service) as server:
            status, body = request(server, "/api/chat", {"message": "Pregunta sintética"})
            self.assertEqual(status, 403)
            self.assertEqual(body["error"]["code"], "CHAT_CONSENT_REQUIRED")
            self.assertEqual(provider.requests, [])
            status, body = request(server, "/api/chat", {"message": "Pregunta sintética", "consent": consent})
            self.assertEqual(status, 200)
            self.assertEqual(body["answer"], "TEST ONLY: respuesta sintética.")
            self.assertEqual(body["provider_mode"], "test_only")
            self.assertFalse(body["external_sent"])
            self.assertNotIn("reasoning", json.dumps(body))
            self.assertEqual(len(provider.requests), 1)
            self.assertEqual([message["role"] for message in provider.requests[0]], ["system", "user"])
            self.assertEqual(provider.requests[0][-1]["content"], "Pregunta sintética")
            self.assertEqual(provider.tools, [None])
            build_chat_request(provider.requests[0])
            status, body = request(server, "/api/status")
            self.assertFalse(body["ai"]["connected"])
            self.assertEqual(body["ai"]["status"], "test_only")


if __name__ == "__main__":
    unittest.main()
