"""El catálogo real se puede proyectar al modelo sin romper el chat.

La ampliación a 341 condiciones introdujo métricas nuevas con unidades y valores
que la proyección no conocía: cualquier búsqueda devolvía REPOSITORY_ERROR y Pai
contestaba con un error. Esta prueba recorre todas las condiciones servidas.
"""

import unittest
from pathlib import Path

import app
from backend_services import CatalogueComparisonService
from catalogue_adapter import CatalogueWithConditions
from conditions_service import ConditionsService
from pai_tools import (CONDITION_STATES, PROJECTED_METRIC_UNITS,
                       _valid_projected_value, ToolDispatcher)


class CatalogueProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servicio = ConditionsService()
        cls.dispatcher = ToolDispatcher(
            CatalogueWithConditions(app.SnapshotRepository(), cls.servicio),
            CatalogueComparisonService(),
        )

    def test_every_served_condition_matches_the_projection_contract(self):
        fallos = []
        for entrada in self.servicio.describe()["products"]:
            for condicion in entrada["conditions"]:
                metric = condicion["metric"]
                unit = condicion["unit"]
                value = condicion["value"]
                state = condicion["state"]
                if (PROJECTED_METRIC_UNITS.get(metric) != unit
                        or state not in CONDITION_STATES
                        or (value is not None and not _valid_projected_value(unit, value))
                        or (state == "known" and value is None)):
                    fallos.append((entrada["product_id"], metric, unit, value, state))
        self.assertEqual(fallos, [])

    def test_search_returns_the_whole_catalogue(self):
        resultado = self.dispatcher.dispatch("search_products", {"query": "", "family": None, "limit": 20})
        self.assertEqual(resultado["status"], "ok", resultado.get("error"))
        self.assertEqual(len(resultado["data"]["items"]), 20)

    def test_a_product_with_more_than_thirty_two_conditions_is_served(self):
        detalle = self.dispatcher.dispatch("get_product_detail", {"product_id": "FND-02"})
        self.assertEqual(detalle["status"], "ok", detalle.get("error"))
        condiciones = detalle["data"]["product"]["conditions"]
        self.assertGreater(len(condiciones), 32)

    def test_values_are_stored_as_text_for_the_projection(self):
        import json
        ruta = Path(__file__).resolve().parents[1] / "data" / "condiciones.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        malos = [(r["candidate_id"], c["metric"]) for r in datos["records"]
                 for c in r.get("documented") or []
                 if isinstance(c.get("value"), (int, float, bool))]
        self.assertEqual(malos, [])


if __name__ == "__main__":
    unittest.main()
