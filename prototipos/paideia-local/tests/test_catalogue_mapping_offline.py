"""Offline contract tests: every identity and positive fact here is synthetic."""
import copy
import unittest
from datetime import timedelta

import app
from backend_services import CatalogueComparisonService, DEPOSIT_CRITERION
from test_catalogue_facts import synthetic_fact, deposit_policy, AS_OF
from test_backend_integration import running_server, request

IDS = ("SYN-B-01", "SYN-B-02")
PRODUCTS = [{"id": x, "family": "deposito"} for x in IDS]


def fact(pid, **kwargs):
    return synthetic_fact(pid, "3.10", permissions_by_action={"app_display": "allowed"}, **kwargs)


def service(facts, **kwargs):
    return CatalogueComparisonService(facts=facts, policy=deposit_policy(permission_action="app_display"),
                                      allow_synthetic=True, clock=lambda: AS_OF, **kwargs)


class SyntheticRepository(app.CatalogueRepository):
    count = 2
    def get_product(self, product_id):
        if product_id not in IDS:
            return None
        return copy.deepcopy({"id": product_id, "name": "TEST ONLY " + product_id,
            "family": "deposito", "conflicts": [], "unknown_fields": [],
            "publication_ready": False, "identity_state": "synthetic_test"})


class OfflineMappingTests(unittest.TestCase):
    def compare(self, facts, products=PRODUCTS):
        return service(facts).compare(products, DEPOSIT_CRITERION)

    def test_exact_permissions_do_not_alias_display_to_app_display(self):
        for rights in ({"display": "allowed"}, {"display": "allowed", "app_display": "pending"},
                       {"app_display": "blocked"}, {"app_display": "Allowed"}):
            with self.subTest(rights=rights):
                facts = [synthetic_fact(pid, "3.10", permissions_by_action=rights) for pid in IDS]
                result = self.compare(facts)
                self.assertFalse(result["quantitative_ready"])
                self.assertTrue(all(i["value"] is None for i in result["items"]))
                self.assertIn("RIGHTS_BLOCKED" if rights.get("app_display") == "blocked" else "RIGHTS_UNRESOLVED", result["items"][0]["reason_codes"])

    def test_family_and_scope_tokens_are_exact_and_never_normalized(self):
        for update, reason in [({"family": "deposito"}, "FAMILY_MISMATCH"),
                               ({"family": "TERM_DEPOSIT"}, "FAMILY_MISMATCH"),
                               ({"semantic_scope": "term_deposit_offer_terms"}, "SCOPE_MISMATCH"),
                               ({"semantic_scope": "term_deposit_tae "}, "SCOPE_MISMATCH")]:
            with self.subTest(update=update):
                result = self.compare([fact(IDS[0], **update), fact(IDS[1])])
                self.assertFalse(result["quantitative_ready"])
                self.assertIn(reason, result["items"][0]["reason_codes"])
        for family in ("etf_ucits", "Deposito", "deposito "):
            result = self.compare([fact(x) for x in IDS], [PRODUCTS[0], {"id": IDS[1], "family": family}])
            self.assertFalse(result["quantitative_ready"])
            self.assertIn("FAMILY_MISMATCH", result["items"][1]["reason_codes"])

    def test_stale_future_missing_and_conflicting_evidence_excludes(self):
        updates = [({"retrieved_at": "2026-10-25T10:00:00+00:00"}, "SOURCE_STALE"),
                   ({"retrieved_at": "2026-10-28T10:00:00+00:00"}, "RETRIEVED_AT_FUTURE"),
                   ({"effective_at": "2026-10-28"}, "EFFECTIVE_DATE_FUTURE"),
                   ({"effective_at": None, "effective_precision": "not_stated"}, "EFFECTIVE_DATE_UNKNOWN"),
                   ({"validity_state": "unknown"}, "VALIDITY_UNKNOWN")]
        for update, reason in updates:
            with self.subTest(reason=reason):
                result = self.compare([fact(IDS[0], **update), fact(IDS[1])])
                self.assertFalse(result["quantitative_ready"])
                self.assertIn(reason, result["items"][0]["reason_codes"])
                self.assertIsNone(result["items"][0]["value"])
        first = fact(IDS[0])
        result = self.compare([first, first, fact(IDS[1])])
        self.assertTrue(result["quantitative_ready"])
        result = self.compare([first, synthetic_fact(IDS[0], "9.99", permissions_by_action={"app_display": "allowed"}), fact(IDS[1])])
        self.assertFalse(result["quantitative_ready"])
        self.assertIn("DATA_CONFLICT", result["items"][0]["reason_codes"])

    def test_default_policy_and_default_synthetic_exclusion(self):
        facts = [fact(x) for x in IDS]
        result = CatalogueComparisonService(facts=facts, allow_synthetic=True).compare(PRODUCTS, DEPOSIT_CRITERION)
        self.assertFalse(result["quantitative_ready"])
        self.assertTrue(all("FRESHNESS_POLICY_NOT_CONFIGURED" in i["reason_codes"] for i in result["items"]))
        result = CatalogueComparisonService(facts=facts, policy=deposit_policy(permission_action="app_display"), clock=lambda: AS_OF).compare(PRODUCTS, DEPOSIT_CRITERION)
        self.assertFalse(result["quantitative_ready"])
        self.assertTrue(all("SYNTHETIC_FACT_REJECTED" in i["reason_codes"] for i in result["items"]))

    def test_old_synthetic_facts_require_both_explicit_bounded_thresholds(self):
        # Seven years covers the synthetic 2020-to-2026 interval, not a production TTL.
        old = [fact(x, retrieved_at="2020-01-01T00:00:00+00:00", effective_at="2020-01-01", valid_from="2020-01-01") for x in IDS]
        policy = deposit_policy(permission_action="app_display", max_retrieval_age=None, max_effective_age=None)
        result = CatalogueComparisonService(facts=old, policy=policy, allow_synthetic=True, clock=lambda: AS_OF).compare(PRODUCTS, DEPOSIT_CRITERION)
        self.assertFalse(result["quantitative_ready"])
        self.assertTrue(all(i["value"] is None and "FRESHNESS_BOUNDS_UNCONFIGURED" in i["reason_codes"] for i in result["items"]))
        policy = deposit_policy(permission_action="app_display", max_retrieval_age=timedelta(days=7*366), max_effective_age=timedelta(days=7*366))
        result = CatalogueComparisonService(facts=old, policy=policy, allow_synthetic=True, clock=lambda: AS_OF).compare(PRODUCTS, DEPOSIT_CRITERION)
        self.assertTrue(result["quantitative_ready"])
        self.assertTrue(result["test_only"])

    def test_missing_source_fact_fails_closed(self):
        result = self.compare([fact(IDS[0])])
        self.assertFalse(result["quantitative_ready"])
        self.assertIsNone(result["items"][1]["value"])
        self.assertIn("METRIC_MISSING", result["items"][1]["reason_codes"])

    def test_http_synthetic_positive_and_permission_exclusion(self):
        for allowed in (True, False):
            rights = {"app_display": "allowed"} if allowed else {"display": "allowed", "app_display": "pending"}
            facts = [synthetic_fact(x, "3.10", permissions_by_action=rights) for x in IDS]
            with running_server(repository=SyntheticRepository(), comparison_service=service(facts)) as server:
                status, body = request(server, "/api/compare", {"product_ids": list(IDS), "criterion": DEPOSIT_CRITERION})
            self.assertEqual(status, 200)
            self.assertEqual(body["quantitative_ready"], allowed)
            diagnosis = body["comparability"]
            self.assertTrue(diagnosis["not_for_publication"])
            if allowed:
                self.assertTrue(diagnosis["test_only"])
                self.assertEqual(body["comparison_kind"], "test_only_quantitative")
                self.assertTrue(all(i["evidence_class"] == "synthetic_test" for i in diagnosis["items"]))
            else:
                self.assertTrue(all(i["value"] is None and "RIGHTS_UNRESOLVED" in i["reason_codes"] for i in diagnosis["items"]))
