"""El despliegue se queda en el plan gratuito y con los cupos abiertos.

DECISIÓN DE PRODUCTO (25/11/2026): Paideia se queda en el plan gratuito de Render.
No se sube a un plan de pago; si el tráfico supera lo que aguanta una instancia, se
acepta la cola antes que la factura.

Y los cupos del chat NO se bajan: medido con 50 usuarios simultáneos reales, el
plan gratuito responde 50/50 con 0 rechazos. Lo que rompía la experiencia no era la
falta de plan, eran los límites artificiales (4 turnos, 10 llamadas/min).

El arranque en frío del plan gratuito (30-50 s tras 15 minutos sin tráfico) NO se
mitiga: es una decisión explícita de producto. Se acepta esa espera en el primer
visitante antes que pagar un plan o mantener un keepalive. No añadir un ping
periódico "por si acaso": ya se valoró y se descartó.

Estos tests fijan lo que sí importa para que un cambio descuidado no lo deshaga.
"""
from __future__ import annotations

import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RENDER_YAML = os.path.join(RAIZ, "render.yaml")


def leer_render_yaml():
    with open(RENDER_YAML, encoding="utf-8") as fichero:
        return fichero.read()


def valor_de(texto, clave):
    """Devuelve el `value:` de una clave del blueprint, o None."""
    patron = rf"- key: {re.escape(clave)}\s*\n\s*value:\s*\"?([^\"\n]+)\"?\s*\n"
    encontrado = re.search(patron, texto)
    return encontrado.group(1).strip() if encontrado else None


class PlanGratuitoTest(unittest.TestCase):
    def setUp(self):
        self.texto = leer_render_yaml()

    def test_el_plan_es_gratuito(self):
        self.assertRegex(
            self.texto, r"plan:\s*free",
            "el despliegue tiene que quedarse en el plan gratuito por decisión de producto")

    def test_no_hay_plan_de_pago_en_el_blueprint(self):
        for plan_de_pago in ("starter", "standard", "pro", "professional"):
            with self.subTest(plan=plan_de_pago):
                self.assertNotRegex(
                    self.texto, rf"plan:\s*{plan_de_pago}",
                    f"el plan {plan_de_pago} es de pago: Paideia se queda en gratis")

    def test_los_cupos_no_bajan_de_la_sala(self):
        por_minuto = valor_de(self.texto, "PAIDEIA_CALLS_PER_MINUTE")
        por_dia = valor_de(self.texto, "PAIDEIA_CALLS_PER_DAY")
        self.assertIsNotNone(por_minuto, "falta PAIDEIA_CALLS_PER_MINUTE en el blueprint")
        self.assertIsNotNone(por_dia, "falta PAIDEIA_CALLS_PER_DAY en el blueprint")
        assert por_minuto is not None and por_dia is not None
        # 50 alumnos preguntando varias veces en el mismo minuto.
        self.assertGreaterEqual(
            int(por_minuto), 150,
            f"el cupo por minuto ({por_minuto}) tiene que cubrir la sala de 50")
        self.assertGreaterEqual(
            int(por_dia), 1000,
            f"el cupo diario ({por_dia}) tiene que cubrir una jornada de clase")

    def test_el_apagon_por_inactividad_queda_documentado(self):
        """Quien lea el blueprint tiene que saber que el servicio duerme."""
        self.assertRegex(self.texto, r"15 minutos|arranque en fr[ií]o",
                         "el blueprint debe explicar el apagado por inactividad")

    def test_no_se_anade_un_keepalive(self):
        """El arranque en frío se acepta: no se reintroduce un ping periódico.

        Se busca una IMPLEMENTACIÓN (una variable de entorno que active un ping, o
        un script), no la palabra en un comentario: el propio blueprint menciona el
        keepalive para dejar constancia de que se descartó.
        """
        self.assertNotRegex(
            self.texto, r"- key: PAIDEIA_KEEPALIVE|keepalive\.py|ping\.py",
            "no reintroducir un mecanismo que evite el apagado: se descartó")
        # Tampoco debe haber una tarea programada apuntando al servicio.
        perfiles = os.path.join(os.path.expanduser("~"), "AppData", "Local",
                                "hermes", "profiles", "trabajos")
        cron = os.path.join(perfiles, "cron", "jobs.json")
        if os.path.exists(cron):
            with open(cron, encoding="utf-8") as fichero:
                contenido = fichero.read()
            self.assertNotIn("mantener_despierta", contenido,
                             "quedó una tarea programada de keepalive: bórrala")


if __name__ == "__main__":
    unittest.main()
