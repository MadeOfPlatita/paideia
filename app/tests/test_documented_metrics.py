"""La ficha de fondos y ETF muestra lo que la fuente publica, y solo eso.

Antes, estas familias solo llevaban tasa y plazo —que no tienen— así que la
ficha salía vacía aunque la transcripción trajera TER, ISIN, comisiones o SRI.
Ahora se emiten esas métricas con su fuente; lo que la fuente no publica sigue
sin fila y la lista de desconocidos lo dice.
"""

import unittest
from datetime import date

from conditions_service import ConditionsService


def conditions_for(product_id):
    report = ConditionsService().describe(today=date(2026, 11, 5))
    product = next(p for p in report["products"] if p["product_id"] == product_id)
    return {c["metric"]: c for c in product["conditions"]}


class DocumentedMetricsTests(unittest.TestCase):
    def test_etf_shows_its_documented_figures(self):
        etf = conditions_for("ETF-01")
        self.assertEqual(etf["ter_percent"]["value"], "0.12")
        self.assertEqual(etf["isin"]["value"], "IE00B4K48X80")
        self.assertEqual(etf["risk_scale"]["value"], "4/7")
        self.assertIn("entry_fee_percent", etf)
        self.assertIn("base_currency", etf)

    def test_fund_shows_fees_and_minimum(self):
        fondo = conditions_for("FND-01")
        self.assertEqual(fondo["management_fee_percent"]["value"], "1.75")
        self.assertEqual(fondo["minimum_eur"]["value"], "100")
        self.assertIn("nav_eur", fondo)

    def test_deposit_keeps_rate_and_adds_limits(self):
        deposito = conditions_for("DEP-01")
        self.assertEqual(deposito["annual_rate_percent"]["value"], "3.24")
        self.assertEqual(deposito["minimum_eur"]["value"], "500")
        self.assertEqual(deposito["maximum_eur"]["value"], "1000000")

    def test_every_emitted_metric_carries_a_source(self):
        for product_id in ("ETF-01", "FND-01", "DEP-01"):
            for metric, condition in conditions_for(product_id).items():
                with self.subTest(product=product_id, metric=metric):
                    if metric in {"annual_rate_percent", "term_months"}:
                        continue
                    self.assertTrue(condition["source_ids"], metric)
                    self.assertIn("https://", condition["source_ids"][0])

    def test_a_value_the_source_does_not_publish_gets_no_row(self):
        # ACC-01 dice que no hay saldo máximo, pero no da cifra: no se emite.
        cuenta = conditions_for("ACC-01")
        self.assertNotIn("maximum_eur", cuenta)

    def test_raw_transcription_labels_do_not_leak_as_metrics(self):
        etf = conditions_for("ETF-01")
        self.assertNotIn("promocion_ventana_alta", etf)
        self.assertNotIn("periodo_mantenimiento_recomendado", etf)
        self.assertIn("holding_period_years", etf)


if __name__ == "__main__":
    unittest.main()
