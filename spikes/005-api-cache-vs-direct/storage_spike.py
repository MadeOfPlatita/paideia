"""Stdlib-only spike: direct reads versus a persistent JSON snapshot cache.

All provider data is synthetic_test. No network client or database exists here.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Protocol


SCHEMA_VERSION = "snapshot.v1"
SOURCE_KIND = "synthetic_test"
SPIKE_DIR = Path(__file__).resolve().parent
class _SnapshotState:
    """In-process state shared by repository instances for one normalized path."""

    def __init__(self):
        self.lock = threading.Lock()
        self.loaded = False
        self.snapshot: dict | None = None


_PATH_STATES: dict[str, _SnapshotState] = {}
_PATH_STATES_GUARD = threading.Lock()


def _state_for_snapshot(path: str | Path) -> _SnapshotState:
    """Coordinate instances in this Python process that address the same file."""
    key = os.path.normcase(str(Path(path).resolve()))
    with _PATH_STATES_GUARD:
        state = _PATH_STATES.get(key)
        if state is None:
            state = _SnapshotState()
            _PATH_STATES[key] = state
        return state


class ProviderError(RuntimeError):
    """A synthetic provider failure; deliberately no retry is performed."""


class DataContractError(ValueError):
    """Provider output is not the normalized schema expected by this spike."""


class SnapshotIntegrityError(ValueError):
    """Stored JSON is malformed, has an unsupported version, or fails its hash."""


@dataclass(frozen=True)
class CachePolicy:
    """Production default is no automatic TTL and no stale-on-error fallback."""

    ttl_seconds: float | None = None
    serve_stale_on_error: bool = False

    def __post_init__(self) -> None:
        if self.ttl_seconds is not None and self.ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative or None")


@dataclass(frozen=True)
class ReadResult:
    records: list[dict]
    status: str
    source_kind: str
    retrieved_at_epoch: float
    is_stale: bool
    digest: str


class CatalogReader(Protocol):
    """Stable read contract for direct, JSON, or a future DB adapter."""

    def read(self) -> ReadResult: ...


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def validate_records(records: object) -> list[dict]:
    """Validate the spike's normalized synthetic-only fixture format."""
    if not isinstance(records, list):
        raise DataContractError("records must be a list")
    required = {"id", "label", "kind", "value", "unit", "effective_date", "source_id"}
    seen: set[str] = set()
    normalized: list[dict] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not required.issubset(record):
            raise DataContractError(f"record {index} is missing normalized fields")
        row = copy.deepcopy(record)
        if not isinstance(row["id"], str) or not row["id"] or row["id"] in seen:
            raise DataContractError(f"record {index} has a missing or duplicate id")
        seen.add(row["id"])
        if row["kind"] != SOURCE_KIND or not str(row["source_id"]).startswith("synthetic_test:"):
            raise DataContractError(f"record {index} is not marked synthetic_test")
        if not isinstance(row["label"], str) or not row["label"].strip():
            raise DataContractError(f"record {index} has an empty label")
        if isinstance(row["value"], bool) or not isinstance(row["value"], (int, float)):
            raise DataContractError(f"record {index} value must be numeric")
        if isinstance(row["value"], float) and not math.isfinite(row["value"]):
            raise DataContractError(f"record {index} value must be finite")
        if not isinstance(row["unit"], str) or not row["unit"]:
            raise DataContractError(f"record {index} has no unit")
        try:
            date.fromisoformat(row["effective_date"])
        except (TypeError, ValueError) as exc:
            raise DataContractError(f"record {index} effective_date must be YYYY-MM-DD") from exc
        normalized.append(row)
    return normalized


def _snapshot_payload(records: list[dict], retrieved_at_epoch: float) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "source_kind": SOURCE_KIND,
        "retrieved_at_epoch": float(retrieved_at_epoch),
        "records": validate_records(records),
    }


def _envelope(payload: dict) -> dict:
    return {**payload, "sha256": _sha256(payload)}


def load_snapshot(path: str | Path) -> dict:
    """Load and validate a snapshot; never treat malformed data as a cache hit."""
    snapshot_path = Path(path)
    try:
        envelope = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SnapshotIntegrityError("snapshot cannot be decoded") from exc
    if not isinstance(envelope, dict):
        raise SnapshotIntegrityError("snapshot root must be an object")
    expected_keys = {"schema_version", "source_kind", "retrieved_at_epoch", "records", "sha256"}
    if set(envelope) != expected_keys:
        raise SnapshotIntegrityError("snapshot fields do not match snapshot.v1")
    if envelope["schema_version"] != SCHEMA_VERSION or envelope["source_kind"] != SOURCE_KIND:
        raise SnapshotIntegrityError("unsupported schema or source kind")
    try:
        fetched_at = float(envelope["retrieved_at_epoch"])
        if not math.isfinite(fetched_at):
            raise ValueError("retrieval time must be finite")
        records = validate_records(envelope["records"])
    except (TypeError, ValueError, DataContractError) as exc:
        raise SnapshotIntegrityError("snapshot payload is invalid") from exc
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_kind": SOURCE_KIND,
        "retrieved_at_epoch": fetched_at,
        "records": records,
    }
    if not isinstance(envelope["sha256"], str) or envelope["sha256"] != _sha256(payload):
        raise SnapshotIntegrityError("snapshot checksum does not match its payload")
    return {**payload, "sha256": envelope["sha256"]}


def atomic_write_snapshot(path: str | Path, envelope: dict) -> None:
    """Write a same-directory temp file and replace the visible snapshot."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(envelope, stream, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, target)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


class FakeProvider:
    """In-process fake only; delay is artificial and no HTTP is issued."""

    def __init__(self, records: list[dict], *, fail: bool = False, delay_seconds: float = 0.0):
        self._records = validate_records(records)
        self.fail = fail
        self.delay_seconds = delay_seconds
        self.request_count = 0
        self._lock = threading.Lock()

    def set_records(self, records: list[dict]) -> None:
        with self._lock:
            self._records = validate_records(records)

    def fetch(self) -> list[dict]:
        with self._lock:
            self.request_count += 1
            should_fail = self.fail
            delay = self.delay_seconds
            records = copy.deepcopy(self._records)
        if delay:
            time.sleep(delay)
        if should_fail:
            raise ProviderError("synthetic_test provider failure")
        return records


class DirectApiRepository:
    """Direct-read adapter: each application read calls the source adapter."""

    def __init__(self, provider: FakeProvider, *, clock: Callable[[], float] = time.time):
        self.provider = provider
        self.clock = clock
        self.cache_hits = 0

    def read(self) -> ReadResult:
        records = validate_records(self.provider.fetch())
        fetched_at = float(self.clock())
        payload = _snapshot_payload(records, fetched_at)
        return ReadResult(records, "direct", SOURCE_KIND, fetched_at, False, _sha256(payload))


class SnapshotRepository:
    """Persistent normalized JSON snapshot with process-local single-flight reads."""

    def __init__(
        self,
        snapshot_path: str | Path,
        provider: FakeProvider,
        policy: CachePolicy = CachePolicy(),
        *,
        clock: Callable[[], float] = time.time,
    ):
        self.snapshot_path = Path(snapshot_path)
        self.provider = provider
        self.policy = policy
        self.clock = clock
        self.cache_hits = 0
        self.stale_fallbacks = 0
        self._state = _state_for_snapshot(self.snapshot_path)
        self._lock = self._state.lock

    def _freshness(self, snapshot: dict) -> tuple[bool, float]:
        age = max(0.0, float(self.clock()) - snapshot["retrieved_at_epoch"])
        expired = self.policy.ttl_seconds is not None and age >= self.policy.ttl_seconds
        return expired, age

    @staticmethod
    def _result(snapshot: dict, status: str, *, is_stale: bool = False) -> ReadResult:
        return ReadResult(
            copy.deepcopy(snapshot["records"]),
            status,
            snapshot["source_kind"],
            snapshot["retrieved_at_epoch"],
            is_stale,
            snapshot["sha256"],
        )

    def _fetch_and_store(self, status: str = "refreshed") -> ReadResult:
        records = validate_records(self.provider.fetch())
        payload = _snapshot_payload(records, float(self.clock()))
        snapshot = _envelope(payload)
        atomic_write_snapshot(self.snapshot_path, snapshot)
        self._state.snapshot = snapshot
        self._state.loaded = True
        return self._result(snapshot, status)

    def read(self) -> ReadResult:
        result_snapshot: dict | None = None
        result_status = "snapshot"
        result_stale = False
        fetched_result: ReadResult | None = None
        with self._lock:
            if not self._state.loaded:
                self._state.loaded = True
                if self.snapshot_path.exists():
                    try:
                        self._state.snapshot = load_snapshot(self.snapshot_path)
                    except SnapshotIntegrityError:
                        self._state.snapshot = None
            snapshot = self._state.snapshot
            expired = False
            if snapshot is not None:
                expired, _ = self._freshness(snapshot)
                if not expired:
                    self.cache_hits += 1
                    result_snapshot = snapshot
            if result_snapshot is None:
                try:
                    fetched_result = self._fetch_and_store("refreshed")
                except (ProviderError, DataContractError, OSError):
                    if snapshot is not None and expired and self.policy.serve_stale_on_error:
                        self.cache_hits += 1
                        self.stale_fallbacks += 1
                        result_snapshot = snapshot
                        result_status = "stale_fallback"
                        result_stale = True
                    else:
                        raise
        if fetched_result is not None:
            return fetched_result
        assert result_snapshot is not None
        return self._result(result_snapshot, result_status, is_stale=result_stale)

    def refresh(self) -> ReadResult:
        """Explicit refresh operation; failure never replaces the last good file."""
        with self._lock:
            return self._fetch_and_store("refreshed")


class CatalogQueryService:
    """Business-facing query service: it knows the reader contract, not storage."""

    def __init__(self, reader: CatalogReader):
        self.reader = reader

    def list_entries(self) -> list[dict]:
        return self.reader.read().records


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    position = max(0, math.ceil(pct * len(ordered)) - 1)
    return round(ordered[position], 3)


def _measure_burst(reader: CatalogReader, count: int = 100, workers: int = 100) -> tuple[list[ReadResult], dict]:
    latencies: list[float] = []
    latency_lock = threading.Lock()

    def timed_read(_: int) -> ReadResult:
        started = time.perf_counter()
        result = reader.read()
        elapsed_ms = (time.perf_counter() - started) * 1000
        with latency_lock:
            latencies.append(elapsed_ms)
        return result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(timed_read, range(count)))
    metrics = {
        "p50": _percentile(latencies, 0.50),
        "p95": _percentile(latencies, 0.95),
        "p99": _percentile(latencies, 0.99),
        "max": round(max(latencies), 3),
    }
    return results, metrics


def _variant_metrics(name: str, results: list[ReadResult], provider_requests: int, cache_hits: int, stale_fallbacks: int, latency: dict, workers: int) -> dict:
    rows_returned = sum(len(result.records) for result in results)
    signatures = {_sha256(result.records) for result in results}
    return {
        "variant": name,
        "read_count": len(results),
        "concurrent_workers": workers,
        "provider_requests": provider_requests,
        "cache_hits": cache_hits,
        "stale_fallbacks": stale_fallbacks,
        "successful_results": sum(1 for result in results if result.records),
        "rows_returned": rows_returned,
        "distinct_result_sets": len(signatures),
        "source_kind": SOURCE_KIND,
        "latency_ms_local_orientation_only": latency,
    }


def run_experiment() -> dict:
    records = [
        {
            "id": f"SYN-{i:03d}",
            "label": f"Synthetic row {i} revision 1",
            "kind": SOURCE_KIND,
            "value": i,
            "unit": "synthetic_count",
            "effective_date": "2026-10-01",
            "source_id": "synthetic_test:fake-provider",
        }
        for i in range(1, 4)
    ]
    workers = 100
    with tempfile.TemporaryDirectory(prefix="run-", dir=SPIKE_DIR) as tmp:
        direct_provider = FakeProvider(records, delay_seconds=0.003)
        direct_reader = DirectApiRepository(direct_provider)
        direct_results, direct_latency = _measure_burst(direct_reader, 100, workers)
        direct_metrics = _variant_metrics("direct_api_read", direct_results, direct_provider.request_count, 0, 0, direct_latency, workers)

        cache_provider = FakeProvider(records, delay_seconds=0.003)
        snapshot_path = Path(tmp) / "snapshot.json"
        cache_reader = SnapshotRepository(snapshot_path, cache_provider, CachePolicy())
        cached_results, cached_latency = _measure_burst(cache_reader, 100, workers)
        cache_metrics = _variant_metrics(
            "persistent_json_snapshot",
            cached_results,
            cache_provider.request_count,
            cache_reader.cache_hits,
            cache_reader.stale_fallbacks,
            cached_latency,
            workers,
        )

        restart_command = [sys.executable, str(Path(__file__).resolve()), "--restart-check", str(snapshot_path)]
        restart_process = subprocess.run(restart_command, cwd=SPIKE_DIR, capture_output=True, text=True, check=False)
        restart_result = json.loads(restart_process.stdout) if restart_process.returncode == 0 else {}
        snapshot_before_update = load_snapshot(snapshot_path)

        cache_provider.set_records([{**row, "label": row["label"].replace("revision 1", "revision 2"), "value": row["value"] + 100} for row in records])
        updated = cache_reader.refresh()
        snapshot_after_update = load_snapshot(snapshot_path)
        atomic_success = updated.records == snapshot_after_update["records"] and snapshot_after_update["records"] != snapshot_before_update["records"]
        before_failed_replace = snapshot_path.read_bytes()
        cache_provider.set_records([{**row, "label": row["label"].replace("revision 2", "revision 3"), "value": row["value"] + 200} for row in records])
        replace_failure_preserved = False
        try:
            from unittest.mock import patch

            with patch("storage_spike.os.replace", side_effect=OSError("injected synthetic replace failure")):
                cache_reader.refresh()
        except OSError:
            replace_failure_preserved = snapshot_path.read_bytes() == before_failed_replace
        temp_files_clean = not list(Path(tmp).glob("*.tmp"))
        integrity_after_update = load_snapshot(snapshot_path)["sha256"] == snapshot_after_update["sha256"]

        failure_provider = FakeProvider(records, delay_seconds=0)
        stale_time = [1000.0]
        stale_clock = lambda: stale_time[0]
        stale_repo = SnapshotRepository(
            Path(tmp) / "stale-policy.json",
            failure_provider,
            CachePolicy(ttl_seconds=10, serve_stale_on_error=True),
            clock=stale_clock,
        )
        stale_repo.read()
        stale_time[0] += 11
        failure_provider.fail = True
        stale_result = stale_repo.read()

        direct_failure_provider = FakeProvider(records, fail=True, delay_seconds=0)
        direct_failure_observed = False
        try:
            DirectApiRepository(direct_failure_provider).read()
        except ProviderError:
            direct_failure_observed = True

        checks = {
            "restart_process_read_snapshot_without_provider": restart_result.get("provider_requests") == 0 and restart_result.get("integrity_verified") is True,
            "snapshot_integrity_after_update": integrity_after_update,
            "atomic_update_replaced_complete_snapshot": atomic_success,
            "failed_replace_kept_last_good_snapshot": replace_failure_preserved and temp_files_clean,
            "expired_stale_fallback_only_by_explicit_policy": stale_result.status == "stale_fallback" and stale_result.is_stale,
            "provider_failure_observed_without_retry": direct_failure_observed and direct_failure_provider.request_count == 1,
        }
        return {
            "schema_version": "storage-spike-results.v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "classification": SOURCE_KIND,
            "experiment": {
                "kind": "catalog_read_burst_not_chat",
                "read_count_per_variant": 100,
                "concurrent_workers": workers,
                "synthetic_provider_delay_ms": 3,
                "network_requests": 0,
                "database_created": False,
                "api_called": False,
                "latency_warning": "Local Python + artificial fake-provider delay only; not network, free-tier, hosting, production, or real-100-user capacity evidence.",
            },
            "command": "python3 spikes/005-api-cache-vs-direct/storage_spike.py --run",
            "exit_code": 0 if all(checks.values()) else 1,
            "variants": [direct_metrics, cache_metrics],
            "checks": checks,
            "restart_process": restart_result,
            "cache_post_burst": {
                "provider_requests_including_explicit_refresh_and_injected_failure": cache_provider.request_count,
                "snapshot_integrity_valid": integrity_after_update,
                "atomic_update_succeeded": atomic_success,
                "failed_replace_preserved_previous_bytes": replace_failure_preserved,
                "temporary_files_cleaned": temp_files_clean,
            },
            "policy_test": {
                "default_ttl_seconds": CachePolicy().ttl_seconds,
                "default_stale_on_error": CachePolicy().serve_stale_on_error,
                "explicit_ttl_seconds": 10,
                "explicit_stale_on_error": True,
                "provider_requests": failure_provider.request_count,
                "fallback_result_status": stale_result.status,
                "stale_flag": stale_result.is_stale,
            },
            "failure_test": {
                "direct_provider_requests": direct_failure_provider.request_count,
                "direct_failure_observed": direct_failure_observed,
            },
            "limitations": [
                "FakeProvider is synthetic_test and performs no network I/O.",
                "One Python process and thread pool; no multi-process or hosted-service claim.",
                "The process-local lock coalesces cold misses only inside this process.",
                "No PostgreSQL, SQLite, other database, API credentials, or real financial data used.",
                "No chat, LLM, free-tier, 100-user production, availability, or quota result is measured.",
                "File fsync plus same-directory os.replace is not a backup or a cross-platform power-loss durability guarantee.",
            ],
        }


def write_results(results: dict) -> tuple[Path, Path]:
    json_path = SPIKE_DIR / "results.json"
    csv_path = SPIKE_DIR / "results.csv"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fieldnames = [
        "variant", "read_count", "concurrent_workers", "provider_requests", "cache_hits",
        "stale_fallbacks", "successful_results", "rows_returned", "distinct_result_sets",
        "p50_ms_local", "p95_ms_local", "p99_ms_local", "max_ms_local", "source_kind",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for variant in results["variants"]:
            latency = variant["latency_ms_local_orientation_only"]
            writer.writerow({
                "variant": variant["variant"],
                "read_count": variant["read_count"],
                "concurrent_workers": variant["concurrent_workers"],
                "provider_requests": variant["provider_requests"],
                "cache_hits": variant["cache_hits"],
                "stale_fallbacks": variant["stale_fallbacks"],
                "successful_results": variant["successful_results"],
                "rows_returned": variant["rows_returned"],
                "distinct_result_sets": variant["distinct_result_sets"],
                "p50_ms_local": latency["p50"],
                "p95_ms_local": latency["p95"],
                "p99_ms_local": latency["p99"],
                "max_ms_local": latency["max"],
                "source_kind": variant["source_kind"],
            })
    return json_path, csv_path


def _restart_check(snapshot_path: Path) -> int:
    provider = FakeProvider(
        [
            {
                "id": f"SYN-{i:03d}",
                "label": f"Synthetic row {i} revision 1",
                "kind": SOURCE_KIND,
                "value": i,
                "unit": "synthetic_count",
                "effective_date": "2026-10-01",
                "source_id": "synthetic_test:fake-provider",
            }
            for i in range(1, 4)
        ],
        fail=True,
        delay_seconds=0,
    )
    reader = SnapshotRepository(snapshot_path, provider, CachePolicy())
    result = reader.read()
    verified = load_snapshot(snapshot_path)
    print(json.dumps({
        "source_kind": result.source_kind,
        "status": result.status,
        "provider_requests": provider.request_count,
        "records": len(result.records),
        "integrity_verified": verified["sha256"] == result.digest,
    }, sort_keys=True))
    return 0


def _repair_check(snapshot_path: Path) -> int:
    provider = FakeProvider(
        [
            {
                "id": f"SYN-{i:03d}",
                "label": f"Synthetic row {i} revision 2",
                "kind": SOURCE_KIND,
                "value": 2 * i,
                "unit": "synthetic_count",
                "effective_date": "2026-10-01",
                "source_id": "synthetic_test:fake-provider",
            }
            for i in range(1, 4)
        ],
        delay_seconds=0,
    )
    reader = SnapshotRepository(snapshot_path, provider, CachePolicy())
    result = reader.read()
    verified = load_snapshot(snapshot_path)
    print(json.dumps({
        "source_kind": result.source_kind,
        "status": result.status,
        "provider_requests": provider.request_count,
        "records": len(result.records),
        "integrity_verified": verified["sha256"] == result.digest,
    }, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == "--restart-check":
        return _restart_check(Path(args[1]))
    if len(args) == 2 and args[0] == "--repair-check":
        return _repair_check(Path(args[1]))
    if args not in ([], ["--run"]):
        print("usage: python3 storage_spike.py --run | --restart-check SNAPSHOT | --repair-check SNAPSHOT", file=sys.stderr)
        return 2
    results = run_experiment()
    results["exit_code"] = 0 if all(results["checks"].values()) else 1
    json_path, csv_path = write_results(results)
    print(json.dumps({
        "exit_code": results["exit_code"],
        "results_json": str(json_path),
        "results_csv": str(csv_path),
        "variants": results["variants"],
        "checks": results["checks"],
    }, ensure_ascii=False, sort_keys=True))
    return results["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
