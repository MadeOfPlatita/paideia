"""Ninguna defensa legítima puede vaciar el turno si ya hay algo que entregar.

Cuatro fallos medidos en producción, todos con el mismo síntoma: el usuario ve un
error o un hueco aunque la aplicación tenía la respuesta a medio hacer.

  A. `finish_reason: "tool_calls"` con una llamada que no se puede ejecutar y texto
     válido en el mismo mensaje. El runner tiraba el texto y devolvía `tool_error`.
  B. El modelo escribe la llamada como XML en el texto. `_strip_tool_attempts` solo
     reconocía bloques CERRADOS, así que `<tool_call>{"name": ...}` sin cierre se
     publicaba crudo al usuario.
  C. Se agota el límite de rondas con el cálculo ya ejecutado. El turno acababa en
     502 CHAT_TOOL_ERROR y el resultado del motor se perdía.
  D. La guarda financiera deja el texto vacío en un turno que SÍ tiene resultado del
     motor. El 502 CHAT_FINANCIAL_QUALITY_REJECTED se comía el cálculo.

Lo que NO cambia (y estas pruebas también lo fijan): una llamada no anunciada no se
ejecuta nunca, un lote con una llamada inválida no ejecuta ninguna, y un turno sin
texto y sin datos locales sigue siendo 502 CHAT_EMPTY_ANSWER.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import (  # noqa: E402
    CATALOGUE_WITHHELD_NOTE,
    LocalChatService,
    ServiceProblem,
    _catalogue_explanation,
    _financial_checked,
    _looks_like_tool_attempt,
    _strip_tool_attempts,
)
from providers import ChatResult, ToolCall  # noqa: E402
from pai_runtime import ToolChatRunner  # noqa: E402
from structured_provider_adapter import FakeChatProvider  # noqa: E402

from test_pai_runtime import (  # noqa: E402
    TestOnlyDispatcher,
    TestOnlyFakeProvider,
    scenario_arguments,
    tool_result,
)

CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
           "purpose": "free_chat", "approved_fields": []}

CALC_DATA = {
    "hypothetical": True, "not_prediction": True, "currency": "EUR",
    "assumptions": {
        "principal": "1000.00", "monthly_contribution": "0.00",
        "annual_rate_percent": "3.00", "inflation_percent": "2.00", "years": 1,
        "method": "compound", "annual_rate_convention": "effective_annual_rate",
        "monthly_contribution_timing": "end_of_month",
        "taxes_included": False, "fees_included": False,
    },
    "summary": {"contributions": "1000.00", "final_balance": "1030.00",
                "interest": "30.00", "inflation_adjusted": "1009.80"},
}


class XmlSinCerrarTests(unittest.TestCase):
    """B: el XML abierto y no cerrado no puede llegar al usuario."""

    SIN_CERRAR = (
        '<tool_call>{"name": "search_products", "arguments": {"query": "depósito"}}',
        'Mira la ficha. <tool_use>{"name": "get_product_detail"}',
        'Texto previo.\n<function_call>{"name": "get_sources"}',
    )

    def test_una_llamada_sin_cerrar_se_detecta(self):
        for texto in self.SIN_CERRAR:
            with self.subTest(texto=texto[:40]):
                self.assertTrue(_looks_like_tool_attempt(texto))

    def test_una_llamada_sin_cerrar_no_deja_xml_en_el_texto(self):
        for texto in self.SIN_CERRAR:
            with self.subTest(texto=texto[:40]):
                limpio = _strip_tool_attempts(texto)
                self.assertNotIn("tool_call", limpio)
                self.assertNotIn("tool_use", limpio)
                self.assertNotIn("function_call", limpio)

    def test_el_texto_anterior_a_la_llamada_se_conserva(self):
        limpio = _strip_tool_attempts('Mira la ficha. <tool_use>{"name": "x"}')
        self.assertEqual(limpio, "Mira la ficha.")

    def test_una_llamada_sin_cerrar_y_sin_prosa_no_publica_nada(self):
        limpio = _strip_tool_attempts('<tool_call>{"name": "search_products"}')
        self.assertEqual(limpio, "")

    def test_la_prosa_del_catalogo_tampoco_lleva_el_xml(self):
        # La explicación se pega a la respuesta compuesta del catálogo: si lleva XML,
        # el bloque se publica dentro de la ficha.
        prosa = ('Mira la ficha. <tool_call>{"name":"get_product_detail",'
                 '"arguments":{"product_id":"DEP-01"}}</tool_call> Comprueba el plazo.')
        limpio = _catalogue_explanation(prosa)
        self.assertIsNotNone(limpio)
        self.assertNotIn("tool_call", limpio)
        self.assertIn("Mira la ficha", limpio)

    def test_una_explicacion_que_solo_era_xml_no_se_publica(self):
        solo_xml = '<tool_call>{"name":"search_products","arguments":{"query":"x"}}</tool_call>'
        self.assertIsNone(_catalogue_explanation(solo_xml))


class GuardaFinancieraConDatosLocalesTests(unittest.TestCase):
    """D: con datos locales, quedarse sin prosa no es un 502."""

    PELIGROSO = "Invertir no conlleva ningún riesgo."

    def test_sin_datos_locales_el_502_se_mantiene(self):
        with self.assertRaises(ServiceProblem) as caught:
            _financial_checked(self.PELIGROSO, has_local_data=False)
        self.assertEqual(caught.exception.code, "CHAT_FINANCIAL_QUALITY_REJECTED")
        self.assertEqual(caught.exception.status, 502)

    def test_con_datos_locales_devuelve_vacio_en_vez_de_lanzar(self):
        self.assertEqual(_financial_checked(self.PELIGROSO, has_local_data=True), "")

    def test_el_texto_seguro_sigue_intacto_con_y_sin_datos(self):
        seguro = "La TAE normaliza el coste anual de un producto."
        self.assertEqual(_financial_checked(seguro, has_local_data=True), seguro)
        self.assertEqual(_financial_checked(seguro, has_local_data=False), seguro)

    def test_la_frase_peligrosa_se_quita_y_el_resto_sobrevive_sin_datos(self):
        mezcla = ("Ahorrar significa conservar dinero sin riesgo de perder el capital. "
                  "La inflación reduce el valor real del dinero ahorrado.")
        limpio = _financial_checked(mezcla, has_local_data=False)
        self.assertNotIn("sin riesgo de perder el capital", limpio)
        self.assertIn("La inflación reduce el valor real", limpio)


class ServicioNoPierdeElCalculoTests(unittest.TestCase):
    """D y C de punta a punta: el turno con motor ejecutado no acaba en hueco."""

    def servicio(self, outcomes):
        import app
        from backend_services import CatalogueComparisonService
        from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission
        from datetime import datetime, timezone
        from pai_tools import ToolDispatcher
        policy = AdmissionPolicy(max_concurrent=2, max_queue=2, calls_per_minute=20,
                                 calls_per_day=40, ticket_ttl_seconds=120,
                                 claim_ttl_seconds=120, scope="TEST_ONLY_502_ROUTES")
        gate = InterfazChatAdmission(
            policy, lambda: datetime.now(timezone.utc),
            budget_state=InMemoryBudgetState.new_empty(scope=policy.scope))
        provider = FakeChatProvider(outcomes[0], test_only=True, outcomes=tuple(outcomes))
        service = LocalChatService(
            provider=provider, enabled=True, test_only=True, admission=gate,
            tools_enabled=True,
            dispatcher=ToolDispatcher(app.SnapshotRepository(),
                                      CatalogueComparisonService()))
        return service, provider

    def calculo_y(self, prosa_final, *, finish="stop"):
        return [
            ChatResult("", None, (ToolCall("c1", "calculate_scenario",
                                           scenario_arguments()),), "tool_calls"),
            ChatResult(prosa_final, None, (), finish),
        ]

    def test_el_motor_calculo_y_el_modelo_no_escribio_nada(self):
        # Antes: 200 con `answer: ""` y el usuario viendo un hueco.
        service, provider = self.servicio(self.calculo_y(""))
        body = service.chat({"message": "Calcula 5000 al 3 % a 2 años.",
                             "consent": CONSENT})
        self.assertEqual(provider.calls, 2)
        self.assertTrue(body["answer"].strip(), "el hueco no es una respuesta")
        self.assertIn("motor local", body["answer"])
        self.assertIsInstance(body["calculation"], dict)

    def test_la_guarda_financiera_no_se_come_el_resultado_del_motor(self):
        # Antes: 502 CHAT_FINANCIAL_QUALITY_REJECTED con el cálculo en la mano.
        service, provider = self.servicio(self.calculo_y(
            "Invertir no conlleva ningún riesgo."))
        body = service.chat({"message": "Calcula 5000 al 3 % a 2 años.",
                             "consent": CONSENT})
        self.assertEqual(provider.calls, 2)
        self.assertNotIn("ningún riesgo", body["answer"])
        self.assertIn("motor local", body["answer"])
        self.assertIsInstance(body["calculation"], dict)
        self.assertEqual(body["calculation"]["summary"]["final_balance"], "1030.00")


class RunnerNoPierdeTrabajoTests(unittest.TestCase):
    """A y C con el runner real: la defensa se mantiene, la prosa no se tira."""

    def test_sin_herramientas_anunciadas_la_llamada_no_se_ejecuta_pero_el_texto_llega(self):
        dispatcher = TestOnlyDispatcher([])
        provider = TestOnlyFakeProvider([ChatResult(
            "Compara el plazo y la liquidez antes que la tasa.", None,
            (ToolCall("c1", "search_products", {"query": "deposito"}),), "tool_calls")])

        result = ToolChatRunner(provider, dispatcher).run(
            [{"role": "user", "content": "TEST ONLY: pregunta de método."}],
            with_tools=False)

        # La frontera se respeta: nada se ejecuta.
        self.assertEqual(dispatcher.calls, [])
        self.assertEqual(len(provider.requests), 1)
        # Y la llamada queda registrada como rechazada, no como ejecutada.
        self.assertEqual([e["state"] for e in result["tool_events"]], ["rejected"])
        # Pero la respuesta ya escrita no se tira: el `finish_reason` del proveedor
        # se conserva tal cual (`tool_calls`), porque es lo que dijo el proveedor.
        self.assertEqual(result["finish_reason"], "tool_calls")
        self.assertIn("plazo y la liquidez", result["answer"])

    def test_sin_herramientas_y_sin_texto_el_turno_sigue_fallando(self):
        dispatcher = TestOnlyDispatcher([])
        provider = TestOnlyFakeProvider([ChatResult(
            "", None, (ToolCall("c1", "search_products", {"query": "deposito"}),),
            "tool_calls")])

        result = ToolChatRunner(provider, dispatcher).run(
            [{"role": "user", "content": "TEST ONLY: pregunta de método."}],
            with_tools=False)

        self.assertEqual(dispatcher.calls, [])
        self.assertEqual(result["finish_reason"], "tool_error")

    def test_el_limite_de_rondas_conserva_el_texto_del_ultimo_turno(self):
        dispatcher = TestOnlyDispatcher([
            tool_result("calculate_scenario", data=CALC_DATA),
            tool_result("search_products", data={"items": []}),
        ])
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("c1", "calculate_scenario",
                                           scenario_arguments()),), "tool_calls"),
            ChatResult("", None, (ToolCall("c2", "search_products",
                                           {"query": "deposito"}),), "tool_calls"),
            ChatResult("Con esos datos, el plazo manda sobre la tasa.", None,
                       (ToolCall("c3", "search_products", {"query": "deposito"}),),
                       "tool_calls"),
        ])

        result = ToolChatRunner(provider, dispatcher, max_tool_rounds=2).run(
            [{"role": "user", "content": "TEST ONLY: insiste."}])

        # La ronda extra no se ejecuta: la defensa contra el bucle sigue en pie.
        self.assertEqual(len(dispatcher.calls), 2)
        self.assertEqual(result["tool_events"][-1]["state"], "rejected")
        # Y el texto del último turno se entrega en vez de morir en un 502.
        self.assertEqual(result["finish_reason"], "stop")
        self.assertIn("el plazo manda", result["answer"])

    def test_el_lote_rechazado_conserva_el_calculo_ya_hecho(self):
        dispatcher = TestOnlyDispatcher([tool_result("calculate_scenario", data=CALC_DATA)])
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (ToolCall("c1", "calculate_scenario",
                                           scenario_arguments()),), "tool_calls"),
            ChatResult("", None, (
                ToolCall("c2", "get_product_detail", {"product_id": " DEP-01"}),
            ), "tool_calls"),
        ])

        result = ToolChatRunner(provider, dispatcher).run(
            [{"role": "user", "content": "TEST ONLY: cálculo y ficha."}])

        # El lote inválido no se ejecuta: el identificador con espacio no es literal.
        self.assertEqual(len(dispatcher.calls), 1)
        self.assertEqual(result["finish_reason"], "stop")
        # El cálculo determinista no se pierde por un rechazo posterior.
        self.assertIsInstance(result["calculation"], dict)
        self.assertEqual(result["calculation"]["summary"]["final_balance"], "1030.00")

    def test_el_motivo_del_fallo_viaja_en_el_dto(self):
        # Sin `failure_detail`, todos los fallos se veían iguales y el diagnóstico
        # mandaba a mirar el límite de rondas aunque el rechazo fuera otro.
        dispatcher = TestOnlyDispatcher([])
        provider = TestOnlyFakeProvider([ChatResult("", None, (
            ToolCall("c1", "search_products", {"query": "", "limit": 99}),
        ), "tool_calls")])

        result = ToolChatRunner(provider, dispatcher).run(
            [{"role": "user", "content": "TEST ONLY: argumentos inválidos."}])

        self.assertEqual(result["finish_reason"], "tool_error")
        self.assertEqual(result["failure_detail"], "batch_rejected:invalid_arguments")
        # Y no filtra los valores recibidos del modelo.
        self.assertNotIn("99", json_dump(result))


def json_dump(value):
    import json
    return json.dumps(value, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
