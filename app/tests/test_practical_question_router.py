"""Las preguntas de consejo no deben acabar en un listado de productos.

Fallo medido en producción, con el catálogo ya funcionando: dos preguntas que
pedían criterio abrían las herramientas y la respuesta se convertía en una lista
de fichas.

- «Tengo una deuda de tarjeta al 20 % y 3000 euros ahorrados. ¿Qué hago
  primero?» devolvía los depósitos de Renault Bank, Openbank y Pibank. La
  respuesta correcta es que amortizar esa deuda es la mejor rentabilidad libre de
  riesgo disponible.
- «Dime una TAE garantizada del 8 % para el año que viene» devolvía una cuenta
  remunerada al 1,5 %. Lo correcto es decir que ese 8 % garantizado no existe.

La causa era `_is_practical_question`: no reconocía «qué hago primero» ni una
petición de garantía como petición de criterio, así que abría el catálogo.

Estas pruebas fijan las dos orillas: las de consejo van sin herramientas y las de
producto las conservan. Si alguien toca el patrón, salta aquí.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _is_practical_question  # noqa: E402

# Piden criterio: sin catálogo.
CONSEJO = (
    "Tengo una deuda de tarjeta al 20 % y 3000 euros ahorrados. ¿Qué hago primero?",
    "Dime una TAE garantizada del 8 % para el año que viene",
    "Tengo 5000 euros y quiero algo seguro. ¿Qué opciones tengo?",
    "¿Cómo reparto mis ingresos mensuales?",
    "¿Qué me recomiendas para ahorrar?",
    "¿Qué es lo mejor para mí con 30 años?",
    "¿Qué priorizo: deuda o ahorro?",
    "¿Cómo empiezo a invertir desde cero?",
)

# Piden el dato de un producto: con catálogo.
PRODUCTO = (
    "¿Qué TAE tiene el depósito de EBN Banco?",
    "¿Qué productos de depósito hay en el catálogo?",
    "Compara el depósito de EBN con el de Self Bank",
    "¿Cuál es el TER del ETF de iShares Core MSCI Europe?",
    "¿Qué letras del Tesoro tienes?",
    "¿Qué comisiones tiene el fondo Olea Neutral?",
)


class PracticalQuestionTests(unittest.TestCase):
    def test_advice_questions_do_not_open_the_catalogue(self):
        for pregunta in CONSEJO:
            with self.subTest(pregunta=pregunta):
                self.assertTrue(_is_practical_question(pregunta),
                                "debería responder sin catálogo, no con un listado")

    def test_product_questions_keep_the_catalogue(self):
        for pregunta in PRODUCTO:
            with self.subTest(pregunta=pregunta):
                self.assertFalse(_is_practical_question(pregunta),
                                 "necesita las herramientas para dar el dato")

    def test_a_non_string_is_not_practical(self):
        self.assertFalse(_is_practical_question(None))
        self.assertFalse(_is_practical_question(42))


if __name__ == "__main__":
    unittest.main()
