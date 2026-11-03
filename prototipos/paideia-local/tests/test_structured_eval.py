import unittest

class SyntheticEvalTests(unittest.TestCase):
    def test_reports_contract_and_label_relevance_separately_without_winner(self):
        from structured_eval import evaluate
        result = evaluate()
        self.assertEqual(result['label'], 'synthetic_test_only')
        self.assertEqual(result['cases'], 4)
        self.assertEqual(result['contract_valid'], 3)
        self.assertEqual(result['relevant_among_valid'], 2)
        self.assertIsNone(result['winner'])
        self.assertNotIn('model_quality', result)
