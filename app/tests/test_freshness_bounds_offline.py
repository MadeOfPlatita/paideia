"""Synthetic-only fail-closed freshness policy regression tests."""
import unittest
from datetime import timedelta

from catalogue_facts import evaluate_comparability
from test_catalogue_facts import AS_OF, deposit_policy, deposit_spec, synthetic_fact


class FreshnessBoundsTests(unittest.TestCase):
    def test_each_unconfigured_bound_excludes_and_retains_other_reasons(self):
        facts = [synthetic_fact('test-product-a', '0.00', permissions_by_action={'display': 'allowed'}),
                 synthetic_fact('test-product-b', '3.25', retrieved_at='2020-01-01T00:00:00+00:00', effective_at='2020-01-01', valid_from='2020-01-01')]
        for retrieval, effective in ((None, None), (None, timedelta(days=1)), (timedelta(days=1), None)):
            with self.subTest(retrieval=retrieval, effective=effective):
                dto = evaluate_comparability(facts, deposit_spec(), deposit_policy(max_retrieval_age=retrieval, max_effective_age=effective)).to_dict()
                self.assertEqual(dto['status'], 'not_comparable')
                self.assertFalse(dto['quantitative_ready'])
                self.assertEqual(dto['eligible_product_ids'], [])
                self.assertTrue(all(i['value'] is None and 'FRESHNESS_BOUNDS_UNCONFIGURED' in i['reason_codes'] for i in dto['items']))
                self.assertIn('RIGHTS_UNRESOLVED', dto['items'][0]['reason_codes'])
                if retrieval is not None:
                    self.assertIn('SOURCE_STALE', dto['items'][1]['reason_codes'])
                if effective is not None:
                    self.assertIn('METRIC_STALE', dto['items'][1]['reason_codes'])

    def test_finite_boundaries_future_and_stale_are_distinct(self):
        policy = deposit_policy(max_retrieval_age=timedelta(hours=2), max_effective_age=timedelta(hours=2))
        def run(retrieved, effective):
            facts = [synthetic_fact(pid, '0.00', retrieved_at=retrieved, effective_at=effective,
                                    effective_precision='datetime') for pid in ('test-product-a', 'test-product-b')]
            return evaluate_comparability(facts, deposit_spec(), policy).to_dict()
        at_boundary = run('2026-10-27T10:00:00+00:00', '2026-10-27T10:00:00+00:00')
        self.assertTrue(at_boundary['quantitative_ready'])
        self.assertEqual(at_boundary['items'][0]['value'], '0.00')
        stale = run('2026-10-27T09:59:59+00:00', '2026-10-27T09:59:59+00:00')
        self.assertFalse(stale['quantitative_ready'])
        self.assertTrue({'SOURCE_STALE', 'METRIC_STALE'} <= set(stale['items'][0]['reason_codes']))
        future = run('2026-10-27T12:00:01+00:00', '2026-10-27T12:00:01+00:00')
        self.assertTrue({'RETRIEVED_AT_FUTURE', 'EFFECTIVE_DATE_FUTURE'} <= set(future['items'][0]['reason_codes']))
        zero = deposit_policy(max_retrieval_age=timedelta(0), max_effective_age=timedelta(0))
        facts = [synthetic_fact(pid, '0', retrieved_at=AS_OF, effective_at=AS_OF, effective_precision='datetime') for pid in ('test-product-a', 'test-product-b')]
        self.assertTrue(evaluate_comparability(facts, deposit_spec(), zero).quantitative_ready)

    def test_non_timedelta_thresholds_rejected_even_false_and_zero(self):
        for value in (False, True, 0, 1, '', '0'):
            for name in ('max_retrieval_age', 'max_effective_age'):
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    deposit_policy(**{name: value})

    def test_missing_and_conflict_keep_their_reason(self):
        a = synthetic_fact('test-product-a', '1')
        b = synthetic_fact('test-product-a', '2', fact_id='other')
        dto = evaluate_comparability([a, b], deposit_spec(), deposit_policy(max_effective_age=None)).to_dict()
        self.assertEqual(dto['items'][0]['reason_codes'], ['FRESHNESS_BOUNDS_UNCONFIGURED', 'DATA_CONFLICT'])
        self.assertEqual(dto['items'][1]['reason_codes'], ['FRESHNESS_BOUNDS_UNCONFIGURED', 'METRIC_MISSING'])
