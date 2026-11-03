#!/usr/bin/env python3
"""Reproduce las salidas educativas de escenarios-ejemplo.json (stdlib only)."""
from __future__ import annotations

import argparse
import calendar
import json
import math
from datetime import date
from pathlib import Path
from typing import Any

DEFAULT_DATA = Path(__file__).with_name("escenarios-ejemplo.json")


def money(value: float) -> float:
    return round(value + 0.0, 2)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def period_end(start: date, month_number: int) -> str:
    if month_number == 0:
        return start.isoformat()
    absolute_month = start.year * 12 + (start.month - 1) + month_number - 1
    year, month0 = divmod(absolute_month, 12)
    month = month0 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day).isoformat()


def annual_snapshots(months: int) -> set[int]:
    points = {0, months}
    points.update(range(12, months + 1, 12))
    return points


def compute_contract(case: dict[str, Any]) -> dict[str, Any]:
    start = parse_date(case["fecha_inicio"])
    maturity = parse_date(case["fecha_vencimiento"])
    days = (maturity - start).days
    if days <= 0:
        raise ValueError(f"{case['id']}: fecha de vencimiento debe ser posterior al inicio")
    inflation = float(case["inflacion_efectiva_anual_supuesta"])
    if inflation <= -1:
        raise ValueError("la inflación supuesta debe ser mayor que -100%")
    inflation_factor = (1.0 + inflation) ** (days / 365.0)
    alternatives = []
    for item in case["alternativas"]:
        initial = float(item["desembolso_inicial_eur"])
        entry_fee = float(item.get("coste_entrada_eur", 0.0))
        gross_receipt = float(item["cobro_bruto_vencimiento_eur"])
        exit_fee = float(item.get("coste_salida_eur", 0.0))
        cash_out = initial + entry_fee
        cash_in = gross_receipt - exit_fee
        if cash_out <= 0 or cash_in <= 0 or entry_fee < 0 or exit_fee < 0:
            raise ValueError(f"{item['id']}: importes y costes inválidos")
        effective_annualized_gross = (gross_receipt / initial) ** (365.0 / days) - 1.0
        effective_annualized_net = (cash_in / cash_out) ** (365.0 / days) - 1.0
        real_receipt = cash_in / inflation_factor
        alternatives.append(
            {
                "id": item["id"],
                "familia": item["familia"],
                "desembolso_total_nominal_eur": money(cash_out),
                "cobro_bruto_vencimiento_eur": money(gross_receipt),
                "coste_total_nominal_eur": money(entry_fee + exit_fee),
                "cobro_neto_vencimiento_eur": money(cash_in),
                "resultado_nominal_vs_desembolso_eur": money(cash_in - cash_out),
                "rendimiento_anualizado_bruto_del_flujo_no_tae": round(effective_annualized_gross, 8),
                "rendimiento_anualizado_neto_del_flujo_no_tae": round(effective_annualized_net, 8),
                "saldo_final_real_eur_fecha_inicio": money(real_receipt),
                "resultado_real_vs_desembolso_inicial_eur_fecha_inicio": money(real_receipt - cash_out),
                "fecha_vencimiento": maturity.isoformat(),
                "dias_calendario": days,
                "impuestos_incluidos": False,
            }
        )
    return {
        "modo": "flujo_contractual_sintetico",
        "fecha_inicio": start.isoformat(),
        "fecha_vencimiento": maturity.isoformat(),
        "inflacion_efectiva_anual_supuesta": inflation,
        "factor_inflacion_periodo": round(inflation_factor, 8),
        "alternativas": alternatives,
    }


def validate_market_case(case: dict[str, Any]) -> None:
    months = int(case["horizonte_meses"])
    if months <= 0:
        raise ValueError(f"{case['id']}: horizonte debe ser positivo")
    if int(case.get("mes_inicio_retiradas", 1)) < 1:
        raise ValueError("mes_inicio_retiradas debe ser >= 1")
    for key in ("aporte_inicial_eur", "aporte_mensual_eur", "retirada_mensual_eur", "coste_entrada_eur", "coste_por_operacion_aporte_eur", "coste_por_operacion_retirada_eur", "coste_anual_sobre_saldo"):
        if float(case.get(key, 0.0)) < 0:
            raise ValueError(f"{case['id']}: {key} no puede ser negativo")
    if float(case["coste_anual_sobre_saldo"]) >= 1:
        raise ValueError("coste anual debe ser menor que 100%")
    inflation = float(case["inflacion_efectiva_anual_supuesta"])
    if inflation <= -1:
        raise ValueError("inflación supuesta debe ser mayor que -100%")


def run_market_path(
    case: dict[str, Any],
    path_id: str,
    label: str,
    annual_returns: list[float],
) -> dict[str, Any]:
    validate_market_case(case)
    start = parse_date(case["fecha_inicio"])
    months = int(case["horizonte_meses"])
    initial = float(case["aporte_inicial_eur"])
    monthly_contribution = float(case["aporte_mensual_eur"])
    monthly_withdrawal = float(case["retirada_mensual_eur"])
    annual_fee = float(case["coste_anual_sobre_saldo"])
    inflation = float(case["inflacion_efectiva_anual_supuesta"])
    entry_fee = float(case.get("coste_entrada_eur", 0.0))
    contribution_fee = float(case.get("coste_por_operacion_aporte_eur", 0.0))
    withdrawal_fee = float(case.get("coste_por_operacion_retirada_eur", 0.0))
    if len(annual_returns) < math.ceil(months / 12):
        raise ValueError(f"{case['id']}/{path_id}: faltan rendimientos para todo el horizonte")
    if any(float(r) <= -1 for r in annual_returns):
        raise ValueError("cada rendimiento anual supuesto debe ser mayor que -100%")
    if entry_fee > initial:
        raise ValueError("el coste de entrada no puede superar el aporte inicial")

    balance = initial - entry_fee
    contributions_nominal = initial
    contributions_real = initial
    withdrawals_requested = 0.0
    withdrawals_paid = 0.0
    withdrawals_paid_real = 0.0
    shortfall = 0.0
    management_costs = 0.0
    transaction_costs = entry_fee
    initial_inflation_factor = 1.0
    output_points: list[dict[str, Any]] = []

    def snapshot(month: int) -> dict[str, Any]:
        inflation_factor = (1.0 + inflation) ** (month / 12.0)
        return {
            "mes": month,
            "fecha": period_end(start, month),
            "aportado_nominal_eur": money(contributions_nominal),
            "aportado_real_eur_fecha_inicio": money(contributions_real),
            "saldo_nominal_eur": money(balance),
            "saldo_real_eur_fecha_inicio": money(balance / inflation_factor),
            "retirado_pagado_nominal_eur": money(withdrawals_paid),
            "retirado_pagado_real_eur_fecha_inicio": money(withdrawals_paid_real),
            "retirada_pedida_acumulada_eur": money(withdrawals_requested),
            "retirada_no_cubierta_acumulada_eur": money(shortfall),
            "costes_acumulados_nominal_eur": money(management_costs + transaction_costs),
        }

    output_points.append(snapshot(0))
    fee_monthly_factor = (1.0 - annual_fee) ** (1.0 / 12.0)
    withdrawal_start = int(case.get("mes_inicio_retiradas", 1))
    points = annual_snapshots(months)

    for month in range(1, months + 1):
        gross_annual_return = float(annual_returns[(month - 1) // 12])
        gross_monthly_factor = (1.0 + gross_annual_return) ** (1.0 / 12.0)
        gross_balance = balance * gross_monthly_factor
        period_management_cost = gross_balance * (1.0 - fee_monthly_factor)
        balance = gross_balance - period_management_cost
        management_costs += period_management_cost

        # Los aportes se hacen al final de mes y no reciben rendimiento ese mes.
        if monthly_contribution:
            if contribution_fee > monthly_contribution:
                raise ValueError("coste por aporte supera el importe del aporte")
            transaction_costs += contribution_fee
            invested = monthly_contribution - contribution_fee
            contributions_nominal += monthly_contribution
            contributions_real += monthly_contribution / ((1.0 + inflation) ** (month / 12.0))
            balance += invested

        # Retirar después de revalorización, coste y aporte; nunca se crea saldo negativo.
        if month >= withdrawal_start and monthly_withdrawal:
            if withdrawal_fee > monthly_withdrawal:
                raise ValueError("coste por retirada supera el importe solicitado")
            requested = monthly_withdrawal
            withdrawals_requested += requested
            paid_gross = min(balance, requested)
            fee_from_withdrawal = min(withdrawal_fee, paid_gross)
            paid_net = paid_gross - fee_from_withdrawal
            balance = max(0.0, balance - paid_gross)
            withdrawals_paid += paid_net
            withdrawals_paid_real += paid_net / ((1.0 + inflation) ** (month / 12.0))
            transaction_costs += fee_from_withdrawal
            shortfall += requested - paid_net

        if month in points:
            output_points.append(snapshot(month))

    inflation_factor_end = (1.0 + inflation) ** (months / 12.0)
    final_real = balance / inflation_factor_end
    result_nominal_vs_contributions = balance + withdrawals_paid - contributions_nominal
    result_real_vs_contributions = final_real + withdrawals_paid_real - contributions_real
    return {
        "id": path_id,
        "etiqueta": label,
        "rentabilidades_efectivas_anuales_nominales_antes_de_costes": [round(float(r), 8) for r in annual_returns],
        "aportado_total_nominal_eur": money(contributions_nominal),
        "aportado_total_real_eur_fecha_inicio": money(contributions_real),
        "saldo_final_nominal_eur": money(balance),
        "saldo_final_real_eur_fecha_inicio": money(final_real),
        "retiradas_solicitadas_nominal_eur": money(withdrawals_requested),
        "retiradas_pagadas_netas_nominal_eur": money(withdrawals_paid),
        "retiradas_no_cubiertas_nominal_eur": money(shortfall),
        "retiradas_pagadas_netas_reales_eur_fecha_inicio": money(withdrawals_paid_real),
        "resultado_nominal_vs_aportado_mas_retiradas_eur": money(result_nominal_vs_contributions),
        "resultado_real_vs_aportado_mas_retiradas_eur_fecha_inicio": money(result_real_vs_contributions),
        "costes_modelados_nominal_eur": money(management_costs + transaction_costs),
        "coste_gestion_sobre_saldo_nominal_eur": money(management_costs),
        "costes_operacion_nominal_eur": money(transaction_costs),
        "impuestos_incluidos": False,
        "serie_anual": output_points,
    }


def compute_market_case(case: dict[str, Any]) -> dict[str, Any]:
    if case["modo"] == "hipotesis_mercado":
        paths = []
        for band in case["bandas"]:
            annual_return = float(band["rentabilidad_efectiva_anual_nominal_antes_de_costes"])
            paths.append(
                run_market_path(case, band["id"], band["etiqueta"], [annual_return] * math.ceil(int(case["horizonte_meses"]) / 12))
            )
    else:
        paths = [
            run_market_path(case, item["id"], item["etiqueta"], item["rentabilidades_efectivas_anuales"])
            for item in case["recorridos_anuales_nominales_antes_de_costes"]
        ]
    return {
        "modo": case["modo"],
        "fecha_inicio": case["fecha_inicio"],
        "horizonte_meses": case["horizonte_meses"],
        "inflacion_efectiva_anual_supuesta": case["inflacion_efectiva_anual_supuesta"],
        "coste_anual_sobre_saldo": case["coste_anual_sobre_saldo"],
        "salidas_por_recorrido": paths,
    }


def compute_all(document: dict[str, Any]) -> dict[str, Any]:
    outputs: dict[str, Any] = {}
    for case in document["entradas"]:
        if case["modo"] == "flujo_contractual":
            outputs[case["id"]] = compute_contract(case)
        else:
            outputs[case["id"]] = compute_market_case(case)
    return outputs


def assert_close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=0.011):
        raise AssertionError(f"{label}: esperado {expected}, obtenido {actual}")


def self_test(outputs: dict[str, Any]) -> None:
    contracts = outputs["contrato-a-vencimiento"]["alternativas"]
    deposit = next(x for x in contracts if x["id"] == "deposito-fijo-sintetico")
    bill = next(x for x in contracts if x["id"] == "letra-sintetica")
    assert_close(deposit["cobro_neto_vencimiento_eur"], 5017.60, "cobro depósito didáctico")
    assert_close(bill["cobro_neto_vencimiento_eur"], 5000.00, "reembolso letra didáctica")
    build_paths = outputs["aportar-sin-retirar"]["salidas_por_recorrido"]
    low, central, high = build_paths
    assert low["saldo_final_nominal_eur"] < low["aportado_total_nominal_eur"]
    assert low["saldo_final_nominal_eur"] < central["saldo_final_nominal_eur"] < high["saldo_final_nominal_eur"]
    drawdown = outputs["retirar-con-caida-temprana"]["salidas_por_recorrido"][0]
    assert_close(drawdown["saldo_final_nominal_eur"], 0.00, "saldo no negativo tras agotar fondos")
    assert drawdown["retiradas_no_cubiertas_nominal_eur"] > 0.0
    assert drawdown["retiradas_pagadas_netas_nominal_eur"] < drawdown["retiradas_solicitadas_nominal_eur"]


def equal_nested(actual: Any, expected: Any, path: str = "salidas") -> None:
    if isinstance(actual, dict) and isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise AssertionError(f"{path}: claves distintas")
        for key in actual:
            equal_nested(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            raise AssertionError(f"{path}: longitudes distintas")
        for i, (left, right) in enumerate(zip(actual, expected)):
            equal_nested(left, right, f"{path}[{i}]")
    elif isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and not isinstance(actual, bool) and not isinstance(expected, bool):
        if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-8):
            raise AssertionError(f"{path}: {actual} != {expected}")
    elif actual != expected:
        raise AssertionError(f"{path}: {actual!r} != {expected!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="JSON de entradas/salidas")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="calcular y escribir la clave salidas")
    group.add_argument("--check", action="store_true", help="comparar cálculo con salidas guardadas")
    args = parser.parse_args()
    document = json.loads(args.data.read_text(encoding="utf-8"))
    outputs = compute_all(document)
    self_test(outputs)
    if args.write:
        document["salidas"] = outputs
        args.data.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Salidas calculadas y guardadas en {args.data}")
    elif args.check:
        equal_nested(outputs, document.get("salidas", {}))
        print(f"OK: {len(outputs)} escenarios, salidas coinciden; invariantes y topes de retiro verificados.")
    else:
        print(json.dumps(outputs, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
