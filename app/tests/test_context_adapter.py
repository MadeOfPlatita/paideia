import copy
import importlib.util
import json
import socket
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
ADAPTER_PATH = Path(__file__).resolve().parents[1] / "context_adapter.py"
FIXTURE_PATH = ROOT / "docs" / "validacion-04" / "04-contexto" / "fixtures" / "synthetic-full-profile.json"


def _load_adapter():
    if not ADAPTER_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("paideia_context_adapter_under_test", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = _load_adapter()


def _fixture_envelope():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"), parse_float=Decimal)


def _consent(purpose="liquidity_planning", fields=None, accepted=True):
    if fields is None:
        fields = ["objective", "target_amount_eur"]
    return {
        "notice_version": "context-adapter-test-v1",
        "accepted_chat_processing": accepted,
        "purpose": purpose,
        "approved_fields": list(fields),
    }


def _preview_payload():
    return {
        "synthetic_fixture": True,
        "fixture_id": "synthetic-full-profile-01",
        "purpose": "liquidity_planning",
        "selected_fields": ["objective", "target_amount_eur"],
        "consent": _consent(),
    }


class ContextAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ADAPTER, "context_adapter.py must implement the requested interface")

    def test_preview_loads_only_allowlisted_fixture_and_preserves_decimal(self):
        with patch.object(socket, "socket", side_effect=AssertionError("network socket attempted")), patch.object(
            socket, "create_connection", side_effect=AssertionError("network connection attempted")
        ):
            result = ADAPTER.preview_synthetic(_preview_payload())

        self.assertEqual(result["external_sent"], False)
        self.assertEqual(
            result["projection"],
            {
                "contract_version": "0.1",
                "purpose": "liquidity_planning",
                "fields": {
                    "objective": {"state": "known", "value": "emergency_reserve"},
                    "target_amount_eur": {
                        "state": "known",
                        "value": {"min_eur": "2500.00", "max_eur": "2500.00", "currency": "EUR"},
                    },
                },
            },
        )

    def test_preview_rejects_profile_payload_instead_of_trusting_client_profile(self):
        payload = _preview_payload()
        payload["profile"] = copy.deepcopy(_fixture_envelope()["profile"])
        payload["profile"]["respuestas"]["objetivo"]["valor"] = "gasto_previsto"

        with self.assertRaises(ADAPTER.AdapterError) as raised:
            ADAPTER.preview_synthetic(payload)

        self.assertEqual(raised.exception.code, "INVALID_PAYLOAD")

    def test_preview_rejects_false_synthetic_flag_and_non_allowlisted_fixture_id(self):
        for update in ({"synthetic_fixture": False}, {"fixture_id": "synthetic-full-profile-02"}):
            with self.subTest(update=update):
                payload = _preview_payload()
                payload.update(update)
                with self.assertRaises(ADAPTER.AdapterError):
                    ADAPTER.preview_synthetic(payload)

    def test_preview_requires_consent_and_rejects_withdrawn_field(self):
        rejected = _preview_payload()
        rejected["consent"] = _consent(accepted=False)
        with self.assertRaises(ADAPTER.AdapterError) as raised:
            ADAPTER.preview_synthetic(rejected)
        self.assertEqual(raised.exception.code, "CONSENT_INVALID")

        withdrawn = _preview_payload()
        withdrawn["consent"] = _consent(fields=["objective"])
        with self.assertRaises(ADAPTER.AdapterError) as raised:
            ADAPTER.preview_synthetic(withdrawn)
        self.assertEqual(raised.exception.code, "CONSENT_INVALID")

    def test_preview_rejects_unknown_payload_and_selection_fields(self):
        extra = _preview_payload()
        extra["debug"] = True
        with self.assertRaises(ADAPTER.AdapterError) as raised:
            ADAPTER.preview_synthetic(extra)
        self.assertEqual(raised.exception.code, "INVALID_PAYLOAD")

        unknown = _preview_payload()
        unknown["selected_fields"] = ["monthly_savings_capacity_eur"]
        unknown["consent"] = _consent(fields=unknown["selected_fields"])
        with self.assertRaises(ADAPTER.AdapterError) as raised:
            ADAPTER.preview_synthetic(unknown)
        self.assertEqual(raised.exception.code, "PROJECTION_INVALID")

    def test_variants_share_identical_base_and_hash(self):
        profile = _fixture_envelope()["profile"]
        consent = _consent("learn_basics", ["objective", "learning_level"])
        requests = {
            variant: ADAPTER.build_context_request(
                profile,
                "learn_basics",
                ["objective", "learning_level"],
                consent,
                "Explica de forma educativa qué significa el objetivo declarado.",
                variant=variant,
            )
            for variant in ("A", "B", "C")
        }

        self.assertEqual(requests["A"]["request_schema"], "pai-context-request/v1")
        self.assertEqual(requests["A"]["base"], requests["B"]["base"])
        self.assertEqual(requests["B"]["base"], requests["C"]["base"])
        self.assertEqual(requests["A"]["base_sha256"], requests["B"]["base_sha256"])
        self.assertEqual(requests["B"]["base_sha256"], requests["C"]["base_sha256"])
        self.assertEqual(requests["A"]["messages"][0], requests["B"]["messages"][0])
        self.assertEqual(requests["B"]["messages"][0], requests["C"]["messages"][0])
        self.assertEqual(requests["A"]["profile_context"]["data"], None)
        self.assertEqual(
            set(requests["B"]["profile_context"]["data"]), {"objective", "learning_level"}
        )
        self.assertEqual(requests["C"]["profile_context"]["status"], "complete_synthetic_profile")

    def test_variant_b_contains_only_selected_dto_values_and_a_contains_none(self):
        profile = _fixture_envelope()["profile"]
        fields = ["objective"]
        consent = _consent("learn_basics", fields)
        request_a = ADAPTER.build_context_request(
            profile, "learn_basics", fields, consent, "Pregunta sintética de prueba.", variant="A"
        )
        request_b = ADAPTER.build_context_request(
            profile, "learn_basics", fields, consent, "Pregunta sintética de prueba.", variant="B"
        )

        self.assertEqual(set(request_b["profile_context"]["data"]), {"objective"})
        self.assertTrue(request_b["profile_context"]["excluded_fields"])
        self.assertTrue(
            all("Campo no seleccionado" in item["reason"] for item in request_b["profile_context"]["excluded_fields"])
        )
        self.assertNotIn("Campo no seleccionado", request_b["messages"][1]["content"])
        self.assertNotIn("monthly_income_eur", request_b["messages"][1]["content"])
        self.assertNotIn("2800.00", request_b["messages"][1]["content"])
        self.assertNotIn("emergency_reserve", request_a["messages"][1]["content"])
        self.assertNotIn("2500.00", request_a["messages"][1]["content"])
        self.assertEqual(request_a["messages"][1]["content"].count("Pregunta sintética de prueba."), 1)

    def test_variant_c_rejects_any_profile_other_than_authorized_fixture(self):
        profile = copy.deepcopy(_fixture_envelope()["profile"])
        profile["respuestas"]["objetivo"]["valor"] = "gasto_previsto"

        with self.assertRaises(ADAPTER.AdapterError) as raised:
            ADAPTER.build_context_request(
                profile,
                "learn_basics",
                ["objective"],
                _consent("learn_basics", ["objective"]),
                "Pregunta sintética.",
                variant="C",
            )

        self.assertEqual(raised.exception.code, "SYNTHETIC_FIXTURE_REQUIRED")

    def test_unknown_income_is_not_zero_and_selection_does_not_mutate_profile(self):
        unknown_profile = copy.deepcopy(_fixture_envelope()["profile"])
        unknown_profile["detalle_economico"]["ingresos_netos"] = {"estado": "no_se"}
        original = copy.deepcopy(unknown_profile)
        zero_profile = copy.deepcopy(unknown_profile)
        zero_profile["detalle_economico"]["ingresos_netos"] = {
            "estado": "declarado",
            "valor": {
                "importe": {
                    "min_eur": Decimal("0.00"),
                    "max_eur": Decimal("0.00"),
                    "moneda": "EUR",
                },
                "periodicidad": "mensual",
            },
        }
        consent = _consent("debt_education", ["monthly_income_eur"])

        unknown_request = ADAPTER.build_context_request(
            unknown_profile,
            "debt_education",
            ["monthly_income_eur"],
            consent,
            "Pregunta sintética.",
        )
        zero_request = ADAPTER.build_context_request(
            zero_profile,
            "debt_education",
            ["monthly_income_eur"],
            consent,
            "Pregunta sintética.",
        )

        self.assertEqual(unknown_request["profile_context"]["data"], {"monthly_income_eur": {"state": "unknown"}})
        self.assertEqual(
            zero_request["profile_context"]["data"],
            {
                "monthly_income_eur": {
                    "state": "known",
                    "value": {
                        "amount": {"min_eur": "0.00", "max_eur": "0.00", "currency": "EUR"},
                        "periodicity": "monthly",
                    },
                }
            },
        )
        self.assertEqual(unknown_profile, original)

    def test_selected_financial_decimal_survives_messages_and_projection_exactly(self):
        profile = _fixture_envelope()["profile"]
        fields = ["target_amount_eur"]
        request = ADAPTER.build_context_request(
            profile,
            "liquidity_planning",
            fields,
            _consent("liquidity_planning", fields),
            "Pregunta sintética sobre una meta.",
        )

        self.assertEqual(
            request["profile_context"]["data"]["target_amount_eur"]["value"]["min_eur"], "2500.00"
        )
        self.assertIn('"min_eur":"2500.00"', request["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
