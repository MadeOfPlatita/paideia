"""La guarda financiera no rechaza frases que ensenan que el riesgo existe.

Falso positivo medido en produccion: «¿Que es la diversificacion?» devolvia
HTTP 502 CHAT_FINANCIAL_QUALITY_REJECTED porque la respuesta contenia frases
CORRECTAS como «ninguna inversion es libre de riesgos» o «un ahorro sin riesgos
no existe». La guarda las leia como la afirmacion peligrosa.

Estas pruebas fijan los dos lados: lo que debe pasar y lo que debe rechazarse.
Cuando una frase es ambigua, se prefiere rechazarla (fail closed): un falso
positivo cuesta una explicacion, un falso negativo publica una promesa falsa.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from financial_quality import assess_financial_text  # noqa: E402


class RefutationPassesTests(unittest.TestCase):
    """Frases correctas que niegan el riesgo absoluto: deben pasar."""

    FRASES = (
        "La diversificación no elimina el riesgo, pero reduce la exposición a un solo activo.",
        "Diversificar no es una inversión libre de riesgo.",
        "Ninguna inversión es libre de riesgos.",
        "Un ahorro sin riesgos no existe.",
        "Tampoco existe una inversión libre de riesgo.",
        "El ahorro no está libre de riesgos por la inflación.",
        "La inversión diversificada no es libre de riesgo.",
    )

    def test_a_false_positive_does_not_block_the_answer(self):
        for frase in self.FRASES:
            with self.subTest(frase=frase):
                self.assertEqual(assess_financial_text(frase), (), frase)


class AssertionIsRejectedTests(unittest.TestCase):
    """Promesas de ausencia de riesgo: deben rechazarse."""

    FRASES = (
        "Invertir en ese fondo es una inversión sin riesgos.",
        "El ahorro es capital libre de riesgo.",
        "Invertir no conlleva ningún riesgo.",
        "Tu inversión está libre de riesgos.",
        "El ahorro garantiza capital sin riesgo.",
        "El ahorro no tiene ningún riesgo.",
        "Invertir es una inversión sin riesgo.",
        "El capital invertido tiene cero riesgo.",
        "Ahorrar implica una inversión libre de riesgo.",
        "Invertir supone cero riesgo.",
    )

    def test_a_promise_of_no_risk_is_flagged(self):
        for frase in self.FRASES:
            with self.subTest(frase=frase):
                self.assertEqual(assess_financial_text(frase), ("ABSOLUTE_NO_RISK",), frase)


class BoundaryTests(unittest.TestCase):
    def test_text_without_the_pattern_is_not_flagged(self):
        for frase in ("La TAE normaliza el coste anual.",
                      "El TIN no incluye comisiones.",
                      "Un depósito a plazo tiene riesgo de liquidez."):
            with self.subTest(frase=frase):
                self.assertEqual(assess_financial_text(frase), ())

    def test_a_refuted_claim_inside_a_longer_text_does_not_block_it(self):
        texto = ("Diversificar reparte el dinero entre activos distintos. "
                 "Ninguna inversión es libre de riesgos, pero la diversificación "
                 "reduce el riesgo específico de un solo valor.")
        self.assertEqual(assess_financial_text(texto), ())

    def test_a_real_claim_inside_a_longer_text_still_blocks_it(self):
        texto = ("Puedes repartir el dinero como quieras. "
                 "Recuerda que el ahorro es capital libre de riesgo y por eso no baja nunca.")
        self.assertEqual(assess_financial_text(texto), ("ABSOLUTE_NO_RISK",))


if __name__ == "__main__":
    unittest.main()
