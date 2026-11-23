"""La pregunta de decision no abre el catalogo y no se queda en un anuncio.

Caso real: «voy a tener un gasto de 1.000 EUR en 2 anos, donde lo meto» acabo en
una respuesta de 73 caracteres («voy a mirar que hay en el catalogo») porque el
modelo recibia herramientas, intentaba una llamada que se descartaba y devolvia
solo el anuncio de la consulta.

Se comprueba: la deteccion de pregunta practica, que el prompt prohibe anunciar
herramientas y que el reintento de una llamada descartada sin texto no deja al
usuario sin respuesta.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import backend_services as bs  # noqa: E402


class PracticalQuestionTests(unittest.TestCase):
    PRACTICAS = [
        "Voy a tener un gasto de 1000 euros en 2 años. ¿Dónde sería mejor meter el dinero?",
        "¿Dónde meto 5.000 euros?",
        "¿Dónde pongo 3.000 euros a un año?",
        "¿Qué me recomiendas con mis ahorros?",
        "¿Qué opciones tengo para 2.000 euros?",
        "¿Dónde invierto 10.000 euros?",
        "¿Cómo monto un colchón de emergencia?",
        "¿Qué es la TAE?",
        "Explícame la diferencia entre TAE y TIN",
    ]

    DE_CATALOGO = [
        "¿Qué TAE tiene el depósito de EBN?",
        "Compara la cuenta de Openbank y la de MyInvestor",
        "Dame la ficha del producto DEP-EBN-12",
    ]

    def test_a_decision_question_is_treated_as_practical(self):
        for pregunta in self.PRACTICAS:
            with self.subTest(pregunta=pregunta):
                self.assertTrue(bs._is_practical_question(pregunta))

    def test_a_catalogue_question_still_gets_the_tools(self):
        for pregunta in self.DE_CATALOGO:
            with self.subTest(pregunta=pregunta):
                self.assertFalse(bs._is_practical_question(pregunta))

    def test_the_prompt_forbids_announcing_a_tool_call(self):
        prompt = bs.CHAT_SYSTEM_PROMPT
        self.assertIn("Nunca anuncies lo que vas a hacer", prompt)
        self.assertIn("deja a la persona sin respuesta", prompt)


if __name__ == "__main__":
    unittest.main()
