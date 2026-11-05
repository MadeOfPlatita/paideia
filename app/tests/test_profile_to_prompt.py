"""El mapa del usuario debe llegar al modelo y cambiar lo que responde.

Estas pruebas no juzgan la prosa: comprueban el cuerpo que sale hacia el
proveedor. Si el perfil no viaja, ninguna respuesta puede tenerlo en cuenta.
"""

import unittest

from backend_services import LocalChatService
from chat_context import NOTICE as CONTEXT_NOTICE, VERSION as CONTEXT_VERSION
from providers import ChatResult
from structured_provider_adapter import FakeChatProvider

CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
           "purpose": "free_chat", "approved_fields": []}
EXTRA = {"notice_version": CONTEXT_NOTICE, "context": True, "history": False}

PERFIL = {
    "version": CONTEXT_VERSION,
    "fields": {
        "respuestas.objetivo": {"estado": "declarado", "valor": "ahorro_largo_plazo"},
        "respuestas.horizonte": {"estado": "declarado", "valor": "mas_3_anos"},
        "detalle_economico.importe_objetivo": {
            "estado": "declarado", "valor": {"min_eur": "20000", "max_eur": "50000", "moneda": "EUR"}},
        "detalle_economico.colchon_liquido": {
            "estado": "declarado", "valor": {"min_eur": "6000", "max_eur": "10000", "moneda": "EUR"}},
    },
}


def fake():
    return FakeChatProvider(ChatResult("Respuesta ficticia", "", (), "stop"), test_only=True)


def system_prompt(provider):
    return provider.requests[0][0]["content"]


class ProfileToPromptTests(unittest.TestCase):
    def test_the_four_fields_reach_the_system_prompt_literally(self):
        provider = fake()
        service = LocalChatService(provider=provider, enabled=True, test_only=True, context_enabled=True)

        service.chat({"message": "Pregunta ficticia", "consent": CONSENT,
                      "context_consent": EXTRA, "context": PERFIL})

        prompt = system_prompt(provider)
        self.assertIn('"version":"chat-context-map-v1"', prompt)
        for fragment in ('"respuestas.objetivo":{"estado":"declarado","valor":"ahorro_largo_plazo"}',
                         '"respuestas.horizonte":{"estado":"declarado","valor":"mas_3_anos"}',
                         '"detalle_economico.importe_objetivo":{"estado":"declarado","valor":{"min_eur":"20000","max_eur":"50000"',
                         '"detalle_economico.colchon_liquido":{"estado":"declarado","valor":{"min_eur":"6000","max_eur":"10000"'):
            self.assertIn(fragment, prompt)
        self.assertNotIn("No recibes ningún perfil personal", prompt)

    def test_without_context_consent_nothing_from_the_profile_is_sent(self):
        provider = fake()
        service = LocalChatService(provider=provider, enabled=True, test_only=True, context_enabled=True)

        service.chat({"message": "Pregunta ficticia", "consent": CONSENT})

        prompt = system_prompt(provider)
        self.assertIn("No recibes ningún perfil personal", prompt)
        self.assertNotIn("ahorro_largo_plazo", prompt)
        self.assertNotIn("20000", prompt)

    def test_undeclared_states_travel_without_a_value(self):
        provider = fake()
        service = LocalChatService(provider=provider, enabled=True, test_only=True, context_enabled=True)
        perfil = {"version": CONTEXT_VERSION, "fields": {
            "respuestas.objetivo": {"estado": "omitido"},
            "respuestas.horizonte": {"estado": "no_se"},
            "detalle_economico.importe_objetivo": {"estado": "sin_preguntar"},
        }}

        service.chat({"message": "Pregunta ficticia", "consent": CONSENT,
                      "context_consent": EXTRA, "context": perfil})

        prompt = system_prompt(provider)
        self.assertIn('"respuestas.objetivo":{"estado":"omitido"}', prompt)
        self.assertIn('"respuestas.horizonte":{"estado":"no_se"}', prompt)
        self.assertIn('"detalle_economico.importe_objetivo":{"estado":"sin_preguntar"}', prompt)
        self.assertNotIn('"valor"', prompt)


if __name__ == "__main__":
    unittest.main()


class ProfileEchoInAnswerTests(unittest.TestCase):
    """La respuesta empieza declarando el perfil autorizado (texto del servidor)."""

    def service(self):
        return LocalChatService(provider=fake(), enabled=True, test_only=True, context_enabled=True)

    def test_the_answer_opens_with_the_authorised_profile(self):
        body = self.service().chat({"message": "Pregunta ficticia", "consent": CONSENT,
                                    "context_consent": EXTRA, "context": PERFIL})
        self.assertTrue(body["answer"].startswith("Según el mapa que tú has autorizado"))
        self.assertIn("más de 3 años", body["answer"])
        self.assertIn("20.000–50.000 €", body["answer"])
        self.assertTrue(body.get("profile_applied"))

    def test_without_context_there_is_no_echo(self):
        body = self.service().chat({"message": "Pregunta ficticia", "consent": CONSENT})
        self.assertNotIn("Según el mapa", body["answer"])
        self.assertFalse(body.get("profile_applied"))

    def test_states_without_data_do_not_invent_a_profile(self):
        vacio = {"version": CONTEXT_VERSION, "fields": {
            "respuestas.horizonte": {"estado": "no_se"},
            "respuestas.objetivo": {"estado": "omitido"},
        }}
        body = self.service().chat({"message": "Pregunta ficticia", "consent": CONSENT,
                                    "context_consent": EXTRA, "context": vacio})
        self.assertNotIn("Según el mapa", body["answer"])
