"""Offline contract for the 2026-11-04 night mission budget.

No real provider is contacted here. Every transport is the closed synthetic
fixture and every clock is injected.
"""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import mission_budget
from mission_budget import MissionBudget, load_mission
from providers import ProviderError
from secure_groq_session import Session
from structured_session_fixture import StructuredSessionFixture

ROOT = Path(__file__).resolve().parents[2]
NIGHT_ROOT = ROOT / 'docs' / 'mision-nocturna-20261104'
NIGHT_MANIFEST = NIGHT_ROOT / 'MISSION.json'
NIGHT_SEAL = NIGHT_ROOT / 'MISSION.seal'
OLD_MANIFESTS = (
    ROOT / 'docs/ia-real-siguiente/ejecucion/1c203c4baa604133806f36f44102e5e0/mission.json',
    ROOT / 'docs/ia-real-siguiente/ejecucion/20261029T220831Z/MISSION.json',
    ROOT / 'docs/ia-real-siguiente/ejecucion/20261030T005810Z/MISSION.json',
)
START = datetime(2026, 11, 4, 0, 0, tzinfo=timezone.utc)
CUTOFF = datetime(2026, 11, 4, 8, 0, tzinfo=timezone.utc)
MISSION = {
    'schema': 'paideia-night-mission.v1',
    'mission_id': 'paideia-night-20261104',
    'start_utc': '2026-11-04T00:00:00Z',
    'deadline_utc': '2026-11-04T08:00:00Z',
    'max_external_attempts': 20,
}
SEAL_SCHEMA = 'paideia-night-ledger-seal.v1'
MESSAGE = [{'role': 'user', 'content': 'SYNTHETIC NIGHT BODY'}]


def write_manifest(directory, *, newline='\n', **overrides):
    data = dict(MISSION)
    data.update(overrides)
    path = Path(directory) / 'MISSION.json'
    raw = json.dumps(data, indent=2).encode('utf8') + b'\n'
    if newline == '\r\n':
        raw = raw.replace(b'\n', b'\r\n')
    path.write_bytes(raw)
    seal = Path(directory) / 'MISSION.seal'
    seal.write_bytes(json.dumps({
        'schema': SEAL_SCHEMA,
        'manifest_sha256': mission_budget.night_manifest_digest(data),
        'mission_id': data['mission_id'],
        'state': 'uninitialized',
    }, separators=(',', ':')).encode('utf8'))
    return path


def state_paths(manifest):
    base = Path(manifest).parent
    ledger = base / 'mission-ledger.json'
    return {
        'ledger': ledger,
        'journal': Path(str(ledger) + '.lock'),
        'seal': base / 'MISSION.seal',
    }


class NightManifestTests(unittest.TestCase):
    def test_manifest_is_exact_and_old_missions_stay_legacy(self):
        self.assertTrue(NIGHT_MANIFEST.is_file(), 'night manifest must exist')
        config = load_mission(NIGHT_MANIFEST)
        self.assertEqual(config.mission_id, MISSION['mission_id'])
        self.assertEqual(config.cap, 20)
        self.assertEqual(config.start, START)
        self.assertEqual(config.cutoff, CUTOFF)
        self.assertTrue(config.sealed)
        self.assertEqual(config.directory, mission_budget.NIGHT_STATE_DIR)
        self.assertEqual(config.manifest, NIGHT_MANIFEST)
        seal = json.loads(NIGHT_SEAL.read_text(encoding='utf8'))
        self.assertEqual(seal['manifest_sha256'], config.digest)
        self.assertEqual(seal['mission_id'], MISSION['mission_id'])
        self.assertEqual(seal['state'], 'uninitialized')
        for old in OLD_MANIFESTS:
            old_config = load_mission(old)
            self.assertEqual(old_config.cap, 24)
            self.assertFalse(old_config.sealed)

    def test_manifest_contains_no_credentials(self):
        text = NIGHT_MANIFEST.read_text(encoding='utf8').lower()
        for marker in ('api_key', 'secret', 'token', 'password', 'bearer'):
            self.assertNotIn(marker, text)

    def test_manifest_rejects_any_tampering(self):
        mutations = (
            {'schema': 'paideia-mission.v1'},
            {'mission_id': 'paideia-night-other'},
            {'start_utc': '2026-11-04T00:00:01+00:00'},
            {'deadline_utc': '2026-11-04T08:00:01+00:00'},
            {'max_external_attempts': 24},
            {'real_calls_authorized': True},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                manifest = write_manifest(tmp, **mutation)
                with patch.object(mission_budget, 'NIGHT_MANIFEST', manifest):
                    with self.assertRaises(ValueError):
                        load_mission(manifest)
        with self.assertRaises(ValueError):
            load_mission('MISSION.json')

    def test_crlf_checkout_keeps_the_same_canonical_binding(self):
        expected = load_mission(NIGHT_MANIFEST).digest
        with tempfile.TemporaryDirectory() as tmp:
            manifest = write_manifest(tmp, newline='\r\n')
            with patch.object(mission_budget, 'NIGHT_MANIFEST', manifest):
                config = load_mission(manifest)
                self.assertEqual(config.digest, expected)
                with MissionBudget(config) as budget:
                    self.assertEqual(budget.remaining(), 20)


class SealedLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.manifest = write_manifest(self.temporary.name)
        self.patch = patch.object(mission_budget, 'NIGHT_MANIFEST', self.manifest)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.config = load_mission(self.manifest)
        self.paths = state_paths(self.manifest)

    def test_sealed_mission_cannot_be_redirected_to_another_ledger(self):
        with tempfile.TemporaryDirectory() as other:
            with self.assertRaises(ValueError):
                MissionBudget(self.config, Path(other) / 'mission-ledger.json')

    def test_missing_precreated_seal_never_initializes(self):
        self.paths['seal'].unlink()
        with self.assertRaises(OSError):
            MissionBudget(self.config)
        self.assertFalse(self.paths['ledger'].exists())

    def test_initializes_once_and_survives_restart(self):
        self.assertFalse(self.paths['ledger'].exists())
        with MissionBudget(self.config) as budget:
            self.assertEqual(budget.remaining(), 20)
            self.assertEqual(budget.reserve(START + timedelta(seconds=1)), 19)
        seal = json.loads(self.paths['seal'].read_text(encoding='utf8'))
        self.assertEqual(seal['state'], 'initialized')
        self.assertEqual(seal['used'], 1)
        with MissionBudget(self.config) as budget:
            self.assertEqual(budget.remaining(), 19)
            self.assertEqual(budget.reserve(START + timedelta(seconds=2)), 18)
        with MissionBudget(self.config) as budget:
            self.assertEqual(budget.remaining(), 18)

    def test_concurrent_threads_never_exceed_twenty(self):
        with MissionBudget(self.config) as budget:
            results, failures = [], []
            barrier = threading.Barrier(40)

            def reserve():
                barrier.wait()
                try:
                    results.append(budget.reserve(START + timedelta(seconds=1)))
                except RuntimeError:
                    failures.append(1)

            threads = [threading.Thread(target=reserve) for _ in range(40)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(len(results), 20)
            self.assertEqual(sorted(results), list(range(20)))
            self.assertEqual(len(failures), 20)
            self.assertEqual(budget.remaining(), 0)
            with self.assertRaises(RuntimeError):
                budget.reserve(START + timedelta(seconds=1))
        with MissionBudget(self.config) as budget:
            self.assertEqual(budget.remaining(), 0)

    def test_second_process_cannot_open_the_sealed_ledger(self):
        with MissionBudget(self.config):
            code = (
                "from pathlib import Path\n"
                "import mission_budget as m\n"
                "m.NIGHT_MANIFEST = Path(%r)\n"
                "m.MissionBudget(m.load_mission(m.NIGHT_MANIFEST))\n"
            ) % str(self.manifest)
            child = subprocess.run(
                [sys.executable, '-B', '-c', code],
                cwd=str(Path(__file__).resolve().parents[1]),
                capture_output=True, timeout=15,
            )
            self.assertNotEqual(child.returncode, 0)
        with MissionBudget(self.config) as budget:
            self.assertEqual(budget.remaining(), 20)

    def test_separate_processes_share_the_twenty_attempt_cap(self):
        code = (
            "import sys\n"
            "from datetime import timedelta\n"
            "from pathlib import Path\n"
            "import mission_budget as m\n"
            "m.NIGHT_MANIFEST = Path(sys.argv[1])\n"
            "config = m.load_mission(m.NIGHT_MANIFEST)\n"
            "count = 0\n"
            "with m.MissionBudget(config) as budget:\n"
            "    while True:\n"
            "        try:\n"
            "            budget.reserve(config.start + timedelta(seconds=1))\n"
            "            count += 1\n"
            "        except RuntimeError:\n"
            "            break\n"
            "print(count)\n"
        )
        counts = []
        for _ in range(3):
            result = subprocess.run(
                [sys.executable, '-B', '-c', code, str(self.manifest)],
                cwd=str(Path(__file__).resolve().parents[1]),
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            counts.append(int(result.stdout.strip()))
        self.assertEqual(sum(counts), 20)
        with MissionBudget(self.config) as budget:
            self.assertEqual(budget.remaining(), 0)

    def test_cutoff_is_checked_exactly_before_each_reservation(self):
        with MissionBudget(self.config) as budget:
            self.assertEqual(budget.reserve(CUTOFF - timedelta(microseconds=1)), 19)
            for now in (CUTOFF, CUTOFF + timedelta(seconds=1),
                        START - timedelta(microseconds=1),
                        datetime(2026, 11, 4, 7, 0)):
                with self.subTest(now=now), self.assertRaises(RuntimeError):
                    budget.reserve(now)
            with self.assertRaises(RuntimeError):
                budget.reserve(START)
            self.assertEqual(budget.remaining(), 19)

    def test_deleting_any_state_prevents_restart(self):
        for missing in ('ledger', 'journal', 'seal', 'all'):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                manifest = write_manifest(tmp)
                with patch.object(mission_budget, 'NIGHT_MANIFEST', manifest):
                    config = load_mission(manifest)
                    with MissionBudget(config) as budget:
                        budget.reserve(config.start + timedelta(seconds=1))
                    paths = state_paths(manifest)
                    if missing == 'all':
                        for path in paths.values():
                            path.unlink()
                    else:
                        paths[missing].unlink()
                    with self.assertRaises((ValueError, OSError, RuntimeError)):
                        MissionBudget(config)

    def test_replayed_ledger_or_journal_is_rejected(self):
        with MissionBudget(self.config) as budget:
            budget.reserve(START + timedelta(seconds=1))
        old_ledger = self.paths['ledger'].read_bytes()
        old_journal = self.paths['journal'].read_bytes()
        with MissionBudget(self.config) as budget:
            budget.reserve(START + timedelta(seconds=2))
        newest_ledger = self.paths['ledger'].read_bytes()
        newest_journal = self.paths['journal'].read_bytes()
        self.paths['ledger'].write_bytes(old_ledger)
        with self.assertRaises((ValueError, OSError)):
            MissionBudget(self.config)
        # Restore the newest files, then replay both to the older consistent
        # snapshot. The seal high-water mark must still reject it.
        self.paths['ledger'].write_bytes(newest_ledger)
        self.paths['journal'].write_bytes(newest_journal)
        self.paths['ledger'].write_bytes(old_ledger)
        self.paths['journal'].write_bytes(old_journal)
        with self.assertRaises((ValueError, OSError)):
            MissionBudget(self.config)


class SessionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.manifest = write_manifest(self.temporary.name)
        self.patch = patch.object(mission_budget, 'NIGHT_MANIFEST', self.manifest)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.config = load_mission(self.manifest)
        self.budget = MissionBudget(self.config)
        self.addCleanup(self.budget.close)

    def test_session_reports_and_enforces_twenty_not_twenty_four(self):
        fixture = StructuredSessionFixture(200, b'{}')
        session = Session('FAKE-NIGHT-KEY', test_only=True, transport=fixture,
                          clock=lambda: START + timedelta(seconds=1),
                          mission_budget=self.budget)
        self.addCleanup(session.close)
        for _ in range(20):
            session.transport.post(host='synthetic', path='/', headers={},
                                   body=b'{}', timeout=1)
        self.assertEqual(session.status()['limit'], 20)
        self.assertEqual(session.status()['calls'], 20)
        self.assertEqual(len(fixture.requests), 20)
        with self.assertRaises(Exception):
            session.transport.post(host='synthetic', path='/', headers={},
                                   body=b'{}', timeout=1)
        self.assertEqual(len(fixture.requests), 20)

    def test_failed_attempt_consumes_one_reservation(self):
        fixture = StructuredSessionFixture(500, b'{}')
        session = Session('FAKE-NIGHT-KEY', test_only=True, transport=fixture,
                          clock=lambda: START + timedelta(seconds=1),
                          mission_budget=self.budget)
        with self.assertRaises(ProviderError):
            session.provider.chat(MESSAGE)
        self.assertEqual(len(fixture.requests), 1)
        self.assertEqual(session.status()['calls'], 1)
        session.close()
        with MissionBudget(self.config) as reopened:
            self.assertEqual(reopened.remaining(), 19)

    def test_cutoff_is_rechecked_after_reservation_before_real_send(self):
        entered, release = threading.Event(), threading.Event()
        fixture = StructuredSessionFixture(200, b'{}')
        fixture.connect_entered, fixture.connect_release = entered, release
        clock = [CUTOFF - timedelta(seconds=2)]
        session = Session('FAKE-NIGHT-KEY', test_only=True, transport=fixture,
                          clock=lambda: clock[0], mission_budget=self.budget)
        self.addCleanup(session.close)
        errors = []

        def send():
            try:
                session.provider.chat(MESSAGE)
            except Exception as error:  # The boundary must fail closed.
                errors.append(error)

        thread = threading.Thread(target=send)
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            clock[0] = CUTOFF
        finally:
            release.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertTrue(errors)
        self.assertEqual(fixture.requests, [])
        self.assertEqual(session.status()['calls'], 1)
        session.close()
        with MissionBudget(self.config) as reopened:
            self.assertEqual(reopened.remaining(), 19)

    def test_ledger_and_status_never_expose_the_key_or_prompt(self):
        key = 'FAKE-NIGHT-KEY-NEVER-PERSIST'
        prompt = [{'role': 'user', 'content': 'SYNTHETIC-NIGHT-PROMPT-NEVER-PERSIST'}]
        fixture = StructuredSessionFixture(500, b'{}')
        session = Session(key, test_only=True, transport=fixture,
                          clock=lambda: START + timedelta(seconds=1),
                          mission_budget=self.budget)
        with self.assertRaises(ProviderError):
            session.provider.chat(prompt)
        session.close()
        for path in Path(self.temporary.name).rglob('*'):
            if path.is_file():
                text = path.read_text(encoding='utf8', errors='ignore')
                self.assertNotIn(key, text, path)
                self.assertNotIn('SYNTHETIC-NIGHT-PROMPT-NEVER-PERSIST', text, path)


if __name__ == '__main__':
    unittest.main()
