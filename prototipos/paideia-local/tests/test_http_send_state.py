"""Loopback-only regression: synthetic key, ledger and HTTPS failures."""
import http.client
import json
import socket
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch
import pytest

import app
import mission_budget
import secure_groq_session as launcher
from backend_services import LocalChatService
from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission
from mission_budget import MissionBudget, load_mission
from tests.test_session_send_boundary import FakeDateTime

CONSENT = {'notice_version': 'paideia-chat-remote-v1', 'accepted_chat_processing': True,
           'purpose': 'free_chat', 'approved_fields': []}
MANIFEST = {'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z',
            'start_utc': '2026-10-29T22:08:31.985015+00:00',
            'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}


@pytest.mark.parametrize(('failure', 'expected'), [('connect', 'not_started'), ('request', 'unknown'), ('response', 'completed'), ('forged', None), ('generic', None), ('status_forged', None)])
def test_trusted_http_transport_failure_reports_state(failure, expected):
    calls = []
    original_socket = socket.socket
    class LoopbackSocket(original_socket):
        def connect(self, address):
            if not isinstance(address, tuple) or address[0] != '127.0.0.1':
                raise AssertionError('external socket blocked')
            return super().connect(address)
        def connect_ex(self, address):
            if not isinstance(address, tuple) or address[0] != '127.0.0.1':
                raise AssertionError('external socket blocked')
            return super().connect_ex(address)
    class FailedConnect:
        def __init__(self, *args, **kwargs): calls.append('connection')
        def connect(self):
            if failure == 'connect': raise OSError('SYNTHETIC-PRIVATE-MARKER')
        def request(self, *args, **kwargs):
            calls.append('request')
            if failure == 'request': raise OSError('SYNTHETIC-PRIVATE-MARKER')
        def getresponse(self):
            raise OSError('SYNTHETIC-PRIVATE-MARKER')
        def close(self): pass
    with tempfile.TemporaryDirectory() as tmp:
        manifest = Path(tmp) / 'MISSION.json'
        manifest.write_text(json.dumps(MANIFEST), encoding='utf8')
        with patch.object(mission_budget, 'NEW_MANIFEST', manifest), \
             patch.object(launcher, 'datetime', FakeDateTime), \
             patch('providers.http.client.HTTPSConnection', FailedConnect), \
             patch.object(socket, 'socket', LoopbackSocket):
            config = load_mission(manifest)
            FakeDateTime.current = config.start
            budget = MissionBudget(config)
            session = launcher.Session('FAKE-KEY-ONLY', mission_budget=budget)
            if failure in ('forged', 'generic'):
                from providers import ProviderError, SendState
                def untrusted(*args, **kwargs):
                    if failure == 'forged':
                        raise ProviderError('transport_error', send_state=SendState.NOT_STARTED)
                    raise RuntimeError('SYNTHETIC-PRIVATE-MARKER')
                session.provider._provider.chat = untrusted
            if failure == 'status_forged':
                from providers import ProviderError, SendState
                def forged_status():
                    raise ProviderError('transport_error', send_state=SendState.NOT_STARTED)
                session.status = forged_status
            policy = AdmissionPolicy(max_concurrent=1, max_queue=0, calls_per_minute=24,
                calls_per_day=24, ticket_ttl_seconds=120, claim_ttl_seconds=120, scope='single-session')
            gate = InterfazChatAdmission(policy, session._clock, budget_state=InMemoryBudgetState.new_empty(scope=policy.scope))
            service = LocalChatService(provider=session.provider, enabled=True, admission=gate)
            server = app.create_server(host='127.0.0.1', port=0, chat_service=service)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
                try:
                    conn.request('POST', '/api/chat', json.dumps({'message':'SYNTHETIC-PRIVATE-MARKER', 'consent':CONSENT}),
                        {'Content-Type':'application/json', 'Origin':f'http://127.0.0.1:{server.server_port}'})
                    response = conn.getresponse()
                    raw = response.read().decode()
                    payload = json.loads(raw)
                finally:
                    conn.close()
                assert response.status == (500 if failure == 'generic' else 503)
                assert payload['error'].get('send_state') == expected
                assert payload['error']['retryable'] is False
                assert 'external_sent' not in raw
                assert 'SYNTHETIC-PRIVATE-MARKER' not in raw and 'FAKE-KEY-ONLY' not in raw
                assert calls == ([] if failure in ('forged', 'generic', 'status_forged') else ['connection'] if failure == 'connect' else ['connection', 'request'])
                assert budget.remaining() == (24 if failure in ('forged', 'generic', 'status_forged') else 23)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(3)
                session.close()
            assert not thread.is_alive()
