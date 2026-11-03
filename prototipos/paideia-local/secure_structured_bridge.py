"""Isolated synthetic byte roundtrip; not a real-session integration."""
from groq_structured_adapter import build_structured_request
from providers import ProviderError, TransportResponse, _parse_chat_response
from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
from structured_education import render_selection


class FakeTransport:
    """In-memory fixture only: accepts no endpoint, headers, callback or socket."""
    __slots__ = ('status', 'body', 'fail_tls', 'requests')

    def __init__(self, status, body, *, fail_tls=False):
        if type(status) is not int or type(body) is not bytes or type(fail_tls) is not bool:
            raise ValueError('invalid fixture')
        self.status, self.body, self.fail_tls = status, body, fail_tls
        self.requests = []

    def post(self, body):
        if type(body) is not bytes or type(self.requests) is not list:
            raise ValueError('invalid fixture state')
        self.requests.append(body)
        if self.fail_tls:
            raise RuntimeError('synthetic TLS failure')
        return TransportResponse(status=self.status, body=self.body)


_fake_post = FakeTransport.post
_MISSING = object()


def run_turn(transport, messages, scenario=_MISSING):
    """Single synthetic post; all output is locally rendered or a generic error."""
    try:
        if type(transport) is not FakeTransport:
            raise ValueError('fixture required')
        request = build_structured_request(messages)
        result = _parse_chat_response(_fake_post(transport, request))
        fixture = FakeChatProvider(result, test_only=True)
        selection = StructuredProviderAdapter(fixture, test_only=True).select_education(messages)
        return render_selection(selection, None if scenario is _MISSING else scenario,
                                scenario_present=scenario is not _MISSING)
    except Exception:
        pass
    raise ProviderError('invalid_response')
