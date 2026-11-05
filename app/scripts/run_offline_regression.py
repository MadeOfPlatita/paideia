#!/usr/bin/env python3
"""Guarded pytest runner, not a sandbox.

The Tk and network guards apply only in this Python process; subprocesses do
not inherit them. Run only audited tests whose children are independently
offline and headless. No guarantee is made about arbitrary test code or cleanup.

Subprocess inventory at review: test_backend_without_tk starts Python for
import/loopback checks (its own Tk blocking or fake widget), mission_budget and
session_mission start Python for local lock checks, synthetic_snapshot reads a
local synthetic file, and test_offline_regression_runner starts this guarded
runner on synthetic files. These observations are not enforcement: re-audit
the commands and any indirect child behavior whenever tests change.
"""
import argparse
import hashlib
import contextlib
import io
import importlib.util
import ipaddress
import json
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI_EXCLUSIONS = {
    'tests/test_secure_groq_smoke.py::TestSecureGroqSmoke::test_window_masks_key_and_does_not_submit_on_open': 'constructs a real Tk window',
    'tests/test_secure_groq_smoke.py::TestSecureGroqSmoke::test_window_roundtrip_saves_sanitized_result_without_key': 'constructs a real Tk window',
    'tests/test_session_ui_feedback.py::UIFeedbackTests::test_failed_start_is_terminal_and_explains_occupied_port': 'constructs a real Tk window',
    'tests/test_session_ui_feedback.py::UIFeedbackTests::test_pending_expiry_erases_entry_and_disables_start': 'constructs a real Tk window',
    'tests/test_session_ui_feedback.py::UIFeedbackTests::test_mission_cutoff_overrides_legacy_on_button_invoke': 'constructs a real Tk window',
    'tests/test_session_ui_feedback.py::UIFeedbackTests::test_invalid_clock_fails_closed_without_leaking': 'constructs a real Tk window',
}
def opaque_id(nodeid):
    return hashlib.sha256(nodeid.encode('utf-8')).hexdigest()


def forbid_gui_and_external_network():
    """Block native Tcl interpreter creation and non-loopback socket connections."""
    try:
        import _tkinter
    except ImportError:
        pass
    else:
        def no_tk(*args, **kwargs):
            raise RuntimeError('Tk construction prohibited by offline runner')
        _tkinter.create = no_tk
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_sendto = socket.socket.sendto
    original_bind = socket.socket.bind
    def check(address):
        if not isinstance(address, tuple) or not address:
            raise OSError('offline runner blocks non-loopback connection')
        host = address[0]
        try:
            allowed = ipaddress.ip_address(host).is_loopback
        except ValueError:
            allowed = host.lower() == 'localhost'
        if not allowed:
            raise OSError('offline runner blocks non-loopback connection')
    def connect(sock, address):
        check(address)
        return original_connect(sock, address)
    def connect_ex(sock, address):
        check(address)
        return original_connect_ex(sock, address)
    def sendto(sock, *args):
        check(args[-1])
        return original_sendto(sock, *args)
    def bind(sock, address):
        check(address)
        return original_bind(sock, address)
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.socket.sendto = sendto
    socket.socket.bind = bind
    original_getaddrinfo = socket.getaddrinfo
    def getaddrinfo(host, *args, **kwargs):
        check((host, 0))
        return original_getaddrinfo(host, *args, **kwargs)
    socket.getaddrinfo = getaddrinfo


class Collector:
    def __init__(self):
        self.collected = []
        self.excluded = []
        self.results = {}
        self.phase_results = {}
        self.phase_errors = set()
        self.ignored_modules = []
        self.collection_errors = []
        self.saw_xfail = False

    def pytest_collectreport(self, report):
        if report.failed:
            message = getattr(getattr(report.longrepr, 'reprcrash', None), 'message', '')
            category = message.split(':', 1)[0]
            allowed = {'ImportError', 'ModuleNotFoundError', 'SyntaxError', 'ValueError',
                       'RuntimeError', 'TypeError', 'OSError', 'AttributeError', 'NameError'}
            self.collection_errors.append({'id': opaque_id(report.nodeid), 'stage': 'collection',
                                           'category': category if category in allowed else 'other'})

    def pytest_collection_modifyitems(self, config, items):
        import unittest
        selected, deselected = [], []
        for item in items:
            if item.nodeid in GUI_EXCLUSIONS:
                self.excluded.append(item.nodeid)
                deselected.append(item)
            else:
                cls = getattr(item, 'cls', None)
                kind = 'unittest' if isinstance(cls, type) and issubclass(cls, unittest.TestCase) else 'pytest_other'
                self.collected.append({'id': item.nodeid, 'kind': kind})
                selected.append(item)
        items[:] = selected
        config.hook.pytest_deselected(items=deselected)

    def pytest_runtest_makereport(self, item, call):
        # pytest's xfail plugin can transform a fixture error into a skip.
        # Record the original exception before that transformation, without its text.
        if call.when in ('setup', 'teardown') and call.excinfo:
            import pytest
            if not isinstance(call.excinfo.value, (pytest.skip.Exception, pytest.xfail.Exception)):
                self.phase_errors.add((item.nodeid, call.when))

    def pytest_runtest_logreport(self, report):
        outcome = report.outcome
        if (report.nodeid, report.when) in self.phase_errors:
            outcome = 'failed'
        elif hasattr(report, 'wasxfail'):
            outcome = 'xpassed' if report.passed else 'xfailed'
        elif report.failed and str(report.longrepr).startswith('[XPASS(strict)]'):
            outcome = 'xpassed'
        phases = self.phase_results.setdefault(report.nodeid, {})
        phases[report.when] = outcome
        if outcome in ('failed', 'xfailed', 'xpassed'):
            self.saw_xfail = True
        priority = {'passed': 0, 'skipped': 1, 'xfailed': 2, 'xpassed': 3, 'failed': 4}
        self.results[report.nodeid] = max(phases.values(), key=priority.__getitem__)


def run(output, tests=None, collect_only=False):
    result = {'engine': 'pytest', 'collected': [], 'counts': {'unittest': 0, 'pytest_other': 0},
              'gui_exclusions': {opaque_id(nodeid): reason for nodeid, reason in GUI_EXCLUSIONS.items()},
              'deselected': [], 'outcomes': {}, 'phase_outcomes': {}, 'exit_status': 2,
              'guard_scope': 'in-process only; child processes do not inherit guards; not a sandbox; audit tests and children for offline/headless behavior'}
    if importlib.util.find_spec('pytest') is None:
        result['error'] = 'pytest is not installed in this interpreter; cannot safely run pytest function tests. No suite was run.'
    else:
        import pytest
        forbid_gui_and_external_network()
        for directory in (ROOT, ROOT / 'tests'):
            if str(directory) not in sys.path:
                sys.path.insert(0, str(directory))
        collector = Collector()
        args = ['-q', '--disable-warnings', '-p', 'no:cacheprovider']
        if collect_only:
            args.append('--collect-only')
        args.extend(tests or [str(ROOT / 'tests')])
        # Plugin autoload can introduce unrelated side effects; only pytest built-ins are needed.
        import os
        os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        old = Path.cwd()
        try:
            os.chdir(ROOT)
            # Do not persist pytest tracebacks/captured output, which may contain secrets.
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result['exit_status'] = int(pytest.main(args, plugins=[collector]))
        finally:
            os.chdir(old)
        if result['exit_status'] == 0 and collector.saw_xfail:
            result['exit_status'] = 1
        result['collected'] = [{'id': opaque_id(item['id']), 'kind': item['kind']} for item in collector.collected]
        result['deselected'] = sorted(opaque_id(nodeid) for nodeid in collector.excluded)
        result['ignored_modules'] = collector.ignored_modules
        result['collection_errors'] = collector.collection_errors
        result['outcomes'] = {opaque_id(nodeid): outcome for nodeid, outcome in collector.results.items()}
        result['phase_outcomes'] = {opaque_id(nodeid): phases for nodeid, phases in collector.phase_results.items()}
        for item in collector.collected:
            result['counts'][item['kind']] += 1
    path = Path(output).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result['exit_status']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', required=True, help='Explicit output JSON path (relative to current directory or absolute)')
    parser.add_argument('--collect-only', action='store_true')
    parser.add_argument('tests', nargs='*', help='Optional pytest paths or node IDs; default tests/')
    args = parser.parse_args()
    return run(args.json, args.tests, args.collect_only)


if __name__ == '__main__':
    sys.exit(main())
