"""Una cifra de producto inventada no puede colarse como «ejemplo educativo».

Caso real medido en la interfaz, con el historial ya activo. El turno 1 pedía el
TAE del depósito de EBN a 12 meses; el turno 2 preguntaba «¿y si lo dejo 24
meses?». El modelo respondió:

    «A modo de ejemplo, si un depósito de 12 meses tiene 3,1 % TAE, un depósito
     de 24 meses podría situarse entre 3,5 % y 4 %»

Ese 3,5 % no existe en ninguna ficha: es una TAE inventada para un producto que
el catálogo no tiene. Se colaba porque la frase llevaba «a modo de ejemplo» y
`_is_labelled_reference` la dejaba pasar como método.

La causa: `_PRODUCT_SUBJECT` solo reconocía un producto cuando llevaba un
determinante demostrativo («ese depósito»), no la forma natural de nombrarlo con
su plazo («un depósito de 24 meses»).

La regla que se fija aquí: un producto con su plazo es un producto concreto; sus
cifras exigen ficha, aunque la frase diga «por ejemplo».
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _catalogue_explanation  # noqa: E402

INVENTADA = (
    "A modo de ejemplo, si un depósito de 12 meses tiene 3,1 % TAE, un depósito "
    "de 24 meses podría situarse entre 3,5 % y 4 % (esto depende de la política "
    "de cada banco)."
)
INVENTADA_FONDO = (
    "Por ejemplo, un fondo de renta variable a 3 años podría dar un 6 % anual."
)

# Prosa de método legítima: no nombra un producto concreto, orienta.
METODO = (
    "Conviene mirar el plazo y si puedes cancelar antes sin coste. "
    "Antes de contratar, comprueba la ficha del producto."
)
GENERICA = (
    "Como referencia general del sector, varios meses de gastos cubren un "
    "imprevisto."
)


class ProductFigureLeakTests(unittest.TestCase):
    def test_an_invented_rate_for_a_product_with_a_term_is_dropped(self):
        self.assertIsNone(_catalogue_explanation(INVENTADA),
                          "una TAE inventada para un depósito a 24 meses no puede publicarse")

    def test_the_same_happens_with_a_fund_and_a_horizon(self):
        limpio = _catalogue_explanation(INVENTADA_FONDO)
        if limpio is not None:
            self.assertNotIn("6 %", limpio,
                             "un 6 % para un fondo concreto es una cifra sin ficha")

    def test_a_method_explanation_survives(self):
        limpio = _catalogue_explanation(METODO)
        self.assertIsNotNone(limpio)
        assert limpio is not None
        self.assertIn("plazo", limpio)

    def test_a_general_reference_survives(self):
        limpio = _catalogue_explanation(GENERICA)
        self.assertIsNotNone(limpio, "una referencia general del sector es legítima")

    def test_the_good_part_of_a_mixed_text_is_kept(self):
        # La primera frase es método; la segunda lleva la cifra inventada.
        mezcla = ("La TAE suele aumentar con el plazo. " + INVENTADA)
        limpio = _catalogue_explanation(mezcla)
        if limpio is not None:
            self.assertNotIn("3,5", limpio)
            self.assertNotIn("4 %", limpio)


if __name__ == "__main__":
    unittest.main()
