"""Vista del catálogo para las herramientas de Pai: identidad + procedencia de condiciones.

No sustituye al repositorio ni a la UI: añade los productos transcritos de fuentes y
adjunta, cuando existen, las condiciones con su estado, su fuente y sus fechas. Nada
se inventa y ningún estado desconocido se presenta como documentado.

Este adaptador no decide la clase de una fuente (oficial/secundaria): solo transporta
`source_ids`, `retrieved_at`, vigencia y tramos tal como los declara el servicio. La
proyección y validación final vive en `pai_tools`.
"""

from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from datetime import date

from pai_tools import ConditionsUnavailable, project_rate_tiers

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
# Tope estructural por producto: por encima se considera un informe invalido.
MAX_CONDITIONS_PER_PRODUCT = 32


def _valid_reference_date(value):
    if type(value) is not str or _ISO_DATE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


class CatalogueWithConditions:
    def __init__(self, repository, conditions_service):
        self._repository = repository
        self._conditions = conditions_service

    def _report(self):
        try:
            report = self._conditions.describe()
        except ConditionsUnavailable:
            raise
        except Exception:
            raise ConditionsUnavailable("El servicio de condiciones no está disponible.") from None
        if type(report) is not dict or type(report.get("products")) is not list:
            raise ConditionsUnavailable("El servicio de condiciones devolvió un informe no válido.")
        seen_ids = set()
        for entry in report["products"]:
            if type(entry) is not dict:
                raise ConditionsUnavailable("El servicio de condiciones devolvió un informe no válido.")
            product_id = entry.get("product_id")
            if (type(product_id) is not str or not product_id.strip()
                    or len(product_id) > 64 or product_id in seen_ids):
                # Sin un identificador único no se puede vincular la condición a su
                # producto: presentarlo como ausencia ocultaría un fallo del servicio.
                raise ConditionsUnavailable(
                    "El servicio de condiciones devolvió un producto sin identificador válido.")
            seen_ids.add(product_id)
            conditions = entry.get("conditions")
            # Un fondo o un ETF declara de forma legitima diez o doce metricas
            # (TER, ISIN, SRI, comisiones, divisa, replica, periodo, depositaria...).
            # El tope anterior de 8 rechazaba el informe entero y dejaba sin catalogo
            # a todas las busquedas; se mantiene un limite estructural amplio.
            if (type(conditions) is not list or len(conditions) > MAX_CONDITIONS_PER_PRODUCT
                    or any(type(condition) is not dict for condition in conditions)):
                # Forma estructural no válida: se falla cerrado, no se descarta en silencio.
                raise ConditionsUnavailable(
                    "El servicio de condiciones devolvió condiciones con una forma no válida.")
        return report

    @staticmethod
    def _entry_for(product_id, report):
        for entry in report.get("products", []):
            if type(entry) is dict and entry.get("product_id") == product_id:
                return entry
        return None

    def _conditions_for(self, product_id, report):
        entry = self._entry_for(product_id, report)
        if entry is None:
            return []
        # `_report` ya validó que es una lista de objetos; aquí no se filtra nada:
        # descartar una condición malformada la convertiría en una ausencia falsa.
        return [deepcopy(condition) for condition in entry["conditions"]]

    @staticmethod
    def _conditions_state(conditions, reference_date):
        """Solo se anuncia `documented` con valor conocido, fuente citada y fecha de referencia."""
        if reference_date is None:
            return "pending"
        for condition in conditions:
            if (condition.get("state") != "known" or condition.get("value") is None
                    or not condition.get("source_ids")):
                continue
            effective_to = condition.get("effective_to")
            if effective_to is None:
                return "documented"
            if (reference_date is not None and type(effective_to) is str
                    and _valid_reference_date(effective_to) and effective_to >= reference_date):
                return "documented"
        return "pending"

    def _enrich(self, item, report):
        entry = self._entry_for(item.get("id"), report) or {}
        conditions = self._conditions_for(item.get("id"), report)
        tiers, tiers_state = project_rate_tiers(entry.get("rate_tiers"))
        reference_date = report.get("reference_date") if _valid_reference_date(report.get("reference_date")) else None
        item["conditions"] = conditions
        item["rate_tiers"] = tiers
        item["rate_tiers_state"] = tiers_state
        item["conditions_state"] = self._conditions_state(conditions, reference_date)
        item["conditions_reference_date"] = reference_date
        source = entry.get("source")
        item["source"] = deepcopy(source) if type(source) is dict else None
        return item

    def list_products(self, q=None, family=None):
        items = [dict(item) for item in self._repository.list_products(q=q, family=family)]
        report = self._report()
        seen = {item.get("id") for item in items}
        try:
            extras = self._conditions.catalogue_extras(q=None, family=family)
        except ConditionsUnavailable:
            raise
        except Exception:
            raise ConditionsUnavailable("El servicio de condiciones no está disponible.") from None
        if type(extras) is not list or any(type(extra) is not dict for extra in extras):
            raise ConditionsUnavailable("El servicio de condiciones devolvió productos no válidos.")
        candidates = []
        for extra in extras:
            if extra.get("id") in seen:
                continue
            haystack = " ".join(str(extra.get(key) or "") for key in ("name", "issuer", "id"))
            hits = self._score(haystack, q) if q else 1
            if q and hits == 0:
                continue
            candidates.append((hits, extra))
        candidates.sort(key=lambda pair: -pair[0])
        for _, extra in candidates:
            seen.add(extra.get("id"))
            items.append(extra)
        return [self._enrich(item, report) for item in items]

    STOPWORDS = frozenset({"a", "al", "de", "del", "el", "la", "las", "los", "con", "en", "por", "para", "que", "y", "o", "un", "una"})

    @classmethod
    def _score(cls, haystack, query):
        """Cuenta cuántas palabras de la consulta aparecen; sirve para ordenar y descartar."""
        if type(haystack) is not str or type(query) is not str:
            return 0
        tokens = [token for token in cls._fold(query).split() if len(token) >= 2 and token not in cls.STOPWORDS]
        if not tokens:
            return 1
        folded = cls._fold(haystack)
        return sum(1 for token in tokens if token in folded)

    @staticmethod
    def _fold(text):
        text = unicodedata.normalize("NFKD", str(text).casefold())
        return "".join(char for char in text if not unicodedata.combining(char))

    def get_product(self, product_id):
        product = self._repository.get_product(product_id)
        report = self._report()
        if product is None:
            entry = self._entry_for(product_id, report)
            if entry is not None:
                source = entry.get("source") or {}
                url = source.get("url")
                if not isinstance(url, str) or not url:
                    return None
                product = {
                    "id": product_id,
                    "name": entry.get("display_name") or product_id,
                    "family": entry.get("family"),
                    "issuer": entry.get("provider"),
                    "isin": None,
                    "identity_state": "verified" if entry.get("identity_state") == "verified" else "proposed",
                    "primary_url": url,
                    "as_of": source.get("retrieved_at"),
                    "publication_ready": False,
                    "conditions_state": "pending",
                    "conflicts": [],
                    "unknown_fields": [],
                }
        if product is None:
            return None
        return self._enrich(dict(product), report)

    def __getattr__(self, name):
        return getattr(self._repository, name)
