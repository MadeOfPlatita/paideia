import json
import unittest
from unittest.mock import patch

from groq_structured_adapter import build_structured_request
from structured_education import render_selection


class CountedProviderTests(unittest.TestCase):
    def test_single_structured_post_and_render(self):
        from structured_counted_provider import FakeCountedTransport, StructuredCountedProvider
        selection = {'version': 'paideia-education-v1', 'intent': 'calculate', 'claim_ids': ['simulation']}
        body = json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(selection)}}]}).encode()
        fixture = FakeCountedTransport(200, body)
        messages = [{'role': 'user', 'content': 'SYNTHETIC TEST ONLY'}]
        with patch('socket.create_connection', side_effect=AssertionError('network prohibited')):
            result = StructuredCountedProvider(fixture).select_education(messages)
        self.assertEqual(result, selection)
        self.assertEqual(fixture.reservations, 1)
        self.assertEqual(len(fixture.requests), 1)
        request = fixture.requests[0]
        self.assertEqual(set(request), {'host', 'path', 'headers', 'body', 'timeout'})
        self.assertEqual(request['body'], build_structured_request(messages))
        self.assertEqual(request['host'], 'api.groq.com')
        self.assertEqual(request['path'], '/openai/v1/chat/completions')
        self.assertEqual(request['headers'], {'Authorization': 'Bearer test-only', 'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.assertEqual(request['timeout'], 15.0)
        self.assertNotIn('tools', json.loads(request['body']))
        scenario = {'principal': '1000', 'monthly_contribution': '0', 'annual_rate_percent': '2', 'inflation_percent': '1', 'years': 2, 'method': 'compound'}
        rendered = render_selection(result, scenario, scenario_present=True)
        self.assertEqual(rendered['provider_mode'], 'test_only')
        self.assertIs(rendered['external_sent'], False)
        self.assertEqual(rendered['structured_education']['calculation']['source'], 'deterministic_local')

    def test_failure_is_sanitized_and_post_state_unknown(self):
        from structured_counted_provider import FakeCountedTransport, StructuredCountedProvider
        from providers import ProviderError
        selection = '{"version":"paideia-education-v1","intent":"explain","claim_ids":["risk"]}'
        def response(content=selection, reason='stop', **extra):
            return json.dumps({'choices': [{'finish_reason': reason, 'message': {'role': 'assistant', 'content': content, **extra}}]}).encode()
        cases = [(429, b'secret-429', False, False), (503, b'secret-503', False, False),
                 (400, b'secret-400', False, False), (200, b'secret-tls', True, False),
                 (200, response(refusal='secret-refusal'), False, False),
                 (200, response(reason='length'), False, False),
                 (200, response('{"version":"paideia-education-v1","intent":"explain","claim_ids":["risk","risk"]}'), False, False),
                 (200, response('{"version":"paideia-education-v1","intent":"explain","intent":"calculate","claim_ids":["risk"]}'), False, False),
                 (200, b'secret-revoked', False, True)]
        for status, body, failure, revoked in cases:
            with self.subTest(status=status, body=body, failure=failure, revoked=revoked):
                fake = FakeCountedTransport(status, body, failure=failure, revoked=revoked)
                with self.assertRaises(ProviderError) as caught:
                    StructuredCountedProvider(fake).select_education([{'role': 'user', 'content': 'secret-input'}])
                error = caught.exception
                self.assertEqual(error.sent_state, 'unknown')
                self.assertEqual(error.code, 'invalid_response')
                self.assertNotIn('secret', str(error))
                self.assertIsNone(error.__cause__)
                self.assertFalse(error.retryable)
                self.assertEqual(fake.reservations, 0 if revoked else 1)
                self.assertEqual(len(fake.requests), 0 if revoked else 1)

    def test_invalid_response_traceback_locals_do_not_retain_fake_payload(self):
        import traceback
        from structured_counted_provider import FakeCountedTransport, StructuredCountedProvider
        from providers import ProviderError

        input_marker = 'SYNTHETIC_INPUT_MARKER'
        response_marker = 'SYNTHETIC_RESPONSE_MARKER'
        fake = FakeCountedTransport(200, response_marker.encode())
        try:
            StructuredCountedProvider(fake).select_education([{'role': 'user', 'content': input_marker}])
        except ProviderError as error:
            captured = traceback.TracebackException.from_exception(error, capture_locals=True)
            import os
            provider_frames = [frame for frame in captured.stack if os.path.basename(frame.filename) == 'structured_counted_provider.py']
            self.assertTrue(provider_frames)
            for frame in provider_frames:
                self.assertTrue({'self', 'messages', 'body', 'transport'}.isdisjoint(frame.locals))
            visible = repr([frame.locals for frame in provider_frames])
            for marker in (input_marker, response_marker, 'Bearer test-only'):
                self.assertNotIn(marker, visible)
            self.assertIsNone(error.__context__)
            self.assertIsNone(error.__cause__)
            self.assertEqual(error.sent_state, 'unknown')
            self.assertEqual(error.code, 'invalid_response')
        else:
            self.fail('invalid fake response must fail')
        self.assertEqual(len(fake.requests), 1)
        self.assertIn(input_marker.encode(), fake.requests[0]['body'])
        self.assertEqual(fake.requests[0]['headers']['Authorization'], 'Bearer test-only')

    def test_transport_gate_and_disabled_real_factory(self):
        from structured_counted_provider import StructuredCountedProvider, create_session_provider
        from providers import ProviderError
        class PretendFake:
            test_only = True
            def post(self, **kwargs):
                raise AssertionError('must not be reached')
        with self.assertRaises(ProviderError):
            StructuredCountedProvider(PretendFake())
        with self.assertRaises(ProviderError) as caught:
            create_session_provider(PretendFake())
        self.assertEqual(caught.exception.code, 'disabled')


if __name__ == '__main__':
    unittest.main()
