import unittest

from catalogue_adapter import CatalogueWithConditions


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

    def test_query_lists_both_issuers(self):
        items = self.adapter().list_products(q="EBN y Self Bank")
        self.assertEqual([item["id"] for item in items], ["DEP-EBN-12"])

    def test_conditions_are_attached_to_the_product(self):
        items = self.adapter().list_products(family="deposito")
        ebn = [item for item in items if item["id"] == "DEP-EBN-12"][0]
        self.assertEqual([(c["metric"], c["value"]) for c in ebn["conditions"]],
                         [("annual_rate_percent", "3.1")])

    def test_detail_falls_back_to_documented_product(self):
        product = self.adapter().get_product("DEP-EBN-12")
        self.assertEqual(product["issuer"], "EBN Banco")
        self.assertEqual(product["conditions"][0]["value"], "3.1")


if __name__ == "__main__":
    unittest.main()
