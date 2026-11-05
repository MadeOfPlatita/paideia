import json
import subprocess
import sys
import threading
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import timedelta
import mission_budget
from mission_budget import load_mission, MissionBudget
from providers import ProviderError
from secure_groq_session import Session
import secure_groq_session as launcher
from tests.test_session_send_boundary import FakeConnection, FakeDateTime, MESSAGE
from structured_session_fixture import StructuredSessionFixture

class NewMissionTests(unittest.TestCase):
    def test_manifest_changed_during_tls_blocks_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                with MissionBudget(config) as budget:
                    fixture = StructuredSessionFixture(200, b'{}')
                    fixture.connect_entered, fixture.connect_release = threading.Event(), threading.Event()
                    session = Session('FAKE', test_only=True, transport=fixture, clock=lambda: config.start + timedelta(seconds=1), mission_budget=budget)
                    errors = []
                    def send():
                        try: session.provider.chat(MESSAGE)
                        except Exception as exc: errors.append(exc)
                    thread = threading.Thread(target=send)
                    thread.start()
                    try:
                        self.assertTrue(fixture.connect_entered.wait(2))
                        manifest.write_text(manifest.read_text(encoding='utf8') + ' ', encoding='utf8')
                    finally:
                        fixture.connect_release.set()
                        thread.join(3)
                    self.assertTrue(errors)
                    self.assertEqual(fixture.requests, [])

                    self.assertEqual(session._environment, {})
    def test_ready_event_is_json_without_credential(self):
        event = launcher.ready_event('run-123', True)
        self.assertEqual(json.loads(event), {'event': 'READY', 'run_id': 'run-123', 'test_only': True})
        self.assertNotIn('FAKE_KEY', event)
    def test_session_uses_new_mission_and_persists_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                with MissionBudget(config) as budget:
                    fixture = StructuredSessionFixture(500, b'{}')
                    session = Session('FAKE', test_only=True, transport=fixture, clock=lambda: config.start + timedelta(seconds=1), mission_budget=budget)
                    with self.assertRaises(ProviderError): session.provider.chat(MESSAGE)
                    self.assertEqual(len(fixture.requests), 1)
                with MissionBudget(config) as budget:
                    self.assertEqual(budget.remaining(), 23)

    def test_transport_exception_persists_mission_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            class FailedRequest(FakeConnection):
                def request(self, *args, **kwargs):
                    super().request(*args, **kwargs)
                    raise OSError('synthetic transport exception')
            FakeConnection.entered, FakeConnection.release = threading.Event(), threading.Event()
            FakeConnection.requests = []
            FakeConnection.release.set()
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                FakeDateTime.current = config.start + timedelta(seconds=1)
                with patch.object(launcher, 'datetime', FakeDateTime), \
                     patch('socket.socket', side_effect=AssertionError('socket prohibited')) as socket_factory, \
                     patch('providers.http.client.HTTPSConnection', FailedRequest):
                    with MissionBudget(config) as budget:
                        session = Session('FAKE', mission_budget=budget)
                        with self.assertRaises(ProviderError) as caught:
                            session.provider.chat(MESSAGE)
                        self.assertEqual(caught.exception.code, 'transport_error')
                        self.assertEqual(session.status()['calls'], 1)
                    socket_factory.assert_not_called()
                self.assertEqual(len(FakeConnection.requests), 1)
                with MissionBudget(config) as budget:
                    self.assertEqual(budget.remaining(), 23)

    def test_cli_mission_flag_does_not_open_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest), patch('sys.argv', ['launcher', '--mission', str(manifest)]), patch.object(launcher, 'create_window') as window:
                launcher.main()
                self.assertEqual(window.call_args.kwargs['mission_config'], load_mission(manifest))

    def test_mission_output_paths_are_isolated(self):

        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                with MissionBudget(config) as budget:
                    session = Session('FAKE', test_only=True, transport=StructuredSessionFixture(200, b'{}'), clock=lambda: config.start + timedelta(seconds=1), mission_budget=budget)
                    self.assertEqual(session._benchmark_path().parent.parent, Path(tmp))
                    self.assertEqual(session._status_path().parent, session._benchmark_path().parent)
                    self.assertEqual(session.status()['run_id'], session._status_path().parent.name)
                with MissionBudget(config) as budget:
                    second = Session('FAKE', test_only=True, transport=StructuredSessionFixture(200, b'{}'), clock=lambda: config.start + timedelta(seconds=1), mission_budget=budget)
                    self.assertNotEqual(second._status_path(), session._status_path())
    def test_new_manifest_restart_and_replay_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                with MissionBudget(config) as budget:
                    saved = budget.path.read_bytes()
                    self.assertEqual(budget.reserve(config.start + timedelta(seconds=1)), 23)
                with MissionBudget(config) as budget:
                    self.assertEqual(budget.remaining(), 23)
                budget.path.write_bytes(saved)
                with self.assertRaises(Exception): MissionBudget(config)

    def test_changed_manifest_after_restart_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            data = {'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}
            manifest.write_text(json.dumps(data), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                with MissionBudget(load_mission(manifest)) as budget:
                    budget.reserve(budget.config.start)
                manifest.write_text(json.dumps(data, indent=2), encoding='utf8')
                with self.assertRaises(Exception): MissionBudget(load_mission(manifest))

    def test_other_process_cannot_open_while_budget_locked(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                with MissionBudget(load_mission(manifest)):
                    code = 'import mission_budget as m; from pathlib import Path; m.NEW_MANIFEST=Path(%r); m.MissionBudget(m.load_mission(m.NEW_MANIFEST))' % str(manifest)
                    child = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True, timeout=10)
                    self.assertNotEqual(child.returncode, 0)
                with MissionBudget(load_mission(manifest)) as budget:
                    self.assertEqual(budget.remaining(), 24)

    def test_new_ledger_clock_and_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                with MissionBudget(config) as budget:
                    budget.reserve(config.start + timedelta(seconds=2))
                    for now in (config.start + timedelta(seconds=1), config.cutoff):
                        with self.assertRaises(RuntimeError): budget.reserve(now)
                    for _ in range(23): budget.reserve(config.start + timedelta(seconds=2))
                    with self.assertRaises(RuntimeError): budget.reserve(config.start + timedelta(seconds=2))
                with MissionBudget(config) as budget: self.assertEqual(budget.remaining(), 0)
