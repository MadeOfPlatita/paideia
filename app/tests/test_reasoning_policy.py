"""Offline request policy tests; never a live provider call."""
import json
import unittest
from providers import build_chat_request

class ReasoningPolicyTests(unittest.TestCase):
    def test_benchmark_payload_matches_native_request_policy_for_every_variant(self):
        from context_quality_benchmark import build_requests
        for row in build_requests('openai/gpt-oss-20b'):
            with self.subTest(case=row['case_id'],variant=row['variant']):
                expected=json.loads(build_chat_request(row['payload']['messages'],model=row['payload']['model']))
                self.assertEqual(row['payload'],expected)
                self.assertEqual(row['request_bytes'],len(build_chat_request(row['payload']['messages'],model=row['payload']['model'])))

    def test_benchmark_uses_a_common_concise_instruction_without_changing_output_budget(self):
        from context_quality_benchmark import build_requests
        rows=build_requests('openai/gpt-oss-20b')
        prompts={row['payload']['messages'][0]['content'] for row in rows}
        self.assertEqual(len(prompts),1)
        self.assertIn('tres frases',next(iter(prompts)))
        self.assertTrue(all(row['payload']['max_tokens']==256 for row in rows))

    def test_oss_requests_keep_output_cap_and_use_low_effort_without_returning_reasoning(self):
        payload=json.loads(build_chat_request([{'role':'user','content':'SYNTHETIC: concepto breve'}]))
        self.assertEqual(payload['max_tokens'],256)
        self.assertEqual(payload.get('reasoning_effort'),'low')
        self.assertIs(payload.get('include_reasoning'),False)
