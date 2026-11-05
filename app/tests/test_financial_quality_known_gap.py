"""Blocking regression discovered after the bounded offline fix loop.
Do not mark expectedFailure or skip merely to obtain a green suite.
"""
import unittest
from financial_quality import assess_financial_text

class KnownNegationGapTests(unittest.TestCase):
    def test_prefix_denial_does_not_become_a_risk_free_promise(self):
        self.assertEqual(assess_financial_text('No es posible ahorrar sin riesgo.'), ())

    def test_untrusted_comma_separated_assertion_never_enters_structured_content(self):
        from structured_education import render_selection
        untrusted = 'No es posible tener deudas, ahorrar es sin riesgo.'
        with self.assertRaises(ValueError):
            render_selection({'version': 'paideia-education-v1', 'intent': 'explain',
                              'claim_ids': ['risk'], 'answer': untrusted})
        result = render_selection({'version': 'paideia-education-v1', 'intent': 'explain',
                                   'claim_ids': ['risk']})
        self.assertNotIn(untrusted, result['answer'])
        self.assertFalse(result['external_sent'])
