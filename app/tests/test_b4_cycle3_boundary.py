"""B4, ciclo 3: frontera fail-closed para prosa y datos de catálogo.

Casos sintéticos, sin red externa ni proveedores reales. Fijan el contrato:

- un proveedor que NO usa herramientas no puede entregar tasas, importes,
  vigencias ni atribuciones de fuente como hechos verificados: el texto se retiene
  y, si hay datos locales, se muestran determinísticamente con su procedencia;
- la retención es una frontera de superficie (cifras/atribuciones), no una
  verificación semántica; se declara como tal en `text_validation`;
- el texto conceptual sin cifras ni atribuciones se conserva;
- un turno de calculadora conserva el resultado determinista local aunque la prosa
  numérica del modelo se retire;
- condiciones estructuralmente malformadas del servicio producen un error explícito
  y nunca se presentan como `identity_only` ni como catálogo vacío;
- una ausencia real de condiciones se declara como ausencia;
- la proyección del chat y la del modelo conservan conflictos y campos desconocidos.
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
from pai_runtime import ToolChatRunner
from pai_tools import ToolDispatcher
from providers import ChatResult, ToolCall
from structured_provider_adapter import FakeChatProvider

from test_b4_condition_provenance import (
    CONSENT,
    OFFICIAL_URL,
    PRODUCTS,
    SyntheticConditionsService,
    SyntheticRepository,
    catalog_item,
    condition,
    make_gate,
)
from test_backend_integration import request, running_server
from test_functional05_http import TestOnlyFakeProvider


SENTINEL = "9,99"
REVIEW_URL = "https://example.invalid/synthetic/DEP-REVIEW"


def review_product():
    """Producto sintético con conflicto declarado y campos desconocidos."""
    product = copy.deepcopy(PRODUCTS[0])
    product.update(
        product_id="DEP-REVIEW",
        display_name="Depósito con conflicto declarado",
        source={"url": REVIEW_URL, "kind": "official", "document_date": None,
                "retrieved_at": "2026-11-03"},
        conditions=[condition(source_ids=[REVIEW_URL])],
        rate_tiers=[],
        origin="curated_conditions",
    )
    return product


def review_repository():
    repository = SyntheticRepository([review_product()])
    repository.items[0]["conflicts"] = [
        "Conflicto de fuentes pendiente: dos plazos distintos para la misma entidad."
    ]
    repository.items[0]["unknown_fields"] = [
        "plazos disponibles", "fecha efectiva de cada oferta"
    ]
    return repository


def service_for(outcomes, *, dispatcher=None, gate=None):
    provider = TestOnlyFakeProvider(list(outcomes))
    service = LocalChatService(
        provider=provider, enabled=True, test_only=True,
        dispatcher=dispatcher if dispatcher is not None else ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository(), SyntheticConditionsService()),
            comparison_service=None),
        tools_enabled=True,
        admission=gate if gate is not None else make_gate(),
        catalogue_usage_approved=True,
    )
    return service, provider


def chat_http(service, message="TEST ONLY: consulta sintética"):
    with running_server(chat_service=service) as server:
        return request(server, "/api/chat", {"message": message, "consent": CONSENT})


class NoToolProseBoundaryTests(unittest.TestCase):
    """B4-C3-01/02: prosa sin herramientas no puede presentar hechos inventados."""

    UNSAFE_VARIANTS = (
        # Variantes reproducidas por la revisión independiente del ciclo 2.
        "TEST ONLY: las TAE vigentes del depósito son del 9,99 %.",
        "TEST ONLY: la TAE del 9,99 % fue confirmada oficialmente por el banco.",
        "TEST ONLY: la TAE del 9,99 % sigue en vigor según el banco.",
        "TEST ONLY: el 9,99 % es la rentabilidad actual confirmada por la entidad.",
        "TEST ONLY: la TAE vigente es 9,99 % y la fuente es oficial.",
        # Otras superficies del mismo fallo: cifra sin palabra de tasa, atribución
        # sin cifra, importe con moneda y URL inventada.
        "TEST ONLY: el banco publicó un 4,10 % anual para ese producto.",
        "TEST ONLY: el tipo fue confirmado por la entidad según el folleto.",
        "TEST ONLY: puedes comprobarlo en https://example.invalid/fabricada.",
        "TEST ONLY: el depósito remunera con tres coma veinticinco por ciento.",
        "TEST ONLY: la TAE es 3,25 %.",
        "TEST ONLY: el producto paga 3,25 al año.",
        "TEST ONLY: ese depósito ofrece 4,10 anual.",
        "TEST ONLY: fuente: el producto es seguro.",
        "TEST ONLY: el producto rinde 3,25.",
        "TEST ONLY: paga 3,25 por cada 100.",
        "TEST ONLY: abona 3,25 mensual.",
    )

    def test_no_tool_prose_with_figures_or_attributions_is_withheld(self):
        for text in self.UNSAFE_VARIANTS:
            with self.subTest(text=text):
                service, provider = service_for([ChatResult(text, None, (), "stop")])

                status, body = chat_http(service)

                self.assertEqual(status, 200, body)
                self.assertEqual(body["answer"], "", body)
                self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
                self.assertEqual(body["answer_provenance"]["text_validation"], "not_performed")
                self.assertEqual(body["answer_provenance"]["text_state"], "withheld_unbacked_claim")
                raw = json.dumps(body, ensure_ascii=False)
                self.assertNotIn(SENTINEL, raw)
                self.assertNotIn("4,10", raw)
                self.assertNotIn("3,25", raw)
                self.assertNotIn("example.invalid/fabricada", raw)
                self.assertNotIn(text, raw)
                self.assertEqual(len(provider.requests), 1, "no debe haber reintento")
                notes = body["answer_provenance"]["limitations"]
                self.assertTrue(any("sin datos locales" in note.lower() for note in notes), notes)
                self.assertTrue(any("cifra" in note.lower() or "atribu" in note.lower()
                                    or "identificador" in note.lower() for note in notes), notes)

    def test_refusal_and_truncated_answers_use_the_same_boundary(self):
        cases = (
            ChatResult("", None, (), "stop", "TEST ONLY: las TAE vigentes son del 9,99 %."),
            ChatResult("TEST ONLY: rentabilidad del 9,99 % confirmada por el banco.",
                       None, (), "length"),
        )
        for outcome in cases:
            with self.subTest(finish_reason=outcome.finish_reason):
                service, provider = service_for([outcome])

                status, body = chat_http(service)

                self.assertEqual(status, 200, body)
                self.assertEqual(body["answer"], "", body)
                self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
                self.assertNotIn(SENTINEL, json.dumps(body, ensure_ascii=False))

    def test_concept_only_prose_is_still_delivered_unverified(self):
        for text in (
            "TEST ONLY: la TAE resume el coste anual efectivo de un producto.",
            "TEST ONLY: el interés compuesto reinvierte los intereses generados.",
            "TEST ONLY: antes de invertir conviene tener un colchón de gastos.",
            "TEST ONLY: en dos años el interés compuesto reinvierte los intereses.",
            "TEST ONLY: según tu horizonte, conviene distinguir ahorro e inversión.",
            "TEST ONLY: las fuentes de financiación de una empresa pueden ser propias o ajenas.",
        ):
            with self.subTest(text=text):
                service, provider = service_for([ChatResult(text, None, (), "stop")])

                status, body = chat_http(service)

                self.assertEqual(status, 200, body)
                self.assertEqual(body["answer"], text)
                self.assertEqual(body["answer_text_state"], "shown_unverified")
                self.assertEqual(body["answer_provenance"]["text_validation"], "not_performed")
                self.assertTrue(any("no se valida semánticamente" in note
                                    for note in body["answer_provenance"]["limitations"]))


class PlainChatBoundaryTests(unittest.TestCase):
    """B4-C3-03b: el chat sin herramientas usa la misma frontera."""

    def service(self, answer):
        provider = FakeChatProvider(ChatResult(answer, None, (), "stop"), test_only=True)
        return LocalChatService(provider=provider, enabled=True, test_only=True)

    def test_plain_chat_withholds_invented_rate(self):
        body = self.service("TEST ONLY: la TAE vigente es 9,99 %.").chat(
            {"message": "TEST ONLY: ¿qué tasa hay?", "consent": CONSENT})

        self.assertEqual(body["answer"], "")
        self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
        self.assertNotIn(SENTINEL, json.dumps(body, ensure_ascii=False))
        self.assertEqual(body["answer_provenance"]["text_state"], "withheld_unbacked_claim")
        self.assertTrue(any("sin datos locales" in note.lower()
                            for note in body["answer_provenance"]["limitations"]))

    def test_plain_chat_keeps_concept_text(self):
        text = "TEST ONLY: la TAE resume el coste anual efectivo de un producto."
        body = self.service(text).chat(
            {"message": "TEST ONLY: explícame la TAE.", "consent": CONSENT})

        self.assertEqual(body["answer"], text)
        self.assertEqual(body["answer_text_state"], "shown_unverified")


class CalculatorBoundaryTests(unittest.TestCase):
    """B4-C3-04: el cálculo determinista sigue disponible cuando la prosa cae."""

    ARGS = {
        "principal": "1000.00", "annual_rate_percent": "3.00", "years": 1,
        "monthly_contribution": "0.00", "method": "compound",
        "inflation_percent": "2.00",
    }

    def test_calculator_prose_with_engine_figures_is_withheld_and_the_result_is_delivered(self):
        service, provider = service_for([
            ChatResult("", None, (ToolCall("calc1", "calculate_scenario", dict(self.ARGS)),), "tool_calls"),
            ChatResult("TEST ONLY: el motor devuelve 1030.00 EUR nominales.", None, (), "stop"),
        ])

        status, body = chat_http(service, message="TEST ONLY: calcula un escenario.")

        self.assertEqual(status, 200, body)
        self.assertEqual(body["answer"], "")
        self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
        self.assertEqual(body["answer_provenance"]["text_validation"], "not_performed")
        self.assertNotIn("1030.00", json.dumps(body["answer"], ensure_ascii=False))
        self.assertEqual(body["calculation"]["summary"]["final_balance"], "1030.00")
        self.assertEqual(body["calculation"]["assumptions"]["principal"], "1000.00")
        self.assertTrue(any("motor" in note.lower() and "local" in note.lower()
                            for note in body["answer_provenance"]["limitations"]))
        # La cifra que ve el cliente procede del motor determinista local y viaja
        # separada de la prosa; ningún número del modelo se presenta como dato.
        from domain import calculate_scenario
        local = calculate_scenario(dict(self.ARGS))
        self.assertEqual(local["summary"]["final_balance"], "1030.00")
        self.assertEqual(body["calculation"]["summary"], local["summary"])

    def test_spanish_thousands_separator_prose_is_not_used_as_evidence(self):
        service, provider = service_for([
            ChatResult("", None, (ToolCall("calc1", "calculate_scenario", dict(self.ARGS)),), "tool_calls"),
            ChatResult("TEST ONLY: el saldo final es 1.030,00 €.", None, (), "stop"),
        ])

        status, body = chat_http(service, message="TEST ONLY: calcula un escenario.")

        self.assertEqual(status, 200, body)
        self.assertEqual(body["answer"], "")
        self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
        self.assertEqual(body["calculation"]["summary"]["final_balance"], "1030.00")

    def test_untraceable_rate_in_a_calculator_turn_is_withheld_but_result_remains(self):
        service, provider = service_for([
            ChatResult("", None, (ToolCall("calc1", "calculate_scenario", dict(self.ARGS)),), "tool_calls"),
            ChatResult("TEST ONLY: la TAE vigente es 9,99 % y es oficial.", None, (), "stop"),
        ])

        status, body = chat_http(service, message="TEST ONLY: calcula un escenario.")

        self.assertEqual(status, 200, body)
        self.assertEqual(body["answer"], "")
        self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
        self.assertNotIn(SENTINEL, json.dumps(body, ensure_ascii=False))
        self.assertEqual(body["calculation"]["summary"]["final_balance"], "1030.00")
        from domain import calculate_scenario
        self.assertEqual(calculate_scenario(dict(self.ARGS))["summary"]["final_balance"], "1030.00")

    def test_untraceable_figure_without_attribution_is_withheld(self):
        for text in ("TEST ONLY: el resultado sería 2500.00 EUR.",
                     "TEST ONLY: el saldo final es 9999.00."):
            with self.subTest(text=text):
                service, provider = service_for([
                    ChatResult("", None, (ToolCall("calc1", "calculate_scenario", dict(self.ARGS)),), "tool_calls"),
                    ChatResult(text, None, (), "stop"),
                ])

                status, body = chat_http(service, message="TEST ONLY: calcula un escenario.")

                self.assertEqual(status, 200, body)
                self.assertEqual(body["answer"], "")
                self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")
                self.assertNotIn("9999.00", json.dumps(body, ensure_ascii=False))

    def test_traceable_figure_cannot_be_attributed_to_a_product(self):
        service, provider = service_for([
            ChatResult("", None, (ToolCall("calc1", "calculate_scenario", dict(self.ARGS)),), "tool_calls"),
            ChatResult("TEST ONLY: la TAE del depósito es 3.00 %.", None, (), "stop"),
        ])

        status, body = chat_http(service, message="TEST ONLY: calcula un escenario.")

        self.assertEqual(status, 200, body)
        self.assertEqual(body["answer"], "")
        self.assertEqual(body["answer_text_state"], "withheld_unbacked_claim")

    def test_concept_calculator_prose_keeps_its_text_and_the_result(self):
        answer = "TEST ONLY: el cálculo es hipotético y lo hace el motor local."
        service, provider = service_for([
            ChatResult("", None, (ToolCall("calc1", "calculate_scenario", dict(self.ARGS)),), "tool_calls"),
            ChatResult(answer, None, (), "stop"),
        ])

        status, body = chat_http(service)

        self.assertEqual(status, 200, body)
        self.assertEqual(body["answer"], answer)
        self.assertEqual(body["answer_text_state"], "shown_unverified")
        self.assertEqual(body["calculation"]["summary"]["final_balance"], "1030.00")
        from domain import calculate_scenario
        self.assertEqual(calculate_scenario(dict(self.ARGS))["summary"]["final_balance"], "1030.00")


class MalformedConditionsService:
    """Servicio que responde con la estructura de condiciones alterada."""

    def __init__(self, entry):
        self.entry = entry

    def describe(self):
        return {"reference_date": "2026-11-04",
                "products": [{"product_id": "DEP-KNOWN", **copy.deepcopy(self.entry)}],
                "state_counts": {}, "rules_version": "catalogue-conditions.v1",
                "not_for_publication": True}

    def catalogue_extras(self, q=None, family=None):
        return []


def dispatcher_with_conditions_entry(entry):
    return ToolDispatcher(
        CatalogueWithConditions(SyntheticRepository(), MalformedConditionsService(entry)),
        comparison_service=None,
    )


class MalformedConditionsTests(unittest.TestCase):
    """B4-C3-05/06: malformación estructural es error, no ausencia."""

    BAD_ENTRIES = (
        {"conditions": ["garbage"]},
        {"conditions": {"bad": "shape"}},
        {"conditions": "texto"},
        {"conditions": [{"metric": "annual_rate_percent"}]},
        {"conditions": [None]},
    )

    def test_tool_returns_explicit_error_and_never_identity_only(self):
        for entry in self.BAD_ENTRIES:
            with self.subTest(entry=entry):
                result = dispatcher_with_conditions_entry(entry).dispatch(
                    "get_product_detail", {"product_id": "DEP-KNOWN"})

                self.assertEqual(result["status"], "error", result)
                self.assertIn(result["error"]["code"],
                              {"CONDITIONS_UNAVAILABLE", "REPOSITORY_ERROR"})
                self.assertEqual(result["data"], {})
                serialized = json.dumps(result, ensure_ascii=False)
                self.assertNotIn("identity_only", serialized)
                self.assertNotIn("PRIVATE", serialized)

    def test_entry_without_conditions_key_is_not_read_as_identity_only(self):
        result = dispatcher_with_conditions_entry({"family": "deposito"}).dispatch(
            "get_product_detail", {"product_id": "DEP-KNOWN"})

        self.assertEqual(result["status"], "error", result)
        self.assertEqual(result["error"]["code"], "CONDITIONS_UNAVAILABLE")

    def test_entry_without_product_id_invalidates_the_report(self):
        class ReportWithoutId:
            def describe(self):
                return {"reference_date": "2026-11-04",
                        "products": [{"conditions": [condition(source_ids=[OFFICIAL_URL])]}]}

            def catalogue_extras(self, q=None, family=None):
                return []

        dispatcher = ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository(), ReportWithoutId()),
            comparison_service=None)

        result = dispatcher.dispatch("get_product_detail", {"product_id": "DEP-KNOWN"})

        self.assertEqual(result["status"], "error", result)
        self.assertEqual(result["error"]["code"], "CONDITIONS_UNAVAILABLE")

    def test_http_malformed_conditions_is_502_without_catalogue(self):
        service, provider = service_for([
            ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                           {"product_id": "DEP-KNOWN"}),), "tool_calls"),
        ], dispatcher=dispatcher_with_conditions_entry({"conditions": ["garbage"]}))

        status, body = chat_http(service)

        self.assertEqual(status, 502, body)
        self.assertEqual(body["error"]["code"], "CHAT_TOOL_ERROR")
        self.assertNotIn("catalogue", body)
        self.assertNotIn("identity_only", json.dumps(body, ensure_ascii=False))

    def test_real_absence_is_declared_as_absence(self):
        class EmptyReport:
            def describe(self):
                return {"reference_date": "2026-11-04", "products": [],
                        "state_counts": {}, "rules_version": "catalogue-conditions.v1",
                        "not_for_publication": True}

            def catalogue_extras(self, q=None, family=None):
                return []

        dispatcher = ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository(), EmptyReport()),
            comparison_service=None)

        result = dispatcher.dispatch("get_product_detail", {"product_id": "DEP-KNOWN"})

        self.assertEqual(result["status"], "ok", result)
        product = result["data"]["product"]
        self.assertEqual(product["conditions_state"], "identity_only")
        self.assertEqual(product["conditions_record_state"], "absent")
        self.assertTrue(any("ausencia" in note.lower()
                            for note in product["conditions_state_reasons"]), product)


class ChatProjectionReviewTests(unittest.TestCase):
    """B4-C3-08/09: conflictos y campos desconocidos llegan al DTO y al modelo."""

    def test_chat_dto_carries_conflicts_and_unknown_fields(self):
        dispatcher = ToolDispatcher(
            CatalogueWithConditions(review_repository(), SyntheticConditionsService([review_product()])),
            comparison_service=None)
        service, provider = service_for([
            ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                           {"product_id": "DEP-REVIEW"}),), "tool_calls"),
            ChatResult("TEST ONLY: prosa no mostrada.", None, (), "stop"),
        ], dispatcher=dispatcher)

        status, body = chat_http(service)

        self.assertEqual(status, 200, body)
        product = next(item for item in body["catalogue"]["products"]
                       if item["id"] == "DEP-REVIEW")
        self.assertEqual(product["conflicts"], [
            "Conflicto de fuentes pendiente: dos plazos distintos para la misma entidad."
        ])
        self.assertEqual(product["unknown_fields"],
                         ["plazos disponibles", "fecha efectiva de cada oferta"])
        self.assertEqual(product["review_state"], "conflicts_and_unknown_fields")
        self.assertTrue(any("conflicto" in note.lower()
                            for note in product["conditions_state_reasons"]), product)

    def test_model_facing_search_projection_carries_conflicts_and_unknown_fields(self):
        dispatcher = ToolDispatcher(
            CatalogueWithConditions(review_repository(), SyntheticConditionsService([review_product()])),
            comparison_service=None)
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("s1", "search_products", {
                "query": "Depósito", "family": "deposito", "limit": 5,
            }),), "tool_calls"),
            ChatResult("TEST ONLY: respuesta no mostrada.", None, (), "stop"),
        ])

        ToolChatRunner(provider, dispatcher).run([
            {"role": "user", "content": "TEST ONLY: busca depósitos."},
        ])

        payload = json.loads(provider.requests[1][-1]["content"])
        item = next(entry for entry in payload["untrusted_tool_result"]["data"]["items"]
                    if entry["id"] == "DEP-REVIEW")
        self.assertEqual(item["conflicts"], [
            "Conflicto de fuentes pendiente: dos plazos distintos para la misma entidad."
        ])
        self.assertEqual(item["unknown_fields"],
                         ["plazos disponibles", "fecha efectiva de cada oferta"])
        self.assertEqual(item["conflicts_count"], 1)
        self.assertEqual(item["unknown_fields_count"], 2)
        self.assertEqual(item["review_state"], "conflicts_and_unknown_fields")


class ProjectionFailClosedTests(unittest.TestCase):
    """B4-C3-10: una condición malformada no se convierte en 'documented'."""

    class StaticDispatcher:
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

    def test_invalid_condition_shape_downgrades_the_product_state(self):
        product = catalog_item(PRODUCTS[0])
        product.update(conditions=[{"metric": "annual_rate_percent"}],
                       conditions_state="documented",
                       conditions_reference_date="2026-11-04")
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                           {"product_id": "DEP-KNOWN"}),), "tool_calls"),
            ChatResult("TEST ONLY: sin datos locales.", None, (), "stop"),
        ])

        result = ToolChatRunner(provider, self.StaticDispatcher(product)).run([
            {"role": "user", "content": "TEST ONLY: detalle."},
        ])

        projected = result["catalogue"]["products"][0]
        self.assertNotEqual(projected["conditions_state"], "documented", projected)
        self.assertEqual(projected["conditions_state"], "conditions_unknown")
        self.assertEqual(projected["conditions"], [])
        self.assertEqual(projected["conditions_record_state"], "invalid")
        self.assertTrue(projected["conditions_state_reasons"])

    def test_non_list_conditions_never_stay_documented(self):
        product = catalog_item(PRODUCTS[0])
        product.update(conditions={"metric": "annual_rate_percent"},
                       conditions_state="documented",
                       conditions_reference_date="2026-11-04")
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                           {"product_id": "DEP-KNOWN"}),), "tool_calls"),
            ChatResult("TEST ONLY: sin datos locales.", None, (), "stop"),
        ])

        result = ToolChatRunner(provider, self.StaticDispatcher(product)).run([
            {"role": "user", "content": "TEST ONLY: detalle."},
        ])

        projected = result["catalogue"]["products"][0]
        self.assertEqual(projected["conditions_state"], "conditions_unknown")
        self.assertTrue(any("forma" in note.lower() or "válida" in note.lower()
                            for note in projected["conditions_state_reasons"]), projected)

    def test_stale_condition_cannot_stay_documented(self):
        projected_known = {
            **condition(source_ids=[OFFICIAL_URL]),
            "source_class": "official", "source_resolution": "resolved",
            "class_state": "consistent",
            "sources": [{"source_id": OFFICIAL_URL, "url": OFFICIAL_URL, "kind": "official",
                         "class": "official", "retrieved_at": "2026-11-03",
                         "resolution": "resolved"}],
        }
        projected_stale = {**projected_known, "state": "stale",
                           "effective_to": "2026-10-31"}
        product = catalog_item(PRODUCTS[0])
        product.update(conditions=[projected_known, projected_stale],
                       conditions_state="documented",
                       conditions_reference_date="2026-11-04")
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                           {"product_id": "DEP-KNOWN"}),), "tool_calls"),
            ChatResult("TEST ONLY: sin datos locales.", None, (), "stop"),
        ])

        result = ToolChatRunner(provider, self.StaticDispatcher(product)).run([
            {"role": "user", "content": "TEST ONLY: detalle."},
        ])

        projected = result["catalogue"]["products"][0]
        self.assertEqual(projected["conditions_state"], "documented_not_current")
        self.assertEqual([entry["state"] for entry in projected["conditions"]], ["known", "stale"])


class UnchangedDataTests(unittest.TestCase):
    """B4-C3-11: el camino documentado válido no cambia."""

    def test_valid_conditions_remain_documented_with_source_and_dates(self):
        dispatcher = ToolDispatcher(
            CatalogueWithConditions(SyntheticRepository(), SyntheticConditionsService()),
            comparison_service=None)
        service, provider = service_for([
            ChatResult("", None, (ToolCall("c1", "get_product_detail",
                                           {"product_id": "DEP-KNOWN"}),), "tool_calls"),
            ChatResult("TEST ONLY: prosa no mostrada.", None, (), "stop"),
        ], dispatcher=dispatcher)

        status, body = chat_http(service)

        self.assertEqual(status, 200, body)
        product = body["catalogue"]["products"][0]
        self.assertEqual(product["id"], "DEP-KNOWN")
        self.assertEqual(product["conditions_state"], "documented")
        self.assertEqual(product["conditions_record_state"], "documented")
        self.assertEqual(product["review_state"], "no_pending_review_items")
        self.assertEqual(product["conditions"][0]["value"], "3.10")
        self.assertEqual(product["conditions"][0]["source_class"], "official")
        self.assertEqual(product["conditions"][0]["retrieved_at"], "2026-11-03")


if __name__ == "__main__":
    unittest.main()
