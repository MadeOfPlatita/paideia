"""Una herramienta rechazada no puede dejar al usuario sin respuesta.

Medido en producción: «¿Es mejor un depósito o un fondo de renta fija a 2 años?»
devolvía 502 CHAT_TOOL_ERROR a los 17,7 s. El modelo propuso una llamada que no
pasó la validación, el runner terminó el turno con `tool_error` y el usuario no
recibió nada.

Ahora, si el turno con herramientas acaba en `tool_error` **sin haber ejecutado
ninguna**, se hace un segundo intento sin herramientas. No duplica trabajo (no se
ejecutó nada) ni gasta cupo de herramienta: solo se le pide al modelo que conteste
con lo que sepa.

Lo que NO cambia: si la herramienta sí se ejecutó y falló, el error se respeta.
Repetir entonces sí duplicaría trabajo.

Se usa `FakeChatProvider` (el único proveedor sintético cerrado que admite el
servicio) con su modo `outcomes`, que permite guionizar varios turnos.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timezone  # noqa: E402

from backend_services import LocalChatService, ServiceProblem  # noqa: E402
from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission  # noqa: E402
from dialogue_tools_double import (  # noqa: E402
    DispatcherQueEjecuta,
    DispatcherQueRechaza,
)
from providers import ChatResult, ToolCall  # noqa: E402
from structured_provider_adapter import FakeChatProvider  # noqa: E402

CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
           "purpose": "free_chat", "approved_fields": []}

LLAMADA_INVENTADA = ChatResult(
    "", None, (ToolCall("c1", "herramienta_no_anunciada", {}),), "tool_calls")
RESPUESTA_SIN_HERRAMIENTAS = ChatResult(
    "Compara el plazo y la liquidez antes que la tasa.", None, (), "stop")


def proveedor(*outcomes):
    return FakeChatProvider(outcomes[0], test_only=True, outcomes=outcomes)


def puerta():
    policy = AdmissionPolicy(max_concurrent=2, max_queue=2, calls_per_minute=20,
                             calls_per_day=40, ticket_ttl_seconds=120,
                             claim_ttl_seconds=120, scope="TEST_ONLY_FALLBACK")
    return InterfazChatAdmission(policy, lambda: datetime.now(timezone.utc),
                                 budget_state=InMemoryBudgetState.new_empty(scope=policy.scope))


def servicio(provider, dispatcher):
    return LocalChatService(provider=provider, enabled=True, test_only=True,
                            dispatcher=dispatcher, tools_enabled=True,
                            tools_scope="catalogue_read", catalogue_usage_approved=True,
                            admission=puerta())


class ToolRejectionFallbackTests(unittest.TestCase):
    def test_a_rejected_call_falls_back_to_a_plain_answer(self):
        # Turno 1: el modelo pide una herramienta que no existe. Turno 2 (sin
        # herramientas): responde con criterio.
        provider = proveedor(LLAMADA_INVENTADA, RESPUESTA_SIN_HERRAMIENTAS)
        cuerpo = servicio(provider, DispatcherQueRechaza()).chat(
            {"message": "¿Es mejor un depósito o un fondo a 2 años?", "consent": CONSENT})
        self.assertIn("plazo", cuerpo["answer"])
        self.assertEqual(provider.calls, 2, "un solo intento de respaldo")

    def test_the_second_attempt_does_not_advertise_tools(self):
        provider = proveedor(LLAMADA_INVENTADA, RESPUESTA_SIN_HERRAMIENTAS)
        servicio(provider, DispatcherQueRechaza()).chat(
            {"message": "¿Es mejor un depósito o un fondo a 2 años?", "consent": CONSENT})
        # El segundo turno se pide sin herramientas: es la clave de que no duplica.
        self.assertIsNotNone(provider.tools[0], "el primero sí las anuncia")
        self.assertIsNone(provider.tools[-1], "el respaldo no las anuncia")

    def test_an_executed_tool_failure_is_not_retried(self):
        # La herramienta sí se ejecutó (y falló): repetir duplicaría trabajo.
        provider = proveedor(ChatResult(
            "", None, (ToolCall("c1", "search_products", {"query": "x"}),), "tool_calls"))
        with self.assertRaises(ServiceProblem) as caught:
            servicio(provider, DispatcherQueEjecuta(falla=True)).chat(
                {"message": "¿Qué depósitos hay?", "consent": CONSENT})
        self.assertEqual(caught.exception.code, "CHAT_TOOL_ERROR")
        self.assertEqual(provider.calls, 1, "tras ejecutar no se repite el turno")

    def test_if_the_fallback_also_fails_the_error_is_reported(self):
        provider = proveedor(LLAMADA_INVENTADA, ChatResult("", None, (), "error"))
        with self.assertRaises(ServiceProblem) as caught:
            servicio(provider, DispatcherQueRechaza()).chat(
                {"message": "¿Es mejor un depósito o un fondo?", "consent": CONSENT})
        self.assertEqual(caught.exception.code, "CHAT_TOOL_ERROR")


if __name__ == "__main__":
    unittest.main()
