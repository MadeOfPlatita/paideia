import tempfile
import unittest
import threading
from unittest.mock import patch
from datetime import datetime, timedelta
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from mission_budget import MissionBudget, load_mission
from secure_groq_session import Session
import secure_groq_session as launcher
from tests.test_session_send_boundary import FakeConnection, MESSAGE
from providers import ProviderError
from structured_session_fixture import StructuredSessionFixture

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'docs/ia-real-siguiente/ejecucion/1c203c4baa604133806f36f44102e5e0/mission.json'
BODY = b'{"choices":[{"message":{"role":"assistant","content":"synthetic"},"finish_reason":"stop"}]}'

def Transport():
    return StructuredSessionFixture(200, BODY)

class Widget:
    def __init__(self, *args, **kwargs): self.value = ''
    def pack(self, **kwargs): pass
    def get(self): return self.value
    def delete(self, *args): self.value = ''
    def configure(self, **kwargs): pass
class Root(Widget):
    def title(self, *args): pass
    def geometry(self, *args): pass
    def protocol(self, *args): pass
    def after(self, *args): return 'timer'
    def after_cancel(self, *args): pass
    def destroy(self): pass
class Variable:
    def __init__(self, root, value=None): self.value = value
    def get(self): return self.value
    def set(self, value): self.value = value

class MissionSessionTests(unittest.TestCase):
    def test_window_test_restores_mission_budget_after_cleanup(self):
        original = launcher.MissionBudget
        case = MissionSessionTests('test_window_requires_separate_confirmation_and_button_for_benchmark')
        try:
            result = unittest.TestResult()
            case.run(result)
            self.assertTrue(result.wasSuccessful(), (result.failures, result.errors))
            self.assertIs(launcher.MissionBudget, original)
        finally:
            launcher.MissionBudget = original

    def test_window_test_restores_mission_budget_after_exception(self):
        original = launcher.MissionBudget
        case = MissionSessionTests('test_window_requires_separate_confirmation_and_button_for_benchmark')
        try:
            with patch.object(launcher, 'create_window', side_effect=RuntimeError('synthetic')):
                result = unittest.TestResult()
                case.run(result)
            self.assertEqual(len(result.errors), 1)
            self.assertIs(launcher.MissionBudget, original)
        finally:
            launcher.MissionBudget = original

    def test_transport_failure_consumes_persisted_reservation(self):
        config = load_mission(MANIFEST)
        now = config.start + timedelta(seconds=1)
        class ClockMeta(type):
            def __instancecheck__(cls, value): return isinstance(value, datetime)
        class FrozenDateTime(datetime, metaclass=ClockMeta):
            @classmethod
            def now(cls, tz=None): return now
        class BrokenConnection(FakeConnection):
            def connect(self): raise OSError('synthetic')
        with tempfile.TemporaryDirectory() as d:
            # The production-only path requires its fixed ledger location; relocate
            # a synthetic copy and stub manifest lookup, never the transport.
            config = replace(config, directory=Path(d))
            path = Path(d) / 'mission-ledger.json'
            with MissionBudget(config, path) as budget, \
                 patch.object(launcher, 'load_mission', return_value=config), \
                 patch.object(launcher, 'datetime', FrozenDateTime), \
                 patch('providers.http.client.HTTPSConnection', BrokenConnection):
                session = Session('FAKE', mission_budget=budget)
                with self.assertRaises(ProviderError) as caught: session.provider.chat(MESSAGE)
                self.assertEqual(caught.exception.code, 'transport_error')
                self.assertEqual(session.status()['calls'], 1)
            with MissionBudget(config, path) as reopened:
                self.assertEqual(reopened.remaining(), 23)

    def test_closed_lock_revokes_active_session_before_any_send(self):
        config = load_mission(MANIFEST)
        now = config.start + timedelta(seconds=1)
        with tempfile.TemporaryDirectory() as d:
            budget = MissionBudget(config, Path(d) / 'ledger')
            session = Session('FAKE', transport=Transport(), test_only=True, clock=lambda: now, mission_budget=budget)
            budget.close()
            self.assertEqual(session.status()['state'], 'revoked')
            self.assertEqual(session._environment, {})

    def test_final_remaining_slot_survives_connect_and_auto_close(self):
        config = load_mission(MANIFEST)
        now = config.start + timedelta(seconds=1)
        with tempfile.TemporaryDirectory() as d:
            config = replace(config, directory=Path(d))
            class ClockMeta(type):
                def __instancecheck__(cls, value): return isinstance(value, datetime)
            class FrozenDateTime(datetime, metaclass=ClockMeta):
                @classmethod
                def now(cls, tz=None): return now
            with MissionBudget(config, Path(d) / 'mission-ledger.json') as budget, \
                 patch.object(launcher, 'load_mission', return_value=config), \
                 patch.object(launcher, 'datetime', FrozenDateTime), \
                 patch('providers.http.client.HTTPSConnection', FakeConnection):
                for _ in range(23): budget.reserve(now)
                FakeConnection.entered, FakeConnection.release = threading.Event(), threading.Event()
                FakeConnection.requests = []
                session = Session('FAKE', mission_budget=budget)
                results = []
                thread = threading.Thread(target=lambda: results.append(session.provider.chat(MESSAGE)))
                thread.start()
                try:
                    self.assertTrue(FakeConnection.entered.wait(2))
                    state = session.status()
                    self.assertEqual(state['mission_remaining'], 0)
                    self.assertTrue(state['final_pending'])
                    self.assertFalse(launcher.should_auto_close(state))
                    self.assertEqual(session._environment, {})
                finally:
                    FakeConnection.release.set()
                    thread.join(3)
                self.assertFalse(thread.is_alive())
                self.assertEqual(len(FakeConnection.requests), 1)
                self.assertEqual(results[0].answer, 'synthetic')
                self.assertTrue(launcher.should_auto_close(session.status()))

    def test_window_requires_separate_confirmation_and_button_for_benchmark(self):
        config = load_mission(MANIFEST)
        now = config.start + timedelta(seconds=1)
        with tempfile.TemporaryDirectory() as d, MissionBudget(config, Path(d) / 'ledger') as budget:
            tk = SimpleNamespace(Tk=Root, BooleanVar=Variable, StringVar=Variable, END='end')
            ttk = SimpleNamespace(**{n: Widget for n in ('Frame','Label','Entry','Checkbutton','Button')})
            patches = [patch.object(launcher, 'MissionBudget', side_effect=lambda *_: budget),
                       patch.object(launcher, 'tk', tk, create=True),
                       patch.object(launcher, 'ttk', ttk, create=True),
                       patch.object(Session, 'start_server', return_value=SimpleNamespace(server_port=0)),
                       patch.object(Session, 'start_benchmark', return_value=True)]
            for p in patches: p.start(); self.addCleanup(p.stop)
            ui = launcher.create_window(mission_config=config, test_only=True, transport=Transport(), clock=lambda: now, port=0)
            self.assertFalse(ui['confirmed'].get())
            self.assertFalse(ui['benchmark_confirmed'].get())
            ui['entry'].value = 'FAKE'
            ui['start']()
            self.assertIsNone(ui['session']())
            self.assertEqual(budget.remaining(), 24)
            ui['benchmark_confirmed'].set(True)
            ui['confirmed'].set(True)
            # Restore the real class for isinstance checks after construction.
            patches[0].stop()
            ui['start']()
            self.assertIsNotNone(ui['session']())
            self.assertEqual(ui['entry'].value, '')
            self.assertFalse(Session.start_benchmark.called)
            self.assertTrue(ui['start_evaluation']())
            Session.start_benchmark.assert_called_once_with(confirmed=True)
            ui['close']()
    def test_corrupt_ledger_revokes_on_status(self):
        config = load_mission(MANIFEST)
        now = config.start + timedelta(seconds=1)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'ledger'
            with MissionBudget(config, path) as budget:
                session = Session('FAKE', transport=Transport(), test_only=True, clock=lambda: now, mission_budget=budget)
                path.write_text('corrupt', encoding='utf-8')
                self.assertEqual(session.status()['state'], 'revoked')
                self.assertEqual(session._environment, {})

    def test_cli_passes_fixed_mission_config_to_window_without_network(self):
        with patch('sys.argv', ['launcher', '--mission-config', str(MANIFEST)]), \
             patch.object(launcher, 'create_window') as window:
            launcher.main()
            self.assertEqual(window.call_args.kwargs['mission_config'], load_mission(MANIFEST))
            window.return_value['root'].mainloop.assert_called_once()

    def test_final_remaining_slot_revokes_key(self):
        config = load_mission(MANIFEST)
        now = config.start + timedelta(seconds=1)
        with tempfile.TemporaryDirectory() as d:
            with MissionBudget(config, Path(d) / 'ledger') as budget:
                for _ in range(23): budget.reserve(now)
                session = Session('FAKE', transport=Transport(), test_only=True, clock=lambda: now, mission_budget=budget)
                self.assertEqual(session.provider.chat(MESSAGE).answer, 'synthetic')
                self.assertEqual(session.status()['state'], 'quota_exhausted')
                self.assertEqual(session._environment, {})
                self.assertEqual(budget.remaining(), 0)
