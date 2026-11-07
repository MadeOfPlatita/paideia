"""Construcción del servicio de chat de Pai desde el entorno local.

La ruta ordinaria conserva el comportamiento histórico que usa `app.py`: sin
`PAIDEIA_GROQ_ENABLED=1` y sin `GROQ_API_KEY` devuelve el servicio deshabilitado
de siempre (`CHAT_NOT_CONFIGURED`); con ambos construye
`GroqProvider.from_environment` bajo la admisión con cupo en memoria de este
proceso (6 llamadas por minuto y 60 por día).  Esta ruta no lee ni exige estado
de misión.

El modo nocturno contado es un camino separado y explícito.  Solo se construye
con `night_mission=True` y `PAIDEIA_NIGHT_MISSION_ENABLED=1`, además del opt-in
y la clave de Groq.  Cada turno pasa por `secure_groq_session.Session` y por el
ledger canónico de la misión (20 intentos globales, corte incluido).  Si falta
el sello, la ventana está cerrada o cualquier paso falla, devuelve el servicio
deshabilitado: nunca cae a `GroqProvider.from_environment`.

Las pruebas de esa ruta usan exclusivamente `test_only=True` con
`StructuredSessionFixture` y un reloj inyectado; no se abre red.  La ruta
nocturna no está conectada a `app.py`; ninguna de las dos cambia credenciales.
"""

from datetime import datetime, timezone
import os
from pathlib import Path

from backend_services import CatalogueComparisonService, LocalChatService
from catalogue_adapter import CatalogueWithConditions
from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission
from conditions_service import ConditionsService
from mission_budget import MissionBudget, MissionConfig, load_mission, read_night_seal
import mission_budget
from pai_tools import ToolDispatcher
from providers import (
    API_KEY_ENV,
    active_provider_name,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_OUTPUT_TOKENS,
    OPT_IN_ENV,
    GroqHTTPSJSONTransport,
    GroqProvider,
    model_is_allowed,
)
from secure_groq_session import Session
from structured_session_fixture import StructuredSessionFixture


MODEL_ENV = "PAIDEIA_GROQ_MODEL"
# Modelo para proveedores distintos de Groq; si falta, el predeterminado del proveedor.
PROVIDER_MODEL_ENV = "PAIDEIA_LLM_MODEL"
TIMEOUT_ENV = "PAIDEIA_GROQ_TIMEOUT"
TOKENS_ENV = "PAIDEIA_GROQ_MAX_TOKENS"
SCOPE = "paideia-chat-local"
MAX_TIMEOUT_SECONDS = 60.0
CHAT_OUTPUT_TOKENS = 2400
# Additional, explicit opt-in for the counted mission route.  It is not used by
# the ordinary application route and does not alter the historical env names.
NIGHT_OPT_IN_ENV = "PAIDEIA_NIGHT_MISSION_ENABLED"
# Immutable identity source created offline.  It never determines state paths:
# an identical copy in any checkout is the same mission and always resolves to
# the canonical per-profile directory.
DOCUMENT_MANIFEST = Path(__file__).resolve().parents[1] / 'docs' / 'mision-nocturna-20261104' / 'MISSION.json'


def _timeout():
    try:
        value = float(os.environ.get(TIMEOUT_ENV, MAX_TIMEOUT_SECONDS))
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS
    if value != value or value < 0.1:
        return DEFAULT_TIMEOUT_SECONDS
    return min(value, MAX_TIMEOUT_SECONDS)


def _model():
    # El nombre histórico (PAIDEIA_GROQ_MODEL) solo vale para Groq: al cambiar de
    # proveedor no debe arrastrar un modelo que allí no existe.
    if active_provider_name() == "groq":
        requested = os.environ.get(MODEL_ENV) or DEFAULT_MODEL
    else:
        requested = os.environ.get(PROVIDER_MODEL_ENV) or DEFAULT_MODEL
    return requested if model_is_allowed(requested) else DEFAULT_MODEL


def _tokens():
    try:
        value = int(os.environ.get(TOKENS_ENV, CHAT_OUTPUT_TOKENS))
    except (TypeError, ValueError):
        return CHAT_OUTPUT_TOKENS
    if value < 32:
        return CHAT_OUTPUT_TOKENS
    return min(value, MAX_OUTPUT_TOKENS)


CALLS_PER_MINUTE_ENV = "PAIDEIA_CALLS_PER_MINUTE"
CALLS_PER_DAY_ENV = "PAIDEIA_CALLS_PER_DAY"
DEFAULT_CALLS_PER_MINUTE = 6
DEFAULT_CALLS_PER_DAY = 60


def _limit(name, default, ceiling):
    """Lee un cupo del entorno, acotado: un valor absurdo no abre la puerta."""
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    if value < 1:
        return default
    return min(value, ceiling)


def _calls_per_minute():
    return _limit(CALLS_PER_MINUTE_ENV, DEFAULT_CALLS_PER_MINUTE, 60)


def _calls_per_day():
    return _limit(CALLS_PER_DAY_ENV, DEFAULT_CALLS_PER_DAY, 5000)


def _current_time(now=None):
    return now if now is not None else datetime.now(timezone.utc)


def _within_mission_window(config, now):
    """True only for an aware datetime inside [start, cutoff)."""
    try:
        return (isinstance(now, datetime) and now.utcoffset() is not None
                and config.start <= now.astimezone(timezone.utc) < config.cutoff)
    except Exception:
        return False


def _mission_config(now=None):
    """Return the authorized canonical mission config without touching state."""
    try:
        try:
            config = load_mission(mission_budget.NIGHT_MANIFEST)
        except FileNotFoundError:
            # The offline docs manifest is an identity source only.  The seal
            # and every counter still live in the canonical profile directory.
            config = load_mission(DOCUMENT_MANIFEST)
        seal = read_night_seal(config)
    except Exception:
        return None
    if type(config) is not MissionConfig or not config.sealed or not config.digest:
        return None
    ledger = config.directory / 'mission-ledger.json'
    journal = Path(str(ledger) + '.lock')
    if seal['state'] == 'initialized' and seal['used'] >= config.cap:
        return None
    try:
        if seal['state'] == 'initialized':
            if not ledger.is_file() or not journal.is_file():
                return None
        elif ledger.exists() or journal.exists():
            # A ledger or journal next to an uninitialized seal is ambiguous.
            return None
    except OSError:
        return None
    if not _within_mission_window(config, _current_time(now)):
        return None
    return config


def _mission_state_ready(config, now):
    """Pure pre-check for the isolated mission route.

    It mirrors the seal/clock conditions before any ledger is created, so an
    unauthorized mission cannot leave state behind just by being requested.
    """
    try:
        seal = read_night_seal(config)
    except Exception:
        return False
    if seal['state'] == 'initialized' and seal['used'] >= config.cap:
        return False
    return _within_mission_window(config, now)


def _valid_key(value):
    return (type(value) is str and bool(value) and value.isascii()
            and len(value) <= 4096
            and all(0x21 <= ord(character) <= 0x7E for character in value))


def chat_enabled():
    """Historical ordinary-chat check: opt-in plus key, no mission state."""
    return os.environ.get(OPT_IN_ENV) == "1" and bool(os.environ.get(API_KEY_ENV))


def _historical_chat_service(repository=None, comparison_service=None):
    """The ordinary `app.py` route, unchanged from before the night mission.

    The in-memory admission is per process and is not the mission ledger; the
    catalogue remains read-only.  This route never consults mission state.
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
        calls_per_minute=_calls_per_minute(),
        calls_per_day=_calls_per_day(),
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
        ToolDispatcher(CatalogueWithConditions(repository, ConditionsService()),
                       comparison_service if comparison_service is not None else CatalogueComparisonService())
        if tools else None
    )
    return LocalChatService(
        provider=provider,
        enabled=True,
        admission=admission,
        dispatcher=dispatcher,
        tools_enabled=tools,
        tools_scope="catalogue_read",
        catalogue_usage_approved=True,
        context_enabled=True,
    )


def _night_chat_service(repository=None, comparison_service=None, *, test_only=False,
                        transport=None, clock=None, mission_config=None):
    """Counted mission route.  Every failure returns a disabled service.

    This function is never called by the historical route.  A closed synthetic
    transport is accepted only with `test_only=True`; production uses the real
    counted session transport without opening it during construction.
    """
    if os.environ.get(NIGHT_OPT_IN_ENV) != "1":
        return LocalChatService()
    if os.environ.get(OPT_IN_ENV) != "1" or not os.environ.get(API_KEY_ENV):
        return LocalChatService()
    if test_only:
        if type(transport) is not StructuredSessionFixture:
            raise ValueError('closed synthetic transport required')
        if not callable(clock):
            raise ValueError('synthetic clock required')
        if type(mission_config) is not MissionConfig:
            raise ValueError('mission config required')
        config = mission_config
        try:
            now = clock()
        except Exception:
            return LocalChatService()
    else:
        if transport is not None or clock is not None or mission_config is not None:
            raise ValueError('test injection is disabled')
        config = _mission_config()
        now = _current_time()
    if config is None:
        return LocalChatService()
    if type(config) is not MissionConfig or not config.sealed or not config.digest:
        return LocalChatService()
    if not _mission_state_ready(config, now):
        return LocalChatService()
    key = os.environ.get(API_KEY_ENV)
    if not _valid_key(key):
        return LocalChatService()
    budget = None
    session = None
    try:
        budget = MissionBudget(config)
        session = Session(key, test_only=test_only, transport=transport, clock=clock,
                          mission_budget=budget, model=_model(), timeout=_timeout(),
                          max_output_tokens=_tokens())
        limit = config.cap
        policy = AdmissionPolicy(
            max_concurrent=1,
            max_queue=4,
            calls_per_minute=min(6, limit),
            calls_per_day=limit,
            ticket_ttl_seconds=120,
            claim_ttl_seconds=60,
            scope=SCOPE,
        )
        admission = InterfazChatAdmission(
            policy,
            clock=clock if test_only else (lambda: datetime.now(timezone.utc)),
            budget_state=InMemoryBudgetState.new_empty(scope=SCOPE),
        )
        tools = repository is not None
        dispatcher = (
            ToolDispatcher(CatalogueWithConditions(repository, ConditionsService()),
                           comparison_service if comparison_service is not None else CatalogueComparisonService())
            if tools else None
        )
        service = LocalChatService(
            provider=session.provider,
            enabled=True,
            test_only=test_only,
            admission=admission,
            dispatcher=dispatcher,
            tools_enabled=tools,
            tools_scope="catalogue_read",
            catalogue_usage_approved=True,
            context_enabled=True,
        )
    except Exception:
        # Fail closed: an ambiguous or unsupported mission state must not take
        # down the normal application, and must never build the ordinary
        # provider as a fallback.
        try:
            if session is not None:
                session.close()
            elif budget is not None:
                budget.close()
        except Exception:
            pass
        return LocalChatService()
    # The caller owns the service for the life of the process; tests can close
    # the session explicitly.  The budget lock serialises the mission.
    service._mission_session = session
    service._mission_budget = budget
    return service


def build_chat_service(repository=None, comparison_service=None, *, night_mission=False,
                       test_only=False, transport=None, clock=None, mission_config=None):
    """Build Pai's chat service for `app.py`.

    The default is the historical ordinary route.  The counted night mission is
    a separate explicit opt-in and is never selected implicitly by environment
    variables or by the absence of mission state.
    """
    if type(night_mission) is not bool:
        raise ValueError('invalid night mission mode')
    if type(test_only) is not bool:
        raise ValueError('invalid test mode')
    if not night_mission:
        if test_only or transport is not None or clock is not None or mission_config is not None:
            raise ValueError('night mission injection requires night_mission=True')
        return _historical_chat_service(repository, comparison_service)
    if test_only:
        if type(transport) is not StructuredSessionFixture:
            raise ValueError('closed synthetic transport required')
        if not callable(clock):
            raise ValueError('synthetic clock required')
        if type(mission_config) is not MissionConfig:
            raise ValueError('mission config required')
    elif transport is not None or clock is not None or mission_config is not None:
        raise ValueError('test injection is disabled')
    return _night_chat_service(
        repository,
        comparison_service,
        test_only=test_only,
        transport=transport,
        clock=clock,
        mission_config=mission_config,
    )
