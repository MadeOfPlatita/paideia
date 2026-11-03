import tempfile
import unittest
from pathlib import Path


class SnapshotTests(unittest.TestCase):
    def test_promote_and_restart(self):
        import synthetic_snapshot as s
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'synthetic-snapshot.json'
            repo = s.SyntheticSnapshotRepository(path, clock=lambda: '2026-10-30T04:00:00Z')
            repo.promote(s.fixture_source())
            self.assertEqual(s.SyntheticSnapshotRepository(path, clock=lambda: '2026-10-30T04:00:00Z').get_product('SYN-01')['id'], 'SYN-01')


import copy
import http.client
import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import synthetic_snapshot as s


class SnapshotFailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'synthetic-snapshot.json'
        self.repo = s.SyntheticSnapshotRepository(self.path, clock=lambda: '2026-10-30T04:00:00Z')
        self.source = s.fixture_source()
        self.repo.promote(self.source)

    def test_restart_real_process(self):
        script = "import synthetic_snapshot as s,sys; print(s.SyntheticSnapshotRepository(sys.argv[1],clock=lambda:'2026-10-30T04:00:00Z').get_product('SYN-01')['id'])"
        run = subprocess.run([sys.executable, '-B', '-c', script, str(self.path)], capture_output=True, text=True, check=True)
        self.assertEqual(run.stdout.strip(), 'SYN-01')

    def test_invalid_source_preserves_bytes(self):
        before = self.path.read_bytes()
        cases = []
        def bad(change):
            value = copy.deepcopy(self.source)
            change(value)
            cases.append(value)
        bad(lambda v: v.update(complete=False))
        bad(lambda v: v.update(records=[]))
        bad(lambda v: v.update(expected_ids=['SYN-01', 'SYN-02']))
        bad(lambda v: v.update(freshness_policy=None))
        bad(lambda v: v['freshness_policy'].update(max_age_seconds=0))
        bad(lambda v: v['records'][0].update(permissions='authorized'))
        bad(lambda v: v['records'][0]['name'].update(source_id='real'))
        bad(lambda v: v['records'][0]['name'].update(checked_at='2026-10-30T04:00:01Z'))
        bad(lambda v: v['records'][0]['name'].update(checked_at='2026-10-30T02:00:00Z'))
        bad(lambda v: v['records'][0].update(extra='leak'))
        bad(lambda v: v.update(classification='real'))
        for value in cases:
            with self.subTest(value=value), self.assertRaises(s.SnapshotError):
                self.repo.promote(value)
            self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.repo.count, 1)

    def test_write_and_replace_failures_preserve_bytes_and_cleanup(self):
        before = self.path.read_bytes()
        for target in ('synthetic_snapshot.os.fsync', 'synthetic_snapshot.os.replace', 'synthetic_snapshot.tempfile.mkstemp'):
            with self.subTest(target=target), patch(target, side_effect=OSError('injected')), self.assertRaises(OSError):
                self.repo.promote(self.source)
            self.assertEqual(self.path.read_bytes(), before)
            self.assertEqual(list(Path(self.tmp.name).glob('*.tmp')), [])
            self.assertEqual(self.repo.count, 1)

    def test_failed_write_keeps_last_good(self):
        before = self.path.read_bytes()
        real_fdopen = s.os.fdopen
        class FailingStream:
            def __init__(self, fd, mode):
                self.stream = real_fdopen(fd, mode)
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def write(self, data):
                self.stream.write(data[:10])
                raise OSError('injected write failure')
        with patch('synthetic_snapshot.os.fdopen', side_effect=FailingStream), self.assertRaises(OSError):
            self.repo.promote(self.source)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(Path(self.tmp.name).glob('*.tmp')), [])
        self.assertEqual(self.repo.count, 1)

    def test_corruption_truncation_hash_duplicate_and_staleness_rejected(self):
        good = self.path.read_bytes()
        envelope = json.loads(good)
        envelope['payload']['records'][0]['name']['value'] += ' tampered'
        for data in (b'{', good[:25], json.dumps(envelope).encode(), b'{"payload":{},"payload":{},"sha256":"x"}'):
            with self.subTest(data=data[:30]):
                self.path.write_bytes(data)
                with self.assertRaises(s.SnapshotError):
                    self.repo.list_products()
        self.path.write_bytes(good)
        expired = s.SyntheticSnapshotRepository(self.path, clock=lambda: '2026-10-30T05:00:00Z')
        with self.assertRaises(s.SnapshotError):
            expired.list_products()

    def test_same_instance_threads_and_defensive_copies(self):
        def task(i):
            if i % 4 == 0:
                self.repo.promote(self.source)
            item = self.repo.get_product('SYN-01')
            item['unknown_fields'].append('changed')
            return item['id']
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(list(pool.map(task, range(100))), ['SYN-01'] * 100)
        self.assertNotIn('changed', self.repo.get_product('SYN-01')['unknown_fields'])

    def test_reserved_filename(self):
        with self.assertRaises(s.SnapshotError):
            s.SyntheticSnapshotRepository(Path(self.tmp.name) / 'candidatos.json')


class HttpFixtureTests(unittest.TestCase):
    def test_real_loopback_readonly_test_only_and_no_source_leak(self):
        from serve_synthetic_snapshot import create_fixture_server
        server, repo, directory = create_fixture_server()
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            before = repo.path.read_bytes()
            def request(method, path, body=None):
                connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                try:
                    connection.request(method, path, body=body)
                    response = connection.getresponse()
                    return response.status, response.read()
                finally:
                    connection.close()
            status, raw = request('GET', '/api/catalogue')
            self.assertEqual(status, 200)
            data = json.loads(raw)
            self.assertEqual(data['count'], 1)
            self.assertTrue(data['not_for_publication'])
            item = data['items'][0]
            self.assertIn('SYNTHETIC TEST ONLY', item['name'])
            self.assertIn('synthetic_test', item['unknown_fields'])
            self.assertFalse(item['publication_ready'])
            self.assertNotIn(b'source_id', raw)
            self.assertNotIn(b'freshness_policy', raw)
            self.assertEqual(request('GET', '/api/products/SYN-01')[0], 200)
            self.assertEqual(request('GET', '/api/products/ACC-01')[0], 404)
            self.assertEqual(request('POST', '/api/catalogue', '{}')[0], 405)
            self.assertEqual(request('DELETE', '/api/products/SYN-01')[0], 405)
            self.assertEqual(repo.path.read_bytes(), before)
            repo.path.write_bytes(b'{')
            status, response = request('GET', '/api/catalogue')
            self.assertEqual(status, 500)
            self.assertNotIn(b'synthetic-snapshot', response)
            self.assertNotIn(b'Traceback', response)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            directory.cleanup()
        self.assertFalse(thread.is_alive())


if __name__ == '__main__':
    unittest.main()
