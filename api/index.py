"""Paideia en Vercel: una función WSGI que sirve la API y los archivos estáticos.

Reutiliza el motor de cálculo y el módulo de condiciones del proyecto local. El
chat con IA queda apagado en esta versión pública: la clave no se publica.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
from datetime import date
from urllib.parse import parse_qs, unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _core.catalogue_conditions import derive  # noqa: E402
from _core.catalogue_data import CANDIDATES, CURATED, SOURCES  # noqa: E402
from _core.domain import InputValidationError, calculate_scenario  # noqa: E402

PRODUCT_ID = re.compile(r"[A-Z0-9]{1,16}(?:-[A-Z0-9]{1,16}){0,3}\Z")


def _conflict_text(item):
    """Texto documentado del conflicto: acotado y sin caracteres de control.

    La vista lo escapa; una frase genérica ocultaría qué discrepa.
    """
    if not isinstance(item, str):
        return ""
    clean = "".join(char for char in item if char.isprintable() or char == " ")
    return " ".join(clean.split())[:300]
FAMILIES = {"cuenta_remunerada", "deposito", "letra_deuda_publica", "fondo_tradicional", "etf_ucits"}
DEPOSIT_CRITERION = "deposit_tae_12m_eur"
MAX_BODY = 16384
STATIC_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_static")
JSON_HEADERS = [("Content-Type", "application/json; charset=utf-8"), ("Cache-Control", "no-store")]


def _json(payload, status="200 OK"):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = JSON_HEADERS + [("Content-Length", str(len(body)))]
    return status, headers, body


def _error(status, code, message):
    return _json({"error": {"code": code, "message": message, "retryable": False}}, status)


def _product(candidate):
    product_id = candidate.get("candidate_id")
    name = candidate.get("name_literal")
    family = candidate.get("family")
    state = candidate.get("candidate_state")
    if (not isinstance(product_id, str) or not PRODUCT_ID.fullmatch(product_id)
            or not isinstance(name, str) or not name.strip()
            or family not in FAMILIES or state not in {"verified", "proposed"}):
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
        # La lista y el comparador de metadatos no publican cifras: el texto literal
        # del conflicto, que puede citar tasas, se reserva para la ficha del producto.
        "conflicts": ["Conflicto de fuentes pendiente de revisión; ver la ficha del producto."
                      for item in conflicts[:5] if isinstance(item, str)],
        "unknown_fields": [item for item in unknown if isinstance(item, str)],
    }


PRODUCTS = [item for item in (_product(candidate) for candidate in CANDIDATES) if item is not None]
BY_ID = {product["id"]: product for product in PRODUCTS}
CONFLICT_DETAILS = {
    candidate.get("candidate_id"): tuple(
        text for item in (candidate.get("conflicts") or [])
        if (text := _conflict_text(item))
    )[:5]
    for candidate in CANDIDATES
    if isinstance(candidate, dict) and isinstance(candidate.get("candidate_id"), str)
}


def _product_detail(product):
    """Copia para la ficha, con el texto literal del conflicto documentado."""
    if product is None:
        return None
    detail = json.loads(json.dumps(product))
    raw = CONFLICT_DETAILS.get(detail.get("id"))
    if raw:
        detail["conflicts"] = list(raw)
    return detail


def _report():
    return derive({"candidates": CANDIDATES}, today=date.today(), curated=CURATED, sources=SOURCES)


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
        "mode": "public_serverless",
        "ai": {
            "connected": False,
            "status": "not_configured",
            "message": "Chat IA no disponible en la versión pública; no se envía nada.",
            "capabilities": {"context": False, "history": False, "synthetic_only": True, "structured_education": False},
            "quota": None,
        },
        "catalogue": {"candidate_count": len(PRODUCTS), "publication_ready": 0},
        "storage": "bundled_snapshot_no_database",
    }


def _static(path):
    relative = path.lstrip("/") or "index.html"
    if not relative or ".." in relative or "\\" in relative or "\x00" in relative:
        return _error("404 Not Found", "NOT_FOUND", "Recurso no encontrado.")
    candidate = os.path.normpath(os.path.join(STATIC_ROOT, relative))
    if not candidate.startswith(os.path.abspath(STATIC_ROOT)):
        return _error("404 Not Found", "NOT_FOUND", "Recurso no encontrado.")
    if not os.path.isfile(candidate):
        if path.startswith("/api"):
            return _error("404 Not Found", "NOT_FOUND", "Recurso no encontrado.")
        candidate = os.path.join(STATIC_ROOT, "index.html")
        if not os.path.isfile(candidate):
            return _error("404 Not Found", "NOT_FOUND", "Recurso no encontrado.")
    content_type = mimetypes.guess_type(candidate)[0] or "application/octet-stream"
    with open(candidate, "rb") as handle:
        body = handle.read()
    headers = [("Content-Type", content_type), ("Content-Length", str(len(body)))]
    if candidate.endswith(".html"):
        headers.append(("Cache-Control", "no-store"))
    else:
        headers.append(("Cache-Control", "public, max-age=300"))
    return "200 OK", headers, body


def _compare(payload):
    if not isinstance(payload, dict) or set(payload) not in ({"product_ids"}, {"product_ids", "criterion"}):
        return _error("400 Bad Request", "INVALID_REQUEST", "Campos de comparación no válidos.")
    product_ids = payload.get("product_ids")
    criterion = payload.get("criterion")
    if (not isinstance(product_ids, list) or not 2 <= len(product_ids) <= 4
            or not all(isinstance(item, str) and PRODUCT_ID.fullmatch(item) for item in product_ids)
            or len(set(product_ids)) != len(product_ids)):
        return _error("400 Bad Request", "INVALID_REQUEST", "Se requieren de 2 a 4 IDs distintos.")
    if criterion is not None and criterion != DEPOSIT_CRITERION:
        return _error("400 Bad Request", "INVALID_REQUEST", "Criterio de comparación no válido.")
    report = _report()
    items = []
    for product_id in product_ids:
        product = BY_ID.get(product_id) or _curated_product(product_id, report)
        if product is None:
            return _error("404 Not Found", "PRODUCT_NOT_FOUND", "Candidato no encontrado.")
        items.append(product)
    reasons = ["Candidatos internos no publicables; solo se comparan metadatos de identidad y fuente."]
    if len({item["family"] for item in items}) > 1:
        reasons.append("Las familias tienen distinta naturaleza; no se ordenan numéricamente.")
    if any(item["conflicts"] or item["unknown_fields"] for item in items):
        reasons.append("Persisten conflictos o campos desconocidos pendientes de revisión.")
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
            result.update(quantitative_ready=True, comparison_kind="quantitative_metric_only",
                          reasons=["Se evalúa solo la métrica documentada en la fuente citada; no la oferta contractual completa."])
        else:
            result["reasons"] = ["No hay dos productos con la misma métrica documentada, vigente y del mismo plazo; no se ordena nada."]
    return _json(result)


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = unquote(environ.get("PATH_INFO", "/") or "/")
    query = parse_qs(environ.get("QUERY_STRING", ""))

    if path == "/api/status" and method == "GET":
        status, headers, body = _json(_status())
    elif path == "/api/conditions" and method == "GET":
        status, headers, body = _json(_report())
    elif path == "/api/catalogue" and method == "GET":
        q = (query.get("q") or [""])[0].strip().casefold()
        family = (query.get("family") or [""])[0].strip()
        items = []
        for product in PRODUCTS:
            if q and q not in f"{product['name']} {product.get('issuer') or ''}".casefold():
                continue
            if family and product["family"] != family:
                continue
            items.append(product)
        status, headers, body = _json({"items": items, "count": len(items), "not_for_publication": True})
    elif path.startswith("/api/products/") and method == "GET":
        product_id = path[len("/api/products/"):]
        if not PRODUCT_ID.fullmatch(product_id):
            status, headers, body = _error("404 Not Found", "NOT_FOUND", "Producto no encontrado.")
        else:
            report = _report()
            product = _product_detail(BY_ID.get(product_id) or _curated_product(product_id, report))
            conditions = _entry(product_id, report)
            if product is None and conditions is None:
                status, headers, body = _error("404 Not Found", "NOT_FOUND", "Producto no encontrado.")
            else:
                status, headers, body = _json({"product": product, "conditions": conditions})
    elif path in {"/api/compare", "/api/calculate"}:
        if method != "POST":
            status, headers, body = _error("405 Method Not Allowed", "METHOD_NOT_ALLOWED", "Método no permitido.")
        else:
            try:
                length = int(environ.get("CONTENT_LENGTH") or 0)
            except ValueError:
                length = 0
            raw = environ["wsgi.input"].read(min(length, MAX_BODY + 1)) if length else b""
            if len(raw) > MAX_BODY:
                status, headers, body = _error("413 Request Entity Too Large", "REQUEST_TOO_LARGE", "La petición es demasiado grande.")
            else:
                try:
                    payload = json.loads(raw or b"{}")
                except ValueError:
                    status, headers, body = _error("400 Bad Request", "INVALID_REQUEST", "JSON no válido.")
                else:
                    if path == "/api/calculate":
                        try:
                            status, headers, body = _json(calculate_scenario(payload))
                        except InputValidationError:
                            status, headers, body = _error("400 Bad Request", "INVALID_REQUEST", "Parámetros de cálculo no válidos.")
                    else:
                        status, headers, body = _compare(payload)
    elif method == "GET":
        status, headers, body = _static(path)
    else:
        status, headers, body = _error("405 Method Not Allowed", "METHOD_NOT_ALLOWED", "Método no permitido.")

    start_response(status, headers)
    return [body]
