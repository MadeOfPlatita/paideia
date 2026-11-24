"""El XML de una llamada a herramienta no puede llegar nunca al usuario.

CASO REAL, medido dos veces en la batería contra producción. El modelo respondió
literalmente:

    <tool_call> {"name":"search_products","arguments":{"query":"VanEck Semiconductor"}} </tool_call>

y en otro turno:

    <tool_use> {"name": "search_products", "input": {"query": "depósito a plazo"}} </tool_use>

El `finish_reason` vino como «stop», no como «tool_calls», así que el servidor no
ejecutó ninguna búsqueda y sirvió ese XML como respuesta al usuario. Doble daño: el
usuario lee basura técnica y la consulta que pedía nunca se hizo.

Se detecta y se quita. Si el turno entero era la llamada, se avisa con un motivo en
vez de devolver vacío o XML.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _looks_like_tool_attempt, _strip_tool_attempts  # noqa: E402

CASOS_REALES = (
    '<tool_call> {"name":"search_products","arguments":{"query":"VanEck Semiconductor"}} </tool_call>',
    '<tool_use> {"name": "search_products", "input": {"query": "depósito a plazo"}} </tool_use>',
    '<function_call>{"name":"get_product_detail"}</function_call>',
    '<invoke name="search_products"></invoke>',
)


class ToolCallAsTextTests(unittest.TestCase):
    def test_the_real_cases_are_detected(self):
        for texto in CASOS_REALES:
            with self.subTest(texto=texto[:40]):
                self.assertTrue(_looks_like_tool_attempt(texto))

    def test_a_pure_tool_attempt_leaves_nothing(self):
        # Sin resto: el servicio avisa de que la consulta no se ejecutó.
        for texto in CASOS_REALES:
            with self.subTest(texto=texto[:40]):
                self.assertEqual(_strip_tool_attempts(texto), "")

    def test_prose_around_the_attempt_is_kept(self):
        mezcla = ('Mira la ficha. <tool_call>{"name":"get_product_detail"}</tool_call> '
                  'Y comprueba el plazo antes de contratar.')
        limpio = _strip_tool_attempts(mezcla)
        self.assertIn("Mira la ficha", limpio)
        self.assertIn("comprueba el plazo", limpio)
        self.assertNotIn("tool_call", limpio)

    def test_normal_text_is_untouched(self):
        texto = "La TAE es el tipo anual equivalente. No confundas TAE con TIN."
        self.assertFalse(_looks_like_tool_attempt(texto))
        self.assertEqual(_strip_tool_attempts(texto), texto)

    def test_a_mention_of_the_word_is_not_a_call(self):
        # Explicar qué es una herramienta no puede disparar la detección.
        texto = "El asistente usa una herramienta para consultar el catálogo."
        self.assertFalse(_looks_like_tool_attempt(texto))


if __name__ == "__main__":
    unittest.main()
