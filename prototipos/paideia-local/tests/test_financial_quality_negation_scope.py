"""Offline scoped-negation regressions; empty flags are not approval."""
import unittest

from financial_quality import assess_financial_text


class FinancialQualityNegationScopeTests(unittest.TestCase):
    def test_unrelated_prefix_negation_does_not_hide_claim(self):
        self.assertEqual(assess_financial_text('No tengo deudas y ahorrar es sin riesgo.'), ('ABSOLUTE_NO_RISK',))

    def test_unrelated_predicate_negation_does_not_hide_claim(self):
        self.assertEqual(assess_financial_text('Ahorrar no requiere esfuerzo y es sin riesgo.'), ('ABSOLUTE_NO_RISK',))

    def test_postposed_denial(self):
        self.assertEqual(assess_financial_text('Ahorrar sin riesgo no es posible.'), ())

    def test_adversative_prefix_does_not_hide_claim(self):
        self.assertEqual(assess_financial_text('No tengo deudas, pero ahorrar es sin riesgo.'), ('ABSOLUTE_NO_RISK',))

    def test_unrelated_negation_without_conjunction(self):
        for text in ('No tengo dudas de que ahorrar es sin riesgo.',
                     'Ahorrar no requiere esfuerzo para ser sin riesgo.'):
            with self.subTest(text=text):
                self.assertEqual(assess_financial_text(text), ('ABSOLUTE_NO_RISK',))

    def test_preserves_known_denials_and_refutations(self):
        for text in (
            'No es correcto afirmar que ahorrar es sin riesgo',
            'Ahorrar no es guardar dinero sin riesgo',
            'Ni ahorrar ni invertir están totalmente libres de riesgo',
            'La frase «ahorrar es guardar dinero sin riesgo» es una simplificación que debe evitarse',
        ):
            with self.subTest(text=text):
                self.assertEqual(assess_financial_text(text), ())
