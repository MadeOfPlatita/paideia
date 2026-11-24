"""Una tabla markdown no puede llegar al usuario como texto con tuberías.

El prompt pide «sin tablas», pero el modelo las usa. La interfaz inserta el texto
literal (solo quita `**negritas**`), así que el usuario acaba viendo:

    | Elemento | Qué mirar |
    | --- | --- |
    | TAE | la tasa anual equivalente |

Medido en un turno real con historial. La tabla se convierte en una lista, que se
lee igual y no depende de que la interfaz entienda markdown.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _catalogue_explanation, _strip_markdown_tables  # noqa: E402

TABLA = """¿Qué debes mirar?
| Elemento | Qué mirar |
| --- | --- |
| TAE | la tasa anual equivalente |
| Plazo | si puedes cancelar antes |"""


class MarkdownTableTests(unittest.TestCase):
    def test_a_table_becomes_a_list(self):
        salida = _strip_markdown_tables(TABLA)
        self.assertNotIn("|", salida, "no puede quedar ninguna tubería")
        self.assertNotIn("---", salida, "la fila de separación se descarta")
        self.assertIn("- TAE: la tasa anual equivalente", salida)
        self.assertIn("- Plazo: si puedes cancelar antes", salida)

    def test_the_heading_survives(self):
        self.assertIn("¿Qué debes mirar?", _strip_markdown_tables(TABLA))

    def test_text_without_tables_is_untouched(self):
        texto = "Mira el plazo y la liquidez. Nada más."
        self.assertEqual(_strip_markdown_tables(texto), texto)

    def test_a_pipe_in_normal_prose_is_not_a_table(self):
        # Una barra suelta en una frase no debe convertirse en lista.
        texto = "Puedes comparar TAE | TIN si quieres."
        salida = _strip_markdown_tables(texto)
        self.assertIn("Puedes comparar", salida)

    def test_the_explanation_pipeline_strips_tables_too(self):
        limpio = _catalogue_explanation(TABLA)
        assert limpio is not None
        self.assertNotIn("|", limpio)


if __name__ == "__main__":
    unittest.main()
