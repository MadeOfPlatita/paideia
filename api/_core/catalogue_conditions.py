# Copia generada por api/build_core.py desde prototipos/paideia-local/catalogue_conditions.py. No editar aquí.
"""Deriva condiciones cuantitativas trazables desde el snapshot de candidatos.

Reglas deliberadamente conservadoras:

- No se completa ningún campo que el snapshot no documente.
- Un campo cuyo literal contiene varias tasas distintas se marca `conflict`.
- Una identidad `proposed` no habilita comparación cuantitativa, aunque haya tasa.
- Una promoción con `effective_to` vencida queda `stale`; nunca se presenta como vigente.
- El permiso de visualización se informa aparte (`permission_state`) y no se declara
  concedido: el módulo no redistribuye contenido de la fuente.

No hace E/S ni red: recibe el snapshot ya cargado y la fecha de referencia.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
DMY_DATE = re.compile(r"\b(\d{2})-(\d{2})-(\d{4})\b")
PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%\s*(TAE|TIN)", re.IGNORECASE)
MONTHS = re.compile(r"(\d{1,2})\s*meses?", re.IGNORECASE)
EUROS = re.compile(r"(\d[\d.]*(?:,\d+)?)\s*€")
LEADING_PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%\s*(TAE|TIN)", re.IGNORECASE)

# Campos del snapshot que pueden contener una tasa anual comparable.
RATE_FIELDS = {
    "cuenta_remunerada": ("promo_tae", "rate", "rate_headline", "main_offer_block"),
    "deposito": ("rate", "rate_ceiling", "reported_terms_snapshot"),
}
# Campos que solo aportan identidad o plazo.
TERM_FIELDS = {"deposito": ("term", "official_document_identity", "duration_and_condition")}
# Días de gracia por familia cuando el literal no fija fin de vigencia.
DEFAULT_TTL_DAYS = {"cuenta_remunerada": 7, "deposito": 30}


@dataclass(frozen=True)
class Condition:
    product_id: str
    family: str
    metric: str
    value: str | None
    unit: str
    state: str  # known | unknown | conflict | stale
    reason: str
    source_ids: tuple[str, ...] = ()
    effective_from: str | None = None
    effective_to: str | None = None
    retrieved_at: str | None = None
    permission_state: str = "pending"
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "family": self.family,
            "metric": self.metric,
            "value": self.value,
            "unit": self.unit,
            "state": self.state,
            "reason": self.reason,
            "source_ids": list(self.source_ids),
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "retrieved_at": self.retrieved_at,
            "permission_state": self.permission_state,
            "notes": list(self.notes),
        }


def _decimal(text: str) -> str | None:
    raw = text.strip().replace("\u00a0", "")
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    raw = raw.replace(" ", "")
    try:
        number = float(raw)
    except ValueError:
        return None
    if number != number or number < 0 or number > 1000:
        return None
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _dates(text: str) -> list[str]:
    found = [f"{a}-{b}-{c}" for a, b, c in ISO_DATE.findall(text)]
    for day, month, year in DMY_DATE.findall(text):
        found.append(f"{year}-{month}-{day}")
    return found


def _rates(text: str) -> list[tuple[str, str]]:
    return [(value.replace(",", "."), kind.upper()) for value, kind in PERCENT.findall(text)]


def _field_text(field: object) -> str:
    if isinstance(field, dict):
        literal = field.get("value_literal") or field.get("value") or ""
        return str(literal)
    return str(field or "")


def _source_ids(field: object) -> tuple[str, ...]:
    if isinstance(field, dict):
        return tuple(str(item) for item in field.get("source_ids") or ())
    return ()


def _field_dates(field: object) -> tuple[str | None, str | None]:
    if not isinstance(field, dict):
        return None, None
    start = field.get("effective_from")
    end = field.get("effective_to")
    return (str(start) if start else None, str(end) if end else None)


def annual_rate(candidate: dict, today: date) -> Condition:
    """TAE anual del producto, con estado y motivo explícitos."""
    family = candidate["family"]
    product_id = candidate["candidate_id"]
    fields = candidate.get("available_fields") or {}
    identity = candidate.get("candidate_state")
    conflicts = candidate.get("conflicts") or []
    retrieved = (candidate.get("dates") or {}).get("checked_at")

    if identity != "verified":
        return Condition(product_id, family, "annual_rate_percent", None, "PERCENT", "unknown",
                         "IDENTITY_NOT_VERIFIED", retrieved_at=retrieved,
                         notes=("La identidad no está verificada; no se usa su tasa.",))

    collected: list[tuple[str, str, object, list[str]]] = []
    for name in RATE_FIELDS.get(family, ()):
        if name not in fields:
            continue
        text = _field_text(fields[name])
        for value, kind in _rates(text):
            if kind == "TAE":
                collected.append((value, name, fields[name], _dates(text)))
    distinct = {value for value, _, _, _ in collected}
    if not collected:
        return Condition(product_id, family, "annual_rate_percent", None, "PERCENT", "unknown",
                         "RATE_NOT_DOCUMENTED", retrieved_at=retrieved,
                         notes=("No hay TAE documentada en el snapshot.",))
    if conflicts:
        return Condition(product_id, family, "annual_rate_percent", None, "PERCENT", "conflict",
                         "SOURCE_CONFLICT", source_ids=_source_ids(collected[0][2]),
                         retrieved_at=retrieved, notes=tuple(str(item) for item in conflicts[:2]))
    if len(distinct) > 1:
        return Condition(product_id, family, "annual_rate_percent", None, "PERCENT", "conflict",
                         "MULTIPLE_RATES_DOCUMENTED", source_ids=_source_ids(collected[0][2]),
                         retrieved_at=retrieved,
                         notes=("El literal contiene varias TAE: " + ", ".join(sorted(distinct)),))

    value, field_name, raw, dates = collected[0]
    start, end = _field_dates(raw)
    end = end or (dates[0] if dates else None)
    if end and end < today.isoformat():
        return Condition(product_id, family, "annual_rate_percent", value, "PERCENT", "stale",
                         "PROMOTION_EXPIRED", source_ids=_source_ids(raw),
                         effective_from=start, effective_to=end, retrieved_at=retrieved,
                         notes=("La vigencia documentada terminó; no se presenta como actual.",))
    ttl = DEFAULT_TTL_DAYS.get(family, 30)
    if retrieved and (today - date.fromisoformat(retrieved)) > timedelta(days=ttl) and not end:
        return Condition(product_id, family, "annual_rate_percent", value, "PERCENT", "stale",
                         "RETRIEVAL_TOO_OLD", source_ids=_source_ids(raw),
                         effective_from=start, effective_to=end, retrieved_at=retrieved,
                         notes=(f"Sin fecha de vigencia y con más de {ttl} días desde la consulta.",))
    return Condition(product_id, family, "annual_rate_percent", value, "PERCENT", "known",
                     f"DOCUMENTED_{field_name.upper()}", source_ids=_source_ids(raw),
                     effective_from=start, effective_to=end, retrieved_at=retrieved)


def term_months(candidate: dict) -> Condition:
    family = candidate["family"]
    product_id = candidate["candidate_id"]
    fields = candidate.get("available_fields") or {}
    identity = candidate.get("candidate_state")
    retrieved = (candidate.get("dates") or {}).get("checked_at")
    if identity != "verified":
        return Condition(product_id, family, "term_months", None, "MONTHS", "unknown",
                         "IDENTITY_NOT_VERIFIED", retrieved_at=retrieved)
    for name in TERM_FIELDS.get(family, ()):
        if name not in fields:
            continue
        text = _field_text(fields[name])
        found = {int(value) for value in MONTHS.findall(text)}
        if len(found) == 1:
            months = found.pop()
            if 1 <= months <= 120:
                return Condition(product_id, family, "term_months", str(months), "MONTHS", "known",
                                 f"DOCUMENTED_{name.upper()}", source_ids=_source_ids(fields[name]),
                                 retrieved_at=retrieved)
        if len(found) > 1:
            return Condition(product_id, family, "term_months", None, "MONTHS", "conflict",
                             "MULTIPLE_TERMS_DOCUMENTED", source_ids=_source_ids(fields[name]),
                             retrieved_at=retrieved)
    return Condition(product_id, family, "term_months", None, "MONTHS", "unknown",
                     "TERM_NOT_DOCUMENTED", retrieved_at=retrieved)


def derive(snapshot: dict, today: date | None = None, curated: dict | None = None) -> dict:
    """Devuelve condiciones por producto y un resumen, sin inventar campos.

    `curated` (opcional) son condiciones transcritas a mano de una fuente con URL y
    fecha; cuando existen, sustituyen al literal del snapshot para ese producto.
    """
    reference = today or date.today()
    candidates = snapshot.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("snapshot without candidates")
    curated_records = _index_curated(curated)
    products = []
    seen = set()
    for candidate in candidates:
        family = candidate.get("family")
        product_id = candidate.get("candidate_id")
        seen.add(product_id)
        conditions = []
        record = curated_records.get(product_id)
        if record is not None:
            conditions.extend(_curated_conditions(record, reference))
        else:
            if family in RATE_FIELDS:
                conditions.append(annual_rate(candidate, reference))
            if family in TERM_FIELDS:
                conditions.append(term_months(candidate))
        products.append({
            "product_id": product_id,
            "family": family,
            "display_name": candidate.get("name_literal"),
            "identity_state": candidate.get("candidate_state"),
            "conditions": [condition.to_dict() for condition in conditions],
            "rate_tiers": record.get("tiers", []) if record else [],
            "source": record.get("source") if record else None,
        })
    for product_id, record in curated_records.items():
        if product_id in seen:
            continue
        products.append({
            "product_id": product_id,
            "family": record.get("family"),
            "display_name": record.get("name"),
            "identity_state": "verified" if (record.get("source") or {}).get("kind") == "official" else "press_documented",
            "conditions": [condition.to_dict() for condition in _curated_conditions(record, reference)],
            "rate_tiers": record.get("tiers", []),
            "source": record.get("source"),
            "provider": record.get("provider"),
            "origin": "curated_conditions",
        })
    counts: dict[str, int] = {}
    for product in products:
        for condition in product["conditions"]:
            counts[condition["state"]] = counts.get(condition["state"], 0) + 1
    return {
        "reference_date": reference.isoformat(),
        "products": products,
        "state_counts": counts,
        "rules_version": "catalogue-conditions.v1",
        "not_for_publication": True,
        "note": "Estados derivados del snapshot y de condiciones transcritas con fuente; permisos de publicación sin revisar.",
    }


def _index_curated(curated: dict | None) -> dict:
    if not curated:
        return {}
    records = curated.get("records") if isinstance(curated, dict) else None
    if not isinstance(records, list):
        raise ValueError("curated conditions without records")
    index = {}
    for record in records:
        product_id = record.get("candidate_id")
        if not isinstance(product_id, str) or not product_id:
            raise ValueError("curated record without candidate_id")
        index[product_id] = record
    return index


def _curated_conditions(record: dict, today: date) -> list[Condition]:
    product_id = record["candidate_id"]
    family = record.get("family")
    source = record.get("source") or {}
    tiers = record.get("tiers") or []
    retrieved = source.get("retrieved_at")
    kind = source.get("kind") or "unknown"
    notes = []
    if kind != "official":
        notes.append("Fuente secundaria: confirmación en página oficial pendiente.")
    conditions = []
    base = next((tier for tier in tiers if tier.get("condition") == "sin_requisito"), tiers[0] if tiers else None)
    if base is None:
        conditions.append(Condition(product_id, family, "annual_rate_percent", None, "PERCENT", "unknown",
                                    "RATE_NOT_DOCUMENTED", retrieved_at=retrieved, notes=tuple(notes)))
    else:
        value = _decimal(str(base.get("tae", "")))
        state, reason = "known", f"CURATED_{kind.upper()}"
        valid_to = record.get("valid_to")
        if value is None:
            state, reason = "unknown", "RATE_UNPARSEABLE"
        elif valid_to and valid_to < today.isoformat():
            state, reason = "stale", "PROMOTION_EXPIRED"
            notes.append("La vigencia declarada ya terminó.")
        conditions.append(Condition(product_id, family, "annual_rate_percent", value, "PERCENT", state,
                                    reason, source_ids=(str(source.get("url")),), effective_to=valid_to,
                                    retrieved_at=retrieved, notes=tuple(notes)))
    term = record.get("term_months")
    if isinstance(term, int) and 1 <= term <= 120:
        conditions.append(Condition(product_id, family, "term_months", str(term), "MONTHS", "known",
                                    "CURATED_TERM", retrieved_at=retrieved))
    return conditions
