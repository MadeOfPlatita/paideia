"""Verificación independiente del motor; solo biblioteca estándar."""
import json
import unittest
from decimal import Decimal
from pathlib import Path

import motor_financiero as mf


FIXTURES = json.loads((Path(__file__).with_name("fixtures.json")).read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in FIXTURES["reference_cases"]}


def d(value):
    return Decimal(str(value))


class TestCasosReferencia(unittest.TestCase):
    def test_interes_simple_act360(self):
        case = CASES["interes_simple_act360"]
        self.assertEqual(mf.simple_interest(**case["input"]), d(case["expected_interest"]))

    def test_compuesto_nominal_mensual(self):
        case = CASES["compuesto_nominal_mensual_12_periodos"]
        self.assertEqual(mf.compound_amount(**case["input"]), d(case["expected_amount"]))

    def test_tae_matematica_desde_tin(self):
        case = CASES["tae_matematica_tin_12_mensual"]
        self.assertEqual(mf.effective_annual_rate(**case["input"]), d(case["expected_effective_annual_rate"]))

    def test_cuenta_tramos_promo_y_limites(self):
        case = CASES["cuenta_tramos_promo_y_limites"]
        result = mf.tiered_account_result(**case["input"])
        self.assertEqual(result["gross_interest"], d(case["expected_gross_interest"]))
        self.assertEqual(result["fees"], d(case["expected_fees"]))
        self.assertEqual(result["ending_value"], d(case["expected_ending_value"]))

    def test_deposito_al_vencimiento(self):
        case = CASES["deposito_vencimiento_sintetico"]
        self.assertEqual(mf.deposit_maturity(**case["input"]), d(case["expected_ending_value"]))

    def test_cancelacion_deposito_aplica_perdida_y_comision_explicitas(self):
        case = CASES["deposito_cancelacion_sintetica"]
        self.assertEqual(mf.deposit_cancellation(**case["input"]), d(case["expected_payout"]))

    def test_letra_distingue_rentabilidad_periodo_y_anualizada_act360(self):
        case = CASES["letra_act360_sintetica"]
        result = mf.bill_return(**case["input"])
        self.assertEqual(result["days"], case["expected_days"])
        self.assertEqual(result["holding_period_return"], d(case["expected_holding_period_return"]))
        self.assertEqual(result["annualized_simple_act360"], d(case["expected_annualized_simple_act360"]))

    def test_bono_cupon_y_tir_separados(self):
        case = CASES["bono_par_cupon_semestral_sintetico"]
        args = case["input"]
        flows = mf.bond_cashflows(args["face_value"], args["annual_coupon_rate"], args["payments_per_year"], args["periods"])
        self.assertEqual(flows, [d(x) for x in case["expected_cashflows"]])
        ytm = mf.bond_yield(**args)
        self.assertLess(abs(ytm["nominal_annual_yield"] - d(case["expected_nominal_annual_yield"])), d("1e-25"))
        self.assertLess(abs(ytm["effective_annual_yield"] - d(case["expected_effective_annual_yield"])), d("1e-25"))

    def test_fondo_valora_por_nav_y_comision_explicita(self):
        case = CASES["fondo_valor_liquidativo_sintetico"]
        self.assertEqual(mf.fund_redemption_value(**case["input"]), d(case["expected_net_redemption"]))

    def test_etf_usa_cotizaciones_y_costes_de_negociacion(self):
        case = CASES["etf_compra_venta_sinteticos"]
        args = case["input"]
        buy = mf.etf_trade_cashflow(args["units"], args["ask_price"], "buy", args["buy_commission"])
        sell = mf.etf_trade_cashflow(args["units"], args["bid_price"], "sell", args["sell_commission"])
        self.assertEqual(buy, d(case["expected_buy_outflow"]))
        self.assertEqual(sell, d(case["expected_sell_proceeds"]))
        self.assertEqual(buy - sell, d(case["expected_round_trip_cost_at_unchanged_quotes"]))

    def test_coste_recurrente_estimado(self):
        case = CASES["coste_recurrente_estimado_sintetico"]
        self.assertEqual(mf.ongoing_cost(**case["input"]), d(case["expected_cost"]))

    def test_aportaciones_fin_de_mes(self):
        case = CASES["aportaciones_fin_mes_dos_meses"]
        self.assertEqual(mf.future_value_contributions(**case["input"]), d(case["expected_amount"]))

    def test_aportaciones_inicio_de_mes(self):
        case = CASES["aportaciones_inicio_mes_dos_meses"]
        self.assertEqual(mf.future_value_contributions(**case["input"]), d(case["expected_amount"]))

    def test_ajuste_por_inflacion(self):
        case = CASES["valor_real_inflacion_un_ano"]
        self.assertEqual(mf.inflation_adjusted_value(**case["input"]), d(case["expected_real_value"]))


class TestLimitesYValidacion(unittest.TestCase):
    def test_ceros_validos_y_redondeo_half_up(self):
        zero = FIXTURES["boundary_cases"]["zero"]
        self.assertEqual(mf.simple_interest("0", "0.05", 365), d(zero["simple_interest_zero_principal"]))
        self.assertEqual(mf.compound_amount("1000", "0", 12, 12), d(zero["compound_zero_rate"]))
        self.assertEqual(mf.future_value_contributions("100", "0.01", 0, "end"), d(zero["contributions_zero_periods"]))
        self.assertEqual(mf.round_money(FIXTURES["boundary_cases"]["money_rounding"]["input"]), d("2.35"))

    def test_tipos_negativos_admitidos_solo_con_factor_valido(self):
        self.assertEqual(mf.simple_interest("1000", "-0.05", 365), d("-50"))
        self.assertEqual(mf.compound_amount("1000", "-0.12", 12, 12), d("886.384871716129280658801000"))
        with self.assertRaises(ValueError):
            mf.compound_amount("1000", "-12", 12, 1)

    def test_rechaza_importes_principales_negativos(self):
        with self.assertRaises(ValueError):
            mf.simple_interest("-1", "0.05", 365)

    def test_rechaza_nan_e_infinito(self):
        for token in FIXTURES["boundary_cases"]["non_finite_rejected"]:
            with self.subTest(token=token):
                with self.assertRaises(ValueError):
                    mf.simple_interest(token, "0.05", 365)

    def test_rechaza_dias_negativos_y_tasa_compuesta_inviable(self):
        with self.assertRaises(ValueError):
            mf.simple_interest("100", "0.05", -1)
        with self.assertRaises(ValueError):
            mf.effective_annual_rate("-12", 12)

    def test_comision_negativa_rechazada(self):
        with self.assertRaises(ValueError):
            mf.etf_trade_cashflow("1", "10", "buy", "-0.01")

    def test_fechas_invalidas_o_intervalo_invertido_rechazados(self):
        with self.assertRaises(ValueError):
            mf.deposit_maturity("100", "0.03", "2025-02-30", "2025-03-01")
        with self.assertRaises(ValueError):
            mf.deposit_maturity("100", "0.03", "2025-03-02", "2025-03-01")

    def test_fecha_act_actual_incluye_bisiesto_y_fin_es_exclusivo(self):
        result = mf.bill_return("100", "101", "2024-02-28", "2024-03-01")
        self.assertEqual(result["days"], 2)

    def test_anualizacion_letra_rechaza_plazo_cero(self):
        with self.assertRaises(ValueError):
            mf.bill_return("100", "101", "2025-01-01", "2025-01-01")

    def test_cuenta_rechaza_tramos_desordenados_y_hueco_de_fechas(self):
        bad_tiers = [{"up_to": "1000", "annual_rate": "0.01"}, {"up_to": "900", "annual_rate": "0.02"}]
        with self.assertRaises(ValueError):
            mf.tiered_account_result("1000", [{"start_date": "2025-01-01", "end_date": "2025-02-01", "tiers": bad_tiers}], 365)
        schedule = [
            {"start_date": "2025-01-01", "end_date": "2025-02-01", "tiers": [{"up_to": None, "annual_rate": "0.01"}]},
            {"start_date": "2025-02-02", "end_date": "2025-03-01", "tiers": [{"up_to": None, "annual_rate": "0.01"}]}
        ]
        with self.assertRaises(ValueError):
            mf.tiered_account_result("1000", schedule, 365)

    def test_limite_sin_tramo_final_deja_exceso_sin_remunerar(self):
        schedule = [{"start_date": "2025-01-01", "end_date": "2025-01-31", "tiers": [{"up_to": "1000", "annual_rate": "0.12"}]}]
        self.assertEqual(mf.tiered_account_result("2000", schedule, 360)["gross_interest"], d("10"))

    def test_cancelacion_no_permite_perdonar_intereses_inexistentes(self):
        with self.assertRaises(ValueError):
            mf.deposit_cancellation("1000", "10", "11")

    def test_fondo_y_venta_etf_no_permiten_costes_mayores_que_el_valor(self):
        with self.assertRaises(ValueError):
            mf.fund_redemption_value("1", "10", "10.01")
        with self.assertRaises(ValueError):
            mf.etf_trade_cashflow("1", "10", "sell", "10.01")

    def test_redondeo_decimal_half_up(self):
        self.assertEqual(mf.round_money("1.005"), d("1.01"))

    def test_fecha_bisiesta_tasa_simple_y_casos_de_cero(self):
        self.assertEqual(mf.simple_interest("1000", "0.36", 2, 360), d("2"))
        self.assertEqual(mf.simple_interest("1000", "0.05", 0, 365), d("0"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
