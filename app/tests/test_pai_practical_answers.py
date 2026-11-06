"""Pai explica el método, no solo la definición.

El prompt pedía «responde solo con lo que devuelva la herramienta» y un máximo de
tres frases, así que a «¿cómo monto un colchón?» contestaba con una definición.
Ahora distingue dato de catálogo (tres frases) de explicación práctica (pasos), y
la redacción de cifras respeta las referencias de método etiquetadas y los datos
que aporta el usuario.
"""

import unittest

import backend_services as servicio
from financial_quality import FINANCIAL_EDUCATION_PROMPT


class PromptTests(unittest.TestCase):
    def test_prompt_asks_for_steps_when_the_question_is_practical(self):
        prompt = servicio.CHAT_SYSTEM_PROMPT
        self.assertIn("no solo definas", prompt)
        self.assertIn("tres a cinco pasos", prompt)
        self.assertIn("hasta ocho frases", prompt)

    def test_catalogue_answers_keep_the_short_budget(self):
        self.assertIn("máximo tres frases", servicio.CHAT_SYSTEM_PROMPT)

    def test_product_figures_still_come_only_from_tools(self):
        prompt = servicio.CHAT_SYSTEM_PROMPT
        self.assertIn("solo pueden salir de esas herramientas", prompt)

    def test_education_prompt_allows_labelled_method_references(self):
        self.assertIn("referencias generales", FINANCIAL_EDUCATION_PROMPT)
        self.assertIn("No inventes cifras de productos", FINANCIAL_EDUCATION_PROMPT)


class RedactionTests(unittest.TestCase):
    def test_labelled_general_reference_survives(self):
        texto = "Como referencia general, entre tres y seis meses de gastos."
        parcial, quitadas = servicio._redact_unbacked_figures(texto)
        self.assertEqual(quitadas, 0)

    def test_user_supplied_amount_survives(self):
        texto = "Con el importe que tú aportaste, 1.500 euros, el colchón cubre un mes."
        parcial, quitadas = servicio._redact_unbacked_figures(texto)
        self.assertEqual(quitadas, 0)

    def test_product_rate_is_still_removed(self):
        texto = "La cuenta remunera al 2,61 % TAE."
        parcial, quitadas = servicio._redact_unbacked_figures(texto)
        self.assertEqual(quitadas, 1)
        self.assertEqual(parcial, "")

    def test_product_amount_is_still_removed(self):
        texto = "Gana 500 euros al mes con ese depósito."
        parcial, quitadas = servicio._redact_unbacked_figures(texto)
        self.assertEqual(quitadas, 1)

    def test_a_label_cannot_smuggle_a_rate(self):
        texto = "Como referencia general, esa cuenta da un 3,10 %."
        parcial, quitadas = servicio._redact_unbacked_figures(texto)
        self.assertEqual(quitadas, 1)

    def test_mixed_text_keeps_the_method_and_drops_the_rate(self):
        texto = ("Primero suma tus gastos fijos. Como referencia general, entre tres y seis meses de gastos. "
                 "La cuenta remunera al 2,61 % TAE.")
        parcial, quitadas = servicio._redact_unbacked_figures(texto)
        self.assertEqual(quitadas, 1)
        self.assertIn("tres y seis meses", parcial)
        self.assertNotIn("2,61", parcial)


if __name__ == "__main__":
    unittest.main()
