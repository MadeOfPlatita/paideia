"""HTTP integration tests. All provider replies and positive facts are TEST ONLY."""
import http.client
import json
import threading
import unittest
from contextlib import contextmanager
from datetime import date

import app
from conditions_service import ConditionsService


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
        # Fecha fija: la TAE de DEP-01 es promocional y caduca sola. Con la fecha
        # real del día la prueba cambiaría de resultado sin que cambie el código.
        service = ConditionsService(reference_date=date(2026, 11, 5))
        with running_server(conditions_service=service) as server:
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

    def test_expired_promotion_stops_being_comparable(self):
        """La misma pareja, pasada la vigencia, deja de ser comparable por sí sola.

        Es el comportamiento que se quiere: la app no presenta una tasa caducada
        como actual, y el motivo viaja en el diagnóstico.
        """
        service = ConditionsService(reference_date=date(2026, 11, 23))
        with running_server(conditions_service=service) as server:
            status, body = request(server, "/api/compare", {
                "product_ids": ["DEP-01", "DEP-02"], "criterion": "deposit_tae_12m_eur"})
        self.assertEqual(status, 200)
        self.assertFalse(body["quantitative_ready"])
        by_id = {item["product_id"]: item for item in body["comparability"]["items"]}
        self.assertIn("DATA_STALE", by_id["DEP-01"]["reason_codes"])
        self.assertFalse(by_id["DEP-01"]["eligible"])
        self.assertIsNone(by_id["DEP-01"]["value"])


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
                # CONTRATO DE REINTENTO (cambio medido). Un fallo de TRANSPORTE
                # (timeout) se reintenta UNA vez, porque la misma pregunta que
                # fallaba respondia al segundo intento en produccion. El resto de
                # errores (credencial, cupo, cuerpo invalido) NO se reintentan: no
                # son de red y repetirlos no arregla nada.
                if upstream == "timeout":
                    self.assertEqual(transport.calls, 2,
                                     "un timeout de transporte se reintenta una vez, no mas")
                else:
                    self.assertEqual(transport.calls, 1,
                                     f"el error {upstream} no debe reintentarse")

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


class InvalidResponseMessageTests(unittest.TestCase):
    """El aviso de forma inválida dice qué faltó, sin cuerpo ni campos internos.

    Transportes sintéticos, sin red. Todas estas rutas pasan por el proveedor
    real con un transporte cerrado de pruebas, así el error recorre el mismo
    camino que en producción (copia del error, diagnóstico y ServiceProblem).
    """

    CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
               "purpose": "free_chat", "approved_fields": []}
    KEY = "TEST_ONLY_NOT_A_SECRET"

    def _service(self, body, status=200):
        from backend_services import LocalChatService
        from providers import GroqProvider, TransportResponse
        class TestOnlyShapeTransport:
            test_only = True
            def __init__(self):
                self.calls = 0
            def post(self, **kwargs):
                self.calls += 1
                return TransportResponse(status, body)
        transport = TestOnlyShapeTransport()
        provider = GroqProvider(transport, opt_in=True, environment={"GROQ_API_KEY": self.KEY})
        from test_functional05_http import make_gate
        return LocalChatService(provider=provider, enabled=True, admission=make_gate()), transport

    def _chat(self, body, status=200):
        service, transport = self._service(body, status)
        with running_server(chat_service=service) as server:
            result = request(server, "/api/chat", {"message": "Pregunta sintética", "consent": self.CONSENT})
        return result, transport

    def test_message_names_what_was_missing_for_each_shape(self):
        cases = (
            (b'{"choices": [{"finish_reason": "stop"}]}', "ningún mensaje del asistente"),
            (json.dumps({"choices": [{"message": {"role": "assistant", "content": None},
                                      "finish_reason": "stop"}]}).encode(),
             "vacío, sin texto ni llamadas"),
            (b'{"choices": []}', "exactamente una opción"),
            (b"no-json", "JSON válido"),
        )
        for body, expected_fragment in cases:
            with self.subTest(fragment=expected_fragment):
                (status, payload), transport = self._chat(body)
                self.assertEqual(status, 502)
                self.assertEqual(payload["error"]["code"], "CHAT_INVALID_RESPONSE")
                message = payload["error"]["message"]
                self.assertIn(expected_fragment, message)
                self.assertIn("(HTTP 200)", message)
                self.assertIn("no hay reintento automático", message)
                self.assertFalse(payload["error"]["retryable"])
                self.assertEqual(transport.calls, 1)

    def test_message_never_repeats_the_provider_body_or_internal_field_names(self):
        from backend_services import INVALID_RESPONSE_REASONS
        private = "PRIVATE_PROVIDER_BODY_MUST_NOT_LEAK"
        bodies = (
            b"Error interno del proveedor: " + private.encode(),
            json.dumps({"choices": [{"message": {"role": "assistant", "content": None,
                       "reasoning": private}, "finish_reason": "length"}]}).encode(),
            json.dumps({"choices": [{"message": {"role": "assistant", "content": "x",
                       "campo_raro": private}, "finish_reason": "stop"}]}).encode(),
            json.dumps({"choices": [{"message": {"role": "assistant", "content": None,
                       "tool_calls": [{"id": "call_1", "type": "function",
                                       "function": {"name": "x", "arguments": private}}]},
                       "finish_reason": "tool_calls"}]}).encode(),
        )
        for body in bodies:
            with self.subTest(body=body[:40]):
                (status, payload), transport = self._chat(body)
                self.assertEqual(status, 502)
                encoded = json.dumps(payload)
                self.assertNotIn(private, encoded)
                self.assertNotIn(self.KEY, encoded)
                for internal in ("response_shape", "choices", "tool_calls", "reasoning_details",
                                 "finish_reason", "unknown_field", "empty_message"):
                    self.assertNotIn(internal, payload["error"]["message"])
                self.assertTrue(payload["error"]["message"].startswith(
                    "No se pudo usar la respuesta del proveedor IA (HTTP 200):"))
                self.assertEqual(transport.calls, 1)

    def test_every_declared_shape_has_a_spanish_reason_and_a_fallback_exists(self):
        from backend_services import INVALID_RESPONSE_REASONS, _invalid_response_message
        from providers import ProviderError, RESPONSE_SHAPES
        self.assertEqual(set(INVALID_RESPONSE_REASONS), set(RESPONSE_SHAPES))
        for shape, reason in INVALID_RESPONSE_REASONS.items():
            with self.subTest(shape=shape):
                self.assertTrue(reason.strip())
                self.assertIs(reason, reason.strip())
                error = ProviderError("invalid_response")
                error.response_shape = shape
                message = _invalid_response_message(error, 200)
                self.assertIn(reason, message)
                self.assertIn("(HTTP 200)", message)
                self.assertIn("no hay reintento automático", message)
        # Sin forma conocida (o con una inventada) el aviso sigue siendo seguro.
        for shape in (None, "shape_inventada", 42):
            error = ProviderError("invalid_response")
            error.response_shape = shape
            message = _invalid_response_message(error)
            self.assertIn("no tenía la forma esperada", message)
            self.assertIn("no hay reintento automático", message)
            self.assertNotIn("HTTP", message)

    def test_other_provider_errors_keep_their_own_message(self):
        # Un 401 no debe recibir el texto de forma inválida.
        (status, payload), transport = self._chat(b"", status=401)
        self.assertEqual(status, 503)
        self.assertEqual(payload["error"]["code"], "CHAT_AUTH_UNAVAILABLE")
        self.assertNotIn("forma", payload["error"]["message"])
        self.assertEqual(transport.calls, 1)

    def test_a_healthy_answer_still_returns_200_and_is_not_retried(self):
        body = json.dumps({"choices": [{"message": {"role": "assistant",
            "content": "TEST ONLY: respuesta sintética."}, "finish_reason": "stop"}]}).encode()
        (status, payload), transport = self._chat(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["answer"], "TEST ONLY: respuesta sintética.")
        self.assertEqual(transport.calls, 1)

    def test_the_counted_transport_path_keeps_the_shape_and_the_safe_notice(self):
        """Ruta real de producción: `_CountedTransport` + transporte HTTPS, sin red."""
        import socket
        import threading
        from types import SimpleNamespace
        from unittest.mock import patch

        import providers
        from backend_services import _invalid_response_message
        from secure_groq_session import _CountedTransport

        for body, expected_shape in ((b'{"choices": []}', "no_choices"),
                                     (b'{"choices": [{"finish_reason": "stop"}]}', "no_message"),
                                     (b"not-json", "not_json")):
            with self.subTest(shape=expected_shape):
                class TestOnlyConnection:
                    status = 200
                    def __init__(self, *args, **kwargs): pass
                    def connect(self): pass
                    def request(self, *args, **kwargs): pass
                    def getresponse(self): return self
                    def read(self, limit): return body
                    def close(self): pass

                session = SimpleNamespace(
                    _lock=threading.RLock(), _state='active', _calls=0, _mission_budget=None,
                    _check=lambda **kwargs: True, _stop=threading.Event())
                transport = _CountedTransport(
                    session, False, providers.GroqHTTPSJSONTransport())
                provider = providers.GroqProvider(
                    transport, opt_in=True, environment={"GROQ_API_KEY": self.KEY})
                with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), \
                     patch.object(providers.http.client, 'HTTPSConnection', TestOnlyConnection):
                    with self.assertRaises(providers.ProviderError) as caught:
                        provider.chat([{"role": "user", "content": "Pregunta sintética."}])

                error = caught.exception
                self.assertEqual(error.code, "invalid_response")
                self.assertEqual(error.response_shape, expected_shape)
                self.assertEqual(error.send_state.value, "completed")
                message = _invalid_response_message(error)
                self.assertNotIn(self.KEY, message)
                self.assertIn("no hay reintento automático", message)

    def test_the_admitted_tools_path_reports_the_same_reason(self):
        """Producción usa la ruta con herramientas y admisión: mismo aviso, un envío."""
        import app
        from backend_services import CatalogueComparisonService, LocalChatService
        from pai_tools import ToolDispatcher
        from providers import GroqProvider, TransportResponse
        from test_functional05_http import make_gate

        class TestOnlyShapeTransport:
            test_only = True
            def __init__(self):
                self.calls = 0
            def post(self, **kwargs):
                self.calls += 1
                return TransportResponse(200, b'{"choices": [{"finish_reason": "stop"}]}')

        transport = TestOnlyShapeTransport()
        provider = GroqProvider(transport, opt_in=True, environment={"GROQ_API_KEY": self.KEY})
        service = LocalChatService(
            provider=provider, enabled=True, admission=make_gate(),
            dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()),
            tools_enabled=True, catalogue_usage_approved=True)
        with running_server(chat_service=service) as server:
            status, payload = request(server, "/api/chat",
                {"message": "Pregunta sintética", "consent": self.CONSENT})
        self.assertEqual(status, 502)
        self.assertEqual(payload["error"]["code"], "CHAT_INVALID_RESPONSE")
        self.assertIn("ningún mensaje del asistente", payload["error"]["message"])
        self.assertIn("no hay reintento automático", payload["error"]["message"])
        self.assertNotIn(self.KEY, json.dumps(payload))
        self.assertEqual(transport.calls, 1)


if __name__ == "__main__":
    unittest.main()
