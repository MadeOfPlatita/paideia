import unittest
from datetime import datetime, timezone, timedelta

from secure_groq_session import Session
from structured_session_fixture import StructuredSessionFixture


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 29, 16, 0, tzinfo=timezone.utc)
    def __call__(self):
        return self.now


class SessionTests(unittest.TestCase):
    def test_gui_requires_explicit_consent_clears_key_and_single_start(self):
        import secure_groq_session as module
        from unittest.mock import patch
        class Widget:
            def __init__(self, *args, **kwargs):
                self.options = kwargs
                self.value = ''
            def pack(self, **kwargs): pass
            def get(self): return self.value
            def delete(self, *args): self.value = ''
            def configure(self, **kwargs): self.options.update(kwargs)
        class Root(Widget):
            def title(self, *args): pass
            def geometry(self, *args): pass
            def protocol(self, *args): pass
            def after(self, *args): return 'timer'
            def after_cancel(self, *args): pass
            def destroy(self): pass
        class Variable:
            def __init__(self, root, value=None): self.value = value
            def get(self): return self.value
            def set(self, value): self.value = value
        import types
        import tkinter
        fake = StructuredSessionFixture(200, b'{}')
        fake_tk = types.SimpleNamespace(Tk=Root, BooleanVar=Variable, StringVar=Variable, END=module.tk.END)
        with patch.object(tkinter, 'Tk', side_effect=AssertionError('real Tk forbidden')), patch.object(module, 'tk', fake_tk), patch.object(module.ttk, 'Frame', Widget), patch.object(module.ttk, 'Label', Widget), patch.object(module.ttk, 'Entry', Widget), patch.object(module.ttk, 'Checkbutton', Widget), patch.object(module.ttk, 'Button', Widget):
            ui = module.create_window(transport=fake, test_only=True, clock=Clock(), port=0)
            self.addCleanup(ui['close'])
            self.assertEqual(ui['entry'].options['show'], '*')
            self.assertFalse(ui['confirmed'].get())
            self.assertFalse(ui['benchmark_confirmed'].get())
            self.assertEqual(len(fake.requests), 0)
            ui['entry'].value = 'FAKE-ONLY'
            ui['start']()
            self.assertEqual(ui['entry'].get(), 'FAKE-ONLY')
            self.assertIsNone(ui['session']())
            ui['confirmed'].set(True)
            ui['start']()
            self.assertEqual(ui['entry'].get(), '')
            session = ui['session']()
            self.assertIsNotNone(session)
            ui['start']()
            self.assertIs(ui['session'](), session)
            self.assertEqual(len(fake.requests), 0)
            ui['close']()
            with patch.object(module.Session, 'start_benchmark', return_value=True) as launch:
                second = module.create_window(transport=fake, test_only=True, clock=Clock(), port=0)
                self.addCleanup(second['close'])
                second['entry'].value = 'FAKE-ONLY'
                second['confirmed'].set(True)
                second['benchmark_confirmed'].set(True)
                second['start']()
                launch.assert_called_once_with(confirmed=True)
                self.assertEqual(len(fake.requests), 0)
                second['close']()

    def test_http_synthetic_calculation_and_safe_status(self):
        import json
        import tempfile
        from pathlib import Path
        from providers import TransportResponse
        from test_backend_integration import request
        from test_pai_runtime import scenario_arguments
        # Legacy tool flow requires a tool-call response followed by a final answer.
        message = {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'synthetic1', 'type': 'function', 'function': {'name': 'calculate_scenario', 'arguments': json.dumps(scenario_arguments())}}]}
        first = json.dumps({'choices': [{'message': message, 'finish_reason': 'tool_calls'}]}).encode()
        final = json.dumps({'choices': [{'message': {'role': 'assistant', 'content': 'SINTÉTICO: resultado'}, 'finish_reason': 'stop'}]}).encode()
        transport = StructuredSessionFixture(200, first, outcomes=((200, first), (200, final)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            session = Session('FAKE-ONLY', transport=transport, clock=Clock(), test_only=True)
            server = session.start_server(port=0, output=path)
            try:
                consent = {'notice_version': 'paideia-chat-remote-v1', 'accepted_chat_processing': True, 'purpose': 'free_chat', 'approved_fields': []}
                status, body = request(server, '/api/chat', {'message': 'SINTÉTICO: calcula', 'consent': consent})
                self.assertEqual(status, 200, body)
                self.assertIn('SINTÉTICO', body['answer'])
                self.assertEqual(body['tool_events'][0]['name'], 'calculate_scenario')
                self.assertEqual(len(transport.requests), 2)
                self.assertEqual([t['function']['name'] for t in json.loads(transport.requests[0])['tools']], ['calculate_scenario'])
                self.assertEqual(session.status()['calls'], 2)
                session.write_status()
                self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['calls'], 2)
                self.assertNotIn('FAKE-ONLY', path.read_text(encoding='utf-8'))
            finally:
                session.close()

    def test_double_start_fails_closed(self):
        session = Session('FAKE-ONLY', transport=StructuredSessionFixture(200, b'{}'), clock=Clock(), test_only=True)
        try:
            session.start_server(port=0)
            with self.assertRaises(Exception):
                session.start_server(port=0)
        finally:
            session.close()

    def test_revoke_during_inflight_does_not_cancel_it_but_blocks_next(self):
        import threading
        from providers import TransportResponse, ProviderError
        entered, release = threading.Event(), threading.Event()
        from structured_session_fixture import StructuredSessionFixture
        upstream = StructuredSessionFixture(200, b'{"choices":[{"message":{"role":"assistant","content":"SYNTHETIC"},"finish_reason":"stop"}]}')
        upstream.post_entered, upstream.post_release = entered, release
        session = Session('FAKE-ONLY', transport=upstream, clock=Clock(), test_only=True)
        results = []
        thread = threading.Thread(target=lambda: results.append(session.provider.chat([{'role':'user','content':'ficticio'}])))
        thread.start()
        self.assertTrue(entered.wait(2))
        session.revoke()
        release.set()
        thread.join(3)
        self.assertEqual(results[0].answer, 'SYNTHETIC')
        with self.assertRaises(ProviderError): session.provider.chat([{'role':'user','content':'ficticio'}])
        self.assertEqual(len(upstream.requests), 1)
        self.assertEqual(session._environment, {})

    def test_close_survives_inaccessible_status_output(self):
        from unittest.mock import patch
        from structured_session_fixture import StructuredSessionFixture
        session = Session('FAKE-ONLY', transport=StructuredSessionFixture(200, b'{}'), clock=Clock(), test_only=True)
        with patch.object(session, 'write_status', side_effect=OSError('no write')):
            session.close()
        self.assertEqual(session.status()['state'], 'revoked')

    def test_benchmark_runs_eighteen_synthetic_calls_with_shared_quota_and_spacing(self):
        import json, tempfile
        from pathlib import Path
        from providers import TransportResponse
        from structured_session_fixture import StructuredSessionFixture
        upstream = StructuredSessionFixture(200, json.dumps({'choices':[{'message':{'role':'assistant','content':'SINTÉTICO: prueba'},'finish_reason':'stop'}]}).encode())
        intervals = []
        session = Session('FAKE-ONLY', transport=upstream, clock=Clock(), test_only=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            self.assertTrue(session.start_benchmark(confirmed=True, output=path, wait=lambda seconds: intervals.append(seconds) or False))
            session._benchmark_thread.join(timeout=10)
            report = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(report['attempted_calls'], 18)
            self.assertEqual(len(report['results']), 18)
            self.assertEqual(report['provenance'], 'test_only')
            self.assertEqual(intervals, [21] * 17)
            self.assertEqual(session.status()['calls'], 18)
        session.close()

    def test_benchmark_requires_explicit_consent_and_stops_on_429(self):
        import json
        import tempfile
        from pathlib import Path
        from providers import TransportResponse
        from structured_session_fixture import StructuredSessionFixture
        upstream = StructuredSessionFixture(429, b'{}')
        session = Session('FAKE-ONLY', transport=upstream, clock=Clock(), test_only=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'benchmark.json'
            self.assertFalse(session.start_benchmark(confirmed=False, output=path, wait=lambda seconds: False))
            self.assertEqual(len(upstream.requests), 0)
            self.assertTrue(session.start_benchmark(confirmed=True, output=path, wait=lambda seconds: False))
            session._benchmark_thread.join(timeout=5)
            self.assertFalse(session._benchmark_thread.is_alive())
            report = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(report['stop_reason'], 'http_429')
            self.assertEqual(session.status()['benchmark'], 'stopped')
            self.assertEqual(report['provenance'], 'test_only')
            self.assertIsNone(report['winner'])
            self.assertNotIn('FAKE-ONLY', path.read_text(encoding='utf-8'))
            self.assertEqual(session.status()['calls'], 1)
            self.assertFalse(session.start_benchmark(confirmed=True, output=path, wait=lambda seconds: False))
        session.close()

    def test_monotonic_elapsed_limit_and_absolute_deadline(self):
        clock = Clock()
        elapsed = [100.0]
        from structured_session_fixture import StructuredSessionFixture
        session = Session('FAKE-ONLY', transport=StructuredSessionFixture(200, b'{}'), clock=clock, test_only=True,
                          monotonic=lambda: elapsed[0], deadline=clock.now + timedelta(seconds=90))
        elapsed[0] += 3600
        with self.assertRaises(Exception): session.transport.post(host='synthetic', path='/', headers={}, body=b'{}', timeout=1)
        self.assertEqual(session.status()['state'], 'expired')
        session = Session('FAKE-ONLY', transport=StructuredSessionFixture(200, b'{}'), clock=clock, test_only=True,
                          monotonic=lambda: elapsed[0], deadline=clock.now + timedelta(seconds=90))
        clock.now += timedelta(seconds=90)
        with self.assertRaises(Exception): session.transport.post(host='synthetic', path='/', headers={}, body=b'{}', timeout=1)
        self.assertEqual(session._environment, {})

    def test_concurrent_counter_and_failed_attempts_count(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        from collections import Counter
        from providers import ProviderError, SendState
        upstream = StructuredSessionFixture(200, b'{}')
        upstream.connect_entered, upstream.connect_release = threading.Event(), threading.Event()
        session = Session('FAKE-ONLY', transport=upstream, clock=Clock(), test_only=True)
        def call(_):
            try:
                session.transport.post(host='synthetic', path='/', headers={}, body=b'{}', timeout=1)
            except TimeoutError as error:
                return (type(error), str(error))
            except ProviderError as error:
                return (type(error), error.code, error.send_state, error.retryable)
            self.fail('unexpected successful call')
        with ThreadPoolExecutor(max_workers=30) as pool:
            results = list(pool.map(call, range(80)))
        self.assertEqual(len(results), 80)
        self.assertEqual(Counter(results), Counter({
            (TimeoutError, 'synthetic connect timeout'): 24,
            (ProviderError, 'disabled', SendState.NOT_STARTED, False): 56,
        }))
        status = session.status()
        self.assertEqual(status['calls'], 24)
        self.assertEqual(status['state'], 'quota_exhausted')
        self.assertFalse(status['final_pending'])
        self.assertEqual(len(upstream.requests), 0)

    def test_transport_counts_and_blocks_at_24(self):
        from structured_session_fixture import StructuredSessionFixture
        clock, upstream = Clock(), StructuredSessionFixture(200, b'{}')
        session = Session('FAKE-ONLY', transport=upstream, clock=clock, test_only=True)
        for _ in range(24):
            session.transport.post(host='synthetic', path='/', headers={}, body=b'{}', timeout=1)
        with self.assertRaises(Exception):
            session.transport.post(host='synthetic', path='/', headers={}, body=b'{}', timeout=1)
        self.assertEqual(len(upstream.requests), 24)
        self.assertEqual(session.status()['calls'], 24)

    def test_revocation_and_expiry_block_future_posts(self):
        from structured_session_fixture import StructuredSessionFixture
        clock, upstream = Clock(), StructuredSessionFixture(200, b'{}')
        session = Session('FAKE-ONLY', transport=upstream, clock=clock, test_only=True)
        session.revoke()
        with self.assertRaises(Exception):
            session.transport.post(host='synthetic', path='/', headers={}, body=b'{}', timeout=1)
        self.assertEqual(session._environment, {})
        session = Session('FAKE-ONLY', transport=upstream, clock=clock, test_only=True)
        clock.now += timedelta(seconds=3600)
        with self.assertRaises(Exception):
            session.transport.post(host='synthetic', path='/', headers={}, body=b'{}', timeout=1)
        self.assertEqual(session._environment, {})
        self.assertEqual(len(upstream.requests), 0)
