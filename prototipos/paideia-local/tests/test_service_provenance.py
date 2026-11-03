import http.client
import socket
import unittest
from unittest.mock import patch

from backend_services import LocalChatService, ServiceProblem
from providers import GroqProvider, GroqHTTPSJSONTransport, ChatResult
from structured_provider_adapter import FakeChatProvider

CONSENT = {'notice_version': 'paideia-chat-remote-v1', 'accepted_chat_processing': True,
           'purpose': 'free_chat', 'approved_fields': []}
PAYLOAD = {'message': 'Pregunta ficticia', 'consent': CONSENT}

class ProvenanceTests(unittest.TestCase):
    def test_real_and_impostor_rejected_before_fake_https_post(self):
        posts = []
        class Connection:
            def __init__(self, *a, **kw): pass
            def request(self, *a, **kw): posts.append(a)
            def getresponse(self):
                class Response:
                    status = 200
                    def read(self, limit):
                        return b'{"choices":[{"message":{"role":"assistant","content":"ficticio"},"finish_reason":"stop"}]}'
                return Response()
            def close(self): pass
        class Impostor:
            test_only = True
            def chat(self, messages):
                return real.chat(messages)
        real = GroqProvider(GroqHTTPSJSONTransport(), opt_in=True,
                            environment={'GROQ_API_KEY': 'FAKE-KEY-ONLY'})
        with patch.object(http.client, 'HTTPSConnection', Connection), patch.object(socket, 'socket', side_effect=AssertionError('network blocked')):
            self.assertEqual(Impostor().chat([{'role': 'user', 'content': 'ficticio'}]).answer, 'ficticio')
            self.assertEqual(len(posts), 1)
            posts.clear()
            for provider in (real, Impostor()):
                with self.subTest(provider=type(provider).__name__):
                    with self.assertRaises(ValueError):
                        LocalChatService(provider=provider, enabled=True, test_only=True)
            self.assertEqual(posts, [])

    def test_actual_real_session_facade_cannot_be_mislabeled(self):
        from datetime import datetime, timezone
        import secure_groq_session
        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 29, 16, 0, tzinfo=timezone.utc)
        with patch.object(secure_groq_session, 'datetime', FrozenDateTime), patch.object(socket, 'socket', side_effect=AssertionError('network blocked')):
            session = secure_groq_session.Session('FAKE-KEY-ONLY', deadline=FrozenDateTime(2026, 10, 29, 17, 0, tzinfo=timezone.utc))
            with self.assertRaises(ValueError):
                LocalChatService(provider=session.provider, enabled=True, test_only=True)
            self.assertEqual(session._calls, 0)

    def test_closed_fixture_uses_pinned_chat_and_client_cannot_set_metadata(self):
        fixture = FakeChatProvider(ChatResult('Respuesta ficticia', None, (), 'stop'), test_only=True)
        service = LocalChatService(provider=fixture, enabled=True, test_only=True)
        with patch.object(FakeChatProvider, 'chat', side_effect=AssertionError('not dispatched')):
            result = service.chat(PAYLOAD)
        self.assertFalse(result['external_sent'])
        self.assertEqual(result['provider_mode'], 'test_only')
        for field in ('external_sent', 'provider_mode', 'test_only'):
            with self.assertRaises(ServiceProblem):
                service.chat({**PAYLOAD, field: False})
        self.assertEqual(fixture.calls, 1)

    def test_errors_do_not_assert_external_sent(self):
        fixture = FakeChatProvider(ChatResult('Respuesta ficticia', None, (), 'stop'), test_only=True)
        service = LocalChatService(provider=fixture, enabled=True, test_only=True)
        with self.assertRaises(ServiceProblem) as caught:
            service.chat({'message': 'sin consentimiento'})
        self.assertFalse(hasattr(caught.exception, 'external_sent'))
        self.assertIsNone(caught.exception.send_state)
        self.assertEqual(fixture.calls, 0)

    def test_http_fixture_success_and_consent_error(self):
        from test_backend_integration import running_server, request
        fixture = FakeChatProvider(ChatResult('Respuesta ficticia', None, (), 'stop'), test_only=True)
        service = LocalChatService(provider=fixture, enabled=True, test_only=True)
        with running_server(chat_service=service) as server:
            status, body = request(server, '/api/chat', PAYLOAD)
            self.assertEqual(status, 200)
            self.assertIs(body['external_sent'], False)
            status, body = request(server, '/api/chat', {'message': 'sin consentimiento'})
            self.assertEqual(status, 403)
            self.assertNotIn('external_sent', body)
            self.assertNotIn('send_state', body['error'])
        self.assertEqual(fixture.calls, 1)
