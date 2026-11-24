"""El reintento de transporte: una vez, solo red, nunca con trabajo hecho.

Medido en producción: alrededor del 2 % de los turnos moría con un 502 sin código
y la misma pregunta respondía al reintentar a mano (2.660, 3.177 y 3.588
caracteres). No era el modelo: era la conexión.

Un reintento mal puesto es peor que ninguno: puede duplicar llamadas al proveedor
y, con herramientas, repetir trabajo ya hecho. Estas pruebas fijan las tres
condiciones:

1. Se reintenta el fallo de red (`transport_error`, `timeout`).
2. NO se reintenta lo que no se arregla repitiendo: cupo, misión, credencial ni
   respuesta inválida.
3. NO se reintenta si el turno ya ejecutó una herramienta.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pai_runtime import ToolChatRunner, _is_retryable_transport  # noqa: E402
from providers import ChatResult, ProviderError, ToolCall  # noqa: E402

TOOLS = [{"type": "function", "function": {
    "name": "search_products",
    "description": "Busca productos del catálogo",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
}}]


class Dispatcher:
    def __init__(self):
        self.calls = []

    def definitions(self):
        return TOOLS

    def dispatch(self, name, arguments):
        self.calls.append(name)
        return {"schema_version": "local-tools.v1", "tool": name, "status": "ok",
                "data": {"items": [{"id": "DEP-04", "name": "Depósito", "family": "deposito",
                                    "issuer": "EBN Banco", "primary_url": "https://example.test/x",
                                    "identity_state": "verified", "publication_ready": False,
                                    "conditions_state": "documented", "conflicts": [],
                                    "unknown_fields": [], "conditions": []}],
                         "count": 1, "limit": 8},
                "sources": [], "error": None}


class Provider:
    """Devuelve las respuestas de la lista; si es una excepción, la lanza."""

    test_only = True

    def __init__(self, guion):
        self.guion = list(guion)
        self.llamadas = 0

    def chat(self, messages, *, tools=None):
        self.llamadas += 1
        paso = self.guion[min(self.llamadas - 1, len(self.guion) - 1)]
        if isinstance(paso, Exception):
            raise paso
        return paso


def runner(guion, dispatcher=None):
    return ToolChatRunner(Provider(guion), dispatcher or Dispatcher())


class RetryClassificationTests(unittest.TestCase):
    def test_network_failures_are_retryable(self):
        for code in ("transport_error", "timeout"):
            with self.subTest(code=code):
                self.assertTrue(_is_retryable_transport(ProviderError(code)))

    def test_everything_else_is_not_retryable(self):
        for code in ("disabled", "not_configured", "unauthorized", "rate_limited",
                     "invalid_response", "mission_exhausted", "mission_closed",
                     "mission_unavailable", "mission_corrupt", "mission_guard_unavailable"):
            with self.subTest(code=code):
                self.assertFalse(_is_retryable_transport(ProviderError(code)))

    def test_an_exception_without_code_is_not_retryable(self):
        self.assertFalse(_is_retryable_transport(RuntimeError("sin codigo")))


class TransportRetryTests(unittest.TestCase):
    def test_a_network_failure_is_retried_once_and_the_turn_succeeds(self):
        proveedor = Provider([ProviderError("transport_error"),
                              ChatResult("Respuesta tras el reintento.", None, (), "stop")])
        resultado = ToolChatRunner(proveedor, Dispatcher()).run(
            [{"role": "user", "content": "hola"}], with_tools=False)
        self.assertEqual(proveedor.llamadas, 2, "debe reintentar exactamente una vez")
        self.assertIn("Respuesta tras el reintento", resultado["answer"])

    def test_a_timeout_is_also_retried(self):
        proveedor = Provider([ProviderError("timeout"),
                              ChatResult("Respuesta.", None, (), "stop")])
        ToolChatRunner(proveedor, Dispatcher()).run(
            [{"role": "user", "content": "hola"}], with_tools=False)
        self.assertEqual(proveedor.llamadas, 2)

    def test_two_network_failures_in_a_row_stop_after_one_retry(self):
        proveedor = Provider([ProviderError("transport_error")])
        resultado = ToolChatRunner(proveedor, Dispatcher()).run(
            [{"role": "user", "content": "hola"}], with_tools=False)
        self.assertEqual(proveedor.llamadas, 2, "un reintento, no un bucle")
        self.assertEqual(resultado["finish_reason"], "error")

    def test_a_quota_error_is_never_retried(self):
        proveedor = Provider([ProviderError("rate_limited"),
                              ChatResult("no deberia llegar", None, (), "stop")])
        ToolChatRunner(proveedor, Dispatcher()).run(
            [{"role": "user", "content": "hola"}], with_tools=False)
        self.assertEqual(proveedor.llamadas, 1, "repetir no arregla un cupo agotado")

    def test_a_transport_failure_is_not_retried_once_a_tool_ran(self):
        # Turno 1: el modelo pide una herramienta. Turno 2: cae la red.
        proveedor = Provider([
            ChatResult("", None, (ToolCall("c1", "search_products", {"query": "deposito"}),),
                       "tool_calls"),
            ProviderError("transport_error"),
        ])
        despachante = Dispatcher()
        ToolChatRunner(proveedor, despachante).run(
            [{"role": "user", "content": "hola"}], with_tools=True)
        self.assertEqual(len(despachante.calls), 1, "la herramienta se ejecutó una vez")
        self.assertEqual(proveedor.llamadas, 2,
                         "tras una herramienta no se repite el turno: duplicaria trabajo")


if __name__ == "__main__":
    unittest.main()
