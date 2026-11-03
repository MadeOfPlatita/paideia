"""TEST ONLY: offline replay through real HTTP; no external provider."""
import unittest
import app
from backend_services import LocalChatService, CatalogueComparisonService
from pai_tools import ToolDispatcher
from providers import ChatResult, ToolCall
from test_backend_integration import running_server, request
from test_functional05_http import make_gate, CONSENT
from test_pai_runtime import scenario_arguments
from test_functional05_http import TestOnlyFakeProvider

REAL_REPLAY = 'Ahorrar significa conservar dinero sin riesgo de perder el capital, mientras que invertir implica usar esos fondos en activos que pueden generar rendimientos pero también conllevan riesgo de pérdida. La inflación reduce el valor real del dinero ahorrado, porque los precios suben y el poder de compra de ese capital disminuye con el tiempo.'

class FinancialQualityIntegration(unittest.TestCase):
    def test_real_replay_never_reaches_http_and_slot_released(self):
        for mode in ('plain', 'admitted', 'tools'):
            with self.subTest(mode=mode):
                provider = TestOnlyFakeProvider([ChatResult(REAL_REPLAY, None, (), 'stop')])
                gate = make_gate() if mode != 'plain' else None
                service = LocalChatService(provider=provider, enabled=True, test_only=True,
                    admission=gate, tools_enabled=mode == 'tools',
                    dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()) if mode == 'tools' else None)
                with running_server(chat_service=service) as server:
                    status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
                self.assertEqual(status, 502)
                self.assertEqual(body['error']['code'], 'CHAT_FINANCIAL_QUALITY_REJECTED')
                self.assertNotIn(REAL_REPLAY, str(body))
                self.assertEqual(len(provider.requests), 1)
                if gate: self.assertEqual(gate.status()['active'], 0)

    def test_safe_and_refusal_visible_in_all_modes(self):
        safe = 'TEST ONLY: Ahorrar puede tener riesgos; la inflación afecta al poder adquisitivo.'
        for mode in ('plain', 'admitted', 'tools'):
            for refusal in (False, True):
                with self.subTest(mode=mode, refusal=refusal):
                    provider = TestOnlyFakeProvider([ChatResult('' if refusal else safe, None, (), 'stop', refusal=safe if refusal else None)])
                    gate = make_gate() if mode != 'plain' else None
                    service = LocalChatService(provider=provider, enabled=True, test_only=True, admission=gate,
                        tools_enabled=mode == 'tools', dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()) if mode == 'tools' else None)
                    with running_server(chat_service=service) as server:
                        status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
                    self.assertEqual(status, 200)
                    self.assertEqual(body['answer'], safe)
                    self.assertEqual(body['refused'], refusal)
                    self.assertEqual(len(provider.requests), 1)
                    if gate: self.assertEqual(gate.status()['active'], 0)

    def test_unsafe_refusal_rejected_in_all_modes(self):
        for mode in ('plain', 'admitted', 'tools'):
            with self.subTest(mode=mode):
                provider = TestOnlyFakeProvider([ChatResult('', None, (), 'stop', refusal=REAL_REPLAY)])
                gate = make_gate() if mode != 'plain' else None
                service = LocalChatService(provider=provider, enabled=True, test_only=True, admission=gate,
                    tools_enabled=mode == 'tools', dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()) if mode == 'tools' else None)
                with running_server(chat_service=service) as server:
                    status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
                self.assertEqual((status, body['error']['code']), (502, 'CHAT_FINANCIAL_QUALITY_REJECTED'))
                self.assertNotIn(REAL_REPLAY, str(body))
                self.assertEqual(len(provider.requests), 1)
                if gate: self.assertEqual(gate.status()['active'], 0)

    def test_tool_followup_unsafe_final_rejected_without_extra_dispatch(self):
        provider = TestOnlyFakeProvider([
            ChatResult('', None, (ToolCall('test-call', 'calculate_scenario', scenario_arguments()),), 'tool_calls'),
            ChatResult(REAL_REPLAY, None, (), 'stop')])
        gate = make_gate()
        service = LocalChatService(provider=provider, enabled=True, test_only=True, admission=gate,
            tools_enabled=True, dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()))
        with running_server(chat_service=service) as server:
            status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
        self.assertEqual((status, body['error']['code']), (502, 'CHAT_FINANCIAL_QUALITY_REJECTED'))
        self.assertNotIn(REAL_REPLAY, str(body))
        self.assertEqual(len(provider.requests), 2)
        self.assertEqual(gate.status()['active'], 0)
        self.assertEqual(gate.status()['calls_day'], 2)
