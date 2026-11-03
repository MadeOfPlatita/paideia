"""EXPERIMENTAL synthetic_test only; never connect this to production.

One repository instance in one process; caller exclusively owns its directory.
No source/network client, no real catalogue data or permissions.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from datetime import datetime, timezone


class SnapshotError(ValueError):
    pass


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SnapshotError('duplicate JSON key')
        result[key] = value
    return result


def _time(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        raise SnapshotError('invalid UTC timestamp')
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise SnapshotError('invalid UTC timestamp') from exc


def fixture_source(now='2026-10-30T04:00:00Z'):
    """Nonfinancial invented identity and a deliberately fixture-only TTL."""
    def field(value):
        return {'value': value, 'source_id': 'synthetic_test:fixture', 'checked_at': now, 'effective_at': now}
    return {'schema_version': 'synthetic-source.v1', 'classification': 'synthetic_test',
            'complete': True, 'expected_ids': ['SYN-01'],
            'freshness_policy': {'version': 'fixture-only.v1', 'max_age_seconds': 3600},
            'records': [{'id': 'SYN-01', 'name': field('SYNTHETIC TEST ONLY — ejemplo'),
                         'family': field('deposito'), 'permissions': 'unknown'}]}


def _validate(source, now):
    def exact(value, keys):
        if type(value) is not dict or set(value) != set(keys):
            raise SnapshotError('unexpected or missing fields')
    exact(source, ('schema_version', 'classification', 'complete', 'expected_ids', 'freshness_policy', 'records'))
    if source['schema_version'] != 'synthetic-source.v1' or source['classification'] != 'synthetic_test' or source['complete'] is not True:
        raise SnapshotError('unsupported or incomplete source')
    policy = source['freshness_policy']
    exact(policy, ('version', 'max_age_seconds'))
    age = policy['max_age_seconds']
    if policy['version'] != 'fixture-only.v1' or type(age) is not int or age <= 0:
        raise SnapshotError('explicit fixture freshness policy required')
    ids, rows = source['expected_ids'], source['records']
    if type(ids) is not list or not ids or type(rows) is not list or len(rows) != len(ids):
        raise SnapshotError('partial source')
    if any(type(x) is not str or not re.fullmatch(r'SYN-[A-Z0-9]{1,12}', x) for x in ids) or len(set(ids)) != len(ids):
        raise SnapshotError('invalid expected identifiers')
    seen = set()
    now = _time(now)
    for row in rows:
        exact(row, ('id', 'name', 'family', 'permissions'))
        if type(row['id']) is not str or row['id'] not in ids or row['id'] in seen or row['permissions'] != 'unknown':
            raise SnapshotError('invalid identifier or permission')
        seen.add(row['id'])
        for key in ('name', 'family'):
            field = row[key]
            exact(field, ('value', 'source_id', 'checked_at', 'effective_at'))
            if field['source_id'] != 'synthetic_test:fixture':
                raise SnapshotError('invalid provenance')
            checked, effective = _time(field['checked_at']), _time(field['effective_at'])
            if effective > now or checked > now or effective > checked or (now - checked).total_seconds() >= age:
                raise SnapshotError('future or expired synthetic field')
        if type(row['name']['value']) is not str or not row['name']['value'].startswith('SYNTHETIC TEST ONLY — ') or len(row['name']['value']) > 100:
            raise SnapshotError('invalid synthetic name')
        if row['family']['value'] not in ('cuenta_remunerada', 'deposito', 'letra_deuda_publica', 'fondo_tradicional', 'etf_ucits'):
            raise SnapshotError('invalid family')
    if seen != set(ids):
        raise SnapshotError('partial source')
    return copy.deepcopy(source)


class SyntheticSnapshotRepository:
    """Experimental read-only app interface plus explicit offline promote()."""
    def __init__(self, path, *, clock=None):
        self.path = Path(path)
        if self.path.name != 'synthetic-snapshot.json':
            raise SnapshotError('reserved synthetic snapshot filename required')
        self.clock = clock or (lambda: datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
        self._lock = threading.Lock()

    def promote(self, source):
        with self._lock:
            payload = _validate(source, self.clock())
            digest = hashlib.sha256(_json(payload).encode('utf-8')).hexdigest()
            encoded = (_json({'payload': payload, 'sha256': digest}) + '\n').encode('utf-8')
            fd, temp = tempfile.mkstemp(prefix='synthetic-snapshot.', suffix='.tmp', dir=self.path.parent)
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write(encoded)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp, self.path)
            finally:
                try:
                    os.unlink(temp)
                except FileNotFoundError:
                    pass

    def _load(self):
        try:
            envelope = json.loads(self.path.read_text(encoding='utf-8'), object_pairs_hook=_unique,
                                  parse_constant=lambda _: (_ for _ in ()).throw(SnapshotError('invalid number')))
            if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'}:
                raise SnapshotError('invalid envelope')
            digest = hashlib.sha256(_json(envelope['payload']).encode('utf-8')).hexdigest()
            if type(envelope['sha256']) is not str or digest != envelope['sha256']:
                raise SnapshotError('snapshot checksum mismatch')
            return _validate(envelope['payload'], self.clock())
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            raise SnapshotError('snapshot invalid, unavailable or stale') from exc

    def _products(self):
        with self._lock:
            data = self._load()
        return [{'id': r['id'], 'name': r['name']['value'], 'family': r['family']['value'],
                 'issuer': None, 'isin': None, 'identity_state': 'proposed', 'primary_url': None,
                 'as_of': r['name']['effective_at'][:10], 'publication_ready': False,
                 'conditions_state': 'pending', 'conflicts': [],
                 'unknown_fields': ['synthetic_test', 'permissions', 'conditions']} for r in data['records']]

    @property
    def count(self):
        return len(self._products())

    def list_products(self, q=None, family=None):
        products = self._products()
        return [p for p in products if (family is None or p['family'] == family) and
                (q is None or q.casefold() in p['name'].casefold() or q.casefold() in p['id'].casefold())]

    def get_product(self, product_id):
        return next((p for p in self._products() if p['id'] == product_id), None)
