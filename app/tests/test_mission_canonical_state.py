"""Canonical per-profile mission state, shared by every authorized checkout.

These tests never touch the real profile state: every subprocess receives a
private LOCALAPPDATA/XDG_STATE_HOME rooted in a temporary directory and a copy
of the runtime in a temporary checkout.  No provider is contacted.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import mission_budget
from mission_budget import MissionBudget, load_mission

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path(__file__).resolve().parents[1]
NIGHT = {
    'schema': 'paideia-night-mission.v1',
    'mission_id': 'paideia-night-20261104',
    'start_utc': '2026-11-04T00:00:00Z',
    'deadline_utc': '2026-11-04T08:00:00Z',
    'max_external_attempts': 20,
}
SEAL_SCHEMA = 'paideia-night-ledger-seal.v1'
START = datetime(2026, 11, 4, 0, 0, tzinfo=timezone.utc)
CUTOFF = datetime(2026, 11, 4, 8, 0, tzinfo=timezone.utc)


def write_canonical_state(directory, *, seal=True, state='uninitialized'):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory / 'MISSION.json'
    manifest.write_text(json.dumps(NIGHT, indent=2) + '\n', encoding='utf8')
    if seal:
        payload = {
            'schema': SEAL_SCHEMA,
            'manifest_sha256': mission_budget.night_manifest_digest(NIGHT),
            'mission_id': NIGHT['mission_id'],
            'state': state,
        }
        if state == 'initialized':
            payload.update({'used': 0, 'journal_sha256': '0' * 64})
        (directory / 'MISSION.seal').write_text(
            json.dumps(payload, separators=(',', ':')), encoding='utf8')
    return manifest


def canonical_dir(profile):
    with patch.dict(os.environ, {
        'LOCALAPPDATA': str(profile),
        'XDG_STATE_HOME': str(Path(profile) / 'state'),
    }):
        return mission_budget.canonical_mission_state_dir(NIGHT['mission_id'])


def child_environment(profile, home):
    allowed = ('SYSTEMROOT', 'PATH', 'TEMP', 'TMP', 'COMSPEC', 'WINDIR')
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment.update({
        'LOCALAPPDATA': str(profile),
        'XDG_STATE_HOME': str(Path(profile) / 'state'),
        'HOME': str(home),
        'USERPROFILE': str(home),
        'PYTHONPATH': '',
        'PAIDEIA_GROQ_ENABLED': '',
        'GROQ_API_KEY': '',
    })
    return environment


def copy_runtime(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RUNTIME / 'mission_budget.py', destination / 'mission_budget.py')
    return destination


def run_child(code, checkout, profile, home, *arguments, timeout=30):
    command = [sys.executable, '-B', '-c', code, *[str(item) for item in arguments]]
    return subprocess.run(
        command, cwd=str(checkout), env=child_environment(profile, home),
        capture_output=True, text=True, timeout=timeout,
    )


class CanonicalLocationTests(unittest.TestCase):
    def test_default_manifest_lives_below_the_profile_not_the_checkout(self):
        location = mission_budget.NIGHT_MANIFEST
        self.assertTrue(location.is_absolute())
        self.assertEqual(location.name, 'MISSION.json')
        self.assertNotIn('App Financiera', location.parts)
        self.assertNotIn('prototipos', location.parts)
        self.assertEqual(location.parent, mission_budget.NIGHT_STATE_DIR)

    def test_copies_of_the_checkout_resolve_to_the_same_canonical_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            profile, home = base / 'profile', base / 'home'
            first, second = copy_runtime(base / 'checkout-a'), copy_runtime(base / 'checkout-b')
            code = (
                "import os, sys\n"
                "sys.path.insert(0, os.getcwd())\n"
                "import mission_budget as m\n"
                "print(m.NIGHT_MANIFEST)\n"
            )
            left = run_child(code, first, profile, home)
            right = run_child(code, second, profile, home)
            self.assertEqual(left.returncode, 0, left.stderr)
            self.assertEqual(right.returncode, 0, right.stderr)
            left_path, right_path = Path(left.stdout.strip()), Path(right.stdout.strip())
            self.assertEqual(left_path, right_path)
            self.assertEqual(left_path, canonical_dir(profile) / 'MISSION.json')
            self.assertNotIn(first, left_path.parents)
            self.assertNotIn(second, right_path.parents)

    def test_canonical_location_differs_per_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            first = canonical_dir(base / 'profile-a')
            second = canonical_dir(base / 'profile-b')
            self.assertNotEqual(first, second)
            self.assertEqual(first.name, NIGHT['mission_id'])

    def test_invalid_mission_identifiers_are_rejected(self):
        for mission_id in ('', '..', 'a/b', 'A' * 100, None, 3):
            with self.subTest(mission_id=mission_id), self.assertRaises(ValueError):
                mission_budget.canonical_mission_state_dir(mission_id)


class SharedLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.profile, self.home = self.base / 'profile', self.base / 'home'
        self.state = canonical_dir(self.profile)
        write_canonical_state(self.state)
        self.first = copy_runtime(self.base / 'checkout-a')
        self.second = copy_runtime(self.base / 'checkout-b')

    def child_reserve_code(self):
        return (
            "import sys\n"
            "from datetime import timedelta\n"
            "import mission_budget as m\n"
            "config = m.load_mission(m.NIGHT_MANIFEST)\n"
            "with m.MissionBudget(config) as budget:\n"
            "    for _ in range(int(sys.argv[1])):\n"
            "        budget.reserve(config.start + timedelta(seconds=1))\n"
            "    print(budget.remaining())\n"
        )

    def test_two_checkout_copies_share_one_ledger_and_one_cap(self):
        code = self.child_reserve_code()
        first = run_child(code, self.first, self.profile, self.home, 3)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout.strip(), '17')
        second = run_child(code, self.second, self.profile, self.home, 2)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second.stdout.strip(), '15')
        reopened = run_child(code, self.first, self.profile, self.home, 0)
        self.assertEqual(reopened.returncode, 0, reopened.stderr)
        self.assertEqual(reopened.stdout.strip(), '15')
        ledger = self.state / 'mission-ledger.json'
        self.assertTrue(ledger.is_file())
        self.assertEqual(json.loads(ledger.read_text(encoding='utf8'))['used'], 5)
        for checkout in (self.first, self.second):
            self.assertFalse((checkout / 'mission-ledger.json').exists())
            self.assertFalse((checkout / 'MISSION.seal').exists())
        # Exactly one ledger exists below the whole temporary profile.
        ledgers = list(self.profile.rglob('mission-ledger.json'))
        self.assertEqual(ledgers, [ledger])

    def test_restart_from_a_copy_keeps_every_reservation(self):
        code = self.child_reserve_code()
        self.assertEqual(run_child(code, self.first, self.profile, self.home, 4).stdout.strip(), '16')
        self.assertEqual(run_child(code, self.second, self.profile, self.home, 0).stdout.strip(), '16')
        self.assertEqual(run_child(code, self.first, self.profile, self.home, 1).stdout.strip(), '15')

    def test_another_profile_has_an_independent_ledger(self):
        other_profile = self.base / 'profile-other'
        other_state = canonical_dir(other_profile)
        write_canonical_state(other_state)
        code = self.child_reserve_code()
        self.assertEqual(run_child(code, self.first, self.profile, self.home, 3).stdout.strip(), '17')
        self.assertEqual(run_child(code, self.first, other_profile, self.home, 0).stdout.strip(), '20')
        self.assertEqual(json.loads((other_state / 'mission-ledger.json').read_text(encoding='utf8'))['used'], 0)

    def test_concurrent_copies_never_exceed_the_shared_cap(self):
        code = (
            "import sys, time\n"
            "from datetime import timedelta\n"
            "import mission_budget as m\n"
            "config = m.load_mission(m.NIGHT_MANIFEST)\n"
            "wanted = int(sys.argv[1]); done = 0; limit = time.time() + 40\n"
            "while done < wanted and time.time() < limit:\n"
            "    try:\n"
            "        with m.MissionBudget(config) as budget:\n"
            "            if budget.remaining() == 0:\n"
            "                break\n"
            "            budget.reserve(config.start + timedelta(seconds=1))\n"
            "            done += 1\n"
            "    except Exception:\n"
            "        time.sleep(0.002)\n"
            "print(done)\n"
        )
        processes = [
            subprocess.Popen(
                [sys.executable, '-B', '-c', code, '8'], cwd=str(checkout),
                env=child_environment(self.profile, self.home),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            for checkout in (self.first, self.second, self.first)
        ]
        outputs = [process.communicate(timeout=60) for process in processes]
        for process, (_out, err) in zip(processes, outputs):
            self.assertEqual(process.returncode, 0, err)
        counts = [int(out.strip()) for out, _err in outputs]
        self.assertEqual(sum(counts), 20)
        ledger = self.state / 'mission-ledger.json'
        self.assertEqual(json.loads(ledger.read_text(encoding='utf8'))['used'], 20)
        self.assertEqual(len(list(self.profile.rglob('mission-ledger.json'))), 1)

    def test_copy_manifest_uses_the_same_canonical_ledger(self):
        # A copied checkout keeps a local docs manifest.  Because the content
        # is byte-equivalent it is the same mission, but all state must still
        # live in the canonical profile directory.
        for checkout in (self.first, self.second):
            local = checkout / 'docs' / 'mision-nocturna-20261104'
            local.mkdir(parents=True)
            shutil.copy2(self.state / 'MISSION.json', local / 'MISSION.json')
        code = (
            "import os, sys\n"
            "from datetime import timedelta\n"
            "sys.path.insert(0, os.getcwd())\n"
            "import mission_budget as m\n"
            "local = os.path.join(os.getcwd(), 'docs', 'mision-nocturna-20261104', 'MISSION.json')\n"
            "config = m.load_mission(local)\n"
            "with m.MissionBudget(config) as budget:\n"
            "    budget.reserve(config.start + timedelta(seconds=1))\n"
            "    print(budget.path)\n"
        )
        result = run_child(code, self.first, self.profile, self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()), self.state / 'mission-ledger.json')
        self.assertFalse((self.first / 'mission-ledger.json').exists())
        self.assertFalse((self.second / 'mission-ledger.json').exists())


class FailClosedCanonicalStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.manifest = write_canonical_state(self.directory)
        self.patch = patch.object(mission_budget, 'NIGHT_MANIFEST', self.manifest)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.config = load_mission(self.manifest)

    def paths(self):
        return {
            'ledger': self.directory / 'mission-ledger.json',
            'journal': self.directory / 'mission-ledger.json.lock',
            'seal': self.directory / 'MISSION.seal',
        }

    def test_missing_seal_never_creates_a_ledger(self):
        self.paths()['seal'].unlink()
        with self.assertRaises((OSError, ValueError)):
            MissionBudget(self.config)
        self.assertFalse(self.paths()['ledger'].exists())
        self.assertFalse(self.paths()['journal'].exists())

    def test_existing_journal_without_a_ledger_is_ambiguous(self):
        self.paths()['journal'].write_bytes(b'')
        with self.assertRaises(ValueError):
            MissionBudget(self.config)
        self.assertFalse(self.paths()['ledger'].exists())

    def test_ledger_without_journal_or_seal_is_rejected(self):
        with MissionBudget(self.config) as budget:
            budget.reserve(self.config.start + timedelta(seconds=1))
        self.paths()['journal'].unlink()
        with self.assertRaises((OSError, ValueError)):
            MissionBudget(self.config)

    def test_deleting_all_state_never_resets_the_cap(self):
        with MissionBudget(self.config) as budget:
            budget.reserve(self.config.start + timedelta(seconds=1))
        for path in self.paths().values():
            path.unlink()
        with self.assertRaises((OSError, ValueError)):
            MissionBudget(self.config)
        self.assertFalse(self.paths()['ledger'].exists())

    def test_seal_rollback_is_rejected_after_both_files_are_replayed(self):
        with MissionBudget(self.config) as budget:
            budget.reserve(self.config.start + timedelta(seconds=1))
        old_ledger = self.paths()['ledger'].read_bytes()
        old_journal = self.paths()['journal'].read_bytes()
        old_seal = self.paths()['seal'].read_bytes()
        with MissionBudget(self.config) as budget:
            budget.reserve(self.config.start + timedelta(seconds=2))
        self.paths()['ledger'].write_bytes(old_ledger)
        self.paths()['journal'].write_bytes(old_journal)
        with self.assertRaises(ValueError):
            MissionBudget(self.config)
        # Replaying the seal too is the residual rollback that only an
        # external witness could detect; it is explicitly documented.
        self.paths()['seal'].write_bytes(old_seal)
        with MissionBudget(self.config) as replay:
            self.assertEqual(replay.remaining(), 19)

    def test_cutoff_is_checked_per_reservation_on_the_canonical_ledger(self):
        with MissionBudget(self.config) as budget:
            self.assertEqual(budget.reserve(CUTOFF - timedelta(microseconds=1)), 19)
            for now in (CUTOFF, CUTOFF + timedelta(seconds=1), START - timedelta(seconds=1)):
                with self.subTest(now=now), self.assertRaises(RuntimeError):
                    budget.reserve(now)
            self.assertEqual(budget.remaining(), 19)


if __name__ == '__main__':
    unittest.main()
