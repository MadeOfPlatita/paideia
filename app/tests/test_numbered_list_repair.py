"""Una lista numerada no puede quedar con números huérfanos.

CASO REAL, visto en producción al responder «Me ofrecen un depósito al 4 % a 18
meses». La respuesta traía seis pasos numerados; cuatro llevaban cifras que no se
pudieron respaldar y se descartaron. Lo que llegó al usuario fue:

    1. Pide las dos cifras por escrito. 2. 3. 4. 5. 6. **Vinculaciones.** Si
    exigen nómina.

Los números sin texto parecen un fallo de la aplicación, y tapan que el contenido se
había quitado a propósito.

La regla: al quitar frases con cifras, el número que las encabezaba se va con ellas y
la lista se renumera. Una lista correcta no se toca.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _redact_unbacked_figures, _renumber  # noqa: E402


class NumberedListRepairTests(unittest.TestCase):
    def test_orphan_numbers_are_removed_and_the_list_renumbered(self):
        # El texto tal como llega al reparador: números sin contenido detrás.
        roto = "1. Pide las cifras. 2. 3. 4. 5. 6. **Vinculaciones.** Si exigen nómina."
        reparado = _renumber(roto)
        self.assertNotIn("2. 3.", reparado)
        self.assertIn("1. Pide las cifras.", reparado)
        self.assertIn("2. **Vinculaciones.**", reparado)

    def test_a_correct_list_is_untouched(self):
        correcta = "1. Mira el plazo. 2. Mira la liquidez. 3. Mira la fiscalidad."
        self.assertEqual(_renumber(correcta), correcta)

    def test_text_without_a_list_is_untouched(self):
        texto = "El tipo del 3 % es bajo para ese plazo."
        self.assertEqual(_renumber(texto), texto)

    def test_the_real_response_loses_the_dangling_numbers(self):
        # Respuesta real con seis pasos, cuatro de ellos con cifras sin respaldo.
        real = (
            "Lo que revisaría antes de firmar: "
            "1. Pide las dos cifras por escrito. "
            "2. **Tipo por tramos.** Ofrecen un 4 % promocional. "
            "3. **Liquidez.** Cancelación con un 2 %. "
            "4. **Fiscalidad.** Tributan al 19 %. "
            "5. **Vencimiento.** Se renueva a un 1 %. "
            "6. **Vinculaciones.** Si exigen nómina."
        )
        limpio, quitadas = _redact_unbacked_figures(real)
        self.assertGreater(quitadas, 0)
        # Lo que no puede quedar: números consecutivos sin texto.
        self.assertNotRegex(limpio, r"\d\.\s+\d\.",
                            f"quedaron números huérfanos: {limpio!r}")
        # Y lo que sí se conserva.
        self.assertIn("Pide las dos cifras", limpio)
        self.assertIn("Vinculaciones", limpio)
        # Las cifras inventadas no se publican.
        self.assertNotIn("19 %", limpio)
        self.assertNotIn("4 % promocional", limpio)

    def test_a_single_number_is_not_a_list(self):
        texto = "Es el paso 3. Y nada más."
        self.assertEqual(_renumber(texto), texto)


if __name__ == "__main__":
    unittest.main()
