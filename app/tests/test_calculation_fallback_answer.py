"""Si el motor calculó, el usuario no puede quedarse con un hueco.

CASO REAL medido en la batería contra producción:

    «Me ofrecen un depósito al 4 % a 18 meses. ¿Es buena idea?»
    -> HTTP 200, answer = "" (cero caracteres)
    -> tools ejecutadas: search_products, calculate_scenario
    -> state: withheld_unbacked_claim

El turno hizo su trabajo: buscó en el catálogo y calculó la rentabilidad. La prosa
del modelo se retuvo porque atribuía cifras sin respaldo local, y con ella se tiró
también el resultado del motor, que es dato local determinista y no depende del
modelo.

La regla: un hueco nunca es mejor que los datos. Si hay cálculo, se entrega.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _calculation_answer  # noqa: E402


class CalculationFallbackTests(unittest.TestCase):
    def test_a_real_calculation_becomes_an_answer(self):
        calculo = {
            "kind": "compound_interest",
            "result": {
                "final_amount": 4321.5,
                "interest": 321.5,
                "contributed": 4000.0,
                "annual_rate_percent": 4.0,
            },
        }
        respuesta = _calculation_answer(calculo)
        self.assertIsNotNone(respuesta)
        # El texto tiene que decir de donde sale el dato.
        self.assertIn("motor local", respuesta)
        self.assertIn("Capital final", respuesta)
        self.assertIn("4321.5", respuesta)

    def test_a_calculation_without_a_result_is_not_invented(self):
        self.assertIsNone(_calculation_answer({"kind": "compound_interest"}))
        self.assertIsNone(_calculation_answer({"result": {}}))
        self.assertIsNone(_calculation_answer(None))
        self.assertIsNone(_calculation_answer([]))

    def test_string_results_are_included(self):
        # El motor puede devolver la cifra ya formateada.
        calculo = {"result": {"final_amount": "4.321,50 EUR"}}
        respuesta = _calculation_answer(calculo)
        self.assertIsNotNone(respuesta)
        self.assertIn("4.321,50 EUR", respuesta)


if __name__ == "__main__":
    unittest.main()
