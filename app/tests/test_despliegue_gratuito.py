"""El despliegue se queda en el plan gratuito y con los cupos abiertos.

DECISIÓN DE PRODUCTO (25/11/2026): Paideia se queda en el plan gratuito de Render.
No se sube a un plan de pago; si el tráfico supera lo que aguanta una instancia, se
acepta la cola antes que la factura.

Y los cupos del chat NO se bajan: medido con 50 usuarios simultáneos reales, el
plan gratuito responde 50/50 con 0 rechazos. Lo que rompía la experiencia no era la
falta de plan, eran los límites artificiales (4 turnos, 10 llamadas/min).

Estos tests fijan las dos cosas para que un cambio descuidado no las deshaga.
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
        """Quien lea el blueprint tiene que saber que el servicio duerme y cómo se evita."""
        self.assertIn("mantener_despierta", self.texto,
                      "el blueprint debe remitir al keepalive que evita el arranque en frío")
        self.assertRegex(self.texto, r"15 minutos|arranque en fr[ií]o",
                         "el blueprint debe explicar el apagado por inactividad")


class KeepaliveExisteTest(unittest.TestCase):
    """El script que evita el arranque en frío tiene que existir y ser usable."""

    def test_el_script_del_keepalive_existe(self):
        ruta = os.path.join(
            os.path.expanduser("~"), "AppData", "Local", "hermes", "profiles",
            "trabajos", "scripts", "mantener_despierta.py")
        if not os.path.exists(ruta):
            self.skipTest("el script vive fuera del repositorio (perfil de Hermes)")
        with open(ruta, encoding="utf-8") as fichero:
            codigo = fichero.read()
        self.assertIn("/api/status", codigo,
                      "el keepalive tiene que llamar a un endpoint que no gaste IA")
        self.assertNotIn("/api/chat", codigo,
                         "el keepalive no puede gastar llamadas al proveedor")


if __name__ == "__main__":
    unittest.main()
