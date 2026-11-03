"""Loopback TEST ONLY: two invented identities; no numeric facts or permissions."""
from datetime import datetime,timezone
from pathlib import Path
import copy,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from synthetic_snapshot import SyntheticSnapshotRepository,fixture_source

def main():
    with tempfile.TemporaryDirectory(prefix='paideia-compare-fixture-') as directory:
        now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        source=fixture_source(now)
        second=copy.deepcopy(source['records'][0]);second['id']='SYN-02';second['name']['value']='SYNTHETIC TEST ONLY — segundo'
        source['records'].append(second);source['expected_ids'].append('SYN-02')
        repo=SyntheticSnapshotRepository(Path(directory)/'synthetic-snapshot.json');repo.promote(source)
        server=app.create_server(port=0,repository=repo)
        print('COMPARISON_FIXTURE test_only=True url=http://127.0.0.1:'+str(server.server_port),flush=True)
        try:server.serve_forever()
        finally:server.server_close()
if __name__=='__main__':main()
