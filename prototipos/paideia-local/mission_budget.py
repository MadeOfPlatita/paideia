"""Fail-closed, single-live-process mission reservation ledger (no secrets)."""
import json
import os
import threading
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MISSION_ID = '1c203c4baa604133806f36f44102e5e0'
START = '2026-10-29T18:25:00.525905+00:00'
CUTOFF = '2026-10-29T19:25:00.525905+00:00'
NEW_MANIFEST = Path(__file__).resolve().parents[2] / 'docs' / 'ia-real-siguiente' / 'ejecucion' / '20261029T220831Z' / 'MISSION.json'


# Explicit fresh authorization after the previous block expired; no old ledger reset.
REAUTHORIZED_BINDINGS = {
    str((Path(__file__).resolve().parents[2] / 'docs' / 'ia-real-siguiente' / 'ejecucion' / '20261030T005810Z' / 'MISSION.json').resolve()): ('paideia-ia-20261030T005810Z', '2026-10-30T00:58:10.375867+00:00', '2026-10-30T01:58:10.375867+00:00')
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

def load_mission(path):
    path = Path(path)
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
    expected = (Path(__file__).resolve().parents[2] / 'docs' / 'ia-real-siguiente' / 'ejecucion' / MISSION_ID / 'mission.json').resolve()
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

class MissionBudget:
    def __init__(self, config, path=None):
        if not isinstance(config, MissionConfig):
            raise ValueError('invalid mission')
        self.config = config
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
            if os.name == 'nt':
                import msvcrt
                self._lock.seek(0)
                msvcrt.locking(self._lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock.seek(0, 2)
            initialized = self._lock.tell() != 0
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

    def _read(self):
        if self._lock.closed:
            raise RuntimeError('mission lock is closed')
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
            return
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'))
            f.flush()
            os.fsync(f.fileno())

    def remaining(self):
        with self._mutex:
            return self.config.cap - self._read()['used']

    def reserve(self, now=None):
        with self._mutex:
            now = now or datetime.now(timezone.utc)
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
