import socket
import traceback
from contextlib import contextmanager
from unittest.mock import patch

import pytest
import providers


def test_request_failure_is_unknown_and_sanitized():
    class Connection:
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs): raise OSError('secret-token secret-body')
        def close(self): pass
    with patch.object(socket, 'create_connection', side_effect=AssertionError('network forbidden')), patch.object(providers.http.client, 'HTTPSConnection', Connection):
        with pytest.raises(Exception) as caught:
            providers.GroqHTTPSJSONTransport().post(host=providers.GROQ_HOST, path=providers.GROQ_PATH, headers={'Authorization': 'Bearer secret-token', 'Content-Type': 'application/json', 'Accept': 'application/json'}, body=b'secret-body', timeout=1)
    assert caught.value.send_state.value == 'unknown'
    assert 'secret-token' not in str(caught.value) and 'secret-body' not in str(caught.value)


@pytest.mark.parametrize('status,content,code', [(429, b'{}', 'rate_limited'), (200, b'not-json', 'invalid_response')])
def test_provider_post_success_then_http_or_parse_error(status, content, code):
    class Connection:
        calls = []
        def __init__(self, host, timeout): pass
        def request(self, *args, **kwargs): self.calls.append((args, kwargs))
        def getresponse(self): return self
        def read(self, limit): return content
        def close(self): pass
    Connection.status = status
    provider = providers.GroqProvider(providers.GroqHTTPSJSONTransport(), opt_in=True, environment={providers.API_KEY_ENV: 'synthetic-token'})
    with patch.object(socket, 'create_connection', side_effect=AssertionError('network forbidden')), patch.object(providers.http.client, 'HTTPSConnection', Connection):
        with pytest.raises(providers.ProviderError) as caught:
            provider.chat([{'role': 'user', 'content': 'synthetic prompt'}])
    assert caught.value.code == code
    assert caught.value.send_state.value == 'completed'
    assert len(Connection.calls) == 1


@pytest.mark.parametrize('phase,expected,count', [('connect', 'not_started', 0), ('guard', 'not_started', 0), ('request', 'unknown', 1), ('response', 'completed', 1), ('read', 'completed', 1), ('success', 'completed', 1)])
def test_real_transport_phases_and_single_request(phase, expected, count):
    calls = []
    events = []
    class Connection:
        status = 200
        def __init__(self, host, timeout):
            assert host == providers.GROQ_HOST and timeout == 1
        def connect(self):
            events.append('connect')
            if phase == 'connect': raise OSError('secret-token secret-body')
        def request(self, method, path, body, headers):
            assert events[-1] == 'guard-enter'
            calls.append((method, path, body, headers))
            if phase == 'request': raise OSError('secret-token secret-body')
        def getresponse(self):
            if phase == 'response': raise OSError('secret-token secret-body')
            return self
        def read(self, limit):
            if phase == 'read': raise OSError('secret-token secret-body')
            return b'{}'
        def close(self): events.append('close')
    @contextmanager
    def guard():
        events.append('guard-enter')
        if phase == 'guard': raise RuntimeError('secret-token secret-body')
        yield
        events.append('guard-exit')
    headers = {'Authorization': 'Bearer secret-token', 'Content-Type': 'application/json', 'Accept': 'application/json'}
    payload = b'secret-body'
    transport = providers.GroqHTTPSJSONTransport()
    with patch.object(socket, 'create_connection', side_effect=AssertionError('network forbidden')), patch.object(providers.http.client, 'HTTPSConnection', Connection):
        if phase == 'success':
            result = transport.post(host=providers.GROQ_HOST, path=providers.GROQ_PATH, headers=headers, body=b'secret-body', timeout=1, send_guard=guard)
            assert result.send_state.value == expected
        else:
            with pytest.raises(providers.ProviderError) as caught:
                transport.post(host=providers.GROQ_HOST, path=providers.GROQ_PATH, headers=headers, body=payload, timeout=1, send_guard=guard)
            assert caught.value.send_state.value == expected
            rendered = ''.join(traceback.format_exception(caught.value))
            assert 'secret-token' not in rendered and 'secret-body' not in rendered
    assert len(calls) == count
    if calls:
        assert calls[0] == ('POST', providers.GROQ_PATH, b'secret-body', headers)
    assert events[-1] == 'close'


@pytest.mark.parametrize('phase,expected', [('request', 'unknown'), ('response', 'completed')])
def test_direct_provider_failure_state(phase, expected):
    calls = []
    class Connection:
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs):
            calls.append(1)
            if phase == 'request': raise OSError('sensitive')
        def getresponse(self): raise OSError('sensitive')
        def close(self): pass
    with patch.object(socket, 'create_connection', side_effect=AssertionError('network forbidden')), patch.object(providers.http.client, 'HTTPSConnection', Connection):
        provider = providers.GroqProvider(providers.GroqHTTPSJSONTransport(), opt_in=True, environment={providers.API_KEY_ENV: 'synthetic-token'})
        with pytest.raises(providers.ProviderError) as caught:
            provider.chat([{'role': 'user', 'content': 'synthetic'}])
    assert caught.value.send_state.value == expected
    assert len(calls) == 1


def test_operation_states_do_not_leak():
    class Connection:
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs): raise OSError('request')
        def connect(self): raise OSError('connect')
        def close(self): pass
    @contextmanager
    def guard(): yield
    headers = {'Authorization': 'Bearer synthetic', 'Content-Type': 'application/json', 'Accept': 'application/json'}
    transport = providers.GroqHTTPSJSONTransport()
    with patch.object(socket, 'create_connection', side_effect=AssertionError('network forbidden')), patch.object(providers.http.client, 'HTTPSConnection', Connection):
        with pytest.raises(providers.ProviderError) as first:
            transport.post(host=providers.GROQ_HOST, path=providers.GROQ_PATH, headers=headers, body=b'{}', timeout=1)
        with pytest.raises(providers.ProviderError) as second:
            transport.post(host=providers.GROQ_HOST, path=providers.GROQ_PATH, headers=headers, body=b'{}', timeout=1, send_guard=guard)
    assert first.value.send_state.value == 'unknown'
    assert second.value.send_state.value == 'not_started'
