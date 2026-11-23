"""Una respuesta con tool_calls malformadas pero texto valido no pierde el turno.

Caso real: el proveedor devolvio HTTP 200 con tool_calls fuera de contrato y el
turno se rechazo con CHAT_INVALID_RESPONSE aunque la contestacion estaba en el
texto. La regla nueva entrega el texto y descarta las llamadas dudosas; sin texto
ni rechazo se sigue rechazando, y una llamada valida se sigue parseando igual.

Estas pruebas usan transportes sinteticos: no hay llamadas reales al proveedor.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from providers import (  # noqa: E402
    GroqProvider,
    MAX_TOOL_CALLS_PER_TURN,
    ProviderError,
    TransportResponse,
)

MODEL = "openai/gpt-oss-20b"
KEY = "SYNTHETIC_TEST_TOKEN_NOT_A_REAL_KEY"
MESSAGES = [{"role": "user", "content": "pregunta"}]


class TestOnlyTransport:
    """Doble de transporte sin red; no es un proveedor real."""

    test_only = True

    def __init__(self, body):
        self._body = body
        self.calls = 0

    def post(self, **kwargs):
        self.calls += 1
        return TransportResponse(200, json.dumps(self._body).encode("utf-8"))


def message(content=None, tool_calls=None, **extra):
    payload = {"role": "assistant"}
    if content is not None:
        payload["content"] = content
    if tool_calls is not None:
        payload["tool_calls"] = tool_calls
    payload.update(extra)
    return {"choices": [{"message": payload, "finish_reason": "stop"}]}


def provider_for(body):
    env = {"PAIDEIA_GROQ_ENABLED": "1", "GROQ_API_KEY": KEY}
    return GroqProvider(TestOnlyTransport(body), opt_in=True, environment=env, model=MODEL)


def valid_call(call_id="call_1"):
    return {"id": call_id, "type": "function",
            "function": {"name": "search_products", "arguments": "{\"query\": \"deposito\"}"}}


class MalformedToolCallTests(unittest.TestCase):
    def test_a_tool_call_with_an_extra_field_no_longer_loses_the_answer(self):
        """El caso medido en produccion: forma inesperada y texto aprovechable."""
        body = message(content="Respuesta util que el usuario debe leer.",
                       tool_calls=[{**valid_call(), "index": 0}])
        result = provider_for(body).chat(MESSAGES)
        self.assertEqual(result.answer, "Respuesta util que el usuario debe leer.")
        self.assertEqual(result.tool_calls, ())

    def test_unparseable_arguments_no_longer_lose_the_answer(self):
        body = message(content="Explicacion conceptual valida.",
                       tool_calls=[{"id": "call_1", "type": "function",
                                    "function": {"name": "search_products", "arguments": "no es json"}}])
        result = provider_for(body).chat(MESSAGES)
        self.assertEqual(result.answer, "Explicacion conceptual valida.")
        self.assertEqual(result.tool_calls, ())

    def test_a_malformed_call_without_text_is_still_rejected(self):
        body = message(content=None, tool_calls=[{**valid_call(), "index": 0}])
        with self.assertRaises(ProviderError) as caught:
            provider_for(body).chat(MESSAGES)
        self.assertEqual(caught.exception.code, "invalid_response")

    def test_a_valid_tool_call_is_still_parsed(self):
        body = message(content=None, tool_calls=[valid_call()])
        result = provider_for(body).chat(MESSAGES)
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0].name, "search_products")
        self.assertEqual(result.tool_calls[0].arguments, {"query": "deposito"})

    def test_too_many_calls_with_text_keeps_the_text(self):
        calls = [valid_call("call_%d" % n) for n in range(MAX_TOOL_CALLS_PER_TURN + 1)]
        body = message(content="Texto aprovechable.", tool_calls=calls)
        result = provider_for(body).chat(MESSAGES)
        self.assertEqual(result.answer, "Texto aprovechable.")

    def test_the_refusal_branch_also_survives_a_malformed_call(self):
        body = message(content=None, refusal="No puedo ayudar con eso.",
                       tool_calls=[{**valid_call(), "index": 0}])
        result = provider_for(body).chat(MESSAGES)
        self.assertEqual(result.refusal, "No puedo ayudar con eso.")


if __name__ == "__main__":
    unittest.main()
