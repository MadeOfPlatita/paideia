"""Offline regression: all previous free-text examples remain untrusted input."""
import json
import unittest
from pathlib import Path
from structured_education import render_selection

class StructuredPriorCorpusTests(unittest.TestCase):
    def test_prior_twenty_examples_cannot_become_editorial_text(self):
        root = Path(__file__).resolve().parents[3]
        file = root / 'docs/ia-real-siguiente/ejecucion/20261030T005810Z/quality-offline/heldout-corpus.json'
        corpus = json.loads(file.read_text(encoding='utf-8'))['rows']
        self.assertEqual(len(corpus), 20)
        for case in corpus:
            with self.subTest(case=case['id']):
                with self.assertRaises(ValueError):
                    render_selection({'version':'paideia-education-v1', 'intent':'explain',
                                      'claim_ids':['risk'], 'answer':case['text']})
