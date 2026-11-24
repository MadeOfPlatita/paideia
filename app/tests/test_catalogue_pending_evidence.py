"""Cuando la ficha está pendiente se dice, en vez de una excusa genérica.

Medido en producción: «¿cuál es el TER del ETF de iShares Core MSCI Europe?»
encontraba el producto (ETF-01), pero su ficha tiene `conditions: 0` y
`conditions_state: pending`. La respuesta era la nota fija «No repito cifras en
prosa: las tasas y comisiones solo valen si salen citadas de la ficha», que suena
a política de estilo y no explica que el dato simplemente no está transcrito.

Ahora se nombra el producto y el motivo. Sigue sin inventar la cifra.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catalogue_answer import (  # noqa: E402
    compose_catalogue_answer,
    pending_evidence_answer,
)

PENDIENTE = {"used": True, "products": [{
    "id": "ETF-01",
    "name": "iShares Core MSCI Europe UCITS ETF EUR (Acc)",
    "issuer": "iShares",
    "conditions": [],
    "conditions_state": "pending",
}]}

CON_DATOS = {"used": True, "products": [{
    "id": "DEP-EBN-12",
    "name": "Depósito Nuevo Ahorro 12 meses",
    "issuer": "EBN Banco",
    "conditions": [{"metric": "annual_rate_percent", "state": "known",
                    "value": "3.1", "unit": "PERCENT",
                    "sources": [{"url": "https://www.ebnbanco.com/x"}]}],
}]}


def texto_pendiente():
    """La composición como cadena, fallando claro si no compone nada."""
    texto = pending_evidence_answer(PENDIENTE)
    assert texto is not None, "debía explicar la ficha pendiente y no lo hizo"
    return texto


class PendingEvidenceTests(unittest.TestCase):
    def test_a_pending_product_is_named_with_its_reason(self):
        texto = texto_pendiente()
        self.assertIn("iShares Core MSCI Europe", texto)
        self.assertIn("no tiene las condiciones transcritas", texto)
        self.assertIn("no invento el dato", texto)

    def test_it_never_invents_a_figure(self):
        texto = texto_pendiente()
        self.assertNotIn("TER:", texto)
        self.assertNotIn("%", texto)

    def test_it_does_not_fire_when_there_are_conditions(self):
        self.assertIsNone(pending_evidence_answer(CON_DATOS))

    def test_a_product_with_conditions_uses_the_normal_composition(self):
        texto = compose_catalogue_answer(CON_DATOS)
        assert texto is not None, "debía componer la respuesta con el dato conocido"
        self.assertIn("3,10 %", texto)
        self.assertIn("https://www.ebnbanco.com/x", texto)

    def test_without_catalogue_used_there_is_no_answer(self):
        self.assertIsNone(pending_evidence_answer({"used": False, "products": []}))
        self.assertIsNone(pending_evidence_answer(None))


if __name__ == "__main__":
    unittest.main()
