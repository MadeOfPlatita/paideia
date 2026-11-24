"""Toda familia real del catálogo debe poder pedirse por la herramienta.

Fallo medido en producción: «¿qué letras del Tesoro tienes?» acababa en 502
CHAT_TOOL_ERROR. El modelo pedía `family: "letra_deuda_publica"` —el nombre
canónico, el valor real de `family` en el catálogo— y la herramienta lo rechazaba
con INVALID_ARGUMENTS porque el mapa de alias tenía «letra», «letras»,
«deuda_publica» y «tesoro», pero no el nombre canónico.

La prueba no comprueba una lista escrita a mano: recorre las familias que el
catálogo tiene de verdad, así que cubre las que se añadan en el futuro.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import SnapshotRepository  # noqa: E402
from pai_tools import ToolDispatcher  # noqa: E402
from catalogue_adapter import CatalogueWithConditions  # noqa: E402
from conditions_service import ConditionsService  # noqa: E402
from backend_services import CatalogueComparisonService  # noqa: E402


def dispatcher():
    return ToolDispatcher(
        CatalogueWithConditions(SnapshotRepository(), ConditionsService()),
        CatalogueComparisonService(),
    )


class FamilyAliasTests(unittest.TestCase):
    def test_every_catalogue_family_is_accepted_by_the_tool(self):
        reales = sorted({p["family"] for p in SnapshotRepository().list_products()})
        self.assertTrue(reales, "el catálogo no debería estar vacío")
        for familia in reales:
            with self.subTest(familia=familia):
                respuesta = dispatcher().dispatch("search_products", {"family": familia})
                self.assertEqual(respuesta["status"], "ok",
                                 f"la familia {familia} se rechaza con {respuesta.get('error')}")
                self.assertGreater((respuesta.get("data") or {}).get("count", 0), 0,
                                   f"la familia {familia} no devolvió ningún producto")

    def test_plural_and_spanish_aliases_still_work(self):
        for alias in ("letras", "letras_del_tesoro", "tesoro", "deuda_publica",
                      "depositos", "cuentas", "etfs", "fondos"):
            with self.subTest(alias=alias):
                respuesta = dispatcher().dispatch("search_products", {"family": alias})
                self.assertEqual(respuesta["status"], "ok", f"alias {alias} rechazado")

    def test_an_invented_family_is_still_rejected(self):
        respuesta = dispatcher().dispatch("search_products", {"family": "producto_inventado"})
        self.assertEqual(respuesta["status"], "error")
        self.assertEqual(respuesta["error"]["code"], "INVALID_ARGUMENTS")

    def test_query_and_family_together_work(self):
        # Es la forma exacta que envía el modelo: los tres campos a la vez.
        respuesta = dispatcher().dispatch(
            "search_products",
            {"query": "letras del Tesoro", "family": "letra_deuda_publica", "limit": 20})
        self.assertEqual(respuesta["status"], "ok")
        self.assertEqual((respuesta.get("data") or {}).get("count"), 4)


if __name__ == "__main__":
    unittest.main()
