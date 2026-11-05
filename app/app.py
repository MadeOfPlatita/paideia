import argparse
import copy
import importlib
import json
import os
import re
import uuid
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, unquote_to_bytes, urlsplit

from domain import InputValidationError, calculate_scenario
from backend_services import CatalogueComparisonService, DEPOSIT_CRITERION, LocalChatService, ServiceProblem
from conditions_service import ConditionsService
from env_local import load_env
from pai_setup import build_chat_service, chat_enabled


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = Path(__file__).resolve().parent
SNAPSHOT_RELATIVE_PATH = Path("docs/validacion-04/05-catalogo/candidatos.json")
SNAPSHOT_PATH = PROJECT_ROOT / SNAPSHOT_RELATIVE_PATH
CURATED_RELATIVE_PATH = Path("app/data/condiciones.json")
CURATED_PATH = PROJECT_ROOT / CURATED_RELATIVE_PATH
# Etiquetas de la instantánea de investigación que dejan de ser «desconocidas» cuando
# la ficha transcrita documenta esos campos. Se empareja por texto, no por posición.
UNKNOWN_FIELD_RULES = (
    (("tin/tae por plazo", "plazos disponibles", "tasa aplicable por plazo"), ("rate", "term")),
    (("mínimo/máximo",), ("min", "max")),
    (("liquidación de intereses", "frecuencia pactada de liquidación"), ("payment",)),
    (("saldo máximo remunerado",), ("max",)),
    (("fecha efectiva de cada oferta", "fecha de inicio/fin de la tae"), ("validity",)),
)


def _unknown_label_is_documented(label, fields):
    """¿La ficha documenta todo lo que esa etiqueta decía desconocer?"""
    texto = label.casefold()
    for needles, required in UNKNOWN_FIELD_RULES:
        if any(needle in texto for needle in needles) and set(required) <= set(fields):
            return True
    return False
STATIC_ROOT = APP_DIR / "static"
MAX_STATIC_BYTES = 2 * 1024 * 1024
STATIC_MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".woff2": "font/woff2",
}
ALLOWED_FAMILIES = frozenset({
    "cuenta_remunerada",
    "deposito",
    "letra_deuda_publica",
    "fondo_tradicional",
    "etf_ucits",
})
SYNTHETIC_FIXTURE_ALLOWLIST = frozenset({"synthetic-full-profile-01"})
CONTEXT_PURPOSE_FIELDS = {
    "learn_basics": frozenset({"objective", "learning_level", "learning_topics"}),
    "debt_education": frozenset({"debt", "objective", "monthly_income_eur", "monthly_expenses_eur", "liquid_reserve_eur", "upcoming_commitments"}),
    "risk_education": frozenset({"objective", "horizon", "risk_tolerance", "loss_capacity", "upcoming_commitments"}),
    "liquidity_planning": frozenset({"objective", "horizon", "target_amount_eur", "monthly_expenses_eur", "liquidity_need", "liquid_reserve_eur", "upcoming_commitments"}),
    "product_comparison": frozenset({"objective", "horizon", "liquidity_need", "risk_tolerance", "loss_capacity", "target_amount_eur", "liquid_reserve_eur"}),
}
_PRODUCT_ID = re.compile(r"[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){0,2}\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_CONFLICT_TEXT_LIMIT = 300


def _conflict_text(item):
    """Texto del conflicto tal y como está documentado, sin HTML ni controles.

    Se escapa al renderizar; aquí solo se acota longitud y se quitan caracteres de
    control. Sustituirlo por una frase genérica ocultaría qué discrepa.
    """
    if not isinstance(item, str):
        return ""
    clean = "".join(char for char in item if char.isprintable() or char == " ")
    clean = " ".join(clean.split())
    return clean[:_CONFLICT_TEXT_LIMIT]


def _curated_product_records():
    """Fichas mínimas de los productos que solo existen como condiciones transcritas.

    Solo datos transcritos con fuente: nombre, entidad, familia y URL. Nada se
    inventa y la ficha sigue marcada como no publicable.
    """
    try:
        resolved = CURATED_PATH.resolve(strict=True)
        if not resolved.is_relative_to(PROJECT_ROOT.resolve(strict=True)):
            return ()
        document = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return ()
    records = document.get("records") if isinstance(document, dict) else None
    if not isinstance(records, list):
        return ()
    products = []
    for record in records:
        if not isinstance(record, dict):
            continue
        product_id = record.get("candidate_id")
        name = record.get("name")
        family = record.get("family")
        provider = record.get("provider")
        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        url = source.get("url")
        kind = source.get("kind")
        if (not isinstance(product_id, str) or not _PRODUCT_ID.fullmatch(product_id)
                or not isinstance(name, str) or not name.strip()
                or family not in ALLOWED_FAMILIES
                or not isinstance(url, str)):
            continue
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname or parts.username is not None:
            continue
        products.append({
            "id": product_id,
            "name": name.strip(),
            "family": family,
            "issuer": provider if isinstance(provider, str) else None,
            "isin": None,
            "identity_state": "verified" if kind == "official" else "proposed",
            "primary_url": url,
            "as_of": source.get("retrieved_at") if isinstance(source.get("retrieved_at"), str) else None,
            "publication_ready": False,
            "conditions_state": "documented",
            "conflicts": [],
            "unknown_fields": [],
            "origin": "curated_conditions",
        })
    return tuple(products)


class ApiProblem(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


MAX_BODY_BYTES = 16_384


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


class CatalogueRepository:
    """Read-only interface for the local catalogue snapshot."""

    @property
    def count(self):
        raise NotImplementedError

    def list_products(self, q=None, family=None):
        raise NotImplementedError

    def get_product(self, product_id):
        raise NotImplementedError


class SnapshotRepository(CatalogueRepository):
    """Whitelisted metadata view of the internal candidate JSON snapshot."""

    def __init__(self):
        source_path = SNAPSHOT_PATH.resolve(strict=True)
        root = PROJECT_ROOT.resolve(strict=True)
        if not source_path.is_relative_to(root):
            raise RuntimeError("catalogue snapshot path is outside the project")
        try:
            source = json.loads(
                source_path.read_text(encoding="utf-8"),
                object_pairs_hook=_unique_object,
            )
        except (OSError, UnicodeError, ValueError) as exc:
            raise RuntimeError("catalogue snapshot cannot be read safely") from exc
        candidates = source.get("candidates") if isinstance(source, dict) else None
        if not isinstance(candidates, list):
            raise RuntimeError("catalogue snapshot must contain a candidates list")

        products = []
        seen_ids = set()
        conflict_details = {}
        for candidate in candidates:
            product = self._to_product(candidate)
            if product["id"] in seen_ids:
                raise RuntimeError("catalogue snapshot contains duplicate candidate IDs")
            seen_ids.add(product["id"])
            products.append(product)
            raw_conflicts = [_conflict_text(item) for item in (candidate.get("conflicts") or [])
                             if isinstance(item, str)]
            raw_conflicts = [text for text in raw_conflicts if text][:5]
            if raw_conflicts:
                conflict_details[product["id"]] = tuple(raw_conflicts)
        self._conflict_details = conflict_details
        self._products = tuple(products)
        self._by_id = {product["id"]: product for product in products}
        # Los transcritos solo existen como condiciones: se añaden a la consulta por id
        # para que su ficha exista, sin alterar la lista de candidatos del snapshot.
        for product in _curated_product_records():
            self._by_id.setdefault(product["id"], product)

    @staticmethod
    def _to_product(candidate):
        if not isinstance(candidate, dict):
            raise RuntimeError("catalogue candidate must be an object")
        product_id = candidate.get("candidate_id")
        name = candidate.get("name_literal")
        family = candidate.get("family")
        state = candidate.get("candidate_state")
        if (not isinstance(product_id, str) or not _PRODUCT_ID.fullmatch(product_id)
                or not isinstance(name, str) or not name.strip()
                or family not in ALLOWED_FAMILIES
                or state not in {"verified", "proposed"}):
            raise RuntimeError("catalogue candidate identity is invalid")

        manager = candidate.get("issuer_manager")
        issuer = manager.get("brand") if isinstance(manager, dict) else None
        if issuer is not None and not isinstance(issuer, str):
            issuer = None
        isin_record = candidate.get("isin")
        isin = isin_record.get("literal") if isinstance(isin_record, dict) else None
        if isin is not None and not isinstance(isin, str):
            isin = None

        primary_url = candidate.get("primary_url")
        if not isinstance(primary_url, str):
            raise RuntimeError("catalogue candidate source URL is missing")
        parts = urlsplit(primary_url)
        if (parts.scheme != "https" or not parts.hostname
                or parts.username is not None or parts.password is not None):
            raise RuntimeError("catalogue candidate source URL is invalid")

        effective = candidate.get("dates", {}).get("effective", {})
        as_of = None
        if isinstance(effective, dict):
            candidate_date = effective.get("as_of")
            scope = effective.get("scope", "")
            if (isinstance(candidate_date, str) and _DATE.fullmatch(candidate_date)
                    and isinstance(scope, str) and "nav" not in scope.casefold()):
                try:
                    date.fromisoformat(candidate_date)
                except ValueError:
                    pass
                else:
                    as_of = candidate_date

        source_conflicts = candidate.get("conflicts", [])
        if not isinstance(source_conflicts, list):
            source_conflicts = []
        # La lista y el comparador de metadatos no publican cifras: el texto literal
        # del conflicto, que puede citar tasas, se reserva para la ficha del producto.
        conflicts = ["Conflicto de fuentes pendiente de revisión; ver la ficha del producto."
                     for item in source_conflicts[:5] if isinstance(item, str)]
        unknown = candidate.get("unknown_fields", [])
        if not isinstance(unknown, list) or not all(isinstance(item, str) for item in unknown):
            unknown = []

        return {
            "id": product_id,
            "name": name,
            "family": family,
            "issuer": issuer,
            "isin": isin,
            "identity_state": state,
            "primary_url": primary_url,
            "as_of": as_of,
            "publication_ready": False,
            "conditions_state": "pending",
            "conflicts": conflicts,
            "unknown_fields": list(unknown),
        }

    @property
    def count(self):
        return len(self._products)

    def list_products(self, q=None, family=None):
        query = q.casefold() if q is not None else None
        products = []
        for product in self._products:
            if family is not None and product["family"] != family:
                continue
            if query is not None:
                searchable = " ".join(str(product[key] or "") for key in (
                    "id", "name", "family", "issuer"
                )).casefold()
                if query not in searchable:
                    continue
            products.append(copy.deepcopy(product))
        return products

    def get_product(self, product_id):
        product = self._by_id.get(product_id)
        return copy.deepcopy(product) if product is not None else None

    def get_product_detail(self, product_id):
        """Ficha: incluye el texto literal del conflicto documentado, sin cifras sueltas."""
        product = self.get_product(product_id)
        if product is not None and product_id in getattr(self, "_conflict_details", {}):
            product["conflicts"] = list(self._conflict_details[product_id])
        return product


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, status, payload, extra_headers=()):
        encoded = json.dumps(
            payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(encoded)

    def _send_error(self, problem):
        error = {
            "code": problem.code,
            "message": problem.message,
            "request_id": uuid.uuid4().hex,
            "retryable": False,
        }
        state = problem.send_state if type(problem) is ServiceProblem else None
        if type(state) is str and state in ('not_started', 'unknown', 'completed'):
            error['send_state'] = state
        self._send_json(problem.status, {"error": error})

    def send_error(self, code, message=None, explain=None):
        self.close_connection = True
        status = 405 if code == 501 else int(code)
        if not 400 <= status <= 599:
            status = 400
        method_error = code == 501
        self._send_json(status, {
            "error": {
                "code": "METHOD_NOT_ALLOWED" if method_error else "BAD_HTTP_REQUEST",
                "message": "Método no permitido." if method_error else "Solicitud HTTP no válida.",
                "request_id": uuid.uuid4().hex,
                "retryable": False,
            }
        })

    def _not_found(self):
        raise ApiProblem(404, "NOT_FOUND", "Recurso no encontrado.")

    def _with_conditions_state(self, item):
        """Ajusta el estado de la ficha a lo que la app tiene documentado.

        La instantánea de investigación marca campos desconocidos que después se
        transcribieron con fuente. Si la ficha los documenta, dejan de listarse como
        desconocidos; si no, se quedan tal cual.
        """
        service = self.server.conditions_service
        if service is None or not isinstance(item, dict):
            return item
        try:
            fields = service.documented_fields(item.get("id"))
        except (OSError, ValueError, RuntimeError):
            return item
        if not fields:
            return item
        unknown = item.get("unknown_fields")
        unknown = list(unknown) if isinstance(unknown, list) else []
        remaining = [label for label in unknown
                     if not (isinstance(label, str) and _unknown_label_is_documented(label, fields))]
        updated = dict(item)
        updated["unknown_fields"] = remaining
        updated["conditions_state"] = "documented" if "rate" in fields else "partial"
        return updated

    def _catalogue_query(self, raw_query):
        if len(raw_query) > 512 or re.search(r"%(?![0-9A-Fa-f]{2})", raw_query):
            raise ApiProblem(400, "INVALID_QUERY", "Parámetros de consulta no válidos.")
        try:
            pairs = parse_qsl(raw_query, keep_blank_values=True, strict_parsing=True)
        except ValueError as exc:
            raise ApiProblem(400, "INVALID_QUERY", "Parámetros de consulta no válidos.") from exc
        values = {}
        for key, value in pairs:
            if key not in {"q", "family"} or key in values:
                raise ApiProblem(400, "INVALID_QUERY", "Parámetros de consulta no válidos.")
            values[key] = value
        q = values.get("q")
        family = values.get("family")
        if q is not None and len(q) > 100:
            raise ApiProblem(400, "INVALID_QUERY", "Parámetros de consulta no válidos.")
        if family is not None and family not in ALLOWED_FAMILIES:
            raise ApiProblem(400, "INVALID_QUERY", "Familia no válida.")
        return q, family

    def _reject_bad_transport(self, status, code, message):
        self.close_connection = True
        raise ApiProblem(status, code, message)

    def _assert_same_origin(self):
        host_values = self.headers.get_all("Host", [])
        origin_values = self.headers.get_all("Origin", [])
        if len(host_values) != 1 or len(origin_values) != 1:
            self._reject_bad_transport(403, "ORIGIN_REJECTED", "Origen no permitido.")
        declared = declared_public_origin()
        if declared:
            self._assert_declared_origin(host_values[0], origin_values[0], declared)
            return
        raw_host = host_values[0]
        try:
            host_parts = urlsplit("//" + raw_host)
            host_name = host_parts.hostname
            host_port = host_parts.port if host_parts.port is not None else 80
        except ValueError:
            self._reject_bad_transport(403, "ORIGIN_REJECTED", "Origen no permitido.")
        if (host_parts.path or host_parts.query or host_parts.fragment
                or host_parts.username is not None or host_parts.password is not None
                or host_name not in {"127.0.0.1", "localhost"}
                or host_port != self.server.server_port):
            self._reject_bad_transport(403, "ORIGIN_REJECTED", "Origen no permitido.")
        try:
            origin = urlsplit(origin_values[0])
            origin_name = origin.hostname
            origin_port = origin.port if origin.port is not None else 80
        except ValueError:
            self._reject_bad_transport(403, "ORIGIN_REJECTED", "Origen no permitido.")
        if (origin.scheme != "http" or origin_name != host_name
                or origin_port != host_port or origin.username is not None
                or origin.password is not None or origin.query or origin.fragment
                or origin.path not in {"", "/"}):
            self._reject_bad_transport(403, "ORIGIN_REJECTED", "Origen no permitido.")

    def _assert_declared_origin(self, raw_host, raw_origin, declared):
        """Origen exacto cuando la app se sirve detrás de un proxy HTTPS (p. ej. Render)."""
        try:
            expected = urlsplit(declared)
            origin = urlsplit(raw_origin)
            host = urlsplit("//" + raw_host)
            expected_port = expected.port or 443
            pairs = [(expected, expected_port, "https"),
                     (origin, expected_port, "https"),
                     (host, expected_port, None)]
            for candidate, port, required_scheme in pairs:
                if (candidate.hostname != expected.hostname
                        or (candidate.port or 443) != port
                        or candidate.path not in ("", "/") or candidate.query
                        or candidate.fragment or candidate.username is not None
                        or candidate.password is not None
                        or (required_scheme is not None and candidate.scheme != required_scheme)):
                    self._reject_bad_transport(403, "ORIGIN_REJECTED", "Origen no permitido.")
        except ValueError:
            self._reject_bad_transport(403, "ORIGIN_REJECTED", "Origen no permitido.")

    def _read_json_body(self):
        content_types = self.headers.get_all("Content-Type", [])
        if len(content_types) != 1:
            self._reject_bad_transport(415, "INVALID_CONTENT_TYPE", "Se requiere application/json.")
        content_type_parts = [part.strip() for part in content_types[0].split(";")]
        if (content_type_parts[0].casefold() != "application/json"
                or any(part.casefold() != "charset=utf-8" for part in content_type_parts[1:])
                or len(content_type_parts) > 2):
            self._reject_bad_transport(415, "INVALID_CONTENT_TYPE", "Se requiere application/json UTF-8.")
        if self.headers.get("Content-Encoding") not in (None, "identity"):
            self._reject_bad_transport(415, "INVALID_CONTENT_ENCODING", "Codificación no admitida.")
        if self.headers.get_all("Transfer-Encoding", []):
            self._reject_bad_transport(400, "INVALID_BODY", "Cuerpo no válido.")
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,8}", lengths[0]):
            self._reject_bad_transport(411, "CONTENT_LENGTH_REQUIRED", "Longitud de cuerpo no válida.")
        length = int(lengths[0])
        if length > MAX_BODY_BYTES:
            self._reject_bad_transport(413, "BODY_TOO_LARGE", "Cuerpo demasiado grande.")
        raw_body = self.rfile.read(length)
        if len(raw_body) != length:
            self._reject_bad_transport(400, "INVALID_BODY", "Cuerpo no válido.")
        try:
            text = raw_body.decode("utf-8", errors="strict")
            payload = json.loads(
                text,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError("non-finite JSON number")),
                object_pairs_hook=_unique_object,
            )
        except (UnicodeError, ValueError, RecursionError, json.JSONDecodeError):
            raise ApiProblem(400, "INVALID_JSON", "JSON no válido.")
        if not isinstance(payload, dict):
            raise ApiProblem(400, "INVALID_REQUEST", "Se requiere un objeto JSON.")
        return payload

    def _handle_compare(self, payload):
        if set(payload) not in ({"product_ids"}, {"product_ids", "criterion"}):
            raise ApiProblem(400, "INVALID_REQUEST", "Campos de comparación no válidos.")
        if "criterion" in payload and payload["criterion"] != DEPOSIT_CRITERION:
            raise ApiProblem(400, "INVALID_REQUEST", "Criterio de comparación no válido.")
        product_ids = payload["product_ids"]
        if (not isinstance(product_ids, list) or not 2 <= len(product_ids) <= 4
                or not all(isinstance(item, str) and _PRODUCT_ID.fullmatch(item) for item in product_ids)
                or len(set(product_ids)) != len(product_ids)):
            raise ApiProblem(400, "INVALID_REQUEST", "Se requieren de 2 a 4 IDs distintos.")
        items = []
        for product_id in product_ids:
            product = self.server.catalogue_repository.get_product(product_id)
            if product is None:
                product = self._curated_product(product_id)
                if product is None:
                    raise ApiProblem(404, "PRODUCT_NOT_FOUND", "Candidato no encontrado.")
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
        if "criterion" in payload:
            comparability = None
            service = self.server.conditions_service
            if service is not None:
                try:
                    comparability = service.comparability(product_ids, payload["criterion"])
                except (OSError, ValueError, RuntimeError):
                    comparability = None
            result["comparability"] = comparability or self.server.comparison_service.compare(items, payload["criterion"])
            if result["comparability"]["quantitative_ready"]:
                synthetic = result["comparability"].get("test_only", False)
                result.update(quantitative_ready=True, hypothetical=synthetic,
                              comparison_kind="test_only_quantitative" if synthetic else "quantitative_metric_only",
                              reasons=["Se evalúa solo la métrica documentada en la fuente citada; no la oferta contractual completa."])
            elif comparability is not None:
                result["reasons"] = ["No hay dos productos con la misma métrica documentada, vigente y del mismo plazo; no se ordena nada."]
        return result

    def _curated_product(self, product_id):
        service = self.server.conditions_service
        if service is None:
            return None
        try:
            entry = service.for_product(product_id)
        except (OSError, ValueError, RuntimeError):
            return None
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

    def _validate_context_preview(self, payload):
        required = {"synthetic_fixture", "fixture_id", "purpose", "selected_fields", "consent"}
        if set(payload) != required:
            raise ApiProblem(400, "INVALID_REQUEST", "Vista previa sintética no válida.")
        if payload["synthetic_fixture"] is not True:
            raise ApiProblem(400, "INVALID_REQUEST", "Se exige synthetic_fixture=true.")
        fixture_id = payload["fixture_id"]
        if not isinstance(fixture_id, str) or fixture_id not in SYNTHETIC_FIXTURE_ALLOWLIST:
            raise ApiProblem(403, "FIXTURE_NOT_ALLOWED", "Fixture sintética no permitida.")
        purpose = payload["purpose"]
        if not isinstance(purpose, str) or purpose not in CONTEXT_PURPOSE_FIELDS:
            raise ApiProblem(400, "INVALID_REQUEST", "Propósito no válido.")
        selected = payload["selected_fields"]
        if (not isinstance(selected, list) or len(selected) > 13
                or not all(isinstance(field, str) for field in selected)
                or len(selected) != len(set(selected))
                or not set(selected).issubset(CONTEXT_PURPOSE_FIELDS[purpose])):
            raise ApiProblem(400, "INVALID_REQUEST", "Selección de campos no válida.")
        consent = payload["consent"]
        if (not isinstance(consent, dict)
                or set(consent) != {"notice_version", "accepted_chat_processing", "purpose", "approved_fields"}
                or not isinstance(consent.get("notice_version"), str)
                or not consent["notice_version"].strip()
                or len(consent["notice_version"]) > 64
                or consent.get("accepted_chat_processing") is not True
                or consent.get("purpose") != purpose
                or consent.get("approved_fields") != selected):
            raise ApiProblem(400, "INVALID_REQUEST", "Consentimiento sintético no válido.")

    def _handle_chat(self, payload):
        return self.server.chat_service.chat(payload)

    def _handle_context_preview(self, payload):
        self._validate_context_preview(payload)
        try:
            adapter = importlib.import_module("context_adapter")
            preview_synthetic = getattr(adapter, "preview_synthetic", None)
        except Exception:
            raise ApiProblem(503, "CONTEXT_ADAPTER_UNAVAILABLE", "Adaptador de contexto no integrado.")
        if not callable(preview_synthetic):
            raise ApiProblem(503, "CONTEXT_ADAPTER_UNAVAILABLE", "Adaptador de contexto no integrado.")
        try:
            result = preview_synthetic(payload)
        except Exception as exc:
            code = getattr(exc, "code", "")
            if code in {"LOCAL_SOURCE_UNAVAILABLE", "FIXTURE_UNAVAILABLE", "FIXTURE_INVALID"}:
                raise ApiProblem(503, "CONTEXT_ADAPTER_UNAVAILABLE", "Fixture o adaptador local no disponible.") from exc
            if code == "FIXTURE_NOT_ALLOWLISTED":
                raise ApiProblem(403, "FIXTURE_NOT_ALLOWED", "Fixture sintética no permitida.") from exc
            raise ApiProblem(400, "INVALID_REQUEST", "La vista previa sintética no pudo validarse.") from exc
        if (not isinstance(result, dict) or set(result) != {"projection", "external_sent"}
                or result.get("external_sent") is not False
                or not isinstance(result.get("projection"), dict)):
            raise ApiProblem(503, "CONTEXT_ADAPTER_UNAVAILABLE", "El adaptador devolvió un resultado no válido.")
        return result

    def do_POST(self):
        request = urlsplit(self.path)
        if request.path in {"/api/status", "/api/catalogue"} or request.path.startswith("/api/products/"):
            self.close_connection = True
            self._send_error(ApiProblem(405, "METHOD_NOT_ALLOWED", "Método no permitido."))
            return
        if request.path not in {"/api/compare", "/api/calculate", "/api/chat", "/api/chat-status", "/api/context-preview"} or request.query:
            self.close_connection = True
            self._send_error(ApiProblem(404, "NOT_FOUND", "Recurso no encontrado."))
            return
        try:
            self._assert_same_origin()
            payload = self._read_json_body()
            if request.path == "/api/compare":
                self._send_json(200, self._handle_compare(payload))
            elif request.path == "/api/calculate":
                try:
                    result = calculate_scenario(payload)
                except InputValidationError as exc:
                    raise ApiProblem(400, "INVALID_REQUEST", "Parámetros de cálculo no válidos.") from exc
                self._send_json(200, result)
            elif request.path == "/api/chat":
                result = self._handle_chat(payload)
                self._send_json(result.pop("_http_status", 200), result)
            elif request.path == "/api/chat-status":
                self._send_json(200, self.server.chat_service.queue_status(payload))
            elif request.path == "/api/context-preview":
                self._send_json(200, self._handle_context_preview(payload))
            else:
                self._not_found()
        except (ApiProblem, ServiceProblem) as problem:
            self._send_error(problem)
        except Exception:
            self._send_error(ApiProblem(500, "INTERNAL_ERROR", "Error interno."))

    def _serve_static(self, raw_path, query):
        if query:
            self._not_found()
        if raw_path == "/" or raw_path in {"/static", "/static/"}:
            relative = "index.html"
        elif raw_path.startswith("/static/"):
            relative = raw_path[len("/static/"):]
        else:
            relative = raw_path.lstrip("/")
        if (not relative or "\\" in relative or "\x00" in relative
                or re.search(r"%(?![0-9A-Fa-f]{2})", relative)):
            self._not_found()
        try:
            decoded = unquote_to_bytes(relative).decode("utf-8", errors="strict")
            segments = decoded.split("/")
            if (decoded.startswith("/") or "\\" in decoded or "\x00" in decoded
                    or any(segment in {"", ".", ".."} for segment in segments)):
                self._not_found()
            static_root = STATIC_ROOT.resolve(strict=True)
            app_dir = APP_DIR.resolve(strict=True)
            expected_static_root = app_dir / "static"
            if STATIC_ROOT.is_symlink() or static_root != expected_static_root:
                self._not_found()
            target = static_root.joinpath(*segments).resolve(strict=True)
            if not target.is_relative_to(static_root) or not target.is_file():
                self._not_found()
            content_type = STATIC_MIME_TYPES.get(target.suffix.casefold())
            if content_type is None or target.stat().st_size > MAX_STATIC_BYTES:
                self._not_found()
            body = target.read_bytes()
        except (OSError, UnicodeError, ValueError):
            self._not_found()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self'; font-src 'self'; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _method_not_allowed(self):
        self._send_error(ApiProblem(405, "METHOD_NOT_ALLOWED", "Método no permitido."))

    def do_OPTIONS(self):
        self._method_not_allowed()

    def do_HEAD(self):
        self._method_not_allowed()

    def do_PUT(self):
        self._method_not_allowed()

    def do_PATCH(self):
        self._method_not_allowed()

    def do_DELETE(self):
        self._method_not_allowed()

    def do_GET(self):
        request = urlsplit(self.path)
        path = request.path
        try:
            if path == "/api/status" and not request.query:
                repo = self.server.catalogue_repository
                self._send_json(200, {
                    "mode": "public_demo" if declared_public_origin() else "local_prototype",
                    "ai": {**self.server.chat_service.status(), "quota": self.server.chat_service.quota()},
                    "catalogue": {"candidate_count": repo.count, "publication_ready": 0},
                    "storage": "local_snapshot_not_postgresql",
                })
                return
            if path == "/api/catalogue":
                q, family = self._catalogue_query(request.query)
                items = [self._with_conditions_state(item)
                         for item in self.server.catalogue_repository.list_products(q=q, family=family)]
                self._send_json(200, {
                    "items": items,
                    "count": len(items),
                    "not_for_publication": True,
                })
                return
            if path == "/api/conditions" and not request.query:
                service = self.server.conditions_service
                if service is None:
                    raise ApiProblem(503, "CONDITIONS_UNAVAILABLE", "Este servidor no expone condiciones del catálogo.")
                try:
                    report = service.describe()
                except (OSError, ValueError, RuntimeError):
                    raise ApiProblem(503, "CONDITIONS_UNAVAILABLE", "No se pudieron leer las condiciones del catálogo.") from None
                self._send_json(200, report)
                return
            if path.startswith("/api/products/") and not request.query:
                product_id = path[len("/api/products/"):]
                if not _PRODUCT_ID.fullmatch(product_id):
                    self._not_found()
                repository = self.server.catalogue_repository
                product = getattr(repository, "get_product_detail", repository.get_product)(product_id)
                service = self.server.conditions_service
                conditions = None
                if service is not None:
                    try:
                        conditions = service.for_product(product_id)
                    except (OSError, ValueError, RuntimeError):
                        conditions = None
                if product is None and conditions is None:
                    self._not_found()
                if product is not None:
                    product = self._with_conditions_state(product)
                self._send_json(200, {"product": product, "conditions": conditions})
                return
            if path in {"/api/compare", "/api/calculate", "/api/chat", "/api/chat-status", "/api/context-preview"}:
                raise ApiProblem(405, "METHOD_NOT_ALLOWED", "Método no permitido.")
            if path == "/api" or path.startswith("/api/"):
                self._not_found()
            self._serve_static(path, request.query)
        except ApiProblem as problem:
            self._send_error(problem)
        except Exception:
            self._send_error(ApiProblem(500, "INTERNAL_ERROR", "Error interno."))

    def log_message(self, fmt, *args):
        return


def declared_public_origin():
    """Origen público exacto, si este proceso se sirve detrás de un proxy HTTPS."""
    for name in ("PAIDEIA_PUBLIC_ORIGIN", "RENDER_EXTERNAL_URL"):
        value = os.environ.get(name, "").strip()
        if value:
            return value.rstrip("/")
    return ""


def create_server(host="127.0.0.1", port=8765, repository=None, *, comparison_service=None, chat_service=None):
    allowed_hosts = {"127.0.0.1"}
    # Un despliegue público declara su origen exacto; solo entonces se permite
    # escuchar fuera del bucle local. Sin esa variable todo sigue siendo local.
    if declared_public_origin():
        allowed_hosts.add("0.0.0.0")
    if host not in allowed_hosts:
        raise ValueError("the local prototype binds only to 127.0.0.1")
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("port must be an integer from 0 through 65535")
    httpd = ThreadingHTTPServer((host, port), _Handler)
    httpd.daemon_threads = True
    try:
        catalogue = repository if repository is not None else SnapshotRepository()
        comparison = comparison_service if comparison_service is not None else CatalogueComparisonService()
        httpd.catalogue_repository = catalogue
        httpd.comparison_service = comparison
        httpd.chat_service = (chat_service if chat_service is not None
                              else build_chat_service(catalogue, comparison))
        httpd.conditions_service = ConditionsService() if repository is None else None
    except Exception:
        httpd.server_close()
        raise
    return httpd


def _port_argument(value):
    try:
        port = int(value, 10)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("port must be an integer from 1 through 65535") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be an integer from 1 through 65535")
    return port


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Paideia local-only prototype backend")
    parser.add_argument("--port", type=_port_argument, default=8765)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    load_env()
    port = int(os.environ.get("PORT") or args.port)
    host = os.environ.get("PAIDEIA_HOST") or ("0.0.0.0" if declared_public_origin() else "127.0.0.1")
    server = create_server(host=host, port=port)
    print(f"Paideia listening on http://{host}:{server.server_port}/")
    from providers import PROVIDER_LABEL, API_KEY_ENV as KEY_ENV
    print("Chat IA: " + (f"conectado a {PROVIDER_LABEL}; una llamada por turno admitido." if chat_enabled()
                          else f"no configurado (sin .env con PAIDEIA_GROQ_ENABLED=1 y {KEY_ENV})."))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
