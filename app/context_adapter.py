"""Local-only bridge from profile 05 to projection 04 and benchmark 03.

This module never opens a network connection. The HTTP preview entry point accepts
only an allowlisted synthetic fixture ID and loads that fixture itself; it does not
accept a profile from the request body.
"""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Mapping
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any


FIXTURE_ID = "synthetic-full-profile-01"
_FIXTURE_KEYS = frozenset({"synthetic_fixture", "fixture_id", "purpose", "selected_fields", "consent"})
_CONSENT_KEYS = frozenset({"notice_version", "accepted_chat_processing", "purpose", "approved_fields"})
_VARIANTS = frozenset({"A", "B", "C"})
_MAX_QUESTION_LENGTH = 4000
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROFILE_PROJECTION_PATH = _PROJECT_ROOT / "docs" / "validacion-04" / "04-contexto" / "profile_projection.py"
_PROFILE_FIXTURE_PATH = (
    _PROJECT_ROOT
    / "docs"
    / "validacion-04"
    / "04-contexto"
    / "fixtures"
    / "synthetic-full-profile.json"
)
_BENCHMARK_MODULE_PATH = _PROJECT_ROOT / "docs" / "validacion-04" / "03-benchmark" / "pai_context_benchmark.py"
_BENCHMARK_DATASET_PATH = _PROJECT_ROOT / "docs" / "validacion-04" / "03-benchmark" / "dataset.json"


class AdapterError(ValueError):
    """Controlled adapter failure with a stable code suitable for an API error body."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _load_module(module_name: str, path: Path) -> ModuleType:
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError("No Python loader for local source")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except (OSError, ImportError, SyntaxError) as exc:
        raise AdapterError("LOCAL_SOURCE_UNAVAILABLE", f"No se pudo cargar el módulo local {path.name}.") from exc


@lru_cache(maxsize=1)
def _projection_module() -> ModuleType:
    return _load_module("paideia_local_profile_projection", _PROFILE_PROJECTION_PATH)


@lru_cache(maxsize=1)
def _benchmark_module() -> ModuleType:
    return _load_module("paideia_local_context_benchmark", _BENCHMARK_MODULE_PATH)


def _read_authorized_fixture() -> dict[str, Any]:
    try:
        fixture = json.loads(_PROFILE_FIXTURE_PATH.read_text(encoding="utf-8"), parse_float=Decimal)
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError("FIXTURE_UNAVAILABLE", "No se pudo leer la fixture sintética autorizada.") from exc
    if (
        not isinstance(fixture, dict)
        or set(fixture) != {"classification", "fixture_id", "profile"}
        or fixture.get("classification") != "synthetic_fixture"
        or fixture.get("fixture_id") != FIXTURE_ID
        or not isinstance(fixture.get("profile"), Mapping)
    ):
        raise AdapterError("FIXTURE_INVALID", "La fixture local no coincide con el contrato sintético allowlisted.")
    return fixture


def _validate_projection_arguments(purpose: Any, selected_fields: Any, consent: Any) -> None:
    if not isinstance(purpose, str):
        raise AdapterError("PROJECTION_INVALID", "purpose debe ser una cadena del contrato cerrado 04.")
    if not isinstance(selected_fields, list) or any(not isinstance(field, str) for field in selected_fields):
        raise AdapterError("PROJECTION_INVALID", "selected_fields debe ser una lista de nombres de campo.")
    if len(selected_fields) != len(set(selected_fields)):
        raise AdapterError("PROJECTION_INVALID", "selected_fields no puede contener campos duplicados.")
    if not isinstance(consent, Mapping) or set(consent) != _CONSENT_KEYS:
        raise AdapterError("CONSENT_INVALID", "consent debe contener exactamente los cuatro campos del contrato 04.")
    if (
        not isinstance(consent.get("notice_version"), str)
        or not consent["notice_version"].strip()
        or len(consent["notice_version"]) > 64
        or type(consent.get("accepted_chat_processing")) is not bool
        or not isinstance(consent.get("purpose"), str)
        or not isinstance(consent.get("approved_fields"), list)
        or any(not isinstance(field, str) for field in consent["approved_fields"])
        or len(consent["approved_fields"]) != len(set(consent["approved_fields"]))
    ):
        raise AdapterError("CONSENT_INVALID", "El consentimiento no cumple la estructura cerrada del contrato 04.")


def _project_profile(profile: Any, purpose: Any, selected_fields: Any, consent: Any) -> dict[str, Any]:
    _validate_projection_arguments(purpose, selected_fields, consent)
    if not isinstance(profile, Mapping):
        raise AdapterError("PROJECTION_INVALID", "profile debe ser un objeto de perfil local 05.")
    projector = _projection_module()
    try:
        return projector.project_profile(
            profile,
            purpose=purpose,
            selected_fields=selected_fields,
            consent=consent,
        )
    except projector.ConsentError as exc:
        raise AdapterError("CONSENT_INVALID", str(exc)) from exc
    except projector.ProjectionError as exc:
        raise AdapterError("PROJECTION_INVALID", str(exc)) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise AdapterError("PROJECTION_INVALID", "El perfil no satisface el contrato cerrado del proyector 04.") from exc


def preview_synthetic(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Project the bundled synthetic fixture; never trusts a caller-supplied profile."""
    if not isinstance(payload, Mapping) or set(payload) != _FIXTURE_KEYS:
        raise AdapterError(
            "INVALID_PAYLOAD",
            "El payload debe contener únicamente synthetic_fixture, fixture_id, purpose, selected_fields y consent.",
        )
    if type(payload.get("synthetic_fixture")) is not bool or payload["synthetic_fixture"] is not True:
        raise AdapterError("SYNTHETIC_FIXTURE_REQUIRED", "La vista previa admite exclusivamente synthetic_fixture=true.")
    if not isinstance(payload.get("fixture_id"), str) or payload["fixture_id"] != FIXTURE_ID:
        raise AdapterError("FIXTURE_NOT_ALLOWLISTED", "fixture_id no está allowlisted para la vista previa local.")

    fixture = _read_authorized_fixture()
    projection = _project_profile(
        fixture["profile"],
        payload.get("purpose"),
        payload.get("selected_fields"),
        payload.get("consent"),
    )
    return {"projection": projection, "external_sent": False}


def _same_typed_value(expected: Any, actual: Any) -> bool:
    """Compare fixture values without treating bool/int or Decimal/int as identical."""
    if isinstance(expected, Mapping):
        return (
            isinstance(actual, Mapping)
            and set(expected) == set(actual)
            and all(_same_typed_value(value, actual[key]) for key, value in expected.items())
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(expected) == len(actual)
            and all(_same_typed_value(left, right) for left, right in zip(expected, actual))
        )
    return type(expected) is type(actual) and expected == actual


def _full_fixture_projection(profile: Mapping[str, Any]) -> dict[str, Any]:
    fixture = _read_authorized_fixture()
    if not _same_typed_value(fixture["profile"], profile):
        raise AdapterError(
            "SYNTHETIC_FIXTURE_REQUIRED",
            "La variante C está reservada a la fixture sintética allowlisted exacta.",
        )
    projector = _projection_module()
    try:
        return projector.project_synthetic_full_for_benchmark(
            {"classification": "synthetic_fixture", "fixture_id": FIXTURE_ID, "profile": profile}
        )
    except projector.ProjectionError as exc:
        raise AdapterError("PROJECTION_INVALID", str(exc)) from exc


def _benchmark_fields(projection_module: ModuleType) -> list[str]:
    return sorted(set().union(*projection_module.PURPOSE_FIELDS.values()))


def build_context_request(
    profile: Mapping[str, Any],
    purpose: str,
    selected_fields: list[str],
    consent: Mapping[str, Any],
    question: str,
    variant: str = "B",
) -> dict[str, Any]:
    """Build an offline Pai A/B/C request using 03's real materializer.

    A carries no profile fields; B carries only the consented 04 DTO selection.
    C is a benchmark-only path and accepts only the exact allowlisted fixture.
    This function constructs messages but does not send or persist them.
    """
    if not isinstance(variant, str) or variant not in _VARIANTS:
        raise AdapterError("VARIANT_INVALID", "variant debe ser A, B o C.")
    if not isinstance(question, str) or not question.strip() or len(question) > _MAX_QUESTION_LENGTH:
        raise AdapterError("QUESTION_INVALID", "question debe ser texto no vacío de hasta 4000 caracteres.")

    projection = _project_profile(profile, purpose, selected_fields, consent)
    projector = _projection_module()
    selected_dto = projection["fields"]
    if variant == "C":
        request_profile = _full_fixture_projection(profile)["fields"]
    else:
        request_profile = {}

    benchmark = _benchmark_module()
    try:
        source_dataset = benchmark.load_dataset(_BENCHMARK_DATASET_PATH)
        benchmark.validate_dataset(source_dataset)
    except benchmark.BenchmarkError as exc:
        raise AdapterError("BENCHMARK_INVALID", str(exc)) from exc

    profile_fields = _benchmark_fields(projector)
    dataset = {
        "profile_fields": profile_fields,
        "prompt_contract": source_dataset["prompt_contract"],
    }
    case = {
        "case_id": "SYN-CONTEXT-ADAPTER",
        "profile": request_profile,
        "projection_fields": list(selected_fields),
        "projection_exclusion_reason": "Campo no seleccionado para esta petición; permanece fuera del contexto.",
        "relevant_projection": {field: selected_dto[field] for field in selected_fields},
        "question": question,
        "fixed_evidence": {},
    }
    try:
        return benchmark.materialize_request(dataset, case, variant)
    except benchmark.BenchmarkError as exc:
        raise AdapterError("BENCHMARK_INVALID", str(exc)) from exc
