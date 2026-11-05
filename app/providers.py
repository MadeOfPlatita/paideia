
"""Adaptador de chat acotado y opt-in. Ninguna ruta de la aplicación se registra aquí.

Hay dos proveedores compatibles con OpenAI y ambos quedan anclados: el host y la
ruta son constantes de este módulo, no configuración arbitraria, así que la clave
solo puede viajar a uno de esos dos destinos. Se elige con
``PAIDEIA_LLM_PROVIDER`` (``groq`` por defecto, ``commandcode`` para la
suscripción de Command Code).
"""

from __future__ import annotations

import json
import http.client
import os
import re
import socket
from contextlib import nullcontext
from dataclasses import dataclass
from enum import Enum

PROVIDER_ENV = "PAIDEIA_LLM_PROVIDER"
DEFAULT_PROVIDER = "groq"

PROVIDERS = {
    "groq": {
        "label": "Groq",
        "host": "api.groq.com",
        "path": "/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "default_model": "openai/gpt-oss-20b",
        # Catálogo cerrado: en Groq solo se admiten estos dos modelos.
        "models": frozenset({"openai/gpt-oss-20b", "openai/gpt-oss-120b"}),
    },
    "vercel": {
        "label": "Vercel AI Gateway",
        "host": "ai-gateway.vercel.sh",
        "path": "/v1/chat/completions",
        "key_env": "AI_GATEWAY_API_KEY",
        "default_model": "reflection/beam-free",
        # Beam 1.0 gratuito durante el lanzamiento; la ruta -free deja de servir
        # cuando termina la oferta, así que no puede convertirse en factura.
        "models": None,
    },
    "commandcode": {
        "label": "Command Code",
        "host": "api.commandcode.ai",
        "path": "/provider/v1/chat/completions",
        "key_env": "COMMANDCODE_API_KEY",
        # Beam 1.0 gratuito dentro del plan de Command Code (0 % de uso hoy).
        "default_model": "reflection/beam:free",
        # El catálogo de la suscripción cambia sin aviso: se valida la forma del
        # identificador, no una lista que quedaría obsoleta.
        "models": None,
    },
}


def active_provider_name():
    name = (os.environ.get(PROVIDER_ENV) or DEFAULT_PROVIDER).strip().lower()
    return name if name in PROVIDERS else DEFAULT_PROVIDER


_ACTIVE = PROVIDERS[active_provider_name()]
PROVIDER_LABEL = _ACTIVE["label"]
API_HOST = _ACTIVE["host"]
API_PATH = _ACTIVE["path"]
API_KEY_ENV = _ACTIVE["key_env"]
ALLOWED_MODELS = _ACTIVE["models"]
DEFAULT_MODEL = _ACTIVE["default_model"]
# Nombres históricos: el resto del proyecto (y sus pruebas) los importan.
GROQ_HOST = API_HOST
GROQ_PATH = API_PATH


def model_is_allowed(model):
    """Un modelo de la lista cerrada, o un identificador con forma válida.

    El catálogo usa dos puntos para las rutas gratuitas (`reflection/beam:free`),
    así que la forma admitida los incluye.
    """
    if type(model) is not str:
        return False
    if ALLOWED_MODELS is not None:
        return model in ALLOWED_MODELS
    return re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}(/[A-Za-z0-9._:-]{1,64})?", model) is not None


DEFAULT_OUTPUT_TOKENS = 256
MAX_OUTPUT_TOKENS = 900
MAX_REQUEST_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 64 * 1024
# Tope de llamadas de herramienta en un mismo turno del modelo: por encima
# de este numero la respuesta se considera invalida, no se ejecuta nada.
MAX_TOOL_CALLS_PER_TURN = 8
DEFAULT_TIMEOUT_SECONDS = 5.0
OPT_IN_ENV = "PAIDEIA_GROQ_ENABLED"


def _valid_name(value):
    return type(value) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is not None


def _reject_constant(_value):
    raise ValueError("invalid JSON")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _decode_json_object_text(value):
    if type(value) is not str:
        return None
    failed = False
    try:
        decoded = json.loads(
            value,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError, RecursionError):
        decoded = None
        failed = True
    if failed or type(decoded) is not dict:
        return None
    return decoded


def _valid_json_object_text(value):
    return _decode_json_object_text(value) is not None


def _validate_messages(messages):
    allowed = {
        "system": {"role", "content"},
        "user": {"role", "content"},
        "assistant": {"role", "content", "tool_calls"},
        "tool": {"role", "tool_call_id", "name", "content"},
    }
    pending = {}
    validated = []
    for message in messages:
        if type(message) is not dict:
            raise ValueError("invalid request")
        role = message.get("role")
        if type(role) is not str or role not in allowed or set(message) - allowed[role]:
            raise ValueError("invalid request")
        if role in {"system", "user"}:
            if set(message) != {"role", "content"} or type(message["content"]) is not str:
                raise ValueError("invalid request")
            validated.append({"role": role, "content": message["content"]})
            continue
        if role == "assistant":
            calls = message.get("tool_calls")
            if calls is None:
                if set(message) != {"role", "content"} or type(message["content"]) is not str:
                    raise ValueError("invalid request")
                validated.append({"role": role, "content": message["content"]})
                continue
            if (set(message) - {"role", "content", "tool_calls"} or type(calls) is not list
                    or not 1 <= len(calls) <= MAX_TOOL_CALLS_PER_TURN):
                raise ValueError("invalid request")
            content = message.get("content")
            if content is not None and type(content) is not str:
                raise ValueError("invalid request")
            clean_calls = []
            for call in calls:
                if type(call) is not dict or set(call) != {"id", "type", "function"}:
                    raise ValueError("invalid request")
                call_id = call["id"]
                function = call["function"]
                if (type(call_id) is not str or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", call_id) is None
                        or call_id in pending or call["type"] != "function"
                        or type(function) is not dict or set(function) != {"name", "arguments"}
                        or not _valid_name(function["name"])
                        or not _valid_json_object_text(function["arguments"])):
                    raise ValueError("invalid request")
                pending[call_id] = function["name"]
                clean_calls.append({
                    "id": call_id,
                    "type": "function",
                    "function": {"name": function["name"], "arguments": function["arguments"]},
                })
            clean = {"role": role, "tool_calls": clean_calls}
            if "content" in message:
                clean["content"] = content
            validated.append(clean)
            continue
        if (set(message) - {"role", "tool_call_id", "name", "content"}
                or not {"role", "tool_call_id", "content"}.issubset(message)
                or type(message["content"]) is not str):
            raise ValueError("invalid request")
        call_id = message["tool_call_id"]
        if type(call_id) is not str or call_id not in pending:
            raise ValueError("invalid request")
        if "name" in message and message["name"] != pending[call_id]:
            raise ValueError("invalid request")
        clean = {"role": "tool", "tool_call_id": call_id, "content": message["content"]}
        if "name" in message:
            clean["name"] = message["name"]
        del pending[call_id]
        validated.append(clean)
    return validated


def _validate_tools(tools):
    if type(tools) is not list or not 1 <= len(tools) <= 8:
        raise ValueError("invalid request")
    names = set()
    validated = []
    for tool in tools:
        if type(tool) is not dict or set(tool) != {"type", "function"} or tool["type"] != "function":
            raise ValueError("invalid request")
        function = tool["function"]
        allowed_fields = {"name", "description", "parameters"}
        if (type(function) is not dict or not {"name", "parameters"}.issubset(function)
                or set(function) - allowed_fields or not _valid_name(function["name"])
                or function["name"] in names or type(function["parameters"]) is not dict
                or function["parameters"].get("type") != "object"):
            raise ValueError("invalid request")
        if "description" in function and type(function["description"]) is not str:
            raise ValueError("invalid request")
        names.add(function["name"])
        validated.append(tool)
    return validated


def build_chat_request(
    messages,
    *,
    model=DEFAULT_MODEL,
    tools=None,
    max_output_tokens=DEFAULT_OUTPUT_TOKENS,
    max_request_bytes=MAX_REQUEST_BYTES,
):
    """Purely serialize a bounded Groq/OpenAI-compatible chat-completions body."""
    if not model_is_allowed(model):
        raise ValueError("invalid request")
    if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= MAX_OUTPUT_TOKENS:
        raise ValueError("invalid request")
    if type(max_request_bytes) is not int or not 1 <= max_request_bytes <= MAX_REQUEST_BYTES:
        raise ValueError("invalid request")
    if type(messages) is not list or not 1 <= len(messages) <= 32:
        raise ValueError("invalid request")

    safe_messages = _validate_messages(messages)
    document = {"model": model, "messages": safe_messages, "max_tokens": max_output_tokens,
                "reasoning_effort": "low", "include_reasoning": False}
    if tools is not None:
        document["tools"] = _validate_tools(tools)
    serialization_failed = False
    try:
        body = json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError, UnicodeError):
        body = b""
        serialization_failed = True
    if serialization_failed:
        raise ValueError("invalid request")
    if len(body) > max_request_bytes:
        raise ValueError("invalid request")
    return body


_ERROR_MESSAGES = {
    "disabled": "El proveedor IA está deshabilitado.",
    "not_configured": "El proveedor IA no está configurado.",
    "invalid_configuration": "La configuración del proveedor IA no es válida.",
    "invalid_request": "La solicitud no cumple el contrato del proveedor.",
    "timeout": "El proveedor IA agotó el tiempo de espera.",
    "transport_error": "No se pudo completar la solicitud al proveedor IA.",
    "unauthorized": "El proveedor IA rechazó la autenticación.",
    "rate_limited": "El proveedor IA indicó un límite temporal.",
    "provider_unavailable": "El proveedor IA no está disponible.",
    "provider_rejected": "El proveedor IA rechazó la solicitud.",
    "invalid_response": "La respuesta del proveedor IA no cumple el contrato.",
    # Cupo global de la misión: el envío no llegó a producirse.
    "mission_exhausted": "Se agotó el cupo de intentos reales de esta misión.",
    "mission_closed": "La ventana de la misión ya está cerrada.",
    "mission_unavailable": "No se pudo verificar el contador de intentos; no se envió nada.",
    "mission_corrupt": "El contador de intentos no es legible; no se envió nada.",
    "mission_guard_unavailable": "Falta el contador de intentos; no se envió nada.",
}


class SendState(str, Enum):
    NOT_STARTED = "not_started"
    UNKNOWN = "unknown"
    COMPLETED = "completed"


class ProviderError(RuntimeError):
    """A fixed, content-free error code safe to pass to an application boundary."""

    def __init__(self, code, *, send_state=SendState.UNKNOWN):
        if type(code) is not str or code not in _ERROR_MESSAGES:
            code = "transport_error"
        self.code = code
        self.send_state = send_state if isinstance(send_state, SendState) else SendState.UNKNOWN
        self.retryable = False
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True)
class TransportResponse:
    status: int
    body: bytes
    send_state: SendState = SendState.UNKNOWN


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class ChatResult:
    answer: str
    reasoning: str | None
    tool_calls: tuple[ToolCall, ...]
    finish_reason: str | None
    refusal: str | None = None


class GroqHTTPSJSONTransport:
    """Stdlib HTTPS transport locked to the one Groq API host and route."""

    def post(self, *, host, path, headers, body, timeout, send_guard=None):
        failure = None
        try:
            result = _GROQ_POST_IMPL(self, host=host, path=path, headers=headers, body=body, timeout=timeout, send_guard=send_guard)
        except ProviderError as error:
            failure = ProviderError(error.code, send_state=error.send_state)
        except ValueError:
            failure = ValueError("invalid transport request")
        finally:
            headers = body = send_guard = None
        if failure is not None:
            raise failure
        return result

    def _post(self, *, host, path, headers, body, timeout, send_guard=None):
        expected_headers = {"Authorization", "Content-Type", "Accept"}
        authorization = headers.get("Authorization") if type(headers) is dict else None
        valid_authorization = (
            type(authorization) is str
            and authorization.startswith("Bearer ")
            and len(authorization) > len("Bearer ")
            and all(0x21 <= ord(character) <= 0x7E for character in authorization[len("Bearer "):])
        )
        if (host != GROQ_HOST or path != GROQ_PATH or type(headers) is not dict
                or set(headers) != expected_headers or headers.get("Content-Type") != "application/json"
                or headers.get("Accept") != "application/json" or not valid_authorization
                or type(body) is not bytes or len(body) > MAX_REQUEST_BYTES
                or type(timeout) not in {int, float} or not 0.1 <= timeout <= 60.0):
            raise ValueError("invalid transport request")
        # Cupo global de la misión: se cuenta ANTES de abrir la conexión. Fuera de una
        # ventana de misión provisionada no interviene y la ruta ordinaria usa su cuota.
        try:
            from mission_ledger import MissionBlocked, reserve_for_active_mission
        except ImportError as error:  # sin contador no se envía: fail closed
            raise ProviderError("mission_guard_unavailable", send_state=SendState.NOT_STARTED) from error
        try:
            reserve_for_active_mission("groq_chat")
        except MissionBlocked as blocked:
            raise ProviderError(blocked.code.lower(), send_state=SendState.NOT_STARTED) from blocked
        state = SendState.NOT_STARTED
        connection = None
        failure = None
        try:
            connection = http.client.HTTPSConnection(GROQ_HOST, timeout=timeout)
            if send_guard is not None:
                connection.connect()
            with send_guard() if send_guard is not None else nullcontext():
                state = SendState.UNKNOWN
                connection.request("POST", GROQ_PATH, body=body, headers=headers)
                state = SendState.COMPLETED
            response = connection.getresponse()
            response_body = response.read(MAX_RESPONSE_BYTES + 1)
            result = TransportResponse(status=response.status, body=response_body, send_state=state)
        except (TimeoutError, socket.timeout):
            failure = "timeout"
        except Exception:
            failure = "transport_error"
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    if failure is None:
                        failure = "transport_error"
        if failure is not None:
            raise ProviderError(failure, send_state=state)
        return result


# Captured at definition time; class monkeypatches must not become callbacks.
_GROQ_POST_IMPL = GroqHTTPSJSONTransport._post
_GROQ_POST = GroqHTTPSJSONTransport.post
_GROQ_CLASS = GroqHTTPSJSONTransport
_counted_trust = lambda transport: False


def _real_transport_intact(transport):
    return (type(transport) is _GROQ_CLASS
            and vars(_GROQ_CLASS).get("post") is _GROQ_POST
            and vars(_GROQ_CLASS).get("_post") is _GROQ_POST_IMPL
            and not ({"post", "_post"} & object.__getattribute__(transport, "__dict__").keys()))


def _parse_output_tool_call(call):
    if type(call) is not dict or set(call) != {"id", "type", "function"}:
        raise ProviderError("invalid_response")
    call_id = call["id"]
    function = call["function"]
    if (type(function) is not dict or set(function) != {"name", "arguments"}
            or type(call_id) is not str or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", call_id) is None
            or call["type"] != "function" or not _valid_name(function["name"])):
        raise ProviderError("invalid_response")
    arguments = _decode_json_object_text(function["arguments"])
    if arguments is None:
        raise ProviderError("invalid_response")
    return ToolCall(id=call_id, name=function["name"], arguments=arguments)


def _optional_text(document, key):
    if key not in document:
        return None
    value = document[key]
    if value is not None and type(value) is not str:
        raise ProviderError("invalid_response")
    return value


def _parse_chat_response(response):
    invalid_response_object = False
    try:
        status = response.status
        body = response.body
    except Exception:
        status = None
        body = None
        invalid_response_object = True
    if invalid_response_object or type(status) is not int or type(body) is not bytes:
        raise ProviderError("invalid_response")
    if status == 401:
        raise ProviderError("unauthorized")
    if status == 429:
        raise ProviderError("rate_limited")
    if 500 <= status <= 599:
        raise ProviderError("provider_unavailable")
    if not 200 <= status <= 299:
        raise ProviderError("provider_rejected")
    if len(body) > MAX_RESPONSE_BYTES:
        raise ProviderError("invalid_response")
    invalid_json = False
    try:
        document = json.loads(
            body.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError):
        document = None
        invalid_json = True
    if invalid_json:
        raise ProviderError("invalid_response")
    if type(document) is not dict:
        raise ProviderError("invalid_response")
    choices = document.get("choices")
    if type(choices) is not list or len(choices) != 1 or type(choices[0]) is not dict:
        raise ProviderError("invalid_response")
    choice = choices[0]
    message = choice.get("message")
    finish_reason = choice.get("finish_reason")
    if (type(message) is not dict or message.get("role") != "assistant"
            or finish_reason is not None and type(finish_reason) is not str):
        raise ProviderError("invalid_response")
    # `reasoning_details` es metadato del proveedor (Command Code lo incluye
    # siempre); se descarta igual que el resto de campos no usados, pero no debe
    # invalidar una respuesta correcta.
    message_fields = {"role", "content", "reasoning", "reasoning_content", "reasoning_details",
                      "tool_calls", "refusal"}
    if set(message) - message_fields or ("reasoning" in message and "reasoning_content" in message):
        raise ProviderError("invalid_response")
    content = _optional_text(message, "content")
    reasoning_field = "reasoning" if "reasoning" in message else "reasoning_content"
    reasoning = _optional_text(message, reasoning_field)
    refusal = _optional_text(message, "refusal")
    calls_value = message.get("tool_calls", [])
    if type(calls_value) is not list or len(calls_value) > MAX_TOOL_CALLS_PER_TURN:
        raise ProviderError("invalid_response")
    tool_calls = tuple(_parse_output_tool_call(call) for call in calls_value)
    if content is None and not tool_calls and refusal is None:
        raise ProviderError("invalid_response")
    return ChatResult(
        answer=content or "",
        reasoning=reasoning,
        tool_calls=tool_calls,
        finish_reason=finish_reason,
        refusal=refusal,
    )


class GroqProvider:
    """Disabled-by-default adapter with no tool execution or app-route side effects."""

    def __init__(
        self,
        transport,
        *,
        opt_in=False,
        environment=None,
        model=DEFAULT_MODEL,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        max_request_bytes=MAX_REQUEST_BYTES,
        max_output_tokens=DEFAULT_OUTPUT_TOKENS,
    ):
        if (type(opt_in) is not bool or not callable(getattr(transport, "post", None))
                or not model_is_allowed(model)
                or type(timeout) not in {int, float} or not 0.1 <= timeout <= 60.0
                or type(max_request_bytes) is not int
                or not 1 <= max_request_bytes <= MAX_REQUEST_BYTES
                or type(max_output_tokens) is not int
                or not 1 <= max_output_tokens <= MAX_OUTPUT_TOKENS):
            raise ValueError("invalid configuration")
        self._transport = transport
        self._opt_in = opt_in
        self._environment = environment
        self._model = model
        self._timeout = float(timeout)
        self._max_request_bytes = max_request_bytes
        self._max_output_tokens = max_output_tokens

    @classmethod
    def from_environment(cls, transport, *, environment=None, **options):
        source = os.environ if environment is None else environment
        try:
            opt_in = source.get(OPT_IN_ENV) == "1"
        except Exception:
            opt_in = False
        return cls(transport, opt_in=opt_in, environment=source, **options)

    def chat(self, messages, *, tools=None):
        try:
            return self._chat(messages, tools=tools)
        finally:
            messages = tools = None

    def _chat(self, messages, *, tools=None, structured=False):
        failure = None
        try:
            result = self._chat_impl(messages, tools=tools, structured=structured)
        except ProviderError as error:
            failure = ProviderError(error.code, send_state=error.send_state)
            if hasattr(error, 'diagnostic'):
                failure.diagnostic = error.diagnostic
        finally:
            messages = tools = None
        if failure is not None:
            raise failure
        return result

    def _chat_impl(self, messages, *, tools=None, structured=False):
        if not self._opt_in:
            raise ProviderError("disabled", send_state=SendState.NOT_STARTED)
        invalid_request = False
        try:
            if structured:
                from secure_groq_session import _CountedTransport
                from structured_session_fixture import StructuredSessionFixture
                session = self._transport._session if type(self._transport) is _CountedTransport else None
                if (tools is not None or session is None or not session.test_only
                        or type(session._upstream) is not StructuredSessionFixture
                        or session._mission_budget is None or not session._mission_budget.config.digest):
                    raise ValueError("invalid request")
                from groq_structured_adapter import build_structured_request
                body = build_structured_request(messages)
            else:
                body = build_chat_request(
                    messages,
                    model=self._model,
                    tools=tools,
                    max_output_tokens=self._max_output_tokens,
                    max_request_bytes=self._max_request_bytes,
                )
        except (TypeError, ValueError):
            body = b""
            invalid_request = True
        if invalid_request:
            raise ProviderError("invalid_request", send_state=SendState.NOT_STARTED)
        environment = os.environ if self._environment is None else self._environment
        environment_error = False
        try:
            api_key = environment.get(API_KEY_ENV)
        except Exception:
            api_key = None
            environment_error = True
        if environment_error:
            raise ProviderError("not_configured", send_state=SendState.NOT_STARTED)
        if (type(api_key) is not str or not api_key or not api_key.isascii() or len(api_key) > 4096
                or any(ord(character) < 0x21 or ord(character) > 0x7E for character in api_key)):
            raise ProviderError("not_configured", send_state=SendState.NOT_STARTED)
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        transport_error = None
        send_state = SendState.UNKNOWN
        # Trust checks never inspect an arbitrary object's properties. This is
        # integrity checking of known classes, not an in-process Python sandbox.
        trusted = False
        try:
            trusted = _real_transport_intact(self._transport) or _counted_trust(self._transport)
        except Exception:
            trusted = False
        try:
            response = self._transport.post(
                host=GROQ_HOST,
                path=GROQ_PATH,
                headers=headers,
                body=body,
                timeout=self._timeout,
            )
        except ProviderError as error:
            if trusted:
                transport_error = error.code
                send_state = error.send_state
            else:
                transport_error = "transport_error"
        except (TimeoutError, socket.timeout):
            transport_error = "timeout"
        except Exception:
            transport_error = "transport_error"
        if transport_error is not None:
            raise ProviderError(transport_error, send_state=send_state)
        if trusted and type(response) is TransportResponse:
            send_state = response.send_state
        invalid_response_object = False
        try:
            raw_response = response.body
            response_status = response.status
        except Exception:
            raw_response = None
            response_status = None
            invalid_response_object = True
        if invalid_response_object:
            raise ProviderError("invalid_response", send_state=send_state)
        if (type(response_status) is int and 200 <= response_status <= 299
                and type(raw_response) is bytes and api_key.encode("ascii") in raw_response):
            raise ProviderError("invalid_response", send_state=send_state)
        try:
            result = _parse_chat_response(TransportResponse(status=response_status, body=raw_response))
        except ProviderError as error:
            error.send_state = send_state
            # Only bounded enum/boolean/count metadata, never response text or reasoning.
            diagnostic = {"http_status": response_status if type(response_status) is int and 100 <= response_status <= 599 else None,
                          "finish_reason": None, "has_content": False, "has_reasoning": False,
                          "tool_call_count": None}
            if type(response_status) is int and 200 <= response_status <= 299 and type(raw_response) is bytes and len(raw_response) <= MAX_RESPONSE_BYTES:
                try:
                    obj = json.loads(raw_response.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
                    choices = obj.get("choices") if type(obj) is dict else None
                    choice = choices[0] if type(choices) is list and len(choices) == 1 and type(choices[0]) is dict else {}
                    reason = choice.get("finish_reason")
                    if type(reason) is str and reason in {"stop", "length", "tool_calls", "content_filter"}:
                        diagnostic["finish_reason"] = reason
                    message = choice.get("message")
                    if type(message) is dict:
                        diagnostic["has_content"] = type(message.get("content")) is str and bool(message["content"].strip())
                        diagnostic["has_reasoning"] = any(type(message.get(name)) is str and bool(message[name]) for name in ("reasoning", "reasoning_content"))
                        calls = message.get("tool_calls", [])
                        diagnostic["tool_call_count"] = len(calls) if type(calls) is list else None
                except (UnicodeError, ValueError, TypeError, RecursionError):
                    pass
            error.diagnostic = diagnostic
            raise
        # Raw bytes alone miss JSON escapes and a tool's nested JSON arguments.
        pending = [result.answer, result.reasoning, result.refusal, result.finish_reason]
        for call in result.tool_calls:
            pending.extend((call.id, call.name, call.arguments))
        while pending:
            value = pending.pop()
            if isinstance(value, str) and api_key in value:
                raise ProviderError("invalid_response", send_state=send_state)
            if isinstance(value, dict):
                pending.extend(value.keys())
                pending.extend(value.values())
            elif isinstance(value, (list, tuple)):
                pending.extend(value)
        return result
