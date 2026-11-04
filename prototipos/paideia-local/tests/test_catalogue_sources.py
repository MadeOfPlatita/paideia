"""Registro de fuentes: los ids numéricos del snapshot deben resolverse a URL.

Sin registro, la app no puede enlazar la fuente de una tasa y no debe presentarla
como dato trazable. Con registro, todo id tiene que resolver o la condición cae a
`unknown` con motivo `SOURCE_UNRESOLVED` (fail closed).
"""

import unittest
from datetime import date

from catalogue_conditions import derive, index_sources, resolve_sources

TODAY = date(2026, 11, 3)

LEDGER = {
    "version": 1,
    "sources": [
        {"id": 1, "url": "https://example.invalid/legal.pdf",
         "title": "Banco — información precontractual", "accessed": "2026-10-27"},
        {"id": 2, "url": "https://example.invalid/cuenta", "title": "Banco — cuenta"},
        {"id": 3, "url": "no-es-una-url", "title": "rota"},
    ],
}


def candidate(**overrides):
    base = {
        "candidate_id": "T-1",
        "family": "deposito",
        "candidate_state": "verified",
        "name_literal": "Producto de prueba",
        "available_fields": {
            "rate": {"value_literal": "2,61 % TAE", "source_ids": [1]},
        },
        "dates": {"checked_at": "2026-11-01"},
        "conflicts": [],
    }
    base.update(overrides)
    return base


def condition_of(item, sources):
    report = derive({"candidates": [item]}, today=TODAY, sources=sources)
    return report["products"][0]["conditions"][0]


class RegistryTests(unittest.TestCase):
    def test_numeric_ids_resolve_to_urls_with_title(self):
        condition = condition_of(candidate(), LEDGER)
        self.assertEqual(condition["state"], "known")
        self.assertEqual(condition["source_ids"], ["https://example.invalid/legal.pdf"])
        self.assertEqual(condition["source_refs"],
                         [{"url": "https://example.invalid/legal.pdf",
                           "title": "Banco — información precontractual",
                           "accessed": "2026-10-27"}])
        self.assertTrue(condition["reason"].startswith("DOCUMENTED_"))

    def test_ids_without_url_are_not_indexed(self):
        index = index_sources(LEDGER)
        self.assertIn("1", index)
        self.assertNotIn("3", index)

    def test_empty_registry_fails_closed(self):
        condition = condition_of(candidate(), {"sources": []})
        self.assertEqual(condition["state"], "unknown")
        self.assertEqual(condition["reason"], "SOURCE_UNRESOLVED")
        self.assertIsNone(condition["value"])
        self.assertEqual(condition["source_ids"], [])
        self.assertTrue(any("1" in note for note in condition["notes"]))

    def test_partially_resolved_ids_fail_closed(self):
        item = candidate(available_fields={
            "rate": {"value_literal": "2,61 % TAE", "source_ids": [1, 99]},
        })
        condition = condition_of(item, LEDGER)
        self.assertEqual(condition["state"], "unknown")
        self.assertEqual(condition["reason"], "SOURCE_UNRESOLVED")
        self.assertIsNone(condition["value"])
        # La URL que sí resuelve se conserva para auditoría, pero el dato no se publica.
        self.assertEqual(condition["source_ids"], ["https://example.invalid/legal.pdf"])

    def test_without_registry_legacy_passthrough(self):
        condition = condition_of(candidate(), None)
        self.assertEqual(condition["state"], "known")
        self.assertEqual(condition["source_ids"], ["1"])

    def test_url_ids_pass_through_registry(self):
        urls, refs, unresolved = resolve_sources(("https://example.invalid/x",), {})
        self.assertEqual(urls, ("https://example.invalid/x",))
        self.assertEqual(refs, (("https://example.invalid/x", None, None),))
        self.assertEqual(unresolved, ())

    def test_report_declares_registry_state(self):
        with_registry = derive({"candidates": [candidate()]}, today=TODAY, sources=LEDGER)
        without = derive({"candidates": [candidate()]}, today=TODAY)
        self.assertEqual(with_registry["source_registry"], "applied")
        self.assertEqual(without["source_registry"], "not_provided")


if __name__ == "__main__":
    unittest.main()
