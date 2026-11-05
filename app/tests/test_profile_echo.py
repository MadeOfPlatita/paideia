"""El perfil autorizado deja huella visible en la respuesta (H4)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from chat_context import profile_echo  # noqa: E402

CORTO = {
    "respuestas.horizonte": {"estado": "declarado", "valor": "6_12_meses"},
    "respuestas.objetivo": {"estado": "declarado", "valor": "colchon_imprevistos"},
    "detalle_economico.importe_objetivo": {
        "estado": "declarado", "valor": {"min_eur": "500", "max_eur": "2000", "moneda": "EUR"}},
    "detalle_economico.colchon_liquido": {
        "estado": "declarado", "valor": {"min_eur": "500", "max_eur": "2000", "moneda": "EUR"}},
}
LARGO = {
    "respuestas.horizonte": {"estado": "declarado", "valor": "mas_3_anos"},
    "respuestas.objetivo": {"estado": "declarado", "valor": "ahorro_largo_plazo"},
    "detalle_economico.importe_objetivo": {
        "estado": "declarado", "valor": {"min_eur": "20000", "max_eur": "50000", "moneda": "EUR"}},
    "detalle_economico.colchon_liquido": {
        "estado": "declarado", "valor": {"min_eur": "20000", "max_eur": "50000", "moneda": "EUR"}},
}


class ProfileEchoTests(unittest.TestCase):
    def test_echo_uses_the_declared_values_and_local_currency_format(self):
        linea = profile_echo(CORTO)
        self.assertIn("entre 6 y 12 meses", linea)
        self.assertIn("colchón para imprevistos", linea)
        self.assertIn("500–2.000 €", linea)
        self.assertTrue(linea.startswith("Según el mapa que tú has autorizado"))

    def test_two_profiles_produce_different_sentences(self):
        self.assertNotEqual(profile_echo(CORTO), profile_echo(LARGO))
        self.assertIn("más de 3 años", profile_echo(LARGO))
        self.assertIn("20.000–50.000 €", profile_echo(LARGO))

    def test_states_without_data_are_silent(self):
        campos = {
            "respuestas.horizonte": {"estado": "no_se"},
            "respuestas.objetivo": {"estado": "omitido"},
            "detalle_economico.importe_objetivo": {"estado": "sin_preguntar"},
        }
        self.assertEqual(profile_echo(campos), "")

    def test_only_declared_fields_travel(self):
        campos = dict(CORTO)
        campos["detalle_economico.importe_objetivo"] = {"estado": "no_se"}
        linea = profile_echo(campos)
        self.assertIn("entre 6 y 12 meses", linea)
        self.assertNotIn("importe objetivo", linea)


if __name__ == "__main__":
    unittest.main()


class CatalogueNoteTests(unittest.TestCase):
    """H5: el estado real del catálogo se dice con claridad y sin tasas nuevas."""

    def test_the_note_states_that_no_card_is_approved_for_publication(self):
        from backend_services import CATALOGUE_WITHHELD_NOTE

        self.assertIn("Ninguna ficha está aprobada para publicación", CATALOGUE_WITHHELD_NOTE)
        self.assertIn("borradores internos", CATALOGUE_WITHHELD_NOTE)
        self.assertNotIn("%", CATALOGUE_WITHHELD_NOTE)

    def test_publication_ready_is_a_configuration_rule_not_a_data_field(self):
        """H5: ningún camino del adaptador publica; es una regla de código, no un dato."""
        from pathlib import Path
        import json
        import re

        base = Path(__file__).resolve().parents[1]
        datos = json.loads((base / "data" / "condiciones.json").read_text(encoding="utf-8"))
        claves = set()
        for registro in datos["records"]:
            claves.update(registro)
        self.assertNotIn("publication_ready", claves)

        fuente = (base / "catalogue_adapter.py").read_text(encoding="utf-8")
        apariciones = re.findall(r'"publication_ready":\s*([A-Za-z]+)', fuente)
        self.assertTrue(apariciones)
        self.assertTrue(all(valor == "False" for valor in apariciones), apariciones)
