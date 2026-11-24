"""La búsqueda del catálogo debe encontrar lo que un estudiante pregunta.

Dos fallos medidos en producción:

1. «¿Qué letras del Tesoro tienes?» devolvía CERO productos y acababa en 502. El
   catálogo dice «Letra del Tesoro» en singular y la búsqueda era subcadena
   literal: `"letras" in "letra del tesoro"` es False.
2. Al corregirlo con un OR entre términos, «deposito EBN» devolvía los cuatro
   depósitos: bastaba con que apareciera «deposito». Quien nombra un banco
   espera ese banco.

Ahora se exige que aparezcan todos los términos y, solo si eso no deja nada, se
admite la coincidencia parcial como red de rescate.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import SnapshotRepository  # noqa: E402


class CatalogueSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = SnapshotRepository()

    def ids(self, consulta):
        return [p["id"] for p in self.repo.list_products(q=consulta)]

    def test_plural_query_finds_the_singular_product_name(self):
        # «letras» no aparece literal en «Letra del Tesoro».
        self.assertEqual(self.ids("letras del Tesoro"),
                         ["DEBT-01", "DEBT-02", "DEBT-03", "DEBT-04"])

    def test_plural_family_finds_all_of_them(self):
        self.assertEqual(len(self.ids("depositos")), 4)
        self.assertEqual(len(self.ids("cuentas remuneradas")), 4)

    def test_naming_a_bank_does_not_return_the_whole_family(self):
        # Antes: los cuatro depósitos. Un usuario que dice EBN espera EBN.
        self.assertEqual(self.ids("deposito EBN"), ["DEP-04"])
        self.assertEqual(self.ids("cuenta Openbank"), ["ACC-03"])

    def test_specific_brands_still_match(self):
        for marca, esperado in (("EBN", "DEP-04"), ("VanEck", "ETF-04"), ("Olea", "FND-02")):
            self.assertIn(esperado, self.ids(marca))

    def test_a_query_with_no_match_returns_nothing(self):
        self.assertEqual(self.ids("hipoteca inversa vitalicia"), [])

    def test_everything_is_found_without_a_query(self):
        self.assertEqual(len(self.repo.list_products()), self.repo.count)


if __name__ == "__main__":
    unittest.main()
