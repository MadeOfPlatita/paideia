import socket
import threading
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import providers
from secure_groq_session import _CountedTransport

TOKEN = 'synthetic-boundary-token'
PROMPT = 'synthetic-boundary-prompt'


def make_provider():
    session = SimpleNamespace(_lock=threading.RLock(), _state='active', _calls=0,
        _mission_budget=None, _check=lambda **kw: True, _stop=threading.Event())
    transport = _CountedTransport(session, False, providers.GroqHTTPSJSONTransport())
    return providers.GroqProvider(transport, opt_in=True, environment={providers.API_KEY_ENV: TOKEN})


@pytest.mark.parametrize('phase,code,state,count', [
    ('connect', 'timeout', 'not_started', 0),
    ('request', 'transport_error', 'unknown', 1),
    ('parse', 'invalid_response', 'completed', 1),
    ('429', 'rate_limited', 'completed', 1),
])
def test_counted_real_transport_state_and_safe_boundary_frames(phase, code, state, count):
    calls = []
    class Connection:
        status = 429 if phase == '429' else 200
        def __init__(self, *args, **kwargs): pass
        def connect(self):
            if phase == 'connect': raise TimeoutError('private')
        def request(self, *args, **kwargs):
            calls.append(1)
            if phase == 'request': raise OSError('private')
        def getresponse(self): return self
        def read(self, limit): return b'{}'
        def close(self): pass
    with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), patch.object(providers.http.client, 'HTTPSConnection', Connection):
        with pytest.raises(providers.ProviderError) as caught:
            make_provider().chat([{'role': 'user', 'content': PROMPT}])
    assert (caught.value.code, caught.value.send_state.value, len(calls)) == (code, state, count)
    assert TOKEN not in ''.join(traceback.format_exception(caught.value))
    trace = traceback.TracebackException.from_exception(caught.value, capture_locals=True)
    for frame in trace.stack:
        if frame.filename.endswith(('providers.py', 'secure_groq_session.py')):
            text = repr(frame.locals)
            assert TOKEN not in text and PROMPT not in text


def test_spoofed_wrapper_state_is_not_trusted():
    class Spoof:
        def post(self, **kwargs):
            raise providers.ProviderError('timeout', send_state=providers.SendState.NOT_STARTED)
    p = providers.GroqProvider(Spoof(), opt_in=True, environment={providers.API_KEY_ENV: TOKEN})
    with pytest.raises(providers.ProviderError) as caught:
        p.chat([{'role': 'user', 'content': PROMPT}])
    assert (caught.value.code, caught.value.send_state.value) == ('transport_error', 'unknown')


def test_disabled_is_not_started():
    p = providers.GroqProvider(providers.GroqHTTPSJSONTransport(), opt_in=False)
    with pytest.raises(providers.ProviderError) as caught:
        p.chat([])
    assert caught.value.send_state.value == 'not_started'


@pytest.mark.parametrize('state,calls', [('revoked', 0), ('active', 24)])
def test_counted_preflight_rejection_is_not_started(state, calls):
    provider = make_provider()
    session = provider._transport._session
    session._state, session._calls = state, calls
    with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')):
        with pytest.raises(providers.ProviderError) as caught:
            provider.chat([{'role': 'user', 'content': PROMPT}])
    assert (caught.value.code, caught.value.send_state.value) == ('disabled', 'not_started')
    assert session._calls == calls


def test_swapped_counted_class_property_does_not_leak():
    import secure_groq_session as module
    class Spoof:
        __module__ = 'secure_groq_session'
        @property
        def _binding(self): raise RuntimeError('SPOOF_SECRET_MARKER')
        def post(self, **kwargs): raise providers.ProviderError('timeout', send_state=providers.SendState.NOT_STARTED)
    p = providers.GroqProvider(Spoof(), opt_in=True, environment={providers.API_KEY_ENV: TOKEN})
    with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), patch.object(module, '_CountedTransport', Spoof):
        with pytest.raises(providers.ProviderError) as caught:
            p.chat([{'role': 'user', 'content': PROMPT}])
    assert caught.value.send_state is providers.SendState.UNKNOWN
    assert 'SPOOF_SECRET_MARKER' not in ''.join(traceback.format_exception(caught.value))


def test_mutated_real_post_cannot_spoof_not_started():
    p = make_provider()
    def malicious(self, **kwargs):
        raise providers.ProviderError('timeout', send_state=providers.SendState.NOT_STARTED)
    with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), patch.object(providers.GroqHTTPSJSONTransport, '_post', malicious):
        with pytest.raises(providers.ProviderError) as caught:
            p.chat([{'role': 'user', 'content': PROMPT}])
    assert caught.value.send_state is providers.SendState.UNKNOWN


def test_mutated_counted_post_implementation_is_not_called():
    p = make_provider()
    called = []
    def malicious(self, **kwargs):
        called.append(True)
        raise providers.ProviderError('timeout', send_state=providers.SendState.NOT_STARTED)
    with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), patch.object(_CountedTransport, '_post', malicious):
        with pytest.raises(providers.ProviderError) as caught:
            p.chat([{'role': 'user', 'content': PROMPT}])
    assert not called
    assert caught.value.send_state is providers.SendState.UNKNOWN
