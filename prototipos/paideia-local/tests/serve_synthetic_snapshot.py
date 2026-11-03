"""TEST ONLY loopback server with isolated in-memory synthetic source; never production."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from synthetic_snapshot import SyntheticSnapshotRepository, fixture_source


def create_fixture_server():
    directory = tempfile.TemporaryDirectory(prefix='paideia-synthetic-test-')
    repo = SyntheticSnapshotRepository(Path(directory.name) / 'synthetic-snapshot.json')
    repo.promote(fixture_source(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')))
    try:
        server = app.create_server(host='127.0.0.1', port=0, repository=repo)
    except Exception:
        directory.cleanup()
        raise
    return server, repo, directory


if __name__ == '__main__':
    server, repo, directory = create_fixture_server()
    print('TEST ONLY synthetic fixture http://127.0.0.1:%d' % server.server_port, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        directory.cleanup()
