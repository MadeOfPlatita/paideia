"""«Tu mapa» confirma cada respuesta en un box antes de avanzar.

El flujo anterior saltaba a la pregunta siguiente en el mismo clic, así que no se
veía qué se había respondido. Ahora la respuesta queda en un box con la pregunta
anterior, el valor y el botón Continuar.
"""

import re
import unittest
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "static"


class ProfileConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.js = (STATIC / "app.js").read_text(encoding="utf-8")
        self.css = (STATIC / "styles.css").read_text(encoding="utf-8")

    def test_box_texts_and_classes_exist(self):
        for marca in ("PREGUNTA ANTERIOR", "profile-answer-box", "profile-confirm",
                      "profileConfirmAnswered", "profileConfirmKey"):
            with self.subTest(marca=marca):
                self.assertIn(marca, self.js)
        for clase in (".profile-answer-box", ".profile-answer-value", ".profile-answer-label"):
            with self.subTest(clase=clase):
                self.assertIn(clase, self.css)

    def test_record_profile_answer_waits_for_confirmation(self):
        inicio = self.js.index("function recordProfileAnswer(")
        fin = self.js.index("function profileConfirmAnswered(")
        cuerpo = self.js[inicio:fin]
        self.assertIn("state.profileConfirmKey = key;", cuerpo)
        self.assertNotIn("state.profileStep += 1", cuerpo,
                         "guardar no debe avanzar sin pasar por el box")

    def test_continue_advances_and_last_question_reviews(self):
        inicio = self.js.index("function profileConfirmAnswered(")
        cuerpo = self.js[inicio:inicio + 700]
        self.assertIn("state.profileConfirmKey = null;", cuerpo)
        self.assertIn("state.profileStep += 1", cuerpo)
        self.assertIn('state.profileMode = "summary"', cuerpo)

    def test_focus_moves_to_the_box_button(self):
        patron = r'route === "perfil" && state\.profileConfirmKey[\s\S]{0,220}\.profile-confirm \.button-primary'
        self.assertRegex(self.js, patron)

    def test_changing_an_answer_returns_to_the_question(self):
        inicio = self.js.index("function renderProfileConfirmation(")
        cuerpo = self.js[inicio:inicio + 2600]
        self.assertIn('button("Cambiar respuesta"', cuerpo)
        self.assertIn("state.profileConfirmKey = null;", cuerpo)


if __name__ == "__main__":
    unittest.main()
