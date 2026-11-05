"""Fusiona la transcripción citada del catálogo con las condiciones que usa la app.

Entrada:  docs/catalogo/transcripcion-2026-11-05.json  (metric/value/source por producto)
Salida:   app/data/condiciones.json (esquema que lee la app)

Reglas:
- No inventa: cada dato sale de una condición transcrita con su URL y fecha.
- El tipo de interés principal es la TAE de 12 meses si existe; si no, la primera
  publicada, y la etiqueta dice a qué plazo o condición corresponde.
- Los registros ya existentes (DEP-02, DEP-03 y las fichas DEP-EBN-12/DEP-SELF-12)
  se conservan sin tocar.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPT = ROOT / "docs" / "catalogo" / "transcripcion-2026-11-05.json"
CANDIDATES = ROOT / "docs" / "validacion-04" / "05-catalogo" / "candidatos.json"
CURATED = ROOT / "app" / "data" / "condiciones.json"

TERM_IN_NOTE = re.compile(r"(?:duraci[oó]n|plazo)\D{0,12}(\d{1,3})\s*mes", re.IGNORECASE)


def _by_metric(conditions, metric):
    return [c for c in conditions if c.get("metric") == metric]


def _first_value(conditions, metric):
    items = _by_metric(conditions, metric)
    return items[0].get("value") if items else None


def _as_text(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return f"{value}".rstrip("0").rstrip(".") if isinstance(value, float) else str(value)
    text = str(value).strip()
    return text or None


def _term_of(condition):
    note = condition.get("note") or ""
    match = TERM_IN_NOTE.search(note)
    if match:
        return int(match.group(1))
    return None


def _tiers(conditions):
    """Tramos de tipo de interés, con etiqueta tomada de la propia fuente."""
    rates = _by_metric(conditions, "tae")
    tiers = []
    for index, rate in enumerate(rates):
        term = _term_of(rate)
        if term:
            label = f"{term} meses"
        elif len(rates) > 1:
            label = "Condición publicada " + str(index + 1)
        else:
            label = "Condición publicada"
        tier = {"condition": "sin_requisito" if index == 0 else f"tramo_{index + 1}",
                "condition_label": label, "tae": _as_text(rate.get("value"))}
        tins = _by_metric(conditions, "tin")
        if index < len(tins) and _term_of(tins[index]) == term:
            tier["tin"] = _as_text(tins[index].get("value"))
        tiers.append(tier)
    return tiers


def _base_tier(tiers):
    """La TAE de 12 meses manda; si no hay, la primera publicada."""
    for tier in tiers:
        if tier.get("condition_label") == "12 meses":
            return tier
    return tiers[0] if tiers else None


def build_record(item, candidates):
    candidate = candidates.get(item["candidate_id"]) or {}
    conditions = item.get("conditions") or []
    tiers = _tiers(conditions)
    base = _base_tier(tiers)
    rate_condition = None
    if base is not None:
        rates = _by_metric(conditions, "tae")
        for rate in rates:
            if _as_text(rate.get("value")) == base.get("tae"):
                rate_condition = rate
                break
    source_condition = rate_condition or (conditions[0] if conditions else {})
    term = _term_of(rate_condition) if rate_condition else None
    if term is None:
        term = _first_value(conditions, "plazo_meses")
    record = {
        "candidate_id": item["candidate_id"],
        "family": candidate.get("family"),
        "name": item.get("name") or candidate.get("name_literal"),
        "provider": candidate.get("issuer_manager"),
        "term_months": int(term) if isinstance(term, (int, float)) and 1 <= int(term) <= 120 else None,
        "minimum_eur": _as_text(_first_value(conditions, "importe_minimo")),
        "maximum_eur": _as_text(_first_value(conditions, "importe_maximo")),
        "interest_payment": _as_text(_first_value(conditions, "liquidacion")),
        "early_cancellation": _as_text(_first_value(conditions, "cancelacion_anticipada")),
        "guarantee": _as_text(_first_value(conditions, "garantia_depositos")),
        "risk_indicator": _as_text(_first_value(conditions, "riesgo")),
        "source": {
            "url": source_condition.get("source_url"),
            "kind": "official" if source_condition.get("source_kind") == "oficial" else "secondary",
            "document_date": _as_text(_first_value(conditions, "fecha_documento")),
            "retrieved_at": source_condition.get("accessed"),
        },
        "valid_to": rate_condition.get("effective_to") if rate_condition else None,
        "tiers": tiers,
        "documented": [
            {"metric": c.get("metric"), "value": c.get("value"), "unit": c.get("unit"),
             "literal": c.get("value_literal"), "source_url": c.get("source_url"),
             "source_title": c.get("source_title"), "accessed": c.get("accessed"),
             "effective_to": c.get("effective_to"), "note": c.get("note")}
            for c in conditions
        ],
    }
    return record


def main():
    transcript = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))
    snapshot = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    candidates = {item.get("candidate_id"): item for item in snapshot.get("candidates", [])}
    curated = json.loads(CURATED.read_text(encoding="utf-8"))
    existing = {record["candidate_id"]: record for record in curated.get("records", [])}

    added = 0
    for item in transcript:
        if item.get("candidate_id") in existing:
            continue
        if not (item.get("conditions") or []):
            continue
        existing[item["candidate_id"]] = build_record(item, candidates)
        added += 1

    document = {
        "schema": curated.get("schema", "paideia.conditions/1"),
        "retrieved_at": "2026-11-05",
        "note": ("Condiciones transcritas de fuentes públicas con su URL y fecha. Los permisos "
                 "de publicación siguen sin revisar; no se reutilizan como oferta vigente."),
        "records": list(existing.values()),
    }
    CURATED.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    without_source = [r["candidate_id"] for r in document["records"] if not (r.get("source") or {}).get("url")]
    print(f"registros: {len(document['records'])} (+{added}); sin URL de origen: {without_source or 'ninguno'}")


if __name__ == "__main__":
    main()
