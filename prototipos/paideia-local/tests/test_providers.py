import contextlib
import importlib
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from providers import (
    ALLOWED_MODELS,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_TOKENS,
    GROQ_HOST,
    GROQ_PATH,
    MAX_OUTPUT_TOKENS,
    MAX_REQUEST_BYTES,
    build_chat_request,
)


class TestOnlyFakeTransport:
    """Offline-only test double; it is not a Groq endpoint or provider."""

    test_only = True

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def post(self, **request):
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        return self.response


class TrackingEnvironment(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_keys = []

    def get(self, key, default=None):
        self.read_keys.append(key)
        return super().get(key, default)


class ProviderRequestBuilderTests(unittest.TestCase):
    def test_builds_a_pure_fixed_endpoint_request_for_an_allowlisted_model(self):
        messages = [
            {"role": "system", "content": "Instrucción sintética."},
            {"role": "user", "content": "Pregunta de prueba."},
        ]
        original = json.loads(json.dumps(messages))

        body = build_chat_request(messages)

        self.assertEqual(GROQ_HOST, "api.groq.com")
        self.assertEqual(GROQ_PATH, "/openai/v1/chat/completions")
        document = json.loads(body.decode("utf-8"))
        self.assertEqual(document, {
            "model": DEFAULT_MODEL,
            "messages": messages,
            "max_tokens": DEFAULT_OUTPUT_TOKENS,
            "reasoning_effort": "low",
            "include_reasoning": False,
        })
        self.assertEqual(DEFAULT_MODEL, "openai/gpt-oss-20b")
        self.assertEqual(ALLOWED_MODELS, {
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
        })
        self.assertEqual(DEFAULT_OUTPUT_TOKENS, 256)
        self.assertLessEqual(DEFAULT_OUTPUT_TOKENS, MAX_OUTPUT_TOKENS)
        self.assertEqual(messages, original)

    def test_rejects_a_role_outside_the_chat_contract(self):
        with self.assertRaises(ValueError):
            build_chat_request([{"role": "developer", "content": "not in contract"}])

    def test_rejects_an_unhashable_role_without_leaking_type_errors(self):
        with self.assertRaises(ValueError):
            build_chat_request([{"role": ["user"], "content": "Pregunta."}])

    def test_rejects_a_request_byte_limit_above_the_hard_ceiling(self):
        with self.assertRaises(ValueError):
            build_chat_request(
                [{"role": "user", "content": "Pregunta."}],
                max_request_bytes=MAX_REQUEST_BYTES + 1,
            )

    def test_rejects_a_tool_message_without_a_matching_assistant_call(self):
        messages = [
            {"role": "user", "content": "Pregunta sintética."},
            {"role": "tool", "tool_call_id": "call-missing", "content": "{}"},
        ]
        with self.assertRaises(ValueError):
            build_chat_request(messages)

    def test_serializes_system_user_assistant_and_tool_messages_without_mutation(self):
        tool_schema = {
            "type": "function",
            "function": {
                "name": "calculate_scenario",
                "description": "Cálculo sintético local.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        }
        messages = [
            {"role": "system", "content": "Solo explica resultados validados."},
            {"role": "user", "content": "Calcula este supuesto sintético."},
            {"role": "assistant", "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "calculate_scenario", "arguments": json.dumps({"years": 1})},
            }]},
            {"role": "tool", "tool_call_id": "call_1", "name": "calculate_scenario", "content": "{}"},
            {"role": "assistant", "content": "Resultado sintético."},
        ]
        original = json.loads(json.dumps(messages))

        body = build_chat_request(
            messages,
            model="openai/gpt-oss-120b",
            tools=[tool_schema],
        )

        document = json.loads(body.decode("utf-8"))
        self.assertEqual(document["model"], "openai/gpt-oss-120b")
        self.assertEqual([item["role"] for item in document["messages"]], [
            "system", "user", "assistant", "tool", "assistant",
        ])
        self.assertEqual(document["messages"][3]["tool_call_id"], "call_1")
        self.assertEqual(document["tools"], [tool_schema])
        self.assertEqual(messages, original)

    def test_rejects_output_ceiling_above_small_cap_and_models_outside_allowlist(self):
        messages = [{"role": "user", "content": "Pregunta sintética."}]
        with self.assertRaises(ValueError):
            build_chat_request(messages, max_output_tokens=MAX_OUTPUT_TOKENS + 1)
        with self.assertRaises(ValueError):
            build_chat_request(messages, model="not-an-allowed-model")

    def test_does_not_mix_strict_structured_outputs_with_tools(self):
        messages = [{"role": "user", "content": "Pregunta sintética."}]
        tools = [{"type": "function", "function": {
            "name": "search_products",
            "parameters": {"type": "object", "properties": {}},
            "strict": True,
        }}]
        with self.assertRaises(ValueError):
            build_chat_request(messages, tools=tools)


class ProviderOptInTests(unittest.TestCase):
    def test_rejects_unrepresentably_large_timeout_as_configuration_error(self):
        module = importlib.import_module("providers")
        with self.assertRaises(ValueError):
            module.GroqProvider(TestOnlyFakeTransport(), timeout=10 ** 1000)

    def test_default_disabled_provider_does_not_read_secret_or_call_transport(self):
        module = importlib.import_module("providers")
        provider_type = getattr(module, "GroqProvider", None)
        self.assertIsNotNone(provider_type, "GroqProvider is not implemented")
        environment = TrackingEnvironment({
            "PAIDEIA_GROQ_ENABLED": "1",
            "GROQ_API_KEY": "OFFLINE_TEST_SECRET_ONLY",
        })
        transport = TestOnlyFakeTransport()
        provider = provider_type(transport, environment=environment)

        with self.assertRaises(module.ProviderError) as caught:
            provider.chat([{"role": "user", "content": "Pregunta sintética."}])

        self.assertEqual(caught.exception.code, "disabled")
        self.assertEqual(environment.read_keys, [])
        self.assertEqual(transport.calls, [])

    def test_opted_in_provider_without_secret_stops_before_transport(self):
        module = importlib.import_module("providers")
        environment = TrackingEnvironment()
        transport = TestOnlyFakeTransport()
        provider = module.GroqProvider(transport, opt_in=True, environment=environment)

        with self.assertRaises(module.ProviderError) as caught:
            provider.chat([{"role": "user", "content": "Pregunta sintética."}])

        self.assertEqual(caught.exception.code, "not_configured")
        self.assertEqual(environment.read_keys, ["GROQ_API_KEY"])
        self.assertEqual(transport.calls, [])

    def test_invalid_secret_header_characters_stop_before_transport(self):
        module = importlib.import_module("providers")
        for secret in ("bad key", "bad\x00key", "bad\nkey", "clavé"):
            with self.subTest(secret=repr(secret)):
                environment = TrackingEnvironment({"GROQ_API_KEY": secret})
                transport = TestOnlyFakeTransport()
                provider = module.GroqProvider(transport, opt_in=True, environment=environment)
                with self.assertRaises(module.ProviderError) as caught:
                    provider.chat([{"role": "user", "content": "Pregunta sintética."}])
                self.assertEqual(caught.exception.code, "not_configured")
                self.assertEqual(transport.calls, [])

    def test_invalid_request_is_rejected_before_secret_read_or_transport(self):
        module = importlib.import_module("providers")
        environment = TrackingEnvironment({"GROQ_API_KEY": "OFFLINE_TEST_SECRET_ONLY"})
        transport = TestOnlyFakeTransport()
        provider = module.GroqProvider(transport, opt_in=True, environment=environment)

        with self.assertRaises(module.ProviderError) as caught:
            provider.chat([{"role": "tool", "tool_call_id": "unknown", "content": "{}"}])

        self.assertEqual(caught.exception.code, "invalid_request")
        self.assertEqual(environment.read_keys, [])
        self.assertEqual(transport.calls, [])

    def test_environment_factory_requires_exact_local_opt_in_before_secret_read(self):
        module = importlib.import_module("providers")
        environment = TrackingEnvironment({
            "PAIDEIA_GROQ_ENABLED": "true",
            "GROQ_API_KEY": "OFFLINE_TEST_SECRET_ONLY",
        })
        transport = TestOnlyFakeTransport()
        provider = module.GroqProvider.from_environment(transport, environment=environment)

        with self.assertRaises(module.ProviderError) as caught:
            provider.chat([{"role": "user", "content": "Pregunta sintética."}])

        self.assertEqual(caught.exception.code, "disabled")
        self.assertEqual(environment.read_keys, ["PAIDEIA_GROQ_ENABLED"])
        self.assertEqual(transport.calls, [])

    def test_explicit_environment_opt_in_reads_secret_only_for_fake_chat_send(self):
        module = importlib.import_module("providers")
        secret = "OFFLINE_TEST_SECRET_ONLY_environment"
        response = SimpleNamespace(
            status=200,
            body=json.dumps({"choices": [{
                "message": {"role": "assistant", "content": "Respuesta sintética."},
                "finish_reason": "stop",
            }]}).encode("utf-8"),
        )
        environment = TrackingEnvironment({
            "PAIDEIA_GROQ_ENABLED": "1",
            "GROQ_API_KEY": secret,
        })
        transport = TestOnlyFakeTransport(response=response)

        provider = module.GroqProvider.from_environment(transport, environment=environment)
        self.assertEqual(environment.read_keys, ["PAIDEIA_GROQ_ENABLED"])
        result = provider.chat([{"role": "user", "content": "Pregunta sintética."}])

        self.assertEqual(result.answer, "Respuesta sintética.")
        self.assertEqual(environment.read_keys, ["PAIDEIA_GROQ_ENABLED", "GROQ_API_KEY"])
        self.assertEqual(len(transport.calls), 1)
        self.assertNotIn(secret, repr(result))

    def test_fake_transport_receives_only_fixed_headers_without_secret_echo(self):
        module = importlib.import_module("providers")
        secret = "OFFLINE_TEST_SECRET_ONLY_7d92"
        response_body = json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "Respuesta sintética.",
                    "reasoning": "Razonamiento separado.",
                },
            }],
        }).encode("utf-8")
        transport = TestOnlyFakeTransport(
            response=SimpleNamespace(status=200, body=response_body),
        )
        environment = TrackingEnvironment({"GROQ_API_KEY": secret})
        provider = module.GroqProvider(transport, opt_in=True, environment=environment)
        output = io.StringIO()

        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = provider.chat([{"role": "user", "content": "Prueba sintética."}])

        self.assertEqual(len(transport.calls), 1)
        sent = transport.calls[0]
        self.assertEqual(sent["host"], GROQ_HOST)
        self.assertEqual(sent["path"], GROQ_PATH)
        self.assertEqual(sent["headers"], {
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        sent_document = json.loads(sent["body"].decode("utf-8"))
        self.assertEqual(sent_document["model"], DEFAULT_MODEL)
        self.assertEqual(sent_document["max_tokens"], 256)
        self.assertNotIn(secret, sent["body"].decode("utf-8"))
        self.assertEqual(result.answer, "Respuesta sintética.")
        self.assertEqual(result.reasoning, "Razonamiento separado.")
        self.assertNotIn(secret, repr(result))
        self.assertNotIn(secret, output.getvalue())

    def test_provider_does_not_return_an_api_key_echoed_in_a_success_response(self):
        module = importlib.import_module("providers")
        secret = "OFFLINE_TEST_SECRET_ONLY_echo"
        response_body = json.dumps({
            "choices": [{
                "message": {"role": "assistant", "content": secret},
                "finish_reason": "stop",
            }],
        }).encode("utf-8")
        transport = TestOnlyFakeTransport(
            response=SimpleNamespace(status=200, body=response_body),
        )
        provider = module.GroqProvider(
            transport,
            opt_in=True,
            environment=TrackingEnvironment({"GROQ_API_KEY": secret}),
        )

        with self.assertRaises(module.ProviderError) as caught:
            provider.chat([{"role": "user", "content": "Pregunta sintética."}])

        self.assertEqual(caught.exception.code, "invalid_response")
        self.assertNotIn(secret, str(caught.exception))
        self.assertEqual(len(transport.calls), 1)

    def test_provider_errors_are_content_free_and_never_retried(self):
        module = importlib.import_module("providers")
        secret = "OFFLINE_TEST_SECRET_ONLY_error"
        error_body = ("PRIVATE_ERROR_BODY " + secret).encode("utf-8")
        malformed_tool_body = json.dumps({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "tool_calls": [{
                        "id": "call_invalid",
                        "type": "function",
                        "function": {"name": "tool_without_arguments"},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
        }).encode("utf-8")
        parallel_tool_body = json.dumps({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {"id": "call_a", "type": "function", "function": {
                            "name": "tool_a", "arguments": json.dumps({}),
                        }},
                        {"id": "call_b", "type": "function", "function": {
                            "name": "tool_b", "arguments": json.dumps({}),
                        }},
                    ],
                },
                "finish_reason": "tool_calls",
            }],
        }).encode("utf-8")
        cases = [
            (401, error_body, "unauthorized", None),
            (429, error_body, "rate_limited", None),
            (503, error_body, "provider_unavailable", None),
            (200, b"{not-json " + secret.encode("ascii"), "invalid_response", None),
            (200, malformed_tool_body, "invalid_response", None),
            (200, parallel_tool_body, "invalid_response", None),
            (200, b"R" * (module.MAX_RESPONSE_BYTES + 1), "invalid_response", None),
            (None, b"", "timeout", TimeoutError("PRIVATE_TIMEOUT " + secret)),
        ]
        for status, body, expected_code, transport_error in cases:
            with self.subTest(code=expected_code):
                response = None if status is None else SimpleNamespace(status=status, body=body)
                transport = TestOnlyFakeTransport(response=response, error=transport_error)
                provider = module.GroqProvider(
                    transport,
                    opt_in=True,
                    environment=TrackingEnvironment({"GROQ_API_KEY": secret}),
                )
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    with self.assertRaises(module.ProviderError) as caught:
                        provider.chat([{"role": "user", "content": "Pregunta sintética."}])
                self.assertEqual(caught.exception.code, expected_code)
                self.assertFalse(caught.exception.retryable)
                self.assertIsNone(caught.exception.__context__)
                self.assertEqual(len(transport.calls), 1)
                self.assertNotIn(secret, str(caught.exception))
                self.assertNotIn("PRIVATE_ERROR_BODY", str(caught.exception))
                self.assertNotIn(secret, output.getvalue())

    def test_tool_call_is_returned_for_server_dispatch_not_executed_here(self):
        module = importlib.import_module("providers")
        response_body = json.dumps({
            "choices": [{
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_123",
                        "type": "function",
                        "function": {"name": "unregistered_tool", "arguments": json.dumps({"x": 1})},
                    }],
                },
            }],
        }).encode("utf-8")
        transport = TestOnlyFakeTransport(
            response=SimpleNamespace(status=200, body=response_body),
        )
        provider = module.GroqProvider(
            transport,
            opt_in=True,
            environment=TrackingEnvironment({"GROQ_API_KEY": "OFFLINE_TEST_SECRET_ONLY"}),
        )

        result = provider.chat([{"role": "user", "content": "Prueba sintética."}])

        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].name, "unregistered_tool")
        self.assertEqual(result.tool_calls[0].arguments, {"x": 1})
        self.assertEqual(result.answer, "")

    def test_https_transport_uses_pinned_host_route_and_bounded_read_without_network(self):
        module = importlib.import_module("providers")

        class TestOnlyHTTPSConnection:
            instances = []

            def __init__(self, host, timeout):
                self.host = host
                self.timeout = timeout
                self.request_args = None
                self.closed = False
                self.response = SimpleNamespace(status=200, read=self.read)
                self.__class__.instances.append(self)

            def request(self, method, path, *, body, headers):
                self.request_args = (method, path, body, dict(headers))

            def getresponse(self):
                return self.response

            def read(self, size):
                self.read_limit = size
                return b"{}"

            def close(self):
                self.closed = True

        request = {
            "host": GROQ_HOST,
            "path": GROQ_PATH,
            "headers": {
                "Authorization": "Bearer OFFLINE_TEST_SECRET_ONLY",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "body": b"{}",
            "timeout": 3.0,
        }
        with patch.object(module.http.client, "HTTPSConnection", TestOnlyHTTPSConnection):
            response = module.GroqHTTPSJSONTransport().post(**request)
            with self.assertRaises(ValueError):
                module.GroqHTTPSJSONTransport().post(**dict(request, host="example.invalid"))
            invalid_headers = dict(request["headers"], Authorization="Bearer bad key")
            with self.assertRaises(ValueError):
                module.GroqHTTPSJSONTransport().post(**dict(request, headers=invalid_headers))

        connection = TestOnlyHTTPSConnection.instances[0]
        self.assertEqual(connection.host, GROQ_HOST)
        self.assertEqual(connection.timeout, 3.0)
        self.assertEqual(connection.request_args[0:2], ("POST", GROQ_PATH))
        self.assertEqual(connection.read_limit, module.MAX_RESPONSE_BYTES + 1)
        self.assertTrue(connection.closed)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, b"{}")
        self.assertEqual(len(TestOnlyHTTPSConnection.instances), 1)


if __name__ == "__main__":
    unittest.main()
