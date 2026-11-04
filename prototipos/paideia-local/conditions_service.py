"""Servicio de lectura de condiciones del catálogo (sin red, sin escritura)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from catalogue_conditions import derive

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_RELATIVE = Path("docs/validacion-04/05-catalogo/candidatos.json")
CURATED_RELATIVE = Path("prototipos/paideia-local/data/condiciones.json")
SOURCES_RELATIVE = Path("docs/validacion-04/05-catalogo/evidencia/sources-ledger.json")


def _read_json(path: Path) -> object:
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(PROJECT_ROOT.resolve(strict=True)):
        raise RuntimeError("path outside project")
    return json.loads(resolved.read_text(encoding="utf-8"))


class ConditionsService:
    """Deriva condiciones con la fecha del día; nunca inventa ni cachea estados."""

    def __init__(self, snapshot_path: Path | None = None, curated_path: Path | None = None,
                 sources_path: Path | None = None):
        self._snapshot_path = snapshot_path or (PROJECT_ROOT / SNAPSHOT_RELATIVE)
        self._curated_path = curated_path or (PROJECT_ROOT / CURATED_RELATIVE)
        self._sources_path = sources_path or (PROJECT_ROOT / SOURCES_RELATIVE)

    def _curated(self) -> dict | None:
        try:
            document = _read_json(self._curated_path)
        except (OSError, ValueError, RuntimeError):
            return None
        return document if isinstance(document, dict) else None

    def _sources(self) -> dict:
        """Ledger de fuentes `id → url`. Si falta o está roto, el registro va vacío y
        cualquier condición del snapshot con id sin URL queda `unknown` (fail closed)."""
        try:
            document = _read_json(self._sources_path)
        except (OSError, ValueError, RuntimeError):
            return {"sources": []}
        if not isinstance(document, dict) or not isinstance(document.get("sources"), list):
            return {"sources": []}
        return document

    def describe(self, today: date | None = None) -> dict:
        snapshot = _read_json(self._snapshot_path)
        if not isinstance(snapshot, dict):
            raise RuntimeError("snapshot is not an object")
        return derive(snapshot, today=today, curated=self._curated(), sources=self._sources())

    def for_product(self, product_id: str, today: date | None = None) -> dict | None:
        report = self.describe(today)
        for product in report["products"]:
            if product["product_id"] == product_id:
                return product
        return None

    def comparability(self, product_ids, criterion, today: date | None = None) -> dict:
        """Comparación cuantitativa sobre condiciones documentadas, sin inventar nada."""
        if criterion != "deposit_tae_12m_eur":
            raise ValueError("unsupported criterion")
        report = self.describe(today)
        index = {product["product_id"]: product for product in report["products"]}
        items = []
        for product_id in product_ids:
            entry = index.get(product_id) or {}
            conditions = {condition["metric"]: condition for condition in entry.get("conditions", [])}
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

    def catalogue_extras(self, q: str | None = None, family: str | None = None) -> list[dict]:
        """Productos que solo viven en las condiciones transcritas, con forma de catálogo."""
        report = self.describe()
        extras = []
        for product in report["products"]:
            if product.get("source") is None or product.get("origin") != "curated_conditions":
                continue
            name = product.get("display_name") or ""
            if q and q.casefold() not in name.casefold():
                continue
            if family and product.get("family") != family:
                continue
            extras.append({
                "id": product["product_id"],
                "name": name,
                "family": product.get("family"),
                "issuer": product.get("provider"),
                "isin": None,
                "identity_state": "verified" if product["identity_state"] == "verified" else "proposed",
                "primary_url": (product.get("source") or {}).get("url"),
                "as_of": (product.get("source") or {}).get("retrieved_at"),
                "publication_ready": False,
                "conditions_state": "pending",
                "conflicts": [],
                "unknown_fields": [],
                "origin": "curated_conditions",
            })
        return extras
