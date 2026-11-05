import threading
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from providers import GroqHTTPSJSONTransport, ProviderError
from secure_groq_session import Session
import secure_groq_session as session_module

NOW = datetime(2026, 10, 29, 16, tzinfo=timezone.utc)
MESSAGE = [{'role': 'user', 'content': 'SYNTHETIC BODY'}]

class TestTransport(GroqHTTPSJSONTransport):
    test_only = True

class _DateTimeMeta(type):
    def __instancecheck__(cls, value):
        return isinstance(value, datetime)

class FakeDateTime(datetime, metaclass=_DateTimeMeta):
    current = NOW
    @classmethod
    def now(cls, tz=None):
        return cls.current

class FakeConnection:
    entered = None
    release = None
    requests = None
    def __init__(self, *args, **kwargs): self.connected = False
    def connect(self):
        self.entered.set()
        if not self.release.wait(3): raise TimeoutError()
        self.connected = True
    def request(self, *args, **kwargs):
        if not self.connected: self.connect()
        self.requests.append('request')
    def getresponse(self):
        class Response:
            status = 200
            def read(self, size):
                return b'{"choices":[{"message":{"role":"assistant","content":"synthetic"},"finish_reason":"stop"}]}'
        return Response()
    def close(self): pass

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        FakeConnection.entered, FakeConnection.release = threading.Event(), threading.Event()
        FakeConnection.requests = []
        FakeDateTime.current = NOW
        for p in (patch.object(session_module, 'datetime', FakeDateTime),
                  patch('socket.socket', side_effect=AssertionError('real socket prohibited'))):
            p.start()
            self.addCleanup(p.stop)

    def test_revoke_while_connecting_prevents_request(self):
        FakeConnection.entered, FakeConnection.release = threading.Event(), threading.Event()
        FakeConnection.requests = []
        session = Session('FAKE-ONLY')
        errors = []
        def call():
            try: session.provider.chat(MESSAGE)
            except ProviderError as e: errors.append(e.code)
        with patch('providers.http.client.HTTPSConnection', FakeConnection):
            thread = threading.Thread(target=call)
            thread.start()
            self.assertTrue(FakeConnection.entered.wait(2))
            session.revoke()
            FakeConnection.release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(FakeConnection.requests, [])
        self.assertEqual(errors, ['transport_error'])
        self.assertEqual(session.status()['calls'], 1)

    def test_deadline_while_connecting_prevents_request(self):
        session = Session('FAKE-ONLY', deadline=NOW + timedelta(seconds=10))
        errors = []
        def call():
            try: session.provider.chat(MESSAGE)
            except ProviderError as e: errors.append(e.code)
        with patch('providers.http.client.HTTPSConnection', FakeConnection):
            thread = threading.Thread(target=call)
            thread.start()
            self.assertTrue(FakeConnection.entered.wait(2))
            FakeDateTime.current += timedelta(seconds=10)
            FakeConnection.release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(FakeConnection.requests, [])
        self.assertEqual(errors, ['transport_error'])
        self.assertEqual(session.status()['state'], 'expired')

    def test_inflight_response_does_not_block_revoke_or_shutdown(self):
        entered, release = threading.Event(), threading.Event()
        class SlowResponse(FakeConnection):
            def getresponse(self):
                entered.set()
                if not release.wait(3): raise TimeoutError()
                return super().getresponse()
        FakeConnection.release.set()
        session = Session('FAKE-ONLY')
        results = []
        with patch('providers.http.client.HTTPSConnection', SlowResponse):
            thread = threading.Thread(target=lambda: results.append(session.provider.chat(MESSAGE)))
            thread.start()
            self.assertTrue(entered.wait(2))
            closer = threading.Thread(target=session.close)
            closer.start()
            closer.join(2)
            self.assertFalse(closer.is_alive())
            release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0].answer, 'synthetic')
        with self.assertRaises(ProviderError): session.provider.chat(MESSAGE)
        self.assertEqual(len(FakeConnection.requests), 1)

    def test_last_slot_sends_and_failure_connect_counts(self):
        FakeConnection.release.set()
        session = Session('FAKE-ONLY')
        with patch('providers.http.client.HTTPSConnection', FakeConnection):
            for _ in range(24): self.assertEqual(session.provider.chat(MESSAGE).answer, 'synthetic')
            with self.assertRaises(ProviderError): session.provider.chat(MESSAGE)
        self.assertEqual(len(FakeConnection.requests), 24)
        self.assertEqual(session.status()['state'], 'quota_exhausted')
        class Failed(FakeConnection):
            def connect(self): raise OSError('SYNTHETIC SECRET OR BODY')
        session = Session('FAKE-ONLY')
        with patch('providers.http.client.HTTPSConnection', Failed):
            with self.assertRaises(ProviderError) as caught: session.provider.chat(MESSAGE)
        self.assertNotIn('SYNTHETIC', str(caught.exception))
        self.assertNotIn('FAKE-ONLY', str(caught.exception))
        self.assertEqual(session.status()['calls'], 1)

    def test_legacy_unguarded_transport_api(self):
        from providers import GROQ_HOST, GROQ_PATH
        FakeConnection.release.set()
        with patch('providers.http.client.HTTPSConnection', FakeConnection):
            response = GroqHTTPSJSONTransport().post(host=GROQ_HOST, path=GROQ_PATH,
                headers={'Authorization': 'Bearer FAKE-ONLY', 'Content-Type': 'application/json',
                         'Accept': 'application/json'}, body=b'{}', timeout=5)
        self.assertEqual(response.status, 200)
        self.assertEqual(len(FakeConnection.requests), 1)

    def test_real_provider_with_mock_connection_never_opens_socket(self):
        FakeConnection.release.set()
        with patch('socket.socket', side_effect=AssertionError('socket prohibited')) as socket_factory, \
             patch('providers.http.client.HTTPSConnection', FakeConnection):
            self.assertEqual(Session('FAKE-ONLY').provider.chat(MESSAGE).answer, 'synthetic')
        socket_factory.assert_not_called()
        self.assertEqual(len(FakeConnection.requests), 1)

    def test_singleflight_serializes_a_failed_request_and_next_attempt(self):
        entered, release = threading.Event(), threading.Event()
        second_started = threading.Event()
        class FirstFails(FakeConnection):
            count = 0
            def getresponse(self):
                type(self).count += 1
                if type(self).count == 1:
                    entered.set()
                    if not release.wait(3): raise TimeoutError()
                    raise OSError('synthetic response failure')
                return super().getresponse()
        FakeConnection.release.set()
        session = Session('FAKE-ONLY')
        errors, results = [], []
        def first():
            try: session.provider.chat(MESSAGE)
            except ProviderError as exc: errors.append(exc.code)
        def second():
            second_started.set()
            results.append(session.provider.chat(MESSAGE))
        with patch('providers.http.client.HTTPSConnection', FirstFails):
            a = threading.Thread(target=first)
            b = threading.Thread(target=second)
            a.start()
            try:
                self.assertTrue(entered.wait(2))
                b.start()
                self.assertTrue(second_started.wait(2))
                self.assertEqual(session.status()['calls'], 1)
                self.assertEqual(len(FakeConnection.requests), 1)
            finally:
                release.set()
                a.join(3)
                if b.ident is not None: b.join(3)
        self.assertFalse(a.is_alive())
        self.assertFalse(b.is_alive())
        self.assertEqual(errors, ['transport_error'])
        self.assertEqual(results[0].answer, 'synthetic')
        self.assertEqual(session.status()['calls'], 2)
        self.assertEqual(len(FakeConnection.requests), 2)

    def test_failure_never_prints_body_or_key(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        class Failed(FakeConnection):
            def connect(self): raise OSError('FAKE-ONLY SYNTHETIC BODY')
        session = Session('FAKE-ONLY')
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), patch('providers.http.client.HTTPSConnection', Failed):
            with self.assertRaises(ProviderError): session.provider.chat(MESSAGE)
        self.assertNotIn('FAKE-ONLY', output.getvalue())
        self.assertNotIn('SYNTHETIC BODY', output.getvalue())
