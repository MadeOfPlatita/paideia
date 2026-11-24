"""Un producto documentado no puede presentarse como «condiciones desconocidas».

BUG REAL medido en produccion. La respuesta del chat decia, en el mismo bloque:

    Depósito Sinycon Plus (DEP-04)
    Condiciones desconocidas; atribución parcial
    Tasa anual (TAE): 2,4 %

Es decir: se mostraba la TAE y a la vez se declaraba que no se sabia nada de sus
condiciones. Cuatro contradicciones en una respuesta.

Se encontraron CUATRO causas encadenadas; cada una sola bastaba para degradar la
ficha entera a `conditions_unknown`:

  1. El bucle del DTO contaba como «ilegible» toda metrica fuera de la lista
     blanca del chat. Pero hay 34 metricas documentadas y el chat solo publica
     tasa y plazo: las que no viajan no estan rotas.
  2. `Decimal(value)` se aplicaba a CUALQUIER condicion. Las clausulas de texto
     («cancelable en cualquier momento», «al vencimiento») no son numeros y se
     daban por invalidas.
  3. El tope de 32 caracteres rechazaba clausulas legitimas y largas
     («Varios titulares, documento firmado por todos»).
  4. La regla de «documentada» exigia una fuente ENLAZADA EN CADA CONDICION, pero
     el adaptador no las pone ahi: la fuente vive en el producto (`primary_url` /
     `source`). Con `sources: None` en las 14 condiciones, el producto se daba por
     desconocido.

La correccion de la 4 no inventa atribuciones: la condicion hereda la fuente del
producto que la documenta, que es la misma procedencia.

Medido despues en los 5 productos de referencia:
    DEP-04      documented              14 condiciones, 14 con fuente
    DEP-EBN-12  documented              15 condiciones, 15 con fuente
    ETF-01      documented              28 condiciones, 28 con fuente
    ACC-01      documented_not_current  11 condiciones (vencida de verdad)
    DEP-01      documented_not_current  14 condiciones (vencida de verdad)
"""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import app  # noqa: E402
from catalogue_adapter import CatalogueWithConditions  # noqa: E402
from conditions_service import ConditionsService  # noqa: E402
from pai_runtime import ToolChatRunner  # noqa: E402

# Productos con ficha transcrita: su tasa y su plazo son datos publicados.
DOCUMENTADOS = ("DEP-04", "DEP-EBN-12", "ETF-01")


def _catalogo():
    return CatalogueWithConditions(app.SnapshotRepository(), ConditionsService())


class DocumentedProductProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo = _catalogo()

    def _dto(self, product_id):
        producto = self.catalogo.get_product_detail(product_id)
        self.assertIsNotNone(producto, f"{product_id} debe existir en el catalogo")
        dto = ToolChatRunner._evidence_product(producto)
        self.assertIsNotNone(dto, f"{product_id} debe proyectarse")
        return dto

    def test_a_documented_product_is_not_reported_as_unknown(self):
        for product_id in DOCUMENTADOS:
            with self.subTest(product=product_id):
                dto = self._dto(product_id)
                self.assertEqual(dto["conditions_state"], "documented",
                                 f"{product_id} tiene condiciones y no puede declararse desconocido")
                self.assertNotEqual(dto.get("conditions_state_reasons"), None)

    def test_its_conditions_travel_with_a_source(self):
        # Sin fuente enlazada no hay dato publicable: la condicion hereda la del
        # producto, pero tiene que llevarla.
        for product_id in DOCUMENTADOS:
            with self.subTest(product=product_id):
                condiciones = self._dto(product_id)["conditions"]
                self.assertGreater(len(condiciones), 0)
                sin_fuente = [c["metric"] for c in condiciones if not c.get("sources")]
                self.assertEqual(sin_fuente, [],
                                 f"{product_id}: condiciones sin fuente: {sin_fuente}")

    def test_text_clauses_are_conditions_not_invalid_data(self):
        # «Varios titulares, documento firmado por todos» es una clausula del
        # contrato, no un dato corrupto.
        dto = self._dto("DEP-04")
        metricas = {c["metric"] for c in dto["conditions"]}
        self.assertIn("annual_rate_percent", metricas)
        self.assertIn("ownership", metricas,
                      "la clausula de titularidad debe viajar como condicion")

    def test_the_rate_and_the_state_agree(self):
        # El sintoma exacto: TAE visible y estado «desconocido» a la vez.
        dto = self._dto("DEP-04")
        tasa = [c for c in dto["conditions"] if c["metric"] == "annual_rate_percent"]
        self.assertEqual(len(tasa), 1)
        self.assertEqual(tasa[0]["value"], "2.4")
        self.assertEqual(dto["conditions_state"], "documented",
                         "si la TAE se muestra, el estado no puede decir «desconocidas»")

    def test_an_expired_product_stays_not_current(self):
        # La correccion no puede convertir una oferta vencida en vigente.
        for product_id in ("ACC-01", "DEP-01"):
            with self.subTest(product=product_id):
                self.assertEqual(self._dto(product_id)["conditions_state"],
                                 "documented_not_current")


if __name__ == "__main__":
    unittest.main()
