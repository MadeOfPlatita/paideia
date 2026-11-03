import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import mission_budget
from mission_budget import MissionBudget, load_mission


class JournalIntegrityTests(unittest.TestCase):
    def test_interrupted_journal_sync_blocks_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                with MissionBudget(config) as budget:
                    with patch.object(mission_budget.os, 'fsync', side_effect=OSError('synthetic sync failure')):
                        with self.assertRaises(OSError): budget.reserve(config.start + timedelta(seconds=1))
                    with self.assertRaises(ValueError): budget.remaining()
                with self.assertRaises(ValueError): MissionBudget(config)

    def test_existing_empty_journal_never_reinitializes(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                ledger = Path(tmp) / 'mission-ledger.json'
                journal = Path(str(ledger) + '.lock')
                journal.write_bytes(b'')
                with self.assertRaises(ValueError): MissionBudget(config)
                self.assertFalse(ledger.exists())
                self.assertEqual(journal.read_bytes(), b'')

    def test_middle_entry_corruption_fails_closed(self):
        for mutation in ('CORRUPTED', 'hex'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                manifest = Path(tmp) / 'MISSION.json'
                manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
                with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                    config = load_mission(manifest)
                    with MissionBudget(config) as budget:
                        budget.reserve(config.start + timedelta(seconds=1))
                        budget.reserve(config.start + timedelta(seconds=2))
                    journal = Path(str(budget.path) + '.lock')
                    lines = journal.read_bytes().splitlines(keepends=True)
                    if mutation == 'CORRUPTED':
                        lines[2] = b'CORRUPTED\n'
                    else:
                        # Flip an ASCII hex byte without changing its syntactic class.
                        line = bytearray(lines[2])
                        index = line.index(b'"snapshot":"') + len(b'"snapshot":"') if b'"snapshot":"' in line else 0
                        line[index] = ord('f') if line[index] != ord('f') else ord('e')
                        lines[2] = bytes(line)
                    journal.write_bytes(b''.join(lines))
                    with self.assertRaises((ValueError, OSError)):
                        MissionBudget(config)

    def test_truncation_removal_and_replay_are_rejected(self):
        for mutation in ('partial', 'remove_middle', 'remove_last', 'replay_snapshot', 'duplicate'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                manifest = Path(tmp) / 'MISSION.json'
                manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
                with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                    config = load_mission(manifest)
                    with MissionBudget(config) as budget:
                        budget.reserve(config.start + timedelta(seconds=1))
                        saved = budget.path.read_bytes()
                        budget.reserve(config.start + timedelta(seconds=2))
                    with MissionBudget(config) as reopened:
                        self.assertEqual(reopened.remaining(), 22)
                    journal = Path(str(budget.path) + '.lock')
                    original = journal.read_bytes()
                    lines = original.splitlines(keepends=True)
                    if mutation == 'partial': journal.write_bytes(original[:-4])
                    elif mutation == 'remove_middle': journal.write_bytes(b''.join(lines[:2] + lines[3:]))
                    elif mutation == 'remove_last': journal.write_bytes(b''.join(lines[:-1]))
                    elif mutation == 'duplicate': journal.write_bytes(b''.join(lines[:3] + [lines[2]] + lines[3:]))
                    else: budget.path.write_bytes(saved)
                    before_journal, before_ledger = journal.read_bytes(), budget.path.read_bytes()
                    with self.assertRaises((ValueError, OSError)):
                        MissionBudget(config)
                    self.assertEqual(journal.read_bytes(), before_journal)
                    self.assertEqual(budget.path.read_bytes(), before_ledger)

    def test_old_format_is_rejected_without_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'MISSION.json'
            manifest.write_text(json.dumps({'schema': 'paideia-mission.v1', 'mission_id': 'paideia-ia-20261029T220831Z', 'start_utc': '2026-10-29T22:08:31.985015+00:00', 'deadline_utc': '2026-10-29T23:08:31.985015+00:00', 'max_external_attempts': 24}), encoding='utf8')
            with patch.object(mission_budget, 'NEW_MANIFEST', manifest):
                config = load_mission(manifest)
                ledger = Path(tmp) / 'mission-ledger.json'
                journal = Path(str(ledger) + '.lock')
                old = b'NEW-MISSION-LEDGER-v1 ' + config.digest.encode() + b'\n' + b'0' * 64 + b'\n'
                journal.write_bytes(old)
                ledger.write_bytes(b'{}')
                with self.assertRaises(ValueError): MissionBudget(config)
                self.assertEqual(journal.read_bytes(), old)
                self.assertEqual(ledger.read_bytes(), b'{}')
