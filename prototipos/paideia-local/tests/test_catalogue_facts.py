import json
import unittest
from datetime import timedelta
from pathlib import Path

from catalogue_facts import (
    ComparisonSpec,
    Fact,
    FreshnessPolicy,
    evaluate_comparability,
)


AS_OF = "2026-10-27T12:00:00+00:00"


def synthetic_fact(product_id, value, *, fact_id=None, **updates):
    fields = {
        "fact_id": fact_id or f"test:{product_id}:tae",
        "product_id": product_id,
        "family": "term_deposit",
        "semantic_scope": "term_deposit_tae",
        "field_path": "deposit.tae",
        "value": value,
        "unit": "PERCENT",
        "currency": "EUR",
        "period": "12_months",
        "effective_at": "2026-10-01",
        "effective_precision": "date",
        "validity_state": "known",
        "valid_from": "2026-10-01",
        "valid_to": "2026-11-01",
        "retrieved_at": "2026-10-27T10:00:00+00:00",
        "state": "known",
        "source_id": "test.synthetic.source",
        "source_revision_id": "test-revision-1",
        "locator": "fixture://test-only/term-deposit/tae",
        "permissions_by_action": {"transform_extract": "allowed"},
        "evidence_class": "synthetic_test",
    }
    fields.update(updates)
    return Fact(**fields)


def deposit_spec(product_ids=("test-product-a", "test-product-b"), **updates):
    fields = {
        "comparison_id": "test-comparison-tae-12m",
        "family": "term_deposit",
        "semantic_scope": "term_deposit_tae",
        "field_path": "deposit.tae",
        "unit": "PERCENT",
        "currency": "EUR",
        "period": "12_months",
        "product_ids": product_ids,
        "permission_action": "transform_extract",
        "as_of": AS_OF,
    }
    fields.update(updates)
    return ComparisonSpec(**fields)


def deposit_policy(**updates):
    fields = {
        "version": "test-only-freshness-v1",
        "family": "term_deposit",
        "semantic_scope": "term_deposit_tae",
        "field_path": "deposit.tae",
        "permission_action": "transform_extract",
        "max_retrieval_age": timedelta(hours=24),
        "max_effective_age": timedelta(days=90),
    }
    fields.update(updates)
    return FreshnessPolicy(**fields)


class CatalogueFactComparabilityTests(unittest.TestCase):
    def test_same_metric_family_period_currency_and_unit_are_comparable(self):
        facts = (
            synthetic_fact("test-product-a", "3.10"),
            synthetic_fact("test-product-b", "3.25"),
        )

        result = evaluate_comparability(facts, deposit_spec(), deposit_policy())
        dto = result.to_dict()

        self.assertTrue(dto["quantitative_ready"])
        self.assertEqual(dto["eligible_product_ids"], ["test-product-a", "test-product-b"])
        self.assertEqual([item["value"] for item in dto["items"]], ["3.10", "3.25"])
        self.assertTrue(all(item["evidence_class"] == "synthetic_test" for item in dto["items"]))
        self.assertEqual(dto["policy_version"], "test-only-freshness-v1")
        self.assertEqual(dto["permission_action"], "transform_extract")
        evidence = dto["items"][0]["source_refs"][0]
        self.assertEqual(evidence["source_revision_id"], "test-revision-1")
        self.assertEqual(evidence["fact_id"], "test:test-product-a:tae")
        self.assertEqual(evidence["source_id"], "test.synthetic.source")
        self.assertEqual(evidence["locator"], "fixture://test-only/term-deposit/tae")
        self.assertEqual(evidence["semantic_scope"], "term_deposit_tae")
        self.assertEqual(evidence["unit"], "PERCENT")
        self.assertEqual(evidence["currency"], "EUR")
        self.assertEqual(evidence["period"], "12_months")
        self.assertEqual(evidence["valid_from"], "2026-10-01")
        self.assertEqual(evidence["valid_to"], "2026-11-01")
        self.assertEqual(evidence["permission_state"], "allowed")
        self.assertEqual(evidence["effective_at"], "2026-10-01")
        self.assertEqual(evidence["effective_precision"], "date")
        self.assertEqual(evidence["retrieved_at"], "2026-10-27T10:00:00+00:00")
        self.assertNotEqual(evidence["effective_at"], evidence["retrieved_at"])

    def test_retrieved_at_does_not_substitute_for_missing_effective_date(self):
        facts = (
            synthetic_fact("test-product-a", "3.10", effective_at=None, effective_precision="not_stated"),
            synthetic_fact("test-product-b", "3.25", effective_at=None, effective_precision="not_stated"),
        )

        dto = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertFalse(dto["quantitative_ready"])
        self.assertTrue(all(item["value"] is None for item in dto["items"]))
        self.assertTrue(all("EFFECTIVE_DATE_UNKNOWN" in item["reason_codes"] for item in dto["items"]))

    def test_not_applicable_null_is_not_a_numeric_zero_or_generic_missing_value(self):
        facts = (
            synthetic_fact("test-product-a", None, state="not_applicable"),
            synthetic_fact("test-product-b", "0.00"),
        )

        dto = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertFalse(dto["quantitative_ready"])
        self.assertIsNone(dto["items"][0]["value"])
        self.assertIn("METRIC_NOT_APPLICABLE", dto["items"][0]["reason_codes"])
        self.assertNotIn("METRIC_MISSING", dto["items"][0]["reason_codes"])
        self.assertTrue(dto["items"][1]["eligible"])
        self.assertEqual(dto["items"][1]["value"], "0.00")

    def test_unknown_conflict_and_unknown_validity_remain_distinct(self):
        facts = (
            synthetic_fact("test-product-a", None, state="unknown"),
            synthetic_fact("test-product-b", None, state="conflict"),
        )

        dto = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertFalse(dto["quantitative_ready"])
        self.assertIn("METRIC_MISSING", dto["items"][0]["reason_codes"])
        self.assertNotIn("DATA_CONFLICT", dto["items"][0]["reason_codes"])
        self.assertIn("DATA_CONFLICT", dto["items"][1]["reason_codes"])
        self.assertTrue(all(item["value"] is None for item in dto["items"]))

    def test_conflicting_values_for_one_metric_are_not_resolved_by_input_order(self):
        facts = (
            synthetic_fact("test-product-a", "3.10", fact_id="test:source-a:tae"),
            synthetic_fact("test-product-a", "3.25", fact_id="test:source-b:tae", source_id="test.other.source"),
            synthetic_fact("test-product-b", "3.20"),
        )

        result = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertFalse(result["quantitative_ready"])
        self.assertFalse(result["items"][0]["eligible"])
        self.assertIsNone(result["items"][0]["value"])
        self.assertIn("DATA_CONFLICT", result["items"][0]["reason_codes"])
        self.assertEqual(len(result["items"][0]["source_refs"]), 2)

    def test_matching_evidence_from_multiple_sources_is_preserved_without_conflict(self):
        facts = (
            synthetic_fact("test-product-a", "3.10", fact_id="test:source-a:tae"),
            synthetic_fact("test-product-a", "3.10", fact_id="test:source-b:tae", source_id="test.other.source"),
            synthetic_fact("test-product-b", "3.25"),
        )

        result = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertTrue(result["quantitative_ready"])
        self.assertTrue(result["items"][0]["eligible"])
        self.assertEqual(result["items"][0]["value"], "3.10")
        self.assertEqual(len(result["items"][0]["source_refs"]), 2)

    def test_permissions_are_scoped_to_action_and_pending_is_not_blocked(self):
        rights = {
            "transform_extract": "allowed",
            "display": "pending",
            "redistribute_raw": "blocked",
        }
        facts = (
            synthetic_fact("test-product-a", "3.10", permissions_by_action=rights),
            synthetic_fact("test-product-b", "3.25", permissions_by_action=rights),
        )

        compute = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()
        display = evaluate_comparability(
            facts,
            deposit_spec(permission_action="display"),
            deposit_policy(permission_action="display"),
        ).to_dict()
        redistribute = evaluate_comparability(
            facts,
            deposit_spec(permission_action="redistribute_raw"),
            deposit_policy(permission_action="redistribute_raw"),
        ).to_dict()

        self.assertTrue(compute["quantitative_ready"])
        self.assertFalse(display["quantitative_ready"])
        self.assertIn("RIGHTS_UNRESOLVED", display["items"][0]["reason_codes"])
        self.assertFalse(redistribute["quantitative_ready"])
        self.assertIn("RIGHTS_BLOCKED", redistribute["items"][0]["reason_codes"])

    def test_retrieval_after_comparison_cutoff_is_not_treated_as_fresh(self):
        facts = (
            synthetic_fact("test-product-a", "3.10", retrieved_at="2026-10-27T12:01:00+00:00"),
            synthetic_fact("test-product-b", "3.25"),
        )

        dto = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertFalse(dto["quantitative_ready"])
        self.assertIn("RETRIEVED_AT_FUTURE", dto["items"][0]["reason_codes"])
        self.assertTrue(dto["items"][1]["eligible"])

    def test_comparison_requires_distinct_products(self):
        with self.assertRaises(ValueError):
            deposit_spec(product_ids=("test-product-a", "test-product-a"))

    def test_fact_value_accepts_only_decimal_strings_or_null(self):
        for value in (3.10, "3,10", "1e2", "NaN", "01.00"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    synthetic_fact("test-product-a", value)
        self.assertIsNone(synthetic_fact("test-product-a", None, state="unknown").value)

    def test_unit_mismatch_has_explicit_versioned_comparability_reason(self):
        facts = (
            synthetic_fact("test-product-a", "3.10", unit="PERCENTAGE_POINT"),
            synthetic_fact("test-product-b", "3.25"),
        )

        dto = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertFalse(dto["quantitative_ready"])
        self.assertEqual(dto["ruleset_version"], "catalogue-fact-comparability.v1")
        self.assertIn("UNIT_MISMATCH", dto["items"][0]["reason_codes"])
        self.assertIn("NUMERIC_BASIS_MISMATCH", dto["items"][0]["reason_codes"])

    def test_fact_rejects_unknown_state_and_precision_tokens(self):
        for updates in (
            {"state": "stale"},
            {"validity_state": "pending"},
            {"effective_precision": "timestamp"},
            {"valid_from": "20261001"},
            {"state": "unknown", "value": "0.00"},
            {"state": "not_applicable", "value": "0.00"},
        ):
            with self.subTest(updates=updates):
                kwargs = dict(updates)
                value = kwargs.pop("value", "3.10")
                with self.assertRaises(ValueError):
                    synthetic_fact("test-product-a", value, **kwargs)

    def test_freshness_policy_is_required_scoped_and_has_no_implicit_ttl(self):
        facts = (
            synthetic_fact("test-product-a", "3.10"),
            synthetic_fact("test-product-b", "3.25"),
        )
        explicitly_bounded = evaluate_comparability(
            facts,
            deposit_spec(),
            deposit_policy(max_retrieval_age=timedelta(hours=24), max_effective_age=timedelta(days=90)),
        )
        self.assertTrue(explicitly_bounded.quantitative_ready)
        with self.assertRaises(TypeError):
            evaluate_comparability(facts, deposit_spec())
        with self.assertRaises(ValueError):
            evaluate_comparability(
                facts,
                deposit_spec(),
                deposit_policy(max_retrieval_age=timedelta(hours=-1)),
            )
        with self.assertRaises(ValueError):
            evaluate_comparability(
                facts,
                deposit_spec(),
                deposit_policy(field_path="fund.nav"),
            )

    def test_currency_and_period_unknown_cannot_become_an_explicit_comparable_basis(self):
        with self.assertRaises(ValueError):
            deposit_spec(currency=None)
        with self.assertRaises(ValueError):
            deposit_spec(period=None)

        facts = (
            synthetic_fact("test-product-a", "3.10", currency=None),
            synthetic_fact("test-product-b", "3.25", period=None),
        )
        dto = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertFalse(dto["quantitative_ready"])
        self.assertIn("CURRENCY_UNKNOWN", dto["items"][0]["reason_codes"])
        self.assertIn("PERIOD_UNKNOWN", dto["items"][1]["reason_codes"])

    def test_auction_and_reference_series_do_not_share_a_numeric_cohort(self):
        facts = (
            synthetic_fact(
                "test-auction", "2.90", family="public_debt_observation",
                field_path="debt.yield", semantic_scope="auction_event",
            ),
            synthetic_fact(
                "test-benchmark", "2.90", family="public_debt_observation",
                field_path="debt.yield", semantic_scope="reference_series",
            ),
        )
        spec = ComparisonSpec(
            comparison_id="test-auction-yield-only",
            family="public_debt_observation",
            field_path="debt.yield",
            semantic_scope="auction_event",
            unit="PERCENT",
            currency="EUR",
            period="2026-10-15",
            product_ids=("test-auction", "test-benchmark"),
            permission_action="transform_extract",
            as_of=AS_OF,
        )
        policy = FreshnessPolicy(
            version="test-only-auction-event-policy.v1",
            family="public_debt_observation",
            field_path="debt.yield",
            semantic_scope="auction_event",
            permission_action="transform_extract",
            max_retrieval_age=timedelta(hours=24),
            max_effective_age=timedelta(days=90),
        )

        dto = evaluate_comparability(facts, spec, policy).to_dict()

        self.assertFalse(dto["quantitative_ready"])
        self.assertIn("SCOPE_MISMATCH", dto["items"][1]["reason_codes"])
        self.assertIn("NUMERIC_BASIS_MISMATCH", dto["items"][1]["reason_codes"])

    def test_fund_nav_and_market_quote_are_not_interchangeable(self):
        facts = (
            synthetic_fact(
                "test-share-class", "100.00", family="fund_share_class",
                field_path="valuation.value", semantic_scope="fund_share_class_nav",
                unit="MONEY", period="2026-10-23",
            ),
            synthetic_fact(
                "test-listing", "100.00", family="market_listing",
                field_path="valuation.value", semantic_scope="market_listing_quote",
                unit="MONEY", period="2026-10-23",
            ),
        )
        spec = ComparisonSpec(
            comparison_id="test-nav-not-quote",
            family="fund_share_class",
            semantic_scope="fund_share_class_nav",
            field_path="valuation.value",
            unit="MONEY",
            currency="EUR",
            period="2026-10-23",
            product_ids=("test-share-class", "test-listing"),
            permission_action="transform_extract",
            as_of=AS_OF,
        )
        policy = FreshnessPolicy(
            version="test-only-nav-policy.v1",
            family="fund_share_class",
            semantic_scope="fund_share_class_nav",
            field_path="valuation.value",
            permission_action="transform_extract",
            max_retrieval_age=timedelta(hours=24),
            max_effective_age=timedelta(days=90),
        )

        dto = evaluate_comparability(facts, spec, policy).to_dict()

        self.assertFalse(dto["quantitative_ready"])
        self.assertTrue(dto["items"][0]["eligible"])
        self.assertIn("FAMILY_MISMATCH", dto["items"][1]["reason_codes"])
        self.assertIn("SCOPE_MISMATCH", dto["items"][1]["reason_codes"])

    def test_unit_currency_period_and_family_must_match_without_conversion(self):
        mismatches = (
            ({"unit": "PERCENTAGE_POINT"}, "UNIT_MISMATCH"),
            ({"currency": "USD"}, "CURRENCY_MISMATCH"),
            ({"period": "6_months"}, "PERIOD_MISMATCH"),
            ({"family": "etf"}, "FAMILY_MISMATCH"),
        )
        for updates, expected_code in mismatches:
            with self.subTest(expected_code=expected_code):
                facts = (
                    synthetic_fact("test-product-a", "3.10", **updates),
                    synthetic_fact("test-product-b", "3.25"),
                )
                dto = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()
                self.assertFalse(dto["quantitative_ready"])
                self.assertIn(expected_code, dto["items"][0]["reason_codes"])
                self.assertIn("NUMERIC_BASIS_MISMATCH", dto["items"][0]["reason_codes"])
                self.assertTrue(dto["items"][1]["eligible"])

    def test_retrieval_age_effective_age_and_validity_are_separate_gates(self):
        stale = synthetic_fact("test-product-a", "3.10", retrieved_at="2026-10-25T10:00:00+00:00")
        unknown_validity = synthetic_fact("test-product-b", "3.25", validity_state="unknown")
        dto = evaluate_comparability((stale, unknown_validity), deposit_spec(), deposit_policy()).to_dict()

        self.assertIn("SOURCE_STALE", dto["items"][0]["reason_codes"])
        self.assertIn("VALIDITY_UNKNOWN", dto["items"][1]["reason_codes"])
        self.assertFalse(dto["quantitative_ready"])

        effective_stale = evaluate_comparability(
            (synthetic_fact("test-product-a", "3.10"), synthetic_fact("test-product-b", "3.25")),
            deposit_spec(),
            deposit_policy(max_effective_age=timedelta(days=1)),
        ).to_dict()
        self.assertTrue(all("METRIC_STALE" in item["reason_codes"] for item in effective_stale["items"]))

    def test_validity_conflict_and_half_open_expiry_exclude_only_the_affected_fact(self):
        conflicted = evaluate_comparability(
            (
                synthetic_fact("test-product-a", "3.10"),
                synthetic_fact("test-product-b", "3.25", validity_state="conflict"),
            ),
            deposit_spec(),
            deposit_policy(),
        ).to_dict()
        self.assertTrue(conflicted["items"][0]["eligible"])
        self.assertFalse(conflicted["items"][1]["eligible"])
        self.assertIn("DATA_CONFLICT", conflicted["items"][1]["reason_codes"])

        expired = evaluate_comparability(
            (
                synthetic_fact("test-product-a", "3.10"),
                synthetic_fact("test-product-b", "3.25", valid_to="2026-10-27"),
            ),
            deposit_spec(),
            deposit_policy(),
        ).to_dict()
        self.assertTrue(expired["items"][0]["eligible"])
        self.assertFalse(expired["items"][1]["eligible"])
        self.assertIn("FACT_EXPIRED", expired["items"][1]["reason_codes"])

    def test_evaluation_is_pure_and_exact_replay_is_idempotent(self):
        first = synthetic_fact("test-product-a", "3.10")
        second = synthetic_fact("test-product-b", "3.25")
        facts = [first, second]
        before = list(facts)

        one = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()
        facts.append(first)
        replay = evaluate_comparability(facts, deposit_spec(), deposit_policy()).to_dict()

        self.assertEqual(facts[:2], before)
        self.assertEqual(one, replay)
        with self.assertRaises((AttributeError, TypeError)):
            first.permissions_by_action["display"] = "allowed"
        with self.assertRaises(AttributeError):
            first.value = "0"

    def test_twenty_catalogue_candidates_remain_inventory_not_quantitative_facts(self):
        project_root = Path(__file__).resolve().parents[3]
        inventory_path = project_root / "docs" / "validacion-04" / "05-catalogo" / "candidatos.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        candidates = inventory["candidates"]

        self.assertEqual(len(candidates), 20)
        self.assertEqual(
            {family: sum(item["family"] == family for item in candidates) for family in {
                "cuenta_remunerada", "deposito", "letra_deuda_publica", "fondo_tradicional", "etf_ucits"
            }},
            {"cuenta_remunerada": 4, "deposito": 4, "letra_deuda_publica": 4,
             "fondo_tradicional": 4, "etf_ucits": 4},
        )
        self.assertTrue(any(
            candidate["candidate_state"] == "verified"
            and candidate.get("isin", {}).get("checksum_valid") is True
            for candidate in candidates
        ))

        for family in sorted({candidate["family"] for candidate in candidates}):
            product_ids = tuple(
                candidate["candidate_id"] for candidate in candidates if candidate["family"] == family
            )
            field_path = "inventory_probe.numeric_metric"
            semantic_scope = "inventory_metadata_probe"
            spec = ComparisonSpec(
                comparison_id=f"inventory-probe-{family}",
                family=family,
                semantic_scope=semantic_scope,
                field_path=field_path,
                unit="PERCENT",
                currency="EUR",
                period="explicit-test-period",
                product_ids=product_ids,
                permission_action="transform_extract",
                as_of=AS_OF,
            )
            policy = FreshnessPolicy(
                version="test-only-empty-inventory-probe.v1",
                family=family,
                semantic_scope=semantic_scope,
                field_path=field_path,
                permission_action="transform_extract",
                max_retrieval_age=timedelta(days=1),
                max_effective_age=timedelta(days=1),
            )
            result = evaluate_comparability((), spec, policy).to_dict()

            self.assertFalse(result["quantitative_ready"])
            self.assertEqual(len(result["items"]), len(product_ids))
            self.assertTrue(all(item["reason_codes"] == ["METRIC_MISSING"] for item in result["items"]))
            self.assertTrue(all(item["value"] is None and item["source_refs"] == [] for item in result["items"]))


if __name__ == "__main__":
    unittest.main()
