"""Motor educativo determinista Paideia. Solo Decimal y biblioteca estándar.

No integra datos reales, fiscalidad, contratación ni una aplicación. Las funciones
calculan únicamente los supuestos explícitos recibidos; véase ESPECIFICACION.md.
"""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext


DECIMAL_PRECISION = 34
CENT = Decimal("0.01")


@contextmanager
def _work_context():
    """Aísla los cálculos de la precisión/contexto Decimal del llamador."""
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_UP
        yield


def _decimal(value, name):
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"{name} debe ser Decimal, entero o cadena decimal; no float/bool")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{name} no es un decimal válido") from None
    if not result.is_finite():
        raise ValueError(f"{name} debe ser finito")
    return result


def _nonnegative(value, name):
    value = _decimal(value, name)
    if value < 0:
        raise ValueError(f"{name} no puede ser negativo")
    return value


def _positive(value, name):
    value = _decimal(value, name)
    if value <= 0:
        raise ValueError(f"{name} debe ser mayor que cero")
    return value


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} debe ser un entero")
    if value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}")
    return value


def _basis(value):
    value = _integer(value, "day_basis", 1)
    if value not in (360, 365):
        raise ValueError("day_basis solo admite 360 o 365; otras convenciones no están implementadas")
    return value


def _iso_date(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} debe ser una fecha ISO YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} no es una fecha ISO válida YYYY-MM-DD") from None
    if parsed.isoformat() != value:
        raise ValueError(f"{name} debe usar exactamente YYYY-MM-DD")
    return parsed


def _actual_days(start, end, start_name, end_name):
    first = _iso_date(start, start_name)
    last = _iso_date(end, end_name)
    days = (last - first).days
    if days <= 0:
        raise ValueError("el intervalo de fechas debe ser positivo (inicio inclusivo, fin exclusivo)")
    return days


def round_money(value):
    """Redondeo de presentación a céntimos, ROUND_HALF_UP; no redondea flujos internos."""
    with _work_context():
        return _decimal(value, "value").quantize(CENT, rounding=ROUND_HALF_UP)


def simple_interest(principal, annual_rate, days, day_basis=365):
    """Interés simple: P * r_anual * días / base; devuelve interés sin redondear."""
    principal = _nonnegative(principal, "principal")
    rate = _decimal(annual_rate, "annual_rate")
    days = _integer(days, "days")
    basis = _basis(day_basis)
    with _work_context():
        interest = principal * rate * Decimal(days) / Decimal(basis)
        if principal + interest < 0:
            raise ValueError("el saldo resultante no puede ser negativo")
        return interest


def compound_amount(principal, nominal_annual_rate, periods_per_year, periods):
    """Capitalización periódica entera: P * (1 + TIN/m)^n; TIN decimal nominal."""
    principal = _nonnegative(principal, "principal")
    rate = _decimal(nominal_annual_rate, "nominal_annual_rate")
    frequency = _integer(periods_per_year, "periods_per_year", 1)
    periods = _integer(periods, "periods")
    with _work_context():
        base = Decimal(1) + rate / Decimal(frequency)
        if base <= 0:
            raise ValueError("1 + TIN/m debe ser mayor que cero")
        return principal * (base ** periods)


def effective_annual_rate(nominal_annual_rate, periods_per_year):
    """Equivalencia matemática TAE=(1+TIN/m)^m-1, sin comisiones ni condiciones."""
    rate = _decimal(nominal_annual_rate, "nominal_annual_rate")
    frequency = _integer(periods_per_year, "periods_per_year", 1)
    with _work_context():
        base = Decimal(1) + rate / Decimal(frequency)
        if base <= 0:
            raise ValueError("1 + TIN/m debe ser mayor que cero")
        return (base ** frequency) - Decimal(1)


def tiered_account_result(balance, schedule, day_basis):
    """Interés simple por tramos y subperiodos; interés no se capitaliza dentro del cálculo.

    Cada tramo indica su límite de saldo acumulado (up_to), o null para saldo restante.
    El último tramo puede ser finito: el exceso queda sin remunerar. Cada periodo puede
    llevar fee explícita; las fechas han de ser contiguas y el coste se descuenta al final.
    """
    balance = _nonnegative(balance, "balance")
    basis = _basis(day_basis)
    if not isinstance(schedule, list) or not schedule:
        raise ValueError("schedule debe ser una lista no vacía")

    parsed_periods = []
    previous_end = None
    for index, period in enumerate(schedule):
        if not isinstance(period, dict):
            raise ValueError("cada periodo debe ser un objeto")
        start = _iso_date(period.get("start_date"), f"schedule[{index}].start_date")
        end = _iso_date(period.get("end_date"), f"schedule[{index}].end_date")
        days = (end - start).days
        if days <= 0:
            raise ValueError("cada periodo debe tener duración positiva")
        if previous_end is not None and start != previous_end:
            raise ValueError("los periodos deben ser contiguos, sin solapes ni huecos")
        previous_end = end
        tiers = period.get("tiers")
        if not isinstance(tiers, list) or not tiers:
            raise ValueError("cada periodo requiere al menos un tramo")
        prior_limit = Decimal(0)
        parsed_tiers = []
        for tier_index, tier in enumerate(tiers):
            if not isinstance(tier, dict) or "annual_rate" not in tier or "up_to" not in tier:
                raise ValueError("cada tramo requiere up_to y annual_rate")
            raw_limit = tier["up_to"]
            if raw_limit is None:
                if tier_index != len(tiers) - 1:
                    raise ValueError("un tramo ilimitado solo puede ser el último")
                limit = None
            else:
                limit = _positive(raw_limit, "up_to")
                if limit <= prior_limit:
                    raise ValueError("los límites de tramos deben crecer estrictamente")
                prior_limit = limit
            rate = _decimal(tier["annual_rate"], "annual_rate")
            parsed_tiers.append((limit, rate))
        fee = _nonnegative(period.get("fee", "0"), "fee")
        parsed_periods.append((days, parsed_tiers, fee))

    with _work_context():
        gross_interest = Decimal(0)
        fees = Decimal(0)
        for days, tiers, fee in parsed_periods:
            lower = Decimal(0)
            period_interest = Decimal(0)
            for limit, rate in tiers:
                upper = balance if limit is None else min(balance, limit)
                tranche_balance = max(Decimal(0), upper - lower)
                period_interest += tranche_balance * rate * Decimal(days) / Decimal(basis)
                if limit is not None:
                    lower = limit
            gross_interest += period_interest
            fees += fee
        ending = balance + gross_interest - fees
        if ending < 0:
            raise ValueError("interés y comisiones dejarían un saldo negativo")
        return {"gross_interest": gross_interest, "fees": fees, "net_interest": gross_interest - fees, "ending_value": ending}


def deposit_maturity(principal, tin, start_date, maturity_date, day_basis=365, fee="0"):
    """Depósito a plazo con TIN simple pagadero al vencimiento; condiciones y fee explícitos."""
    principal = _nonnegative(principal, "principal")
    days = _actual_days(start_date, maturity_date, "start_date", "maturity_date")
    fee = _nonnegative(fee, "fee")
    interest = simple_interest(principal, tin, days, day_basis)
    with _work_context():
        ending = principal + interest - fee
        if ending < 0:
            raise ValueError("el pago al vencimiento no puede ser negativo")
        return ending


def deposit_cancellation(principal, accrued_interest, forfeited_interest, fee="0"):
    """Payout de cancelación solo bajo forfeiture y cargo indicados expresamente."""
    principal = _nonnegative(principal, "principal")
    accrued = _nonnegative(accrued_interest, "accrued_interest")
    forfeited = _nonnegative(forfeited_interest, "forfeited_interest")
    fee = _nonnegative(fee, "fee")
    if forfeited > accrued:
        raise ValueError("forfeited_interest no puede superar el interés devengado")
    with _work_context():
        payout = principal + accrued - forfeited - fee
        if payout < 0:
            raise ValueError("el pago de cancelación no puede ser negativo")
        return payout


def bill_return(purchase_price, redemption_value, purchase_date, maturity_date, purchase_fee="0", redemption_fee="0"):
    """Retorno de Letra sintético: retorno del periodo y anualización simple ACT/360.

    La anualización no es TAE ni supone reinversión. Fechas reales: inicio inclusivo,
    vencimiento exclusivo; costes explícitos modifican desembolso y reembolso netos.
    """
    price = _positive(purchase_price, "purchase_price")
    redemption = _nonnegative(redemption_value, "redemption_value")
    days = _actual_days(purchase_date, maturity_date, "purchase_date", "maturity_date")
    buy_fee = _nonnegative(purchase_fee, "purchase_fee")
    sell_fee = _nonnegative(redemption_fee, "redemption_fee")
    with _work_context():
        outflow = price + buy_fee
        inflow = redemption - sell_fee
        if inflow < 0:
            raise ValueError("redemption_fee no puede superar el importe de reembolso")
        holding = inflow / outflow - Decimal(1)
        annualized = holding * Decimal(360) / Decimal(days)
        return {"days": days, "net_cash_outlay": outflow, "net_redemption": inflow,
                "holding_period_return": holding, "annualized_simple_act360": annualized}


def bond_cashflows(face_value, annual_coupon_rate, payments_per_year, periods):
    """Flujos contractuales didácticos: cupón periódico y nominal en el último periodo."""
    face = _positive(face_value, "face_value")
    coupon_rate = _nonnegative(annual_coupon_rate, "annual_coupon_rate")
    frequency = _integer(payments_per_year, "payments_per_year", 1)
    periods = _integer(periods, "periods", 1)
    with _work_context():
        coupon = face * coupon_rate / Decimal(frequency)
        flows = [coupon for _ in range(periods)]
        flows[-1] += face
        return flows


def bond_yield(price, face_value, annual_coupon_rate, payments_per_year, periods):
    """TIR de bono con cupones regulares; bisección en yield periódico, antes de impuestos."""
    price = _positive(price, "price")
    flows = bond_cashflows(face_value, annual_coupon_rate, payments_per_year, periods)
    frequency = _integer(payments_per_year, "payments_per_year", 1)
    with _work_context():
        def present_value(rate):
            base = Decimal(1) + rate
            if base <= 0:
                raise ValueError("el rendimiento periódico debe ser mayor que -100%")
            return sum((flow / (base ** index) for index, flow in enumerate(flows, start=1)), Decimal(0))

        low = Decimal("-0.999999999999999999999999999999999")
        high = Decimal(1)
        if present_value(low) < price:
            raise ValueError("precio implica una TIR demasiado próxima a -100% para esta precisión")
        while present_value(high) > price:
            high = high * Decimal(2) + Decimal(1)
            if high > Decimal("1e12"):
                raise ValueError("no se pudo acotar la TIR dentro del rango admitido")
        for _ in range(256):
            middle = (low + high) / Decimal(2)
            if middle == low or middle == high:
                break
            if present_value(middle) > price:
                low = middle
            else:
                high = middle
        periodic_yield = (low + high) / Decimal(2)
        nominal_annual = periodic_yield * Decimal(frequency)
        effective_annual = (Decimal(1) + periodic_yield) ** frequency - Decimal(1)
        return {"periodic_yield": periodic_yield, "nominal_annual_yield": nominal_annual,
                "effective_annual_yield": effective_annual}


def fund_redemption_value(units, nav, redemption_fee="0"):
    """Reembolso educativo a NAV indicado menos comisión explícita; NAV no es precio ETF."""
    units = _nonnegative(units, "units")
    nav = _positive(nav, "nav")
    fee = _nonnegative(redemption_fee, "redemption_fee")
    with _work_context():
        gross = units * nav
        if fee > gross:
            raise ValueError("redemption_fee no puede superar el valor bruto a NAV")
        return gross - fee


def etf_trade_cashflow(units, price, side, commission="0", other_fees="0"):
    """Flujo ETF a cotización indicada; compra debe usar ask y venta bid por quien llame."""
    units = _nonnegative(units, "units")
    price = _positive(price, "price")
    commission = _nonnegative(commission, "commission")
    other_fees = _nonnegative(other_fees, "other_fees")
    if side not in ("buy", "sell"):
        raise ValueError("side debe ser 'buy' o 'sell'")
    with _work_context():
        gross = units * price
        costs = commission + other_fees
        if side == "buy":
            return gross + costs
        if costs > gross:
            raise ValueError("los costes de venta superan el importe de la venta")
        return gross - costs


def ongoing_cost(position_value, annual_cost_rate, days, day_basis=365):
    """Aproximación lineal de coste recurrente sobre valor inicial constante; no NAV observado."""
    value = _nonnegative(position_value, "position_value")
    rate = _nonnegative(annual_cost_rate, "annual_cost_rate")
    days = _integer(days, "days")
    basis = _basis(day_basis)
    with _work_context():
        return value * rate * Decimal(days) / Decimal(basis)


def future_value_contributions(contribution, periodic_rate, periods, timing):
    """Aportación fija mensual; tasa periódica mensual; timing 'beginning' o 'end'."""
    contribution = _nonnegative(contribution, "contribution")
    rate = _decimal(periodic_rate, "periodic_rate")
    periods = _integer(periods, "periods")
    if rate <= -1:
        raise ValueError("periodic_rate debe ser mayor que -100%")
    if timing not in ("beginning", "end"):
        raise ValueError("timing debe ser 'beginning' o 'end'")
    with _work_context():
        balance = Decimal(0)
        factor = Decimal(1) + rate
        for _ in range(periods):
            if timing == "beginning":
                balance = (balance + contribution) * factor
            else:
                balance = balance * factor + contribution
        return balance


def inflation_adjusted_value(nominal_value, inflation_rate, years):
    """Poder adquisitivo en moneda de hoy: valor nominal / (1+inflación)^años."""
    value = _nonnegative(nominal_value, "nominal_value")
    inflation = _decimal(inflation_rate, "inflation_rate")
    years = _integer(years, "years")
    with _work_context():
        factor = Decimal(1) + inflation
        if factor <= 0:
            raise ValueError("inflation_rate debe ser mayor que -100%")
        return value / (factor ** years)
