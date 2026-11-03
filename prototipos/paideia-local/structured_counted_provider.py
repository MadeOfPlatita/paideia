"""Synthetic counted-transport boundary; never an operational session provider."""
from groq_structured_adapter import build_structured_request
from providers import GROQ_HOST, GROQ_PATH, ProviderError, TransportResponse, _parse_chat_response
from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter


class FakeCountedTransport:
    """In-memory only. No callbacks, URL configuration, sockets or credentials."""
    __slots__ = ('status', 'body', 'failure', 'revoked', 'reservations', 'requests')

    def __init__(self, status, body, *, failure=False, revoked=False):
        if type(status) is not int or type(body) is not bytes or type(failure) is not bool or type(revoked) is not bool:
            raise ValueError('invalid fixture')
        self.status, self.body, self.failure, self.revoked = status, body, failure, revoked
        self.reservations, self.requests = 0, []

    def post(self, *, host, path, headers, body, timeout):
        if self.revoked:
            raise RuntimeError('fixture revoked')
        self.reservations += 1
        self.requests.append({'host': host, 'path': path, 'headers': headers, 'body': body, 'timeout': timeout})
        if self.failure:
            raise RuntimeError('fixture TLS failure')
        return TransportResponse(self.status, self.body)


_fake_post = FakeCountedTransport.post


class StructuredCountedProvider:
    __slots__ = ('_transport',)

    def __init__(self, transport):
        if type(transport) is not FakeCountedTransport:
            raise ProviderError('disabled')
        self._transport = transport

    def select_education(self, messages):
        result, sent_state = _select_fake(self._transport, messages)
        # Do not retain the provider, its fake transport, or inputs in this
        # exception frame. The worker has returned and no exception is chained.
        del self, messages
        if sent_state is None:
            return result
        error = ProviderError('invalid_response')
        error.sent_state = sent_state
        raise error from None


def _select_fake(transport, messages):
    posted = False
    try:
        if type(transport) is not FakeCountedTransport:
            raise ValueError('invalid fixture')
        body = build_structured_request(messages)
        posted = True
        response = _fake_post(transport, host=GROQ_HOST, path=GROQ_PATH,
                              headers={'Authorization': 'Bearer test-only',
                                       'Content-Type': 'application/json', 'Accept': 'application/json'},
                              body=body, timeout=15.0)
        result = _parse_chat_response(response)
        fixture = FakeChatProvider(result, test_only=True)
        return StructuredProviderAdapter(fixture, test_only=True).select_education(messages), None
    except Exception:
        # Post entry is conservative even for a revoked in-memory fixture.
        return None, 'unknown' if posted else 'not_started'


def create_session_provider(*args, **kwargs):
    """No activation route exists in this offline artifact."""
    raise ProviderError('disabled')
