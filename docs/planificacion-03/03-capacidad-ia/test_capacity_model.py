import unittest

from capacity_model import build_scenarios, compute_turn, evaluate_scenario, build_edge_cases


class CapacityModelTests(unittest.TestCase):
    def test_tool_rounds_repeat_context_and_count_tool_payload(self):
        result = compute_turn(
            base_context_tokens=1000,
            history_tokens=0,
            current_message_tokens=60,
            answer_tokens=250,
            tool_loops=2,
            tool_call_output_tokens=50,
            tool_result_tokens=120,
        )
        self.assertEqual(result["requests"], 3)
        self.assertEqual(result["input_tokens"], 3690)
        self.assertEqual(result["output_tokens"], 350)

    def test_initial_burst_excludes_tool_results_not_yet_produced(self):
        row = evaluate_scenario({
            "model_id": "openai/gpt-oss-20b",
            "onboarding_mode": "buttons",
            "turns": 3,
            "context_profile": "lean",
            "answer_tokens": 250,
            "tool_loops": 2,
            "users": 100,
        })
        # First wave contains only static context + current question + tool-call
        # output. Results from later tool rounds do not exist in this wave.
        expected_first_wave = (1000 + 60 + 50) * 100
        self.assertEqual(row["first_turn_initial_burst_tokens"], expected_first_wave)

    def test_grid_covers_requested_dimensions(self):
        rows = build_scenarios()
        self.assertEqual(len(rows), 432)
        self.assertEqual({r["onboarding_mode"] for r in rows}, {"buttons", "llm"})
        self.assertEqual({r["turns"] for r in rows}, {3, 5, 10})
        self.assertEqual({r["answer_tokens"] for r in rows}, {250, 500})
        self.assertEqual({r["tool_loops"] for r in rows}, {0, 1, 2})
        self.assertEqual({r["context_profile"] for r in rows}, {"lean", "typical", "heavy"})
        self.assertEqual({r["provider"] for r in rows}, {"Cloudflare Workers AI", "GroqCloud"})

    def test_buttons_avoid_onboarding_llm_spend(self):
        row = evaluate_scenario({
            "provider": "GroqCloud",
            "model_id": "openai/gpt-oss-20b",
            "onboarding_mode": "buttons",
            "turns": 3,
            "context_profile": "lean",
            "answer_tokens": 250,
            "tool_loops": 0,
            "users": 100,
        })
        self.assertEqual(row["onboarding_requests"], 0)
        self.assertEqual(row["onboarding_input_tokens"], 0)
        self.assertEqual(row["onboarding_output_tokens"], 0)

    def test_llm_onboarding_is_one_bounded_call_per_user(self):
        row = evaluate_scenario({
            "provider": "GroqCloud",
            "model_id": "openai/gpt-oss-20b",
            "onboarding_mode": "llm",
            "turns": 3,
            "context_profile": "lean",
            "answer_tokens": 250,
            "tool_loops": 0,
            "users": 100,
        })
        self.assertEqual(row["onboarding_requests"], 100)
        self.assertEqual(row["onboarding_input_tokens"], 60000)
        self.assertEqual(row["onboarding_output_tokens"], 12000)

    def test_deterministic_test_cases_cover_quota_queue_rate_and_latency(self):
        cases = build_edge_cases()
        by_id = {case["case_id"]: case for case in cases}
        self.assertEqual(set(by_id), {"quota_exhausted", "queue_required", "rate_exceeded", "latency_unknown"})
        self.assertEqual(by_id["latency_unknown"]["latency_ms"], None)
        self.assertGreater(by_id["queue_required"]["queue_drain_lower_bound_minutes"], 0)
        self.assertEqual(by_id["quota_exhausted"]["state"], "exhausted")
        self.assertTrue(by_id["rate_exceeded"]["would_429_without_queue"])


if __name__ == "__main__":
    unittest.main()
