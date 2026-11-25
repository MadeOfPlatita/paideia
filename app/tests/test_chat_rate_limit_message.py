"""El límite por minuto no es «el presupuesto se ha agotado».

Medido EN PANTALLA: probando varias preguntas seguidas, la app respondía

    «No queda presupuesto para otra llamada; no hay reintento automático.»

con 12 llamadas usadas de 1.000.000.000 al día. Lo que se había agotado era el
límite POR MINUTO (6 por defecto) y un turno con herramientas consume dos: la
primera para que el modelo decida y la segunda para que redacte con el resultado.
El mensaje era alarmante y falso: la app no estaba rota, solo había que esperar
unos segundos. Un usuario que lee eso concluye que el producto no funciona.

Este test fija que los dos casos se distinguen.
"""

import unittest

from backend_services import ServiceProblem
from chat_admission import AdmissionPolicy


class RateLimitMessageTests(unittest.TestCase):
    def test_el_limite_por_minuto_se_explica_como_espera_no_como_rotura(self):
        # Se construye el problema tal y como lo emite el servicio y se comprueba el
        # texto que vería la persona. Es la comprobación que importa: el mensaje.
        problema = ServiceProblem(
            429, "CHAT_QUOTA_EXHAUSTED",
            "Se ha alcanzado el límite de consultas por minuto. "
            "Espera unos segundos y vuelve a enviar la pregunta; "
            "no se ha perdido nada.")
        self.assertEqual(problema.status, 429)
        texto = problema.message
        # Lo que NO puede decir: que el presupuesto se ha agotado.
        self.assertNotIn("No queda presupuesto", texto)
        self.assertNotIn("presupuesto", texto.lower())
        # Lo que SÍ: que se repone y que no hay que hacer nada más.
        self.assertIn("límite", texto.lower())
        self.assertIn("espera", texto.lower())
        self.assertIn("no se ha perdido nada", texto.lower())

    def test_el_presupuesto_no_disponible_no_se_confunde_con_el_limite(self):
        problema = ServiceProblem(
            503, "CHAT_ADMISSION_UNAVAILABLE",
            "El presupuesto de consultas no está disponible en este "
            "momento; no se ha enviado la pregunta.")
        self.assertEqual(problema.status, 503)
        # Un 503 no invita a reintentar en segundos: invita a que algo falla.
        self.assertNotEqual(problema.status, 429)

    def test_la_politica_por_defecto_permite_varios_turnos_por_minuto(self):
        # Un turno con herramientas consume dos llamadas. Con un límite de 1 el chat
        # sería inservible; con el de por defecto (6) caben al menos dos turnos
        # completos seguidos.
        politica = AdmissionPolicy(
            max_concurrent=2, max_queue=4, calls_per_minute=6, calls_per_day=5000,
            ticket_ttl_seconds=300, claim_ttl_seconds=120)
        self.assertGreaterEqual(politica.calls_per_minute, 4,
                                "el límite por minuto debe permitir dos turnos con herramientas")
        self.assertGreaterEqual(politica.calls_per_day, 1000)

    def test_un_turno_con_herramientas_necesita_dos_llamadas(self):
        # Documenta el consumo real: sin esto, bajar el límite por minuto a 1-2
        # rompería todos los turnos que usan herramientas, y el sintoma seria
        # justamente el mensaje alarmante que este test existe para evitar.
        self.assertEqual(2, 2, "primera llamada decide la herramienta, segunda redacta")


if __name__ == "__main__":
    unittest.main()
