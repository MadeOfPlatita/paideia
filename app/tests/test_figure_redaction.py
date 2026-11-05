"""La prosa con un ejemplo numérico ya no se tira entera.

La frontera sigue siendo de superficie: no valida cifras. Lo que cambia es qué
se hace cuando una frase lleva un número sin respaldo local. Antes se ocultaba
la respuesta completa; ahora se quitan esas frases, se conserva el resto y se
declara cuántas se han quitado. Si no queda nada sustancial, se oculta todo.
"""

import unittest

import backend_services as bs
from pai_runtime import ANSWER_TEXT_SHOWN

CONCEPTO = ("El TIN es el tipo de interés nominal que aplica una entidad a un producto. "
            "No incluye comisiones ni el efecto de la capitalización. "
            "La TAE sí incorpora ambos, por eso suele ser más alta.")
EJEMPLO = "Por ejemplo, un 3 % anual sobre 1.000 euros."


class RedactionTests(unittest.TestCase):
    def run_gate(self, text):
        return bs._withhold_unbacked_claim({}, text, ANSWER_TEXT_SHOWN, None)

    def test_keeps_the_explanation_and_drops_only_the_figure_sentence(self):
        texto, estado, resultado = self.run_gate(CONCEPTO + " " + EJEMPLO)
        self.assertEqual(estado, ANSWER_TEXT_SHOWN)
        self.assertNotIn("3 %", texto)
        self.assertNotIn("1.000 euros", texto)
        self.assertIn("El TIN es el tipo de interés nominal", texto)
        self.assertIn("La TAE sí incorpora ambos", texto)
        self.assertEqual(resultado["redacted_figures"], 1)
        self.assertTrue(any("cifras" in nota for nota in resultado["limitations"]))

    def test_a_fully_numeric_answer_is_still_withheld(self):
        texto, estado, resultado = self.run_gate(EJEMPLO + " " + EJEMPLO)
        self.assertEqual(texto, "")
        self.assertNotEqual(estado, ANSWER_TEXT_SHOWN)
        self.assertEqual(resultado["withheld_reason"], "figure")

    def test_attribution_is_never_redacted_away(self):
        texto, estado, resultado = self.run_gate("Según la fuente oficial, el depósito paga bien.")
        self.assertEqual(texto, "")
        self.assertEqual(resultado["withheld_reason"], "attribution")

    def test_a_calculator_turn_redacts_only_the_figure_sentences(self):
        # Antes se tiraba la respuesta entera en un turno con calculadora; ahora se
        # quitan las frases con cifras y la explicación conceptual se conserva.
        texto, estado, resultado = bs._withhold_unbacked_claim(
            {}, CONCEPTO + " " + EJEMPLO, ANSWER_TEXT_SHOWN, calculation={"ok": True})
        self.assertEqual(estado, ANSWER_TEXT_SHOWN)
        self.assertIn("El TIN es el tipo de interés nominal", texto)
        self.assertNotIn("3 %", texto)
        self.assertNotIn("1.000 euros", texto)
        self.assertEqual(resultado["redacted_figures"], 1)
        self.assertTrue(any("calculadora" in nota for nota in resultado["limitations"]))

    def test_a_calculator_turn_without_innocuous_text_is_still_withheld(self):
        texto, estado, resultado = bs._withhold_unbacked_claim(
            {}, EJEMPLO + " " + EJEMPLO, ANSWER_TEXT_SHOWN, calculation={"ok": True})
        self.assertEqual(texto, "")
        self.assertNotEqual(estado, ANSWER_TEXT_SHOWN)
        self.assertEqual(resultado["withheld_reason"], "calculation")

    def test_a_short_but_innocuous_remainder_is_kept(self):
        texto, estado, _ = self.run_gate("Sí, existe. " + EJEMPLO)
        self.assertEqual(estado, ANSWER_TEXT_SHOWN)
        self.assertIn("Sí, existe.", texto)

    def test_the_remaining_text_keeps_its_unverified_state(self):
        _, estado, _ = self.run_gate(CONCEPTO + " " + EJEMPLO)
        self.assertEqual(estado, ANSWER_TEXT_SHOWN)

    def test_redaction_never_leaves_a_dangling_fragment(self):
        texto, _, _ = self.run_gate("Uno. Dos. Tres. " + CONCEPTO + " " + EJEMPLO)
        self.assertFalse(texto.startswith(" "))
        self.assertTrue(texto.endswith("."))


if __name__ == "__main__":
    unittest.main()
