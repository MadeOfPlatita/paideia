"""The send guard must run before any TCP/TLS connection is created."""
import json
import socket
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import mission_budget
import providers
import secure_groq_session as session_module
from mission_budget import MissionBudget, load_mission
from secure_groq_session import Session
from tests.test_session_send_boundary import FakeDateTime

LEGACY = {
    'schema': 'paideia-mission.v1',
    'mission_id': 'paideia-ia-20261029T220831Z',
    'start_utc': '2026-10-29T22:08:31.985015+00:00',
    'deadline_utc': '2026-10-29T23:08:31.985015+00:00',
    'max_external_attempts': 24,
}
MESSAGE = [{'role': 'user', 'content': 'SYNTHETIC-GUARD-BODY'}]
BODY = json.dumps({
    'choices': [{'message': {'role': 'assistant', 'content': 'ok'}, 'finish_reason': 'stop'}],
}).encode('utf8')


class GuardBeforeConnectTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.manifest = self.directory / 'MISSION.json'
        self.manifest.write_text(json.dumps(LEGACY), encoding='utf8')
        self.patch = patch.object(mission_budget, 'NEW_MANIFEST', self.manifest)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.config = load_mission(self.manifest)
        self.budget = MissionBudget(self.config)
        self.addCleanup(self.budget.close)

    def test_guard_failure_never_constructs_a_connection(self):
        FakeDateTime.current = self.config.start + timedelta(seconds=1)
        original = self.budget.reserve

        def reserve(now=None):
            remaining = original(now)
            FakeDateTime.current = self.config.cutoff
            return remaining

        self.budget.reserve = reserve
        created = []

        class ForbiddenConnection:
            def __init__(self, *args, **kwargs):
                created.append(True)
                raise AssertionError('TCP connection must not start before the guard')

        with patch.object(session_module, 'datetime', FakeDateTime), \
             patch.object(socket, 'socket', side_effect=AssertionError('raw socket forbidden')), \
             patch.object(providers.http.client, 'HTTPSConnection', ForbiddenConnection):
            session = Session('FAKE-GUARD-KEY', mission_budget=self.budget)
            with self.assertRaises(providers.ProviderError):
                session.provider.chat(MESSAGE)
        self.assertEqual(created, [])
        self.assertEqual(session.status()['calls'], 1)
        session.close()
        with MissionBudget(self.config) as reopened:
            self.assertEqual(reopened.remaining(), 23)

    def test_guard_passes_then_exactly_one_connection_and_request(self):
        created, requests = [], []
        FakeDateTime.current = self.config.start + timedelta(seconds=1)

        class Connection:
            status = 200
            def __init__(self, *args, **kwargs):
                created.append(True)
            def connect(self):
                pass
            def request(self, *args, **kwargs):
                requests.append(True)
            def getresponse(self):
                return self
            def read(self, limit):
                return BODY
            def close(self):
                pass

        with patch.object(session_module, 'datetime', FakeDateTime), \
             patch.object(socket, 'socket', side_effect=AssertionError('raw socket forbidden')), \
             patch.object(providers.http.client, 'HTTPSConnection', Connection):
            session = Session('FAKE-GUARD-KEY', mission_budget=self.budget)
            result = session.provider.chat(MESSAGE)
        self.assertEqual(result.answer, 'ok')
        self.assertEqual((len(created), len(requests)), (1, 1))
        self.assertEqual(session.status()['calls'], 1)
        session.close()
        with MissionBudget(self.config) as reopened:
            self.assertEqual(reopened.remaining(), 23)

    def test_mutated_upstream_is_rejected_before_any_reservation(self):
        def malicious(self, **kwargs):
            raise AssertionError('mutated transport must not run')

        FakeDateTime.current = self.config.start + timedelta(seconds=1)
        with patch.object(session_module, 'datetime', FakeDateTime), \
             patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')), \
             patch.object(providers.GroqHTTPSJSONTransport, '_post', malicious):
            session = Session('FAKE-GUARD-KEY', mission_budget=self.budget)
            with self.assertRaises(providers.ProviderError):
                session.transport.post(
                    host=providers.GROQ_HOST, path=providers.GROQ_PATH,
                    headers={'Authorization': 'Bearer FAKE-GUARD-KEY',
                             'Content-Type': 'application/json', 'Accept': 'application/json'},
                    body=b'{}', timeout=1,
                )
        self.assertEqual(session.status()['calls'], 0)
        session.close()
        with MissionBudget(self.config) as reopened:
            self.assertEqual(reopened.remaining(), 24)


if __name__ == '__main__':
    unittest.main()
