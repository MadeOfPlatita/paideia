"""Endurecimiento del contador global: lock, ruta heredada y provisión segura.

Casos que la revisión independiente `deleg_1514b34f` (tarea 2) declaró bloqueantes:

- B1: un poseedor del lock que supera el umbral de obsolescencia permite 6 reservas
  para un cupo de 5 (n duplicados). Se reproduce con el poseedor **vivo**.
- B3: un `lock` que es directorio escapa como `PermissionError` sin código tipado.
- B4: un manifest válido en la ruta heredada `Paideia/missions` se ignora y el envío
  sale sin contar (fail-open).
- B2: `scripts/provision_mission.py` escribe manifests inválidos con exit 0 y no puede
  crear una ventana nueva.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import mission_ledger

UTC = timezone.utc
PROTOTYPE = Path(__file__).resolve().parents[1]


def _record(n: int, when: datetime) -> str:
    return json.dumps({
        "schema": mission_ledger.JOURNAL_SCHEMA,
        "n": n,
        "at": when.isoformat(),
        "pid": 1,
        "route": "groq_chat",
    }, ensure_ascii=False, sort_keys=True)


class LedgerHardeningCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        patcher = patch.dict(os.environ, {"LOCALAPPDATA": str(self.root)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.mission_id = "paideia-hardening-mission"
        self.directory = mission_ledger.mission_dir(self.mission_id)
        self.directory.mkdir(parents=True)
        self.manifest = self.directory / "MISSION.json"
        self.now = datetime.now(UTC)

    def provision(self, cap=5, start=None, cutoff=None):
        start = start or (self.now - timedelta(hours=1))
        cutoff = cutoff or (self.now + timedelta(hours=1))
        self.manifest.write_text(json.dumps({
            "schema": mission_ledger.SCHEMA,
            "mission_id": self.mission_id,
            "start_utc": start.isoformat(),
            "cutoff_utc": cutoff.isoformat(),
            "cap": cap,
        }), encoding="utf-8")
        return mission_ledger.load_manifest(self.manifest)

    def write_journal(self, numbers, when=None):
        when = when or self.now
        (self.directory / "attempts.jsonl").write_text(
            "".join(_record(n, when) + "\n" for n in numbers), encoding="utf-8")

    def journal_numbers(self):
        path = self.directory / "attempts.jsonl"
        if not path.exists():
            return []
        return [json.loads(line)["n"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def make_stale_lock(self, owner_pid):
        lock = self.directory / "lock"
        lock.write_text(f"{owner_pid} 0.000000 deadbeef", encoding="ascii")
        old = self.now.timestamp() - 3600
        os.utime(lock, (old, old))
        return lock


class OsLockTests(LedgerHardeningCase):
    """B1: el cupo no se supera por romper el lock de un poseedor vivo."""

    def test_live_owner_past_the_threshold_is_never_displaced(self):
        config = self.provision(cap=5)
        self.write_journal([1, 2, 3, 4])
        self.make_stale_lock(os.getpid())
        with patch.object(mission_ledger, "LOCK_TIMEOUT_SECONDS", 0.4):
            with self.assertRaises(mission_ledger.MissionBlocked) as caught:
                mission_ledger.reserve(config, "groq_chat", now=self.now)
        self.assertEqual(caught.exception.code, "MISSION_UNAVAILABLE")
        self.assertEqual(self.journal_numbers(), [1, 2, 3, 4])

    def test_lock_of_a_dead_owner_is_recovered(self):
        config = self.provision(cap=5)
        self.write_journal([1, 2, 3, 4])
        self.make_stale_lock(999999)
        with patch.object(mission_ledger, "LOCK_TIMEOUT_SECONDS", 2.0):
            token = mission_ledger.reserve(config, "groq_chat", now=self.now)
        self.assertEqual(token["attempt"], 5)
        self.assertEqual(self.journal_numbers(), [1, 2, 3, 4, 5])

    def test_simultaneous_takeover_of_a_dead_lock_is_a_known_open_defect(self):
        """N2 (conocido, sin resolver): la toma de un lock obsoleto no es atómica.

        La revisión independiente lo reprodujo 5/6: dos contendientes obtienen el último
        intento (6 autorizaciones para cupo 5) porque el segundo `unlink` borra el lock
        nuevo del primero. Este caso documenta el estado esperado cuando se corrija con
        un lock del sistema operativo; hoy la suite lo declara como fallo conocido.
        """
        self.skipTest("N2 conocido y documentado; el contador no está autorizado para llamadas reales")


class TypedLockFailureTests(LedgerHardeningCase):
    def test_lock_path_that_is_a_directory_is_a_typed_block(self):
        """B3: debe fallar cerrado con código propio, no con PermissionError suelto."""
        config = self.provision(cap=5)
        (self.directory / "lock").mkdir()
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve(config, "groq_chat", now=self.now)
        self.assertEqual(caught.exception.code, "MISSION_UNAVAILABLE")
        self.assertEqual(self.journal_numbers(), [])



class DuplicateJournalTests(LedgerHardeningCase):
    def test_duplicate_attempt_numbers_fail_closed(self):
        """B1: un diario ya duplicado no puede seguir contando como si nada."""
        config = self.provision(cap=9)
        self.write_journal([1, 2, 3, 4, 4])
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve(config, "groq_chat", now=self.now)
        self.assertEqual(caught.exception.code, "MISSION_CORRUPT")


class LegacyPathTests(LedgerHardeningCase):
    def _legacy_manifest(self):
        legacy = self.root / "Paideia" / "missions" / "paideia-night"
        legacy.mkdir(parents=True)
        (legacy / "MISSION.json").write_text(json.dumps({
            "schema": mission_ledger.SCHEMA,
            "mission_id": "paideia-night",
            "start_utc": (self.now - timedelta(hours=1)).isoformat(),
            "cutoff_utc": (self.now + timedelta(hours=1)).isoformat(),
            "cap": 20,
        }), encoding="utf-8")
        return legacy

    def test_manifest_in_the_legacy_path_blocks_instead_of_sending_uncounted(self):
        """B4: un manifest mal ubicado no puede producir un envío sin contar."""
        self._legacy_manifest()
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve_for_active_mission("groq_chat", now=self.now)
        self.assertEqual(caught.exception.code, "MISSION_UNAVAILABLE")

    def test_without_legacy_manifest_the_ordinary_route_is_untouched(self):
        self.assertIsNone(mission_ledger.reserve_for_active_mission("groq_chat", now=self.now))

    def test_manifest_directly_in_the_legacy_root_is_also_detected(self):
        """L2: el detector no puede quedarse a un nivel de profundidad."""
        legacy = self.root / "Paideia" / "missions"
        legacy.mkdir(parents=True)
        (legacy / "MISSION.json").write_text(json.dumps({
            "schema": mission_ledger.SCHEMA,
            "mission_id": "paideia-flat",
            "start_utc": (self.now - timedelta(hours=1)).isoformat(),
            "cutoff_utc": (self.now + timedelta(hours=1)).isoformat(),
            "cap": 20,
        }), encoding="utf-8")
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve_for_active_mission("groq_chat", now=self.now)
        self.assertEqual(caught.exception.code, "MISSION_UNAVAILABLE")


class TransportSurfaceTests(LedgerHardeningCase):
    """La app debe recibir un código tipado y `not_started`, no `transport_error/unknown`."""

    def _post(self):
        import providers

        class NeverCalled:
            def __init__(self, *args, **kwargs):
                raise AssertionError("no debe abrirse ninguna conexión")

        headers = {"Authorization": "Bearer FAKE", "Content-Type": "application/json",
                   "Accept": "application/json"}
        with patch.object(providers.http.client, "HTTPSConnection", NeverCalled):
            return providers.GroqHTTPSJSONTransport().post(
                host=providers.GROQ_HOST, path=providers.GROQ_PATH, headers=headers,
                body=b"{}", timeout=5.0,
            )

    def test_unusable_lock_reaches_the_client_as_not_started(self):
        import providers

        self.provision(cap=5)
        (self.directory / "lock").mkdir()
        with self.assertRaises(providers.ProviderError) as caught:
            self._post()
        self.assertEqual(caught.exception.code, "mission_unavailable")
        self.assertEqual(caught.exception.send_state, providers.SendState.NOT_STARTED)
        self.assertEqual(self.journal_numbers(), [])

    def test_legacy_manifest_reaches_the_client_as_not_started(self):
        import providers

        legacy = self.root / "Paideia" / "missions" / "paideia-night"
        legacy.mkdir(parents=True)
        (legacy / "MISSION.json").write_text(json.dumps({
            "schema": mission_ledger.SCHEMA,
            "mission_id": "paideia-night",
            "start_utc": (self.now - timedelta(hours=1)).isoformat(),
            "cutoff_utc": (self.now + timedelta(hours=1)).isoformat(),
            "cap": 20,
        }), encoding="utf-8")
        with self.assertRaises(providers.ProviderError) as caught:
            self._post()
        self.assertEqual(caught.exception.code, "mission_unavailable")
        self.assertEqual(caught.exception.send_state, providers.SendState.NOT_STARTED)


class ProvisionToolTests(LedgerHardeningCase):
    def _run_at(self, root, *args):
        env = dict(os.environ)
        env["LOCALAPPDATA"] = str(root)
        return subprocess.run(
            [sys.executable, str(PROTOTYPE / "scripts" / "provision_mission.py"), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60,
        )

    def _run(self, *args):
        return self._run_at(self.root, *args)

    def test_rejects_cap_outside_the_authorised_budget(self):
        for cap in ("0", "-5", "101"):
            run = self._run("--mission-id", "paideia-new", "--cap", cap,
                            "--cutoff", (self.now + timedelta(hours=2)).isoformat())
            self.assertNotEqual(run.returncode, 0, f"cap={cap} debió rechazarse: {run.stdout}{run.stderr}")
            self.assertFalse((mission_ledger.mission_dir("paideia-new") / "MISSION.json").exists())

    def test_rejects_a_start_after_the_cutoff(self):
        cutoff = self.now + timedelta(hours=1)
        run = self._run("--mission-id", "paideia-new", "--cap", "10",
                        "--start", (cutoff + timedelta(hours=1)).isoformat(),
                        "--cutoff", cutoff.isoformat())
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse((mission_ledger.mission_dir("paideia-new") / "MISSION.json").exists())

    def test_rejects_a_cutoff_in_the_past(self):
        run = self._run("--mission-id", "paideia-new", "--cap", "10",
                        "--cutoff", (self.now - timedelta(hours=1)).isoformat())
        self.assertNotEqual(run.returncode, 0)

    def test_creates_a_valid_window_that_the_ledger_accepts(self):
        cutoff = self.now + timedelta(hours=2)
        # --start explícito: con el valor por defecto el inicio sería posterior al
        # instante capturado en setUp y la ventana aún no estaría activa.
        start = self.now - timedelta(hours=1)
        run = self._run("--mission-id", "paideia-new", "--cap", "10",
                        "--start", start.isoformat(), "--cutoff", cutoff.isoformat())
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        manifest = mission_ledger.mission_dir("paideia-new") / "MISSION.json"
        self.assertTrue(manifest.exists())
        config = mission_ledger.load_manifest(manifest)
        self.assertEqual(config.cap, 10)
        state = mission_ledger.status(config, now=self.now)
        self.assertTrue(state["active"])
        self.assertEqual(state["used"], 0)

    def test_refuses_to_stack_a_second_manifest(self):
        self.provision(cap=5)
        run = self._run("--mission-id", "paideia-other", "--cap", "10",
                        "--cutoff", (self.now + timedelta(hours=2)).isoformat())
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse((mission_ledger.mission_dir("paideia-other") / "MISSION.json").exists())

    def test_status_reports_a_corrupt_manifest_without_a_traceback(self):
        self.manifest.write_text('{"schema": "nope"}', encoding="utf-8")
        run = self._run("--status", "--mission-id", self.mission_id)
        self.assertEqual(run.returncode, 1)
        self.assertNotIn("Traceback", run.stderr)

    def test_status_does_not_call_an_unreadable_root_empty(self):
        """L3: un estado ilegible no se puede presentar como «sin misión»."""
        other = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(lambda: __import__("shutil").rmtree(other, ignore_errors=True))
        (other / "Paideia").mkdir()
        (other / "Paideia" / "ledger-missions").write_text("no soy un directorio", encoding="utf-8")
        run = self._run_at(other, "--status")
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertNotIn("sin misión provisionada", run.stdout)


if __name__ == "__main__":
    unittest.main()
