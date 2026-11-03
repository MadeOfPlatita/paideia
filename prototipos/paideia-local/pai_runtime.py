"""Bounded tool orchestration for Pai's local-tools.v1 dispatcher.

This module deliberately knows nothing about consent, external history, profiles,
SQL, network access, or the calculation engine. Its caller supplies an already
validated message context and a trusted dispatcher implementation.
"""

from __future__ import annotations

import copy
import json
import re
from decimal import Decimal, InvalidOperation

from providers import ChatResult, ToolCall


TOOL_NAMES = frozenset({
    "search_products",
    "get_product_detail",
    "compare_products",
    "calculate_scenario",
    "get_sources",
})
PRODUCT_FAMILIES = frozenset({
    "cuenta_remunerada",
    "deposito",
    "letra_deuda_publica",
    "fondo_tradicional",
    "etf_ucits",
})
_TOOL_CALL_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_LOCAL_PRODUCT_ID = re.compile(r"[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){0,2}\Z")
_AMOUNT = re.compile(r"(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?\Z")
_PERCENT = re.compile(r"-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,4})?\Z")
_SUCCESS_STATUSES = frozenset({"ok", "partial", "not_found"})
_DISPATCH_STATUSES = _SUCCESS_STATUSES | {"error", "rejected", "temporarily_unavailable"}
_FAILURE_MESSAGE = "No se pudo completar la respuesta solicitada."
_TOOL_FAILURE_MESSAGE = "Se rechazó una llamada de herramienta no válida."


class ToolChatRunner:
    """Run a model/tool cycle with a fixed registry and at most two tool rounds."""

    def __init__(self, provider, dispatcher, max_tool_rounds=2):
        if (not callable(getattr(provider, "chat", None))
                or not callable(getattr(dispatcher, "definitions", None))
                or not callable(getattr(dispatcher, "dispatch", None))
                or type(max_tool_rounds) is not int
                or not 0 <= max_tool_rounds <= 2):
            raise ValueError("invalid tool chat configuration")
        self._provider = provider
        self._dispatcher = dispatcher
        self._max_tool_rounds = max_tool_rounds

    @staticmethod
    def _dto(answer="", refusal=None, finish_reason=None, tool_events=None, sources=None):
        return {
            "answer": answer,
            "refusal": refusal,
            "finish_reason": finish_reason,
            "tool_events": [] if tool_events is None else tool_events,
            "sources": [] if sources is None else sources,
        }

    @classmethod
    def _failure(cls, *, tool_events, sources, tool_failure=False):
        return cls._dto(
            refusal=_TOOL_FAILURE_MESSAGE if tool_failure else _FAILURE_MESSAGE,
            finish_reason="tool_error" if tool_failure else "error",
            tool_events=tool_events,
            sources=sources,
        )

    @staticmethod
    def _valid_definitions(definitions):
        if type(definitions) is not list or not 1 <= len(definitions) <= len(TOOL_NAMES):
            return False
        names = []
        for definition in definitions:
            if type(definition) is not dict or set(definition) != {"type", "function"}:
                return False
            if definition.get("type") != "function":
                return False
            function = definition.get("function")
            if type(function) is not dict:
                return False
            if set(function) - {"name", "description", "parameters"}:
                return False
            name = function.get("name")
            parameters = function.get("parameters")
            if (type(name) is not str or name not in TOOL_NAMES
                    or not {"name", "parameters"}.issubset(function)
                    or type(parameters) is not dict or parameters.get("type") != "object"
                    or ("description" in function and type(function["description"]) is not str)):
                return False
            names.append(name)
        return len(set(names)) == len(names) and set(names).issubset(TOOL_NAMES)

    @staticmethod
    def _is_local_product_id(value):
        return type(value) is str and _LOCAL_PRODUCT_ID.fullmatch(value) is not None

    @classmethod
    def _valid_arguments(cls, name, arguments):
        if type(arguments) is not dict:
            return False

        if name == "search_products":
            return (
                set(arguments) == {"query", "family", "limit"}
                and type(arguments["query"]) is str and len(arguments["query"]) <= 100
                and (arguments["family"] is None or (
                    type(arguments["family"]) is str and arguments["family"] in PRODUCT_FAMILIES
                ))
                and type(arguments["limit"]) is int and 1 <= arguments["limit"] <= 20
            )

        if name == "get_product_detail":
            return (
                set(arguments) == {"product_id"}
                and cls._is_local_product_id(arguments["product_id"])
            )

        if name == "compare_products":
            product_ids = arguments.get("product_ids")
            criterion = arguments.get("criterion")
            return (
                set(arguments) == {"product_ids", "criterion"}
                and type(product_ids) is list and 2 <= len(product_ids) <= 4
                and all(cls._is_local_product_id(item) for item in product_ids)
                and len(set(product_ids)) == len(product_ids)
                and (criterion is None or criterion == "deposit_tae_12m_eur")
            )

        if name == "calculate_scenario":
            expected = {
                "principal", "annual_rate_percent", "years",
                "monthly_contribution", "method", "inflation_percent",
            }
            if set(arguments) != expected:
                return False
            for key in ("principal", "monthly_contribution"):
                value = arguments[key]
                if type(value) is not str or _AMOUNT.fullmatch(value) is None:
                    return False
                try:
                    if Decimal(value) > Decimal("1000000000.00"):
                        return False
                except (InvalidOperation, ValueError):
                    return False
            for key in ("annual_rate_percent", "inflation_percent"):
                value = arguments[key]
                if type(value) is not str or _PERCENT.fullmatch(value) is None:
                    return False
                try:
                    rate = Decimal(value)
                except (InvalidOperation, ValueError):
                    return False
                if rate <= Decimal("-100") or rate > Decimal("1000"):
                    return False
            years = arguments["years"]
            return (
                type(years) is int and 1 <= years <= 40
                and type(arguments["method"]) is str
                and arguments["method"] in {"simple", "compound"}
            )

        if name == "get_sources":
            product_ids = arguments.get("product_ids")
            return (
                set(arguments) == {"product_ids"}
                and type(product_ids) is list and 1 <= len(product_ids) <= 20
                and all(cls._is_local_product_id(item) for item in product_ids)
                and len(set(product_ids)) == len(product_ids)
            )

        return False

    @staticmethod
    def _valid_call_id(value):
        return type(value) is str and _TOOL_CALL_ID.fullmatch(value) is not None

    @staticmethod
    def _event(call, *, state, status):
        call_id = getattr(call, "id", None)
        name = getattr(call, "name", None)
        return {
            "tool_call_id": call_id if ToolChatRunner._valid_call_id(call_id) else None,
            "name": name if type(name) is str and name in TOOL_NAMES else None,
            "state": state,
            "status": status,
        }

    @staticmethod
    def _json_text(value):
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    @classmethod
    def _valid_dispatch_result(cls, result, expected_tool):
        if (type(result) is not dict
                or set(result) != {"schema_version", "tool", "status", "data", "sources", "error"}
                or result.get("schema_version") != "local-tools.v1"
                or result.get("tool") != expected_tool
                or type(result.get("status")) is not str
                or result["status"] not in _DISPATCH_STATUSES
                or type(result.get("data")) is not dict
                or type(result.get("sources")) is not list
                or len(result["sources"]) > 20
                or not all(type(source) is dict for source in result["sources"])
                or (result.get("error") is not None and type(result["error"]) is not dict)):
            return False
        try:
            cls._json_text(result)
        except (TypeError, ValueError, RecursionError, OverflowError):
            return False
        return True

    @staticmethod
    def _valid_chat_result(result):
        return (
            isinstance(result, ChatResult)
            and type(result.answer) is str
            and (result.refusal is None or type(result.refusal) is str)
            and (result.finish_reason is None or type(result.finish_reason) is str)
            and type(result.tool_calls) is tuple
            and all(isinstance(call, ToolCall) for call in result.tool_calls)
        )

    def run(self, messages):
        """Run one bounded turn over messages already authorized by the service."""
        tool_events = []
        sources = []
        try:
            current_messages = copy.deepcopy(messages)
            definitions = copy.deepcopy(self._dispatcher.definitions())
        except Exception:
            return self._failure(tool_events=tool_events, sources=sources)
        if not self._valid_definitions(definitions):
            return self._failure(tool_events=tool_events, sources=sources)

        advertised_names = frozenset(item["function"]["name"] for item in definitions)
        seen_call_ids = set()
        seen_invocations = set()
        tool_rounds = 0

        for _model_call in range(self._max_tool_rounds + 1):
            try:
                result = self._provider.chat(copy.deepcopy(current_messages), tools=copy.deepcopy(definitions))
            except Exception:
                return self._failure(tool_events=tool_events, sources=sources)
            if not self._valid_chat_result(result):
                return self._failure(tool_events=tool_events, sources=sources)

            # Reasoning is intentionally ignored: it is neither returned nor appended to context.
            if result.refusal is not None:
                return self._dto(result.answer, result.refusal, result.finish_reason, tool_events, sources)
            if result.finish_reason == "length":
                return self._dto(result.answer, None, result.finish_reason, tool_events, sources)
            if not result.tool_calls:
                return self._dto(result.answer, None, result.finish_reason, tool_events, sources)
            if len(result.tool_calls) != 1:
                for call in result.tool_calls:
                    tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)

            call = result.tool_calls[0]
            if not self._valid_call_id(call.id):
                tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)
            if call.id in seen_call_ids:
                tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)
            seen_call_ids.add(call.id)

            if type(call.name) is not str or call.name not in advertised_names:
                tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)
            if not self._valid_arguments(call.name, call.arguments):
                tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)
            if tool_rounds >= self._max_tool_rounds:
                tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)

            try:
                invocation = (call.name, self._json_text(call.arguments))
            except (TypeError, ValueError, RecursionError, OverflowError):
                tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)
            if invocation in seen_invocations:
                tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)
            seen_invocations.add(invocation)

            try:
                dispatched = self._dispatcher.dispatch(call.name, copy.deepcopy(call.arguments))
            except Exception:
                tool_events.append(self._event(call, state="rejected", status="temporarily_unavailable"))
                return self._failure(tool_events=tool_events, sources=sources)
            if not self._valid_dispatch_result(dispatched, call.name):
                tool_events.append(self._event(call, state="rejected", status="rejected"))
                return self._failure(tool_events=tool_events, sources=sources)

            status = dispatched["status"]
            if status not in _SUCCESS_STATUSES or dispatched["error"] is not None:
                tool_events.append(self._event(call, state="rejected", status=status))
                return self._failure(tool_events=tool_events, sources=sources)

            tool_events.append(self._event(call, state="executed", status=status))
            for source in dispatched["sources"]:
                sources.append({
                    "tool_call_id": call.id,
                    "tool": call.name,
                    "source": copy.deepcopy(source),
                })

            assistant_message = {"role": "assistant"}
            if result.answer:
                assistant_message["content"] = result.answer
            assistant_message["tool_calls"] = [{
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": self._json_text(call.arguments),
                },
            }]
            model_result = copy.deepcopy(dispatched)
            if call.name == "search_products" and isinstance(model_result["data"].get("items"), list):
                # Preserve all identities, but do not duplicate full URL/unknown-field metadata
                # in the small model context. Complete citations remain in the service DTO.
                fields = {"id", "name", "family", "identity_state", "publication_ready", "conditions_state"}
                model_result["data"]["items"] = [
                    {key: value for key, value in item.items() if key in fields}
                    for item in model_result["data"]["items"]
                ]
                model_result["data"]["model_projection"] = "identity_summary_only_not_verified_offer"
                model_result["sources"] = [
                    {key: value for key, value in source.items() if key in {"source_ref", "claim_scope"}}
                    for source in model_result["sources"]
                ]
            tool_message = {
                "role": "tool",
                "tool_call_id": call.id,
                "name": call.name,
                "content": self._json_text({"untrusted_tool_result": model_result}),
            }
            current_messages.extend((assistant_message, tool_message))
            tool_rounds += 1

        return self._failure(tool_events=tool_events, sources=sources, tool_failure=True)
