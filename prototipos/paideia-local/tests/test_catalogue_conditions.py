import unittest
from datetime import date

from catalogue_conditions import annual_rate, derive, term_months


def candidate(**overrides):
    base = {
        "candidate_id": "T-1",
        "family": "deposito",
        "candidate_state": "verified",
        "name_literal": "Producto de prueba",
        "available_fields": {},
        "dates": {"checked_at": "2026-11-01"},
        "conflicts": [],
    }
    base.update(overrides)
    return base


TODAY = date(2026, 11, 3)


class RateTests(unittest.TestCase):
    def test_documented_rate_is_known_with_source(self):
        item = candidate(available_fields={
            "rate": {"value_literal": "3,25 % TAE y 3,22 % TIN anual", "source_ids": [5], "effective_from": "2026-10-08"},
        })
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "known")
        self.assertEqual(condition.value, "3.25")
        self.assertEqual(condition.source_ids, ("5",))

    def test_two_distinct_rates_are_a_conflict_not_a_choice(self):
        item = candidate(available_fields={
            "rate": {"value_literal": "3,03 % TAE en portada; 3,00 % TAE en ficha", "source_ids": [7]},
        })
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "conflict")
        self.assertEqual(condition.reason, "MULTIPLE_RATES_DOCUMENTED")
        self.assertIsNone(condition.value)

    def test_known_conflicts_block_the_rate(self):
        item = candidate(conflicts=["La misma página mezcla 2,50 % y 1,25 %."],
                         available_fields={"rate": {"value_literal": "2,50 % TAE", "source_ids": [2]}})
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "conflict")
        self.assertEqual(condition.reason, "SOURCE_CONFLICT")

    def test_unverified_identity_never_provides_a_rate(self):
        item = candidate(candidate_state="proposed",
                         available_fields={"rate": {"value_literal": "3,25 % TAE / 3,20 % TIN"}})
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "unknown")
        self.assertEqual(condition.reason, "IDENTITY_NOT_VERIFIED")

    def test_expired_promotion_is_stale_not_current(self):
        item = candidate(family="cuenta_remunerada", available_fields={
            "promo_tae": {"value_literal": "2,61 % TAE", "source_ids": [1],
                          "effective_from": "2026-10-21", "effective_to": "2026-11-18"},
        })
        self.assertEqual(annual_rate(item, TODAY).state, "known")
        later = annual_rate(item, date(2026, 11, 19))
        self.assertEqual(later.state, "stale")
        self.assertEqual(later.reason, "PROMOTION_EXPIRED")
        self.assertEqual(later.value, "2.61")

    def test_undated_old_retrieval_becomes_stale(self):
        item = candidate(dates={"checked_at": "2026-09-01"},
                         available_fields={"rate": {"value_literal": "2,00 % TAE", "source_ids": [4]}})
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "stale")
        self.assertEqual(condition.reason, "RETRIEVAL_TOO_OLD")

    def test_missing_rate_stays_unknown(self):
        condition = annual_rate(candidate(), TODAY)
        self.assertEqual(condition.state, "unknown")
        self.assertEqual(condition.reason, "RATE_NOT_DOCUMENTED")


class TermTests(unittest.TestCase):
    def test_single_term_is_known(self):
        item = candidate(available_fields={"term": {"value": "12 meses"}})
        condition = term_months(item)
        self.assertEqual((condition.state, condition.value), ("known", "12"))

    def test_term_from_identity_text(self):
        item = candidate(available_fields={"official_document_identity": {"value": "Depósito Open 6 meses"}})
        self.assertEqual(term_months(item).value, "6")

    def test_ambiguous_terms_are_a_conflict(self):
        item = candidate(available_fields={"term": {"value": "6 meses o 12 meses"}})
        self.assertEqual(term_months(item).state, "conflict")


class DeriveTests(unittest.TestCase):
    def test_derive_reports_states_without_inventing(self):
        snapshot = {"candidates": [
            candidate(available_fields={"rate": {"value_literal": "2,00 % TAE", "source_ids": [1]},
                                        "term": {"value": "12 meses"}}),
            candidate(candidate_id="T-2", available_fields={"rate": {"value_literal": "1,50 % TIN"}}),
        ]}
        result = derive(snapshot, TODAY)
        self.assertEqual(result["reference_date"], "2026-11-03")
        self.assertTrue(result["not_for_publication"])
        states = {(p["product_id"], c["metric"]): c["state"] for p in result["products"] for c in p["conditions"]}
        self.assertEqual(states[("T-1", "annual_rate_percent")], "known")
        self.assertEqual(states[("T-1", "term_months")], "known")
        self.assertEqual(states[("T-2", "annual_rate_percent")], "unknown")

    def test_invalid_snapshot_is_rejected(self):
        with self.assertRaises(ValueError):
            derive({"catalogue": "texto"})


class CuratedTests(unittest.TestCase):
    def curated(self, **overrides):
        record = {
            "candidate_id": "C-1",
            "family": "deposito",
            "name": "Depósito de prueba",
            "term_months": 12,
            "source": {"url": "https://example.invalid/ficha", "kind": "official", "retrieved_at": "2026-11-03"},
            "valid_to": None,
            "tiers": [{"condition": "sin_requisito", "condition_label": "Sin requisito", "tae": "3.10", "tin": "3.06"}],
        }
        record.update(overrides)
        return {"records": [record]}

    def test_curated_rate_replaces_prose_literal(self):
        snapshot = {"candidates": [candidate(available_fields={"rate": {"value_literal": "1,00 % TAE"}})]}
        result = derive(snapshot, TODAY, self.curated(candidate_id="T-1"))
        product = next(p for p in result["products"] if p["product_id"] == "T-1")
        rate = next(c for c in product["conditions"] if c["metric"] == "annual_rate_percent")
        self.assertEqual((rate["state"], rate["value"]), ("known", "3.1"))
        self.assertEqual(rate["reason"], "CURATED_OFFICIAL")

    def test_curated_keeps_tiers_apart_from_the_base_rate(self):
        record = self.curated()
        record["records"][0]["tiers"].append({"condition": "nomina_900", "condition_label": "Con nómina", "tae": "3.25", "tin": "3.22"})
        result = derive({"candidates": []}, TODAY, record)
        product = result["products"][0]
        rate = next(c for c in product["conditions"] if c["metric"] == "annual_rate_percent")
        self.assertEqual(rate["value"], "3.1")
        self.assertEqual([tier["condition"] for tier in product["rate_tiers"]], ["sin_requisito", "nomina_900"])

    def test_expired_curated_offer_is_stale(self):
        record = self.curated(valid_to="2026-10-31")
        result = derive({"candidates": []}, TODAY, record)
        rate = next(c for c in result["products"][0]["conditions"] if c["metric"] == "annual_rate_percent")
        self.assertEqual(rate["state"], "stale")
        self.assertEqual(rate["reason"], "PROMOTION_EXPIRED")

    def test_secondary_source_is_flagged(self):
        record = self.curated(source={"url": "https://example.invalid/prensa", "kind": "secondary_press", "retrieved_at": "2026-11-03"})
        result = derive({"candidates": []}, TODAY, record)
        product = result["products"][0]
        rate = next(c for c in product["conditions"] if c["metric"] == "annual_rate_percent")
        self.assertEqual(rate["state"], "known")
        self.assertIn("Fuente secundaria", rate["notes"][0])
        self.assertEqual(product["identity_state"], "press_documented")

    def test_real_curated_file_parses(self):
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "data" / "condiciones.json"
        curated = json.loads(path.read_text(encoding="utf-8"))
        result = derive({"candidates": []}, TODAY, curated)
        rates = {p["product_id"]: next(c for c in p["conditions"] if c["metric"] == "annual_rate_percent")
                 for p in result["products"]}
        self.assertEqual(rates["DEP-02"]["value"], "2.75")
        self.assertEqual(rates["DEP-EBN-12"]["value"], "3.1")
        self.assertEqual(rates["DEP-03"]["state"], "stale")


if __name__ == "__main__":
    unittest.main()
