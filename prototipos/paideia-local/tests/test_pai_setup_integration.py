"""Pai's ordinary application service must keep its historical chat startup.

The counted night mission is a separate explicit opt-in.  Its integration is
exercised only with a closed synthetic transport and an injected clock.  No
real key, network or profile state is used.
"""
import json
import os
import tempfile
import unittest
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import app
import mission_budget
import pai_setup
import secure_groq_session as session_module
from backend_services import CHAT_NOTICE_VERSION, LocalChatService, ServiceProblem
from mission_budget import MissionBudget, MissionConfig, load_mission
from secure_groq_session import _SingleFlightProvider
from structured_session_fixture import StructuredSessionFixture
from tests.test_session_send_boundary import FakeDateTime

NIGHT = {
    'schema': 'paideia-night-mission.v1',
    'mission_id': 'paideia-night-20261104',
    'start_utc': '2026-11-04T00:00:00Z',
    'deadline_utc': '2026-11-04T08:00:00Z',
    'max_external_attempts': 20,
}
START = datetime(2026, 11, 4, 0, 0, tzinfo=timezone.utc)
CUTOFF = datetime(2026, 11, 4, 8, 0, tzinfo=timezone.utc)
KEY = 'FAKE-SETUP-KEY-NEVER-PERSIST'
PROMPT = 'SYNTHETIC-SETUP-PROMPT-NEVER-PERSIST'
BODY = json.dumps({
    'choices': [{'message': {'role': 'assistant', 'content': 'Respuesta sintética.'},
                 'finish_reason': 'stop'}],
}).encode('utf8')
CONSENT = {
    'notice_version': CHAT_NOTICE_VERSION,
    'accepted_chat_processing': True,
    'purpose': 'free_chat',
    'approved_fields': [],
}


class PlainFixtureTransport:
    """Adapt the closed fixture to the historical provider transport shape.

    The ordinary provider does not pass the session's ``send_guard``; the
    fixture still receives one so the same closed in-memory transport is used.
    """

    def __init__(self, fixture):
        self.fixture = fixture

    def post(self, *, host, path, headers, body, timeout):
        return self.fixture.post(
            host=host,
            path=path,
            headers=headers,
            body=body,
            timeout=timeout,
            send_guard=nullcontext,
        )


def write_state(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory / 'MISSION.json'
    manifest.write_text(json.dumps(NIGHT, indent=2) + '\n', encoding='utf8')
    (directory / 'MISSION.seal').write_text(json.dumps({
        'schema': 'paideia-night-ledger-seal.v1',
        'manifest_sha256': mission_budget.night_manifest_digest(NIGHT),
        'mission_id': NIGHT['mission_id'],
        'state': 'uninitialized',
    }, separators=(',', ':')), encoding='utf8')
    return manifest


class SetupIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.manifest = write_state(self.directory)
        self.patch = patch.object(mission_budget, 'NIGHT_MANIFEST', self.manifest)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.config = load_mission(self.manifest)
        self.clock = lambda: START + timedelta(seconds=1)

    def environment(self, *, key=KEY, opt_in='1', night='0'):
        return patch.dict(os.environ, {
            'PAIDEIA_GROQ_ENABLED': opt_in,
            'GROQ_API_KEY': key,
            pai_setup.NIGHT_OPT_IN_ENV: night,
        }, clear=False)

    def assert_disabled(self, service):
        self.assertIs(type(service), LocalChatService)
        self.assertEqual(service.status()['status'], 'not_configured')
        self.assertFalse(hasattr(service, '_mission_session'))

    def assert_no_secret_in_state(self):
        for path in self.directory.rglob('*'):
            if path.is_file():
                text = path.read_text(encoding='utf8', errors='ignore')
                self.assertNotIn(KEY, text, path)
                self.assertNotIn(PROMPT, text, path)

    # --- Historical ordinary route -------------------------------------

    def test_historical_route_builds_without_mission_and_keeps_historical_values(self):
        fixture = StructuredSessionFixture(200, BODY)
        transport = PlainFixtureTransport(fixture)
        with self.environment(night='0'), \
             patch.object(mission_budget, 'NIGHT_MANIFEST', self.directory / 'absent' / 'MISSION.json'), \
             patch.object(pai_setup, 'DOCUMENT_MANIFEST', self.directory / 'absent-docs' / 'MISSION.json'), \
             patch.object(pai_setup, 'GroqHTTPSJSONTransport', return_value=transport), \
             patch.object(pai_setup, 'Session') as session_class:
            service = pai_setup.build_chat_service(
                repository=object(), comparison_service=object())
            session_class.assert_not_called()
            self.assertIs(type(service), LocalChatService)
            self.assertEqual(service.status()['status'], 'configured_not_verified')
            self.assertFalse(service._test_only)
            self.assertTrue(service.status()['capabilities']['context'])
            self.assertTrue(service.status()['capabilities']['catalogue'])
            self.assertEqual(service.quota()['calls_per_minute'], 6)
            self.assertEqual(service.quota()['calls_per_day'], 60)
            answer = service.chat({'message': PROMPT, 'consent': dict(CONSENT)})
            self.assertEqual(answer['answer'], 'Respuesta sintética.')
            self.assertEqual(len(fixture.requests), 1)
        self.assertFalse((self.directory / 'mission-ledger.json').exists())
        self.assertFalse((self.directory / 'mission-ledger.json.lock').exists())

    def test_historical_route_ignores_mission_cutoff_and_never_reads_mission_state(self):
        fixture = StructuredSessionFixture(200, BODY)
        transport = PlainFixtureTransport(fixture)
        with self.environment(night='0'), \
             patch.object(pai_setup, '_current_time', lambda now=None: CUTOFF + timedelta(seconds=1)), \
             patch.object(pai_setup, '_mission_config') as mission_config, \
             patch.object(pai_setup, 'GroqHTTPSJSONTransport', return_value=transport), \
             patch.object(pai_setup, 'Session') as session_class:
            service = pai_setup.build_chat_service()
            mission_config.assert_not_called()
            session_class.assert_not_called()
            self.assertIs(type(service), LocalChatService)
            self.assertEqual(service.status()['status'], 'configured_not_verified')
            self.assertFalse(service._test_only)
            answer = service.chat({'message': PROMPT, 'consent': dict(CONSENT)})
            self.assertEqual(answer['answer'], 'Respuesta sintética.')
            self.assertEqual(len(fixture.requests), 1)

    def test_historical_route_stays_disabled_without_key_or_opt_in(self):
        with self.environment(key='', opt_in='1'), \
             patch.object(pai_setup.GroqProvider, 'from_environment') as ordinary:
            self.assert_disabled(pai_setup.build_chat_service())
            ordinary.assert_not_called()
        with self.environment(key=KEY, opt_in='0'), \
             patch.object(pai_setup.GroqProvider, 'from_environment') as ordinary:
            self.assert_disabled(pai_setup.build_chat_service())
            ordinary.assert_not_called()

    def test_chat_enabled_is_historical_environment_only(self):
        (self.directory / 'MISSION.seal').unlink()
        with self.environment(night='0'):
            self.assertTrue(pai_setup.chat_enabled())
        with self.environment(key='', opt_in='1', night='0'):
            self.assertFalse(pai_setup.chat_enabled())
        with self.environment(key=KEY, opt_in='0', night='1'):
            self.assertFalse(pai_setup.chat_enabled())

    def test_app_server_keeps_the_historical_ordinary_route(self):
        fixture = StructuredSessionFixture(200, BODY)
        transport = PlainFixtureTransport(fixture)
        with self.environment(night='0'), \
             patch.object(mission_budget, 'NIGHT_MANIFEST', self.directory / 'absent' / 'MISSION.json'), \
             patch.object(pai_setup, 'DOCUMENT_MANIFEST', self.directory / 'absent-docs' / 'MISSION.json'), \
             patch.object(pai_setup, 'GroqHTTPSJSONTransport', return_value=transport):
            server = app.create_server(port=0, repository=object(), comparison_service=object())
            try:
                service = server.chat_service
                self.assertIs(type(service), LocalChatService)
                self.assertEqual(service.status()['status'], 'configured_not_verified')
                self.assertFalse(service._test_only)
                self.assertFalse(hasattr(service, '_mission_session'))
                answer = service.chat({'message': PROMPT, 'consent': dict(CONSENT)})
                self.assertEqual(answer['answer'], 'Respuesta sintética.')
                self.assertEqual(len(fixture.requests), 1)
            finally:
                server.server_close()

    # --- Counted night mission is explicit and isolated -----------------

    def test_night_route_is_not_selected_by_environment_or_default(self):
        fixture = StructuredSessionFixture(200, BODY)
        absent = self.directory / 'absent' / 'MISSION.json'
        absent_docs = self.directory / 'absent-docs' / 'MISSION.json'
        with self.environment(night='1'), \
             patch.object(mission_budget, 'NIGHT_MANIFEST', absent), \
             patch.object(pai_setup, 'DOCUMENT_MANIFEST', absent_docs), \
             patch.object(pai_setup, 'GroqHTTPSJSONTransport', return_value=PlainFixtureTransport(fixture)), \
             patch.object(pai_setup, 'Session') as session_class, \
             patch.object(pai_setup, '_historical_chat_service',
                          wraps=pai_setup._historical_chat_service) as historical:
            default_service = pai_setup.build_chat_service()
            self.assertIs(type(default_service), LocalChatService)
            self.assertFalse(default_service._test_only)
            self.assertFalse(hasattr(default_service, '_mission_session'))
            self.assertEqual(default_service.status()['status'], 'configured_not_verified')
            self.assertEqual(historical.call_count, 1)
            session_class.assert_not_called()

            historical.reset_mock()
            night_service = pai_setup.build_chat_service(night_mission=True)
            self.assert_disabled(night_service)
            historical.assert_not_called()
            session_class.assert_not_called()
            self.assertEqual(fixture.requests, [])

    def test_night_route_without_seal_disables_and_never_falls_back(self):
        (self.directory / 'MISSION.seal').unlink()
        fixture = StructuredSessionFixture(200, BODY)
        with self.environment(night='1'), \
             patch.object(pai_setup, 'Session') as session_class, \
             patch.object(pai_setup.GroqProvider, 'from_environment') as ordinary:
            isolated = pai_setup.build_chat_service(
                night_mission=True, test_only=True, transport=fixture,
                clock=self.clock, mission_config=self.config)
            self.assert_disabled(isolated)
            with self.assertRaises(ServiceProblem):
                isolated.chat({'message': PROMPT, 'consent': dict(CONSENT)})
            self.assertEqual(fixture.requests, [])
            session_class.assert_not_called()
            ordinary.assert_not_called()

            production = pai_setup.build_chat_service(night_mission=True)
            self.assert_disabled(production)
            session_class.assert_not_called()
            ordinary.assert_not_called()
        self.assertFalse((self.directory / 'mission-ledger.json').exists())
        self.assertFalse((self.directory / 'mission-ledger.json.lock').exists())

    def test_night_route_outside_its_window_disables_and_never_falls_back(self):
        fixture = StructuredSessionFixture(200, BODY)
        with self.environment(night='1'), \
             patch.object(pai_setup, 'Session') as session_class, \
             patch.object(pai_setup.GroqProvider, 'from_environment') as ordinary:
            for moment in (CUTOFF, START - timedelta(seconds=1)):
                with self.subTest(moment=moment):
                    service = pai_setup.build_chat_service(
                        night_mission=True, test_only=True, transport=fixture,
                        clock=lambda moment=moment: moment, mission_config=self.config)
                    self.assert_disabled(service)
                    with self.assertRaises(ServiceProblem):
                        service.chat({'message': PROMPT, 'consent': dict(CONSENT)})
                    self.assertEqual(fixture.requests, [])
                    session_class.assert_not_called()
                    ordinary.assert_not_called()
            with patch.object(pai_setup, '_current_time', lambda now=None: CUTOFF):
                production = pai_setup.build_chat_service(night_mission=True)
                self.assert_disabled(production)
                session_class.assert_not_called()
                ordinary.assert_not_called()
        self.assertFalse((self.directory / 'mission-ledger.json').exists())
        self.assertFalse((self.directory / 'mission-ledger.json.lock').exists())

    def test_night_route_at_exhausted_cap_disables_and_never_falls_back(self):
        with MissionBudget(self.config) as budget:
            for _ in range(self.config.cap):
                budget.reserve(self.clock())
        fixture = StructuredSessionFixture(200, BODY)
        with self.environment(night='1'), \
             patch.object(pai_setup, 'Session') as session_class, \
             patch.object(pai_setup.GroqProvider, 'from_environment') as ordinary:
            service = pai_setup.build_chat_service(
                night_mission=True, test_only=True, transport=fixture,
                clock=self.clock, mission_config=self.config)
            self.assert_disabled(service)
            with self.assertRaises(ServiceProblem):
                service.chat({'message': PROMPT, 'consent': dict(CONSENT)})
            self.assertEqual(fixture.requests, [])
            session_class.assert_not_called()
            ordinary.assert_not_called()

    def test_night_route_counts_each_round_through_the_mission_ledger(self):
        fixture = StructuredSessionFixture(200, BODY)
        with self.environment(night='1'):
            service = pai_setup.build_chat_service(
                night_mission=True, test_only=True, transport=fixture,
                clock=self.clock, mission_config=self.config)
        try:
            self.assertIs(type(service), LocalChatService)
            self.assertEqual(service.status()['status'], 'test_only')
            self.assertTrue(hasattr(service, '_mission_session'))
            answer = service.chat({'message': PROMPT, 'consent': dict(CONSENT)})
            self.assertEqual(answer['answer'], 'Respuesta sintética.')
            self.assertEqual(len(fixture.requests), 1)
            session = service._mission_session
            self.assertEqual(session.status()['calls'], 1)
        finally:
            service._mission_session.close()
        with MissionBudget(self.config) as reopened:
            self.assertEqual(reopened.remaining(), 19)
        self.assert_no_secret_in_state()

    def test_night_route_two_rounds_consume_two_reservations(self):
        fixture = StructuredSessionFixture(200, BODY)
        with self.environment(night='1'):
            service = pai_setup.build_chat_service(
                night_mission=True, test_only=True, transport=fixture,
                clock=self.clock, mission_config=self.config)
        try:
            for _ in range(2):
                service.chat({'message': PROMPT, 'consent': dict(CONSENT)})
        finally:
            service._mission_session.close()
        self.assertEqual(len(fixture.requests), 2)
        with MissionBudget(self.config) as reopened:
            self.assertEqual(reopened.remaining(), 18)

    def test_production_night_route_builds_the_counted_session_without_network(self):
        FakeDateTime.current = START + timedelta(seconds=1)
        with self.environment(night='1'), \
             patch.object(pai_setup, '_current_time', lambda now=None: START + timedelta(seconds=1)), \
             patch.object(session_module, 'datetime', FakeDateTime), \
             patch('socket.socket', side_effect=AssertionError('network forbidden')):
            service = pai_setup.build_chat_service(night_mission=True)
        try:
            self.assertIs(type(service), LocalChatService)
            self.assertIs(type(service._provider), _SingleFlightProvider)
            self.assertFalse(service._mission_session.test_only)
            self.assertEqual(service.status()['status'], 'configured_not_verified')
        finally:
            service._mission_session.close()
        with MissionBudget(self.config) as reopened:
            self.assertEqual(reopened.remaining(), 20)

    def test_night_route_failure_is_fail_closed_never_historical_provider(self):
        fixture = StructuredSessionFixture(200, BODY)
        with self.environment(night='1'), \
             patch.object(pai_setup, 'MissionBudget', side_effect=RuntimeError('synthetic failure')), \
             patch.object(pai_setup, 'Session') as session_class, \
             patch.object(pai_setup.GroqProvider, 'from_environment') as ordinary:
            service = pai_setup.build_chat_service(
                night_mission=True, test_only=True, transport=fixture,
                clock=self.clock, mission_config=self.config)
            self.assert_disabled(service)
            with self.assertRaises(ServiceProblem):
                service.chat({'message': PROMPT, 'consent': dict(CONSENT)})
            self.assertEqual(fixture.requests, [])
            session_class.assert_not_called()
            ordinary.assert_not_called()

        with self.environment(night='1'), \
             patch.object(pai_setup, '_current_time', lambda now=None: START + timedelta(seconds=1)), \
             patch.object(pai_setup, 'Session', side_effect=RuntimeError('synthetic failure')) as session_class, \
             patch.object(pai_setup.GroqProvider, 'from_environment') as ordinary:
            service = pai_setup.build_chat_service(night_mission=True)
            self.assert_disabled(service)
            session_class.assert_called_once()
            ordinary.assert_not_called()

    def test_night_route_rejects_implicit_or_partial_injection(self):
        fixture = StructuredSessionFixture(200, BODY)
        with self.environment(night='1'):
            for kwargs in (
                {'night_mission': 'yes'},
                {'test_only': True},
                {'transport': fixture, 'clock': self.clock},
                {'night_mission': True, 'transport': fixture, 'clock': self.clock},
                {'night_mission': True, 'test_only': True, 'transport': object(),
                 'clock': self.clock, 'mission_config': self.config},
                {'night_mission': True, 'test_only': True, 'transport': fixture,
                 'mission_config': self.config},
                {'night_mission': True, 'test_only': True, 'transport': fixture,
                 'clock': self.clock, 'mission_config': object()},
            ):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    pai_setup.build_chat_service(**kwargs)

    def test_docs_manifest_is_only_an_identity_source(self):
        canonical = self.directory / 'canonical'
        write_state(canonical)
        (canonical / 'MISSION.json').unlink()
        docs = self.directory / 'docs' / 'MISSION.json'
        docs.parent.mkdir(parents=True)
        docs.write_text(json.dumps(NIGHT, indent=2) + '\n', encoding='utf8')
        with patch.object(mission_budget, 'NIGHT_MANIFEST', canonical / 'MISSION.json'), \
             patch.object(pai_setup, 'DOCUMENT_MANIFEST', docs):
            config = pai_setup._mission_config(now=START + timedelta(seconds=1))
            self.assertIs(type(config), MissionConfig)
            self.assertEqual(config.directory, canonical)
            self.assertFalse((canonical / 'mission-ledger.json').exists())
            self.assertFalse((canonical / 'mission-ledger.json.lock').exists())


if __name__ == '__main__':
    unittest.main()
