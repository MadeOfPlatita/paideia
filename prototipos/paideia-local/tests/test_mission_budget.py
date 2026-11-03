import tempfile
import unittest
import subprocess
import sys
import threading
from datetime import timedelta
from pathlib import Path
from mission_budget import MissionBudget, load_mission

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'docs/ia-real-siguiente/ejecucion/1c203c4baa604133806f36f44102e5e0/mission.json'

class BudgetTests(unittest.TestCase):
    def test_closed_budget_never_reserves_without_its_process_lock(self):
        config = load_mission(MANIFEST)
        with tempfile.TemporaryDirectory() as d:
            budget = MissionBudget(config, Path(d) / 'ledger')
            budget.close()
            with self.assertRaises(RuntimeError): budget.reserve(config.start)

    def test_manifest_path_and_types(self):
        with self.assertRaises(ValueError): load_mission('mission.json')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): load_mission(Path(d) / 'mission.json')
        config = load_mission(MANIFEST)
        self.assertEqual(config.cap, 24)
        self.assertEqual(config.cutoff - config.start, timedelta(hours=1))

    def test_concurrent_threads_reserve_no_more_than_cap(self):
        config = load_mission(MANIFEST)
        with tempfile.TemporaryDirectory() as d:
            with MissionBudget(config, Path(d) / 'ledger') as budget:
                results = []
                def reserve():
                    try: results.append(budget.reserve(config.start + timedelta(seconds=1)))
                    except RuntimeError: pass
                threads = [threading.Thread(target=reserve) for _ in range(30)]
                for thread in threads: thread.start()
                for thread in threads: thread.join()
                self.assertEqual(sorted(results), list(range(24)))
                self.assertEqual(budget.remaining(), 0)

    def test_second_process_is_excluded(self):
        config = load_mission(MANIFEST)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'ledger'
            with MissionBudget(config, path):
                code = ('from mission_budget import load_mission,MissionBudget; '
                        'MissionBudget(load_mission(%r),%r)' % (str(MANIFEST), str(path)))
                result = subprocess.run([sys.executable, '-c', code], capture_output=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
            with MissionBudget(config, path) as budget:
                self.assertEqual(budget.remaining(), 24)

    def test_cutoff_and_rollback_fail_closed(self):
        config = load_mission(MANIFEST)
        with tempfile.TemporaryDirectory() as d:
            with MissionBudget(config, Path(d) / 'ledger') as budget:
                budget.reserve(config.start + timedelta(seconds=2))
                for now in (config.start + timedelta(seconds=1), config.cutoff):
                    with self.assertRaises(RuntimeError): budget.reserve(now)
                self.assertEqual(budget.remaining(), 23)

    def test_missing_or_corrupt_ledger_never_reinitializes(self):
        config = load_mission(MANIFEST)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'ledger'
            with MissionBudget(config, path) as budget: budget.reserve(config.start)
            path.unlink()
            with self.assertRaises(Exception): MissionBudget(config, path)
            path.write_text('{', encoding='utf-8')
            with self.assertRaises(Exception): MissionBudget(config, path)

    def test_reservation_survives_restart(self):
        config = load_mission(MANIFEST)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'ledger.json'
            with MissionBudget(config, path) as budget:
                self.assertEqual(budget.reserve(config.start), 23)
            with MissionBudget(config, path) as budget:
                self.assertEqual(budget.remaining(), 23)
