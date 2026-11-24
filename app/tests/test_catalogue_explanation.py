"""La explicación del modelo acompaña a los datos, nunca los sustituye.

Antes, cuando el turno usaba el catálogo, la prosa del modelo se descartaba
entera: el usuario recibía el listado de cifras y nada que le orientara. Ahora se
limpia (sin cifras ni atribuciones) y se coloca detrás de los datos verificados.

La regla que no se puede romper: **las cifras solo salen de la ficha**. Si la
prosa del modelo trae un número, esa frase desaparece; si no queda nada, no se
añade nada.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _catalogue_explanation  # noqa: E402
from catalogue_answer import compose_catalogue_answer  # noqa: E402

FICHA = {"used": True, "products": [{
    "id": "DEP-EBN-12",
    "name": "Depósito Nuevo Ahorro 12 meses",
    "issuer": "EBN Banco",
    "conditions": [{"metric": "annual_rate_percent", "state": "known",
                    "value": "3.1", "unit": "PERCENT",
                    "sources": [{"url": "https://www.ebnbanco.com/x"}]}],
}]}


class ExplanationTests(unittest.TestCase):
    def test_a_sharp_rate_in_the_model_text_is_removed(self):
        # «9,99 %» no está en la ficha: esa frase no puede sobrevivir.
        texto = _catalogue_explanation(
            "Este depósito es interesante. Paga un 9,99 % y además es seguro.")
        if texto is not None:
            self.assertNotIn("9,99", texto)

    def test_a_purely_conceptual_explanation_survives(self):
        limpio = _catalogue_explanation(
            "Conviene mirar el plazo y si puedes cancelar antes sin coste.")
        self.assertIsNotNone(limpio)
        assert limpio is not None
        self.assertIn("plazo", limpio)

    def test_an_empty_or_missing_answer_yields_nothing(self):
        for valor in (None, "", "   ", 42, {}):
            with self.subTest(valor=repr(valor)):
                self.assertIsNone(_catalogue_explanation(valor))

    def test_the_explanation_goes_after_the_verified_data(self):
        texto = compose_catalogue_answer(
            FICHA, explanation="Mira el plazo antes de contratar.")
        assert texto is not None
        posicion_dato = texto.index("3,1 %")
        posicion_explicacion = texto.index("Mira el plazo")
        self.assertLess(posicion_dato, posicion_explicacion,
                        "los datos verificados van primero")
        self.assertIn("no una oferta ni una recomendación", texto)

    def test_without_explanation_the_answer_is_just_the_data(self):
        texto = compose_catalogue_answer(FICHA)
        assert texto is not None
        self.assertIn("3,1 %", texto)
        self.assertNotIn("Mira el plazo", texto)


if __name__ == "__main__":
    unittest.main()
