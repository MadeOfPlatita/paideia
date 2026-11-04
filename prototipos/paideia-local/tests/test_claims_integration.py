"""Canal cerrado v2 (afirmaciones estructuradas) extremo a extremo, sin red.

Fija el contrato que la UI y el backend comparten:

- el modelo solo aporta identificadores; el texto lo pone el servidor;
- una selección v2 válida produce `claims.state='shown'`, un `answer` que es
  exactamente la unión de los textos del catálogo y, si hay escenario, el
  cálculo determinista;
- un id desconocido o una forma inválida no producen texto parcial;
- v1 sigue funcionando sin cambios (compatibilidad hacia atrás).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))

from claims_catalog import VERSION, CLAIM_IDS, CLAIMS, MAX_CLAIMS  # noqa: E402
from claims_channel import compose, rejected, validate_selection  # noqa: E402
from backend_services import _rejected_turn  # noqa: E402
from structured_education import render_selection, VERSION as V1  # noqa: E402


def selection(ids, intent="explain", **extra):
    payload = {"version": VERSION, "intent": intent, "claim_ids": list(ids)}
    payload.update(extra)
    return payload


class ChannelTests(unittest.TestCase):
    def test_catalog_has_the_agreed_shape(self):
        self.assertEqual(VERSION, "paideia-education-v2")
        self.assertEqual(MAX_CLAIMS, 6)
        self.assertEqual(len(CLAIM_IDS), 39)
        for claim_id in CLAIM_IDS:
            entry = CLAIMS[claim_id]
            self.assertEqual(set(entry), {"text", "when", "never_claim"})
            self.assertFalse(any(char.isdigit() for char in entry["text"]), claim_id)
            for token in ("%", "€", "oficial", "vigente", "vigencia"):
                self.assertNotIn(token, entry["text"].lower(), claim_id)

    def test_compose_uses_only_server_text(self):
        ids = [CLAIM_IDS[0], CLAIM_IDS[1]]
        result = compose(selection(ids))
        self.assertEqual(result["claims"]["state"], "shown")
        self.assertEqual([item["id"] for item in result["claims"]["items"]], ids)
        self.assertEqual(result["answer"], "\n\n".join(CLAIMS[i]["text"] for i in ids))

    def test_render_selection_dispatches_on_version(self):
        rendered = render_selection(selection([CLAIM_IDS[0], CLAIM_IDS[2]]))
        self.assertEqual(rendered["structured_education"]["version"], VERSION)
        self.assertEqual(rendered["structured_education"]["kind"], "claims")
        self.assertEqual(rendered["claims"]["count"], 2)
        self.assertEqual(rendered["provider_mode"], "test_only")
        self.assertFalse(rendered["external_sent"])

    def test_v1_still_renders(self):
        v1 = {"version": V1, "intent": "explain", "claim_ids": ["risk"]}
        rendered = render_selection(v1)
        self.assertNotIn("claims", rendered)
        self.assertTrue(rendered["answer"].startswith("Los riesgos dependen"))


class RejectionTests(unittest.TestCase):
    def test_unknown_id_is_rejected_without_partial_text(self):
        with self.assertRaises(ValueError) as error:
            compose(selection([CLAIM_IDS[0], "no_existe"]))
        self.assertEqual(str(error.exception), "invalid_claim_id")

    def test_too_many_claims(self):
        with self.assertRaises(ValueError) as error:
            compose(selection(CLAIM_IDS[: MAX_CLAIMS + 1]))
        self.assertEqual(str(error.exception), "too_many_claims")

    def test_duplicate_claim(self):
        with self.assertRaises(ValueError) as error:
            compose(selection([CLAIM_IDS[0], CLAIM_IDS[0]]))
        self.assertEqual(str(error.exception), "duplicate_claim")

    def test_extra_key_is_rejected(self):
        with self.assertRaises(ValueError):
            compose(selection([CLAIM_IDS[0]], texto="prosa del modelo"))

    def test_bool_is_not_a_valid_container(self):
        with self.assertRaises(ValueError):
            compose(True)

    def test_rejected_state_carries_no_text(self):
        payload = rejected("invalid_claim_id")
        self.assertEqual(payload["answer"], "")
        self.assertEqual(payload["claims"]["state"], "rejected")
        self.assertEqual(payload["claims"]["reason"], "invalid_claim_id")
        self.assertEqual(payload["claims"]["items"], [])

    def test_rejected_refuses_free_text_reason(self):
        with self.assertRaises(ValueError):
            rejected("el modelo dijo algo")

    def test_rejected_turn_is_a_valid_response_without_text(self):
        """Un rechazo del canal es 200 con estado, no un error de proveedor."""
        turn = _rejected_turn("invalid_claim_id")
        self.assertEqual(turn["answer"], "")
        self.assertEqual(turn["claims"]["state"], "rejected")
        self.assertEqual(turn["claims"]["reason"], "invalid_claim_id")
        self.assertEqual(turn["structured_education"]["kind"], "claims")
        self.assertEqual(turn["structured_education"]["items"], [])
        self.assertFalse(turn["external_sent"])


class ScenarioTests(unittest.TestCase):
    scenario = {"principal": "1000.00", "annual_rate_percent": "3.00", "years": 2,
                "monthly_contribution": "0.00", "method": "compound",
                "inflation_percent": "0.00"}

    def test_calculation_comes_from_the_engine(self):
        rendered = render_selection(selection([CLAIM_IDS[0]], intent="calculate"),
                                    self.scenario, scenario_present=True)
        data = rendered["structured_education"]["calculation"]["data"]
        self.assertEqual(data["summary"]["final_balance"], "1060.90")
        self.assertEqual(data["summary"]["interest"], "60.90")
        # El texto de las afirmaciones no incorpora la cifra del motor.
        self.assertNotIn("1060,90", rendered["answer"])

    def test_calculate_without_scenario_is_rejected(self):
        with self.assertRaises(ValueError):
            render_selection(selection([CLAIM_IDS[0]], intent="calculate"))


if __name__ == "__main__":
    unittest.main()
