"""Pure, traceable fact and comparability primitives for the local prototype.

This module deliberately has no I/O, catalogue loading, API wiring, or defaults for
production freshness. Callers must supply an explicitly scoped policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import re
from types import MappingProxyType
from typing import Mapping


RULESET_VERSION = "catalogue-fact-comparability.v1"


@dataclass(frozen=True)
class Fact:
    """Immutable single-field evidence record. Decimal values remain strings."""

    fact_id: str
    product_id: str
    family: str
    semantic_scope: str
    field_path: str
    value: str | None
    unit: str
    currency: str | None
    period: str | None
    effective_at: str | None
    effective_precision: str
    validity_state: str
    valid_from: str | None
    valid_to: str | None
    retrieved_at: str
    state: str
    source_id: str
    source_revision_id: str
    locator: str
    permissions_by_action: Mapping[str, str]
    evidence_class: str

    def __post_init__(self) -> None:
        if self.value is not None and (
            not isinstance(self.value, str)
            or re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", self.value) is None
        ):
            raise ValueError("fact values must be base-10 decimal strings or null")
        if self.state not in {"known", "unknown", "conflict", "not_applicable"}:
            raise ValueError("invalid fact state")
        if self.state in {"unknown", "not_applicable"} and self.value is not None:
            raise ValueError("unknown and not_applicable facts must have a null value")
        if self.validity_state not in {"known", "unknown", "conflict"}:
            raise ValueError("invalid validity state")
        if self.effective_precision not in {"date", "datetime", "not_stated"}:
            raise ValueError("invalid effective date precision")
        if self.evidence_class not in {"synthetic_test", "production_candidate"}:
            raise ValueError("invalid evidence class")
        if self.effective_precision == "not_stated":
            if self.effective_at is not None:
                raise ValueError("not_stated precision requires a null effective date")
        elif self.effective_at is None:
            raise ValueError("stated effective precision requires an effective date")
        elif self.effective_precision == "date":
            if date.fromisoformat(self.effective_at).isoformat() != self.effective_at:
                raise ValueError("effective date must use ISO date precision")
        else:
            _parse_datetime(self.effective_at)
        _parse_datetime(self.retrieved_at)
        starts = _parse_iso_date(self.valid_from) if self.valid_from is not None else None
        ends = _parse_iso_date(self.valid_to) if self.valid_to is not None else None
        if starts is not None and ends is not None and starts >= ends:
            raise ValueError("validity interval must use [valid_from, valid_to)")
        if self.currency is not None and re.fullmatch(r"[A-Z]{3}", self.currency) is None:
            raise ValueError("currency must be an uppercase three-letter code")
        if not all((self.fact_id, self.product_id, self.family, self.semantic_scope, self.field_path, self.unit,
                    self.source_id, self.source_revision_id, self.locator)):
            raise ValueError("fact identity and source references must be non-empty")
        object.__setattr__(self, "permissions_by_action", MappingProxyType(dict(self.permissions_by_action)))


@dataclass(frozen=True)
class ComparisonSpec:
    comparison_id: str
    family: str
    semantic_scope: str
    field_path: str
    unit: str
    currency: str
    period: str
    product_ids: tuple[str, ...]
    permission_action: str
    as_of: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_ids", tuple(self.product_ids))
        if not all((self.comparison_id, self.family, self.semantic_scope, self.field_path, self.unit,
                    self.currency, self.period, self.permission_action, self.as_of)):
            raise ValueError("comparison identity, currency, period, and scope must be explicit")
        if re.fullmatch(r"[A-Z]{3}", self.currency) is None:
            raise ValueError("comparison currency must be an uppercase three-letter code")
        if len(self.product_ids) < 2 or len(set(self.product_ids)) != len(self.product_ids):
            raise ValueError("comparison requires at least two distinct product ids")


@dataclass(frozen=True)
class FreshnessPolicy:
    """Explicit freshness thresholds scoped to one family/metric/action."""

    version: str
    family: str
    semantic_scope: str
    field_path: str
    permission_action: str
    max_retrieval_age: timedelta | None
    max_effective_age: timedelta | None

    def __post_init__(self) -> None:
        if not all((self.version, self.family, self.semantic_scope, self.field_path, self.permission_action)):
            raise ValueError("freshness policy version and scope must be explicit")
        for threshold in (self.max_retrieval_age, self.max_effective_age):
            if threshold is not None and (not isinstance(threshold, timedelta) or threshold < timedelta(0)):
                raise ValueError("freshness thresholds must be non-negative timedeltas or explicitly None")


@dataclass(frozen=True)
class _ComparisonItem:
    product_id: str
    eligible: bool
    value: str | None
    evidence_class: str | None
    reason_codes: tuple[str, ...]
    source_refs: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "product_id": self.product_id,
            "eligible": self.eligible,
            "value": self.value,
            "evidence_class": self.evidence_class,
            "reason_codes": list(self.reason_codes),
            "source_refs": [dict(reference) for reference in self.source_refs],
        }


@dataclass(frozen=True)
class ComparisonResult:
    comparison_id: str
    ruleset_version: str
    family: str
    semantic_scope: str
    field_path: str
    unit: str
    currency: str
    period: str
    permission_action: str
    as_of: str
    policy_version: str
    items: tuple[_ComparisonItem, ...]

    @property
    def quantitative_ready(self) -> bool:
        return sum(item.eligible for item in self.items) >= 2

    def to_dict(self) -> dict[str, object]:
        eligible = [item.product_id for item in self.items if item.eligible]
        return {
            "schema_version": "catalogue-comparison.v1",
            "comparison_id": self.comparison_id,
            "ruleset_version": self.ruleset_version,
            "status": "comparable" if self.quantitative_ready else "not_comparable",
            "quantitative_ready": self.quantitative_ready,
            "family": self.family,
            "semantic_scope": self.semantic_scope,
            "field_path": self.field_path,
            "unit": self.unit,
            "currency": self.currency,
            "period": self.period,
            "permission_action": self.permission_action,
            "as_of": self.as_of,
            "policy_version": self.policy_version,
            "eligible_product_ids": eligible,
            "items": [item.to_dict() for item in self.items],
        }


def _source_ref(fact: Fact, permission_action: str) -> dict[str, object]:
    return {
        "fact_id": fact.fact_id,
        "source_id": fact.source_id,
        "source_revision_id": fact.source_revision_id,
        "locator": fact.locator,
        "family": fact.family,
        "semantic_scope": fact.semantic_scope,
        "field_path": fact.field_path,
        "unit": fact.unit,
        "currency": fact.currency,
        "period": fact.period,
        "valid_from": fact.valid_from,
        "valid_to": fact.valid_to,
        "effective_at": fact.effective_at,
        "effective_precision": fact.effective_precision,
        "retrieved_at": fact.retrieved_at,
        "state": fact.state,
        "validity_state": fact.validity_state,
        "permission_state": fact.permissions_by_action.get(permission_action),
    }


def _parse_iso_date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("dates must use ISO YYYY-MM-DD precision")
    return parsed


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def _effective_datetime(fact: Fact) -> datetime | None:
    if fact.effective_at is None and fact.effective_precision == "not_stated":
        return None
    if fact.effective_at is None:
        raise ValueError("effective date is required when precision is stated")
    if fact.effective_precision == "date":
        return datetime.combine(_parse_iso_date(fact.effective_at), datetime.min.time(), timezone.utc)
    if fact.effective_precision == "datetime":
        return _parse_datetime(fact.effective_at)
    raise ValueError("effective date precision is not stated")


def _semantic_signature(fact: Fact) -> tuple[object, ...]:
    return (
        fact.product_id,
        fact.family,
        fact.semantic_scope,
        fact.field_path,
        fact.value,
        fact.unit,
        fact.currency,
        fact.period,
        fact.effective_at,
        fact.effective_precision,
        fact.validity_state,
        fact.valid_from,
        fact.valid_to,
        fact.state,
        fact.evidence_class,
    )


def _fact_reason_codes(
    fact: Fact, spec: ComparisonSpec, policy: FreshnessPolicy, as_of: datetime
) -> tuple[str, ...]:
    reasons: list[str] = []
    if policy.max_retrieval_age is None or policy.max_effective_age is None:
        reasons.append("FRESHNESS_BOUNDS_UNCONFIGURED")
    if fact.family != spec.family:
        reasons.append("FAMILY_MISMATCH")
    if fact.semantic_scope != spec.semantic_scope:
        reasons.append("SCOPE_MISMATCH")
    if fact.unit != spec.unit:
        reasons.append("UNIT_MISMATCH")
    if fact.currency is None:
        reasons.append("CURRENCY_UNKNOWN")
    elif fact.currency != spec.currency:
        reasons.append("CURRENCY_MISMATCH")
    if fact.period is None:
        reasons.append("PERIOD_UNKNOWN")
    elif fact.period != spec.period:
        reasons.append("PERIOD_MISMATCH")
    if any(code in reasons for code in (
        "FAMILY_MISMATCH", "SCOPE_MISMATCH", "UNIT_MISMATCH", "CURRENCY_UNKNOWN", "CURRENCY_MISMATCH",
        "PERIOD_UNKNOWN", "PERIOD_MISMATCH"
    )):
        reasons.append("NUMERIC_BASIS_MISMATCH")
    if fact.state == "conflict":
        reasons.append("DATA_CONFLICT")
    elif fact.state == "not_applicable":
        reasons.append("METRIC_NOT_APPLICABLE")
    elif fact.state == "unknown" or fact.value is None:
        reasons.append("METRIC_MISSING")
    permission = fact.permissions_by_action.get(spec.permission_action)
    if permission == "blocked":
        reasons.append("RIGHTS_BLOCKED")
    elif permission != "allowed":
        reasons.append("RIGHTS_UNRESOLVED")
    retrieved_at = _parse_datetime(fact.retrieved_at)
    if retrieved_at > as_of:
        reasons.append("RETRIEVED_AT_FUTURE")
    elif policy.max_retrieval_age is not None and as_of - retrieved_at > policy.max_retrieval_age:
        reasons.append("SOURCE_STALE")
    effective_at = _effective_datetime(fact)
    if effective_at is None:
        reasons.append("EFFECTIVE_DATE_UNKNOWN")
    elif effective_at > as_of:
        reasons.append("EFFECTIVE_DATE_FUTURE")
    elif policy.max_effective_age is not None and as_of - effective_at > policy.max_effective_age:
        reasons.append("METRIC_STALE")
    if fact.validity_state == "unknown":
        reasons.append("VALIDITY_UNKNOWN")
    elif fact.validity_state == "conflict":
        reasons.append("DATA_CONFLICT")
    if fact.valid_from is not None and _parse_iso_date(fact.valid_from) > as_of.date():
        reasons.append("NOT_YET_EFFECTIVE")
    if fact.valid_to is not None and as_of.date() >= _parse_iso_date(fact.valid_to):
        reasons.append("FACT_EXPIRED")
    return tuple(dict.fromkeys(reasons))


def evaluate_comparability(
    facts: tuple[Fact, ...] | list[Fact],
    spec: ComparisonSpec,
    policy: FreshnessPolicy,
) -> ComparisonResult:
    """Evaluate exact-scope facts without conversion, ranking, or latest-source precedence."""
    if (
        policy.family != spec.family
        or policy.semantic_scope != spec.semantic_scope
        or policy.field_path != spec.field_path
        or policy.permission_action != spec.permission_action
    ):
        raise ValueError("freshness policy scope must match the comparison specification")

    as_of = _parse_datetime(spec.as_of)
    unconfigured = policy.max_retrieval_age is None or policy.max_effective_age is None
    by_product: dict[str, list[Fact]] = {product_id: [] for product_id in spec.product_ids}
    for fact in facts:
        if fact.product_id in by_product and fact.field_path == spec.field_path:
            by_product[fact.product_id].append(fact)

    items: list[_ComparisonItem] = []
    for product_id in spec.product_ids:
        candidates = by_product[product_id]
        if not candidates:
            reasons = ("FRESHNESS_BOUNDS_UNCONFIGURED", "METRIC_MISSING") if unconfigured else ("METRIC_MISSING",)
            items.append(_ComparisonItem(product_id, False, None, None, reasons, ()))
            continue
        unique_candidates: dict[str, Fact] = {}
        conflicting_fact_id = False
        for candidate in candidates:
            previous = unique_candidates.get(candidate.fact_id)
            if previous is None:
                unique_candidates[candidate.fact_id] = candidate
            elif previous != candidate:
                conflicting_fact_id = True
        distinct_candidates = tuple(unique_candidates.values())
        signatures = {_semantic_signature(candidate) for candidate in distinct_candidates}
        ordered_candidates = tuple(sorted(
            distinct_candidates,
            key=lambda item: (item.fact_id, item.source_id, item.source_revision_id, item.locator),
        ))
        if conflicting_fact_id or len(signatures) > 1:
            refs = tuple(_source_ref(candidate, spec.permission_action) for candidate in sorted(
                candidates,
                key=lambda item: (item.fact_id, item.source_id, item.source_revision_id, item.locator),
            ))
            evidence_classes = {candidate.evidence_class for candidate in candidates}
            items.append(_ComparisonItem(
                product_id=product_id,
                eligible=False,
                value=None,
                evidence_class=next(iter(evidence_classes)) if len(evidence_classes) == 1 else "mixed",
                reason_codes=(("FRESHNESS_BOUNDS_UNCONFIGURED", "DATA_CONFLICT") if unconfigured else ("DATA_CONFLICT",)),
                source_refs=refs,
            ))
            continue

        evaluated = tuple(
            (candidate, _fact_reason_codes(candidate, spec, policy, as_of))
            for candidate in ordered_candidates
        )
        eligible_sources = tuple(candidate for candidate, reasons in evaluated if not reasons)
        if eligible_sources:
            item_reasons: tuple[str, ...] = ()
            used_sources = eligible_sources
            value = eligible_sources[0].value
        else:
            item_reasons = tuple(dict.fromkeys(
                reason for _, reasons in evaluated for reason in reasons
            ))
            used_sources = ordered_candidates
            value = None
        evidence_classes = {candidate.evidence_class for candidate in ordered_candidates}
        items.append(_ComparisonItem(
            product_id=product_id,
            eligible=bool(eligible_sources),
            value=value,
            evidence_class=next(iter(evidence_classes)) if len(evidence_classes) == 1 else "mixed",
            reason_codes=item_reasons,
            source_refs=tuple(_source_ref(candidate, spec.permission_action) for candidate in used_sources),
        ))

    return ComparisonResult(
        comparison_id=spec.comparison_id,
        ruleset_version=RULESET_VERSION,
        family=spec.family,
        semantic_scope=spec.semantic_scope,
        field_path=spec.field_path,
        unit=spec.unit,
        currency=spec.currency,
        period=spec.period,
        permission_action=spec.permission_action,
        as_of=spec.as_of,
        policy_version=policy.version,
        items=tuple(items),
    )
