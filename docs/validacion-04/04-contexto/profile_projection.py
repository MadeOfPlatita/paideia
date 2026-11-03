from collections.abc import Mapping
from decimal import Decimal


class ProjectionError(ValueError):
    """Base error for an invalid profile projection request."""


class ConsentError(ProjectionError):
    """Raised when the requested remote processing is not authorized."""


PURPOSE_FIELDS = {
    "learn_basics": frozenset({"objective", "learning_level", "learning_topics"}),
    "debt_education": frozenset({"debt", "objective", "monthly_income_eur", "monthly_expenses_eur", "liquid_reserve_eur", "upcoming_commitments"}),
    "risk_education": frozenset({"objective", "horizon", "risk_tolerance", "loss_capacity", "upcoming_commitments"}),
    "liquidity_planning": frozenset({"objective", "horizon", "target_amount_eur", "monthly_expenses_eur", "liquidity_need", "liquid_reserve_eur", "upcoming_commitments"}),
    "product_comparison": frozenset({"objective", "horizon", "liquidity_need", "risk_tolerance", "loss_capacity", "target_amount_eur", "liquid_reserve_eur"}),
}

_LOCAL_STATES = {
    "declarado": "known",
    "no_se": "unknown",
    "omitido": "omitted",
    "sin_preguntar": "not_asked",
}

_HORIZONS = {
    "menos_6_meses": "under_6_months",
    "6_12_meses": "6_to_12_months",
    "1_3_anos": "1_to_3_years",
    "mas_3_anos": "over_3_years",
    "sin_fecha": "no_fixed_date",
}


_EXPERIENCE_LEVELS = {
    "empezando": "beginner",
    "leido_o_comparado": "read_or_compared",
    "ha_tenido_alguno": "has_used_one",
    "prefiere_no_contar": "prefer_not_to_say",
}

_TOPICS = {
    "cuentas_remuneradas": "remunerated_accounts",
    "depositos": "term_deposits",
    "deuda_publica": "government_debt",
    "fondos": "mutual_funds",
    "etf": "etf",
}


_LIQUIDITY_NEEDS = {
    "acceso_cualquier_momento": "anytime_access",
    "planificar_fecha": "planned_date",
    "solo_dinero_ficticio": "fictional_money_only",
}


_COMMITMENT_TIMING = {
    "menos_3_meses": "under_3_months",
    "3_6_meses": "3_to_6_months",
    "6_12_meses": "6_to_12_months",
    "fecha_no_clara": "date_unclear",
}


_RISK_TOLERANCE = {
    "preferiria_salir": "would_prefer_to_exit",
    "esperaria_con_inquietud": "would_wait_with_concern",
    "podria_esperar_aceptando_caidas": "can_wait_with_drops",
}

_LOSS_IMPACTS = {
    "sin_cambio_en_necesidad_o_meta": "no_change_to_need_or_goal",
    "retrasaria_o_reduciria_meta": "would_delay_or_reduce_goal",
    "afectaria_gasto_esencial_o_compromiso": "would_affect_essential_spending_or_commitment",
}


_OBJECTIVES = {
    "colchon_imprevistos": "emergency_reserve",
    "gasto_previsto": "planned_expense",
    "ahorro_largo_plazo": "long_term_savings",
    "entender_riesgo": "understand_risk",
    "comparar_familias": "compare_families",
    "aprender_conceptos": "learn_concepts",
    "curiosear": "explore",
}

_CONSENT_KEYS = {
    "notice_version",
    "accepted_chat_processing",
    "purpose",
    "approved_fields",
}


def _approved_list(value, label):
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise ProjectionError(f"{label} must be a list of field names")
    if len(value) != len(set(value)):
        raise ProjectionError(f"{label} contains duplicate field names")
    return set(value)


def _local_answer(answer, value_mapper):
    if not isinstance(answer, Mapping) or set(answer) - {"estado", "valor"}:
        raise ProjectionError("Local answer has an invalid shape")
    state = answer.get("estado")
    if not isinstance(state, str) or state not in _LOCAL_STATES:
        raise ProjectionError("Local answer has an unknown state")
    result = {"state": _LOCAL_STATES[state]}
    if state == "declarado":
        if "valor" not in answer:
            raise ProjectionError("Declared local answer is missing its value")
        try:
            result["value"] = value_mapper(answer["valor"])
        except ProjectionError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise ProjectionError("Declared local answer value is invalid") from exc
    elif "valor" in answer:
        raise ProjectionError("Undeclared local answer must not contain a value")
    return result


def _map_objective(profile):
    try:
        answer = profile["respuestas"]["objetivo"]
    except (KeyError, TypeError) as exc:
        raise ProjectionError("Local objective answer is missing") from exc
    return _local_answer(answer, lambda value: _OBJECTIVES[value])


def _map_horizon(profile):
    try:
        answer = profile["respuestas"]["horizonte"]
    except (KeyError, TypeError) as exc:
        raise ProjectionError("Local horizon answer is missing") from exc
    return _local_answer(answer, lambda value: _HORIZONS[value])


def _map_liquidity_need(profile):
    try:
        answer = profile["respuestas"]["liquidez"]
    except (KeyError, TypeError) as exc:
        raise ProjectionError("Local liquidity answer is missing") from exc
    return _local_answer(answer, lambda value: _LIQUIDITY_NEEDS[value])


def _map_experience(profile, part):
    try:
        answer = profile["respuestas"]["experiencia"]
    except (KeyError, TypeError) as exc:
        raise ProjectionError("Local experience answer is missing") from exc

    def map_value(value):
        if not isinstance(value, Mapping) or set(value) != {"nivel", "temas_interes"}:
            raise ProjectionError("Local experience value has an invalid shape")
        try:
            if part == "learning_level":
                return _EXPERIENCE_LEVELS[value["nivel"]]
            topics = value["temas_interes"]
            if not isinstance(topics, (list, tuple)) or len(topics) != len(set(topics)):
                raise ProjectionError("Learning topics must be a unique list")
            return [_TOPICS[topic] for topic in topics]
        except KeyError as exc:
            raise ProjectionError("Unknown local experience value") from exc

    return _local_answer(answer, map_value)


def _map_risk(profile, field_name):
    try:
        answer = profile["riesgo"][field_name]
    except (KeyError, TypeError) as exc:
        raise ProjectionError(f"Local risk answer {field_name} is missing") from exc

    if field_name == "tolerancia":
        return _local_answer(answer, lambda value: _RISK_TOLERANCE[value])

    def map_capacity(value):
        if not isinstance(value, Mapping) or set(value) != {"escenario_id", "impacto"}:
            raise ProjectionError("Loss capacity answer has an invalid shape")
        if value["escenario_id"] != "caida_100_de_1000":
            raise ProjectionError("Unknown loss-capacity scenario")
        try:
            impact = _LOSS_IMPACTS[value["impacto"]]
        except KeyError as exc:
            raise ProjectionError("Unknown loss-capacity impact") from exc
        return {"scenario": "drop_100_of_1000", "impact": impact}

    return _local_answer(answer, map_capacity)


def _decimal_string(value):
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise ProjectionError("Financial values must be int or Decimal, never float")
    amount = Decimal(value) if isinstance(value, int) else value
    if not amount.is_finite() or amount.is_signed():
        raise ProjectionError("Financial values must be finite and non-negative")
    return format(amount, "f")


def _map_euro_range(value):
    if not isinstance(value, Mapping) or set(value) != {"min_eur", "max_eur", "moneda"}:
        raise ProjectionError("Euro range has an invalid shape")
    if value["moneda"] != "EUR":
        raise ProjectionError("Only EUR ranges are supported in this prototype")
    minimum = _decimal_string(value["min_eur"])
    maximum = None if value["max_eur"] is None else _decimal_string(value["max_eur"])
    if maximum is not None and Decimal(minimum) > Decimal(maximum):
        raise ProjectionError("Euro range minimum exceeds maximum")
    return {"min_eur": minimum, "max_eur": maximum, "currency": "EUR"}


def _map_percent_range(value):
    if not isinstance(value, Mapping) or set(value) != {"min_pct", "max_pct"}:
        raise ProjectionError("Percentage range has an invalid shape")
    minimum = _decimal_string(value["min_pct"])
    maximum = "100" if value["max_pct"] is None else _decimal_string(value["max_pct"])
    if Decimal(minimum) > Decimal(maximum) or Decimal(maximum) > Decimal("100"):
        raise ProjectionError("Percentage range is outside 0–100 or inverted")
    return {"min_percent": minimum, "max_percent": maximum}


def _map_flow(answer):
    def map_value(value):
        if not isinstance(value, Mapping) or set(value) != {"importe", "periodicidad"}:
            raise ProjectionError("Flow value has an invalid shape")
        periods = {
            "semanal": "weekly",
            "cada_14_dias": "every_14_days",
            "dos_veces_al_mes": "twice_monthly",
            "mensual": "monthly",
            "anual": "annual",
        }
        try:
            periodicity = periods[value["periodicidad"]]
        except KeyError as exc:
            raise ProjectionError("Unknown flow periodicity") from exc
        return {"amount": _map_euro_range(value["importe"]), "periodicity": periodicity}

    return _local_answer(answer, map_value)


def _map_flow_field(profile, local_name):
    try:
        answer = profile["detalle_economico"][local_name]
    except (KeyError, TypeError) as exc:
        raise ProjectionError(f"Local {local_name} answer is missing") from exc
    return _map_flow(answer)


def _map_target_amount(profile):
    try:
        answer = profile["detalle_economico"]["importe_objetivo"]
    except (KeyError, TypeError) as exc:
        raise ProjectionError("Local target amount answer is missing") from exc
    return _local_answer(answer, _map_euro_range)


def _map_amount_field(profile, local_name):
    try:
        answer = profile["detalle_economico"][local_name]
    except (KeyError, TypeError) as exc:
        raise ProjectionError(f"Local {local_name} answer is missing") from exc
    return _local_answer(answer, _map_euro_range)


def _map_commitments(profile):
    try:
        answer = profile["detalle_economico"]["compromisos_proximos"]
    except (KeyError, TypeError) as exc:
        raise ProjectionError("Local commitments answer is missing") from exc

    def map_value(value):
        if not isinstance(value, Mapping):
            raise ProjectionError("Local commitments value must be an object")
        if value == {"hay_compromiso": False}:
            return {"has_commitment": False}
        if set(value) != {"hay_compromiso", "total_eur", "plazo"} or value["hay_compromiso"] is not True:
            raise ProjectionError("Local commitments value has an invalid shape")
        try:
            due_within = _COMMITMENT_TIMING[value["plazo"]]
        except KeyError as exc:
            raise ProjectionError("Unknown commitment timing") from exc
        return {
            "has_commitment": True,
            "total_eur": _map_euro_range(value["total_eur"]),
            "due_within": due_within,
        }

    return _local_answer(answer, map_value)


def _map_debt(profile):
    try:
        answer = profile["detalle_economico"]["deuda"]
    except (KeyError, TypeError) as exc:
        raise ProjectionError("Local debt answer is missing") from exc

    def map_debt_value(value):
        if not isinstance(value, Mapping):
            raise ProjectionError("Local debt value must be an object")
        if value == {"situacion": "sin_deuda"}:
            return {"situation": "no_debt"}
        expected = {"situacion", "saldo_eur", "cuota", "coste_anual_pct"}
        if set(value) != expected or value["situacion"] != "con_deuda":
            raise ProjectionError("Local debt value has an invalid shape")
        return {
            "situation": "has_debt",
            "balance_eur": _local_answer(value["saldo_eur"], _map_euro_range),
            "monthly_payment_eur": _map_flow(value["cuota"]),
            "annual_cost_percent": _local_answer(value["coste_anual_pct"], _map_percent_range),
        }

    return _local_answer(answer, map_debt_value)


_FIELD_MAPPERS = {
    "objective": _map_objective,
    "debt": _map_debt,
    "target_amount_eur": _map_target_amount,
    "horizon": _map_horizon,
    "monthly_expenses_eur": lambda profile: _map_flow_field(profile, "gastos_esenciales"),
    "learning_level": lambda profile: _map_experience(profile, "learning_level"),
    "learning_topics": lambda profile: _map_experience(profile, "learning_topics"),
    "risk_tolerance": lambda profile: _map_risk(profile, "tolerancia"),
    "loss_capacity": lambda profile: _map_risk(profile, "capacidad_perdidas"),
    "liquidity_need": _map_liquidity_need,
    "upcoming_commitments": _map_commitments,
    "monthly_income_eur": lambda profile: _map_flow_field(profile, "ingresos_netos"),
    "liquid_reserve_eur": lambda profile: _map_amount_field(profile, "colchon_liquido"),
}

_ALL_PROFILE_FIELDS = frozenset(_FIELD_MAPPERS)
_BENCHMARK_FIXTURE_IDS = frozenset({"synthetic-full-profile-01"})


def project_profile(profile, *, purpose, selected_fields, consent):
    """Build a selected-only remote DTO; never serialize the local profile."""
    if not isinstance(consent, Mapping):
        raise ConsentError("Explicit chat-processing consent is required")
    if consent.get("accepted_chat_processing") is not True:
        raise ConsentError("Chat processing consent is required")
    if set(consent) != _CONSENT_KEYS:
        raise ConsentError("Consent object has missing or unexpected fields")
    if not isinstance(consent.get("notice_version"), str) or not consent["notice_version"].strip():
        raise ConsentError("A notice version is required")

    if not isinstance(purpose, str) or purpose not in PURPOSE_FIELDS:
        raise ProjectionError("Unknown projection purpose")
    requested = _approved_list(selected_fields, "selected_fields")
    approved = _approved_list(consent["approved_fields"], "approved_fields")
    if not requested:
        raise ProjectionError("At least one profile field must be selected")
    if consent.get("purpose") != purpose or approved != requested:
        raise ConsentError("Consent does not match the current purpose and field selection")
    if not requested <= PURPOSE_FIELDS[purpose]:
        raise ProjectionError("A selected field is not allowed for this purpose")

    fields = {name: _FIELD_MAPPERS[name](profile) for name in selected_fields}
    return {"contract_version": "0.1", "purpose": purpose, "fields": fields}


def project_synthetic_full_for_benchmark(fixture):
    """Project every mapped field from an explicitly synthetic fixture only."""
    if not isinstance(fixture, Mapping) or set(fixture) != {"classification", "fixture_id", "profile"}:
        raise ProjectionError("Benchmark input must be a closed synthetic-fixture envelope")
    if fixture["classification"] != "synthetic_fixture":
        raise ProjectionError("Full projection is reserved for synthetic fixtures")
    fixture_id = fixture["fixture_id"]
    if not isinstance(fixture_id, str) or fixture_id not in _BENCHMARK_FIXTURE_IDS:
        raise ProjectionError("Fixture ID is not allowlisted for this benchmark")
    profile = fixture["profile"]
    if not isinstance(profile, Mapping):
        raise ProjectionError("Synthetic fixture profile must be an object")
    if profile.get("version_esquema") != "1.0.0" or profile.get("tipo") != "mapa_educativo":
        raise ProjectionError("Synthetic fixture must use the local Spanish profile schema")

    fields = {name: _FIELD_MAPPERS[name](profile) for name in sorted(_ALL_PROFILE_FIELDS)}
    return {
        "classification": "synthetic_benchmark_only",
        "contract_version": "0.1",
        "purpose": "complete_synthetic_benchmark",
        "fixture_id": fixture_id,
        "fields": fields,
    }
