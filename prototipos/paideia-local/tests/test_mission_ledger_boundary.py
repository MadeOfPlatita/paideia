"""Cupo global: corte duro, aislamiento del mecanismo nocturno y estado de envío.

Cubre los defectos que encontró la revisión independiente del contador:

- El corte solo se aplicaba llamando a `reserve()`; el transporte seguía enviando.
- El contador compartía `Paideia/missions` con la misión nocturna y un manifest ajeno
  lo bloqueaba todo.
- La ruta de sesión contada (`secure_groq_session`) abría su propia conexión HTTPS
  sin pasar por el contador.
- El HTTP de la app devolvía el código de cupo agotado sin `send_state`.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import mission_ledger
import providers
from providers import SendState

UTC = timezone.utc
START = datetime(2026, 11, 4, 10, 0, tzinfo=UTC)
CUTOFF = datetime(2026, 11, 4, 15, 21, 47, tzinfo=UTC)


class RootCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        patcher = patch.dict(os.environ, {"LOCALAPPDATA": str(self.root)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def provision(self, mission_id="paideia-mission-test", start=START, cutoff=CUTOFF, cap=5):
        directory = mission_ledger.mission_dir(mission_id)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "MISSION.json").write_text(json.dumps({
            "schema": mission_ledger.SCHEMA, "mission_id": mission_id,
            "start_utc": start.isoformat(), "cutoff_utc": cutoff.isoformat(), "cap": cap,
        }), encoding="utf-8")
        return directory


class HardCutoffTests(RootCase):
    def test_no_manifest_leaves_the_ordinary_route_alone(self):
        self.assertIsNone(mission_ledger.reserve_for_active_mission("groq_chat", START))

    def test_transport_path_blocks_after_cutoff(self):
        self.provision()
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve_for_active_mission("groq_chat", CUTOFF)
        self.assertEqual(caught.exception.code, "MISSION_CLOSED")

    def test_transport_path_blocks_before_start(self):
        self.provision()
        with self.assertRaises(mission_ledger.MissionBlocked) as caught:
            mission_ledger.reserve_for_active_mission("groq_chat", START - timedelta(seconds=1))
        self.assertEqual(caught.exception.code, "MISSION_CLOSED")

    def test_transport_path_allows_inside_the_window(self):
        self.provision(cap=3)
        token = mission_ledger.reserve_for_active_mission("groq_chat", START + timedelta(minutes=5))
        self.assertEqual(token["attempt"], 1)

    def test_closing_the_manifest_restores_the_ordinary_route(self):
        directory = self.provision()
        (directory / "MISSION.json").unlink()
        self.assertIsNone(mission_ledger.reserve_for_active_mission("groq_chat", CUTOFF))


class NamespaceTests(RootCase):
    def test_ledger_uses_its_own_directory(self):
        self.assertEqual(mission_ledger.mission_dir("x").parent.name, "ledger-missions")

    def test_night_mission_manifest_does_not_block_the_app(self):
        night = self.root / "Paideia" / "missions" / "paideia-night-20261104"
        night.mkdir(parents=True)
        (night / "MISSION.json").write_text(json.dumps({
            "schema": "paideia-night-mission.v1", "mission_id": "paideia-night-20261104",
            "start_utc": START.isoformat(), "cutoff_utc": CUTOFF.isoformat(), "cap": 20,
        }), encoding="utf-8")
        self.assertIsNone(mission_ledger.reserve_for_active_mission("groq_chat", START))


class CountedSessionRouteTests(RootCase):
    def test_counted_session_transport_is_blocked_when_exhausted(self):
        import secure_groq_session

        # La ventana fija caducó el 4/11/2026; el transporte usa el reloj real, así que
        # esta ruta necesita una ventana que contenga el instante de la prueba.
        now = datetime.now(UTC)
        directory = self.provision(cap=1, start=now - timedelta(hours=1), cutoff=now + timedelta(hours=1))
        (directory / "attempts.jsonl").write_text(json.dumps({
            "schema": mission_ledger.JOURNAL_SCHEMA, "n": 1,
            "at": START.isoformat(), "pid": 1, "route": "groq_session"}) + "\n", encoding="utf-8")

        class NeverCalled:
            def __init__(self, *args, **kwargs):
                raise AssertionError("no debe abrirse ninguna conexión con el cupo agotado")

        headers = {"Authorization": "Bearer FAKE", "Content-Type": "application/json",
                   "Accept": "application/json"}
        with patch.object(secure_groq_session.http.client, "HTTPSConnection", NeverCalled):
            with self.assertRaises(providers.ProviderError) as caught:
                secure_groq_session._guarded_https_post(
                    None, host=providers.GROQ_HOST, path=providers.GROQ_PATH,
                    headers=headers, body=b"{}", timeout=5.0, send_guard=lambda: __import__("contextlib").nullcontext())
        self.assertEqual(caught.exception.code, "mission_exhausted")
        self.assertIs(caught.exception.send_state, SendState.NOT_STARTED)


class HttpSendStateTests(RootCase):
    def test_mission_block_reaches_the_client_as_not_started(self):
        from backend_services import MISSION_MESSAGES, ServiceProblem, _mission_block

        error = providers.ProviderError("mission_exhausted", send_state=SendState.NOT_STARTED)
        code, state = _mission_block(error)
        self.assertEqual((code, state), ("mission_exhausted", "not_started"))
        problem = ServiceProblem(429, "CHAT_MISSION_EXHAUSTED", MISSION_MESSAGES[code], send_state=state)
        self.assertEqual(problem.send_state, "not_started")
        self.assertIn("No se envió nada", problem.message)

    def test_other_provider_errors_do_not_claim_not_started(self):
        from backend_services import _mission_block

        error = providers.ProviderError("transport_error", send_state=SendState.UNKNOWN)
        self.assertEqual(_mission_block(error), (None, None))


if __name__ == "__main__":
    unittest.main()
