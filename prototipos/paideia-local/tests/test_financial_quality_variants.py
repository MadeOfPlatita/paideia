"""Offline lexical guard regressions; no flag does not imply approval."""
import unittest

from financial_quality import assess_financial_text


class FinancialQualityVariantsTests(unittest.TestCase):
    def test_known_absolute_variants_and_bypasses(self):
        for text in (
            'El ahorro está libre de riesgo de pérdida de capital.',
            'Ahorrar no conlleva ningún riesgo.',
            'Ahorrar es guardar dinero sin\u200briesgo.',
            'Tu ahorro está totalmente libre de riesgos.',
            'Ahorrar es guardar dinero sin riesgo y no debes preocuparte.',
            "Ahorrar es 'guardar dinero sin riesgo'.",
        ):
            with self.subTest(text=text):
                self.assertEqual(assess_financial_text(text), ('ABSOLUTE_NO_RISK',))

    def test_negated_refuted_and_hypothetical_claims(self):
        for text in (
            'Ahorrar no es guardar dinero sin riesgo',
            'Es incorrecto decir que ahorrar es guardar dinero sin riesgo',
            'La frase «ahorrar es guardar dinero sin riesgo» es una simplificación que debe evitarse',
            'Ni ahorrar ni invertir están totalmente libres de riesgo',
            'Si ahorrar fuera sin riesgo, no existirían pérdidas.',
            'Ahorrar podría ser sin riesgo en una hipótesis.',
        ):
            with self.subTest(text=text):
                self.assertEqual(assess_financial_text(text), ())

    def test_normalization_does_not_change_input(self):
        text = 'Ahorrar es guardar dinero sin\u200briesgo.'
        assess_financial_text(text)
        self.assertEqual(text, 'Ahorrar es guardar dinero sin\u200briesgo.')
