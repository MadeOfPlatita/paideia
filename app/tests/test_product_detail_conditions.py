"""La ficha debe llegar con sus condiciones, no vacía.

Bug medido en producción: `CatalogueWithConditions` no definía
`get_product_detail`, así que `__getattr__` lo delegaba al repositorio base. Ese
método devuelve la ficha **sin** enriquecer, de modo que la herramienta recibía
`conditions: []` y `conditions_state: pending` aunque el servicio tuviera las
métricas documentadas.

Consecuencia visible: «¿cuál es el TER del ETF de iShares Core MSCI Europe?»
respondía «su ficha todavía no tiene las condiciones transcritas» cuando el TER
del 0,12 % estaba transcrito con su fuente. Y lo mismo con las comisiones de
Olea Neutral (32 métricas) y con el depósito DEP-04 (14).

La prueba compara `get_product` con `get_product_detail`: si divergen, algo está
delegando sin enriquecer, que es exactamente el agujero que tenía.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import SnapshotRepository  # noqa: E402
from conditions_service import ConditionsService  # noqa: E402
from catalogue_adapter import CatalogueWithConditions  # noqa: E402

# Productos cuyas condiciones están transcritas en data/condiciones.json.
TRANSCRITOS = ("ETF-01", "ETF-02", "ETF-03", "ETF-04",
               "FND-01", "FND-02", "FND-03", "FND-04")


class ProductDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = CatalogueWithConditions(SnapshotRepository(), ConditionsService())

    def ficha(self, product_id):
        """La ficha, fallando claro si no existe (así el test dice por qué)."""
        detalle = self.adapter.get_product_detail(product_id)
        assert detalle is not None, f"{product_id} debería existir en el catálogo"
        return detalle

    def test_detail_matches_enriched_product(self):
        for product_id in TRANSCRITOS:
            with self.subTest(product_id=product_id):
                detalle = self.ficha(product_id)
                enriquecido = self.adapter.get_product(product_id)
                assert enriquecido is not None
                self.assertEqual(detalle.get("conditions"), enriquecido.get("conditions"),
                                 "la ficha no puede venir sin las condiciones del producto")

    def test_transcribed_products_are_documented_not_pending(self):
        for product_id in TRANSCRITOS:
            with self.subTest(product_id=product_id):
                detalle = self.ficha(product_id)
                self.assertGreater(len(detalle.get("conditions") or []), 0,
                                   f"{product_id} tiene condiciones transcritas")
                self.assertEqual(detalle.get("conditions_state"), "documented",
                                 f"{product_id} debería figurar como documentado")

    def test_the_etf_ter_is_reachable(self):
        # Es el caso que reportó el usuario: el TER del ETF de iShares.
        detalle = self.ficha("ETF-01")
        ter = [c for c in detalle["conditions"] if c.get("metric") == "ter_percent"]
        self.assertTrue(ter, "el TER debería estar entre las condiciones de ETF-01")
        self.assertEqual(ter[0].get("state"), "known")
        self.assertEqual(ter[0].get("value"), "0.12")

    def test_a_missing_product_detail_is_none(self):
        self.assertIsNone(self.adapter.get_product_detail("NO-EXISTE-404"))


if __name__ == "__main__":
    unittest.main()
