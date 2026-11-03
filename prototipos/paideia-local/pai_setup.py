"""Construcción del servicio de chat de Pai desde el entorno local.

Sin `PAIDEIA_GROQ_ENABLED=1` y sin `GROQ_API_KEY`, devuelve el servicio
deshabilitado de siempre (`CHAT_NOT_CONFIGURED`). Con ambos, conecta el
adaptador Groq existente bajo la admisión con cupo en memoria de este proceso.
No lee claves de argumentos, navegador ni logs, y no las devuelve.
"""

from datetime import datetime, timezone
import os

from backend_services import CatalogueComparisonService, LocalChatService
from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission
from pai_tools import ToolDispatcher
from providers import (
    ALLOWED_MODELS,
    API_KEY_ENV,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_OUTPUT_TOKENS,
    OPT_IN_ENV,
    GroqHTTPSJSONTransport,
    GroqProvider,
)


MODEL_ENV = "PAIDEIA_GROQ_MODEL"
TIMEOUT_ENV = "PAIDEIA_GROQ_TIMEOUT"
TOKENS_ENV = "PAIDEIA_GROQ_MAX_TOKENS"
SCOPE = "paideia-chat-local"
MAX_TIMEOUT_SECONDS = 20.0
CHAT_OUTPUT_TOKENS = 800


def _timeout():
    try:
        value = float(os.environ.get(TIMEOUT_ENV, MAX_TIMEOUT_SECONDS))
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS
    if value != value or value < 0.1:
        return DEFAULT_TIMEOUT_SECONDS
    return min(value, MAX_TIMEOUT_SECONDS)


def _model():
    requested = os.environ.get(MODEL_ENV, DEFAULT_MODEL)
    return requested if requested in ALLOWED_MODELS else DEFAULT_MODEL


def _tokens():
    try:
        value = int(os.environ.get(TOKENS_ENV, CHAT_OUTPUT_TOKENS))
    except (TypeError, ValueError):
        return CHAT_OUTPUT_TOKENS
    if value < 32:
        return CHAT_OUTPUT_TOKENS
    return min(value, MAX_OUTPUT_TOKENS)


def chat_enabled():
    return os.environ.get(OPT_IN_ENV) == "1" and bool(os.environ.get(API_KEY_ENV))


def build_chat_service(repository=None, comparison_service=None):
    """Servicio de chat listo para `app.py`; deshabilitado si falta opt-in o clave.

    Con repositorio y servicio de comparación, Pai puede usar la calculadora
    local (`calculate_scenario`) y nada más: nunca el catálogo.
    """
    if not chat_enabled():
        return LocalChatService()
    provider = GroqProvider.from_environment(
        GroqHTTPSJSONTransport(),
        model=_model(),
        timeout=_timeout(),
        max_output_tokens=_tokens(),
    )
    policy = AdmissionPolicy(
        max_concurrent=1,
        max_queue=4,
        calls_per_minute=6,
        calls_per_day=60,
        ticket_ttl_seconds=120,
        claim_ttl_seconds=60,
        scope=SCOPE,
    )
    admission = InterfazChatAdmission(
        policy,
        clock=lambda: datetime.now(timezone.utc),
        budget_state=InMemoryBudgetState.new_empty(scope=SCOPE),
    )
    tools = repository is not None
    dispatcher = (
        ToolDispatcher(repository, comparison_service if comparison_service is not None else CatalogueComparisonService())
        if tools else None
    )
    return LocalChatService(
        provider=provider,
        enabled=True,
        admission=admission,
        dispatcher=dispatcher,
        tools_enabled=tools,
        tools_scope="calculator_only",
        context_enabled=True,
    )
