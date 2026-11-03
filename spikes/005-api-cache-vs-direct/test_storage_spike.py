"""Acceptance tests for the stdlib-only storage comparison spike."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from storage_spike import (
    CachePolicy,
    CatalogQueryService,
    DirectApiRepository,
    FakeProvider,
    ProviderError,
    SnapshotIntegrityError,
    SnapshotRepository,
    load_snapshot,
)

SPIKE_DIR = Path(__file__).resolve().parent


def synthetic_records(revision: int = 1) -> list[dict]:
    """Non-financial fixture rows; never catalogue offers or user data."""
    return [
        {
            "id": f"SYN-{i:03d}",
            "label": f"Synthetic row {i} revision {revision}",
            "kind": "synthetic_test",
            "value": revision * i,
            "unit": "synthetic_count",
            "effective_date": "2026-10-01",
            "source_id": "synthetic_test:fake-provider",
        }
        for i in range(1, 4)
    ]


class FakeClock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class StorageSpikeTests(unittest.TestCase):
    def test_direct_reader_requests_provider_for_every_read(self) -> None:
        provider = FakeProvider(synthetic_records(), delay_seconds=0)
        reader = DirectApiRepository(provider)

        results = [reader.read() for _ in range(5)]

        self.assertEqual(provider.request_count, 5)
        self.assertEqual(reader.cache_hits, 0)
        self.assertEqual(results[-1].source_kind, "synthetic_test")
        self.assertEqual(len(results[-1].records), 3)
        self.assertTrue(all(result.status == "direct" for result in results))

    def test_persistent_json_cache_coalesces_100_concurrent_reads(self) -> None:
        provider = FakeProvider(synthetic_records(), delay_seconds=0.002)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            snapshot_path = Path(tmp) / "catalog.json"
            reader = SnapshotRepository(snapshot_path, provider, CachePolicy())
            with ThreadPoolExecutor(max_workers=32) as pool:
                results = list(pool.map(lambda _: reader.read(), range(100)))

            self.assertEqual(provider.request_count, 1)
            self.assertEqual(reader.cache_hits, 99)
            self.assertEqual(len(results), 100)
            self.assertTrue(all(result.records == synthetic_records() for result in results))
            self.assertTrue(snapshot_path.is_file())
            snapshot = load_snapshot(snapshot_path)
            self.assertEqual(snapshot["source_kind"], "synthetic_test")
            self.assertEqual(len(snapshot["records"]), 3)

    def test_restart_process_reads_snapshot_without_provider_call(self) -> None:
        provider = FakeProvider(synthetic_records(), delay_seconds=0)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            snapshot_path = Path(tmp) / "catalog.json"
            SnapshotRepository(snapshot_path, provider, CachePolicy()).read()
            command = [sys.executable, str(SPIKE_DIR / "storage_spike.py"), "--restart-check", str(snapshot_path)]
            completed = subprocess.run(command, cwd=SPIKE_DIR, capture_output=True, text=True, check=False)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            restart = json.loads(completed.stdout)
            self.assertEqual(restart["source_kind"], "synthetic_test")
            self.assertEqual(restart["provider_requests"], 0)
            self.assertEqual(restart["records"], 3)
            self.assertTrue(restart["integrity_verified"])

    def test_no_ttl_is_default_and_fresh_snapshot_survives_elapsed_time(self) -> None:
        self.assertIsNone(CachePolicy().ttl_seconds)
        self.assertFalse(CachePolicy().serve_stale_on_error)
        clock = FakeClock()
        provider = FakeProvider(synthetic_records(), delay_seconds=0)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            reader = SnapshotRepository(Path(tmp) / "catalog.json", provider, CachePolicy(), clock=clock)
            first = reader.read()
            clock.advance(365 * 24 * 60 * 60)
            second = reader.read()

            self.assertEqual(provider.request_count, 1)
            self.assertEqual(second.status, "snapshot")
            self.assertEqual(second.records, first.records)

    def test_expired_snapshot_falls_back_only_when_policy_explicitly_allows_it(self) -> None:
        clock = FakeClock()
        provider = FakeProvider(synthetic_records(), delay_seconds=0)
        policy = CachePolicy(ttl_seconds=10, serve_stale_on_error=True)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            reader = SnapshotRepository(Path(tmp) / "catalog.json", provider, policy, clock=clock)
            reader.read()
            clock.advance(11)
            provider.fail = True

            stale = reader.read()

            self.assertEqual(stale.status, "stale_fallback")
            self.assertEqual(stale.records, synthetic_records())
            self.assertTrue(stale.is_stale)
            self.assertEqual(reader.stale_fallbacks, 1)

    def test_expired_snapshot_fails_closed_when_stale_fallback_is_not_enabled(self) -> None:
        clock = FakeClock()
        provider = FakeProvider(synthetic_records(), delay_seconds=0)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            reader = SnapshotRepository(Path(tmp) / "catalog.json", provider, CachePolicy(ttl_seconds=5), clock=clock)
            reader.read()
            before = (Path(tmp) / "catalog.json").read_bytes()
            clock.advance(6)
            provider.fail = True

            with self.assertRaises(ProviderError):
                reader.read()

            self.assertEqual((Path(tmp) / "catalog.json").read_bytes(), before)
            self.assertEqual(reader.stale_fallbacks, 0)

    def test_failed_refresh_keeps_last_good_snapshot(self) -> None:
        provider = FakeProvider(synthetic_records(), delay_seconds=0)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            path = Path(tmp) / "catalog.json"
            reader = SnapshotRepository(path, provider, CachePolicy())
            reader.read()
            before = path.read_bytes()
            provider.fail = True

            with self.assertRaises(ProviderError):
                reader.refresh()

            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(load_snapshot(path)["records"], synthetic_records())

    def test_snapshot_update_is_atomic_and_preserves_old_file_if_replace_fails(self) -> None:
        provider = FakeProvider(synthetic_records(1), delay_seconds=0)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            path = Path(tmp) / "catalog.json"
            reader = SnapshotRepository(path, provider, CachePolicy())
            reader.read()
            old_bytes = path.read_bytes()
            provider.set_records(synthetic_records(2))
            reader.refresh()
            new_bytes = path.read_bytes()
            self.assertNotEqual(new_bytes, old_bytes)
            self.assertEqual(load_snapshot(path)["records"], synthetic_records(2))

            provider.set_records(synthetic_records(3))
            with patch("storage_spike.os.replace", side_effect=OSError("injected synthetic replace failure")):
                with self.assertRaises(OSError):
                    reader.refresh()

            self.assertEqual(path.read_bytes(), new_bytes)
            self.assertEqual(load_snapshot(path)["records"], synthetic_records(2))
            self.assertEqual(list(Path(tmp).glob("*.tmp")), [])

    def test_corrupt_snapshot_is_not_served_and_is_rebuilt_from_provider(self) -> None:
        provider = FakeProvider(synthetic_records(1), delay_seconds=0)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            path = Path(tmp) / "catalog.json"
            reader = SnapshotRepository(path, provider, CachePolicy())
            reader.read()
            envelope = json.loads(path.read_text(encoding="utf-8"))
            envelope["records"][0]["value"] = 999999
            path.write_text(json.dumps(envelope), encoding="utf-8")
            provider.set_records(synthetic_records(2))

            with self.assertRaises(SnapshotIntegrityError):
                load_snapshot(path)
            command = [sys.executable, str(SPIKE_DIR / "storage_spike.py"), "--repair-check", str(path)]
            completed = subprocess.run(command, cwd=SPIKE_DIR, capture_output=True, text=True, check=False)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            repaired = json.loads(completed.stdout)
            self.assertEqual(repaired["status"], "refreshed")
            self.assertEqual(repaired["provider_requests"], 1)
            self.assertEqual(repaired["records"], 3)
            self.assertTrue(repaired["integrity_verified"])
            self.assertEqual(load_snapshot(path)["records"][0]["value"], 2)

    def test_concurrent_readers_never_observe_partial_snapshot_during_replacement(self) -> None:
        provider = FakeProvider(synthetic_records(1), delay_seconds=0)
        with tempfile.TemporaryDirectory(dir=SPIKE_DIR) as tmp:
            path = Path(tmp) / "catalog.json"
            writer = SnapshotRepository(path, provider, CachePolicy())
            writer.read()
            offline_provider = FakeProvider(synthetic_records(), fail=True, delay_seconds=0)
            reader = SnapshotRepository(path, offline_provider, CachePolicy())
            start = threading.Barrier(9)
            errors: list[str] = []
            observed: list[list[dict]] = []

            def read_many() -> None:
                start.wait()
                for _ in range(40):
                    try:
                        observed.append(reader.read().records)
                    except Exception as exc:  # test reports unexpected torn/corrupt reads
                        errors.append(type(exc).__name__ + ": " + str(exc))

            def update_many() -> None:
                start.wait()
                for revision in range(2, 22):
                    provider.set_records(synthetic_records(revision))
                    writer.refresh()

            with ThreadPoolExecutor(max_workers=9) as pool:
                futures = [pool.submit(read_many) for _ in range(8)]
                futures.append(pool.submit(update_many))
                for future in futures:
                    future.result()

            self.assertEqual(errors, [])
            self.assertEqual(len(observed), 320)
            self.assertTrue(all(len(records) == 3 for records in observed))
            self.assertEqual(offline_provider.request_count, 0)
            self.assertEqual(len(load_snapshot(path)["records"]), 3)

    def test_catalog_query_service_uses_reader_contract_and_returns_normalized_rows(self) -> None:
        provider = FakeProvider(synthetic_records(), delay_seconds=0)
        service = CatalogQueryService(DirectApiRepository(provider))

        rows = service.list_entries()

        self.assertEqual(rows, synthetic_records())
        self.assertEqual(provider.request_count, 1)


if __name__ == "__main__":
    unittest.main()
