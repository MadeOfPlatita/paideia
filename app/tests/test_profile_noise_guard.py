"""El perfil autorizado no debe invadir la respuesta del modelo.

Caso medido en produccion: con el mapa marcado, la pregunta «¿que es el interes
compuesto?» devolvia primero «Segun el mapa que tu has autorizado: horizonte mas
de 3 anos» y despues la definicion. El campo no venia al caso: era ruido del
servidor delante del texto del modelo, y se repetia en TODAS las respuestas.

Ahora la linea del perfil viaja aparte, en `profile_line`, y el texto de la
respuesta queda limpio. El perfil sigue llegando al prompt: no se pierde nada.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import LocalChatService  # noqa: E402
from structured_provider_adapter import FakeChatProvider  # noqa: E402
from providers import ChatResult  # noqa: E402

CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
           "purpose": "free_chat", "approved_fields": []}
EXTRA = {"notice_version": "paideia-chat-context-map-v1", "context": True, "history": False}
PERFIL = {"version": "chat-context-map-v1", "fields": {
    "respuestas.horizonte": {"estado": "declarado", "valor": "mas_3_anos"},
    "respuestas.objetivo": {"estado": "declarado", "valor": "aprender_conceptos"},
}}


def service():
    return LocalChatService(provider=FakeChatProvider(
        ChatResult("El interes compuesto capitaliza los intereses.", None, (), "stop"),
        test_only=True), enabled=True, test_only=True, context_enabled=True)


class ProfileDoesNotInvadeAnswerTests(unittest.TestCase):
    def test_the_answer_is_the_model_text_alone(self):
        body = service().chat({"message": "¿Que es el interes compuesto?", "consent": CONSENT,
                               "context_consent": EXTRA, "context": PERFIL})
        self.assertEqual(body["answer"], "El interes compuesto capitaliza los intereses.")
        self.assertNotIn("Según el mapa", body["answer"])

    def test_the_profile_line_is_published_separately(self):
        body = service().chat({"message": "¿Que es el interes compuesto?", "consent": CONSENT,
                               "context_consent": EXTRA, "context": PERFIL})
        self.assertTrue(body.get("profile_applied"))
        self.assertIn("más de 3 años", body["profile_line"])

    def test_without_context_there_is_no_profile_line(self):
        body = service().chat({"message": "¿Que es el interes compuesto?", "consent": CONSENT})
        self.assertNotIn("profile_line", body)
        self.assertFalse(body.get("profile_applied"))


if __name__ == "__main__":
    unittest.main()
