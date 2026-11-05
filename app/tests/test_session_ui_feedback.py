import time
import unittest
from datetime import timedelta
from unittest.mock import patch
import tkinter as tk

import secure_groq_session as module
from test_secure_groq_session import Clock
from structured_session_fixture import StructuredSessionFixture


class UIFeedbackTests(unittest.TestCase):
    def make_ui(self, clock, mission_config=None):
        original = tk.Tk
        def hidden_root():
            root = original()
            root.withdraw()
            return root
        with patch.object(module.tk, 'Tk', hidden_root):
            ui = module.create_window(test_only=True, transport=StructuredSessionFixture(200, b'{}'), clock=clock, port=0, mission_config=mission_config)
        ui['root'].update_idletasks()
        self.addCleanup(lambda: self.close_ui(ui))
        return ui

    @staticmethod
    def close_ui(ui):
        if ui['root'].winfo_exists():
            ui['close']()

    @staticmethod
    def button(ui):
        frame = ui['entry'].master
        return next(w for w in frame.winfo_children() if w.winfo_class() == 'TButton' and w.cget('text') == 'Iniciar sesión limitada')

    def test_failed_start_is_terminal_and_explains_occupied_port(self):
        ui = self.make_ui(Clock())
        ui['entry'].insert(0, 'FAKE-ONLY')
        ui['confirmed'].set(True)
        with patch.object(module.Session, 'start_server', side_effect=OSError('FAKE-ONLY private detail')):
            self.button(ui).invoke()
        self.assertIn('puerto', ui['status'].get().lower())
        self.assertIn('cierra', ui['status'].get().lower())
        self.assertNotIn('FAKE-ONLY', ui['status'].get())
        self.assertEqual(str(self.button(ui).cget('state')), 'disabled')
        self.assertEqual(ui['entry'].get(), '')

    def test_pending_expiry_erases_entry_and_disables_start(self):
        clock = Clock()
        ui = self.make_ui(clock)
        ui['entry'].insert(0, 'FAKE-ONLY')
        clock.now = module.HARD_DEADLINE
        end = time.monotonic() + 0.8
        while time.monotonic() < end:
            ui['root'].update()
            time.sleep(0.01)
        self.assertIn('vencido', ui['status'].get().lower())
        self.assertEqual(str(self.button(ui).cget('state')), 'disabled')
        self.assertEqual(ui['entry'].get(), '')
    def test_mission_cutoff_overrides_legacy_on_button_invoke(self):
        from types import SimpleNamespace
        clock = Clock()
        config = SimpleNamespace(cutoff=clock.now + timedelta(hours=3), cap=24)
        class Budget:
            def __init__(self, config): pass
            def remaining(self): return 24
            def close(self): pass
        with patch.object(module, 'MissionBudget', Budget):
            ui = self.make_ui(clock, config)
        ui['entry'].insert(0, 'FAKE-ONLY')
        clock.now = config.cutoff
        self.button(ui).invoke()
        self.assertIn('vencido', ui['status'].get().lower())
        self.assertEqual(ui['entry'].get(), '')
        self.assertEqual(str(self.button(ui).cget('state')), 'disabled')

    def test_invalid_clock_fails_closed_without_leaking(self):
        def broken(): raise RuntimeError('FAKE-ONLY private detail')
        ui = self.make_ui(broken)
        ui['entry'].insert(0, 'FAKE-ONLY')
        self.button(ui).invoke()
        self.assertIn('reloj', ui['status'].get().lower())
        self.assertNotIn('FAKE-ONLY', ui['status'].get())
        self.assertEqual(ui['entry'].get(), '')
        self.assertEqual(str(self.button(ui).cget('state')), 'disabled')


if __name__ == '__main__':
    unittest.main()
