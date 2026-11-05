import threading
import unittest
from datetime import timedelta
from unittest.mock import patch
from types import SimpleNamespace

import secure_groq_session as module
from providers import ProviderError
from test_session_send_boundary import NOW, MESSAGE, FakeConnection, FakeDateTime
from structured_session_fixture import StructuredSessionFixture
BODY = b'{"choices":[{"message":{"role":"assistant","content":"synthetic"},"finish_reason":"stop"}]}'


class Widget:
    def __init__(self, *args, **kwargs): self.value = ''
    def pack(self, **kwargs): pass
    def get(self): return self.value
    def delete(self, *args): self.value = ''
    def configure(self, **kwargs): pass

class Root(Widget):
    def title(self, *args): pass
    def geometry(self, *args): pass
    def protocol(self, *args): pass
    def after(self, delay, callback): self.callback = callback; return 'timer'
    def after_cancel(self, *args): pass
    def destroy(self): pass

class Variable:
    def __init__(self, root, value=None): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value

class LastSlotLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.now = [NOW]
        self.fixture = StructuredSessionFixture(200, BODY)
        self.fixture.connect_entered, self.fixture.connect_release = threading.Event(), threading.Event()
        self.fixture.connect_release.set()
        patches = [patch.object(module.tk, 'Tk', Root), patch.object(module.tk, 'BooleanVar', Variable),
                   patch.object(module.tk, 'StringVar', Variable),
                   *[patch.object(module.ttk, name, Widget) for name in ('Frame', 'Label', 'Entry', 'Checkbutton', 'Button')],
                   patch.object(module.Session, 'start_server', return_value=SimpleNamespace(server_port=0))]
        for p in patches: p.start(); self.addCleanup(p.stop)
        self.ui = module.create_window(test_only=True, transport=self.fixture, clock=lambda: self.now[0], deadline=NOW + timedelta(seconds=10), port=0)
        self.ui['entry'].value = 'FAKE-ONLY'
        self.ui['confirmed'].set(True)
        self.ui['start']()
        self.session = self.ui['session']()
        self.fixture.connect_release.set()
        for _ in range(23): self.session.provider.chat(MESSAGE)
        self.fixture.connect_release.clear()
        self.fixture.connect_entered.clear()
        self.results, self.errors = [], []
        def call():
            try: self.results.append(self.session.provider.chat(MESSAGE))
            except ProviderError as e: self.errors.append(e.code)
        self.thread = threading.Thread(target=call)
        self.thread.start()
        self.addCleanup(self.finish)
        self.assertTrue(self.fixture.connect_entered.wait(2))

    def finish(self):
        self.fixture.connect_release.set()
        self.thread.join(3)

    def test_poll_keeps_reserved_final_attempt_alive(self):
        self.assertEqual(self.session.status()['state'], 'quota_exhausted')
        self.assertTrue(self.session.status()['final_pending'])
        self.assertEqual(self.session._environment, {})
        self.ui['root'].callback()
        self.assertEqual(self.session.status()['state'], 'quota_exhausted')
        with self.assertRaises(RuntimeError):
            self.session.transport.post()
        self.finish()
        self.assertFalse(self.thread.is_alive())
        self.assertEqual(len(self.fixture.requests), 24)
        self.assertEqual(self.results[0].answer, 'synthetic')
        self.assertFalse(self.session.status()['final_pending'])
        self.ui['root'].callback()
        self.assertEqual(self.session.status()['state'], 'revoked')

    def test_explicit_revoke_wins_before_send(self):
        self.session.revoke()
        self.finish()
        self.assertEqual(len(self.fixture.requests), 23)
        self.assertEqual(self.errors, ['transport_error'])

    def test_poll_closes_on_deadline_even_while_pending(self):
        self.now[0] += timedelta(seconds=10)
        self.ui['root'].callback()
        self.assertEqual(self.session.status()['state'], 'revoked')
        self.finish()
        self.assertEqual(len(self.fixture.requests), 23)
        self.assertEqual(self.errors, ['transport_error'])

    def test_failure_clears_pending_and_poll_closes(self):
        # The closed fixture's synthetic connect times out before send.
        self.thread.join(4)
        self.assertFalse(self.thread.is_alive())
        self.assertEqual(len(self.fixture.requests), 23)
        self.assertEqual(self.errors, ['timeout'])
        self.assertFalse(self.session.status()['final_pending'])
        self.ui['root'].callback()
        self.assertEqual(self.session.status()['state'], 'revoked')


class RealTransportFinalFailureTests(unittest.TestCase):
    def test_final_request_exception_clears_pending_and_poll_closes(self):
        from contextlib import ExitStack
        class FailedLast(FakeConnection):
            def request(self, *args, **kwargs):
                super().request(*args, **kwargs)
                if len(FakeConnection.requests) == 24:
                    raise OSError('synthetic request failure')
        FakeDateTime.current = NOW
        FakeConnection.entered, FakeConnection.release = threading.Event(), threading.Event()
        FakeConnection.requests = []
        FakeConnection.release.set()
        with ExitStack() as stack:
            for p in [patch.object(module, 'datetime', FakeDateTime),
                      patch('socket.socket', side_effect=AssertionError('socket prohibited')),
                      patch('providers.http.client.HTTPSConnection', FailedLast),
                      patch.object(module.tk, 'Tk', Root), patch.object(module.tk, 'BooleanVar', Variable),
                      patch.object(module.tk, 'StringVar', Variable),
                      *[patch.object(module.ttk, name, Widget) for name in ('Frame', 'Label', 'Entry', 'Checkbutton', 'Button')],
                      patch.object(module.Session, 'start_server', return_value=SimpleNamespace(server_port=0))]:
                stack.enter_context(p)
            ui = module.create_window()
            ui['entry'].value = 'FAKE-ONLY'
            ui['confirmed'].set(True)
            ui['start']()
            session = ui['session']()
            for _ in range(23): session.provider.chat(MESSAGE)
            FakeConnection.release.clear()
            FakeConnection.entered.clear()
            errors = []
            def call():
                try: session.provider.chat(MESSAGE)
                except ProviderError as exc: errors.append(exc.code)
            thread = threading.Thread(target=call)
            thread.start()
            try:
                self.assertTrue(FakeConnection.entered.wait(2))
                self.assertTrue(session.status()['final_pending'])
                ui['root'].callback()
                self.assertEqual(session.status()['state'], 'quota_exhausted')
            finally:
                FakeConnection.release.set()
                thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, ['transport_error'])
            self.assertEqual(len(FakeConnection.requests), 24)
            self.assertEqual(session.status()['calls'], 24)
            self.assertFalse(session.status()['final_pending'])
            ui['root'].callback()
            self.assertEqual(session.status()['state'], 'revoked')
