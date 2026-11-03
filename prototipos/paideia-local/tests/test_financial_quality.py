"""TEST ONLY fixtures; absence of flags is not quality approval."""
import unittest
from financial_quality import assess_financial_text
from test_financial_quality_integration import REAL_REPLAY

class FinancialQualityTests(unittest.TestCase):
    def test_explicit_absolute_claims(self):
        for text in (REAL_REPLAY, 'Ahorrar es guardar dinero sin riesgo.', 'Invertir es siempre sin riesgo.', 'El capital está garantizado sin riesgo.'):
            with self.subTest(text=text): self.assertEqual(assess_financial_text(text), ('ABSOLUTE_NO_RISK',))
    def test_negation_refuted_quotes_and_conditional(self):
        for text in ('Ahorrar no es sin riesgo.', 'No es cierto que ahorrar sea sin riesgo.', 'Decir «ahorrar es sin riesgo» es falso.', 'Si ahorrar fuera sin riesgo, no existirían pérdidas.', 'Ahorrar puede implicar riesgos de custodia y pérdida de poder adquisitivo.'):
            with self.subTest(text=text): self.assertEqual(assess_financial_text(text), ())
    def test_quote_does_not_hide_independent_assertion(self):
        self.assertEqual(assess_financial_text('«Ahorrar es sin riesgo» es falso. Invertir es sin riesgo.'), ('ABSOLUTE_NO_RISK',))
