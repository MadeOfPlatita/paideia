"""Una cifra citada para DESMENTIRLA no se puede quitar como si fuera un dato.

CASO REAL medido en produccion. La pregunta era:

    «Dime una TAE garantizada del 8 % para el año que viene»

y la respuesta del modelo empezaba, correctamente:

    «No existe una TAE garantizada del 8 % para el año que viene, y quien te la
     ofrezca te está mintiendo. El motivo es doble. La señal de alarma...»

Lo que llegaba al usuario eran 432 caracteres empezando por «El motivo es doble.»
sin saber de qué: la guarda de cifras había borrado la primera frase por contener
«8 %» y la palabra «TAE».

La causa: la guarda no distinguía una cifra INVENTADA de un producto (que hay que
frenar) de una cifra CITADA PARA NEGARLA (que es justo la respuesta). La segunda es
del usuario, no un dato del catálogo que haya que respaldar.

La regla: desmentir una cifra no es publicarla.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _is_labelled_reference, _redact_unbacked_figures  # noqa: E402

# Frases que DESMIENTEN una cifra: deben conservarse.
DESMIENTEN = (
    "No existe una TAE garantizada del 8 % para el año que viene, y quien te la ofrezca te está mintiendo.",
    "Ningún producto puede garantizarte un 8 % anual.",
    "Nadie puede ofrecerte un 12 % sin riesgo.",
    "Ese 7 % es imposible en el escenario actual.",
    "No hay ningún depósito al 6 % hoy.",
    "Quien te prometa un 10 % fijo te está engañando.",
)

# Frases que AFIRMAN un dato de producto: deben quitarse (no cambia nada aquí).
AFIRMAN = (
    "El depósito de EBN ofrece una TAE del 3,1 %.",
    "Este fondo renta un 8 % anual garantizado por el banco.",
    "La cuenta remunerada de Openbank paga un 2,5 %.",
)


class DesmentirNoEsPublicarTests(unittest.TestCase):
    def test_a_denied_figure_survives(self):
        for frase in DESMIENTEN:
            with self.subTest(frase=frase[:48]):
                limpio, quitadas = _redact_unbacked_figures(frase)
                self.assertTrue(limpio.strip(),
                                f"una frase que desmiente la cifra no puede borrarse: {frase!r}")
                self.assertEqual(quitadas, 0)

    def test_a_denied_figure_is_labelled_as_reference(self):
        for frase in DESMIENTEN:
            with self.subTest(frase=frase[:48]):
                self.assertTrue(_is_labelled_reference(frase))

    def test_an_affirmed_product_figure_is_still_removed(self):
        for frase in AFIRMAN:
            with self.subTest(frase=frase[:48]):
                limpio, quitadas = _redact_unbacked_figures(frase)
                self.assertEqual(limpio.strip(), "",
                                 f"una cifra de producto sin fuente sigue sin publicarse: {frase!r}")

    def test_the_real_answer_keeps_its_first_sentence(self):
        # El texto medido, entero. La primera frase es la respuesta y no puede caer.
        respuesta = (
            "No existe una TAE garantizada del 8 % para el año que viene, y quien te "
            "la ofrezca te está mintiendo. El motivo es doble. La señal de alarma que "
            "deberías reconocer es la combinación de garantizado + rentabilidad alta."
        )
        limpio, _ = _redact_unbacked_figures(respuesta)
        self.assertIn("No existe una TAE garantizada", limpio)
        self.assertIn("El motivo es doble", limpio)


if __name__ == "__main__":
    unittest.main()
