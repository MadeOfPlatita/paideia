"""El reintento no puede hacer que el turno muera en el proxy como 502 mudo.

MOTIVO MEDIDO. Render corta las peticiones a los 100 s y devuelve un 502 **sin
cuerpo**: el usuario pierde hasta el código del error. El proveedor puede tardar
60 s por intento, así que un fallo de tiempo agotado más su reintento sumarían
120 s y el turno moriría en el proxy.

Distribución real de 267 turnos medidos:

    mediana 20 s · p90 32 s · máximo 77 s · solo 1 por encima de 55 s

La regla: si el turno ya consumió su presupuesto, no se reintenta. El usuario recibe
el 504 con su motivo, que es un diagnóstico honesto, en vez de un 502 mudo del proxy.
"""

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pai_runtime  # noqa: E402
from pai_runtime import _RETRY_TIME_BUDGET_SECONDS, ToolChatRunner  # noqa: E402
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
                "data": {"items": [], "count": 0, "limit": 8},
                "sources": [], "error": None}


class Provider:
    test_only = True

    def __init__(self, guion, retraso=0.0):
        self.guion = list(guion)
        self.llamadas = 0
        self.retraso = retraso

    def chat(self, messages, *, tools=None):
        self.llamadas += 1
        if self.retraso:
            time.sleep(self.retraso)
        paso = self.guion[min(self.llamadas - 1, len(self.guion) - 1)]
        if isinstance(paso, Exception):
            raise paso
        return paso


class RetryTimeBudgetTests(unittest.TestCase):
    def test_the_budget_leaves_room_for_one_full_attempt(self):
        # El proveedor admite hasta 60 s por intento y el proxy corta a 100 s: el
        # presupuesto no puede ser tan alto que 30 + 60 se pase de 100.
        self.assertLess(_RETRY_TIME_BUDGET_SECONDS + 60.0, 100.0)

    def test_a_fast_turn_still_retries(self):
        proveedor = Provider([
            ChatResult("", None, (ToolCall("c1", "search_products", {"query": "x"}),), "tool_calls"),
            ProviderError("timeout"),
            ChatResult("listo", None, (), "stop"),
        ])
        despachante = Dispatcher()
        ToolChatRunner(proveedor, despachante).run([{"role": "user", "content": "hola"}],
                                                   with_tools=True)
        self.assertEqual(proveedor.llamadas, 3, "un turno rapido si reintenta")
        self.assertEqual(len(despachante.calls), 1, "y no repite la herramienta")

    def test_a_slow_turn_does_not_retry(self):
        # Un turno que ya tardo mas que el presupuesto: se queda en su error.
        # Se simula el reloj en vez de dormir 30 s: la prueba mide la DECISION, no
        # hace esperar a nadie.
        proveedor = Provider([
            ChatResult("", None, (ToolCall("c1", "search_products", {"query": "x"}),), "tool_calls"),
            ProviderError("timeout"),
            ChatResult("listo", None, (), "stop"),
        ])
        despachante = Dispatcher()
        original = pai_runtime.time.monotonic
        llamadas_reloj = {"n": 0}

        def reloj_lento():
            # La primera lectura (inicio) da 0; las siguientes, muy avanzadas.
            llamadas_reloj["n"] += 1
            return 0.0 if llamadas_reloj["n"] == 1 else 1000.0

        try:
            pai_runtime.time.monotonic = reloj_lento
            resultado = ToolChatRunner(proveedor, despachante).run(
                [{"role": "user", "content": "hola"}], with_tools=True)
        finally:
            pai_runtime.time.monotonic = original
        self.assertEqual(proveedor.llamadas, 2,
                         "un turno lento NO se reintenta: moriria en el proxy")
        self.assertEqual(resultado["finish_reason"], "error",
                         "devuelve su error propio, no un 502 mudo del proxy")
        self.assertEqual(len(despachante.calls), 1)

    def test_the_budget_is_configurable_for_measurement(self):
        # El valor vive en una constante del modulo y se puede bajar en una prueba
        # sin tocar el codigo de produccion.
        original = pai_runtime._RETRY_TIME_BUDGET_SECONDS
        try:
            pai_runtime._RETRY_TIME_BUDGET_SECONDS = -1.0
            proveedor = Provider([
                ChatResult("", None, (ToolCall("c1", "search_products", {"query": "x"}),), "tool_calls"),
                ProviderError("timeout"),
                ChatResult("listo", None, (), "stop"),
            ])
            ToolChatRunner(proveedor, Dispatcher()).run(
                [{"role": "user", "content": "hola"}], with_tools=True)
            self.assertEqual(proveedor.llamadas, 2, "presupuesto agotado: no reintenta")
        finally:
            pai_runtime._RETRY_TIME_BUDGET_SECONDS = original


if __name__ == "__main__":
    unittest.main()
