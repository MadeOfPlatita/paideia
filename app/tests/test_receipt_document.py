"""El justificante se imprime como documento, no como una copia de la web.

Fija el contrato que se rompió dos veces: el CSS del informe no puede ocultar
toda la aplicación y el justificante debe existir como documento aparte.
"""

import re
import unittest
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "static"


class ReceiptDocumentTests(unittest.TestCase):
    def leer(self, nombre):
        return (STATIC / nombre).read_text(encoding="utf-8")

    def test_index_links_the_receipt_stylesheet(self):
        self.assertIn('href="./receipt_print.css"', self.leer("index.html"))

    def test_receipt_is_hidden_on_screen_and_shown_only_when_printing(self):
        css = self.leer("receipt_print.css")
        self.assertRegex(css, r"#receipt-print\s*\{\s*display:\s*none")
        self.assertIn("body.receipt-printing > :not(#receipt-print)", css)
        self.assertIn("body.receipt-printing #receipt-print", css)
        self.assertIn("@page", css)

    def test_report_stylesheet_does_not_hide_the_whole_app_by_default(self):
        css = self.leer("comparison_report.css")
        sueltas = re.findall(r"body\s*>\s*:not\(#comparison-report-print\)", css)
        self.assertEqual(sueltas, [], "la regla debe ir dentro de body.report-printing")
        self.assertIn("body.report-printing > :not(#comparison-report-print)", css)

    def test_app_builds_a_document_and_prints_it_through_its_own_function(self):
        js = self.leer("app.js")
        for nombre in ("function buildReceiptDocument", "function mountReceiptDocument",
                       "function printReceiptDocument", "function clearReceiptDocument"):
            self.assertIn(nombre, js)
        self.assertIn("printReceiptDocument()", js)
        self.assertNotIn('"Imprimir justificante HTML", () => window.print()', js)
        for seccion in ("Datos del ejercicio", "Producto de referencia", "Condiciones documentadas",
                        "Importe imaginado", "Lo que este documento no acredita"):
            self.assertIn(seccion, js)


if __name__ == "__main__":
    unittest.main()
