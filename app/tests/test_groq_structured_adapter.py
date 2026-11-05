import json
import unittest

from providers import ChatResult
from structured_provider_adapter import FakeChatProvider


class OfflineGroqContractTests(unittest.TestCase):
    def test_builds_existing_request_and_selects_once(self):
        from groq_structured_adapter import OfflineGroqStructuredAdapter
        fixture = FakeChatProvider(ChatResult(json.dumps({'version': 'paideia-education-v1', 'intent': 'explain', 'claim_ids': ['risk']}), None, (), 'stop'), test_only=True)
        adapter = OfflineGroqStructuredAdapter(fixture)
        from unittest.mock import patch
        from groq_structured_adapter import build_structured_request
        bodies = []
        def capture(messages):
            body = build_structured_request(messages)
            bodies.append(body)
            return body
        with patch('groq_structured_adapter.build_structured_request', capture):
            selection = adapter.select_education([{'role': 'user', 'content': 'Explica el riesgo'}])
        self.assertEqual(selection['claim_ids'], ['risk'])
        self.assertEqual(fixture.calls, 1)
        body = json.loads(bodies[0])
        self.assertEqual(body['messages'], [{'role': 'user', 'content': 'Explica el riesgo'}])
        from structured_education import EDITORIAL, VERSION
        self.assertEqual(body['max_tokens'], 256)
        self.assertEqual(body['model'], 'openai/gpt-oss-20b')
        fmt = body['response_format']
        self.assertEqual(fmt['type'], 'json_schema')
        self.assertEqual(fmt['json_schema']['name'], 'paideia_education_v1')
        self.assertIs(fmt['json_schema']['strict'], False)
        schema = fmt['json_schema']['schema']
        self.assertEqual(schema['additionalProperties'], False)
        self.assertEqual(set(schema['required']), {'version', 'intent', 'claim_ids'})
        self.assertEqual(set(schema['properties']), set(schema['required']))
        self.assertEqual(schema['properties']['version']['enum'], [VERSION])
        self.assertEqual(schema['properties']['intent']['enum'], ['explain', 'calculate'])
        self.assertEqual(set(schema['properties']['claim_ids']['items']['enum']), set(EDITORIAL))
        self.assertIs(schema['properties']['claim_ids']['uniqueItems'], True)
        self.assertEqual(json.loads(json.dumps(body)), body)
        self.assertNotIn('tools', body)
        self.assertNotIn('stream', body)

    def test_request_rejects_controls_history_and_post_schema_oversize(self):
        from groq_structured_adapter import build_structured_request
        from providers import MAX_REQUEST_BYTES
        message = {'role': 'user', 'content': 'x'}
        for bad in ([message, message], [{'role': 'user', 'content': 'x', 'profile': 'private'}],
                    [{'role': 'assistant', 'content': 'old'}, message],
                    [{'role': 'user', 'content': 'x' * (MAX_REQUEST_BYTES - 200)}]):
            with self.subTest(bad=str(bad)[:90]), self.assertRaises(ValueError):
                build_structured_request(bad)
        for option in ('model', 'schema', 'response_format', 'tools', 'stream', 'max_output_tokens'):
            with self.subTest(option=option), self.assertRaises(TypeError):
                build_structured_request([message], **{option: 'untrusted'})

    def test_error_boundary_does_not_keep_sensitive_exception_context(self):
        from unittest.mock import patch
        from providers import ProviderError
        from groq_structured_adapter import OfflineGroqStructuredAdapter
        fixture = FakeChatProvider(None, test_only=True)
        with patch('groq_structured_adapter.build_chat_request', side_effect=ValueError('FAKE_SECRET')):
            with self.assertRaises(ProviderError) as caught:
                OfflineGroqStructuredAdapter(fixture).select_education([{'role': 'user', 'content': 'x'}])
        self.assertIsNone(caught.exception.__context__)
        self.assertNotIn('FAKE_SECRET', str(caught.exception))
        self.assertEqual(fixture.calls, 0)

    def test_rejects_nonfixture_even_with_test_only_label(self):
        from groq_structured_adapter import OfflineGroqStructuredAdapter
        class Impostor:
            test_only = True
        with self.assertRaises(ValueError):
            OfflineGroqStructuredAdapter(Impostor())
        with self.assertRaises(TypeError):
            OfflineGroqStructuredAdapter(None, transport=Impostor())

    def test_rejects_malformed_or_untrusted_responses_without_retry(self):
        from groq_structured_adapter import OfflineGroqStructuredAdapter
        from providers import ProviderError
        good = '{"version":"paideia-education-v1","intent":"explain","claim_ids":["risk"]}'
        variants = [
            ChatResult('{', None, (), 'stop'),
            ChatResult('{"version":"paideia-education-v1","version":"paideia-education-v1","intent":"explain","claim_ids":["risk"]}', None, (), 'stop'),
            ChatResult(good, None, (), 'length'),
            ChatResult(good, None, (), None),
            ChatResult(good, None, (), 'stop', 'FAKE_SECRET'),
            ChatResult(good, None, ('tool',), 'stop'),
            ChatResult(good, None, (), 'tool_calls'),
            ChatResult(good.replace('"risk"', '"unknown"'), None, (), 'stop'),
            ChatResult(good.replace('"risk"', '"risk","risk"'), None, (), 'stop'),
            ChatResult(good[:-1] + ',"scenario":{"principal":"1"}}', None, (), 'stop'),
            ChatResult(good[:-1] + ',"answer":"FAKE_SECRET"}', None, (), 'stop'),
            ChatResult('é' * 2049, None, (), 'stop'),
            ChatResult('\ud800', None, (), 'stop'),
        ]
        for result in variants:
            with self.subTest(result=repr(result)[:80]):
                fixture = FakeChatProvider(result, test_only=True)
                with self.assertRaises(ProviderError) as caught:
                    OfflineGroqStructuredAdapter(fixture).select_education([{'role': 'user', 'content': 'x'}])
                self.assertEqual(caught.exception.code, 'invalid_response')
                self.assertIsNone(caught.exception.__context__)
                self.assertNotIn('FAKE_SECRET', str(caught.exception))
                self.assertEqual(fixture.calls, 1)

    def test_service_will_not_accept_this_adapter(self):
        from backend_services import LocalChatService
        from groq_structured_adapter import OfflineGroqStructuredAdapter
        fixture = FakeChatProvider(None, test_only=True)
        with self.assertRaises(ValueError):
            LocalChatService(provider=OfflineGroqStructuredAdapter(fixture), enabled=True, test_only=True, structured_mode=True)

    def test_calculation_requires_same_turn_scenario_owned_by_renderer(self):
        from groq_structured_adapter import OfflineGroqStructuredAdapter
        from structured_education import render_selection
        fixture = FakeChatProvider(ChatResult('{"version":"paideia-education-v1","intent":"calculate","claim_ids":["simulation"]}', None, (), 'stop'), test_only=True)
        selection = OfflineGroqStructuredAdapter(fixture).select_education([{'role': 'user', 'content': 'x'}])
        with self.assertRaises(ValueError):
            render_selection(selection)
        scenario = {'principal': '100', 'monthly_contribution': '0', 'annual_rate_percent': '0', 'inflation_percent': '0', 'years': 1, 'method': 'compound'}
        rendered = render_selection(selection, scenario, scenario_present=True)
        self.assertEqual(rendered['structured_education']['calculation']['source'], 'deterministic_local')
        self.assertEqual(fixture.calls, 1)

if __name__ == '__main__':
    unittest.main()
