import unittest
from pathlib import Path
from mission_budget import load_mission
class ReauthorizedMissionTests(unittest.TestCase):
    def test_explicitly_authorized_new_block_loads_without_changing_old_block(self):
        path=Path(__file__).resolve().parents[2]/'docs/ia-real-siguiente/ejecucion'/'20261030T005810Z'/'MISSION.json'
        accepted=False
        try:
            config=load_mission(path)
            accepted=config.mission_id=='paideia-ia-20261030T005810Z' and config.cap==24
        except ValueError:
            pass
        self.assertTrue(accepted,'Explicit newly authorized block must load separately from old ledger')
