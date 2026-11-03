#!/usr/bin/env python3
"""Validador local de contrato/fixtures. No descarga fuentes ni publica datos."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # No instala dependencias automáticamente.
    raise SystemExit("Falta jsonschema; no se instala automáticamente.") from exc

ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "adapter.schema.json"
FIXTURE_PATH = ROOT / "fixtures" / "casos.json"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fail(message: str) -> None:
    raise AssertionError(message)


def validate_raw_hash(case: dict, record: dict) -> None:
    raw = case["source_text"].encode("utf-8")
    expected = hashlib.sha256(raw).hexdigest()
    actual = record["source"]["raw_evidence"]["sha256"]
    if actual != expected:
        fail(f"{case['case_id']}: raw SHA-256 no corresponde al texto sintético")
    if not case["source_text"].startswith("SYNTHETIC FIXTURE ONLY:"):
        fail(f"{case['case_id']}: source_text no lleva aviso de fixture")
    if record["classification"] != "synthetic_fixture":
        fail(f"{case['case_id']}: una fixture no está marcada synthetic_fixture")
    if not record["source"]["source_uri"].startswith("fixture://"):
        fail(f"{case['case_id']}: URI fuente no reservada a fixture")


def check_conflict_stale_outlier(case: dict) -> None:
    records = case["records"]
    if len(records) != 2:
        fail("conflicto-stale-outlier: se esperaban dos observaciones sintéticas")
    a, b = records
    fa, fb = a["facts"][0], b["facts"][0]
    same_scope = (
        a["identity"] == b["identity"]
        and fa["field_path"] == fb["field_path"]
        and fa["observation"] == fb["observation"]
        and fa["unit"] == fb["unit"]
        and fa.get("currency") == fb.get("currency")
    )
    if not same_scope or fa["value"] == fb["value"]:
        fail("conflicto-stale-outlier: fixture no representa mismo scope con valores distintos")
    if a["source"]["source_id"] == b["source"]["source_id"]:
        fail("conflicto-stale-outlier: se esperaban fuentes distintas")

    policy = case["test_only_policy"]
    observed = date.fromisoformat(fa["observation"]["observed_at"])
    as_of = date.fromisoformat(policy["as_of_date"])
    age_days = (as_of - observed).days
    if age_days <= policy["max_observation_age_days"]:
        fail("conflicto-stale-outlier: caso no supera el umbral stale de fixture")
    delta = abs(Decimal(fa["value"]) - Decimal(fb["value"]))
    if delta <= Decimal(policy["max_difference"]):
        fail("conflicto-stale-outlier: caso no supera el umbral outlier de fixture")
    required = {"SOURCE_CONFLICT", "POSSIBLE_OUTLIER", "STALE"}
    if not required.issubset(set(case["expected_reasons"])) or case["expected_gate"] != "manual_review":
        fail("conflicto-stale-outlier: expectativa debe ser revisión humana")


def check_case_semantics(case: dict) -> None:
    case_id = case["case_id"]
    records = case["records"]
    if case["expected_publishable"] is not False:
        fail(f"{case_id}: ninguna fixture puede publicarse")

    if case_id == "clase-fondo-y-listing-separados":
        fund = next(r for r in records if r["family"] == "fund_share_class")
        listing = next(r for r in records if r["family"] == "market_listing")
        isin = fund["identity"]["class_isin"]
        if listing["identity"]["related_class_isin"] != isin:
            fail("listing no enlaza la clase ficticia por identificador")
        if listing["identity"]["ticker"] == isin:
            fail("ticker no debe sustituir al ISIN")

    elif case_id == "serie-mensual-historica-no-quote":
        record = records[0]
        if record["source"]["declared_frequency"] != "monthly":
            fail("la fixture mensual debe conservar su frecuencia declarada")
        if record["identity"]["scope"] != "statistical_series":
            fail("la serie agregada no debe clasificarse como cotización por título")
        if case["expected_gate"] != "historical_only":
            fail("la serie sintética debe quedar solo como histórica")

    elif case_id == "pdf-ia-no-promocion-sin-revision":
        extraction = records[0]["source"]["extraction"]
        if extraction["method"] != "llm_assisted" or extraction["human_verified"]:
            fail("el caso debe representar extracción IA no verificada")
        if case["expected_gate"] != "manual_review":
            fail("la extracción IA sin validar exige revisión")

    elif case_id == "conflicto-outlier-y-stale":
        check_conflict_stale_outlier(case)

    elif case_id == "replay-idempotente-noop":
        if len(records) != 2 or canonical(records[0]) != canonical(records[1]):
            fail("replay-idempotente: registros repetidos no son idénticos")
        if records[0]["idempotency_key"] != records[1]["idempotency_key"]:
            fail("replay-idempotente: claves lógicas distintas")
        if case["expected_gate"] != "no_op_duplicate":
            fail("replay idéntico debe producir no-op")

    elif case_id == "deposito-condiciones-sin-observacion":
        record = records[0]
        if record["source"]["declared_frequency"] != "unknown":
            fail("la fixture no debe atribuir una cadencia no documentada")
        if any(f["observation"]["observed_at"] is not None for f in record["facts"]):
            fail("la fixture debe conservar observación no declarada como null")


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    fixture_set = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    cases = fixture_set["cases"]
    if fixture_set.get("test_only") is not True:
        fail("fixture_set no está marcado test_only")

    records_count = 0
    expected_rejects = 0
    for case in cases:
        errors = []
        for record in case["records"]:
            records_count += 1
            errors.extend(validator.iter_errors(record))
            if case["expected_schema_valid"]:
                validate_raw_hash(case, record)
        schema_valid = not errors
        if schema_valid != case["expected_schema_valid"]:
            messages = "; ".join(error.message for error in errors[:3])
            fail(f"{case['case_id']}: schema_valid={schema_valid}; esperado={case['expected_schema_valid']}; {messages}")
        if not schema_valid:
            expected_rejects += 1
        else:
            check_case_semantics(case)

    print(
        f"OK: {len(cases)} casos JSON; {records_count} registros; "
        f"JSON Schema Draft 2020-12 válido; {expected_rejects} rechazo(s) estructural(es) esperado(s); "
        "ninguna fixture publicable."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, StopIteration, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
