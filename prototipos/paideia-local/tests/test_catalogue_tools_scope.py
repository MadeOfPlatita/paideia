import unittest

from backend_services import LocalChatService
from pai_tools import ToolDispatcher


class FakeRepository:
    def list_products(self, q=None, family=None):
        return []

    def get_product(self, product_id):
        return None


class ScopeTests(unittest.TestCase):
    def service(self, scope, approved=False):
        return LocalChatService(
            provider=object(),
            enabled=True,
            tools_enabled=True,
            tools_scope=scope,
            catalogue_usage_approved=approved,
            dispatcher=ToolDispatcher(FakeRepository(), None),
        )

    def names(self, service):
        return {item["function"]["name"] for item in service._dispatcher.definitions()}

    def test_catalogue_read_exposes_only_search_detail_and_calculator(self):
        service = self.service("catalogue_read", approved=True)
        self.assertEqual(self.names(service), {"search_products", "get_product_detail", "calculate_scenario"})

    def test_catalogue_read_refuses_comparison_and_bulk_sources(self):
        service = self.service("catalogue_read", approved=True)
        with self.assertRaises(ValueError):
            service._dispatcher.dispatch("compare_products", {"product_ids": ["A-1", "A-2"], "criterion": None})
        with self.assertRaises(ValueError):
            service._dispatcher.dispatch("get_sources", {"product_ids": ["A-1"]})

    def test_calculator_scope_stays_narrow(self):
        service = self.service("calculator_only")
        self.assertEqual(self.names(service), {"calculate_scenario"})

    def test_catalogue_read_is_a_known_scope(self):
        with self.assertRaises(ValueError):
            self.service("catalogue_everything")

    def test_unapproved_catalogue_scope_is_rejected_at_request_time(self):
        service = self.service("catalogue", approved=False)
        self.assertEqual(service._catalogue_usage_approved, False)


if __name__ == "__main__":
    unittest.main()
