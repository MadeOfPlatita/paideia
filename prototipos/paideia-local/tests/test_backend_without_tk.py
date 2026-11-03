"""Backend and GUI dependency boundary in isolated interpreters."""
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
BLOCK_TK = r'''
import builtins
original_import = builtins.__import__
def block_tk(name, *args, **kwargs):
    if name == "tkinter" or name.startswith("tkinter.") or name == "_tkinter":
        raise ModuleNotFoundError("tkinter blocked by test", name=name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = block_tk
'''


class BackendWithoutTkTests(unittest.TestCase):
    def run_isolated(self, script):
        result = subprocess.run([sys.executable, '-c', BLOCK_TK + textwrap.dedent(script)],
                                cwd=APP_DIR, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_import_backend_and_app_without_tk(self):
        self.run_isolated('''
            import backend_services
            import app
        ''')

    def test_loopback_status_without_tk_or_external_sockets(self):
        self.run_isolated('''
            import socket
            real_socket = socket.socket
            real_getaddrinfo = socket.getaddrinfo
            class LoopbackSocket(real_socket):
                def connect(self, address):
                    assert isinstance(address, tuple) and address[0] == '127.0.0.1', address
                    return super().connect(address)
                def connect_ex(self, address):
                    assert isinstance(address, tuple) and address[0] == '127.0.0.1', address
                    return super().connect_ex(address)
                def bind(self, address):
                    assert isinstance(address, tuple) and address[0] == '127.0.0.1', address
                    return super().bind(address)
            def loopback_dns(host, *args, **kwargs):
                assert host == '127.0.0.1', host
                return real_getaddrinfo(host, *args, **kwargs)
            socket.socket = LoopbackSocket
            socket.getaddrinfo = loopback_dns
            import app
            import http.client
            import json
            import threading
            server = app.create_server(port=0)
            worker = threading.Thread(target=server.serve_forever)
            worker.start()
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            try:
                conn.request('GET', '/api/status')
                response = conn.getresponse()
                body = json.loads(response.read())
                assert response.status == 200, response.status
                assert body['mode'] == 'local_prototype', body
                assert 'ai' in body and 'catalogue' in body, body
            finally:
                conn.close()
                server.shutdown()
                worker.join(timeout=5)
                server.server_close()
                assert not worker.is_alive()
        ''')

    def test_legacy_tk_module_attributes_remain_available_lazily(self):
        result = subprocess.run([sys.executable, '-c', textwrap.dedent('''
            import secure_groq_session as session
            try:
                import tkinter
                from tkinter import ttk
            except ImportError:
                print('TK_UNAVAILABLE')
            else:
                assert session.tk is tkinter
                assert session.ttk is ttk
        ''')], cwd=APP_DIR, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        if 'TK_UNAVAILABLE' in result.stdout:
            self.skipTest('tkinter is not installed')

    def test_legacy_gui_module_override_is_honored(self):
        result = subprocess.run([sys.executable, '-c', textwrap.dedent('''
            import secure_groq_session as session
            try:
                import tkinter
            except ImportError:
                print('TK_UNAVAILABLE')
            else:
                from types import SimpleNamespace
                from unittest.mock import patch
                class Marker(Exception): pass
                def fake_tk(): raise Marker()
                with patch.object(tkinter, 'Tk', side_effect=AssertionError('native Tk forbidden')), patch.object(session, 'tk', SimpleNamespace(Tk=fake_tk)):
                    try:
                        session.create_window()
                    except Marker:
                        pass
                    else:
                        raise AssertionError('legacy tk override was ignored')
        ''')], cwd=APP_DIR, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        if 'TK_UNAVAILABLE' in result.stdout:
            self.skipTest('tkinter is not installed')

    def test_missing_tk_does_not_initialize_mission_budget(self):
        self.run_isolated('''
            import secure_groq_session as session
            from unittest.mock import patch
            with patch.object(session, 'MissionBudget', side_effect=AssertionError('budget must not open')) as budget:
                try:
                    session.create_window(mission_config=object())
                except RuntimeError as exc:
                    assert 'tkinter' in str(exc).lower(), str(exc)
                else:
                    raise AssertionError('GUI should require tkinter')
                budget.assert_not_called()
        ''')

    def test_missing_tk_has_explicit_gui_error(self):
        self.run_isolated('''
            import secure_groq_session
            try:
                secure_groq_session.create_window()
            except RuntimeError as exc:
                assert 'tkinter' in str(exc).lower(), str(exc)
            else:
                raise AssertionError('GUI should require tkinter')
        ''')


if __name__ == '__main__':
    unittest.main()
