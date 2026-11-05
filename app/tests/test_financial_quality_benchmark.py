"""TEST ONLY benchmark: no provider network calls."""
import unittest
from context_quality_benchmark import run_benchmark
from test_financial_quality_integration import REAL_REPLAY

class FinancialBenchmarkTests(unittest.TestCase):
    def test_unsafe_http_200_stops_without_publishing_answer_or_winner(self):
        calls = []
        def provider(payload):
            calls.append(payload)
            return {'status': 200, 'text': REAL_REPLAY}
        report = run_benchmark(provider, 'synthetic-test-model', test_only=True)
        self.assertEqual(report['stop_reason'], 'financial_quality_rejected')
        self.assertEqual(report['failed_case']['quality_flags'], ['ABSOLUTE_NO_RISK'])
        self.assertEqual(report['results'], [])
        self.assertIsNone(report['winner'])
        self.assertEqual(len(calls), 1)
        self.assertNotIn(REAL_REPLAY, str(report))
