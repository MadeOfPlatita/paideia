"""Synthetic snapshot to real HTTP comparator: no external calls or publication."""
import copy
import tempfile
import unittest
from pathlib import Path
from synthetic_snapshot import SyntheticSnapshotRepository, fixture_source
from test_backend_integration import running_server, request

class SnapshotComparisonHttpTests(unittest.TestCase):
    def test_two_synthetic_candidates_are_metadata_only(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixture_source('2026-10-30T04:00:00Z')
            second = copy.deepcopy(source['records'][0])
            second['id'] = 'SYN-02'
            second['name']['value'] = 'SYNTHETIC TEST ONLY — otro ejemplo'
            source['records'].append(second)
            source['expected_ids'].append('SYN-02')
            repo = SyntheticSnapshotRepository(Path(directory)/'synthetic-snapshot.json', clock=lambda:'2026-10-30T04:01:00Z')
            repo.promote(source)
            with running_server(repository=repo) as server:
                status, body = request(server, '/api/compare', {'product_ids':['SYN-01','SYN-02']})
            self.assertEqual(status, 200)
            self.assertFalse(body['quantitative_ready'])
            self.assertEqual(len(body['items']), 2)
            self.assertTrue(all(not p['publication_ready'] for p in body['items']))
