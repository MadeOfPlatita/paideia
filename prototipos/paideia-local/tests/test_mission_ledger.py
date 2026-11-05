"""Contador global de intentos reales: cupo, corte, diario y frontera del transporte."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import mission_ledger
import providers

UTC = timezone.utc
START = datetime(2026, 11, 4, 10, 56, tzinfo=UTC)
CUTOFF = datetime(2026, 11, 4, 15, 21, 47, tzinfo=UTC)


class LedgerCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.patch = patch.dict(os.environ, {"LOCALAPPDATA": str(self.root)})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.mission_id = "paideia-test-mission"
        self.directory = mission_ledger.mission_dir(self.mission_id)
        self.directory.mkdir(parents=True)
        self.manifest = self.directory / "MISSION.json"

    def provision(self, cap=3, start=START, cutoff=CUTOFF, mission_id=None, directory=None):
        target = (directory or self.directory) / "MISSION.json"
        target.write_text(json.dumps({
            "schema": mission_ledger.SCHEMA,
            "mission_id": mission_id or self.mission_id,
            "start_utc": start.isoformat(),
            "cutoff_utc": cutoff.isoformat(),
            "cap": cap,
        }), encoding="utf-8")
        return mission_ledger.load_manifest(target)

    def journal_lines(self):
        path = self.directory / "attempts.jsonl"
        if not path.exists():
            return []
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class ManifestTests(LedgerCase):
    def test_without_manifest_there_is_no_mission(self):
        self.assertIsNone(mission_ledger.load_manifest(self.manifest))
        self.assertIsNone(mission_ledger.active_mission(START))
        self.assertIsNone(mission_ledger.reserve_for_active_mission("groq_chat", START))

    def test_manifest_outside_canonical_directory_is_rejected(self):
        outside = self.root / "elsewhere"
        outside.mkdir()
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            self.provision(directory=outside)
        self.assertEqual(caught.exception.code, "MISSION_UNAVAILABLE")

    def test_corrupt_manifest_fails_closed(self):
        self.manifest.write_text("{no json", encoding="utf-8")
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.load_manifest(self.manifest)
        self.assertEqual(caught.exception.code, "MISSION_CORRUPT")

    def test_window_bounds(self):
        config = self.provision()
        self.assertFalse(config.active(START - timedelta(seconds=1)))
        self.assertTrue(config.active(START))
        self.assertFalse(config.active(CUTOFF))


class ReservationTests(LedgerCase):
    def test_counts_before_sending_and_survives_reopen(self):
        config = self.provision()
        first = mission_ledger.reserve(config, "groq_chat", now=START + timedelta(minutes=1))
        self.assertEqual((first["attempt"], first["remaining"]), (1, 2))
        self.assertEqual(len(self.journal_lines()), 1)
        reopened = mission_ledger.load_manifest(self.manifest)
        second = mission_ledger.reserve(reopened, "groq_chat", now=START + timedelta(minutes=2))
        self.assertEqual(second["attempt"], 2)
        self.assertEqual(len(self.journal_lines()), 2)

    def test_cap_is_a_hard_stop(self):
        config = self.provision(cap=2)
        mission_ledger.reserve(config, "groq_chat", now=START)
        mission_ledger.reserve(config, "groq_chat", now=START)
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve(config, "groq_chat", now=START)
        self.assertEqual(caught.exception.code, "MISSION_EXHAUSTED")
        self.assertEqual(len(self.journal_lines()), 2)

    def test_cutoff_blocks_even_with_budget_left(self):
        config = self.provision(cap=100)
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve(config, "groq_chat", now=CUTOFF)
        self.assertEqual(caught.exception.code, "MISSION_CLOSED")
        self.assertEqual(self.journal_lines(), [])

    def test_corrupt_journal_blocks_instead_of_resetting(self):
        self.provision()
        (self.directory / "attempts.jsonl").write_text('{"n": 1}\n', encoding="utf-8")
        config = mission_ledger.load_manifest(self.manifest)
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve(config, "groq_chat", now=START)
        self.assertEqual(caught.exception.code, "MISSION_CORRUPT")

    def test_two_active_missions_are_refused(self):
        self.provision(cap=5)
        other = mission_ledger.mission_dir("paideia-test-mission-2")
        other.mkdir(parents=True)
        self.manifest  # primero ya escrito
        (other / "MISSION.json").write_text(self.manifest.read_text(encoding="utf-8")
                                            .replace(self.mission_id, "paideia-test-mission-2"), encoding="utf-8")
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.active_mission(START)
        self.assertEqual(caught.exception.code, "MISSION_CORRUPT")

    def test_status_reports_used_and_remaining(self):
        config = self.provision(cap=100)
        mission_ledger.reserve(config, "groq_chat", now=START)
        state = mission_ledger.status(config, now=START)
        self.assertEqual((state["used"], state["remaining"], state["active"]), (1, 99, True))


class TransportBoundaryTests(LedgerCase):
    def provision_active(self, cap=5):
        """Ventana que contiene el reloj real: el transporte sella con la hora del sistema.

        La ventana fija de la misión caducó el 4/11/2026 a las 15:21:47Z; con ella, estas
        pruebas del transporte fallaban por corte y no por el comportamiento que miden.
        Las pruebas unitarias conservan la ventana histórica con ``now=`` explícito.
        """
        now = datetime.now(UTC)
        return self.provision(cap=cap, start=now - timedelta(hours=1), cutoff=now + timedelta(hours=1))

    def _post(self, created):
        class Connection:
            status = 200

            def __init__(self, *args, **kwargs):
                created.append(True)

            def connect(self):
                pass

            def request(self, *args, **kwargs):
                pass

            def getresponse(self):
                return self

            def read(self, limit):
                return b'{"choices": []}'

            def close(self):
                pass

        headers = {"Authorization": "Bearer FAKE", "Content-Type": "application/json",
                   "Accept": "application/json"}
        with patch.object(providers.http.client, "HTTPSConnection", Connection):
            return providers.GroqHTTPSJSONTransport().post(
                host=providers.GROQ_HOST, path=providers.GROQ_PATH, headers=headers,
                body=b"{}", timeout=5.0,
            )

    def test_send_without_mission_does_not_touch_the_ledger(self):
        created = []
        self._post(created)
        self.assertEqual(created, [True])
        self.assertFalse((self.directory / "attempts.jsonl").exists())

    def test_active_mission_counts_the_real_send_before_connecting(self):
        self.provision_active(cap=5)
        created = []
        self._post(created)
        self.assertEqual(created, [True])
        self.assertEqual(len(self.journal_lines()), 1)

    def test_exhausted_mission_never_opens_a_connection(self):
        self.provision_active(cap=1)
        (self.directory / "attempts.jsonl").write_text(
            json.dumps({"schema": mission_ledger.JOURNAL_SCHEMA, "n": 1,
                        "at": START.isoformat(), "pid": 1, "route": "groq_chat"}) + "\n",
            encoding="utf-8")
        created = []
        with self.assertRaises(providers.ProviderError) as caught:
            self._post(created)
        self.assertEqual(caught.exception.code, "mission_exhausted")
        self.assertEqual(caught.exception.send_state, providers.SendState.NOT_STARTED)
        self.assertEqual(created, [])
        self.assertEqual(len(self.journal_lines()), 1)


if __name__ == "__main__":
    unittest.main()
