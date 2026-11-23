"""Un 200 sin texto no se entrega como respuesta.

Medido en produccion: «Tengo 1000 euros que necesito en 2 anos, donde los pongo»
devolvio HTTP 200 con `answer: ""` y `answer_text_state: shown_unverified`. El
usuario veia un hueco sin explicacion: la interfaz pintaba una respuesta vacia.

Ahora el servicio responde 502 CHAT_EMPTY_ANSWER con un motivo, salvo que haya
datos locales que mostrar (catalogo o calculo), en cuyo caso el hueco esta
justificado y se entrega el turno con esos datos.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend_services import LocalChatService, ServiceProblem  # noqa: E402
from providers import ChatResult  # noqa: E402
from structured_provider_adapter import FakeChatProvider  # noqa: E402

CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
           "purpose": "free_chat", "approved_fields": []}


def service_with(result):
    return LocalChatService(provider=FakeChatProvider(result, test_only=True),
                            enabled=True, test_only=True)


class EmptyAnswerTests(unittest.TestCase):
    def test_a_turn_without_text_is_reported_not_delivered(self):
        service = service_with(ChatResult("", "", (), "stop"))
        with self.assertRaises(ServiceProblem) as caught:
            service.chat({"message": "Tengo 1000 euros que necesito en 2 años. ¿Dónde los pongo?",
                          "consent": CONSENT})
        self.assertEqual(caught.exception.code, "CHAT_EMPTY_ANSWER")
        self.assertEqual(caught.exception.status, 502)
        self.assertIn("reformula", caught.exception.message)

    def test_blank_whitespace_is_also_empty(self):
        service = service_with(ChatResult("   \n\t ", "", (), "stop"))
        with self.assertRaises(ServiceProblem) as caught:
            service.chat({"message": "¿Qué es la TAE?", "consent": CONSENT})
        self.assertEqual(caught.exception.code, "CHAT_EMPTY_ANSWER")

    def test_a_normal_answer_is_untouched(self):
        service = service_with(ChatResult("La TAE normaliza el coste anual.", "", (), "stop"))
        body = service.chat({"message": "¿Qué es la TAE?", "consent": CONSENT})
        self.assertIn("La TAE normaliza", body["answer"])

    def test_a_refusal_is_not_treated_as_empty(self):
        service = service_with(ChatResult("", "", (), "stop", refusal="No puedo ayudar con eso."))
        body = service.chat({"message": "¿Qué es la TAE?", "consent": CONSENT})
        self.assertEqual(body["answer"], "No puedo ayudar con eso.")


if __name__ == "__main__":
    unittest.main()
