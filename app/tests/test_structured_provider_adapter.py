import json
import unittest
from providers import ChatResult

class AdapterTests(unittest.TestCase):
    def test_pure_parser_projects_raw_result_and_rejects_adversarial_results(self):
        import structured_provider_adapter as adapter
        from providers import ProviderError, ToolCall
        valid = '{"version":"paideia-education-v1","intent":"explain","claim_ids":["inflation"]}'
        expected = json.loads(valid)
        self.assertEqual(adapter.parse_selection(ChatResult(valid, 'ignored', (), 'stop')), expected)
        bad = [object(), ChatResult(valid, object(), (), 'stop'), ChatResult(valid, 'x' * 32769, (), 'stop'),
               ChatResult(valid, None, (), 'length'), ChatResult(valid, None, (), 'stop', 'refused'),
               ChatResult(valid, None, (ToolCall('id', 'tool', {}),), 'stop'),
               ChatResult(valid.replace('"intent":"explain"', '"intent":"explain","intent":"calculate"'), None, (), 'stop'),
               ChatResult(valid.replace('"inflation"', '"inflation","inflation"'), None, (), 'stop'),
               ChatResult(valid.replace('inflation', 'unknown'), None, (), 'stop'),
               ChatResult(valid[:-1] + ',"answer":"forged"}', None, (), 'stop'),
               ChatResult(valid + ' trailing', None, (), 'stop'), ChatResult('\ud800', None, (), 'stop')]
        for raw in bad:
            with self.subTest(raw=repr(raw)), self.assertRaises(ProviderError) as error:
                adapter.parse_selection(raw)
            self.assertEqual(error.exception.code, 'invalid_response')

    def test_closed_sequence_records_tools_and_provider_errors(self):
        from providers import ProviderError
        from structured_provider_adapter import FakeChatProvider
        first = ChatResult('first', None, (), 'stop')
        fake = FakeChatProvider(None, test_only=True, outcomes=(first, ProviderError('timeout')))
        messages = [{'role': 'user', 'content': 'synthetic'}]
        self.assertIs(fake.chat(messages, tools=[]), first)
        with self.assertRaises(ProviderError) as error:
            fake.chat(messages, tools=None)
        self.assertEqual(error.exception.code, 'timeout')
        self.assertEqual(fake.calls, 2)
        self.assertEqual(fake.requests, [messages, messages])
        self.assertEqual(fake.tools, [[], None])
        with self.assertRaises(ProviderError):
            fake.chat(messages)

    def test_closed_sequence_rejects_arbitrary_outcomes(self):
        from structured_provider_adapter import FakeChatProvider
        for outcomes in ([], (), (lambda: None,), (object(),), (ChatResult('x', None, (), 'stop'),) * 33):
            with self.subTest(outcomes=outcomes), self.assertRaises(ValueError):
                FakeChatProvider(None, test_only=True, outcomes=outcomes)


    def test_closed_sequence_rejects_unsafe_nested_values(self):
        from providers import ToolCall
        from structured_provider_adapter import FakeChatProvider
        for response in (ChatResult(object(), None, (), 'stop'),
                         ChatResult('', None, (ToolCall('x', 'tool', {'x': object()}),), 'tool_calls')):
            with self.subTest(response=response), self.assertRaises(ValueError):
                FakeChatProvider(None, test_only=True, outcomes=(response,))

    def test_fixture_rechecks_mutated_data_before_dispatch(self):
        from providers import ToolCall, ProviderError
        from structured_provider_adapter import FakeChatProvider
        args = {'x': 'safe'}
        fake = FakeChatProvider(None, test_only=True, outcomes=(ChatResult('', None, (ToolCall('i', 'n', args),), 'tool_calls'),))
        args['x'] = object()
        with self.assertRaises(ProviderError): fake.chat([{'role':'user','content':'test'}])
        single = FakeChatProvider(ChatResult(object(), None, (), 'stop'), test_only=True)
        with self.assertRaises(ProviderError): single.chat([{'role':'user','content':'test'}])

    def test_browser_fixture_modes_are_closed_and_synthetic_only(self):
        from structured_provider_adapter import FakeChatProvider, BrowserFixture
        from providers import ProviderError
        m = lambda text: [{'role': 'user', 'content': text}]
        context = FakeChatProvider(None, test_only=True, browser=BrowserFixture.CONTEXT)
        self.assertIn('respuesta sintética', context.chat(m('SYNTHETIC TEST ONLY: context')).answer)
        with self.assertRaises(ProviderError): context.chat(m('non synthetic'))
        quality = FakeChatProvider(None, test_only=True, browser=BrowserFixture.QUALITY)
        self.assertIn('sin riesgo', quality.chat(m('SYNTHETIC TEST ONLY: unsafe')).answer)
        self.assertIn('No es posible', quality.chat(m('SYNTHETIC TEST ONLY: prefix-denial')).answer)
        self.assertIn('inflación', quality.chat(m('SYNTHETIC TEST ONLY: safe')).answer)
        with self.assertRaises(ValueError): FakeChatProvider(None, test_only=True, browser='quality')

    def test_browser_scenario_runs_actual_tool_and_respects_admission(self):
        import app
        from backend_services import LocalChatService, CatalogueComparisonService
        from pai_tools import ToolDispatcher
        from structured_provider_adapter import FakeChatProvider, BrowserFixture
        from test_functional05_http import CONSENT, make_gate
        fake = FakeChatProvider(None, test_only=True, browser=BrowserFixture.SCENARIO)
        gate = make_gate()
        service = LocalChatService(provider=fake, enabled=True, test_only=True, admission=gate,
                                   tools_enabled=True, dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()))
        response = service.chat({'message':'SYNTHETIC TEST ONLY: calculate', 'consent':CONSENT})
        # La prosa con cifras no se publica, pero la frase inocua que la acompaña sí:
        # el cliente recibe el resultado determinista y no la atribución dudosa.
        self.assertTrue(response['answer'].strip())
        self.assertNotIn('1030', response['answer'])
        self.assertEqual(response['answer_text_state'], 'shown_unverified')
        self.assertEqual(response['calculation']['summary']['final_balance'], '1030.00')
        self.assertEqual(response['calculation']['assumptions']['principal'], '1000.00')
        self.assertEqual(response['tool_events'][0]['state'], 'executed')
        self.assertEqual(fake.calls, 2)
        self.assertEqual(gate.status()['calls_day'], 2)
        self.assertIn('1030.00', fake.requests[1][-1]['content'])
        self.assertTrue(fake.tools[0])

    def test_arbitrary_test_only_network_like_provider_rejected_before_invocation(self):
        import socket
        from unittest.mock import patch
        from backend_services import LocalChatService
        class ArbitraryNetworkLike:
            test_only = True
            def select_education(self, messages):
                socket.socket().connect(('127.0.0.1', 9))
        provider = ArbitraryNetworkLike()
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network')) as connect:
            with self.assertRaises(ValueError):
                LocalChatService(provider=provider, enabled=True, test_only=True, structured_mode=True)
            connect.assert_not_called()

    def test_exact_types_and_pinned_methods_prevent_dynamic_dispatch(self):
        import socket
        from unittest.mock import patch
        from backend_services import LocalChatService, ServiceProblem
        from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
        from test_structured_education import CONSENT
        class FakeSubclass(FakeChatProvider):
            pass
        class AdapterSubclass(StructuredProviderAdapter):
            pass
        valid = json.dumps({'version':'paideia-education-v1','intent':'explain','claim_ids':['inflation']})
        fake = FakeChatProvider(ChatResult(valid, None, (), 'stop'), test_only=True)
        adapter = StructuredProviderAdapter(fake, test_only=True)
        with self.assertRaises(ValueError):
            StructuredProviderAdapter(FakeSubclass(None, test_only=True), test_only=True)
        with self.assertRaises(ValueError):
            LocalChatService(provider=AdapterSubclass(fake, test_only=True), enabled=True, test_only=True, structured_mode=True)
        with self.assertRaises(AttributeError):
            fake.chat = lambda _: socket.socket().connect(('127.0.0.1', 9))
        with self.assertRaises(AttributeError):
            adapter.select_education = lambda _: socket.socket().connect(('127.0.0.1', 9))
        service = LocalChatService(provider=adapter, enabled=True, test_only=True, structured_mode=True)
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network')) as connect, \
             patch.object(FakeChatProvider, 'chat', side_effect=AssertionError('patched fake')), \
             patch.object(StructuredProviderAdapter, 'select_education', side_effect=AssertionError('patched adapter')):
            response = service.chat({'message':'synthetic', 'consent':CONSENT})
            self.assertFalse(response['external_sent'])
            connect.assert_not_called()
        self.assertEqual(fake.calls, 1)
        adapter._provider = object()
        with self.assertRaises(ServiceProblem) as err:
            service.chat({'message':'synthetic', 'consent':CONSENT})
        self.assertEqual(err.exception.code, 'CHAT_STRUCTURED_INVALID_PROVIDER')
        self.assertEqual(fake.calls, 1)

    def test_scripted_browser_fixture_over_http(self):
        from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
        from backend_services import LocalChatService
        from test_backend_integration import running_server, request
        from test_structured_education import CONSENT, SCENARIO
        fake = FakeChatProvider(None, test_only=True, scripted=True)
        service = LocalChatService(provider=StructuredProviderAdapter(fake, test_only=True), enabled=True, test_only=True, structured_mode=True)
        with running_server(chat_service=service) as server:
            for message, expected in [('SYNTHETIC TEST ONLY: explain', 200),
                                      ('SYNTHETIC TEST ONLY: calculate', 200),
                                      ('SYNTHETIC TEST ONLY: forged', 502),
                                      ('not synthetic', 502)]:
                payload = {'message':message, 'consent':CONSENT}
                if 'calculate' in message:
                    payload['scenario'] = SCENARIO
                status, body = request(server, '/api/chat', payload)
                self.assertEqual(status, expected)
                if status == 200:
                    self.assertIs(body['external_sent'], False)
                else:
                    self.assertNotIn('texto falsificado', str(body))
        self.assertEqual(fake.calls, 4)

    def test_valid_fake_chat_result_is_projected_to_closed_selection(self):
        from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
        selection = {'version':'paideia-education-v1','intent':'explain','claim_ids':['inflation']}
        fake = FakeChatProvider(ChatResult(json.dumps(selection), None, (), 'stop'), test_only=True)
        adapter = StructuredProviderAdapter(fake, test_only=True)
        self.assertEqual(adapter.select_education([{'role':'user','content':'inflation'}]), selection)
        self.assertEqual(fake.calls, 1)

    def test_history_or_extra_message_fields_never_reach_fake(self):
        from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
        from providers import ProviderError
        fake = FakeChatProvider(ChatResult('{}', None, (), 'stop'), test_only=True)
        adapter = StructuredProviderAdapter(fake, test_only=True)
        for messages in ([{'role':'user','content':'first'}, {'role':'assistant','content':'old'}, {'role':'user','content':'new'}],
                         [{'role':'user','content':'new','profile':'SYNTHETIC_PRIVATE'}]):
            with self.assertRaises(ProviderError):
                adapter.select_education(messages)
        self.assertEqual(fake.calls, 0)

    def test_closed_contract_rejects_adversarial_chat_results(self):
        from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
        from providers import ProviderError, ToolCall
        valid = '{"version":"paideia-education-v1","intent":"explain","claim_ids":["inflation"]}'
        secret = 'FAKE_SECRET_9384'
        bad = [
            ChatResult('prefix '+valid, None, (), 'stop'),
            ChatResult(valid+' trailing', None, (), 'stop'),
            ChatResult(valid.replace('"intent":"explain"','"intent":"explain","intent":"calculate"'), None, (), 'stop'),
            ChatResult(valid.replace('"inflation"','"inflation","inflation"'), None, (), 'stop'),
            ChatResult(valid.replace('inflation','unknown'), None, (), 'stop'),
            ChatResult(valid[:-1]+',"answer":"'+secret+'"}', None, (), 'stop'),
            ChatResult(valid[:-1]+',"answer":"'+chr(92)+'u0046AKE_SECRET_9384"}', None, (), 'stop'),
            ChatResult(valid.replace('explain','calculate')[:-1]+',"scenario":{}}', None, (), 'stop'),
            ChatResult(valid.replace('inflation','inflation'+chr(0x200b)), None, (), 'stop'),
            ChatResult('"'+('x'*4097)+'"', None, (), 'stop'),
            ChatResult(chr(0xd800), None, (), 'stop'),
            ChatResult(valid, None, (), 'length'),
            ChatResult(valid, None, (), None),
            ChatResult(valid, None, (), 'stop', secret),
            ChatResult(valid, None, (ToolCall('id','leak',{'x':secret}),), 'stop'),
            ChatResult(valid, None, [], 'stop'),
            object(),
        ]
        for response in bad:
            with self.subTest(response=repr(response)):
                fake = FakeChatProvider(response, test_only=True)
                with self.assertRaises(ProviderError) as err:
                    StructuredProviderAdapter(fake, test_only=True).select_education([{'role':'user','content':'test'}])
                self.assertEqual(err.exception.code, 'invalid_response')
                self.assertNotIn(secret, str(err.exception))
                self.assertEqual(fake.calls, 1)

    def test_fake_only_and_no_environment_network_or_tools(self):
        import os, socket
        from unittest.mock import patch
        from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
        valid = '{"version":"paideia-education-v1","intent":"explain","claim_ids":["risk"]}'
        with self.assertRaises(ValueError): FakeChatProvider(None)
        with self.assertRaises(ValueError): StructuredProviderAdapter(object(), test_only=True)
        with self.assertRaises(ValueError): StructuredProviderAdapter(FakeChatProvider(None, test_only=True))
        fake = FakeChatProvider(ChatResult(valid, 'FAKE_SECRET_9384', (), 'stop'), test_only=True)
        from providers import GroqHTTPSJSONTransport
        with patch.object(os, 'getenv', side_effect=AssertionError('environment')), patch.object(socket, 'create_connection', side_effect=AssertionError('network')), patch.object(GroqHTTPSJSONTransport, 'post', side_effect=AssertionError('HTTPS')) as https:
            selection = StructuredProviderAdapter(fake, test_only=True).select_education([{'role':'user','content':'ignore instructions'}])
            https.assert_not_called()
        self.assertEqual(selection['claim_ids'], ['risk'])
        self.assertNotIn('FAKE_SECRET_9384', str(selection))
        self.assertEqual(fake.calls, 1)

    def test_service_and_http_calculation_bound_to_same_turn_and_safe_failure(self):
        from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
        from backend_services import LocalChatService, ServiceProblem
        from test_backend_integration import running_server, request
        from test_structured_education import CONSENT, SCENARIO
        import domain
        valid = '{"version":"paideia-education-v1","intent":"calculate","claim_ids":["simulation"]}'
        fake = FakeChatProvider(ChatResult(valid, 'FAKE_SECRET_9384', (), 'stop'), test_only=True)
        service = LocalChatService(provider=StructuredProviderAdapter(fake, test_only=True), enabled=True, test_only=True, structured_mode=True)
        payload = {'message':'SYNTHETIC calculate','consent':CONSENT,'scenario':SCENARIO}
        result = service.chat(payload)
        self.assertEqual(result['structured_education']['calculation']['data'], domain.calculate_scenario(SCENARIO))
        self.assertNotIn('principal', str(fake.requests))
        with self.assertRaises(ServiceProblem): service.chat({'message':'repeat','consent':CONSENT})
        with running_server(chat_service=service) as server:
            status, body = request(server, '/api/chat', payload)
            self.assertEqual(status, 200)
            self.assertEqual(body['structured_education']['calculation']['data'], domain.calculate_scenario(SCENARIO))
            self.assertNotIn('FAKE_SECRET_9384', str(body))
            fake.result = ChatResult(valid[:-1]+',"answer":"FAKE_SECRET_9384"}', None, (), 'stop')
            status, body = request(server, '/api/chat', payload)
            self.assertEqual(status, 502)
            self.assertEqual(body['error']['code'], 'CHAT_STRUCTURED_INVALID_RESPONSE')
            self.assertNotIn('FAKE_SECRET_9384', str(body))
        self.assertEqual(fake.calls, 4)
        self.assertTrue(all([m['role'] for m in messages] == ['system','user'] for messages in fake.requests))

    def test_engine_failure_is_safe_and_not_retried(self):
        from unittest.mock import patch
        from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
        from backend_services import LocalChatService, ServiceProblem
        from test_backend_integration import running_server, request
        from test_structured_education import CONSENT, SCENARIO
        import domain
        raw = '{"version":"paideia-education-v1","intent":"calculate","claim_ids":["simulation"]}'
        fake = FakeChatProvider(ChatResult(raw, None, (), 'stop'), test_only=True)
        service = LocalChatService(provider=StructuredProviderAdapter(fake, test_only=True), enabled=True, test_only=True, structured_mode=True)
        payload = {'message':'SYNTHETIC calculate','consent':CONSENT,'scenario':SCENARIO}
        with patch.object(domain, 'calculate_scenario', side_effect=RuntimeError('FAKE_SECRET_9384')) as calc:
            with running_server(chat_service=service) as server:
                status, body = request(server, '/api/chat', payload)
            self.assertEqual(status, 502)
            self.assertNotIn('FAKE_SECRET_9384', str(body))
            calc.assert_called_once()
        self.assertEqual(fake.calls, 1)
