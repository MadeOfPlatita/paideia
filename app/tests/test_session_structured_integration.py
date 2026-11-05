"""Synthetic local HTTP integration; no external network or real mission."""
import http.client
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import mission_budget
from mission_budget import MissionBudget, load_mission
from secure_groq_session import Session
from structured_session_fixture import StructuredSessionFixture
import domain
CONSENT = {'notice_version':'paideia-chat-remote-v1', 'accepted_chat_processing':True, 'purpose':'free_chat', 'approved_fields':[]}
SCENARIO = {'principal':'123456.78', 'annual_rate_percent':'7.83', 'years':13, 'monthly_contribution':'234.56', 'method':'simple', 'inflation_percent':'1.37'}

class StructuredSessionIntegration(unittest.TestCase):
    def test_invalid_http_responses_complete_admission_without_retry(self):
        from backend_services import LocalChatService
        from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission
        from test_backend_integration import running_server, request
        valid = '{"version":"paideia-education-v1","intent":"explain","claim_ids":["risk"]}'
        invalid = [valid[:-1] + ',"answer":"SYNTHETIC_SECRET"}',
                   valid.replace('"risk"', '"unknown"'),
                   valid.replace('"intent":"explain"', '"intent":"explain","intent":"calculate"')]
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema':'paideia-mission.v1', 'mission_id':'paideia-ia-20261029T220831Z', 'start_utc':'2026-10-29T22:08:31.985015+00:00', 'deadline_utc':'2026-10-29T23:08:31.985015+00:00', 'max_external_attempts':24}), encoding='utf8')
            def wrapped(content):
                return json.dumps({'choices':[{'finish_reason':'stop', 'message':{'role':'assistant', 'content':content}}]}).encode()
            fixture = StructuredSessionFixture(200, wrapped(invalid[0]), outcomes=tuple((200, wrapped(value)) for value in invalid))
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                now = config.start + timedelta(seconds=1)
                budget = MissionBudget(config)
                session = Session('FAKE-KEY-ONLY', test_only=True, transport=fixture, clock=lambda:now, mission_budget=budget)
                gate = InterfazChatAdmission(AdmissionPolicy(1, 0, 24, 24, 120, 120, scope='synthetic'), lambda:now,
                    budget_state=InMemoryBudgetState.new_empty(scope='synthetic'))
                service = LocalChatService(provider=session.provider, enabled=True, test_only=True, admission=gate, structured_session_test_only=True)
                try:
                    with running_server(chat_service=service) as server:
                        for index in range(len(invalid)):
                            status, payload = request(server, '/api/chat', {'message':'synthetic', 'consent':CONSENT, 'scenario':SCENARIO})
                            self.assertEqual(status, 502)
                            self.assertEqual(payload['error']['code'], 'CHAT_STRUCTURED_INVALID_RESPONSE')
                            self.assertNotIn('SYNTHETIC_SECRET', str(payload))
                            self.assertEqual(len(fixture.requests), index + 1)
                            self.assertEqual(gate.status()['active'], 0)
                    self.assertEqual(budget.remaining(), 21)
                finally:
                    session.close()
                with MissionBudget(config) as reopened:
                    self.assertEqual(reopened.remaining(), 21)

    def test_http_admission_durable_mission_structured_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema':'paideia-mission.v1', 'mission_id':'paideia-ia-20261029T220831Z', 'start_utc':'2026-10-29T22:08:31.985015+00:00', 'deadline_utc':'2026-10-29T23:08:31.985015+00:00', 'max_external_attempts':24}), encoding='utf8')
            selection = {'version':'paideia-education-v1', 'intent':'calculate', 'claim_ids':['simulation']}
            body = json.dumps({'choices':[{'finish_reason':'stop', 'message':{'role':'assistant', 'content':json.dumps(selection)}}]}).encode()
            fixture = StructuredSessionFixture(200, body)
            captured = fixture.requests
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                budget = MissionBudget(config)
                session = Session('FAKE-KEY-ONLY', test_only=True, transport=fixture, clock=lambda: config.start + timedelta(seconds=1), mission_budget=budget)
                try:
                    server = session.start_server(port=0, output=Path(tmp)/'status.json', structured_test_only=True)
                    conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
                    try:
                        from structured_provider_adapter import FakeChatProvider
                        with patch.object(FakeChatProvider, '__init__', side_effect=AssertionError('unexpected fake construction')) as constructor:
                            conn.request('POST', '/api/chat', json.dumps({'message':'synthetic calculate', 'consent':CONSENT, 'scenario':SCENARIO}), {'Content-Type':'application/json', 'Origin':f'http://127.0.0.1:{server.server_port}'})
                            response = conn.getresponse()
                            payload = json.loads(response.read())
                            constructor.assert_not_called()
                    finally: conn.close()
                    self.assertEqual(response.status, 200, payload)
                    self.assertEqual(payload['structured_education']['calculation']['data'], domain.calculate_scenario(SCENARIO))
                    self.assertEqual(budget.remaining(), 23)
                    self.assertEqual(len(captured), 1)
                    request = json.loads(captured[0])
                    self.assertFalse(request['response_format']['json_schema']['strict'])
                    self.assertNotIn('scenario', captured[0].decode())
                    for literal in ('123456.78', '7.83', '234.56', '1.37'):
                        self.assertNotIn(literal, captured[0].decode())
                    self.assertEqual(payload['provider_mode'], 'test_only')
                    self.assertFalse(payload['external_sent'])
                finally:
                    session.close()
                with MissionBudget(config) as reopened:
                    self.assertEqual(reopened.remaining(), 23)
