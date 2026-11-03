"""Closed local tools for the Paideia research-only catalogue prototype."""

from __future__ import annotations

from copy import deepcopy
import re
from urllib.parse import urlsplit

from domain import CALCULATION_FIELDS, InputValidationError, calculate_scenario


FAMILIES = (
    "cuenta_remunerada",
    "deposito",
    "letra_deuda_publica",
    "fondo_tradicional",
    "etf_ucits",
)
DEPOSIT_CRITERION = "deposit_tae_12m_eur"
_PRODUCT_ID = re.compile(r"[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){0,2}\Z")


_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Busca candidatos de investigación por identidad; no son ofertas publicables.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "maxLength": 100},
                    "family": {"type": ["string", "null"], "enum": [*FAMILIES, None]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["query", "family", "limit"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_detail",
            "description": "Obtiene metadatos internos de identidad; no implica condiciones del producto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "pattern": "^[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){0,2}$"},
                },
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_products",
            "description": "Compara metadatos internos; una métrica solo se evalúa con el servicio de comparación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "string", "pattern": "^[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){0,2}$"},
                        "minItems": 2,
                        "maxItems": 4,
                        "uniqueItems": True,
                    },
                    "criterion": {
                        "type": ["string", "null"],
                        "enum": [DEPOSIT_CRITERION, None],
                    },
                },
                "required": ["product_ids", "criterion"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_scenario",
            "description": "Calcula un escenario hipotético con el motor determinista local; no es una predicción.",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {
                        "type": "string",
                        "pattern": r"^-?(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?$",
                        "description": "Importe EUR; hasta 1.000.000.000,00.",
                    },
                    "annual_rate_percent": {
                        "type": "string",
                        "pattern": r"^-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,4})?$",
                        "description": "Porcentaje anual; mayor que -100 y hasta 1000.",
                    },
                    "years": {"type": "integer", "minimum": 1, "maximum": 40},
                    "monthly_contribution": {
                        "type": "string",
                        "pattern": r"^-?(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?$",
                        "description": "Aportación mensual EUR; hasta 1.000.000.000,00.",
                    },
                    "method": {"type": "string", "enum": ["simple", "compound"]},
                    "inflation_percent": {
                        "type": "string",
                        "pattern": r"^-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,4})?$",
                        "description": "Porcentaje anual de inflación; mayor que -100 y hasta 1000.",
                    },
                },
                "required": [
                    "principal",
                    "annual_rate_percent",
                    "years",
                    "monthly_contribution",
                    "method",
                    "inflation_percent",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sources",
            "description": "Devuelve citas locales de identidad a partir de los candidatos solicitados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "string", "pattern": "^[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){0,2}$"},
                        "minItems": 1,
                        "maxItems": 20,
                        "uniqueItems": True,
                    },
                },
                "required": ["product_ids"],
                "additionalProperties": False,
            },
        },
    },
]


class ToolDispatcher:
    def __init__(self, repository, comparison_service):
        self._repository = repository
        self._comparison_service = comparison_service

    def definitions(self):
        return deepcopy(_TOOL_DEFINITIONS)

    def dispatch(self, name, arguments):
        if type(name) is not str or name not in {item["function"]["name"] for item in _TOOL_DEFINITIONS}:
            return self._reply(None, "error", error=("UNKNOWN_TOOL", "Herramienta desconocida."))
        try:
            if name == "search_products":
                query, family, limit = self._validate_search(arguments)
                try:
                    raw_products = self._repository.list_products(q=query, family=family)
                except Exception:
                    raise _ToolFailure("REPOSITORY_ERROR", "No se pudo leer el catálogo local.") from None
                if type(raw_products) is not list:
                    raise _ToolFailure("REPOSITORY_ERROR", "No se pudo leer el catálogo local.")
                products = [self._project_product(item) for item in raw_products[:limit]]
                sources = [self._source_for(product) for product in products]
                data = {
                    "items": products,
                    "count": len(products),
                    "limit": limit,
                    "not_for_publication": True,
                    "scope": "product_identity_only",
                }
                return self._reply(name, "ok", data=data, sources=sources)
            if name == "get_product_detail":
                product_id = self._validate_single_id(arguments)
                product = self._lookup_product(product_id)
                return self._reply(name, "ok", data={
                    "product": product,
                    "not_for_publication": True,
                    "scope": "product_identity_only",
                }, sources=[self._source_for(product)])
            if name == "calculate_scenario":
                if type(arguments) is not dict or set(arguments) != CALCULATION_FIELDS:
                    raise _ToolFailure("INVALID_ARGUMENTS", "Los argumentos no cumplen el contrato de la herramienta.")
                try:
                    data = calculate_scenario(deepcopy(arguments))
                except InputValidationError:
                    raise _ToolFailure("INVALID_ARGUMENTS", "Los argumentos no cumplen el contrato de la herramienta.") from None
                return self._reply(name, "ok", data=data, sources=[])
            if name == "compare_products":
                product_ids, criterion = self._validate_compare(arguments)
                products = [self._lookup_product(product_id) for product_id in product_ids]
                sources = [self._source_for(product) for product in products]
                data = {
                    "items": products,
                    "comparison_kind": "educational_metadata_only",
                    "quantitative_ready": False,
                    "hypothetical": False,
                    "not_for_publication": True,
                }
                if criterion is not None:
                    if self._comparison_service is None:
                        raise _ToolFailure("COMPARISON_UNAVAILABLE", "El servicio de comparación no está disponible.")
                    try:
                        comparability = self._comparison_service.compare(deepcopy(products), criterion)
                    except Exception:
                        raise _ToolFailure("COMPARISON_ERROR", "No se pudo evaluar la comparabilidad solicitada.") from None
                    if type(comparability) is not dict or type(comparability.get("quantitative_ready")) is not bool:
                        raise _ToolFailure("COMPARISON_ERROR", "El servicio de comparación devolvió un resultado no válido.")
                    data["comparability"] = deepcopy(comparability)
                    ready = comparability["quantitative_ready"] is True
                    synthetic = comparability.get("test_only") is True
                    data["quantitative_ready"] = ready
                    data["hypothetical"] = ready and synthetic
                    if ready:
                        data["comparison_kind"] = "test_only_quantitative" if synthetic else "quantitative_metric_only"
                return self._reply(name, "ok", data=data, sources=sources)
            if name == "get_sources":
                product_ids = self._validate_source_ids(arguments)
                products = [self._lookup_product(product_id) for product_id in product_ids]
                sources = [self._source_for(product) for product in products]
                return self._reply(name, "ok", data={
                    "count": len(sources),
                    "scope": "product_identity_only",
                    "not_for_publication": True,
                }, sources=sources)
            return self._reply(name, "error", error=("TOOL_UNAVAILABLE", "Herramienta no disponible."))
        except _ToolFailure as failure:
            return self._reply(name, "error", error=(failure.code, failure.message))
        except Exception:
            return self._reply(name, "error", error=("INTERNAL_ERROR", "No se pudo completar la herramienta."))

    @staticmethod
    def _validate_single_id(arguments):
        if (type(arguments) is not dict or set(arguments) != {"product_id"}
                or type(arguments["product_id"]) is not str
                or _PRODUCT_ID.fullmatch(arguments["product_id"]) is None):
            raise _ToolFailure("INVALID_ARGUMENTS", "Los argumentos no cumplen el contrato de la herramienta.")
        return arguments["product_id"]

    def _lookup_product(self, product_id):
        try:
            raw_product = self._repository.get_product(product_id)
        except Exception:
            raise _ToolFailure("REPOSITORY_ERROR", "No se pudo leer el catálogo local.") from None
        if raw_product is None:
            raise _ToolFailure("PRODUCT_NOT_FOUND", "Candidato local no encontrado.")
        product = self._project_product(raw_product)
        if product["id"] != product_id:
            raise _ToolFailure("REPOSITORY_ERROR", "El catálogo local devolvió metadatos no válidos.")
        return product

    @staticmethod
    def _validate_compare(arguments):
        if (type(arguments) is not dict or set(arguments) != {"product_ids", "criterion"}
                or type(arguments["product_ids"]) is not list
                or not 2 <= len(arguments["product_ids"]) <= 4
                or any(type(item) is not str or _PRODUCT_ID.fullmatch(item) is None
                       for item in arguments["product_ids"])
                or len(set(arguments["product_ids"])) != len(arguments["product_ids"])):
            raise _ToolFailure("INVALID_ARGUMENTS", "Los argumentos no cumplen el contrato de la herramienta.")
        criterion = arguments["criterion"]
        if criterion is not None and (type(criterion) is not str or criterion != DEPOSIT_CRITERION):
            raise _ToolFailure("INVALID_ARGUMENTS", "Los argumentos no cumplen el contrato de la herramienta.")
        return list(arguments["product_ids"]), criterion

    @staticmethod
    def _validate_source_ids(arguments):
        if (type(arguments) is not dict or set(arguments) != {"product_ids"}
                or type(arguments["product_ids"]) is not list
                or not 1 <= len(arguments["product_ids"]) <= 20
                or any(type(item) is not str or _PRODUCT_ID.fullmatch(item) is None
                       for item in arguments["product_ids"])
                or len(set(arguments["product_ids"])) != len(arguments["product_ids"])):
            raise _ToolFailure("INVALID_ARGUMENTS", "Los argumentos no cumplen el contrato de la herramienta.")
        return list(arguments["product_ids"])

    @staticmethod
    def _validate_search(arguments):
        if type(arguments) is not dict or set(arguments) != {"query", "family", "limit"}:
            raise _ToolFailure("INVALID_ARGUMENTS", "Los argumentos no cumplen el contrato de la herramienta.")
        query = arguments["query"]
        family = arguments["family"]
        limit = arguments["limit"]
        if (type(query) is not str or len(query) > 100
                or (family is not None and (type(family) is not str or family not in FAMILIES))
                or type(limit) is not int or not 1 <= limit <= 20):
            raise _ToolFailure("INVALID_ARGUMENTS", "Los argumentos no cumplen el contrato de la herramienta.")
        return query, family, limit

    @staticmethod
    def _project_product(raw_product):
        if type(raw_product) is not dict:
            raise _ToolFailure("REPOSITORY_ERROR", "El catálogo local devolvió metadatos no válidos.")
        product_id = raw_product.get("id")
        name = raw_product.get("name")
        family = raw_product.get("family")
        issuer = raw_product.get("issuer")
        isin = raw_product.get("isin")
        identity_state = raw_product.get("identity_state")
        primary_url = raw_product.get("primary_url")
        as_of = raw_product.get("as_of")
        conflicts = raw_product.get("conflicts")
        unknown_fields = raw_product.get("unknown_fields")
        if (type(product_id) is not str or _PRODUCT_ID.fullmatch(product_id) is None
                or type(name) is not str or not name.strip()
                or type(family) is not str or family not in FAMILIES
                or (issuer is not None and type(issuer) is not str)
                or (isin is not None and type(isin) is not str)
                or type(identity_state) is not str or identity_state not in {"verified", "proposed"}
                or type(primary_url) is not str or len(primary_url) > 2048
                or not _is_repository_url(primary_url)
                or (as_of is not None and type(as_of) is not str)
                or raw_product.get("publication_ready") is not False
                or raw_product.get("conditions_state") != "pending"
                or type(conflicts) is not list or not all(type(item) is str for item in conflicts)
                or type(unknown_fields) is not list or not all(type(item) is str for item in unknown_fields)):
            raise _ToolFailure("REPOSITORY_ERROR", "El catálogo local devolvió metadatos no válidos.")
        return {
            "id": product_id,
            "name": name,
            "family": family,
            "issuer": issuer,
            "isin": isin,
            "identity_state": identity_state,
            "primary_url": primary_url,
            "as_of": as_of,
            "publication_ready": False,
            "conditions_state": "pending",
            "conflicts": deepcopy(conflicts),
            "unknown_fields": deepcopy(unknown_fields),
        }

    @staticmethod
    def _source_for(product):
        return {
            "source_ref": {"namespace": "local-tools.v1", "id": f"identity:{product['id']}"},
            "product_id": product["id"],
            "kind": "identity",
            "claim_scope": "product_identity_only",
            "label": product["name"],
            "url": product["primary_url"],
            "not_for_publication": True,
        }

    @staticmethod
    def _reply(tool, status, data=None, sources=None, error=None):
        safe_error = None if error is None else {"code": error[0], "message": error[1]}
        safe_data = {} if status == "error" and data is None else data
        return {
            "schema_version": "local-tools.v1",
            "tool": tool,
            "status": status,
            "data": deepcopy(safe_data),
            "sources": deepcopy(sources) if sources is not None else [],
            "error": safe_error,
        }


class _ToolFailure(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def _is_repository_url(value):
    try:
        parts = urlsplit(value)
        return (parts.scheme == "https" and bool(parts.hostname)
                and parts.username is None and parts.password is None)
    except (TypeError, ValueError):
        return False
