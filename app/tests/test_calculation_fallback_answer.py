"""Si el motor calculó, el usuario no puede quedarse con un hueco.

CASO REAL medido en la batería contra producción, dos veces:

    «Si meto 5000 euros al 3 % durante 2 años, ¿cuánto tendré?»
    «Me ofrecen un depósito al 4 % a 18 meses. ¿Es buena idea?»
    -> HTTP 200, answer = "" (cero caracteres), state = withheld_unbacked_claim
    -> calculate_scenario ejecutado

El turno hizo su trabajo: calculó con el motor determinista. La prosa del modelo se
retuvo por una atribución sin respaldo, y con ella se tiró también el resultado del
motor, que no depende del modelo y es dato local exacto.

LA PRIMERA VERSIÓN DE ESTE ARREGLO NO SERVÍA. La función buscaba `result` con
`final_amount` / `contributed`, claves que **no existen**: el DTO real trae `summary`
con `final_balance`, `interest`, `contributions` e `inflation_adjusted`, más
`assumptions` y `disclaimer`. Devolvía None siempre, así que el hueco seguía ahí y el
test pasaba porque también usaba las claves inventadas.

Estas pruebas usan el DTO **real**, capturado de la respuesta de producción y del
dispatcher, no una forma supuesta.

La regla: un hueco nunca es mejor que los datos.
"""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from backend_services import _calculation_answer  # noqa: E402

# DTO tal como lo devuelve producción para 5.000 € al 3 % a 2 años.
CALCULO_REAL = {
    "hypothetical": True,
    "not_prediction": True,
    "currency": "EUR",
    "assumptions": {
        "principal": "5.000,00",
        "monthly_contribution": "0.00",
        "annual_rate_percent": "3",
        "inflation_percent": "0",
        "years": 2,
        "method": "simple",
        "annual_rate_convention": "simple_annual_rate",
        "monthly_contribution_timing": "end_of_month",
        "taxes_included": False,
        "fees_included": False,
    },
    "summary": {
        "contributions": "5.000,00",
        "final_balance": "5.300,00",
        "interest": "300,00",
        "inflation_adjusted": "5.300,00",
    },
    "disclaimer": ("Escenario hipotético calculado por el motor determinista local; "
                   "no es una predicción ni una oferta."),
}


class CalculationFallbackTests(unittest.TestCase):
    def test_the_real_dto_becomes_an_answer(self):
        respuesta = _calculation_answer(CALCULO_REAL)
        self.assertIsNotNone(respuesta, "el DTO real de producción debe componer respuesta")
        assert respuesta is not None
        # Las cifras que el usuario necesita.
        self.assertIn("5.300,00", respuesta)
        self.assertIn("300,00", respuesta)
        # Y de dónde salen.
        self.assertIn("motor local", respuesta)
        # Se cuenta en una frase, no con las etiquetas «Capital final:» /
        # «Intereses:» en líneas sueltas: medido en pantalla, eso es exactamente lo
        # que se lee como una tabla y no como una respuesta.
        self.assertIn("acabas con 5.300,00 €", respuesta)
        self.assertIn("300,00 € de intereses", respuesta)
        self.assertNotIn("Capital final:", respuesta)

    def test_the_assumptions_travel_with_the_result(self):
        respuesta = _calculation_answer(CALCULO_REAL)
        assert respuesta is not None
        self.assertIn("5.000,00", respuesta)
        self.assertIn("3,00 %", respuesta)
        self.assertIn("2 años", respuesta)

    def test_the_disclaimer_is_kept(self):
        respuesta = _calculation_answer(CALCULO_REAL)
        assert respuesta is not None
        self.assertIn("no es una predicción", respuesta)

    def test_an_empty_calculation_is_not_invented(self):
        self.assertIsNone(_calculation_answer(None))
        self.assertIsNone(_calculation_answer([]))
        self.assertIsNone(_calculation_answer({}))
        self.assertIsNone(_calculation_answer({"summary": {}}))
        # Las claves que la primera versión buscaba y que NO existen: si solo llegan
        # esas, no hay nada que publicar (esto es lo que fallaba en silencio).
        self.assertIsNone(_calculation_answer(
            {"result": {"final_amount": 4321.5, "contributed": 4000.0}}))

    def test_a_compound_calculation_also_works(self):
        compuesto = dict(CALCULO_REAL)
        compuesto["summary"] = {"contributions": "5.000,00", "final_balance": "5.304,50",
                                "interest": "304.50", "inflation_adjusted": "5.304,50"}
        respuesta = _calculation_answer(compuesto)
        assert respuesta is not None
        self.assertIn("5.304,50", respuesta)


if __name__ == "__main__":
    unittest.main()
