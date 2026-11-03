"""Contract tests for the offline runner; synthetic inputs only."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import shutil

RUNNER = Path(__file__).resolve().parents[1] / 'scripts' / 'run_offline_regression.py'


class RunnerContractTests(unittest.TestCase):
    def test_runner_present_and_defines_exact_exclusions(self):
        self.assertTrue(RUNNER.is_file(), 'offline runner must exist')
        spec = importlib.util.spec_from_file_location('offline_runner_under_test', RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIn('tests/test_secure_groq_smoke.py::TestSecureGroqSmoke::test_window_masks_key_and_does_not_submit_on_open', module.GUI_EXCLUSIONS)
        self.assertNotIn('tests/test_mission_session.py::MissionSessionTests::test_window_requires_separate_confirmation_and_button_for_benchmark', module.GUI_EXCLUSIONS)
        self.assertNotIn('tests/test_secure_groq_session.py', module.GUI_EXCLUSIONS)

    @unittest.skipUnless(importlib.util.find_spec('pytest'), 'pytest unavailable')
    def test_failing_pytest_and_unittest_both_counted_and_exit_preserved(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            temp = Path(directory)
            case = temp / 'test_sample.py'
            case.write_text('import unittest\nclass Example(unittest.TestCase):\n def test_pass(self): pass\ndef test_failure(): assert False\n', encoding='utf-8')
            out = temp / 'report.json'
            process = subprocess.run([sys.executable, str(RUNNER), '--json', str(out), str(case)], capture_output=True, text=True, timeout=45)
            report = json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
            self.assertEqual(report['exit_status'], 1)
            self.assertEqual(report['counts'], {'unittest': 1, 'pytest_other': 1})
            self.assertEqual(sorted(report['outcomes'].values()), ['failed', 'passed'])

    @unittest.skipUnless(importlib.util.find_spec('pytest'), 'pytest unavailable')
    def test_loopback_is_allowed_and_tk_and_external_are_blocked(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            temp = Path(directory)
            case = temp / 'test_safety.py'
            case.write_text('''import socket, pytest
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading, http.client

def test_guard():
    with pytest.raises(OSError): socket.getaddrinfo('example.invalid', 80)
    with pytest.raises(OSError): socket.socket().connect(('203.0.113.1', 80))
    try: import _tkinter
    except ImportError: pass
    else:
        with pytest.raises(RuntimeError): _tkinter.create()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self): self.send_response(200); self.end_headers()
        def log_message(self, *args): pass
    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
        conn.request('GET', '/')
        assert conn.getresponse().status == 200
        conn.close()
    finally:
        server.shutdown(); server.server_close(); thread.join()
''', encoding='utf-8')
            out = temp / 'report.json'
            process = subprocess.run([sys.executable, str(RUNNER), '--json', str(out), str(case)], capture_output=True, text=True, timeout=45)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertEqual(json.loads(out.read_text(encoding='utf-8'))['outcomes'].popitem()[1], 'passed')

    @unittest.skipUnless(importlib.util.find_spec('pytest'), 'pytest unavailable')
    def test_explicit_gui_case_deselected_but_neighbor_retained(self):
        spec = importlib.util.spec_from_file_location('runner_selection_test', RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        class Item:
            cls = unittest.TestCase
            def __init__(self, nodeid): self.nodeid = nodeid
        class Hook:
            def pytest_deselected(self, items): self.items = items
        class Config: hook = Hook()
        excluded = next(iter(module.GUI_EXCLUSIONS))
        items = [Item(excluded), Item('tests/test_secure_groq_smoke.py::TestSecureGroqSmoke::test_no_network_without_explicit_free_plan_confirmation')]
        collector = module.Collector()
        collector.pytest_collection_modifyitems(Config(), items)
        self.assertEqual(collector.excluded, [excluded])
        self.assertEqual(len(items), 1)
        self.assertEqual(len(collector.collected), 1)

    def test_parameterized_gui_name_is_not_an_exact_exclusion(self):
        spec = importlib.util.spec_from_file_location('runner_exact_selection_test', RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        class Item:
            cls = unittest.TestCase
            nodeid = next(iter(module.GUI_EXCLUSIONS)) + '[synthetic]'
        class Hook:
            def pytest_deselected(self, items): pass
        class Config: hook = Hook()
        items = [Item()]
        collector = module.Collector()
        collector.pytest_collection_modifyitems(Config(), items)
        self.assertEqual(len(items), 1)
        self.assertEqual(collector.excluded, [])

    def run_synthetic(self, source, name='test_case.py'):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / 'tests').mkdir()
            runner = root / 'scripts' / 'run_offline_regression.py'
            shutil.copyfile(RUNNER, runner)
            case = root / 'tests' / name
            case.write_text(source, encoding='utf-8')
            out = root / 'report.json'
            process = subprocess.run([sys.executable, str(runner), '--json', str(out), str(root / 'tests')], capture_output=True, text=True, timeout=45)
            return process.returncode, out.read_text(encoding='utf-8'), process.stdout, process.stderr

    def test_parameter_ids_never_persist_or_print(self):
        code, report, stdout, stderr = self.run_synthetic('import pytest\n@pytest.mark.parametrize("value", ["SYNTHETIC_MARKER_42"])\ndef test_value(value): assert value\n')
        self.assertEqual(code, 0)
        self.assertNotIn('SYNTHETIC_MARKER_42', report + stdout + stderr)

    def test_xfail_and_xpass_are_explicit_non_green(self):
        code, report, _, _ = self.run_synthetic('import pytest\n@pytest.mark.xfail(reason="synthetic")\ndef test_expected(): assert False\n@pytest.mark.xfail(reason="synthetic")\ndef test_unexpected(): pass\n')
        self.assertNotEqual(code, 0)
        self.assertEqual(sorted(json.loads(report)['outcomes'].values()), ['xfailed', 'xpassed'])

    def test_strict_xpass_is_explicit_non_green(self):
        code, report, _, _ = self.run_synthetic('import pytest\n@pytest.mark.xfail(strict=True, reason="synthetic")\ndef test_unexpected(): pass\n')
        self.assertNotEqual(code, 0)
        self.assertEqual(list(json.loads(report)['outcomes'].values()), ['xpassed'])

    def test_xfail_followed_by_teardown_skip_still_fails(self):
        code, report, _, _ = self.run_synthetic('import pytest\n@pytest.fixture\ndef fixture():\n yield\n pytest.skip("synthetic")\n@pytest.mark.xfail\ndef test_case(fixture): assert False\n')
        self.assertNotEqual(code, 0)
        self.assertIn('xfailed', json.loads(report)['outcomes'].values())

    def test_xfail_and_xpass_with_teardown_error_preserve_each_phase(self):
        source = '''import pytest
@pytest.fixture
def fixture():
 yield
 raise RuntimeError("synthetic")
@pytest.mark.xfail(reason="synthetic")
def test_xfail(fixture): assert False
@pytest.mark.xfail(reason="synthetic")
def test_xpass(fixture): pass
'''
        code, report, stdout, stderr = self.run_synthetic(source)
        self.assertNotEqual(code, 0)
        data = json.loads(report)
        phases = list(data['phase_outcomes'].values())
        self.assertEqual(sorted(p['call'] for p in phases), ['xfailed', 'xpassed'])
        self.assertTrue(all(p['setup'] == 'passed' and p['teardown'] == 'failed' for p in phases))
        self.assertEqual(list(data['outcomes'].values()).count('failed'), 2)
        self.assertNotIn('tests/test_case.py::test_', report + stdout + stderr)

    def test_setup_error_is_not_xfailed(self):
        source = '''import pytest
@pytest.fixture
def fixture(): raise RuntimeError("synthetic")
@pytest.mark.xfail(reason="synthetic", raises=AssertionError)
def test_case(fixture): pass
'''
        code, report, _, _ = self.run_synthetic(source)
        self.assertNotEqual(code, 0)
        data = json.loads(report)
        self.assertEqual(list(data['phase_outcomes'].values()), [{'setup': 'failed', 'teardown': 'passed'}])
        self.assertEqual(list(data['outcomes'].values()), ['failed'])

    def test_persisted_gui_exclusions_have_only_hashed_ids(self):
        code, report, stdout, stderr = self.run_synthetic('def test_case(): pass\n')
        self.assertEqual(code, 0)
        data = json.loads(report)
        self.assertEqual(len(data['gui_exclusions']), 6)
        for key in data['gui_exclusions']:
            self.assertRegex(key, r'^[0-9a-f]{64}$')
        self.assertNotIn('tests/test_secure_groq_smoke.py::', report + stdout + stderr)
        self.assertNotIn('tests/test_session_ui_feedback.py::', report + stdout + stderr)

    def test_dynamic_gui_named_module_test_is_collected(self):
        source = '''import unittest
class UIFeedbackTests(unittest.TestCase):
 def test_invalid_clock_fails_closed_without_leaking(self): raise AssertionError("must deselect")
def generated(): assert False
globals()["test_dynamic"] = generated
'''
        code, report, _, _ = self.run_synthetic(source, 'test_session_ui_feedback.py')
        self.assertEqual(code, 1)
        data = json.loads(report)
        self.assertEqual(list(data['outcomes'].values()), ['failed'])
        self.assertEqual(len(data['deselected']), 1)

    def test_collection_error_diagnostic_is_categorized_without_marker(self):
        code, report, stdout, stderr = self.run_synthetic('raise ValueError("SYNTHETIC_MARKER_42")\n')
        self.assertNotEqual(code, 0)
        data = json.loads(report)
        self.assertEqual(data['collection_errors'][0]['stage'], 'collection')
        self.assertEqual(data['collection_errors'][0]['category'], 'ValueError')
        self.assertNotIn('SYNTHETIC_MARKER_42', report + stdout + stderr)
