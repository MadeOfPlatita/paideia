"""Canal cerrado de afirmaciones: validación, composición y degradación.

El modelo solo elige identificadores. Todo el texto que ve el usuario lo
compone este módulo a partir de ``claims_catalog.CLAIMS``; ninguna cadena del
proveedor llega al resultado. Sin red, sin estado y sin efectos.
"""
import re

import claims_catalog

VERSION = claims_catalog.VERSION
MAX_CLAIMS = claims_catalog.MAX_CLAIMS
MAX_EVIDENCE_REFS = 3
CLAIM_IDS = claims_catalog.CLAIM_IDS

# Códigos estables de rechazo. Nunca se acepta un motivo fuera de esta lista:
# el motivo viaja al DTO y no puede contener texto del modelo.
REJECTION_REASONS = (
    "invalid_shape",
    "invalid_version",
    "invalid_intent",
    "invalid_claim_id",
    "duplicate_claim",
    "too_many_claims",
    "invalid_evidence_ref",
)
_REJECTION_SET = frozenset(REJECTION_REASONS)

_BASE_KEYS = frozenset({"version", "intent", "claim_ids"})
_OPTIONAL_KEYS = frozenset({"evidence_refs"})
_INTENTS = frozenset({"explain", "calculate"})
_EVIDENCE_PREFIX = "identity:"
_EVIDENCE_PATTERN = re.compile(r"^identity:[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
_MAX_EVIDENCE_REF_LENGTH = 64


def _fail(reason):
    """Aborta con un código estable, sin añadir texto libre al mensaje."""
    raise ValueError(reason)


def _valid_evidence_ref(ref):
    """Acepta solo ``identity:<producto>`` con un identificador simple y acotado."""
    return (
        ref.startswith(_EVIDENCE_PREFIX)
        and len(ref) <= _MAX_EVIDENCE_REF_LENGTH
        and _EVIDENCE_PATTERN.fullmatch(ref) is not None
    )


def validate_selection(raw):
    """Normaliza una selección del modelo o lanza ``ValueError`` con un código.

    Devuelve siempre ``{version, intent, claim_ids, evidence_refs}`` con listas
    propias. ``claim_ids`` vacío es válido: el turno se compone sin texto.
    """
    if type(raw) is not dict:
        _fail("invalid_shape")

    keys = frozenset(raw)
    if keys not in (_BASE_KEYS, _BASE_KEYS | _OPTIONAL_KEYS):
        _fail("invalid_shape")

    if type(raw["version"]) is not str or raw["version"] != VERSION:
        _fail("invalid_version")

    intent = raw["intent"]
    if type(intent) is not str or intent not in _INTENTS:
        _fail("invalid_intent")

    claim_ids = raw["claim_ids"]
    if type(claim_ids) is not list:
        _fail("invalid_shape")
    seen = set()
    for claim_id in claim_ids:
        if type(claim_id) is not str or claim_id not in claims_catalog.CLAIMS:
            _fail("invalid_claim_id")
        if claim_id in seen:
            _fail("duplicate_claim")
        seen.add(claim_id)
    if len(claim_ids) > MAX_CLAIMS:
        _fail("too_many_claims")

    evidence_refs = raw.get("evidence_refs", [])
    if type(evidence_refs) is not list or len(evidence_refs) > MAX_EVIDENCE_REFS:
        _fail("invalid_evidence_ref")
    seen_refs = set()
    for ref in evidence_refs:
        if type(ref) is not str or not _valid_evidence_ref(ref) or ref in seen_refs:
            _fail("invalid_evidence_ref")
        seen_refs.add(ref)

    return {
        "version": VERSION,
        "intent": intent,
        "claim_ids": list(claim_ids),
        "evidence_refs": list(evidence_refs),
    }


def compose(selection, *, calculation=None, sources=None):
    """Compone la respuesta con textos del catálogo, en el orden elegido.

    ``calculation`` y ``sources`` se copian tal cual: las cifras viven en sus
    paneles y nunca se interpolan en ``answer``. Una selección inválida aborta
    la composición completa, sin texto parcial.
    """
    normalized = validate_selection(selection)

    items = [
        {"id": claim_id, "text": claims_catalog.CLAIMS[claim_id]["text"]}
        for claim_id in normalized["claim_ids"]
    ]

    if sources is None:
        composed_sources = []
    elif type(sources) in (list, tuple):
        composed_sources = list(sources)
    else:
        _fail("invalid_shape")

    return {
        "answer": "\n\n".join(item["text"] for item in items),
        "claims": {
            "version": VERSION,
            "state": "shown" if items else "empty",
            "items": items,
            "count": len(items),
        },
        "calculation": calculation,
        "sources": composed_sources,
    }


def rejected(reason):
    """DTO de degradación: sin texto, con el motivo estable y los paneles vacíos.

    El motivo debe ser uno de ``REJECTION_REASONS``; cualquier otra cadena
    (por ejemplo, texto del modelo) se rechaza en el servidor.
    """
    if type(reason) is not str or reason not in _REJECTION_SET:
        _fail("invalid_reason")
    return {
        "answer": "",
        "claims": {
            "version": VERSION,
            "state": "rejected",
            "items": [],
            "count": 0,
            "reason": reason,
        },
        "calculation": None,
        "sources": [],
    }
