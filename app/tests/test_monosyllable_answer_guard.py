"""Un monosílabo no es una respuesta.

CASO REAL, medido en la batería de 53 preguntas contra producción. La pregunta era
solo la letra «a» — un mensaje que llega incompleto, como teclear sin querer — y el
modelo contestó:

    «No»

Dos caracteres. La persona se queda sin saber si la aplicación funciona, si su
mensaje se envió o si tiene que reformular. Un «No» seco es peor que un error,
porque parece una decisión.

Se arregla en dos niveles:
  1. El prompt pide (categoría 6) decir que el mensaje llegó incompleto, repetirlo
     entre comillas y ofrecer qué sí se puede hacer.
  2. Una red en el servidor: por debajo de ocho caracteres se devuelve un motivo en
     vez del monosílabo.

Ocho y no más: un «No sé» o un «Depende» son cortos pero legítimos, y el umbral no
debe convertir en error una respuesta breve correcta.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import _MIN_USEFUL_ANSWER_CHARS, _too_short_to_help  # noqa: E402

# Respuestas que NO son útiles: se sustituyen por un motivo.
MONOSILABOS = ("No", "Sí", "Nop", "Ok", "?", "a", "No.")

# Respuestas cortas pero legítimas: se respetan.
CORTAS_VALIDAS = ("No sé.", "Depende.", "No lo sé", "Falta el dato.")


class MonosyllableGuardTests(unittest.TestCase):
    def test_a_monosyllable_is_not_a_useful_answer(self):
        for texto in MONOSILABOS:
            with self.subTest(texto=texto):
                self.assertTrue(_too_short_to_help(texto),
                                f"«{texto}» no puede llegar como respuesta")

    def test_a_short_but_valid_answer_is_respected(self):
        for texto in CORTAS_VALIDAS:
            with self.subTest(texto=texto):
                self.assertFalse(_too_short_to_help(texto),
                                 f"«{texto}» es corto pero válido")

    def test_an_empty_answer_is_handled_by_the_empty_guard(self):
        # El vacío tiene su propio guard (CHAT_EMPTY_ANSWER); este no debe pisarlo.
        for texto in ("", "   ", "\n"):
            with self.subTest(texto=repr(texto)):
                self.assertFalse(_too_short_to_help(texto))

    def test_a_normal_answer_passes(self):
        self.assertFalse(_too_short_to_help(
            "La TAE es el coste anual efectivo de un producto financiero."))

    def test_synthetic_test_text_is_not_blocked(self):
        # Las pruebas de integración usan respuestas como «TEST ONLY»; no son
        # respuestas al usuario y no deben disparar el guard.
        self.assertFalse(_too_short_to_help("TEST ONLY"))

    def test_the_threshold_is_small(self):
        # Si el umbral creciera, empezaria a rechazar respuestas correctas.
        self.assertLessEqual(_MIN_USEFUL_ANSWER_CHARS, 10)


if __name__ == "__main__":
    unittest.main()
