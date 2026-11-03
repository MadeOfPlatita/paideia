"""Additional session safety checks, fictional credentials only."""
import unittest
from secure_groq_session import Session
from test_secure_groq_session import Clock
from structured_session_fixture import StructuredSessionFixture

class SessionGuardTests(unittest.TestCase):
    def test_last_authorized_attempt_revokes_future_access_and_releases_key_reference(self):
        transport=StructuredSessionFixture(200, b'{}')
        session=Session('SYNTHETIC_NOT_A_REAL_KEY',transport=transport,clock=Clock(),test_only=True)
        for _ in range(24):
            session.transport.post(host='synthetic', path='/', headers={}, body=b'{}', timeout=1)
        self.assertEqual(len(transport.requests),24)
        self.assertEqual(session._environment,{},'Exhausted sessions must not retain a credential until the deadline')
        self.assertEqual(session.status()['state'],'quota_exhausted')
        with self.assertRaises(Exception): session.transport.post()
        self.assertEqual(len(transport.requests),24)
