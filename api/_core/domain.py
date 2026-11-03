# Copia generada por api/build_core.py desde prototipos/paideia-local/domain.py. No editar aquí.
import re
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext


CENT = Decimal("0.01")
MAX_AMOUNT = Decimal("1000000000.00")
MAX_RATE_PERCENT = Decimal("1000")
CALCULATION_FIELDS = frozenset({
    "principal",
    "annual_rate_percent",
    "years",
    "monthly_contribution",
    "method",
    "inflation_percent",
})
_AMOUNT_PATTERN = re.compile(r"-?(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?\Z")
_RATE_PATTERN = re.compile(r"-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,4})?\Z")


class InputValidationError(ValueError):
    """Raised for a closed-contract request with invalid or unsafe values."""


def _parse_decimal_string(value, name, pattern, minimum, maximum):
    if not isinstance(value, str) or len(value) > 24 or not pattern.fullmatch(value):
        raise InputValidationError(f"{name} must be a bounded decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise InputValidationError(f"{name} must be a bounded decimal string") from exc
    if not parsed.is_finite() or parsed < minimum or parsed > maximum:
        raise InputValidationError(f"{name} is outside the allowed range")
    return parsed


def parse_amount(value, name):
    return _parse_decimal_string(
        value, name, _AMOUNT_PATTERN, Decimal("0"), MAX_AMOUNT
    )


def parse_percent(value, name):
    parsed = _parse_decimal_string(
        value, name, _RATE_PATTERN, Decimal("-100"), MAX_RATE_PERCENT
    )
    if parsed <= Decimal("-100"):
        raise InputValidationError(f"{name} must be greater than -100 percent")
    return parsed


def _money(value):
    rounded = value.quantize(CENT, rounding=ROUND_HALF_UP)
    if rounded == 0:
        rounded = Decimal("0.00")
    return format(rounded, ".2f")


def _plain_decimal(value):
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _effective_monthly_rate(annual_percent):
    if annual_percent == 0:
        return Decimal("0")
    annual_factor = Decimal("1") + annual_percent / Decimal("100")
    return (annual_factor.ln() / Decimal("12")).exp() - Decimal("1")


def calculate_scenario(request):
    """Calculate a hypothetical simple/compound series without product claims."""
    if not isinstance(request, Mapping) or set(request) != CALCULATION_FIELDS:
        raise InputValidationError("calculation fields do not match the contract")

    principal = parse_amount(request["principal"], "principal")
    annual_rate = parse_percent(request["annual_rate_percent"], "annual_rate_percent")
    monthly_contribution = parse_amount(
        request["monthly_contribution"], "monthly_contribution"
    )
    inflation = parse_percent(request["inflation_percent"], "inflation_percent")
    years = request["years"]
    if isinstance(years, bool) or not isinstance(years, int) or not 1 <= years <= 40:
        raise InputValidationError("years must be an integer from 1 through 40")
    method = request["method"]
    if not isinstance(method, str) or method not in {"simple", "compound"}:
        raise InputValidationError("method must be simple or compound")

    months = years * 12
    with localcontext() as context:
        context.prec = 80
        annual_rate_monthly = annual_rate / Decimal("1200")
        compound_monthly_rate = _effective_monthly_rate(annual_rate)
        inflation_monthly_rate = _effective_monthly_rate(inflation)
        compound_factor = Decimal("1") + compound_monthly_rate
        inflation_factor = Decimal("1") + inflation_monthly_rate

        points = []
        balance = principal
        inflation_accumulator = Decimal("1")

        def append_point(month, current_balance, contributions):
            real_balance = current_balance / inflation_accumulator
            points.append({
                "month": month,
                "contributions": _money(contributions),
                "balance": _money(current_balance),
                "real_balance": _money(real_balance),
            })

        append_point(0, balance, principal)
        for month in range(1, months + 1):
            contributions = principal + monthly_contribution * month
            if method == "compound":
                balance = balance * compound_factor + monthly_contribution
            else:
                interest = annual_rate_monthly * (
                    principal * month
                    + monthly_contribution * month * (month - 1) / Decimal("2")
                )
                balance = contributions + interest
            inflation_accumulator *= inflation_factor
            if month % 12 == 0 or month == months:
                append_point(month, balance, contributions)

        total_contributions = principal + monthly_contribution * months
        final_balance = balance
        final_interest = final_balance - total_contributions
        final_real_balance = final_balance / inflation_accumulator

        return {
            "hypothetical": True,
            "not_prediction": True,
            "currency": "EUR",
            "assumptions": {
                "principal": _money(principal),
                "annual_rate_percent": _plain_decimal(annual_rate),
                "years": years,
                "monthly_contribution": _money(monthly_contribution),
                "method": method,
                "inflation_percent": _plain_decimal(inflation),
                "annual_rate_convention": "effective_annual_rate" if method == "compound" else "simple_annual_rate",
                "monthly_contribution_timing": "end_of_month",
                "monthly_rate_conversion": "effective_monthly_rate" if method == "compound" else "annual_simple_rate_divided_by_12",
                "working_precision": "80_significant_decimal_digits",
                "rounding": "half_up_to_cents_in_serialized_output; no_cent_rounding_per_month",
                "taxes_included": False,
                "fees_included": False,
            },
            "summary": {
                "contributions": _money(total_contributions),
                "final_balance": _money(final_balance),
                "interest": _money(final_interest),
                "inflation_adjusted": _money(final_real_balance),
            },
            "series": points,
        }
