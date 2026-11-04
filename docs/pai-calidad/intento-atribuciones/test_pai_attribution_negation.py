"""Pai: una negación no es una atribución.

La frontera de superficie retenía cualquier prosa que nombrara «oficial»,
«vigente» o «confirmar», incluso cuando el texto negaba justo eso. La
evaluación de diez preguntas lo dejó a la vista: una respuesta correcta a
«¿es fiable una fuente secundaria?» dice «una fuente secundaria no es
oficial», y era retenida por la misma palabra que la hace correcta.

Contrato que fijan estas pruebas:

- una atribución negada (no / nunca / jamás / tampoco / sin / ni) no se
  presenta como hecho y se deja pasar;
- una atribución afirmada se sigue reteniendo, aunque el texto incluya
  además una negación;
- las negaciones dobles («no solo es oficial») cuentan como afirmación;
- las cifras y los identificadores se siguen reteniendo sin cambios.

Son casos sintéticos: no hay red, ni proveedor, ni datos personales.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))

from backend_services import (  # noqa: E402
    ANSWER_TEXT_WITHHELD_UNBACKED,
    _text_surface_gate,
    _withhold_unbacked_claim,
)
from pai_runtime import ANSWER_TEXT_SHOWN  # noqa: E402


class NegatedAttributionTests(unittest.TestCase):
    def assert_allowed(self, text):
        allowed, reason = _text_surface_gate(text)
        self.assertTrue(allowed, f"se retuvo una negación: {reason} · {text!r}")
        self.assertEqual(reason, "concept_only")

    def assert_blocked(self, text, expected_reason):
        allowed, reason = _text_surface_gate(text)
        self.assertFalse(allowed, f"pasó una afirmación: {text!r}")
        self.assertEqual(reason, expected_reason, text)

    def test_secondary_source_is_not_official(self):
        self.assert_allowed(
            "Una fuente secundaria no es oficial: contrasta siempre la ficha del producto.")

    def test_expired_data_is_no_longer_current(self):
        self.assert_allowed(
            "Ese dato ya no está vigente: conviene comprobar la fecha de consulta.")

    def test_refusal_to_confirm_is_not_a_confirmation(self):
        self.assert_allowed(
            "No puedo confirmar que la entidad publique esa condición.")

    def test_without_official_source_is_allowed(self):
        self.assert_allowed(
            "Sin fuente oficial a mano, lo prudente es no dar la cifra por buena.")

    def test_neither_official_nor_current(self):
        self.assert_allowed(
            "Ni oficial ni vigente: esa ficha solo describe el producto hace meses.")

    def test_asserted_attribution_is_still_blocked(self):
        self.assert_blocked(
            "Según la fuente oficial, la TAE es la publicada en la ficha.", "attribution")

    def test_assertion_wins_over_a_negation_in_the_same_text(self):
        self.assert_blocked(
            "El banco confirma que la ficha no es oficial.", "attribution")

    def test_trailing_positive_publication_is_still_blocked(self):
        self.assert_blocked(
            "No es oficial, pero el folleto lo publica.", "attribution")

    def test_double_negative_counts_as_assertion(self):
        self.assert_blocked(
            "No solo es oficial, sino que además está vigente.", "attribution")

    def test_sin_duda_is_an_assertion_despite_the_negative_particle(self):
        self.assert_blocked("Sin duda es oficial.", "attribution")

    def test_no_cabe_duda_is_an_assertion(self):
        self.assert_blocked("No cabe duda de que está vigente.", "attribution")

    def test_no_deja_de_ser_is_an_assertion(self):
        self.assert_blocked("No deja de ser oficial.", "attribution")

    def test_negation_does_not_reach_a_later_comma_clause(self):
        self.assert_blocked("No es oficial, es publicado por el banco.", "attribution")

    # Ciclo de corrección 1: fugas encontradas por la revisión independiente.
    def test_no_obstante_is_a_connector_not_a_negation(self):
        self.assert_blocked("No obstante el folleto lo publica.", "attribution")

    def test_sin_embargo_is_a_connector_not_a_negation(self):
        self.assert_blocked("Sin embargo el folleto lo publica.", "attribution")

    def test_a_prepositional_attribution_is_never_negated_by_a_previous_no(self):
        self.assert_blocked("No es un banco según la entidad.", "attribution")

    def test_no_dudo_is_an_assertion(self):
        self.assert_blocked("No dudo que el folleto lo publica.", "attribution")

    def test_no_es_menos_cierto_is_an_assertion(self):
        self.assert_blocked("No es menos cierto que el folleto lo publica.", "attribution")

    def test_no_hay_quien_dude_is_an_assertion(self):
        self.assert_blocked("No hay quien dude que el banco lo confirma.", "attribution")

    def test_a_document_can_be_the_subject_of_a_negation(self):
        self.assert_allowed("El folleto no lo recoge.")

    def test_a_document_can_deny_knowing_vigency(self):
        self.assert_allowed("El folleto no aclara si sigue vigente.")

    def test_sin_duda_can_also_negate_the_predicate(self):
        self.assert_allowed("Sin duda no está vigente.")

    def test_no_cabe_duda_can_also_negate_the_predicate(self):
        self.assert_allowed("No cabe duda de que no es oficial.")

    def test_figures_are_still_blocked(self):
        self.assert_blocked("Un depósito al 3 % anual, sin comisiones.", "figure")

    def test_identifiers_are_still_blocked(self):
        self.assert_blocked("Mira ACC-01 antes de decidir.", "identifier")

    def test_plain_concept_is_still_allowed(self):
        self.assert_allowed(
            "Distingue entre el tipo nominal y la tasa anual equivalente.")


class EndToEndTests(unittest.TestCase):
    """El mismo texto, a través de la función que decide qué ve el usuario."""

    @staticmethod
    def result():
        return {"answer_text_state": ANSWER_TEXT_SHOWN, "limitations": [],
                "catalogue": {"used": False, "products": []}}

    def test_negated_attribution_reaches_the_user(self):
        text = "Una fuente secundaria no es oficial: contrasta la ficha del producto."
        shown, state, result = _withhold_unbacked_claim(self.result(), text, ANSWER_TEXT_SHOWN)
        self.assertEqual(state, ANSWER_TEXT_SHOWN)
        self.assertEqual(shown, text)
        self.assertNotIn("withheld_reason", result)

    def test_asserted_attribution_is_still_withheld(self):
        text = "Según la fuente oficial, la TAE es la publicada en la ficha."
        shown, state, result = _withhold_unbacked_claim(self.result(), text, ANSWER_TEXT_SHOWN)
        self.assertEqual(shown, "")
        self.assertEqual(state, ANSWER_TEXT_WITHHELD_UNBACKED)
        self.assertEqual(result["withheld_reason"], "attribution")

    def test_negated_attribution_with_a_figure_is_still_withheld(self):
        text = "No es oficial, pero el 3 % sigue anunciado."
        shown, state, result = _withhold_unbacked_claim(self.result(), text, ANSWER_TEXT_SHOWN)
        self.assertEqual(shown, "")
        self.assertEqual(state, ANSWER_TEXT_WITHHELD_UNBACKED)
        self.assertEqual(result["withheld_reason"], "figure")


if __name__ == "__main__":
    unittest.main()
