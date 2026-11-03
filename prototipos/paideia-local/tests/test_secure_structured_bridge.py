import json
import unittest

from groq_structured_adapter import build_structured_request
from domain import calculate_scenario
from providers import ProviderError

MESSAGES = [{'role': 'user', 'content': 'Explica'}]
SCENARIO = {'principal': '100', 'monthly_contribution': '0', 'annual_rate_percent': '0', 'inflation_percent': '0', 'years': 1, 'method': 'compound'}
SELECTION = {'version': 'paideia-education-v1', 'intent': 'calculate', 'claim_ids': ['simulation']}

def body(content=None, **message):
    return json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(SELECTION) if content is None else content, **message}}]}).encode()

class BridgeTests(unittest.TestCase):
    def test_exact_request_to_rendered_calculation(self):
        from secure_structured_bridge import FakeTransport, run_turn
        fake = FakeTransport(200, body())
        result = run_turn(fake, MESSAGES, SCENARIO)
        self.assertEqual(fake.requests, [build_structured_request(MESSAGES)])
        request = json.loads(fake.requests[0])
        self.assertEqual(request['response_format']['json_schema']['schema']['required'], ['version', 'intent', 'claim_ids'])
        self.assertFalse(request['response_format']['json_schema']['strict'])
        for field in ('tools', 'stream', 'scenario', 'profile'):
            self.assertNotIn(field, request)
        self.assertEqual(result['provider_mode'], 'test_only')
        self.assertIs(result['external_sent'], False)
        self.assertEqual(result['structured_education']['calculation']['data'], calculate_scenario(SCENARIO))
        self.assertEqual(result['structured_education']['items'][0]['id'], 'simulation')

    def test_fail_closed_no_retry_or_sensitive_errors(self):
        from secure_structured_bridge import FakeTransport, run_turn
        tool = [{'id': 'abc', 'type': 'function', 'function': {'name': 'x', 'arguments': '{}'}}]
        duplicate = '{"version":"paideia-education-v1","version":"paideia-education-v1","intent":"calculate","claim_ids":["simulation"]}'
        truncated = json.dumps({'choices': [{'finish_reason': 'length', 'message': {'role': 'assistant', 'content': json.dumps(SELECTION)}}]}).encode()
        variants = [(200, b'{', False), (200, b'{"choices":[],"choices":[]}', False),
                    (200, body('{'), False), (200, body(duplicate), False),
                    (200, body(json.dumps({**SELECTION, 'claim_ids': ['simulation', 'simulation']})), False),
                    (200, body(refusal='FAKE_SECRET'), False), (200, truncated, False),
                    (200, body(tool_calls=tool), False), (429, b'FAKE_SECRET', False),
                    (200, body(), True), (200, body(json.dumps({**SELECTION, 'answer': 'FAKE_SECRET'})), False),
                    (200, body(json.dumps({**SELECTION, 'scenario': SCENARIO})), False)]
        for status, payload, tls in variants:
            with self.subTest(payload=payload[:60], status=status, tls=tls):
                fixture = FakeTransport(status, payload, fail_tls=tls)
                with self.assertRaises(ProviderError) as caught:
                    run_turn(fixture, MESSAGES, SCENARIO)
                self.assertEqual(caught.exception.code, 'invalid_response')
                self.assertIsNone(caught.exception.__context__)
                self.assertNotIn('FAKE_SECRET', str(caught.exception))
                self.assertEqual(len(fixture.requests), 1)

    def test_reasoning_never_displayed_and_scenario_must_be_same_turn(self):
        from secure_structured_bridge import FakeTransport, run_turn
        fake = FakeTransport(200, body(reasoning='FAKE_SECRET'))
        result = run_turn(fake, MESSAGES, SCENARIO)
        self.assertNotIn('FAKE_SECRET', json.dumps(result))
        with self.assertRaises(ProviderError):
            run_turn(fake, MESSAGES)
        self.assertEqual(len(fake.requests), 2)

    def test_rejects_network_like_impostor_and_invalid_request(self):
        from secure_structured_bridge import FakeTransport, run_turn
        class Impostor:
            test_only = True
            def post(self, *args):
                raise AssertionError('must never run')
        with self.assertRaises(ProviderError):
            run_turn(Impostor(), MESSAGES, SCENARIO)
        fake = FakeTransport(200, body())
        with self.assertRaises(ProviderError):
            run_turn(fake, [{'role': 'user', 'content': 'x', 'profile': 'private'}], SCENARIO)
        self.assertEqual(fake.requests, [])
