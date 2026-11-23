"""Batería de Pai: qué responde, qué retiene y con qué forma.

Cubre los tres defectos reportados con llamadas reales a producción:
  1. «¿qué es la TAE?» se quedaba en blanco («tanto anual equivalente» sí
     respondía): el filtro de atribución trataba el vocabulario de manual como
     si atribuyera datos del catálogo.
  2. Las preguntas prácticas («1.000 € en 2 años, ¿dónde lo pongo?») no daban
     orientación; el prompt no lo pedía.
  3. Las respuestas largas se cortaban por presupuesto de salida.

Estas pruebas son de frontera (superficie y contrato), no de calidad semántica:
no afirman que el texto sea correcto, solo que no se retiene lo que debe pasar,
que sí se retiene lo que adjudica datos sin fuente y que el DTO declara el corte.
"""

import unittest

import backend_services as bs
from pai_runtime import ANSWER_TEXT_SHOWN

GOOD = ",\n".join


class AttributionGateTests(unittest.TestCase):
    """El filtro no debe confundir manual con catálogo."""

    MANUAL = [
        "La TAE oficial la publica el banco.",
        "Se calcula conforme al folleto del producto.",
        "El tipo oficial de referencia es el Euríbor.",
        "La TAE vigente puede cambiar.",
        "La TAE confirmada por el banco es la que aplica.",
        "Compara la TAE publicada por cada entidad.",
        "Revisa el folleto del producto antes de contratar.",
        "Debes consultar la ficha del producto.",
        "La normativa europea obliga a publicar la TAE.",
        "El banco publica su TAE en su web.",
        "La TAE es un indicador estandarizado que expresa el coste anual.",
        "El TIN no incluye comisiones; la TAE sí.",
        "Según la normativa, la TAE incluye el coste del dinero en préstamos.",
        "Un producto regulado debe informar de la TAE antes de contratar.",
    ]

    ADJUDICA = [
        "Esa cuenta ofrece una TAE del 3,10 % según la fuente oficial.",
        "Según la ficha, este depósito paga un 2,75 % a 12 meses.",
        "El producto está confirmado como vigente en el folleto.",
        "Este fondo tiene un TER del 0,20 % publicado por la gestora.",
        "Esa oferta remunera al 3 % desde el 1 de enero de 2026.",
        "El depósito está vigente con una TAE del 2,50 %.",
    ]

    def test_the_financial_manual_vocabulary_passes(self):
        for frase in self.MANUAL:
            with self.subTest(frase=frase):
                permitido, motivo = bs._text_surface_gate(frase)
                self.assertTrue(permitido, f"se retuvo vocabulario de manual: {motivo}")

    def test_a_claim_about_a_concrete_product_is_withheld(self):
        for frase in self.ADJUDICA:
            with self.subTest(frase=frase):
                permitido, motivo = bs._text_surface_gate(frase)
                self.assertFalse(permitido, "se dejó pasar una adjudicación de dato")
                # El motivo puede ser `attribution` (atribuye el dato) o `figure`
                # (la cifra sola ya basta). Ambos retienen; lo que no puede pasar
                # es que una adjudicación de dato quede sin retener.
                self.assertIn(motivo, {"attribution", "figure"})

    def test_a_catalogue_turn_keeps_the_strict_rule(self):
        """Con datos de catálogo, atribuir una fuente es adjudicar un dato local."""
        frases = ("Esa cuenta da un 3,10 % según la fuente oficial.",
                  "Según la ficha, este depósito sube un 0,25 %.")
        for frase in frases:
            with self.subTest(frase=frase):
                permitido, motivo = bs._text_surface_gate(frase)
                self.assertFalse(permitido)
                self.assertIn(motivo, {"attribution", "figure"})

    def test_the_identifier_surface_is_unchanged(self):
        permitido, motivo = bs._text_surface_gate("El producto DEP-EBN-12 ofrece ventajas.")
        self.assertFalse(permitido)
        self.assertEqual(motivo, "identifier")

    def test_a_bare_figure_is_still_a_figure(self):
        permitido, motivo = bs._text_surface_gate("El rendimiento es del 3,10 % anual.")
        self.assertFalse(permitido)
        self.assertEqual(motivo, "figure")


class WithholdEntryPointTests(unittest.TestCase):
    """La función que decide el estado final del turno."""

    def test_an_explanation_with_manual_vocabulary_is_shown(self):
        texto = ("La TAE, o tasa anual equivalente, es la referencia normalizada del coste o "
                 "rendimiento de un producto financiero. La publica la entidad conforme a la "
                 "normativa y sirve para comparar ofertas con plazos distintos.")
        salida, estado, resultado = bs._withhold_unbacked_claim({}, texto, ANSWER_TEXT_SHOWN)
        self.assertEqual(estado, ANSWER_TEXT_SHOWN)
        self.assertEqual(salida, texto)
        self.assertNotIn("withheld_reason", resultado)

    def test_a_concept_turn_with_catalogue_data_withholds_the_attribution(self):
        texto = "Según la ficha oficial, este depósito paga un 3,25 %."
        salida, estado, resultado = bs._withhold_unbacked_claim(
            {}, texto, ANSWER_TEXT_SHOWN)
        self.assertEqual(salida, "")
        self.assertIn(resultado["withheld_reason"], {"attribution", "figure"})

    def test_a_practical_answer_with_the_user_figures_is_kept(self):
        """Los datos que aporta la persona no son cifras de producto."""
        texto = ("Con 1.000 € a 2 años no asumiría renta variable: una caída en el momento de "
                 "rescatar te obligaría a vender con pérdidas. Por ejemplo, un 2 % sobre 1.000 € "
                 "son 40 € en dos años. Prioriza liquidez y plazo cubierto.")
        _, estado, _ = bs._withhold_unbacked_claim({}, texto, ANSWER_TEXT_SHOWN)
        self.assertEqual(estado, ANSWER_TEXT_SHOWN)


class PromptContractTests(unittest.TestCase):
    """El prompt debe pedir utilidad, no solo cautela."""

    def test_the_prompt_declares_the_educational_role_without_disabling_help(self):
        prompt = bs.CHAT_SYSTEM_PROMPT
        self.assertIn("no un asesor financiero registrado", prompt)
        self.assertIn("Nunca digas que no puedes ayudar por no ser asesor", prompt)

    def test_the_prompt_asks_for_exhaustive_definitions(self):
        prompt = bs.CHAT_SYSTEM_PROMPT
        self.assertIn("definición completa y exhaustiva", prompt)
        self.assertIn("sinónimos", prompt)

    def test_the_prompt_asks_for_guidance_on_practical_decisions(self):
        prompt = bs.CHAT_SYSTEM_PROMPT
        self.assertIn("Decisión práctica", prompt)
        self.assertIn("dos o tres", prompt)
        self.assertIn("qué harías tú con ese dinero", prompt)

    def test_the_prompt_still_forbids_inventing_product_data(self):
        prompt = bs.CHAT_SYSTEM_PROMPT
        self.assertIn("nunca inventes productos, tasas, fuentes ni citas", prompt)
        self.assertIn("solo pueden salir de", prompt)


class OutputBudgetTests(unittest.TestCase):
    def test_the_chat_budget_allows_a_long_answer(self):
        import pai_setup
        self.assertGreaterEqual(pai_setup.CHAT_OUTPUT_TOKENS, 3000)
        from providers import MAX_OUTPUT_TOKENS
        self.assertLessEqual(pai_setup.CHAT_OUTPUT_TOKENS, MAX_OUTPUT_TOKENS)


if __name__ == "__main__":
    unittest.main()
