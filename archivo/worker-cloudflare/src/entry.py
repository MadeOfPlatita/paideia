"""Paideia — API para Cloudflare Workers (Python).

Sirve el catálogo, las condiciones documentadas, la comparación y la calculadora
sobre el mismo código puro que la app local. El chat con IA no se expone aquí: la
clave no puede viajar al navegador y este Worker no la necesita.
"""

from datetime import date
import json
import re
from urllib.parse import parse_qs

from js import Response, URL

from catalogue_conditions import derive
from catalogue_data import CANDIDATES, CURATED
from domain import InputValidationError, calculate_scenario

PRODUCT_ID = re.compile(r"[A-Z0-9]{1,16}(?:-[A-Z0-9]{1,16}){0,3}\Z")
FAMILIES = {"cuenta_remunerada", "deposito", "letra_deuda_publica", "fondo_tradicional", "etf_ucits"}
DEPOSIT_CRITERION = "deposit_tae_12m_eur"
MAX_BODY = 16384


def _json(payload, status=200):
    return Response.new(
        json.dumps(payload, ensure_ascii=False),
        {
            "status": status,
            "headers": {
                "content-type": "application/json; charset=utf-8",
                "cache-control": "no-store",
                "x-content-type-options": "nosniff",
            },
        },
    )


def _error(status, code, message):
    return _json({"error": {"code": code, "message": message, "retryable": False}}, status)


def _product(candidate):
    product_id = candidate.get("candidate_id")
    name = candidate.get("name_literal")
    family = candidate.get("family")
    state = candidate.get("candidate_state")
    if (not isinstance(product_id, str) or not PRODUCT_ID.fullmatch(product_id)
            or not isinstance(name, str) or not name.strip()
            or family not in FAMILIES
            or state not in {"verified", "proposed"}):
        return None
    manager = candidate.get("issuer_manager")
    issuer = manager.get("brand") if isinstance(manager, dict) else None
    isin_record = candidate.get("isin")
    isin = isin_record.get("literal") if isinstance(isin_record, dict) else None
    dates = candidate.get("dates") or {}
    effective = dates.get("effective") if isinstance(dates, dict) else None
    as_of = None
    if isinstance(effective, dict):
        candidate_date = effective.get("as_of")
        scope = effective.get("scope", "")
        if isinstance(candidate_date, str) and isinstance(scope, str) and "nav" not in scope.casefold():
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate_date):
                as_of = candidate_date
    conflicts = candidate.get("conflicts") or []
    unknown = candidate.get("unknown_fields") or []
    return {
        "id": product_id,
        "name": name,
        "family": family,
        "issuer": issuer,
        "isin": isin,
        "identity_state": state,
        "primary_url": candidate.get("primary_url"),
        "as_of": as_of,
        "publication_ready": False,
        "conditions_state": "pending",
        "conflicts": ["Conflicto de fuentes o condiciones pendiente de revisión." for item in conflicts[:5] if isinstance(item, str)],
        "unknown_fields": [item for item in unknown if isinstance(item, str)],
    }


PRODUCTS = [item for item in (_product(candidate) for candidate in CANDIDATES) if item is not None]
BY_ID = {product["id"]: product for product in PRODUCTS}


def _conditions(today=None):
    return derive({"candidates": CANDIDATES}, today=today, curated=CURATED)


def _report(today=None):
    return _conditions(today)


def _entry(product_id, report):
    for product in report["products"]:
        if product["product_id"] == product_id:
            return product
    return None


def _curated_product(product_id, report):
    entry = _entry(product_id, report)
    if entry is None:
        return None
    source = entry.get("source") or {}
    return {
        "id": product_id,
        "name": entry.get("display_name") or product_id,
        "family": entry.get("family"),
        "issuer": entry.get("provider"),
        "isin": None,
        "identity_state": "verified" if entry.get("identity_state") == "verified" else "proposed",
        "primary_url": source.get("url"),
        "as_of": source.get("retrieved_at"),
        "publication_ready": False,
        "conditions_state": "documented",
        "conflicts": [],
        "unknown_fields": [],
        "origin": "curated_conditions",
    }


def _comparability(product_ids, criterion, report):
    index = {product["product_id"]: product for product in report["products"]}
    items = []
    for product_id in product_ids:
        entry = index.get(product_id) or {}
        conditions = {item["metric"]: item for item in entry.get("conditions", [])}
        rate = conditions.get("annual_rate_percent")
        term = conditions.get("term_months")
        reasons = []
        if entry.get("family") != "deposito":
            reasons.append("FAMILY_MISMATCH")
        if not term or term.get("state") != "known" or str(term.get("value")) != "12":
            reasons.append("PERIOD_MISMATCH")
        if rate is None or rate.get("state") != "known":
            reasons.append({"stale": "DATA_STALE", "conflict": "DATA_CONFLICT"}.get((rate or {}).get("state"), "METRIC_MISSING"))
        eligible = not reasons
        items.append({
            "product_id": product_id,
            "eligible": eligible,
            "value": rate.get("value") if eligible else None,
            "reason_codes": reasons,
            "source_refs": [{"source_ids": rate.get("source_ids", []), "retrieved_at": rate.get("retrieved_at")}] if eligible else [],
        })
    eligible_ids = [item["product_id"] for item in items if item["eligible"]]
    return {
        "criterion": criterion,
        "items": items,
        "eligible_product_ids": eligible_ids,
        "quantitative_ready": len(eligible_ids) >= 2,
        "status": "comparable" if len(eligible_ids) >= 2 else "not_comparable",
        "basis": "documented_conditions",
        "policy_version": None,
        "test_only": False,
        "reference_date": report["reference_date"],
        "not_for_publication": True,
    }


def _status():
    return {
        "mode": "cloud_worker",
        "ai": {
            "connected": False,
            "status": "not_configured",
            "message": "Chat IA no disponible en esta versión pública; no se envía nada.",
            "capabilities": {"context": False, "history": False, "synthetic_only": True, "structured_education": False},
            "quota": None,
        },
        "catalogue": {"candidate_count": len(PRODUCTS), "publication_ready": 0},
        "storage": "bundled_snapshot_no_database",
    }


async def on_fetch(request, env):
    url = URL.new(request.url)
    path = url.pathname or "/"
    method = request.method

    if path == "/api/status":
        return _json(_status())
    if path == "/api/conditions":
        report = _report()
        return _json(report)
    if path == "/api/catalogue":
        query = parse_qs(url.search[1:] if url.search else "")
        q = (query.get("q") or [""])[0].strip().casefold()
        family = (query.get("family") or [""])[0].strip()
        items = []
        for product in PRODUCTS:
            if q and q not in f"{product['name']} {product.get('issuer') or ''}".casefold():
                continue
            if family and product["family"] != family:
                continue
            items.append(product)
        return _json({"items": items, "count": len(items), "not_for_publication": True})
    if path.startswith("/api/products/"):
        product_id = path[len("/api/products/"):]
        if not PRODUCT_ID.fullmatch(product_id):
            return _error(404, "NOT_FOUND", "Producto no encontrado.")
        report = _report()
        product = BY_ID.get(product_id) or _curated_product(product_id, report)
        conditions = _entry(product_id, report)
        if product is None and conditions is None:
            return _error(404, "NOT_FOUND", "Producto no encontrado.")
        return _json({"product": product, "conditions": conditions})
    if path in {"/api/compare", "/api/calculate"}:
        if method != "POST":
            return _error(405, "METHOD_NOT_ALLOWED", "Método no permitido.")
        try:
            raw = await request.text()
        except Exception:
            return _error(400, "INVALID_REQUEST", "Petición no válida.")
        if len(raw.encode("utf-8")) > MAX_BODY:
            return _error(413, "REQUEST_TOO_LARGE", "La petición es demasiado grande.")
        try:
            payload = json.loads(raw)
        except ValueError:
            return _error(400, "INVALID_REQUEST", "JSON no válido.")
        if path == "/api/calculate":
            try:
                return _json(calculate_scenario(payload))
            except InputValidationError:
                return _error(400, "INVALID_REQUEST", "Parámetros de cálculo no válidos.")
        return _compare(payload)
    return _error(404, "NOT_FOUND", "Recurso no encontrado.")


def _compare(payload):
    if not isinstance(payload, dict) or set(payload) not in ({"product_ids"}, {"product_ids", "criterion"}):
        return _error(400, "INVALID_REQUEST", "Campos de comparación no válidos.")
    product_ids = payload.get("product_ids")
    criterion = payload.get("criterion")
    if (not isinstance(product_ids, list) or not 2 <= len(product_ids) <= 4
            or not all(isinstance(item, str) and PRODUCT_ID.fullmatch(item) for item in product_ids)
            or len(set(product_ids)) != len(product_ids)):
        return _error(400, "INVALID_REQUEST", "Se requieren de 2 a 4 IDs distintos.")
    if criterion is not None and criterion != DEPOSIT_CRITERION:
        return _error(400, "INVALID_REQUEST", "Criterio de comparación no válido.")
    report = _report()
    items = []
    for product_id in product_ids:
        product = BY_ID.get(product_id) or _curated_product(product_id, report)
        if product is None:
            return _error(404, "PRODUCT_NOT_FOUND", "Candidato no encontrado.")
        items.append(product)
    reasons = ["Candidatos de investigación no publicables; se comparan condiciones documentadas y metadatos de identidad."]
    if len({item["family"] for item in items}) > 1:
        reasons.append("Las familias tienen distinta naturaleza; no se ordenan numéricamente.")
    result = {
        "items": items,
        "comparison_kind": "educational_metadata_only",
        "quantitative_ready": False,
        "reasons": reasons,
        "hypothetical": False,
    }
    if criterion is not None:
        comparability = _comparability(product_ids, criterion, report)
        result["comparability"] = comparability
        if comparability["quantitative_ready"]:
            result.update(
                quantitative_ready=True,
                comparison_kind="quantitative_metric_only",
                reasons=["Se evalúa solo la métrica documentada en la fuente citada; no la oferta contractual completa."],
            )
        else:
            result["reasons"] = ["No hay dos productos con la misma métrica documentada, vigente y del mismo plazo; no se ordena nada."]
    return _json(result)
