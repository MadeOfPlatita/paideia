"""El diario de desarrollo existe, cuenta lo usado y no filtra credenciales."""

import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIARIO = RAIZ / "docs" / "DIARIO-DESARROLLO.md"


class DiaryTests(unittest.TestCase):
    def setUp(self):
        self.texto = DIARIO.read_text(encoding="utf-8")

    def test_existe_y_tiene_las_secciones_pedidas(self):
        self.assertTrue(DIARIO.is_file())
        for seccion in ("## Herramientas utilizadas", "## APIs y proveedores",
                        "## Cómo se verifica hoy", "## Límites vigentes"):
            with self.subTest(seccion=seccion):
                self.assertIn(seccion, self.texto)

    def test_nombra_las_herramientas_y_proveedores_reales(self):
        for nombre in ("Hermes Agent", "Render", "Vercel", "Command Code", "Groq",
                       "Tesoro", "CNMV", "pytest", "node --test"):
            with self.subTest(nombre=nombre):
                self.assertIn(nombre, self.texto)

    def test_no_contiene_credenciales(self):
        patrones = (r"gsk_[A-Za-z0-9]", r"sk-[A-Za-z0-9]{10}", r"Bearer\s+[A-Za-z0-9]")
        for patron in patrones:
            with self.subTest(patron=patron):
                self.assertIsNone(re.search(patron, self.texto))


if __name__ == "__main__":
    unittest.main()
