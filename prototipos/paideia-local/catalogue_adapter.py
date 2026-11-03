"""Vista del catálogo para las herramientas de Pai: identidad + condiciones documentadas.

No sustituye al repositorio ni a la UI: añade los productos transcritos de fuentes y
adjunta, cuando existen, las condiciones con su estado y su fuente. Nada se inventa.
"""

from __future__ import annotations

import unicodedata


class CatalogueWithConditions:
    def __init__(self, repository, conditions_service):
        self._repository = repository
        self._conditions = conditions_service

    def _report(self):
        try:
            return self._conditions.describe()
        except Exception:
            return {"products": []}

    def _conditions_for(self, product_id, report):
        for entry in report["products"]:
            if entry.get("product_id") == product_id:
                return [condition for condition in entry.get("conditions", []) if condition.get("state") in {"known", "stale", "conflict", "unknown"}]
        return []

    def list_products(self, q=None, family=None):
        items = [dict(item) for item in self._repository.list_products(q=q, family=family)]
        report = self._report()
        seen = {item.get("id") for item in items}
        try:
            extras = self._conditions.catalogue_extras(q=None, family=family)
        except Exception:
            extras = []
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
        for item in items:
            item["conditions"] = self._conditions_for(item.get("id"), report)
        return items

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
            for entry in report["products"]:
                if entry.get("product_id") == product_id:
                    source = entry.get("source") or {}
                    product = {
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
                    }
                    break
        if product is None:
            return None
        product = dict(product)
        product["conditions"] = self._conditions_for(product_id, report)
        return product

    def __getattr__(self, name):
        return getattr(self._repository, name)
