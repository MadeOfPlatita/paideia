"""Offline tests only; no actual credential or network."""
import importlib
import unittest

try:
    smoke = importlib.import_module('secure_groq_smoke')
except ModuleNotFoundError:
    smoke = None


class TestSecureGroqSmoke(unittest.TestCase):
    def test_single_attempt_uses_fixed_synthetic_prompt_and_never_returns_key(self):
        self.assertIsNotNone(smoke)
        import json
        from providers import TransportResponse
        class TestOnlyTransport:
            test_only = True
            calls = 0
            def post(self, **kwargs):
                self.calls += 1
                body = json.loads(kwargs['body'])
                self.messages = body['messages']
                return TransportResponse(200, json.dumps({'choices':[{'message':{'role':'assistant','content':'SYNTHETIC TEST RESPONSE'},'finish_reason':'stop'}]}).encode())
        transport = TestOnlyTransport()
        session = smoke.SmokeSession(transport=transport)
        key = 'SYNTHETIC_TEST_TOKEN_NOT_A_REAL_KEY'
        first = session.run(key, free_plan_confirmed=True)
        second = session.run(key, free_plan_confirmed=True)
        self.assertEqual(transport.calls, 1, 'A double click must not cause another request')
        self.assertEqual(first['provider_calls'], 1)
        self.assertTrue(first['test_only'])
        self.assertEqual(first['status'], 'success')
        self.assertEqual(second['status'], 'already_attempted')
        self.assertNotIn(key, json.dumps(first))
        self.assertEqual(transport.messages, smoke.SMOKE_MESSAGES)

    def test_window_masks_key_and_does_not_submit_on_open(self):
        self.assertIsNotNone(smoke)
        self.assertTrue(callable(getattr(smoke, 'create_window', None)), 'Masked local window is missing')
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / 'result.json'
            window = smoke.create_window(report)
            try:
                window['root'].withdraw()
                self.assertEqual(window['key_entry'].cget('show'), '*')
                self.assertFalse(window['confirmed'].get())
                self.assertFalse(report.exists())
                self.assertFalse(window['session'].attempted)
            finally:
                window['root'].destroy()

    def test_window_roundtrip_saves_sanitized_result_without_key(self):
        import inspect, json, tempfile, time
        from pathlib import Path
        from providers import TransportResponse
        self.assertIn('transport', inspect.signature(smoke.create_window).parameters, 'The UI must allow offline end-to-end verification')
        class TestOnlyTransport:
            test_only = True
            def post(self, **kwargs):
                return TransportResponse(200, json.dumps({'choices':[{'message':{'role':'assistant','content':'SYNTHETIC WINDOW TEST'},'finish_reason':'stop'}]}).encode())
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'report.json'
            window = smoke.create_window(path, transport=TestOnlyTransport())
            try:
                window['root'].withdraw()
                key = 'SYNTHETIC_WINDOW_TOKEN_NOT_A_REAL_KEY'
                window['key_entry'].insert(0, key)
                window['start'].invoke()
                self.assertFalse(window['session'].attempted)
                window['confirmed'].set(True)
                window['start'].invoke()
                self.assertEqual(window['key_entry'].get(), '')
                deadline = time.monotonic() + 3
                while not path.exists() and time.monotonic() < deadline:
                    window['root'].update()
                    time.sleep(0.01)
                self.assertTrue(path.exists())
                raw = path.read_text(encoding='utf-8')
                self.assertNotIn(key, raw)
                self.assertTrue(json.loads(raw)['test_only'])
                self.assertIn('SINTÉTICA', window['status'].get())
                self.assertTrue(window['start'].instate(['disabled']))
            finally:
                window['root'].destroy()

    def test_no_network_without_explicit_free_plan_confirmation(self):
        self.assertIsNotNone(smoke, 'The memory-only guarded smoke runner is missing')
        class NeverTransport:
            test_only = True
            def post(self, **kwargs):
                raise AssertionError('Network must not run before confirmation')
        session = smoke.SmokeSession(transport=NeverTransport())
        result = session.run('SYNTHETIC_TEST_TOKEN_NOT_A_REAL_KEY', free_plan_confirmed=False)
        self.assertEqual(result['status'], 'free_plan_confirmation_required')
        self.assertEqual(result['provider_calls'], 0)
        self.assertFalse(session.attempted)
