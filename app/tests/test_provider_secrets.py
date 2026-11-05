"""Security regression; literal TEST ONLY token, never a real credential."""
import json
import unittest
from providers import GroqProvider, ProviderError, TransportResponse


class ProviderSecretBoundaryTests(unittest.TestCase):
    def test_json_escaped_secret_is_not_returned_in_any_result_field(self):
        fake_key = "TEST_ONLY_NOT_A_REAL_CREDENTIAL"
        encoded = "".join("\\u%04x" % ord(character) for character in fake_key)
        class TestOnlyTransport:
            test_only = True
            def __init__(self, message):
                # Replace placeholder after JSON serialization to model escaped upstream text.
                self.body = json.dumps({"choices": [{"message": message, "finish_reason": "stop"}]}).replace("PLACEHOLDER", encoded).encode()
            def post(self, **kwargs):
                return TransportResponse(200, self.body)
        messages = [
            {"role": "assistant", "content": "PLACEHOLDER"},
            {"role": "assistant", "content": "TEST ONLY answer", "reasoning": "PLACEHOLDER"},
            {"role": "assistant", "content": None, "refusal": "PLACEHOLDER"},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "test-call-1", "type": "function", "function": {
                "name": "test_only_tool", "arguments": json.dumps({"value": "PLACEHOLDER"})}}]},
        ]
        for message in messages:
            with self.subTest(fields=tuple(message)):
                provider = GroqProvider(TestOnlyTransport(message), opt_in=True, environment={"GROQ_API_KEY": fake_key})
                with self.assertRaises(ProviderError) as problem:
                    provider.chat([{"role": "user", "content": "TEST ONLY prompt"}])
                self.assertEqual(problem.exception.code, "invalid_response")
                self.assertNotIn(fake_key, str(problem.exception))


if __name__ == "__main__":
    unittest.main()
