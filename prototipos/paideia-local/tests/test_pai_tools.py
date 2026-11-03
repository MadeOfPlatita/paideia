import unittest

from pai_tools import ToolDispatcher


class ToolDispatcherDefinitionTests(unittest.TestCase):
    def test_definitions_expose_exact_local_tools(self):
        dispatcher = ToolDispatcher(repository=None, comparison_service=None)

        definitions = dispatcher.definitions()

        self.assertEqual([item["function"]["name"] for item in definitions], [
            "search_products",
            "get_product_detail",
            "compare_products",
            "calculate_scenario",
            "get_sources",
        ])
        self.assertTrue(all(item["type"] == "function" for item in definitions))
        self.assertTrue(all(item["function"]["parameters"]["additionalProperties"] is False
                            for item in definitions))

    def test_definitions_are_accepted_by_offline_provider_request_builder(self):
        import json

        from providers import build_chat_request

        dispatcher = ToolDispatcher(repository=None, comparison_service=None)
        payload = build_chat_request(
            [{"role": "user", "content": "Busca SYN-01"}],
            tools=dispatcher.definitions(),
        )
        body = json.loads(payload.decode("utf-8"))

        self.assertEqual(
            [tool["function"]["name"] for tool in body["tools"]],
            ["search_products", "get_product_detail", "compare_products", "calculate_scenario", "get_sources"],
        )

    def test_scenario_definition_mirrors_domain_decimal_and_year_bounds(self):
        definition = next(item["function"] for item in ToolDispatcher(None, None).definitions()
                          if item["function"]["name"] == "calculate_scenario")
        parameters = definition["parameters"]
        properties = parameters["properties"]

        self.assertEqual(set(properties), {
            "principal", "annual_rate_percent", "years", "monthly_contribution",
            "method", "inflation_percent",
        })
        self.assertEqual(parameters["required"], [
            "principal", "annual_rate_percent", "years", "monthly_contribution",
            "method", "inflation_percent",
        ])
        amount_pattern = r"^-?(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?$"
        rate_pattern = r"^-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,4})?$"
        self.assertEqual(properties["principal"]["pattern"], amount_pattern)
        self.assertEqual(properties["monthly_contribution"]["pattern"], amount_pattern)
        self.assertEqual(properties["annual_rate_percent"]["pattern"], rate_pattern)
        self.assertEqual(properties["inflation_percent"]["pattern"], rate_pattern)
        self.assertEqual((properties["years"]["minimum"], properties["years"]["maximum"]), (1, 40))


class SyntheticRepository:
    """In-memory, test-only source; it never reads or writes project data."""

    def __init__(self):
        self.products = [
            {
                "id": f"SYN-{number:02d}",
                "name": f"Synthetic candidate {number}",
                "family": "deposito",
                "issuer": "Synthetic issuer",
                "isin": None,
                "identity_state": "proposed",
                "primary_url": f"https://example.invalid/synthetic/SYN-{number:02d}",
                "as_of": None,
                "publication_ready": False,
                "conditions_state": "pending",
                "conflicts": [],
                "unknown_fields": ["conditions"],
                "private_internal": "must not escape",
            }
            for number in (1, 2, 3)
        ]
        self.snapshot = __import__("copy").deepcopy(self.products)
        self.calls = []

    def list_products(self, q=None, family=None):
        self.calls.append(("list_products", q, family))
        return [
            __import__("copy").deepcopy(product)
            for product in self.products
            if (q is None or q.casefold() in product["name"].casefold())
            and (family is None or family == product["family"])
        ]

    def get_product(self, product_id):
        self.calls.append(("get_product", product_id))
        for product in self.products:
            if product["id"] == product_id:
                return __import__("copy").deepcopy(product)
        return None


class ToolDispatcherSearchTests(unittest.TestCase):
    def test_search_is_bounded_whitelisted_and_cites_identity_only(self):
        repository = SyntheticRepository()
        dispatcher = ToolDispatcher(repository=repository, comparison_service=None)
        arguments = {"query": "Synthetic", "family": "deposito", "limit": 1}
        original_arguments = __import__("copy").deepcopy(arguments)

        result = dispatcher.dispatch("search_products", arguments)

        self.assertEqual(result["schema_version"], "local-tools.v1")
        self.assertEqual(result["tool"], "search_products")
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(result["error"])
        self.assertEqual(result["data"]["count"], 1)
        self.assertEqual(result["data"]["limit"], 1)
        self.assertTrue(result["data"]["not_for_publication"])
        self.assertEqual([item["id"] for item in result["data"]["items"]], ["SYN-01"])
        self.assertNotIn("private_internal", result["data"]["items"][0])
        self.assertEqual(result["sources"], [{
            "source_ref": {"namespace": "local-tools.v1", "id": "identity:SYN-01"},
            "product_id": "SYN-01",
            "kind": "identity",
            "claim_scope": "product_identity_only",
            "label": "Synthetic candidate 1",
            "url": "https://example.invalid/synthetic/SYN-01",
            "not_for_publication": True,
        }])
        self.assertEqual(arguments, original_arguments)
        self.assertEqual(repository.products, repository.snapshot)


class ToolDispatcherDetailTests(unittest.TestCase):
    def test_detail_returns_internal_metadata_for_exact_local_id(self):
        repository = SyntheticRepository()
        dispatcher = ToolDispatcher(repository=repository, comparison_service=None)

        result = dispatcher.dispatch("get_product_detail", {"product_id": "SYN-02"})

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["product"]["id"], "SYN-02")
        self.assertFalse(result["data"]["product"]["publication_ready"])
        self.assertEqual(result["data"]["product"]["conditions_state"], "pending")
        self.assertEqual(result["data"]["scope"], "product_identity_only")
        self.assertEqual([source["product_id"] for source in result["sources"]], ["SYN-02"])
        self.assertEqual(repository.calls, [("get_product", "SYN-02")])


class ToolDispatcherCompareTests(unittest.TestCase):
    def test_compare_without_criterion_is_metadata_only_and_skips_metric_service(self):
        repository = SyntheticRepository()
        dispatcher = ToolDispatcher(repository=repository, comparison_service=None)

        result = dispatcher.dispatch("compare_products", {
            "product_ids": ["SYN-01", "SYN-02"],
            "criterion": None,
        })

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["comparison_kind"], "educational_metadata_only")
        self.assertFalse(result["data"]["quantitative_ready"])
        self.assertFalse(result["data"]["hypothetical"])
        self.assertEqual([item["id"] for item in result["data"]["items"]], ["SYN-01", "SYN-02"])
        self.assertEqual([source["product_id"] for source in result["sources"]], ["SYN-01", "SYN-02"])
        self.assertEqual(repository.calls, [("get_product", "SYN-01"), ("get_product", "SYN-02")])


class SyntheticComparisonService:
    def __init__(self):
        self.calls = []
        self.result = {
            "status": "comparable",
            "quantitative_ready": True,
            "test_only": True,
            "not_for_publication": True,
            "items": [
                {"product_id": "SYN-01", "eligible": True, "value": "3.10", "source_refs": []},
                {"product_id": "SYN-02", "eligible": True, "value": "3.20", "source_refs": []},
            ],
        }

    def compare(self, products, criterion):
        self.calls.append((
            [product["id"] for product in products],
            criterion,
            [product["name"] for product in products],
        ))
        return __import__("copy").deepcopy(self.result)


class ToolDispatcherQuantitativeCompareTests(unittest.TestCase):
    def test_metric_comparison_uses_service_and_keeps_synthetic_evidence_scoped(self):
        repository = SyntheticRepository()
        comparison_service = SyntheticComparisonService()
        dispatcher = ToolDispatcher(repository, comparison_service)
        arguments = {
            "product_ids": ["SYN-01", "SYN-02"],
            "criterion": "deposit_tae_12m_eur",
        }
        original_arguments = __import__("copy").deepcopy(arguments)

        result = dispatcher.dispatch("compare_products", arguments)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["comparison_kind"], "test_only_quantitative")
        self.assertTrue(result["data"]["quantitative_ready"])
        self.assertTrue(result["data"]["hypothetical"])
        self.assertTrue(result["data"]["not_for_publication"])
        self.assertEqual(result["data"]["comparability"], comparison_service.result)
        self.assertEqual(comparison_service.calls, [(
            ["SYN-01", "SYN-02"],
            "deposit_tae_12m_eur",
            ["Synthetic candidate 1", "Synthetic candidate 2"],
        )])
        self.assertEqual(arguments, original_arguments)
        self.assertEqual(repository.products, repository.snapshot)


class ToolDispatcherScenarioTests(unittest.TestCase):
    def test_scenario_delegates_to_domain_motor_without_sources(self):
        from domain import calculate_scenario

        dispatcher = ToolDispatcher(repository=None, comparison_service=None)
        arguments = {
            "principal": "1000.00",
            "annual_rate_percent": "12.00",
            "years": 1,
            "monthly_contribution": "100.00",
            "method": "compound",
            "inflation_percent": "2.00",
        }

        result = dispatcher.dispatch("calculate_scenario", arguments)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"], calculate_scenario(arguments))
        self.assertEqual(result["data"]["summary"]["final_balance"], "2384.65")
        self.assertTrue(result["data"]["hypothetical"])
        self.assertTrue(result["data"]["not_prediction"])
        self.assertEqual(result["sources"], [])


class ToolDispatcherSourcesTests(unittest.TestCase):
    def test_get_sources_returns_repository_urls_with_local_identity_refs(self):
        repository = SyntheticRepository()
        dispatcher = ToolDispatcher(repository, comparison_service=None)

        result = dispatcher.dispatch("get_sources", {"product_ids": ["SYN-03", "SYN-01"]})

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"], {
            "count": 2,
            "scope": "product_identity_only",
            "not_for_publication": True,
        })
        self.assertEqual([source["product_id"] for source in result["sources"]], ["SYN-03", "SYN-01"])
        self.assertEqual([source["url"] for source in result["sources"]], [
            "https://example.invalid/synthetic/SYN-03",
            "https://example.invalid/synthetic/SYN-01",
        ])
        self.assertEqual([source["source_ref"]["id"] for source in result["sources"]], [
            "identity:SYN-03", "identity:SYN-01",
        ])
        self.assertTrue(all(source["source_ref"]["namespace"] == "local-tools.v1"
                            for source in result["sources"]))
        self.assertTrue(all(source["claim_scope"] == "product_identity_only"
                            for source in result["sources"]))
        self.assertEqual(repository.products, repository.snapshot)


class ToolDispatcherRepositoryBoundaryTests(unittest.TestCase):
    def test_invalid_repository_identity_is_a_stable_safe_error(self):
        repository = SyntheticRepository()
        repository.products[0]["identity_state"] = []
        dispatcher = ToolDispatcher(repository, comparison_service=None)

        result = dispatcher.dispatch("get_product_detail", {"product_id": "SYN-01"})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["code"], "REPOSITORY_ERROR")
        self.assertEqual(result["data"], {})
        self.assertEqual(result["sources"], [])
        self.assertNotIn("identity_state", result["error"]["message"])


class ToolDispatcherClosedValidationTests(unittest.TestCase):
    def assert_invalid(self, dispatcher, tool, arguments):
        result = dispatcher.dispatch(tool, arguments)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")
        self.assertEqual(result["data"], {})
        self.assertEqual(result["sources"], [])
        return result

    def test_unknown_tool_is_rejected_with_closed_envelope_without_read(self):
        repository = SyntheticRepository()
        dispatcher = ToolDispatcher(repository, comparison_service=None)

        result = dispatcher.dispatch("purchase_product", {"amount": "100.00"})

        self.assertEqual(set(result), {"schema_version", "tool", "status", "data", "sources", "error"})
        self.assertEqual(result["schema_version"], "local-tools.v1")
        self.assertIsNone(result["tool"])
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["code"], "UNKNOWN_TOOL")
        self.assertEqual(repository.calls, [])

    def test_search_rejects_open_fields_nulls_nan_booleans_and_limits_before_read(self):
        repository = SyntheticRepository()
        dispatcher = ToolDispatcher(repository, comparison_service=None)
        valid_shape = {"query": "SYN", "family": None, "limit": 1}
        invalid_arguments = [
            None,
            {},
            {**valid_shape, "url": "https://example.invalid"},
            {**valid_shape, "query": None},
            {**valid_shape, "query": "x" * 101},
            {**valid_shape, "family": "all"},
            {**valid_shape, "limit": 0},
            {**valid_shape, "limit": 21},
            {**valid_shape, "limit": True},
            {**valid_shape, "limit": float("nan")},
            {**valid_shape, "limit": 1.0},
        ]

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                self.assert_invalid(dispatcher, "search_products", arguments)
        self.assertEqual(repository.calls, [])

    def test_detail_rejects_non_local_ids_and_unknown_fields_before_read(self):
        repository = SyntheticRepository()
        dispatcher = ToolDispatcher(repository, comparison_service=None)
        invalid_arguments = [
            None,
            {},
            {"product_id": None},
            {"product_id": "syn-01"},
            {"product_id": "550e8400-e29b-41d4-a716-446655440000"},
            {"product_id": "SYN-01", "url": "https://example.invalid"},
        ]

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                self.assert_invalid(dispatcher, "get_product_detail", arguments)
        self.assertEqual(repository.calls, [])

    def test_compare_rejects_bad_criteria_ids_duplicates_and_bounds_before_read(self):
        repository = SyntheticRepository()
        comparison_service = SyntheticComparisonService()
        dispatcher = ToolDispatcher(repository, comparison_service)
        valid_shape = {"product_ids": ["SYN-01", "SYN-02"], "criterion": None}
        invalid_arguments = [
            None,
            {"product_ids": ["SYN-01", "SYN-02"]},
            {**valid_shape, "unexpected": True},
            {**valid_shape, "criterion": "arbitrary_metric"},
            {**valid_shape, "criterion": False},
            {**valid_shape, "product_ids": []},
            {**valid_shape, "product_ids": ["SYN-01"]},
            {**valid_shape, "product_ids": ["SYN-01"] * 5},
            {**valid_shape, "product_ids": ["SYN-01", "SYN-01"]},
            {**valid_shape, "product_ids": ["bad/id", "SYN-02"]},
            {**valid_shape, "product_ids": [None, "SYN-02"]},
        ]

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                self.assert_invalid(dispatcher, "compare_products", arguments)
        self.assertEqual(repository.calls, [])
        self.assertEqual(comparison_service.calls, [])

    def test_sources_rejects_empty_duplicate_malformed_or_unbounded_id_lists_before_read(self):
        repository = SyntheticRepository()
        dispatcher = ToolDispatcher(repository, comparison_service=None)
        invalid_arguments = [
            None,
            {},
            {"product_ids": []},
            {"product_ids": ["SYN-01", "SYN-01"]},
            {"product_ids": ["not/a/local-id"]},
            {"product_ids": ["SYN-01"], "url": "https://example.invalid"},
            {"product_ids": [f"SYN-{number:02d}" for number in range(1, 22)]},
        ]

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                self.assert_invalid(dispatcher, "get_sources", arguments)
        self.assertEqual(repository.calls, [])

    def test_calculation_rejects_non_decimal_non_finite_boolean_and_out_of_range_values(self):
        dispatcher = ToolDispatcher(repository=None, comparison_service=None)
        base = {
            "principal": "1000.00",
            "annual_rate_percent": "3.00",
            "years": 5,
            "monthly_contribution": "10.00",
            "method": "compound",
            "inflation_percent": "2.00",
        }
        invalid_arguments = [
            None,
            {key: value for key, value in base.items() if key != "method"},
            {**base, "extra": "not allowed"},
            {**base, "principal": None},
            {**base, "principal": 1.0},
            {**base, "principal": float("nan")},
            {**base, "principal": "NaN"},
            {**base, "principal": "1000000000.01"},
            {**base, "annual_rate_percent": "-100"},
            {**base, "annual_rate_percent": "1000.0001"},
            {**base, "years": True},
            {**base, "years": 0},
            {**base, "years": 41},
            {**base, "monthly_contribution": False},
            {**base, "method": "compound; SQL"},
            {**base, "inflation_percent": "Infinity"},
        ]

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                self.assert_invalid(dispatcher, "calculate_scenario", arguments)

    def test_zero_amounts_remain_valid_but_zero_years_and_zero_limit_do_not(self):
        dispatcher = ToolDispatcher(repository=None, comparison_service=None)
        result = dispatcher.dispatch("calculate_scenario", {
            "principal": "0",
            "annual_rate_percent": "0",
            "years": 1,
            "monthly_contribution": "0",
            "method": "compound",
            "inflation_percent": "0",
        })
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["summary"]["final_balance"], "0.00")


class ToolDispatcherBlockedComparabilityTests(unittest.TestCase):
    def test_blocked_synthetic_metric_stays_non_comparable_and_has_no_value(self):
        from datetime import timedelta

        from backend_services import CatalogueComparisonService
        from catalogue_facts import Fact, FreshnessPolicy

        repository = SyntheticRepository()
        product_ids = ("SYN-01", "SYN-02")
        facts = tuple(Fact(
            fact_id=f"test:{product_id}:tae",
            product_id=product_id,
            family="term_deposit",
            semantic_scope="term_deposit_tae",
            field_path="deposit.tae",
            value=value,
            unit="PERCENT",
            currency="EUR",
            period="12_months",
            effective_at="2026-10-01",
            effective_precision="date",
            validity_state="known",
            valid_from="2026-10-01",
            valid_to="2026-11-01",
            retrieved_at="2026-10-27T10:00:00+00:00",
            state="known",
            source_id="test.synthetic.source",
            source_revision_id="fixture-1",
            locator="fixture://test-only/tae",
            permissions_by_action={"app_display": "blocked"},
            evidence_class="synthetic_test",
        ) for product_id, value in zip(product_ids, ("3.10", "3.20")))
        policy = FreshnessPolicy(
            version="test-only-freshness-v1",
            family="term_deposit",
            semantic_scope="term_deposit_tae",
            field_path="deposit.tae",
            permission_action="app_display",
            max_retrieval_age=timedelta(days=1),
            max_effective_age=timedelta(days=90),
        )
        comparison_service = CatalogueComparisonService(
            facts=facts,
            policy=policy,
            allow_synthetic=True,
            clock=lambda: "2026-10-27T12:00:00+00:00",
        )
        dispatcher = ToolDispatcher(repository, comparison_service)

        result = dispatcher.dispatch("compare_products", {
            "product_ids": list(product_ids),
            "criterion": "deposit_tae_12m_eur",
        })

        comparability = result["data"]["comparability"]
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["data"]["quantitative_ready"])
        self.assertFalse(result["data"]["hypothetical"])
        self.assertTrue(comparability["test_only"])
        self.assertFalse(comparability["quantitative_ready"])
        self.assertTrue(all(item["value"] is None for item in comparability["items"]))
        self.assertTrue(all("RIGHTS_BLOCKED" in item["reason_codes"]
                            for item in comparability["items"]))


class ToolDispatcherRepositoryFailureTests(unittest.TestCase):
    def test_repository_exception_is_replaced_with_content_free_stable_error(self):
        class FailingRepository:
            def get_product(self, product_id):
                raise RuntimeError("PRIVATE repository detail")

        dispatcher = ToolDispatcher(FailingRepository(), comparison_service=None)

        result = dispatcher.dispatch("get_product_detail", {"product_id": "SYN-01"})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["code"], "REPOSITORY_ERROR")
        self.assertNotIn("PRIVATE", result["error"]["message"])


class ToolDispatcherRunnerContractTests(unittest.TestCase):
    def test_error_dto_is_accepted_by_runner_without_leaking_or_retrying(self):
        from pai_runtime import ToolChatRunner
        from providers import ChatResult, ToolCall

        class EmptyRepository:
            def get_product(self, product_id):
                return None

        class OneCallProvider:
            def __init__(self):
                self.calls = 0

            def chat(self, messages, tools=None):
                self.calls += 1
                return ChatResult("", None, (
                    ToolCall("call_missing", "get_product_detail", {"product_id": "SYN-99"}),
                ), "tool_calls")

        provider = OneCallProvider()
        dispatcher = ToolDispatcher(EmptyRepository(), comparison_service=None)

        result = ToolChatRunner(provider, dispatcher).run([
            {"role": "user", "content": "TEST ONLY: detalle local."},
        ])

        self.assertEqual(provider.calls, 1)
        self.assertEqual(result["tool_events"][0]["status"], "error")
        self.assertEqual(result["finish_reason"], "error")
        self.assertNotIn("PRODUCT_NOT_FOUND", str(result))
        self.assertNotIn("SYN-99", str(result))


if __name__ == "__main__":
    unittest.main()
