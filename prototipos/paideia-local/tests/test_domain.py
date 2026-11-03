import copy
import importlib
import unittest
from decimal import Decimal


def scenario(**updates):
    request = {
        "principal": "1000.00",
        "annual_rate_percent": "12.00",
        "years": 1,
        "monthly_contribution": "100.00",
        "method": "compound",
        "inflation_percent": "0.00",
    }
    request.update(updates)
    return request


class ScenarioCalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.domain = importlib.import_module("domain")

    def test_zero_rate_compound_keeps_end_of_month_contributions_separate(self):
        result = self.domain.calculate_scenario(scenario(
            annual_rate_percent="0.00", inflation_percent="0.00"
        ))
        self.assertEqual(result["summary"], {
            "contributions": "2200.00",
            "final_balance": "2200.00",
            "interest": "0.00",
            "inflation_adjusted": "2200.00",
        })
        self.assertEqual(result["series"][0]["month"], 0)
        self.assertEqual(result["series"][-1]["month"], 12)
        self.assertEqual(result["series"][-1]["contributions"], "2200.00")

    def test_compound_uses_effective_annual_rate_and_end_of_month_deposits(self):
        result = self.domain.calculate_scenario(scenario())
        self.assertEqual(result["summary"]["final_balance"], "2384.65")
        self.assertEqual(result["summary"]["interest"], "184.65")

    def test_simple_interest_uses_remaining_time_for_each_contribution(self):
        result = self.domain.calculate_scenario(scenario(method="simple"))
        self.assertEqual(result["summary"]["final_balance"], "2386.00")
        self.assertEqual(result["summary"]["interest"], "186.00")

    def test_rate_metadata_matches_simple_or_compound_calculation(self):
        simple = self.domain.calculate_scenario(scenario(method="simple"))
        compound = self.domain.calculate_scenario(scenario(method="compound"))
        self.assertEqual(simple["assumptions"]["annual_rate_convention"], "simple_annual_rate")
        self.assertEqual(simple["assumptions"]["monthly_rate_conversion"], "annual_simple_rate_divided_by_12")
        self.assertEqual(compound["assumptions"]["annual_rate_convention"], "effective_annual_rate")
        self.assertEqual(compound["assumptions"]["monthly_rate_conversion"], "effective_monthly_rate")

    def test_inflation_adjustment_uses_effective_annual_deflator(self):
        result = self.domain.calculate_scenario(scenario(
            principal="1000.00", annual_rate_percent="0.00",
            monthly_contribution="0.00", inflation_percent="2.00"
        ))
        self.assertEqual(result["summary"]["final_balance"], "1000.00")
        self.assertEqual(result["summary"]["inflation_adjusted"], "980.39")
        self.assertEqual(result["series"][-1]["real_balance"], "980.39")

    def test_subcent_negative_interest_serializes_as_zero_cents_without_negative_zero(self):
        result = self.domain.calculate_scenario(scenario(
            principal="0.01", annual_rate_percent="-0.01", years=1,
            monthly_contribution="0.00", method="simple", inflation_percent="0.00"
        ))
        self.assertEqual(result["summary"]["interest"], "0.00")

    def test_negative_simple_rate_can_show_a_loss(self):
        result = self.domain.calculate_scenario(scenario(
            principal="1000.00", annual_rate_percent="-10.00", years=2,
            monthly_contribution="0.00", method="simple"
        ))
        self.assertEqual(result["summary"]["final_balance"], "800.00")
        self.assertEqual(result["summary"]["interest"], "-200.00")

    def test_series_has_annual_points_and_final_month_without_mutating_input(self):
        request = scenario(years=40)
        before = copy.deepcopy(request)
        result = self.domain.calculate_scenario(request)
        self.assertEqual(request, before)
        self.assertEqual(len(result["series"]), 41)
        self.assertEqual(result["series"][-1]["month"], 480)
        self.assertEqual(result["series"][-1]["contributions"], "49000.00")
        self.assertTrue(all(isinstance(point["balance"], str) for point in result["series"]))

    def test_maximum_bounds_produce_finite_fixed_point_strings(self):
        result = self.domain.calculate_scenario(scenario(
            principal="1000000000.00", annual_rate_percent="1000.0000",
            years=40, monthly_contribution="1000000000.00", inflation_percent="0.00"
        ))
        balance = result["summary"]["final_balance"]
        self.assertTrue(Decimal(balance).is_finite())
        self.assertRegex(balance, r"-?\d+\.\d{2}")
        for point in result["series"]:
            for key in ("contributions", "balance", "real_balance"):
                self.assertRegex(point[key], r"-?\d+\.\d{2}")

    def test_rejects_invalid_numeric_shapes_and_out_of_range_values(self):
        invalid_requests = [
            scenario(principal=-1),
            scenario(principal="-1.00"),
            scenario(principal="1000000000.01"),
            scenario(principal="1.001"),
            scenario(annual_rate_percent="-100"),
            scenario(annual_rate_percent="1000.01"),
            scenario(annual_rate_percent="1.00001"),
            scenario(inflation_percent="-100"),
            scenario(inflation_percent="Infinity"),
            scenario(monthly_contribution="NaN"),
            scenario(years=True),
            scenario(years=0),
            scenario(years=41),
            scenario(method="unknown"),
            scenario(method=[]),
            scenario(extra_field="not allowed"),
        ]
        for request in invalid_requests:
            with self.subTest(request=request):
                with self.assertRaises(ValueError):
                    self.domain.calculate_scenario(request)

    def test_result_is_hypothetical_and_excludes_tax_and_fee_assumptions(self):
        result = self.domain.calculate_scenario(scenario())
        self.assertTrue(result["hypothetical"])
        self.assertTrue(result["not_prediction"])
        self.assertFalse(result["assumptions"]["taxes_included"])
        self.assertFalse(result["assumptions"]["fees_included"])
        self.assertEqual(result["assumptions"]["monthly_contribution_timing"], "end_of_month")
        self.assertEqual(result["assumptions"]["working_precision"], "80_significant_decimal_digits")
        self.assertIn("no_cent_rounding_per_month", result["assumptions"]["rounding"])


if __name__ == "__main__":
    unittest.main()
