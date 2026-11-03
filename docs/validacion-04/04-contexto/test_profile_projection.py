import copy
import unittest

import profile_projection
from profile_projection import ConsentError, project_profile


class ProfileProjectionTests(unittest.TestCase):
    def test_rejects_projection_without_chat_processing_consent(self):
        profile = {
            "respuestas": {
                "objetivo": {"estado": "declarado", "valor": "colchon_imprevistos"}
            }
        }
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": False,
            "purpose": "learn_basics",
            "approved_fields": ["objective"],
        }

        with self.assertRaises(ConsentError):
            project_profile(
                profile,
                purpose="learn_basics",
                selected_fields=["objective"],
                consent=consent,
            )

    def test_projects_risk_tolerance_separately_from_loss_capacity(self):
        profile = {
            "riesgo": {
                "tolerancia": {
                    "estado": "declarado",
                    "valor": "podria_esperar_aceptando_caidas",
                },
                "capacidad_perdidas": {
                    "estado": "declarado",
                    "valor": {
                        "escenario_id": "caida_100_de_1000",
                        "impacto": "afectaria_gasto_esencial_o_compromiso",
                    },
                },
            }
        }
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "risk_education",
            "approved_fields": ["risk_tolerance", "loss_capacity"],
        }

        result = project_profile(
            profile,
            purpose="risk_education",
            selected_fields=["risk_tolerance", "loss_capacity"],
            consent=consent,
        )

        self.assertEqual(
            result["fields"],
            {
                "risk_tolerance": {"state": "known", "value": "can_wait_with_drops"},
                "loss_capacity": {
                    "state": "known",
                    "value": {
                        "scenario": "drop_100_of_1000",
                        "impact": "would_affect_essential_spending_or_commitment",
                    },
                },
            },
        )

    def test_projects_selected_learning_preferences(self):
        profile = {
            "respuestas": {
                "experiencia": {
                    "estado": "declarado",
                    "valor": {"nivel": "empezando", "temas_interes": ["etf", "fondos"]},
                }
            }
        }
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "learn_basics",
            "approved_fields": ["learning_level", "learning_topics"],
        }

        result = project_profile(
            profile,
            purpose="learn_basics",
            selected_fields=["learning_level", "learning_topics"],
            consent=consent,
        )

        self.assertEqual(
            result["fields"],
            {
                "learning_level": {"state": "known", "value": "beginner"},
                "learning_topics": {"state": "known", "value": ["etf", "mutual_funds"]},
            },
        )

    def test_maps_income_and_liquid_reserve_only_when_selected(self):
        from decimal import Decimal

        income_range = {"min_eur": Decimal("2500.00"), "max_eur": Decimal("2500.00"), "moneda": "EUR"}
        reserve_range = {"min_eur": Decimal("8000.00"), "max_eur": Decimal("8000.00"), "moneda": "EUR"}
        profile = {
            "detalle_economico": {
                "ingresos_netos": {
                    "estado": "declarado",
                    "valor": {"importe": income_range, "periodicidad": "mensual"},
                },
                "colchon_liquido": {"estado": "declarado", "valor": reserve_range},
            }
        }
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "debt_education",
            "approved_fields": ["monthly_income_eur", "liquid_reserve_eur"],
        }

        result = project_profile(
            profile,
            purpose="debt_education",
            selected_fields=["monthly_income_eur", "liquid_reserve_eur"],
            consent=consent,
        )

        self.assertEqual(
            result["fields"],
            {
                "monthly_income_eur": {
                    "state": "known",
                    "value": {
                        "amount": {"min_eur": "2500.00", "max_eur": "2500.00", "currency": "EUR"},
                        "periodicity": "monthly",
                    },
                },
                "liquid_reserve_eur": {
                    "state": "known",
                    "value": {"min_eur": "8000.00", "max_eur": "8000.00", "currency": "EUR"},
                },
            },
        )

    def test_maps_upcoming_commitment_and_explicit_absence(self):
        from decimal import Decimal

        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "liquidity_planning",
            "approved_fields": ["upcoming_commitments"],
        }
        commitment = {
            "estado": "declarado",
            "valor": {
                "hay_compromiso": True,
                "total_eur": {
                    "min_eur": Decimal("400.00"),
                    "max_eur": Decimal("400.00"),
                    "moneda": "EUR",
                },
                "plazo": "menos_3_meses",
            },
        }
        no_commitment = {"estado": "declarado", "valor": {"hay_compromiso": False}}

        def project(answer):
            return project_profile(
                {"detalle_economico": {"compromisos_proximos": answer}},
                purpose="liquidity_planning",
                selected_fields=["upcoming_commitments"],
                consent=consent,
            )["fields"]["upcoming_commitments"]

        self.assertEqual(
            project(commitment),
            {
                "state": "known",
                "value": {
                    "has_commitment": True,
                    "total_eur": {
                        "min_eur": "400.00",
                        "max_eur": "400.00",
                        "currency": "EUR",
                    },
                    "due_within": "under_3_months",
                },
            },
        )
        self.assertEqual(project(no_commitment), {"state": "known", "value": {"has_commitment": False}})

    def test_maps_liquidity_need_without_inference(self):
        profile = {"respuestas": {"liquidez": {"estado": "declarado", "valor": "acceso_cualquier_momento"}}}
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "liquidity_planning",
            "approved_fields": ["liquidity_need"],
        }

        result = project_profile(
            profile,
            purpose="liquidity_planning",
            selected_fields=["liquidity_need"],
            consent=consent,
        )

        self.assertEqual(result["fields"]["liquidity_need"], {"state": "known", "value": "anytime_access"})

    def test_maps_monthly_expenses_as_decimal_flow(self):
        from decimal import Decimal

        profile = {
            "detalle_economico": {
                "gastos_esenciales": {
                    "estado": "declarado",
                    "valor": {
                        "importe": {
                            "min_eur": Decimal("1200.10"),
                            "max_eur": Decimal("1350.20"),
                            "moneda": "EUR",
                        },
                        "periodicidad": "mensual",
                    },
                }
            }
        }
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "liquidity_planning",
            "approved_fields": ["monthly_expenses_eur"],
        }

        result = project_profile(
            profile,
            purpose="liquidity_planning",
            selected_fields=["monthly_expenses_eur"],
            consent=consent,
        )

        self.assertEqual(
            result["fields"]["monthly_expenses_eur"],
            {
                "state": "known",
                "value": {
                    "amount": {"min_eur": "1200.10", "max_eur": "1350.20", "currency": "EUR"},
                    "periodicity": "monthly",
                },
            },
        )

    def test_preserves_horizon_answer_state(self):
        cases = (
            ({"estado": "declarado", "valor": "6_12_meses"}, {"state": "known", "value": "6_to_12_months"}),
            ({"estado": "no_se"}, {"state": "unknown"}),
            ({"estado": "omitido"}, {"state": "omitted"}),
            ({"estado": "sin_preguntar"}, {"state": "not_asked"}),
        )
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "liquidity_planning",
            "approved_fields": ["horizon"],
        }

        for local_answer, expected in cases:
            with self.subTest(state=local_answer["estado"]):
                result = project_profile(
                    {"respuestas": {"horizonte": local_answer}},
                    purpose="liquidity_planning",
                    selected_fields=["horizon"],
                    consent=consent,
                )
                self.assertEqual(result["fields"]["horizon"], expected)

    def test_preserves_selected_financial_decimal_exactly(self):
        from decimal import Decimal

        profile = {
            "detalle_economico": {
                "importe_objetivo": {
                    "estado": "declarado",
                    "valor": {
                        "min_eur": Decimal("123456789.0040"),
                        "max_eur": Decimal("123456789.0040"),
                        "moneda": "EUR",
                    },
                }
            }
        }
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "liquidity_planning",
            "approved_fields": ["target_amount_eur"],
        }

        result = project_profile(
            profile,
            purpose="liquidity_planning",
            selected_fields=["target_amount_eur"],
            consent=consent,
        )

        self.assertEqual(
            result["fields"]["target_amount_eur"],
            {
                "state": "known",
                "value": {
                    "min_eur": "123456789.0040",
                    "max_eur": "123456789.0040",
                    "currency": "EUR",
                },
            },
        )

    def test_debt_zero_and_unknown_remain_distinct_from_no_debt(self):
        from decimal import Decimal

        zero_range = {"min_eur": Decimal("0"), "max_eur": Decimal("0"), "moneda": "EUR"}
        known_zero_profile = {
            "detalle_economico": {
                "deuda": {
                    "estado": "declarado",
                    "valor": {
                        "situacion": "con_deuda",
                        "saldo_eur": {"estado": "declarado", "valor": zero_range},
                        "cuota": {
                            "estado": "declarado",
                            "valor": {"importe": zero_range, "periodicidad": "mensual"},
                        },
                        "coste_anual_pct": {
                            "estado": "declarado",
                            "valor": {"min_pct": Decimal("0"), "max_pct": Decimal("0")},
                        },
                    },
                }
            }
        }
        unknown_profile = {"detalle_economico": {"deuda": {"estado": "no_se"}}}

        def project_debt(profile):
            return project_profile(
                profile,
                purpose="debt_education",
                selected_fields=["debt"],
                consent={
                    "notice_version": "test-1",
                    "accepted_chat_processing": True,
                    "purpose": "debt_education",
                    "approved_fields": ["debt"],
                },
            )["fields"]["debt"]

        self.assertEqual(
            project_debt(known_zero_profile),
            {
                "state": "known",
                "value": {
                    "situation": "has_debt",
                    "balance_eur": {
                        "state": "known",
                        "value": {"min_eur": "0", "max_eur": "0", "currency": "EUR"},
                    },
                    "monthly_payment_eur": {
                        "state": "known",
                        "value": {
                            "amount": {"min_eur": "0", "max_eur": "0", "currency": "EUR"},
                            "periodicity": "monthly",
                        },
                    },
                    "annual_cost_percent": {
                        "state": "known",
                        "value": {"min_percent": "0", "max_percent": "0"},
                    },
                },
            },
        )
        self.assertEqual(project_debt(unknown_profile), {"state": "unknown"})

    def test_maps_declared_no_debt_without_conflating_zero(self):
        profile = {
            "detalle_economico": {
                "deuda": {"estado": "declarado", "valor": {"situacion": "sin_deuda"}}
            }
        }
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "debt_education",
            "approved_fields": ["debt"],
        }

        result = project_profile(
            profile,
            purpose="debt_education",
            selected_fields=["debt"],
            consent=consent,
        )

        self.assertEqual(
            result["fields"]["debt"],
            {"state": "known", "value": {"situation": "no_debt"}},
        )

    def test_full_benchmark_projection_is_tagged_and_uses_only_synthetic_fixture(self):
        not_asked = {"estado": "sin_preguntar"}
        profile = {
            "version_esquema": "1.0.0",
            "tipo": "mapa_educativo",
            "respuestas": {
                "objetivo": not_asked,
                "horizonte": not_asked,
                "liquidez": not_asked,
                "experiencia": not_asked,
            },
            "detalle_economico": {
                "importe_objetivo": not_asked,
                "ingresos_netos": not_asked,
                "gastos_esenciales": not_asked,
                "deuda": not_asked,
                "colchon_liquido": not_asked,
                "compromisos_proximos": not_asked,
            },
            "riesgo": {"tolerancia": not_asked, "capacidad_perdidas": not_asked},
            "supuestos_escenario": [],
        }
        fixture = {
            "classification": "synthetic_fixture",
            "fixture_id": "synthetic-full-profile-01",
            "profile": profile,
        }

        full_projector = getattr(profile_projection, "project_synthetic_full_for_benchmark")
        result = full_projector(fixture)

        self.assertEqual(result["classification"], "synthetic_benchmark_only")
        self.assertEqual(result["purpose"], "complete_synthetic_benchmark")
        self.assertEqual(
            set(result["fields"]),
            {
                "objective", "horizon", "liquidity_need", "learning_level", "learning_topics",
                "target_amount_eur", "monthly_income_eur", "monthly_expenses_eur", "debt",
                "liquid_reserve_eur", "upcoming_commitments", "risk_tolerance", "loss_capacity",
            },
        )
        self.assertTrue(all(value == {"state": "not_asked"} for value in result["fields"].values()))
        self.assertNotIn("supuestos_escenario", result["fields"])

    def test_rejects_a_field_withdrawn_after_consent(self):
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "learn_basics",
            "approved_fields": [],
        }

        with self.assertRaises(ConsentError):
            project_profile(
                {},
                purpose="learn_basics",
                selected_fields=["objective"],
                consent=consent,
            )

    def test_rejects_profile_full_boolean_on_production_projector(self):
        with self.assertRaises(TypeError):
            project_profile(
                {},
                purpose="learn_basics",
                selected_fields=["objective"],
                consent={
                    "notice_version": "test-1",
                    "accepted_chat_processing": True,
                    "purpose": "learn_basics",
                    "approved_fields": ["objective"],
                },
                full=True,
            )

    def test_full_projection_rejects_non_synthetic_input(self):
        with self.assertRaises(profile_projection.ProjectionError):
            profile_projection.project_synthetic_full_for_benchmark(
                {
                    "classification": "production_profile",
                    "fixture_id": "synthetic-full-profile-01",
                    "profile": {},
                }
            )
        with self.assertRaises(profile_projection.ProjectionError):
            profile_projection.project_synthetic_full_for_benchmark(
                {
                    "classification": "synthetic_fixture",
                    "fixture_id": "unregistered-fixture",
                    "profile": {},
                }
            )

    def test_emits_only_selected_field_for_its_purpose(self):
        profile = {
            "respuestas": {
                "objetivo": {"estado": "declarado", "valor": "colchon_imprevistos"},
                "experiencia": {
                    "estado": "declarado",
                    "valor": {"nivel": "empezando", "temas_interes": ["etf"]},
                },
            },
            "detalle_economico": {
                "ingresos_netos": {"estado": "declarado", "valor": {"unused": "private"}}
            },
        }
        profile_before = copy.deepcopy(profile)
        consent = {
            "notice_version": "test-1",
            "accepted_chat_processing": True,
            "purpose": "learn_basics",
            "approved_fields": ["objective"],
        }

        result = project_profile(
            profile,
            purpose="learn_basics",
            selected_fields=["objective"],
            consent=consent,
        )

        self.assertEqual(
            result,
            {
                "contract_version": "0.1",
                "purpose": "learn_basics",
                "fields": {"objective": {"state": "known", "value": "emergency_reserve"}},
            },
        )
        self.assertNotIn("detalle_economico", result)
        self.assertEqual(profile, profile_before)


if __name__ == "__main__":
    unittest.main()
