import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from providers import GroqHTTPSJSONTransport
from secure_groq_session import Session
from structured_session_fixture import StructuredSessionFixture

NOW = datetime(2026, 10, 29, 16, tzinfo=timezone.utc)

class BoundaryRegression(unittest.TestCase):
    def test_labelled_liar_cannot_dispatch_https(self):
        requests = []
        class Connection:
            def __init__(self, *a, **kw): pass
            def request(self, *a, **kw): requests.append('sent')
            def getresponse(self): raise OSError('synthetic')
            def close(self): pass
        class Liar:
            test_only = True
            post = GroqHTTPSJSONTransport.post
        with patch('providers.http.client.HTTPSConnection', Connection):
            try:
                session = Session('FAKE', transport=Liar(), clock=lambda: NOW, test_only=True)
                session.provider.chat([{'role': 'user', 'content': 'synthetic'}])
            except Exception:
                pass
        self.assertEqual(requests, [])

    def test_substituted_transport_is_rejected_before_dispatch(self):
        fixture = StructuredSessionFixture(200, b'{}')
        session = Session('FAKE', transport=fixture, clock=lambda: NOW, test_only=True)
        calls = []
        class Liar:
            test_only = True
            def post(self, **kwargs): calls.append('sent')
        session._upstream = Liar()
        with self.assertRaises(Exception):
            session.provider.chat([{'role': 'user', 'content': 'synthetic'}])
        self.assertEqual(calls, [])

    def test_cannot_relabel_test_session_as_real(self):
        fixture = StructuredSessionFixture(200, b'{}')
        session = Session('FAKE', transport=fixture, clock=lambda: NOW, test_only=True)
        with self.assertRaises(AttributeError):
            session.test_only = False

    def test_fixture_method_replacement_is_not_dispatched(self):
        fixture = StructuredSessionFixture(200, b'{}')
        calls = []
        with patch.object(StructuredSessionFixture, 'post', lambda *a, **k: calls.append('unsafe')):
            session = Session('FAKE', transport=fixture, clock=lambda: NOW, test_only=True)
            try:
                session.provider.chat([{'role': 'user', 'content': 'synthetic'}])
            except Exception:
                pass
        self.assertEqual(calls, [])
