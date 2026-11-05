"""B4, ciclo 2: cierre de huecos de atribución, estado y texto no validado.

Casos sintéticos, sin red ni proveedores reales. Fijan el contrato de fallo cerrado:

- un error del servicio de condiciones no se convierte en catálogo sin condiciones;
- `documented` exige fuente atribuible, clase coherente y vigencia comprobable;
- una cita incoherente no publica clase `official` ni atribución `resolved`;
- los identificadores se validan literalmente (sin espacios ni guiones tipográficos);
- los tramos contradictorios no se muestran;
- si el turno consultó el catálogo, el texto libre del modelo no llega al usuario:
  la respuesta útil son los datos locales con clase, fechas y límites;
- el chat conceptual y la calculadora local conservan su texto con aviso de no validación.
"""

from __future__ import annotations

import copy
import http.client
import json
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))
sys.path.insert(0, str(TESTS_DIR))

from backend_services import CATALOGUE_WITHHELD_NOTE, LocalChatService, ServiceProblem
from catalogue_adapter import CatalogueWithConditions
from pai_runtime import ToolChatRunner
from pai_tools import ConditionsUnavailable, ToolDispatcher
from providers import ChatResult, ToolCall

from test_b4_condition_provenance import (
    CONSENT,
    OFFICIAL_URL,
    PRESS_URL,
    PRODUCTS,
    SyntheticConditionsService,
    SyntheticRepository,
    catalog_item,
    condition,
    expanded_products,
    make_gate,
    product_of,
)
from test_backend_integration import request, running_server
from test_functional05_http import TestOnlyFakeProvider


class BrokenConditionsService:
    """Servicio que falla: nunca debe leerse como 'sin condiciones'."""

    def __init__(self):
        self.calls = 0

    def describe(self):
        self.calls += 1
        raise RuntimeError("PRIVATE CONDITIONS detail")

    def catalogue_extras(self, q=None, family=None):
        self.calls += 1
        raise RuntimeError("PRIVATE CONDITIONS detail")


def dispatcher_for(products=None, service=None, repository=None):
    repository = repository or SyntheticRepository(products)
    service = service or SyntheticConditionsService(products)
    return ToolDispatcher(CatalogueWithConditions(repository, service), comparison_service=None)


def detail(dispatcher, product_id="DEP-KNOWN"):
    return dispatcher.dispatch("get_product_detail", {"product_id": product_id})


class ConditionsFailureTests(unittest.TestCase):
    def test_conditions_service_error_is_never_reported_as_an_empty_catalogue(self):
        broken = BrokenConditionsService()
        dispatcher = ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository(), broken), comparison_service=None)

        result = detail(dispatcher)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["code"], "CONDITIONS_UNAVAILABLE")
        self.assertNotIn("PRIVATE", json.dumps(result))
        self.assertGreaterEqual(broken.calls, 1)

    def test_adapter_errors_are_not_swallowed_into_an_empty_list(self):
        adapter = CatalogueWithConditions(SyntheticRepository(), BrokenConditionsService())

        with self.assertRaises(ConditionsUnavailable):
            adapter.list_products()

    def test_search_also_fails_closed_when_conditions_are_unavailable(self):
        dispatcher = ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository(), BrokenConditionsService()),
            comparison_service=None)

        result = dispatcher.dispatch("search_products", {
            "query": "Depósito", "family": "deposito", "limit": 5,
        })

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["code"], "CONDITIONS_UNAVAILABLE")


class DocumentedStateTests(unittest.TestCase):
    def raw(self, conditions, *, reference="2026-11-04", **overrides):
        product = catalog_item(PRODUCTS[0])
        product["conditions"] = conditions
        product["conditions_reference_date"] = reference
        product.update(overrides)
        return product

    def test_known_condition_expired_at_reference_is_not_documented(self):
        product = self.raw([condition(value="3.10", effective_to="2026-10-31")])
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        result = detail(dispatcher)
        projected = product_of(result)

        self.assertEqual(projected["conditions"][0]["state"], "stale")
        self.assertEqual(projected["conditions_state"], "documented_not_current")
        self.assertNotEqual(projected["conditions_state"], "documented")
        self.assertTrue(any("vigencia" in note.lower()
                            for note in projected["conditions"][0]["limitations"]))

    def test_known_condition_with_internal_unresolved_source_is_not_documented(self):
        product = self.raw([condition(source_ids=["ACC-01"], reason="DOCUMENTED_RATE",
                                      effective_from=None, effective_to=None)])
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        projected = product_of(detail(dispatcher))

        self.assertEqual(projected["conditions"][0]["source_resolution"], "unresolved")
        self.assertEqual(projected["conditions_state"], "documented_unattributed")
        self.assertNotEqual(projected["conditions_state"], "documented")
        self.assertEqual(projected["attribution_state"], "unresolved")

    def test_known_condition_without_citation_is_not_documented(self):
        product = self.raw([condition(source_ids=[], reason="DOCUMENTED_RATE",
                                      effective_from=None, effective_to=None)])
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        projected = product_of(detail(dispatcher))

        self.assertEqual(projected["conditions_state"], "documented_unattributed")
        self.assertNotEqual(projected["conditions_state"], "documented")
        self.assertTrue(any("sin fuente citada" in note.lower()
                            for note in projected["conditions"][0]["limitations"]))

    def test_missing_reference_date_prevents_documented_claim(self):
        product = self.raw([condition()])
        product.pop("conditions_reference_date")
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        projected = product_of(detail(dispatcher))

        self.assertNotEqual(projected["conditions_state"], "documented")
        self.assertEqual(projected["conditions_state"], "documented_unattributed")
        self.assertTrue(any("fecha de referencia" in note.lower()
                            for note in projected["conditions"][0]["limitations"]))

    def test_secondary_source_remains_documented_but_secondary(self):
        result = detail(dispatcher_for(), "DEP-PRESS")
        projected = product_of(result)

        self.assertEqual(projected["conditions"][0]["source_class"], "secondary")
        self.assertEqual(projected["conditions_state"], "documented")
        self.assertEqual(projected["attribution_state"], "resolved")
        claimed = [source for source in result["sources"]
                   if source["claim_scope"] == "condition_documentation_only"]
        self.assertEqual(claimed[0]["source_class"], "secondary")


class InconsistentClassTests(unittest.TestCase):
    def raw(self, conditions, **overrides):
        product = catalog_item(PRODUCTS[0])
        product["conditions"] = conditions
        product["conditions_reference_date"] = "2026-11-04"
        product.update(overrides)
        return product

    def test_class_conflict_never_publishes_official_citation_or_resolved_attribution(self):
        product = self.raw(
            [condition(source_ids=[OFFICIAL_URL], reason="CURATED_SECONDARY_PRESS")],
            source={"url": OFFICIAL_URL, "kind": "official", "retrieved_at": "2026-11-03"})
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        result = detail(dispatcher)
        projected = product_of(result)["conditions"][0]

        self.assertEqual(projected["source_class"], "unknown")
        self.assertEqual(projected["sources"], [])
        self.assertEqual(product_of(result)["attribution_state"], "inconsistent")
        condition_sources = [source for source in result["sources"]
                             if source["claim_scope"] == "condition_documentation_only"]
        self.assertEqual(condition_sources, [])
        self.assertNotIn('"class": "official"', json.dumps(result))

    def test_registry_id_without_url_is_not_declared_official(self):
        product = self.raw(
            [condition(source_ids=["s1"], reason="CURATED_OFFICIAL")],
            sources=[{"id": "s1", "kind": "official", "retrieved_at": "2026-11-03"}],
            source=None)
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        projected = product_of(detail(dispatcher))["conditions"][0]

        self.assertEqual(projected["source_class"], "unknown")
        self.assertNotEqual(projected["source_class"], "official")
        self.assertEqual(projected["sources"], [])
        self.assertEqual(product_of(detail(dispatcher))["conditions_state"],
                         "documented_unattributed")

    def test_identity_source_exposes_its_date_when_the_product_has_one(self):
        result = detail(dispatcher_for())
        identity = [source for source in result["sources"]
                    if source["claim_scope"] == "product_identity_only"]
        self.assertEqual(identity[0]["retrieved_at"], "2026-11-03")
        self.assertEqual(identity[0]["date_state"], "documented")

    def test_identity_source_without_date_declares_unknown_date(self):
        product = catalog_item(PRODUCTS[0])
        product["as_of"] = None
        product["conditions_reference_date"] = "2026-11-04"
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        result = detail(dispatcher)
        identity = [source for source in result["sources"]
                    if source["claim_scope"] == "product_identity_only"]
        self.assertIsNone(identity[0]["retrieved_at"])
        self.assertEqual(identity[0]["date_state"], "unknown")


class RateTierCoherenceTests(unittest.TestCase):
    def raw_with_tiers(self, tiers):
        product = catalog_item(PRODUCTS[0])
        product["conditions"] = [condition()]
        product["conditions_reference_date"] = "2026-11-04"
        product["rate_tiers"] = tiers
        return product

    def test_tae_lower_than_tin_is_not_shown_as_a_valid_tier(self):
        product = self.raw_with_tiers([
            {"condition": "sin_requisito", "condition_label": "Sin requisito",
             "tae": "2.00", "tin": "3.00"},
        ])
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        result = detail(dispatcher)
        projected = product_of(result)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(projected["rate_tiers"], [])
        self.assertEqual(projected["rate_tiers_state"], "inconsistent")
        self.assertTrue(projected["rate_tiers_limitations"])
        self.assertNotIn("2.00", json.dumps(projected["rate_tiers"]))

    def test_duplicate_tier_conditions_are_inconsistent(self):
        product = self.raw_with_tiers([
            {"condition": "nomina_900", "condition_label": "Con nómina", "tae": "3.10", "tin": "3.05"},
            {"condition": "nomina_900", "condition_label": "Con nómina (bis)", "tae": "3.20", "tin": "3.15"},
        ])
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        projected = product_of(detail(dispatcher))

        self.assertEqual(projected["rate_tiers"], [])
        self.assertEqual(projected["rate_tiers_state"], "inconsistent")

    def test_out_of_range_rate_is_rejected(self):
        product = self.raw_with_tiers([
            {"condition": "sin_requisito", "condition_label": "Sin requisito",
             "tae": "1001", "tin": None},
        ])
        dispatcher = ToolDispatcher(SingleProductRepository(product), comparison_service=None)

        projected = product_of(detail(dispatcher))

        self.assertEqual(projected["rate_tiers"], [])
        self.assertIn(projected["rate_tiers_state"], {"invalid", "inconsistent"})


class LiteralIdentifierTests(unittest.TestCase):
    def spy(self):
        class SpyRepository:
            def __init__(self):
                self.calls = []

            def get_product(self, product_id):
                self.calls.append(product_id)
                return None

            def list_products(self, q=None, family=None):
                self.calls.append((q, family))
                return []

        return SpyRepository()

    def test_tool_rejects_padded_and_typographic_identifiers_before_lookup(self):
        for value in (" ACC-01", "ACC-01 ", "ACC\u201101", "ACC-01\n", "acc-01", "ACC-01\u00a0"):
            with self.subTest(value=repr(value)):
                repository = self.spy()
                dispatcher = ToolDispatcher(repository, comparison_service=None)

                result = dispatcher.dispatch("get_product_detail", {"product_id": value})

                self.assertEqual(result["status"], "error")
                self.assertEqual(result["error"]["code"], "INVALID_ARGUMENTS")
                self.assertEqual(repository.calls, [])

    def test_runtime_rejects_typographic_and_padded_identifiers_before_dispatch(self):
        class RecordingDispatcher:
            test_only = True

            def __init__(self):
                self.calls = []

            def definitions(self):
                return ToolDispatcher(None, None).definitions()

            def dispatch(self, name, arguments):
                self.calls.append((name, arguments))
                raise AssertionError("must not dispatch")

        for call in (
            ToolCall("call_padded", "get_product_detail", {"product_id": " ACC-01"}),
            ToolCall("call_dash", "get_product_detail", {"product_id": "ACC\u201101"}),
            ToolCall("call_compare", "compare_products", {
                "product_ids": ["ACC-01", "ACC\u201102"], "criterion": None}),
        ):
            with self.subTest(call=call.name):
                dispatcher = RecordingDispatcher()
                provider = TestOnlyFakeProvider([ChatResult("", None, (call,), "tool_calls")])

                result = ToolChatRunner(provider, dispatcher).run([
                    {"role": "user", "content": "TEST ONLY: consulta literal."},
                ])

                self.assertEqual(dispatcher.calls, [])
                self.assertEqual(result["finish_reason"], "tool_error")
                self.assertEqual(result["answer"], "")


class WithheldCatalogueAnswerTests(unittest.TestCase):
    def provider(self, answer, tool, arguments, *, call_id="call_detail"):
        return TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall(call_id, tool, arguments),), "tool_calls"),
            ChatResult(answer, None, (), "stop"),
        ])

    def test_catalogue_turn_withholds_unverified_text_and_exposes_local_evidence(self):
        unsafe = "TEST ONLY: la TAE vigente es 9,99 % y la fuente es oficial."
        dispatcher = dispatcher_for()
        provider = self.provider(unsafe, "get_product_detail", {"product_id": "DEP-KNOWN"})

        result = ToolChatRunner(provider, dispatcher).run([
            {"role": "user", "content": "TEST ONLY: detalla el depósito."},
        ])

        self.assertEqual(result["answer"], "")
        self.assertEqual(result["answer_text_state"], "withheld_catalogue_evidence")
        self.assertNotIn("9,99", json.dumps(result))
        self.assertTrue(result["catalogue"]["used"])
        product = result["catalogue"]["products"][0]
        self.assertEqual(product["id"], "DEP-KNOWN")
        self.assertEqual(product["conditions_state"], "documented")
        entry = product["conditions"][0]
        self.assertEqual(entry["state"], "known")
        self.assertEqual(entry["value"], "3.10")
        self.assertEqual(entry["source_class"], "official")
        self.assertEqual(entry["retrieved_at"], "2026-11-03")
        self.assertEqual(entry["effective_from"], "2026-11-01")
        self.assertEqual(entry["effective_to"], "2026-12-01")
        self.assertTrue(any("texto del modelo" in note.lower()
                            for note in result["limitations"]))

    def test_search_turn_withholds_text_and_keeps_unknown_states_visible(self):
        unsafe = "TEST ONLY: todos tienen una TAE oficial vigente del 5 %."
        dispatcher = dispatcher_for()
        provider = self.provider(unsafe, "search_products", {
            "query": "Depósito", "family": "deposito", "limit": 5,
        })

        result = ToolChatRunner(provider, dispatcher).run([
            {"role": "user", "content": "TEST ONLY: busca depósitos."},
        ])

        self.assertEqual(result["answer"], "")
        self.assertNotIn("5 %", json.dumps(result))
        products = {item["id"]: item for item in result["catalogue"]["products"]}
        self.assertEqual(products["DEP-UNKNOWN"]["conditions_state"], "conditions_unknown")
        self.assertEqual(products["DEP-UNKNOWN"]["attribution_state"], "none")

    def test_conceptual_turn_keeps_text_with_explicit_validation_limit(self):
        unsafe = "TEST ONLY: explicación conceptual sin datos de catálogo."
        provider = TestOnlyFakeProvider([ChatResult(unsafe, None, (), "stop")])

        result = ToolChatRunner(provider, dispatcher_for()).run([
            {"role": "user", "content": "TEST ONLY: ¿qué es la inflación?"},
        ])

        self.assertEqual(result["answer"], unsafe)
        self.assertEqual(result["answer_text_state"], "shown_unverified")
        self.assertFalse(result["catalogue"]["used"])
        self.assertTrue(any("no se valida semánticamente" in note
                            for note in result["limitations"]))

    def test_calculator_turn_keeps_text_because_it_does_not_read_the_catalogue(self):
        answer = "TEST ONLY: el cálculo es hipotético."
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("call_calc", "calculate_scenario", {
                "principal": "1000.00", "annual_rate_percent": "3.00", "years": 1,
                "monthly_contribution": "0.00", "method": "compound",
                "inflation_percent": "2.00",
            }),), "tool_calls"),
            ChatResult(answer, None, (), "stop"),
        ])

        result = ToolChatRunner(provider, dispatcher_for()).run([
            {"role": "user", "content": "TEST ONLY: calcula."},
        ])

        self.assertEqual(result["answer"], answer)
        self.assertEqual(result["answer_text_state"], "shown_unverified")
        self.assertFalse(result["catalogue"]["used"])


class ServiceAndHttpProvenanceTests(unittest.TestCase):
    def service(self, provider, *, dispatcher=None, gate=None):
        return LocalChatService(
            provider=provider, enabled=True, test_only=True,
            dispatcher=dispatcher if dispatcher is not None else dispatcher_for(),
            tools_enabled=True,
            admission=gate if gate is not None else make_gate(),
            catalogue_usage_approved=True,
        )

    def test_conceptual_claim_of_official_or_current_rate_is_withheld(self):
        unsafe = "TEST ONLY: la TAE vigente es 9,99 % según la fuente oficial."
        provider = TestOnlyFakeProvider([ChatResult(unsafe, None, (), "stop")])

        body = self.service(provider).chat({
            "message": "TEST ONLY: ¿qué tasa hay?", "consent": CONSENT,
        })

        self.assertEqual(body["answer"], "")
        self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
        self.assertNotIn("9,99", json.dumps(body))
        self.assertTrue(any("sin datos locales" in note.lower()
                            for note in body["answer_provenance"]["limitations"]))

    def test_conceptual_definition_without_attribution_keeps_its_text(self):
        answer = "TEST ONLY: la TAE resume el coste anual efectivo de un producto."
        provider = TestOnlyFakeProvider([ChatResult(answer, None, (), "stop")])

        body = self.service(provider).chat({
            "message": "TEST ONLY: explícame la TAE.", "consent": CONSENT,
        })

        self.assertEqual(body["answer"], answer)
        self.assertEqual(body["answer_text_state"], "shown_unverified")

    def test_service_response_carries_withheld_state_and_local_facts(self):
        unsafe = "TEST ONLY: tasa vigente 9,99 % de fuente oficial."
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("call_detail", "get_product_detail",
                                           {"product_id": "DEP-PRESS"}),), "tool_calls"),
            ChatResult(unsafe, None, (), "stop"),
        ])

        body = self.service(provider).chat({
            "message": "TEST ONLY: detalla DEP-PRESS.", "consent": CONSENT,
        })

        self.assertEqual(body["answer"], CATALOGUE_WITHHELD_NOTE)
        self.assertNotIn("TEST ONLY", body["answer"])
        self.assertNotIn("9,99", json.dumps(body))
        self.assertEqual(body["answer_text_state"], "withheld_catalogue_evidence")
        self.assertEqual(body["answer_provenance"]["text_state"], "withheld_catalogue_evidence")
        self.assertEqual(body["answer_provenance"]["text_validation"], "not_performed")
        product = body["catalogue"]["products"][0]
        condition = product["conditions"][0]
        self.assertEqual(condition["source_class"], "secondary")
        self.assertEqual(condition["retrieved_at"], "2026-11-03")
        self.assertEqual(condition["effective_to"], "2026-12-01")
        claimed = [source for source in body["sources"]
                   if source["source"]["claim_scope"] == "condition_documentation_only"]
        self.assertEqual(claimed[0]["source"]["source_class"], "secondary")

    def test_http_chat_withholds_unsafe_text_and_shows_class_and_dates(self):
        unsafe = "TEST ONLY: la TAE vigente es 9,99 % y la fuente es oficial."
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("call_detail", "get_product_detail",
                                           {"product_id": "DEP-KNOWN"}),), "tool_calls"),
            ChatResult(unsafe, None, (), "stop"),
        ])

        with running_server(chat_service=self.service(provider)) as server:
            status, body = request(server, "/api/chat", {
                "message": "TEST ONLY: detalla DEP-KNOWN.", "consent": CONSENT})

        self.assertEqual(body["answer"], CATALOGUE_WITHHELD_NOTE)
        self.assertNotIn("TEST ONLY", body["answer"])
        self.assertNotIn("9,99", json.dumps(body))
        self.assertEqual(body["answer_text_state"], "withheld_catalogue_evidence")
        condition = body["catalogue"]["products"][0]["conditions"][0]
        self.assertEqual(condition["source_class"], "official")
        self.assertEqual(condition["retrieved_at"], "2026-11-03")
        self.assertEqual(condition["effective_from"], "2026-11-01")
        self.assertEqual(condition["effective_to"], "2026-12-01")
        self.assertTrue(body["answer_provenance"]["limitations"])
        self.assertFalse(body["external_sent"])

    def test_http_conditions_failure_returns_502_without_empty_catalogue_claims(self):
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("call_detail", "get_product_detail",
                                           {"product_id": "DEP-KNOWN"}),), "tool_calls"),
        ])
        broken_dispatcher = ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository(), BrokenConditionsService()),
            comparison_service=None)

        with running_server(chat_service=self.service(provider, dispatcher=broken_dispatcher)) as server:
            status, body = request(server, "/api/chat", {
                "message": "TEST ONLY: detalla DEP-KNOWN.", "consent": CONSENT})

        self.assertEqual(status, 502)
        self.assertEqual(body["error"]["code"], "CHAT_TOOL_ERROR")
        self.assertNotIn("PRIVATE", json.dumps(body))
        self.assertNotIn("catalogue", body)


class SingleProductRepository:
    def __init__(self, product):
        self.product = product

    def get_product(self, product_id):
        return copy.deepcopy(self.product) if product_id == self.product["id"] else None

    def list_products(self, q=None, family=None):
        return [copy.deepcopy(self.product)]


if __name__ == "__main__":
    unittest.main()
