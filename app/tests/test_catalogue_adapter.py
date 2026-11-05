import unittest

from catalogue_adapter import CatalogueWithConditions
from pai_tools import ConditionsUnavailable


class FakeRepository:
    def list_products(self, q=None, family=None):
        if q:
            return []
        return [{
            "id": "DEP-01", "name": "Depósito Tú+", "family": "deposito",
            "issuer": "Renault Bank", "isin": None, "identity_state": "verified",
            "primary_url": "https://example.test/a", "as_of": None,
            "publication_ready": False, "conditions_state": "pending",
            "conflicts": [], "unknown_fields": [],
        }]

    def get_product(self, product_id):
        return None


class FakeConditions:
    def describe(self):
        return {"products": [{
            "product_id": "DEP-EBN-12", "family": "deposito",
            "display_name": "Depósito Nuevo Ahorro 12 meses",
            "provider": "EBN Banco", "identity_state": "verified",
            "conditions": [{
                "metric": "annual_rate_percent", "state": "known", "value": "3.1",
                "unit": "PERCENT", "reason": "CURATED_OFFICIAL", "source_ids": ["1"],
                "effective_to": None, "notes": [],
            }],
            "source": {"url": "https://example.test/ebn", "retrieved_at": "2026-11-03"},
        }]}

    def catalogue_extras(self, q=None, family=None):
        return [{
            "id": "DEP-EBN-12", "name": "Depósito Nuevo Ahorro 12 meses",
            "family": "deposito", "issuer": "EBN Banco", "isin": None,
            "identity_state": "verified", "primary_url": "https://example.test/ebn",
            "as_of": "2026-11-03", "publication_ready": False, "conditions_state": "pending",
            "conflicts": [], "unknown_fields": [],
        }]


class AdapterTests(unittest.TestCase):
    def adapter(self):
        return CatalogueWithConditions(FakeRepository(), FakeConditions())

    def test_merges_documented_products(self):
        items = self.adapter().list_products(family="deposito")
        self.assertEqual([item["id"] for item in items], ["DEP-01", "DEP-EBN-12"])

    def test_query_matches_issuer_without_accents(self):
        items = self.adapter().list_products(q="ebn")
        self.assertEqual([item["id"] for item in items], ["DEP-EBN-12"])

    def test_query_ignores_accents(self):
        items = self.adapter().list_products(q="deposito nuevo")
        self.assertEqual([item["id"] for item in items], ["DEP-EBN-12"])

    def test_a_query_with_two_issuers_does_not_invent_a_match(self):
        # Toda palabra de la consulta debe aparecer: «Self Bank» no esta en la ficha
        # de EBN, asi que no se devuelve como si lo estuviera.
        items = self.adapter().list_products(q="EBN y Self Bank")
        self.assertEqual(items, [])

    def test_conditions_are_attached_to_the_product(self):
        items = self.adapter().list_products(family="deposito")
        ebn = [item for item in items if item["id"] == "DEP-EBN-12"][0]
        self.assertEqual([(c["metric"], c["value"]) for c in ebn["conditions"]],
                         [("annual_rate_percent", "3.1")])

    def test_a_fund_with_twelve_conditions_is_accepted(self):
        # FND-01 y FND-04 declaran doce metricas; el informe debe pasar entero.
        condiciones = [{
            "metric": "metric_%d" % index, "state": "known", "value": "1",
            "unit": "PERCENT", "reason": "CURATED_OFFICIAL", "source_ids": ["1"],
            "effective_to": None, "notes": [],
        } for index in range(12)]

        class DoceCondiciones(FakeConditions):
            def describe(self):
                return {"products": [{
                    "product_id": "FND-01", "family": "fondo",
                    "display_name": "Fondo índice global",
                    "provider": "Ejemplo Gestión", "identity_state": "verified",
                    "conditions": condiciones,
                    "source": {"url": "https://example.test/fnd", "retrieved_at": "2026-11-03"},
                }]}

        report = CatalogueWithConditions(FakeRepository(), DoceCondiciones())._report()
        self.assertEqual(len(report["products"][0]["conditions"]), 12)

    def test_an_absurd_number_of_conditions_still_fails_closed(self):
        demasiadas = [{"metric": "metric_%d" % index} for index in range(33)]

        class Demasiadas(FakeConditions):
            def describe(self):
                return {"products": [{
                    "product_id": "FND-01", "family": "fondo",
                    "display_name": "Fondo índice global",
                    "provider": "Ejemplo Gestión", "identity_state": "verified",
                    "conditions": demasiadas,
                    "source": {"url": "https://example.test/fnd", "retrieved_at": "2026-11-03"},
                }]}

        with self.assertRaises(ConditionsUnavailable):
            CatalogueWithConditions(FakeRepository(), Demasiadas())._report()

    def test_plural_query_matches_even_if_the_repository_would_not(self):
        class RepositorioEstricto:
            def list_products(self, q=None, family=None):
                productos = [{
                    "id": "DEP-01", "name": "Depósito Tú+", "family": "deposito",
                    "issuer": "Renault Bank", "isin": None, "identity_state": "verified",
                    "primary_url": "https://example.test/a", "as_of": None,
                    "publication_ready": False, "conditions_state": "pending",
                    "conflicts": [], "unknown_fields": [],
                }]
                if q:
                    return [p for p in productos if q.casefold() in p["name"].casefold()]
                return productos

            def get_product(self, product_id):
                return None

        items = CatalogueWithConditions(RepositorioEstricto(), FakeConditions()).list_products(q="depósitos")
        self.assertIn("DEP-01", [item["id"] for item in items])

    def test_a_family_word_finds_products_that_do_not_name_it(self):
        class RepositorioSinLaPalabra:
            def list_products(self, q=None, family=None):
                return [{
                    "id": "FND-01", "name": "Vanguard Global Stock", "family": "fondo_tradicional",
                    "issuer": "Vanguard", "isin": None, "identity_state": "verified",
                    "primary_url": "https://example.test/f", "as_of": None,
                    "publication_ready": False, "conditions_state": "pending",
                    "conflicts": [], "unknown_fields": [],
                }]

            def get_product(self, product_id):
                return None

        items = CatalogueWithConditions(RepositorioSinLaPalabra(), FakeConditions()).list_products(q="fondos")
        self.assertIn("FND-01", [item["id"] for item in items])

    def test_detail_falls_back_to_documented_product(self):
        product = self.adapter().get_product("DEP-EBN-12")
        self.assertEqual(product["issuer"], "EBN Banco")
        self.assertEqual(product["conditions"][0]["value"], "3.1")


if __name__ == "__main__":
    unittest.main()
