"""Pruebas del catálogo cerrado de afirmaciones y de su canal de composición.

Todo el módulo es puro: no abre red, no usa proveedor y no escribe estado.
Se ejecuta con ``python -m pytest tests/test_claims_channel.py -q``.
"""
import copy
import json
import unittest

import claims_catalog
import claims_channel

VERSION = "paideia-education-v2"
REASONS = (
    "invalid_shape",
    "invalid_version",
    "invalid_intent",
    "invalid_claim_id",
    "duplicate_claim",
    "too_many_claims",
    "invalid_evidence_ref",
)
VALID = {
    "version": VERSION,
    "intent": "explain",
    "claim_ids": ["interes_tae_equivalente", "garantia_de_depositos_que_es"],
}
ALL_IDS = tuple(claims_catalog.CLAIMS)


def selection(**changes):
    """Copia independiente de una selección válida con los cambios indicados."""
    raw = copy.deepcopy(VALID)
    raw.update(changes)
    return raw


class ClaimsCatalogTests(unittest.TestCase):
    def test_version_limit_and_size(self):
        self.assertEqual(claims_catalog.VERSION, VERSION)
        self.assertEqual(claims_channel.VERSION, VERSION)
        self.assertEqual(len(claims_catalog.CLAIMS), 39)
        self.assertEqual(claims_catalog.MAX_CLAIMS, 6)
        self.assertEqual(claims_channel.MAX_CLAIMS, 6)
        self.assertEqual(claims_channel.MAX_CLAIMS, claims_catalog.MAX_CLAIMS)

    def test_every_entry_has_exactly_the_three_editorial_fields(self):
        for claim_id, entry in claims_catalog.CLAIMS.items():
            with self.subTest(claim_id=claim_id):
                self.assertIsInstance(claim_id, str)
                self.assertTrue(claim_id)
                self.assertEqual(set(entry), {"text", "when", "never_claim"})
                for field in ("text", "when", "never_claim"):
                    self.assertIsInstance(entry[field], str)
                    self.assertTrue(entry[field].strip())

    def test_groups_partition_the_catalog_by_prefix(self):
        expected = {
            "alcance_": 3,
            "ahorro_": 3,
            "interes_": 5,
            "inflacion_": 4,
            "liquidez_": 4,
            "comparar_": 5,
            "garantia_": 6,
            "fuente_": 5,
            "simulacion_": 4,
        }
        self.assertEqual({prefix: len(ids) for prefix, ids in claims_catalog.GROUPS.items()}, expected)
        grouped = [claim_id for ids in claims_catalog.GROUPS.values() for claim_id in ids]
        self.assertEqual(len(grouped), 39)
        self.assertEqual(set(grouped), set(claims_catalog.CLAIMS))
        for prefix, ids in claims_catalog.GROUPS.items():
            for claim_id in ids:
                self.assertTrue(claim_id.startswith(prefix))

    def test_texts_contain_no_figures_or_status_words(self):
        banned = ("oficial", "vigente", "vigencia")
        for claim_id, entry in claims_catalog.CLAIMS.items():
            text = entry["text"]
            with self.subTest(claim_id=claim_id):
                self.assertFalse(any(character.isdigit() for character in text), text)
                self.assertNotIn("%", text)
                self.assertNotIn("€", text)
                for word in banned:
                    self.assertNotIn(word, text.lower())

    def test_catalog_is_immutable(self):
        entry = claims_catalog.CLAIMS["alcance_datos_que_faltan"]
        with self.assertRaises(TypeError):
            entry["text"] = "texto sustituido"
        with self.assertRaises(TypeError):
            claims_catalog.CLAIMS["afirmacion_nueva"] = entry
        with self.assertRaises(TypeError):
            del claims_catalog.CLAIMS["alcance_datos_que_faltan"]
        with self.assertRaises(TypeError):
            claims_catalog.GROUPS["otro_"] = ()
        self.assertIn("alcance_datos_que_faltan", claims_catalog.CLAIMS)


class ValidateSelectionTests(unittest.TestCase):
    def test_minimal_selection_is_normalized_with_empty_evidence_refs(self):
        result = claims_channel.validate_selection(selection())
        self.assertEqual(result, {**VALID, "evidence_refs": []})
        self.assertEqual(set(result), {"version", "intent", "claim_ids", "evidence_refs"})
        self.assertIsNot(result, VALID)
        self.assertIsNot(result["claim_ids"], VALID["claim_ids"])

    def test_selection_preserves_order_and_evidence_refs(self):
        raw = selection(
            intent="calculate",
            evidence_refs=["identity:DEP-EJEMPLO", "identity:SYN-01"],
        )
        result = claims_channel.validate_selection(raw)
        self.assertEqual(result["intent"], "calculate")
        self.assertEqual(result["claim_ids"], VALID["claim_ids"])
        self.assertEqual(result["evidence_refs"], ["identity:DEP-EJEMPLO", "identity:SYN-01"])

    def test_root_must_be_an_exact_dict(self):
        class DictSubclass(dict):
            pass

        for raw in (None, True, False, [], "selection", 3, (), DictSubclass(VALID)):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError) as raised:
                    claims_channel.validate_selection(raw)
                self.assertEqual(str(raised.exception), "invalid_shape")

    def test_key_sets_are_exact(self):
        cases = (
            {"version": VERSION, "intent": "explain"},
            {"version": VERSION, "intent": "explain", "evidence_refs": []},
            {**VALID, "evidence_refs": [], "answer": "texto del modelo"},
            {**VALID, "scenario": {}},
            {**VALID, "extra": None},
        )
        for raw in cases:
            with self.subTest(keys=tuple(raw)):
                with self.assertRaises(ValueError) as raised:
                    claims_channel.validate_selection(raw)
                self.assertEqual(str(raised.exception), "invalid_shape")

    def test_version_must_be_the_exact_closed_version(self):
        for version in ("paideia-education-v1", "PAIDEIA-EDUCATION-V2", "", 2, None, True):
            with self.subTest(version=version):
                with self.assertRaises(ValueError) as raised:
                    claims_channel.validate_selection(selection(version=version))
                self.assertEqual(str(raised.exception), "invalid_version")

    def test_intent_is_closed_to_explain_and_calculate(self):
        for intent in ("recommend", "EXPLAIN", "", 1, None, True, ["explain"]):
            with self.subTest(intent=intent):
                with self.assertRaises(ValueError) as raised:
                    claims_channel.validate_selection(selection(intent=intent))
                self.assertEqual(str(raised.exception), "invalid_intent")

    def test_claim_ids_must_be_a_list(self):
        for claim_ids in (None, "interes_tae_equivalente", 1, True, {}, ()):
            with self.subTest(claim_ids=claim_ids):
                with self.assertRaises(ValueError) as raised:
                    claims_channel.validate_selection(selection(claim_ids=claim_ids))
                self.assertEqual(str(raised.exception), "invalid_shape")

    def test_claim_ids_must_be_known_strings(self):
        for claim_ids in (["no_existe"], [1], [None], [True], [["interes_tae_equivalente"]]):
            with self.subTest(claim_ids=claim_ids):
                with self.assertRaises(ValueError) as raised:
                    claims_channel.validate_selection(selection(claim_ids=claim_ids))
                self.assertEqual(str(raised.exception), "invalid_claim_id")

    def test_duplicates_are_rejected(self):
        claim_ids = ["interes_tae_equivalente", "interes_tae_equivalente"]
        with self.assertRaises(ValueError) as raised:
            claims_channel.validate_selection(selection(claim_ids=claim_ids))
        self.assertEqual(str(raised.exception), "duplicate_claim")

    def test_seven_claims_exceed_the_limit(self):
        with self.assertRaises(ValueError) as raised:
            claims_channel.validate_selection(selection(claim_ids=list(ALL_IDS[:7])))
        self.assertEqual(str(raised.exception), "too_many_claims")

    def test_six_claims_are_accepted(self):
        result = claims_channel.validate_selection(selection(claim_ids=list(ALL_IDS[:6])))
        self.assertEqual(len(result["claim_ids"]), 6)

    def test_empty_selection_is_rejected(self):
        """Un turno sin ninguna afirmación no es una respuesta del canal."""
        with self.assertRaises(ValueError) as error:
            claims_channel.validate_selection(selection(claim_ids=[]))
        self.assertEqual(str(error.exception), "invalid_shape")

    def test_every_catalog_id_is_selectable(self):
        for claim_id in ALL_IDS:
            with self.subTest(claim_id=claim_id):
                result = claims_channel.validate_selection(selection(claim_ids=[claim_id]))
                self.assertEqual(result["claim_ids"], [claim_id])

    def test_evidence_refs_must_be_identity_strings(self):
        cases = (
            "identity:DEP-EJEMPLO",
            {},
            [1],
            [None],
            [True],
            [["identity:DEP-EJEMPLO"]],
            ["DEP-EJEMPLO"],
            ["product:DEP-EJEMPLO"],
            ["identity:"],
            ["identity"],
            ["identity:DEP EJEMPLO"],
            ["identity:DEP/EJEMPLO"],
            ["identity: DEP-EJEMPLO"],
            ["identity:" + "A" * 80],
            ["identity:DEP-EJEMPLO"] * 2,
            ["identity:DEP-EJEMPLO", "identity:SYN-01", "identity:SYN-02", "identity:SYN-03"],
        )
        for refs in cases:
            with self.subTest(refs=refs):
                with self.assertRaises(ValueError) as raised:
                    claims_channel.validate_selection(selection(evidence_refs=refs))
                self.assertEqual(str(raised.exception), "invalid_evidence_ref")

    def test_three_evidence_refs_are_accepted(self):
        refs = ["identity:DEP-EJEMPLO", "identity:SYN-01", "identity:SYN-02"]
        result = claims_channel.validate_selection(selection(evidence_refs=refs))
        self.assertEqual(result["evidence_refs"], refs)


class ComposeTests(unittest.TestCase):
    def test_compose_uses_only_catalog_texts_in_selection_order(self):
        result = claims_channel.compose(selection(evidence_refs=["identity:DEP-EJEMPLO"]))
        texts = [claims_catalog.CLAIMS[claim_id]["text"] for claim_id in VALID["claim_ids"]]
        self.assertEqual(result["answer"], "\n\n".join(texts))
        self.assertEqual([item["id"] for item in result["claims"]["items"]], VALID["claim_ids"])
        self.assertEqual([item["text"] for item in result["claims"]["items"]], texts)
        self.assertEqual(
            result["claims"],
            {
                "version": VERSION,
                "state": "shown",
                "items": [
                    {"id": VALID["claim_ids"][index], "text": texts[index]}
                    for index in range(len(texts))
                ],
                "count": 2,
            },
        )
        self.assertEqual(set(result), {"answer", "claims", "calculation", "sources"})
        self.assertEqual(set(result["claims"]), {"version", "state", "items", "count"})
        self.assertEqual(set(result["claims"]["items"][0]), {"id", "text"})
        self.assertIsNone(result["calculation"])
        self.assertEqual(result["sources"], [])

    def test_answer_is_exactly_the_union_of_catalog_texts(self):
        result = claims_channel.compose(selection())
        parts = result["answer"].split("\n\n")
        self.assertEqual(len(parts), len(VALID["claim_ids"]))
        for part in parts:
            self.assertIn(part, {entry["text"] for entry in claims_catalog.CLAIMS.values()})
        self.assertFalse(any(character.isdigit() for character in result["answer"]))

    def test_compose_passes_calculation_and_sources_without_paraphrasing(self):
        calculation = {
            "source": "deterministic_local",
            "summary": {"final_balance": "1030.00"},
        }
        sources = [{"tool": "search_products", "source_ref": {"id": "identity:DEP-EJEMPLO"}}]
        result = claims_channel.compose(selection(), calculation=calculation, sources=sources)
        self.assertEqual(result["calculation"], calculation)
        self.assertEqual(result["sources"], sources)
        self.assertNotIn("1030", result["answer"])
        for character in result["answer"]:
            self.assertFalse(character.isdigit())

    def test_compose_does_not_mutate_selection_or_catalog(self):
        raw = selection(evidence_refs=["identity:DEP-EJEMPLO"])
        raw_before = copy.deepcopy(raw)
        catalog_before = {claim_id: dict(entry) for claim_id, entry in claims_catalog.CLAIMS.items()}
        result = claims_channel.compose(raw)
        self.assertEqual(raw, raw_before)
        self.assertEqual(
            {claim_id: dict(entry) for claim_id, entry in claims_catalog.CLAIMS.items()},
            catalog_before,
        )

        result["claims"]["items"].append({"id": "x", "text": "y"})
        result["claims"]["items"][0]["text"] = "texto mutado"
        self.assertEqual(
            claims_catalog.CLAIMS[VALID["claim_ids"][0]]["text"],
            catalog_before[VALID["claim_ids"][0]]["text"],
        )
        self.assertEqual(
            claims_channel.compose(raw)["claims"]["items"][0]["text"],
            catalog_before[VALID["claim_ids"][0]]["text"],
        )

    def test_unknown_claim_produces_no_partial_text(self):
        raw = selection(claim_ids=["interes_tae_equivalente", "afirmacion_inventada"])
        with self.assertRaises(ValueError) as raised:
            claims_channel.compose(raw)
        self.assertEqual(str(raised.exception), "invalid_claim_id")

    def test_compose_rejects_invalid_selection_instead_of_degrading(self):
        for raw in (None, {**VALID, "intent": "recommend"}, selection(claim_ids=["no_existe"])):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    claims_channel.compose(raw)

    def test_compose_is_deterministic_byte_to_byte(self):
        raw = selection(evidence_refs=["identity:DEP-EJEMPLO"])
        first = claims_channel.compose(raw)
        second = claims_channel.compose(copy.deepcopy(raw))
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True),
            json.dumps(second, ensure_ascii=False, sort_keys=True),
        )

    def test_compose_accepts_a_normalized_selection(self):
        normalized = claims_channel.validate_selection(selection())
        self.assertEqual(
            claims_channel.compose(normalized),
            claims_channel.compose(selection()),
        )


class RejectedTests(unittest.TestCase):
    def test_rejected_shape_for_every_reason(self):
        self.assertEqual(tuple(claims_channel.REJECTION_REASONS), REASONS)
        for reason in REASONS:
            with self.subTest(reason=reason):
                result = claims_channel.rejected(reason)
                self.assertEqual(
                    result,
                    {
                        "answer": "",
                        "claims": {
                            "version": VERSION,
                            "state": "rejected",
                            "items": [],
                            "count": 0,
                            "reason": reason,
                        },
                        "calculation": None,
                        "sources": [],
                    },
                )
                self.assertEqual(set(result), {"answer", "claims", "calculation", "sources"})
                self.assertEqual(
                    set(result["claims"]),
                    {"version", "state", "items", "count", "reason"},
                )

    def test_rejected_never_echoes_model_text(self):
        for reason in ("El modelo dijo: invierte todo en X", "", None, 1, True, "invalid_json"):
            with self.subTest(reason=reason):
                with self.assertRaises(ValueError) as raised:
                    claims_channel.rejected(reason)
                self.assertEqual(str(raised.exception), "invalid_reason")

    def test_rejected_does_not_share_mutable_state_between_calls(self):
        first = claims_channel.rejected("invalid_shape")
        first["claims"]["items"].append({"id": "x", "text": "y"})
        first["sources"].append({"tool": "x"})
        second = claims_channel.rejected("invalid_shape")
        self.assertEqual(second["claims"]["items"], [])
        self.assertEqual(second["sources"], [])


if __name__ == "__main__":
    unittest.main()
