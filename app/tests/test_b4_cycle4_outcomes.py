"""B4, ciclo 4: resultado real del motor y límites verificables.

Estos casos fijan el resultado que ve la persona, no solo la forma del DTO:

- en un turno de calculadora, la prosa del modelo con cualquier cifra o
  atribución no se publica: no se coteja literalmente contra el motor porque
  una cifra correcta puede quedar atribuida al concepto equivocado (principal
  presentado como interés, signo invertido, etc.);
- el cliente recibe el resultado y los supuestos del motor local en un DTO
  acotado, sin la serie mensual y con la declaración de hipótesis;
- una condición con métrica y unidad incoherentes, o con estado `unknown` y un
  valor, se rechaza o degrada de forma declarada; nunca se muestra como
  documentada;
- la proyección al modelo tiene un tope por ruta y el tope agregado de fuentes
  declara cuántas se omitieron, sin pérdida silenciosa.

Casos sintéticos, sin red externa ni proveedores reales.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))
sys.path.insert(0, str(TESTS_DIR))

from backend_services import LocalChatService
from catalogue_adapter import CatalogueWithConditions
from domain import calculate_scenario
from pai_runtime import ToolChatRunner
from pai_tools import ToolDispatcher
from providers import ChatResult, ToolCall

from test_b4_condition_provenance import (
    CONSENT,
    OFFICIAL_URL,
    PRODUCTS,
    SyntheticConditionsService,
    SyntheticRepository,
    catalog_item,
    condition,
    expanded_products,
)
from test_backend_integration import request, running_server
from test_b4_cycle3_boundary import review_product, review_repository, service_for
from test_functional05_http import TestOnlyFakeProvider


CALC_ARGS = {
    "principal": "1000.00", "annual_rate_percent": "3.00", "years": 2,
    "monthly_contribution": "0.00", "method": "compound",
    "inflation_percent": "2.00",
}
LOCAL = calculate_scenario(dict(CALC_ARGS))
CALC_TEXT = "TEST ONLY: calcula un escenario hipotético."


def chat_http(service, message=CALC_TEXT):
    with running_server(chat_service=service) as server:
        return request(server, "/api/chat", {"message": message, "consent": CONSENT})


def calculator_service(answer):
    service, provider = service_for([
        ChatResult("", None, (ToolCall("calc1", "calculate_scenario", dict(CALC_ARGS)),), "tool_calls"),
        ChatResult(answer, None, (), "stop"),
    ])
    return service, provider


class CalculatorEngineOutcomeTests(unittest.TestCase):
    """B4-C4-01: el motor local sustituye a la prosa numérica no verificada."""

    UNSAFE_PROSE = (
        # Intercambio principal/interés y saldo/interés: cifras reales del motor,
        # concepto equivocado. La coincidencia literal no puede avalarlas.
        "El interés obtenido es 1.000,00 euros.",
        "El interés obtenido es 1.060,90 euros.",
        "El saldo final es 1.000,00 euros.",
        "Las aportaciones son 1.060,90 euros.",
        "El saldo final es 2 euros.",
        "El interés es 3.00 euros.",
        "El interés es -1.000,00 euros.",
        # Prosa maliciosa: cifra correcta acompañada de una atribución falsa.
        "El interés real es 60,90 euros y el banco lo confirma.",
        "El interés es 60,90 euros y está garantizado por el banco.",
        "La TAE es 99 % y el saldo 1060.90, según la fuente oficial.",
        "Este producto ofrece un interés de 1.000,00 euros.",
        "Según el folleto, el saldo final es 1.060,90 euros.",
        # Otras superficies de la misma frontera.
        "TEST ONLY: el motor devuelve 1030.00 EUR nominales.",
        "TEST ONLY: el saldo final es 1.030,00 €.",
        # Cifra escrita con palabras: no lleva dígito, pero sigue siendo una cifra.
        "El interés obtenido es mil euros.",
        "El interés es dos mil euros.",
        "Obtendrás treinta euros de interés.",
    )

    def test_engine_result_and_assumptions_reach_the_client(self):
        service, provider = calculator_service("El interés obtenido es 1.000,00 euros.")

        status, body = chat_http(service)

        self.assertEqual(status, 200, body)
        self.assertEqual(len(provider.requests), 2, "no debe haber reintento")
        self.assertEqual(body["answer"], "")
        self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
        self.assertEqual(body["answer_provenance"]["withheld_reason"], "calculation")
        calculation = body.get("calculation")
        self.assertIsInstance(calculation, dict, body)
        self.assertEqual(calculation["summary"], LOCAL["summary"])
        self.assertEqual(calculation["assumptions"]["principal"], "1000.00")
        self.assertEqual(calculation["assumptions"]["annual_rate_percent"], "3")
        self.assertEqual(calculation["assumptions"]["years"], 2)
        self.assertEqual(calculation["assumptions"]["method"], "compound")
        self.assertEqual(calculation["assumptions"]["monthly_contribution"], "0.00")
        self.assertEqual(calculation["assumptions"]["inflation_percent"], "2")
        self.assertIs(calculation["hypothetical"], True)
        self.assertIs(calculation["not_prediction"], True)
        self.assertEqual(calculation["currency"], "EUR")
        self.assertNotIn("series", calculation)
        self.assertLess(len(json.dumps(body, ensure_ascii=False).encode("utf-8")), 8192)
        self.assertTrue(any("motor" in note.lower() and "local" in note.lower()
                            for note in body["answer_provenance"]["limitations"]))
        self.assertEqual(body["answer_provenance"]["text_validation"], "not_performed")

    def test_model_prose_with_numbers_or_attributions_is_never_shown(self):
        for text in self.UNSAFE_PROSE:
            with self.subTest(text=text):
                service, provider = calculator_service(text)

                status, body = chat_http(service)

                self.assertEqual(status, 200, body)
                self.assertEqual(body["answer"], "", text)
                self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim", text)
                raw = json.dumps(body, ensure_ascii=False)
                self.assertNotIn(text, raw)
                self.assertNotIn("1.000,00 euros", raw)
                self.assertEqual(body["answer_provenance"]["text_state"],
                                 "withheld_unbacked_claim")
                self.assertIsInstance(body.get("calculation"), dict)
                self.assertEqual(body["calculation"]["summary"], LOCAL["summary"])
                self.assertEqual(len(provider.requests), 2)

    def test_concept_only_prose_survives_in_calculator_turns(self):
        answer = "TEST ONLY: el cálculo es hipotético y lo hace el motor local."
        service, provider = calculator_service(answer)

        status, body = chat_http(service)

        self.assertEqual(status, 200, body)
        self.assertEqual(body["answer"], answer)
        self.assertEqual(body["answer_text_state"], "shown_unverified")
        self.assertEqual(body["calculation"]["summary"], LOCAL["summary"])

    def test_no_tool_concept_prose_is_untouched(self):
        text = "TEST ONLY: la TAE resume el coste anual efectivo de un producto."
        service, provider = service_for([ChatResult(text, None, (), "stop")])

        status, body = chat_http(service)

        self.assertEqual(status, 200, body)
        self.assertEqual(body["answer"], text)
        self.assertEqual(body["answer_text_state"], "shown_unverified")
        self.assertIsNone(body.get("calculation"))


class ConditionShapeDefectTests(unittest.TestCase):
    """B4-C4-02: métrica/unidad y valor con estado `unknown` no son documentables."""

    BAD_CONDITIONS = (
        {"metric": "annual_rate_percent", "unit": "MONTHS"},
        {"metric": "term_months", "unit": "PERCENT"},
    )

    def dispatcher_for(self, conditions):
        product = {**PRODUCTS[0], "conditions": conditions}
        return ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository([product]),
                                    SyntheticConditionsService([product])),
            comparison_service=None)

    def test_metric_unit_mismatch_is_rejected_by_the_tool(self):
        for overrides in self.BAD_CONDITIONS:
            with self.subTest(condition=overrides):
                bad = {**condition(source_ids=[OFFICIAL_URL]), **overrides}
                result = self.dispatcher_for([bad]).dispatch(
                    "get_product_detail", {"product_id": "DEP-KNOWN"})

                self.assertEqual(result["status"], "error", result)
                self.assertEqual(result["error"]["code"], "REPOSITORY_ERROR")
                self.assertEqual(result["data"], {})

    def test_unknown_state_with_a_value_is_rejected_by_the_tool(self):
        bad = {**condition(state="unknown", value="3.10", reason="RATE_NOT_DOCUMENTED"),
               "source_ids": []}
        result = self.dispatcher_for([bad]).dispatch(
            "get_product_detail", {"product_id": "DEP-KNOWN"})

        self.assertEqual(result["status"], "error", result)
        self.assertEqual(result["error"]["code"], "REPOSITORY_ERROR")

    def test_metric_unit_mismatch_turns_the_http_turn_into_a_declared_error(self):
        bad = {**condition(source_ids=[OFFICIAL_URL]), "unit": "MONTHS"}
        dispatcher = self.dispatcher_for([bad])
        service, provider = service_for([
            ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                           {"product_id": "DEP-KNOWN"}),), "tool_calls"),
        ], dispatcher=dispatcher)

        status, body = chat_http(service)

        self.assertEqual(status, 502, body)
        self.assertEqual(body["error"]["code"], "CHAT_TOOL_ERROR")
        self.assertNotIn("catalogue", body)

    def test_runtime_projection_never_publishes_incoherent_conditions(self):
        cases = (
            {**condition(source_ids=[OFFICIAL_URL]), "unit": "MONTHS"},
            {**condition(state="unknown", value="3.10", reason="RATE_NOT_DOCUMENTED"),
             "source_ids": []},
        )
        for bad in cases:
            with self.subTest(condition=bad):
                product = catalog_item(PRODUCTS[0])
                product.update(conditions=[bad], conditions_state="documented",
                               conditions_reference_date="2026-11-04")
                provider = TestOnlyFakeProvider([
                    ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                                   {"product_id": "DEP-KNOWN"}),), "tool_calls"),
                    ChatResult("TEST ONLY: sin datos locales.", None, (), "stop"),
                ])
                result = ToolChatRunner(provider, StaticProductDispatcher(product)).run([
                    {"role": "user", "content": "TEST ONLY: detalle."},
                ])

                projected = result["catalogue"]["products"][0]
                self.assertEqual(projected["conditions_state"], "conditions_unknown", projected)
                self.assertEqual(projected["conditions_record_state"], "invalid")
                self.assertEqual(projected["conditions"], [])
                self.assertNotEqual(projected["conditions_state"], "documented")


class StaticProductDispatcher:
    """Dispatcher de prueba con un producto fijo; no lee el catálogo real."""

    def __init__(self, product):
        self.product = product

    def definitions(self):
        return ToolDispatcher(None, None).definitions()

    def dispatch(self, name, arguments):
        return {
            "schema_version": "local-tools.v1", "tool": name, "status": "ok",
            "data": {"product": copy.deepcopy(self.product),
                     "not_for_publication": True},
            "sources": [], "error": None,
        }


class StaticItemsDispatcher:
    def __init__(self, items):
        self.items = items

    def definitions(self):
        return ToolDispatcher(None, None).definitions()

    def dispatch(self, name, arguments):
        return {
            "schema_version": "local-tools.v1", "tool": name, "status": "ok",
            "data": {"items": copy.deepcopy(self.items), "count": len(self.items),
                     "limit": 20, "not_for_publication": True},
            "sources": [], "error": None,
        }


class ModelProjectionSizeTests(unittest.TestCase):
    """B4-C4-03: ninguna ruta puede enviar al modelo un resultado sin tope."""

    MAX_MODEL_BYTES = 32768

    def run_turn(self, dispatcher, call):
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (call,), "tool_calls"),
            ChatResult("TEST ONLY: prosa retenida.", None, (), "stop"),
        ])
        ToolChatRunner(provider, dispatcher).run([
            {"role": "user", "content": "TEST ONLY: consulta."},
        ])
        tool_message = provider.requests[1][-1]
        return tool_message["content"], json.loads(tool_message["content"])

    def test_detail_with_a_huge_conflict_is_bounded_and_declared(self):
        product = catalog_item(PRODUCTS[0])
        product.update(conflicts=["CONFLICTO " + ("X" * 100_000)],
                       unknown_fields=["campo " + ("Y" * 50_000)],
                       conditions_state="documented",
                       conditions_reference_date="2026-11-04")
        dispatcher = StaticProductDispatcher(product)

        raw, payload = self.run_turn(dispatcher, ToolCall(
            "c1", "get_product_detail", {"product_id": "DEP-KNOWN"}))

        self.assertLess(len(raw.encode("utf-8")), self.MAX_MODEL_BYTES, len(raw))
        self.assertNotIn("X" * 5000, raw)
        self.assertNotIn("Y" * 5000, raw)
        data = payload["untrusted_tool_result"]["data"]
        product_data = data["product"]
        self.assertEqual(product_data["conflicts_count"], 1)
        self.assertEqual(product_data["unknown_fields_count"], 1)
        self.assertLessEqual(len(product_data["conflicts"][0]), 200)
        self.assertLessEqual(len(product_data["unknown_fields"][0]), 120)

    def test_search_with_a_huge_name_is_bounded(self):
        item = catalog_item(PRODUCTS[0])
        item.update(name="PRODUCTO " + ("Z" * 100_000))
        dispatcher = StaticItemsDispatcher([item])

        raw, payload = self.run_turn(dispatcher, ToolCall(
            "s1", "search_products", {"query": "Producto", "family": "deposito", "limit": 5}))

        self.assertLess(len(raw.encode("utf-8")), self.MAX_MODEL_BYTES, len(raw))
        self.assertNotIn("Z" * 5000, raw)
        model_item = payload["untrusted_tool_result"]["data"]["items"][0]
        self.assertLessEqual(len(model_item["name"]), 200)


    def test_compare_and_sources_routes_are_bounded_too(self):
        item = catalog_item(PRODUCTS[0])
        item.update(name="COMPARA " + ("Q" * 100_000),
                    conflicts=["conflicto " + ("W" * 100_000)],
                    unknown_fields=["campo " + ("V" * 100_000)])
        compare_dispatcher = StaticItemsDispatcher([item, item])
        raw, payload = self.run_turn(compare_dispatcher, ToolCall(
            "cmp1", "compare_products",
            {"product_ids": ["DEP-KNOWN", "DEP-REVIEW"], "criterion": None}))
        self.assertLess(len(raw.encode("utf-8")), self.MAX_MODEL_BYTES, len(raw))
        self.assertNotIn("Q" * 5000, raw)
        compare_data = payload["untrusted_tool_result"]["data"]
        self.assertEqual(compare_data["comparison_kind"], None)
        self.assertTrue(compare_data["items"] or compare_data["items"] == [])

        class HugeSourcesDispatcher:
            def definitions(self):
                return ToolDispatcher(None, None).definitions()

            def dispatch(self, name, arguments):
                return {
                    "schema_version": "local-tools.v1", "tool": name, "status": "ok",
                    "data": {"count": 20, "scope": "product_identity_only" * 10_000,
                             "not_for_publication": True},
                    "sources": [{"source_ref": {"id": "identity:" + ("S" * 100_000)},
                                 "kind": "identity", "claim_scope": "product_identity_only",
                                 "label": "L" * 100_000, "url": "https://example.invalid/x"}
                                for _ in range(20)],
                    "error": None,
                }

        raw, payload = self.run_turn(HugeSourcesDispatcher(), ToolCall(
            "src1", "get_sources", {"product_ids": ["DEP-KNOWN"]}))
        self.assertLess(len(raw.encode("utf-8")), self.MAX_MODEL_BYTES, len(raw))
        self.assertNotIn("S" * 5000, raw)
        self.assertLessEqual(len(payload["untrusted_tool_result"]["sources"]), 20)

    def test_calculation_route_sends_assumptions_and_summary_without_the_series(self):
        dispatcher = ToolDispatcher(repository=None, comparison_service=None)

        raw, payload = self.run_turn(dispatcher, ToolCall(
            "calc1", "calculate_scenario", dict(CALC_ARGS)))

        data = payload["untrusted_tool_result"]["data"]
        self.assertIs(data["hypothetical"], True)
        self.assertEqual(data["summary"]["final_balance"], "1060.90")
        self.assertEqual(data["summary"]["interest"], "60.90")
        self.assertNotIn("series", data)
        self.assertLess(len(raw.encode("utf-8")), self.MAX_MODEL_BYTES)


class AggregateSourceBudgetTests(unittest.TestCase):
    """B4-C4-04: el tope de 20 fuentes es agregado y declara lo omitido."""

    def test_search_plus_detail_reports_dropped_sources_instead_of_hiding_them(self):
        products = expanded_products(20)
        dispatcher = ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository(products),
                                    SyntheticConditionsService(products)),
            comparison_service=None)
        service, provider = service_for([
            ChatResult("", None, (ToolCall("s1", "search_products", {
                "query": "Producto", "family": "deposito", "limit": 20,
            }),), "tool_calls"),
            ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                           {"product_id": "SIN-01"}),), "tool_calls"),
            ChatResult("TEST ONLY: prosa retenida.", None, (), "stop"),
        ], dispatcher=dispatcher)

        status, body = chat_http(service)

        self.assertEqual(status, 200, body)
        self.assertEqual(len(body["sources"]), 20)
        self.assertEqual(body["sources_total"], 22)
        self.assertEqual(body["sources_truncated"], 2)
        self.assertTrue(any("20" in note and ("omiti" in note.lower() or "límite" in note.lower())
                            for note in body["answer_provenance"]["limitations"]),
                        body["answer_provenance"]["limitations"])
        self.assertLessEqual(len(json.dumps(body, ensure_ascii=False).encode("utf-8")), 65536)


if __name__ == "__main__":
    unittest.main()
