"""Fail-closed, single-live-process mission reservation ledger (no secrets).

A sealed night mission lives in exactly one canonical directory per operating
system profile and mission identifier, outside every checkout.  A copy of the
tree therefore resolves to the same manifest, seal, journal and ledger; it
cannot silently start a second budget.  The directory must be provisioned
offline with the pre-created ``MISSION.seal``; an identical ``MISSION.json``
copy (for example the one under ``docs``) is accepted only as identity, never
as a state location.  The runtime never creates that seal, so deleting the
ledger, the journal or the seal fails closed instead of starting again at zero.  The seal carries the journal
high-water mark, which rejects replaying both the ledger and journal to an
older consistent state.

A rollback of every local file, seal included, cannot be distinguished from
the last committed state without an external trusted witness; that residual
limit is documented rather than hidden.  This is also not a sandbox against
the process owner or arbitrary Python mutation: the budget is only asserted
for the routes that actually open this ledger.
"""
import json
import os
import re
import threading
import time
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MISSION_ID = '1c203c4baa604133806f36f44102e5e0'
START = '2026-10-29T18:25:00.525905+00:00'
CUTOFF = '2026-10-29T19:25:00.525905+00:00'
NEW_MANIFEST = Path(__file__).resolve().parents[1] / 'docs' / 'ia-real-siguiente' / 'ejecucion' / '20261029T220831Z' / 'MISSION.json'

# Night mission: one canonical directory per OS profile and mission identifier.
# The location is deliberately not derived from __file__: every authorized
# checkout and process of the same profile must resolve to the same ledger.
NIGHT_SCHEMA = 'paideia-night-mission.v1'
NIGHT_MISSION_ID = 'paideia-night-20261104'
NIGHT_START = '2026-11-04T00:00:00Z'
NIGHT_CUTOFF = '2026-11-04T08:00:00Z'
NIGHT_CAP = 20
NIGHT_SEAL_NAME = 'MISSION.seal'
NIGHT_SEAL_SCHEMA = 'paideia-night-ledger-seal.v1'
NIGHT_START_DT = datetime.fromisoformat(NIGHT_START.replace('Z', '+00:00'))
NIGHT_CUTOFF_DT = datetime.fromisoformat(NIGHT_CUTOFF.replace('Z', '+00:00'))
NIGHT_STATE_NAMESPACE = 'Paideia'
NIGHT_MISSION_NAME = 'missions'
_MISSION_ID_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')


def _profile_state_root():
    """Return the per-OS-profile state root, never a checkout location."""
    if os.name == 'nt':
        configured = os.environ.get('LOCALAPPDATA')
        base = Path(configured) if configured and Path(configured).is_absolute() else Path.home() / 'AppData' / 'Local'
    else:
        configured = os.environ.get('XDG_STATE_HOME')
        base = Path(configured) if configured and Path(configured).is_absolute() else Path.home() / '.local' / 'state'
    if not base.is_absolute():
        raise ValueError('invalid profile state root')
    return base


def canonical_mission_state_dir(mission_id):
    """Canonical state directory for one profile and mission identifier.

    The same profile and mission always produce the same absolute path no
    matter which checkout (or copy) is executing.  Different Windows users or
    POSIX home/XDG profiles resolve to different directories.
    """
    if type(mission_id) is not str or _MISSION_ID_PATTERN.fullmatch(mission_id) is None:
        raise ValueError('invalid mission identifier')
    return _profile_state_root() / NIGHT_STATE_NAMESPACE / NIGHT_MISSION_NAME / mission_id


NIGHT_STATE_DIR = canonical_mission_state_dir(NIGHT_MISSION_ID)
NIGHT_MANIFEST = NIGHT_STATE_DIR / 'MISSION.json'
JOURNAL_LOCK_WAIT_SECONDS = 2.0


def _acquire_journal_lock(stream):
    """Bounded wait for the cross-process journal lock.

    A live session keeps the ledger for its whole process.  Waiting briefly
    lets concurrent checkouts or restarts take their turn; a holder that does
    not release within the bound still fails closed rather than bypassing the
    counter.
    """
    deadline = time.monotonic() + JOURNAL_LOCK_WAIT_SECONDS
    while True:
        try:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)


def night_manifest_digest(data):
    """Canonical content digest, independent of checkout line endings."""
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf8')
    return hashlib.sha256(canonical).hexdigest()


# Explicit fresh authorization after the previous block expired; no old ledger reset.
REAUTHORIZED_BINDINGS = {
    str((Path(__file__).resolve().parents[1] / 'docs' / 'ia-real-siguiente' / 'ejecucion' / '20261030T005810Z' / 'MISSION.json').resolve()): ('paideia-ia-20261030T005810Z', '2026-10-30T00:58:10.375867+00:00', '2026-10-30T01:58:10.375867+00:00')
}

@dataclass(frozen=True)
class MissionConfig:
    mission_id: str
    start: datetime
    cutoff: datetime
    cap: int
    directory: Path
    manifest: Path = None
    digest: str = ''
    sealed: bool = False

def load_mission(path):
    path = Path(path)
    if path.is_absolute() and path.name == 'MISSION.json':
        raw = path.read_bytes()
        data = json.loads(raw)
        expected = {'schema', 'mission_id', 'start_utc', 'deadline_utc', 'max_external_attempts'}
        if (type(data) is dict and set(data) == expected
                and data.get('schema') == NIGHT_SCHEMA
                and data.get('mission_id') == NIGHT_MISSION_ID
                and data.get('start_utc') == NIGHT_START
                and data.get('deadline_utc') == NIGHT_CUTOFF
                and type(data.get('max_external_attempts')) is int
                and data['max_external_attempts'] == NIGHT_CAP):
            # Any byte-equivalent copy of the authorized manifest is the same
            # mission, but its state always lives in the canonical profile
            # directory.  A checkout copy cannot create a second ledger.
            return MissionConfig(NIGHT_MISSION_ID, NIGHT_START_DT, NIGHT_CUTOFF_DT, NIGHT_CAP,
                                 NIGHT_MANIFEST.parent, path.resolve(),
                                 night_manifest_digest(data), True)
        if path.resolve() == NIGHT_MANIFEST.resolve():
            raise ValueError('invalid mission manifest')
    binding = (('paideia-ia-20261029T220831Z', '2026-10-29T22:08:31.985015+00:00', '2026-10-29T23:08:31.985015+00:00')
               if path.resolve() == NEW_MANIFEST.resolve() else REAUTHORIZED_BINDINGS.get(str(path.resolve())))
    if path.is_absolute() and binding is not None:
        raw = path.read_bytes()
        data = json.loads(raw)
        if (type(data) is not dict or set(data) != {'schema', 'mission_id', 'start_utc', 'deadline_utc', 'max_external_attempts'}
                or data.get('schema') != 'paideia-mission.v1' or data.get('mission_id') != binding[0]
                or data.get('start_utc') != binding[1]
                or data.get('deadline_utc') != binding[2]
                or type(data.get('max_external_attempts')) is not int or data['max_external_attempts'] != 24):
            raise ValueError('invalid mission manifest')
        return MissionConfig(data['mission_id'], datetime.fromisoformat(data['start_utc'].replace('Z', '+00:00')),
                             datetime.fromisoformat(data['deadline_utc'].replace('Z', '+00:00')), 24,
                             path.parent, path.resolve(), hashlib.sha256(raw).hexdigest())
    expected = (Path(__file__).resolve().parents[1] / 'docs' / 'ia-real-siguiente' / 'ejecucion' / MISSION_ID / 'mission.json').resolve()
    if not path.is_absolute() or path.resolve() != expected:
        raise ValueError('invalid mission path')
    data = json.loads(path.read_text(encoding='utf-8'))
    if (data.get('schema') != 'paideia-ai-mission.v1' or data.get('mission_id') != MISSION_ID
        or data.get('start_utc') != START or data.get('cutoff_utc') != CUTOFF
        or type(data.get('max_external_attempts')) is not int or data['max_external_attempts'] != 24
        or data.get('real_calls_authorized') is not False
        or data.get('authorization_gate') != 'masked_window_and_free_confirmation_required'
        or data.get('state') != 'offline_preflight'
        or data.get('scope') != 'point1_only_no_deploy_no_db_no_payments_no_real_profiles'):
        raise ValueError('invalid mission manifest')
    return MissionConfig(MISSION_ID, datetime.fromisoformat(START), datetime.fromisoformat(CUTOFF), 24, path.parent)


def read_night_seal(config):
    """Pure seal reader: validates the pre-created seal without creating state."""
    if (type(config) is not MissionConfig or not config.sealed or not config.digest
            or config.manifest is None or not config.mission_id):
        raise ValueError('invalid sealed mission')
    data = json.loads((config.directory / NIGHT_SEAL_NAME).read_bytes())
    base = {'schema', 'manifest_sha256', 'mission_id', 'state'}
    if (type(data) is not dict or data.get('schema') != NIGHT_SEAL_SCHEMA
            or data.get('manifest_sha256') != config.digest
            or data.get('mission_id') != config.mission_id
            or data.get('state') not in ('uninitialized', 'initialized')):
        raise ValueError('invalid mission seal')
    if data['state'] == 'uninitialized':
        if set(data) != base:
            raise ValueError('invalid mission seal')
    else:
        if set(data) != base | {'used', 'journal_sha256'}:
            raise ValueError('invalid mission seal')
        used, digest = data.get('used'), data.get('journal_sha256')
        if (type(used) is not int or not 0 <= used <= config.cap
                or type(digest) is not str or len(digest) != 64
                or any(character not in '0123456789abcdef' for character in digest)):
            raise ValueError('invalid mission seal')
    return data

class MissionBudget:
    def __init__(self, config, path=None):
        if not isinstance(config, MissionConfig):
            raise ValueError('invalid mission')
        self.config = config
        if config.sealed:
            # One manifest, one durable counter, twenty attempts. A sealed
            # mission cannot be redirected to a second ledger path.
            if (not config.digest or config.manifest is None
                    or config.directory.resolve() != NIGHT_MANIFEST.parent.resolve()
                    or config.mission_id != NIGHT_MISSION_ID or config.cap != NIGHT_CAP
                    or config.start != NIGHT_START_DT or config.cutoff != NIGHT_CUTOFF_DT):
                raise ValueError('invalid sealed mission')
            if load_mission(config.manifest) != config:
                raise ValueError('mission changed')
            if path is not None and Path(path).resolve() != (config.directory / 'mission-ledger.json').resolve():
                raise ValueError('sealed ledger path is fixed')
            # Read the pre-created seal before touching the filesystem journal:
            # a missing or invalid seal must not even create the lock file.
            seal = read_night_seal(config)
            if seal['state'] == 'initialized':
                missing = [name for name in ('mission-ledger.json', 'mission-ledger.json.lock')
                           if not (config.directory / name).is_file()]
                if missing:
                    raise ValueError('sealed ledger is missing')
        self.path = Path(path) if path is not None else config.directory / 'mission-ledger.json'
        self._mutex = threading.RLock()
        created = False
        if config.digest:
            try:
                self._lock = open(str(self.path) + '.lock', 'x+b')
                created = True
            except FileExistsError:
                self._lock = open(str(self.path) + '.lock', 'a+b')
        else:
            self._lock = open(str(self.path) + '.lock', 'a+b')
        try:
            _acquire_journal_lock(self._lock)
            self._lock.seek(0, 2)
            initialized = self._lock.tell() != 0
            if config.sealed:
                if not initialized and not created:
                    raise ValueError('empty existing journal')
                if initialized and created:
                    raise ValueError('ambiguous sealed journal')
                self._sealed_open(created)
            else:
                if config.digest and not initialized and not created:
                    raise ValueError('empty existing journal')
                if not initialized:
                    self._lock.write(b'1' if not config.digest else b'')
                    self._lock.flush()
                    os.fsync(self._lock.fileno())
                    if self.path.exists():
                        raise ValueError('ambiguous ledger')
                    if config.digest:
                        header = b'NEW-MISSION-LEDGER-v2 ' + config.digest.encode('ascii') + b'\n'
                        if self._lock.write(header) != len(header):
                            raise OSError('incomplete journal header')
                        self._lock.flush()
                        os.fsync(self._lock.fileno())
                    self._write({'mission_id': config.mission_id, 'used': 0, 'last_utc': config.start.isoformat()})
            self._read()
        except Exception:
            self._lock.close()
            raise

    def _seal_path(self):
        return self.config.directory / NIGHT_SEAL_NAME

    def _read_seal(self):
        return read_night_seal(self.config)

    def _write_seal(self, used, journal_sha256):
        payload = {
            'schema': NIGHT_SEAL_SCHEMA,
            'manifest_sha256': self.config.digest,
            'mission_id': self.config.mission_id,
            'state': 'initialized',
            'used': used,
            'journal_sha256': journal_sha256,
        }
        raw = json.dumps(payload, separators=(',', ':')).encode('utf8')
        path = self._seal_path()
        temporary = path.with_name(path.name + '.tmp')
        with open(temporary, 'wb') as stream:
            if stream.write(raw) != len(raw):
                raise OSError('incomplete seal write')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)

    def _sealed_open(self, created):
        seal = self._read_seal()
        if created:
            if seal['state'] != 'uninitialized':
                raise ValueError('sealed journal is missing')
            if self.path.exists():
                raise ValueError('ambiguous sealed ledger')
            header = b'NEW-MISSION-LEDGER-v2 ' + self.config.digest.encode('ascii') + b'\n'
            self._lock.seek(0, 2)
            if self._lock.write(header) != len(header):
                raise OSError('incomplete journal header')
            self._lock.flush()
            os.fsync(self._lock.fileno())
            # _write appends the genesis record, writes the snapshot and raises
            # the seal to its initialized high-water mark.
            self._write({'mission_id': self.config.mission_id, 'used': 0,
                         'last_utc': self.config.start.isoformat()})
        elif seal['state'] != 'initialized':
            raise ValueError('sealed journal is unexpectedly initialized')

    def _validate_seal(self, ledger, journal_raw):
        seal = self._read_seal()
        if seal['state'] != 'initialized' or journal_raw is None or not journal_raw.endswith(b'\n'):
            raise ValueError('ledger replay or seal mismatch')
        last_line = journal_raw.rstrip(b'\n').rsplit(b'\n', 1)[-1]
        if (seal['used'] != ledger['used']
                or seal['journal_sha256'] != hashlib.sha256(last_line).hexdigest()):
            raise ValueError('ledger replay or seal mismatch')

    def _read(self):
        if self._lock.closed:
            raise RuntimeError('mission lock is closed')
        journal_raw = None
        if self.config.digest:
            if load_mission(self.config.manifest) != self.config:
                raise ValueError('mission changed')
            self._lock.seek(0)
            journal_raw = self._lock.read()
            journal = journal_raw.splitlines()
            raw = self.path.read_bytes()
            if (not journal_raw.endswith(b'\n') or len(journal) < 2
                    or journal[0] != b'NEW-MISSION-LEDGER-v2 ' + self.config.digest.encode('ascii')):
                raise ValueError('ledger replay or corruption')
            previous = hashlib.sha256(journal[0]).hexdigest()
            previous_time = self.config.start
            for index, line in enumerate(journal[1:]):
                record = json.loads(line)
                if (type(record) is not dict or set(record) != {'used', 'last_utc', 'snapshot', 'prev'}
                        or type(record['used']) is not int or record['used'] != index
                        or index > self.config.cap or record['prev'] != previous
                        or type(record['last_utc']) is not str):
                    raise ValueError('invalid journal record')
                current_time = datetime.fromisoformat(record['last_utc'])
                if (current_time.utcoffset() is None or current_time < previous_time
                        or current_time >= self.config.cutoff
                        or (index == 0 and record['last_utc'] != self.config.start.isoformat())):
                    raise ValueError('invalid journal clock')
                snapshot = {'mission_id': self.config.mission_id, 'used': index, 'last_utc': record['last_utc']}
                encoded = json.dumps(snapshot, separators=(',', ':')).encode('utf8')
                if (record['snapshot'] != hashlib.sha256(encoded).hexdigest()
                        or line != json.dumps(record, separators=(',', ':')).encode('utf8')):
                    raise ValueError('invalid journal snapshot')
                previous = hashlib.sha256(line).hexdigest()
                previous_time = current_time
            if raw != encoded:
                raise ValueError('ledger replay or corruption')
        data = json.loads(self.path.read_text(encoding='utf-8'))
        if (type(data) is not dict or set(data) != {'mission_id', 'used', 'last_utc'}
            or data['mission_id'] != self.config.mission_id or type(data['used']) is not int
            or not 0 <= data['used'] <= self.config.cap or type(data['last_utc']) is not str):
            raise ValueError('invalid ledger')
        last = datetime.fromisoformat(data['last_utc'])
        if last.utcoffset() is None or last < self.config.start or last >= self.config.cutoff:
            raise ValueError('invalid ledger clock')
        if self.config.sealed:
            self._validate_seal(data, journal_raw)
        return data

    def _write(self, data):
        # A torn or interrupted write is invalid and blocks all future reservations.
        if self.config.digest:
            raw = json.dumps(data, separators=(',', ':')).encode('utf8')
            self._lock.seek(0)
            lines = self._lock.read().splitlines()
            record = {'used': data['used'], 'last_utc': data['last_utc'],
                      'snapshot': hashlib.sha256(raw).hexdigest(),
                      'prev': hashlib.sha256(lines[-1]).hexdigest()}
            entry = json.dumps(record, separators=(',', ':')).encode('utf8') + b'\n'
            self._lock.seek(0, 2)
            if self._lock.write(entry) != len(entry):
                raise OSError('incomplete journal write')
            self._lock.flush()
            os.fsync(self._lock.fileno())
            with open(self.path, 'wb') as f:
                if f.write(raw) != len(raw):
                    raise OSError('incomplete ledger write')
                f.flush()
                os.fsync(f.fileno())
            if self.config.sealed:
                # The seal is pre-created and is never recreated by the
                # runtime: deleting the ledger cannot silently reset it.
                self._write_seal(data['used'], hashlib.sha256(entry[:-1]).hexdigest())
            return
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'))
            f.flush()
            os.fsync(f.fileno())

    def verify_cutoff(self, now=None):
        with self._mutex:
            if self._lock.closed:
                raise RuntimeError('mission unavailable')
            now = now or datetime.now(timezone.utc)
            if not isinstance(now, datetime) or now.utcoffset() is None:
                raise RuntimeError('mission unavailable')
            current = now.astimezone(timezone.utc)
            if current < self.config.start or current >= self.config.cutoff:
                raise RuntimeError('mission unavailable')
            if self.config.sealed and self._read_seal()['state'] != 'initialized':
                raise RuntimeError('mission unavailable')
            return True

    def remaining(self):
        with self._mutex:
            return self.config.cap - self._read()['used']

    def reserve(self, now=None):
        with self._mutex:
            now = now or datetime.now(timezone.utc)
            self.verify_cutoff(now)
            data = self._read()
            if (not isinstance(now, datetime) or now.utcoffset() is None or now < self.config.start
                or now < datetime.fromisoformat(data['last_utc']) or now >= self.config.cutoff
                or data['used'] >= self.config.cap):
                raise RuntimeError('mission unavailable')
            data['used'] += 1
            data['last_utc'] = now.astimezone(timezone.utc).isoformat()
            self._write(data)
            return self.config.cap - data['used']

    def close(self):
        with self._mutex:
            if not self._lock.closed:
                self._lock.close()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()
