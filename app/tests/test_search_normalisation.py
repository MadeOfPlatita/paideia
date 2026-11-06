"""La búsqueda acepta cómo escriben los modelos, no solo la clave exacta."""

import unittest

import app
from backend_services import CatalogueComparisonService
from catalogue_adapter import CatalogueWithConditions
from conditions_service import ConditionsService
from pai_tools import ToolDispatcher


class SearchNormalisationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dispatcher = ToolDispatcher(
            CatalogueWithConditions(app.SnapshotRepository(), ConditionsService()),
            CatalogueComparisonService(),
        )

    def buscar(self, **argumentos):
        resultado = self.dispatcher.dispatch("search_products", argumentos)
        self.assertEqual(resultado["status"], "ok", resultado.get("error"))
        return resultado["data"]["items"]

    def test_plural_and_accent_are_understood(self):
        self.assertEqual(len(self.buscar(family="depósitos", limit=20)), 6)
        self.assertEqual(len(self.buscar(family="cuentas", limit=20)), 4)
        self.assertEqual(len(self.buscar(family="ETFs", limit=20)), 4)

    def test_wildcard_query_is_treated_as_no_filter(self):
        self.assertEqual(len(self.buscar(query="*", limit=20)), 20)
        self.assertEqual(len(self.buscar(query="%", limit=20)), 20)

    def test_an_unknown_family_is_still_rejected(self):
        resultado = self.dispatcher.dispatch("search_products", {"query": "", "family": "banco", "limit": 20})
        self.assertEqual(resultado["status"], "error")
        self.assertEqual(resultado["error"]["code"], "INVALID_ARGUMENTS")


if __name__ == "__main__":
    unittest.main()
