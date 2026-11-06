"""El ritmo vertical y la separación entre cajas no vuelven a pegarse.

Fija el contrato que se rompió: las rutas se apilan en una rejilla con hueco
uniforme, la hoja se carga la última y las rejillas de tarjetas no bajan de 10 px.
"""

import re
import unittest
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "static"


class SpacingTests(unittest.TestCase):
    def leer(self, nombre):
        return (STATIC / nombre).read_text(encoding="utf-8")

    def test_stylesheet_is_linked_last(self):
        html = self.leer("index.html")
        hojas = re.findall(r'href="\./([\w.-]+\.css)"', html)
        self.assertIn("spacing.css", hojas)
        self.assertEqual(hojas[-1], "spacing.css", hojas)

    def test_page_shell_is_a_single_column_grid_with_a_real_gap(self):
        css = self.leer("spacing.css")
        encontrado = re.search(r"\.page-shell\s*\{([^}]*)\}", css)
        self.assertIsNotNone(encontrado)
        bloque = encontrado.group(1)
        self.assertIn("display: grid", bloque)
        gap = re.search(r"gap:\s*(\d+)px", bloque)
        self.assertIsNotNone(gap)
        self.assertGreaterEqual(int(gap.group(1)), 16)

    def test_direct_children_do_not_add_their_own_margins(self):
        css = self.leer("spacing.css")
        self.assertIn(".page-shell > *", css)
        self.assertIn("margin-top: 0", css)

    def test_card_grids_keep_a_minimum_gap(self):
        css = self.leer("spacing.css")
        for selector in (".home-actions", ".privacy-field-list", ".choice-list",
                         ".result-list", ".comparison-columns", ".scenario-summary"):
            with self.subTest(selector=selector):
                bloque = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
                self.assertIsNotNone(bloque, selector)
                gap = re.search(r"gap:\s*(\d+)px", bloque.group(1))
                self.assertIsNotNone(gap)
                self.assertGreaterEqual(int(gap.group(1)), 10)

    def test_mobile_home_actions_are_not_glued(self):
        css = self.leer("spacing.css")
        # Busca el bloque de 640 px que contiene .home-actions, sin depender de
        # que sea el último @media del archivo.
        bloques = re.findall(r"@media \(max-width: 640px\)\s*\{(.*?)\n\}", css, re.S)
        candidatos = [b for b in bloques if ".home-actions" in b]
        self.assertTrue(candidatos, "no hay bloque móvil con .home-actions")
        gap = re.search(r"\.home-actions\s*\{[^}]*gap:\s*(\d+)px", candidatos[0])
        self.assertIsNotNone(gap)
        self.assertGreaterEqual(int(gap.group(1)), 12)


if __name__ == "__main__":
    unittest.main()
