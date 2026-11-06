"""Mide qué campos canónicos documenta cada ficha del catálogo.

Sirve para revisar el catálogo entero de una pasada: qué falta por familia, qué
productos están cojos y si un hueco es de la fuente o de la transcripción.
No inventa nada: solo compara lo que hay con la lista de campos esperables.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from conditions_service import ConditionsService  # noqa: E402

ESPERADOS = {
    "cuenta_remunerada": ["tae", "tin", "liquidacion", "comisiones", "garantia_depositos",
                          "elegibilidad", "disponibilidad", "titularidad", "promocion_ventana_alta",
                          "base_calculo_intereses", "divisa", "importe_maximo"],
    "deposito": ["tae", "tin", "plazo_meses", "importe_minimo", "importe_maximo", "liquidacion",
                 "cancelacion_anticipada", "renovacion", "comisiones", "garantia_depositos",
                 "retencion_fiscal", "titularidad"],
    "letra_deuda_publica": ["isin", "vencimiento", "fecha_subasta", "tipo_marginal", "tipo_medio",
                            "precio_medio", "precio_minimo_aceptado", "nominal_adjudicado",
                            "saldo_vivo", "fecha_liquidacion"],
    "fondo_tradicional": ["isin", "categoria", "gestora", "depositaria", "comision_gestion",
                        "comision_deposito", "comision_entrada", "comision_salida",
                        "cifra_anual_gastos", "importe_minimo", "nav", "patrimonio", "participes",
                        "riesgo", "periodo_mantenimiento_recomendado", "suscripcion_reembolso",
                        "registro_cnmv", "fecha_lanzamiento", "divisa", "reparto", "sfdr"],
    "etf_ucits": ["isin", "ter", "comision_entrada", "comision_salida", "riesgo", "nav", "patrimonio",
            "divisa_base", "replica", "reparto", "ucits", "costes_operacion", "mercado_principal",
            "prestamo_valores", "sfdr"],
}

# Claves de la transcripción que el servicio sirve con otro nombre.
SERVIDA = {
    "tae": "annual_rate_percent", "tin": "nominal_rate_percent", "plazo_meses": "term_months",
    "comisiones": "declared_fees", "garantia_depositos": "deposit_guarantee_fund",
    "elegibilidad": "eligibility", "disponibilidad": "availability", "titularidad": "ownership",
    "promocion_ventana_alta": "promotion_window", "base_calculo_intereses": "interest_basis",
    "divisa": "base_currency", "importe_minimo": "minimum_eur", "importe_maximo": "maximum_eur",
    "liquidacion": "settlement", "cancelacion_anticipada": "early_cancellation",
    "renovacion": "renewal", "retencion_fiscal": "withholding_percent", "isin": "isin",
    "vencimiento": "maturity_date", "fecha_subasta": "auction_date", "tipo_marginal": "marginal_rate_percent",
    "tipo_medio": "average_rate_percent", "precio_medio": "average_price_percent",
    "precio_minimo_aceptado": "minimum_price_percent", "nominal_adjudicado": "awarded_nominal_eur",
    "saldo_vivo": "outstanding_balance", "fecha_liquidacion": "settlement_date",
    "categoria": "category", "gestora": "manager", "depositaria": "depositary",
    "comision_gestion": "management_fee_percent", "comision_deposito": "custody_fee_percent",
    "comision_entrada": "entry_fee_percent", "comision_salida": "exit_fee_percent",
    "cifra_anual_gastos": "annual_cost_figure", "nav": "nav_eur", "patrimonio": "fund_assets_eur",
    "participes": "fund_investors", "riesgo": "risk_scale",
    "periodo_mantenimiento_recomendado": "holding_period_years",
    "suscripcion_reembolso": "subscription_redemption", "registro_cnmv": "cnmv_registry",
    "fecha_lanzamiento": "launch_date", "reparto": "distribution_policy", "sfdr": "sfdr_article",
    "ter": "ter_percent", "divisa_base": "base_currency", "replica": "replication",
    "ucits": "ucits", "costes_operacion": "operating_costs", "mercado_principal": "main_market",
    "prestamo_valores": "securities_lending",
}


def main() -> int:
    servicio = ConditionsService()
    registros = json.loads((APP / "data" / "condiciones.json").read_text(encoding="utf-8"))["records"]
    salida = []
    for registro in registros:
        pid = registro["candidate_id"]
        familia = registro.get("family")
        condiciones = servicio.for_product(pid)["conditions"]
        servidas = {c["metric"] for c in condiciones if c["state"] == "known"}
        esperados = ESPERADOS.get(familia, [])
        faltan = [campo for campo in esperados if SERVIDA.get(campo, campo) not in servidas]
        salida.append({
            "candidate_id": pid,
            "name": registro.get("name"),
            "family": familia,
            "documented": len([c for c in condiciones if c["state"] == "known"]),
            "expected": len(esperados),
            "coverage": round(100 * (len(esperados) - len(faltan)) / max(1, len(esperados))),
            "missing": faltan,
        })
    salida.sort(key=lambda x: (x["coverage"], x["candidate_id"]))
    for fila in salida:
        cubiertos = fila["expected"] - len(fila["missing"])
        print(f"{fila['candidate_id']:12} {fila['coverage']:3}%  {cubiertos:2}/{fila['expected']:2} campos  ({fila['documented']:2} condiciones)  faltan: {', '.join(fila['missing']) or '—'}")
    destino = Path(__file__).resolve().parents[2] / "docs" / "catalogo" / "cobertura-2026-11-06.json"
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\ninforme: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
