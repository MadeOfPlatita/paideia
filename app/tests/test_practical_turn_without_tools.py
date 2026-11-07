"""Las preguntas de método no abren el catálogo ni anuncian herramientas."""

import unittest

import app
from backend_services import CatalogueComparisonService, _is_practical_question
from catalogue_adapter import CatalogueWithConditions
from conditions_service import ConditionsService
from pai_runtime import ChatResult, ToolChatRunner
from pai_tools import ToolDispatcher


class RecordingProvider:
    test_only = True

    def __init__(self):
        self.tools = "sin_llamar"

    def chat(self, messages, *, tools=None):
        self.tools = tools
        return ChatResult("Pasos de método.", None, (), "stop")


class PracticalTurnTests(unittest.TestCase):
    def test_practical_questions_are_recognised(self):
        for pregunta in ("¿Cómo monto un colchón de emergencia?",
                         "¿Cómo funcionan las letras del Tesoro?",
                         "Diferencia entre TAE y TIN",
                         "¿Cómo salgo de una deuda de tarjeta?"):
            self.assertTrue(_is_practical_question(pregunta), pregunta)

    def test_product_questions_keep_the_catalogue(self):
        for pregunta in ("¿Qué TAE tiene la Cuenta Contigo?",
                         "¿Qué depósitos hay en el catálogo?",
                         "¿Qué TAE ofrece Openbank?"):
            self.assertFalse(_is_practical_question(pregunta), pregunta)

    def test_a_practical_turn_is_sent_without_tools(self):
        provider = RecordingProvider()
        dispatcher = ToolDispatcher(
            CatalogueWithConditions(app.SnapshotRepository(), ConditionsService()),
            CatalogueComparisonService(),
        )
        resultado = ToolChatRunner(provider, dispatcher).run(
            [{"role": "user", "content": "¿Cómo monto un colchón?"}], with_tools=False)
        self.assertIsNone(provider.tools)
        self.assertEqual(resultado["finish_reason"], "stop")
        self.assertEqual(resultado["tool_events"], [])


if __name__ == "__main__":
    unittest.main()
