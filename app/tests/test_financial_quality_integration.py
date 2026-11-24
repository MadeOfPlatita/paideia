"""TEST ONLY: offline replay through real HTTP; no external provider.

CONTRATO (cambio medido, no cosmetico)
--------------------------------------
Antes: cualquier frase que prometiera riesgo cero tiraba el turno ENTERO con 502
CHAT_FINANCIAL_QUALITY_REJECTED.

Eso se midio contra el proveedor real y el resultado fue que preguntas educativas
normales dejaban de funcionar. «¿Que es la inflacion y como afecta a mis
ahorros?» devolvio 502 en 5 de 5 intentos, y las 5 respuestas eran correctas:
contenian UNA frase con una formula que la guarda no reconocia, entre otras diez
que ensenaban bien. Cada redaccion nueva del modelo («no conviene afirmar», «no
asumas», «no debe presentarse», «no trates»...) costaba un 502 al usuario.

Ahora: la frase peligrosa se ELIMINA y el resto se entrega. La promesa de riesgo
cero no se muestra nunca; lo que cambia es que no se castiga al usuario por una
frase entre veinte. El fail-closed se conserva donde tiene sentido: si al quitar
las frases peligrosas no queda NADA, sigue siendo 502.
"""
import unittest
import app
from backend_services import LocalChatService, CatalogueComparisonService
from pai_tools import ToolDispatcher
from providers import ChatResult, ToolCall
from test_backend_integration import running_server, request
from test_functional05_http import make_gate, CONSENT
from test_pai_runtime import scenario_arguments
from test_functional05_http import TestOnlyFakeProvider

# Frase PELIGROSA seguida de contenido correcto. La primera afirma que ahorrar no
# tiene riesgo; el resto explica la inflacion correctamente.
FRASE_PELIGROSA = "Ahorrar significa conservar dinero sin riesgo de perder el capital."
RESTO_SEGURO = ("La inflación reduce el valor real del dinero ahorrado, porque los "
                "precios suben y el poder de compra de ese capital disminuye con el tiempo.")
REAL_REPLAY = FRASE_PELIGROSA + " " + RESTO_SEGURO

# Respuesta en la que TODO es peligroso: no queda nada que entregar.
SOLO_PELIGROSO = "Invertir no conlleva ningún riesgo. Este producto tiene cero riesgo."


class FinancialQualityIntegration(unittest.TestCase):
    def _service(self, provider, mode):
        """Devuelve (servicio, puerta) para poder mirar la puerta desde el test."""
        gate = make_gate() if mode != 'plain' else None
        servicio = LocalChatService(provider=provider, enabled=True, test_only=True,
            admission=gate, tools_enabled=mode == 'tools',
            dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()) if mode == 'tools' else None)
        return servicio, gate

    def test_the_unsafe_sentence_is_removed_and_the_rest_is_delivered(self):
        # Antes: 502 y el usuario perdia la explicacion entera.
        # Ahora: 200 sin la frase peligrosa y con el resto intacto.
        for mode in ('plain', 'admitted', 'tools'):
            with self.subTest(mode=mode):
                provider = TestOnlyFakeProvider([ChatResult(REAL_REPLAY, None, (), 'stop')])
                service, gate = self._service(provider, mode)
                with running_server(chat_service=service) as server:
                    status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
                self.assertEqual(status, 200)
                # La promesa de riesgo cero NO se muestra nunca.
                self.assertNotIn("sin riesgo de perder el capital", body['answer'])
                self.assertNotIn(FRASE_PELIGROSA, str(body))
                # Y lo que si era correcto se conserva.
                self.assertIn("La inflación reduce el valor real", body['answer'])
                self.assertEqual(len(provider.requests), 1)
                if gate: self.assertEqual(gate.status()['active'], 0)

    def test_a_fully_unsafe_answer_is_still_rejected(self):
        # Fail-closed se conserva: si no sobrevive nada, es 502.
        for mode in ('plain', 'admitted', 'tools'):
            with self.subTest(mode=mode):
                provider = TestOnlyFakeProvider([ChatResult(SOLO_PELIGROSO, None, (), 'stop')])
                service, gate = self._service(provider, mode)
                with running_server(chat_service=service) as server:
                    status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
                self.assertEqual((status, body['error']['code']), (502, 'CHAT_FINANCIAL_QUALITY_REJECTED'))
                self.assertNotIn("cero riesgo", str(body))
                self.assertEqual(len(provider.requests), 1)
                if gate: self.assertEqual(gate.status()['active'], 0)

    def test_safe_and_refusal_visible_in_all_modes(self):
        safe = 'TEST ONLY: Ahorrar puede tener riesgos; la inflación afecta al poder adquisitivo.'
        for mode in ('plain', 'admitted', 'tools'):
            for refusal in (False, True):
                with self.subTest(mode=mode, refusal=refusal):
                    provider = TestOnlyFakeProvider([ChatResult('' if refusal else safe, None, (), 'stop', refusal=safe if refusal else None)])
                    service, gate = self._service(provider, mode)
                    with running_server(chat_service=service) as server:
                        status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
                    self.assertEqual(status, 200)
                    self.assertEqual(body['answer'], safe)
                    self.assertEqual(body['refused'], refusal)
                    self.assertEqual(len(provider.requests), 1)
                    if gate: self.assertEqual(gate.status()['active'], 0)

    def test_an_unsafe_refusal_loses_only_the_unsafe_sentence(self):
        for mode in ('plain', 'admitted', 'tools'):
            with self.subTest(mode=mode):
                provider = TestOnlyFakeProvider([ChatResult('', None, (), 'stop', refusal=REAL_REPLAY)])
                service, gate = self._service(provider, mode)
                with running_server(chat_service=service) as server:
                    status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
                self.assertEqual(status, 200)
                self.assertNotIn(FRASE_PELIGROSA, str(body))
                self.assertEqual(len(provider.requests), 1)
                if gate: self.assertEqual(gate.status()['active'], 0)

    def test_tool_followup_unsafe_final_keeps_the_safe_part_without_extra_dispatch(self):
        provider = TestOnlyFakeProvider([
            ChatResult('', None, (ToolCall('test-call', 'calculate_scenario', scenario_arguments()),), 'tool_calls'),
            ChatResult(REAL_REPLAY, None, (), 'stop')])
        gate = make_gate()
        service = LocalChatService(provider=provider, enabled=True, test_only=True, admission=gate,
            tools_enabled=True, dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()))
        with running_server(chat_service=service) as server:
            status, body = request(server, '/api/chat', {'message':'TEST ONLY', 'consent':CONSENT})
        self.assertEqual(status, 200)
        self.assertNotIn(FRASE_PELIGROSA, str(body))
        # Sin despacho extra: dos peticiones, una por turno.
        self.assertEqual(len(provider.requests), 2)
        self.assertEqual(gate.status()['active'], 0)
        self.assertEqual(gate.status()['calls_day'], 2)
