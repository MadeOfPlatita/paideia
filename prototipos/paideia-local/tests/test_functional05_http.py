"""Coordinator end-to-end tests: loopback HTTP and TEST ONLY upstream replies."""
import unittest
from datetime import datetime, timezone

import app
from backend_services import LocalChatService, CatalogueComparisonService
from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission
from pai_tools import ToolDispatcher
from providers import ChatResult, ToolCall
from test_backend_integration import running_server, request
from test_pai_runtime import scenario_arguments
from structured_provider_adapter import FakeChatProvider


def TestOnlyFakeProvider(outcomes):
    return FakeChatProvider(None, test_only=True, outcomes=tuple(outcomes))


CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
           "purpose": "free_chat", "approved_fields": []}


def make_gate(limit=10):
    policy = AdmissionPolicy(max_concurrent=1, max_queue=2, calls_per_minute=limit,
                             calls_per_day=limit, ticket_ttl_seconds=120,
                             claim_ttl_seconds=120, scope="TEST_ONLY_FUNCTIONAL05")
    return InterfazChatAdmission(policy, lambda: datetime.now(timezone.utc),
        budget_state=InMemoryBudgetState.new_empty(scope=policy.scope))


def calculation_provider():
    return TestOnlyFakeProvider([
        ChatResult("", "PRIVATE REASONING", (ToolCall("test-calc-1", "calculate_scenario", scenario_arguments()),), "tool_calls"),
        ChatResult("TEST ONLY: el motor devuelve 1030.00 EUR nominales.", "PRIVATE REASONING", (), "stop"),
    ])


class Functional05HttpTests(unittest.TestCase):
    def test_detail_comparison_and_all_identity_sources_work_through_http(self):
        repository = app.SnapshotRepository()
        ids = [product["id"] for product in repository.list_products()]
        for name, args in (("get_product_detail", {"product_id": "ACC-01"}),
                ("compare_products", {"product_ids": ["ACC-01", "ACC-02", "DEP-01", "DEP-02"], "criterion": None}),
                ("get_sources", {"product_ids": ids})):
            with self.subTest(tool=name):
                provider = TestOnlyFakeProvider([
                    ChatResult("", None, (ToolCall("test-read-1", name, args),), "tool_calls"),
                    ChatResult("TEST ONLY: fuentes de identidad, no condiciones de una oferta.", None, (), "stop")])
                service = LocalChatService(provider=provider, enabled=True, test_only=True,
                    dispatcher=ToolDispatcher(repository, CatalogueComparisonService()), tools_enabled=True, admission=make_gate())
                with running_server(chat_service=service) as server:
                    status, body = request(server, "/api/chat", {"message": "TEST ONLY: consulta", "consent": CONSENT})
                self.assertEqual(status, 200)
                self.assertEqual(len(provider.requests), 2)
                self.assertTrue(body["sources"])
                self.assertTrue(all(item["source"]["claim_scope"]=="product_identity_only" for item in body["sources"]))

    def test_admitted_provider_errors_preserve_rate_limit_and_timeout_codes(self):
        from providers import ProviderError
        for code, expected_status, expected_code in (("rate_limited",429,"CHAT_RATE_LIMITED"),("timeout",504,"CHAT_TIMEOUT")):
            with self.subTest(code=code):
                provider, gate = TestOnlyFakeProvider([ProviderError(code)]), make_gate()
                service = LocalChatService(provider=provider, enabled=True, test_only=True,
                    dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()), tools_enabled=True, admission=gate)
                with running_server(chat_service=service) as server:
                    status, body = request(server, "/api/chat", {"message": "TEST ONLY", "consent": CONSENT})
                self.assertEqual(status, expected_status)
                self.assertEqual(body["error"]["code"], expected_code)
                self.assertEqual(len(provider.requests),1)
                self.assertEqual(gate.status()["active"],0)
                self.assertEqual(gate.status()["calls_day"],1)

    def test_followup_budget_exhaustion_prevents_second_provider_call(self):
        provider, gate = calculation_provider(), make_gate(limit=1)
        service = LocalChatService(provider=provider, enabled=True, test_only=True,
            dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()), tools_enabled=True, admission=gate)
        with running_server(chat_service=service) as server:
            status, body = request(server, "/api/chat", {"message": "TEST ONLY: calcula", "consent": CONSENT})
        self.assertEqual(status, 429)
        self.assertEqual(body["error"]["code"], "CHAT_QUOTA_EXHAUSTED")
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(gate.status()["calls_day"], 1)
        self.assertEqual(gate.status()["active"], 0)
        self.assertNotIn("answer", body)

    def test_tools_never_bypass_missing_consent_or_missing_budget_state(self):
        provider = calculation_provider()
        gate = InterfazChatAdmission(None)
        service = LocalChatService(provider=provider, enabled=True, test_only=True,
            dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()), tools_enabled=True, admission=gate)
        with running_server(chat_service=service) as server:
            status, body = request(server, "/api/chat", {"message": "TEST ONLY"})
            self.assertEqual(status, 403)
            status, body = request(server, "/api/chat", {"message": "TEST ONLY", "consent": CONSENT})
            self.assertEqual(status, 503)
            self.assertEqual(body["error"]["code"], "CHAT_ADMISSION_UNAVAILABLE")
        self.assertEqual(provider.requests, [])

    def test_twenty_real_candidate_metadata_fit_provider_request_budget(self):
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("test-search-20", "search_products", {"query": "", "family": None, "limit": 20}),), "tool_calls"),
            ChatResult("TEST ONLY: he consultado el inventario, no ofertas verificadas.", None, (), "stop"),
        ])
        service = LocalChatService(provider=provider, enabled=True, test_only=True,
            dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()), tools_enabled=True, admission=make_gate())
        with running_server(chat_service=service) as server:
            status, body = request(server, "/api/chat", {"message": "TEST ONLY: muestra los candidatos", "consent": CONSENT})
        self.assertEqual(status, 200)
        self.assertEqual(len(provider.requests), 2)
        self.assertEqual(len(body["sources"]), 20)
        from providers import build_chat_request
        build_chat_request(provider.requests[-1], tools=provider.tools[-1])
        self.assertEqual(body["tool_events"][0]["state"], "executed")

    def test_external_plain_chat_also_requires_known_admission_budget(self):
        provider = TestOnlyFakeProvider([ChatResult("TEST ONLY", None, (), "stop")])
        service = LocalChatService(provider=provider, enabled=True)
        with running_server(chat_service=service) as server:
            status, body = request(server, "/api/chat", {"message": "TEST ONLY: pregunta", "consent": CONSENT})
        self.assertEqual(status, 503)
        self.assertEqual(body["error"]["code"], "CHAT_ADMISSION_UNAVAILABLE")
        self.assertEqual(provider.requests, [])

    def test_queued_http_turn_is_visible_and_resumes_without_storing_message(self):
        provider, gate = calculation_provider(), make_gate()
        occupied = gate.submit()["ticket"]
        self.assertEqual(gate.claim(occupied)["code"], "claimed")
        service = LocalChatService(provider=provider, enabled=True, test_only=True,
            dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()),
            tools_enabled=True, admission=gate)
        payload = {"message": "TEST ONLY: pregunta en cola", "consent": CONSENT}
        with running_server(chat_service=service) as server:
            status, body = request(server, "/api/chat", payload)
            self.assertEqual(status, 202)
            self.assertEqual(body["status"], "queued")
            self.assertFalse(body["external_sent"])
            ticket = body["queue"]["ticket"]
            self.assertEqual(body["queue"]["position"], 1)
            self.assertEqual(provider.requests, [])
            status, body = request(server, "/api/chat-status", {"ticket": ticket})
            self.assertEqual(status, 200)
            self.assertEqual(body["queue"]["code"], "queued")
            self.assertNotIn(payload["message"], str(body))
            gate.complete(occupied)
            status, body = request(server, "/api/chat", {**payload, "ticket": ticket})
            self.assertEqual(status, 200)
            self.assertEqual(len(provider.requests), 2)
            self.assertEqual(gate.status()["active"], 0)
            status, body = request(server, "/api/chat", {**payload, "ticket": ticket})
            self.assertEqual(status, 409)
            self.assertEqual(len(provider.requests), 2)

    def test_external_tools_require_separate_catalogue_usage_approval(self):
        provider, gate = calculation_provider(), make_gate()
        dispatcher = ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService())
        service = LocalChatService(provider=provider, enabled=True, dispatcher=dispatcher,
                                   tools_enabled=True, admission=gate)
        with running_server(chat_service=service) as server:
            status, body = request(server, "/api/chat", {"message": "TEST ONLY: pregunta", "consent": CONSENT})
        self.assertEqual(status, 503)
        self.assertEqual(body["error"]["code"], "CHAT_TOOLS_NOT_APPROVED")
        self.assertEqual(provider.requests, [])
        self.assertEqual(gate.status()["calls_day"], 0)

    def test_http_tool_roundtrip_reserves_each_upstream_and_releases_slot(self):
        provider, gate = calculation_provider(), make_gate()
        dispatcher = ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService())
        service = LocalChatService(provider=provider, enabled=True, test_only=True,
                                   dispatcher=dispatcher, tools_enabled=True, admission=gate)
        with running_server(chat_service=service) as server:
            status, body = request(server, "/api/chat", {"message": "TEST ONLY: calcula un escenario", "consent": CONSENT})
        self.assertEqual(status, 200)
        self.assertEqual(body["provider_mode"], "test_only")
        self.assertFalse(body["external_sent"])
        self.assertEqual(body["tool_events"][0]["name"], "calculate_scenario")
        self.assertEqual(body["tool_events"][0]["state"], "executed")
        self.assertIn("1030.00", provider.requests[-1][-1]["content"])
        self.assertTrue(provider.tools[0])
        from providers import build_chat_request
        build_chat_request(provider.requests[-1], tools=provider.tools[-1])
        self.assertEqual(len(provider.requests), 2)
        self.assertNotIn("PRIVATE REASONING", str(body))
        self.assertEqual(gate.status()["calls_day"], 2)
        self.assertEqual(gate.status()["active"], 0)


if __name__ == "__main__":
    unittest.main()
