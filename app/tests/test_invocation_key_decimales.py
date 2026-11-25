"""La misma invocación escrita con otro formato decimal no puede tumbar el turno.

CASO REAL. El modelo llamaba dos veces a `calculate_scenario` con el mismo cálculo
—«2000» en una llamada y «2000.00» en la otra— porque el prompt le pide repetir el
escenario cuando la persona cambia un dato. El runtime comparaba los argumentos
como texto JSON: las dos claves eran distintas, el lote se marcaba como
`duplicate_invocation` y se tiraba ENTERO con `_failure(... detail="round_limit")`.
El servicio lo publicaba como 502 CHAT_TOOL_ERROR y la persona se quedaba sin
respuesta teniendo el cálculo hecho.

La regla que se fija aquí:

  1. «2000», «2000.0» y «2000.00» son la MISMA invocación (el motor los parsea con
     `Decimal`, así que producen el mismo resultado). Se reutiliza el resultado y se
     ejecuta una sola vez.
  2. Dos invocaciones GENUINAMENTE distintas (otro principal, otro plazo, otro
     método, otro tipo) siguen siendo dos invocaciones: se ejecutan las dos. Si se
     colapsaran, el usuario vería el resultado del cálculo equivocado.
  3. El formato de la clave no depende de la escala: `Decimal.normalize()` puede
     devolver notación científica (`2E+3`) y esa cadena no puede ser la clave de
     nada que después haya que volver a construir igual.
"""

import re
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pai_runtime import ToolChatRunner  # noqa: E402
from providers import ChatResult, ToolCall  # noqa: E402

from test_pai_runtime import (  # noqa: E402
    TestOnlyDispatcher,
    TestOnlyFakeProvider,
    tool_result,
)


def escenario(**overrides):
    """Escenario completo con el formato que escribe el modelo en producción."""
    base = {
        "principal": "2000",
        "annual_rate_percent": "3",
        "years": 1,
        "monthly_contribution": "0",
        "method": "compound",
        "inflation_percent": "2",
    }
    base.update(overrides)
    return base


def clave(**overrides):
    return ToolChatRunner._invocation_key("calculate_scenario", escenario(**overrides))


# Representaciones del MISMO número decimal. El motor las parsea igual.
EQUIVALENTES = (
    "2000",
    "2000.0",
    "2000.00",
    "2000.000",
)


class ClaveDeInvocacionTests(unittest.TestCase):
    def test_el_mismo_importe_escrito_de_otra_forma_da_la_misma_clave(self):
        referencia = clave()
        for texto in EQUIVALENTES:
            with self.subTest(principal=texto):
                self.assertEqual(clave(principal=texto), referencia,
                                 f"«{texto}» es el mismo importe que «2000»")

    def test_los_cuatro_campos_decimales_se_normalizan(self):
        referencia = clave()
        for campo, valor in (("principal", "2000.00"),
                             ("monthly_contribution", "0.00"),
                             ("annual_rate_percent", "3.0000"),
                             ("inflation_percent", "2.00")):
            with self.subTest(campo=campo):
                self.assertEqual(clave(**{campo: valor}), referencia,
                                 f"{campo} con «{valor}» es el mismo número")

    def test_la_clave_no_usa_notacion_cientifica(self):
        # Decimal("2000").normalize() da 2E+3; si esa cadena fuera la clave, dos
        # llamadas equivalentes podrían no coincidir al reconstruirla. Se exige el
        # formato decimal llano, sin exponente.
        texto = clave(principal="2000")[1]
        self.assertIsNone(re.search(r"\d[Ee][+-]?\d", texto), texto)
        self.assertIn('"principal":"2000"', texto)

    def test_un_importe_con_miles_de_decimales_sigue_siendo_estable(self):
        # La aritmética de Decimal no debe introducir ruido: «0.10» y «0.1» son el
        # mismo número, y ninguno de los dos puede acabar en «0.1000000001».
        self.assertEqual(clave(principal="0.1"), clave(principal="0.10"))

    def test_las_invocaciones_distintas_conservan_claves_distintas(self):
        referencia = clave()
        distintos = (
            {"principal": "2001"},
            {"principal": "2000", "years": 2},
            {"principal": "2000", "method": "simple"},
            {"principal": "2000", "annual_rate_percent": "4"},
            {"principal": "2000", "inflation_percent": "3"},
            {"principal": "2000", "monthly_contribution": "100"},
        )
        for cambio in distintos:
            with self.subTest(cambio=cambio):
                self.assertNotEqual(clave(**cambio), referencia,
                                    f"{cambio} no es el mismo cálculo")

    def test_un_decimal_invalido_no_revienta_la_clave(self):
        # La validación de argumentos ya lo rechaza antes; aquí solo se exige que la
        # construcción de la clave no lance (si lanzara, el turno moriría por otra
        # vía). Se conserva el valor literal en la clave.
        for malo in ("no-es-un-numero", "", "1,5"):
            with self.subTest(valor=malo):
                self.assertEqual(clave(principal=malo), clave(principal=malo))


class RunnerReutilizaLaInvocacionTests(unittest.TestCase):
    """El runner, no solo la clave: el turno termina con texto y una ejecución."""

    def resultado(self, saldo):
        return tool_result("calculate_scenario", data={
            "hypothetical": True,
            "not_prediction": True,
            "currency": "EUR",
            "assumptions": {
                "principal": "2000.00", "monthly_contribution": "0.00",
                "annual_rate_percent": "3", "inflation_percent": "2", "years": 1,
                "method": "compound", "annual_rate_convention": "effective_annual_rate",
                "monthly_contribution_timing": "end_of_month",
                "taxes_included": False, "fees_included": False,
            },
            "summary": {"contributions": "2000.00", "final_balance": saldo,
                        "interest": "60.00", "inflation_adjusted": "2000.00"},
        })

    def test_dos_llamadas_equivalentes_en_el_mismo_lote_ejecutan_una_y_contestan(self):
        dispatcher = TestOnlyDispatcher([self.resultado("2060.00")])
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (
                ToolCall("call_a", "calculate_scenario", escenario(principal="2000")),
                ToolCall("call_b", "calculate_scenario", escenario(principal="2000.00")),
            ), "tool_calls"),
            ChatResult("El escenario da 2.060,00 EUR.", None, (), "stop"),
        ])

        result = ToolChatRunner(provider, dispatcher).run([
            {"role": "user", "content": "TEST ONLY: calcula 2000 al 3 % un año."},
        ])

        # Una sola ejecución: el resultado del mismo cálculo se reaprovecha.
        self.assertEqual(len(dispatcher.calls), 1, dispatcher.calls)
        # Y las dos llamadas constan como atendidas, con su propia respuesta.
        self.assertEqual([event["state"] for event in result["tool_events"]],
                         ["executed", "executed"])
        self.assertEqual([event["tool_call_id"] for event in result["tool_events"]],
                         ["call_a", "call_b"])
        # El turno termina con texto, no con `tool_error`.
        self.assertEqual(result["finish_reason"], "stop")
        self.assertIn("2.060,00", result["answer"])
        # El proveedor recibió contestadas sus dos llamadas.
        segundo = provider.requests[1]["messages"]
        self.assertEqual([m["tool_call_id"] for m in segundo if m["role"] == "tool"],
                         ["call_a", "call_b"])

    def test_dos_llamadas_distintas_en_el_mismo_lote_ejecutan_las_dos(self):
        dispatcher = TestOnlyDispatcher([self.resultado("2060.00"),
                                         self.resultado("4120.00")])
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (
                ToolCall("call_a", "calculate_scenario", escenario(principal="2000")),
                ToolCall("call_b", "calculate_scenario", escenario(principal="4000")),
            ), "tool_calls"),
            ChatResult("Los dos escenarios están calculados.", None, (), "stop"),
        ])

        result = ToolChatRunner(provider, dispatcher).run([
            {"role": "user", "content": "TEST ONLY: dos escenarios distintos."},
        ])

        # Dos invocaciones de verdad: se ejecutan las dos. Colapsarlas daría al
        # usuario el resultado del cálculo equivocado.
        self.assertEqual([llamada[1] for llamada in dispatcher.calls],
                         [escenario(principal="2000"), escenario(principal="4000")])
        self.assertEqual([event["state"] for event in result["tool_events"]],
                         ["executed", "executed"])
        self.assertEqual(result["finish_reason"], "stop")

    def test_el_calculo_equivalente_en_otra_ronda_tambien_se_reutiliza(self):
        dispatcher = TestOnlyDispatcher([self.resultado("2060.00")])
        provider = TestOnlyFakeProvider([
            ChatResult("", None, (
                ToolCall("call_a", "calculate_scenario", escenario(principal="2000")),
            ), "tool_calls"),
            ChatResult("", None, (
                ToolCall("call_b", "calculate_scenario", escenario(principal="2000.00")),
            ), "tool_calls"),
            ChatResult("El resultado sigue siendo 2.060,00 EUR.", None, (), "stop"),
        ])

        result = ToolChatRunner(provider, dispatcher).run([
            {"role": "user", "content": "TEST ONLY: insiste con el mismo cálculo."},
        ])

        self.assertEqual(len(dispatcher.calls), 1)
        self.assertEqual(len(provider.requests), 3)
        self.assertEqual(result["finish_reason"], "stop")
        self.assertIn("2.060,00", result["answer"])


if __name__ == "__main__":
    unittest.main()
