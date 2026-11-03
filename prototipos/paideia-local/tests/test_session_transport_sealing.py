import threading
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from secure_groq_session import Session
from structured_session_fixture import StructuredSessionFixture

NOW = datetime(2026, 10, 29, 16, tzinfo=timezone.utc)
BODY = b'{"choices":[{"message":{"role":"assistant","content":"synthetic"},"finish_reason":"stop"}]}'

class SealingTests(unittest.TestCase):
    def test_requests_swap_while_connecting_never_calls_attacker(self):
        fake = StructuredSessionFixture(200, BODY)
        fake.connect_entered, fake.connect_release = threading.Event(), threading.Event()
        session = Session('FAKE', test_only=True, transport=fake, clock=lambda: NOW)
        attacks = []
        class Evil(list):
            def append(self, value):
                attacks.append('network')
                import socket
                socket.create_connection(('example.invalid', 443))
        errors = []
        def run():
            try: session.provider.chat([{'role':'user','content':'synthetic'}])
            except Exception as e: errors.append(e)
        with patch('socket.create_connection') as network:
            thread = threading.Thread(target=run); thread.start()
            self.assertTrue(fake.connect_entered.wait(2))
            fake.requests = Evil()
            fake.connect_release.set(); thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(attacks, [])
            network.assert_not_called()

    def test_mutable_mode_and_upstream_do_not_change_transport(self):
        fake = StructuredSessionFixture(200, BODY)
        session = Session('FAKE', test_only=True, transport=fake, clock=lambda: NOW)
        class Evil:
            def post(self, **kwargs):
                import socket
                socket.create_connection(('example.invalid', 443))
                raise RuntimeError('network')
        fake.connect_entered, fake.connect_release = threading.Event(), threading.Event()
        errors = []
        def run():
            try: session.provider.chat([{'role':'user','content':'synthetic'}])
            except Exception as e: errors.append(e)
        with patch('socket.create_connection') as network:
            thread = threading.Thread(target=run); thread.start()
            self.assertTrue(fake.connect_entered.wait(2))
            session._test_only = False
            session._upstream = Evil()
            fake.connect_release.set(); thread.join(3)
            self.assertFalse(thread.is_alive())
            network.assert_not_called()
            self.assertEqual(errors, [])
            session.provider.chat([{'role':'user','content':'synthetic'}])
            network.assert_not_called()
        self.assertTrue(session.test_only)
        with self.assertRaises(AttributeError):
            session.transport._binding = (False, Evil())

    def test_sequence_survives_request_log_mutation(self):
        fake = StructuredSessionFixture(200, BODY, outcomes=((200, BODY), (429, b'{}')))
        session = Session('FAKE', test_only=True, transport=fake, clock=lambda: NOW)
        first = session.transport.post(host='x', path='/', headers={}, body=b'1', timeout=1)
        fake.requests.clear()
        fake.requests = []
        second = session.transport.post(host='x', path='/', headers={}, body=b'2', timeout=1)
        self.assertEqual((first.status, second.status), (200, 429))
        with self.assertRaisesRegex(ValueError, 'outcomes exhausted'):
            session.transport.post(host='x', path='/', headers={}, body=b'3', timeout=1)

    def test_resetting_sequence_does_not_replay_outcomes(self):
        fake = StructuredSessionFixture(200, BODY, outcomes=((200, BODY), (429, b'{}')))
        session = Session('FAKE', test_only=True, transport=fake, clock=lambda: NOW)
        session.transport.post(host='x', path='/', headers={}, body=b'1', timeout=1)
        fake._sequence = 0
        second = session.transport.post(host='x', path='/', headers={}, body=b'2', timeout=1)
        self.assertEqual(second.status, 429)

    def test_replaced_lock_never_invokes_callback_or_network(self):
        fake = StructuredSessionFixture(200, BODY)
        session = Session('FAKE', test_only=True, transport=fake, clock=lambda: NOW)
        called = []
        class EvilLock:
            def __enter__(self):
                called.append(True)
                import socket
                socket.create_connection(('example.invalid', 443))
            def __exit__(self, *args):
                pass
        fake._sequence_lock = EvilLock()
        with patch('socket.create_connection') as network:
            try:
                session.transport.post(host='x', path='/', headers={}, body=b'1', timeout=1)
            except ValueError:
                pass
            self.assertEqual(called, [])
            network.assert_not_called()

    def test_sequential_fixture_responses(self):
        fake = StructuredSessionFixture(200, BODY, outcomes=((200, BODY), (429, b'{}')))
        session = Session('FAKE', test_only=True, transport=fake, clock=lambda: NOW)
        first = session.transport.post(host='x', path='/', headers={}, body=b'1', timeout=1)
        second = session.transport.post(host='x', path='/', headers={}, body=b'2', timeout=1)
        self.assertEqual((first.status, second.status), (200, 429))
