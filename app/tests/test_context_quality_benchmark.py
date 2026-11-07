import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'context_quality_benchmark.py'
spec = importlib.util.spec_from_file_location('quality', PATH)
quality = importlib.util.module_from_spec(spec)
if PATH.exists():
    spec.loader.exec_module(quality)


class QualityTests(unittest.TestCase):
    def test_measured_latency_is_retained_without_inventing_usage_or_cost(self):
        report=quality.run_benchmark(lambda _: {'status':200,'text':'TEST ONLY','latency_ms':12.5},
                                     'openai/gpt-oss-20b',max_calls=1,test_only=True)
        row=report['results'][0]
        self.assertIn('latency_ms',row)
        self.assertEqual(row['latency_ms'],12.5)
        self.assertIsNone(row['usage'])
        self.assertIsNone(row['cost'])

    def test_synthetic_plan_has_18_limited_groq_requests(self):
        requests = quality.build_requests('synthetic-test-model')
        self.assertEqual(len(requests), 18)
        self.assertEqual([r['variant'] for r in requests[:3]], ['A', 'B', 'C'])
        for r in requests:
            self.assertLessEqual(r['request_bytes'], 32768)
            self.assertEqual(r['payload']['max_tokens'], 256)
            self.assertEqual([m['role'] for m in r['payload']['messages']], ['system', 'user'])

    def test_run_stops_on_error_and_keeps_partial_with_unknown_usage(self):
        calls = []
        def test_only_provider(payload):
            calls.append(payload)
            if len(calls) == 2:
                return {'status': 429}
            return {'status': 200, 'text': 'fixture test_only'}
        result = quality.run_benchmark(test_only_provider, 'synthetic-test-model', max_calls=5, test_only=True)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result['stop_reason'], 'http_429')
        self.assertEqual(len(result['results']), 1)
        self.assertIsNone(result['results'][0]['usage'])
        self.assertIsNone(result['winner'])

    def test_test_only_results_are_explicitly_labeled(self):
        result = quality.run_benchmark(lambda _: {'status': 200, 'text': 'fixture test_only'},
                                       'synthetic-test-model', max_calls=1, test_only=True)
        self.assertEqual(result['provenance'], 'test_only')
        self.assertEqual(result['real_model_result_count'], 0)
        self.assertEqual(result['stop_reason'], 'budget_exhausted')

    def test_states_and_common_safe_prompt(self):
        requests = quality.build_requests('synthetic-test-model')
        a, b, c = requests[12:15]
        self.assertNotIn('Contexto sintético:', a['payload']['messages'][1]['content'])
        for r in (b, c):
            text = r['payload']['messages'][1]['content']
            for token in ('"valor": "0"', '"no_se"', '"omitido"', '"sin_preguntar"'):
                self.assertIn(token, text)
        for r in requests:
            prompt = r['payload']['messages'][0]['content']
            for phrase in ('no clasifiques', 'inflación', 'no garantiza', 'No hagas cálculos', 'no inventes'):
                self.assertIn(phrase, prompt)
        self.assertIn('sin riesgo', requests[0]['payload']['messages'][1]['content'])

    def test_exception_and_zero_budget_never_retry(self):
        calls = []
        def test_only_error(payload):
            calls.append(payload)
            raise RuntimeError('test_only')
        self.assertEqual(quality.run_benchmark(test_only_error, 'm', max_calls=0, test_only=True)['stop_reason'], 'budget_exhausted')
        self.assertEqual(len(calls), 0)
        report = quality.run_benchmark(test_only_error, 'm', test_only=True)
        self.assertEqual((len(calls), report['stop_reason']), (1, 'provider_error'))
        with self.assertRaises(ValueError):
            quality.run_benchmark(test_only_error, 'm', max_calls=19)

if __name__ == '__main__':
    unittest.main()
