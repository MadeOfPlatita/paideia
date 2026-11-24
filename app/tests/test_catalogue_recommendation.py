"""Contrato de la respuesta de catálogo: recomendar, no volcar la ficha.

El uso real lo dejó claro: a «dame los productos de depósito» la app devolvía seis
fichas con familia, emisor, identidad, estado, atribución, ocho condiciones cada
una, su clase de fuente, su vigencia y sus URLs. Un muro de texto que no se puede
leer y que no responde. Lo que se espera de un asesor es «para esto te recomiendo
este, y por esto», no un copy-paste del catálogo.

Estas pruebas fijan el contrato nuevo para que no se vuelva atrás por accidente:
  1. Se recomienda UN producto y se dice por qué.
  2. Como mucho tres datos clave.
  3. Los demás se mencionan por nombre, sin sus condiciones.
  4. Una oferta vencida no se recomienda.
  5. A un listado se contesta con lo que hay, no con una elección inventada.
  6. Nada de cifras inventadas: solo condiciones con estado `known`.
"""

import unittest

from catalogue_answer import compose_catalogue_answer, pending_evidence_answer


def _condition(metric, value, *, state="known", unit="PERCENT", url=None):
    condition = {"metric": metric, "value": value, "state": state, "unit": unit}
    if url:
        condition["sources"] = [{"url": url, "class": "official"}]
    return condition


def _product(pid, name, issuer="Banco Sintético", state="documented", conditions=None):
    return {
        "id": pid,
        "name": name,
        "issuer": issuer,
        "conditions_state": state,
        "conditions": conditions or [],
    }


def _catalogue(*products):
    return {"used": True, "products": list(products)}


class RecommendationsTest(unittest.TestCase):
    def test_a_rate_question_picks_the_best_paying_product_and_gives_the_reason(self):
        catalogo = _catalogue(
            _product("DEP-1", "Depósito Uno", "Banco A", conditions=[
                _condition("annual_rate_percent", "2.4", url="https://a.example/x")]),
            _product("DEP-2", "Depósito Dos", "Banco B", conditions=[
                _condition("annual_rate_percent", "3.1", url="https://b.example/y")]),
        )
        texto = compose_catalogue_answer(catalogo, question="¿Qué TAE tiene el depósito de Banco B?")
        assert texto is not None
        self.assertIn("Depósito Dos", texto)
        self.assertIn("3,1", texto)
        # El motivo: por qué ese y no otro.
        self.assertIn("mejor remunerado", texto)

    def test_it_gives_at_most_three_key_facts_not_the_whole_file(self):
        condiciones = [
            _condition("annual_rate_percent", "3.1"),
            _condition("term_months", "12", unit="MONTHS"),
            _condition("minimum_eur", "5000", unit="EUR"),
            _condition("withholding_percent", "19"),
            _condition("isin", "ES0000000001", unit="TEXT"),
            _condition("manager", "Gestora Sintética", unit="TEXT"),
        ]
        texto = compose_catalogue_answer(
            _catalogue(_product("DEP-1", "Depósito Uno", conditions=condiciones)),
            question="¿Qué TAE tiene?")
        assert texto is not None
        # Tres datos como mucho: el cuarto (la retención) no debe aparecer.
        self.assertIn("TAE", texto)
        self.assertIn("plazo", texto)
        self.assertNotIn("Gestora Sintética", texto)

    def test_the_other_products_are_mentioned_by_name_only(self):
        catalogo = _catalogue(
            _product("DEP-1", "Depósito Uno", "Banco A", conditions=[
                _condition("annual_rate_percent", "3.1"),
                _condition("isin", "ES0000000001", unit="TEXT")]),
            _product("DEP-2", "Depósito Dos", "Banco B", conditions=[
                _condition("annual_rate_percent", "2.4"),
                _condition("isin", "ES0000000002", unit="TEXT")]),
        )
        texto = compose_catalogue_answer(catalogo, question="¿Qué TAE tiene el depósito?")
        assert texto is not None
        # El alternativo se nombra…
        self.assertIn("Depósito Dos", texto)
        # …pero sin arrastrar su ficha: su ISIN no se publica.
        self.assertNotIn("ES0000000002", texto)

    def test_a_current_offer_is_preferred_over_an_expired_one(self):
        catalogo = _catalogue(
            _product("DEP-1", "Depósito Vencido", "Banco A", state="documented_not_current",
                     conditions=[_condition("annual_rate_percent", "5.0")]),
            _product("DEP-2", "Depósito Vigente", "Banco B",
                     conditions=[_condition("annual_rate_percent", "2.0")]),
        )
        texto = compose_catalogue_answer(catalogo, question="¿Qué TAE tiene el depósito?")
        assert texto is not None
        # La tasa del vencido es más alta, pero no se puede recomendar.
        self.assertIn("Depósito Vigente", texto)
        self.assertIn("Para lo que preguntas", texto)

    def test_if_every_offer_is_expired_it_says_so_instead_of_recommending_it(self):
        catalogo = _catalogue(
            _product("DEP-1", "Depósito Vencido", "Banco A", state="documented_not_current",
                     conditions=[_condition("annual_rate_percent", "5.0")]),
        )
        texto = compose_catalogue_answer(catalogo, question="¿Qué TAE tiene el depósito?")
        assert texto is not None
        self.assertIn("no vigente", texto)

    def test_a_listing_question_answers_with_what_exists(self):
        catalogo = _catalogue(
            _product("DEP-1", "Depósito Uno", "Banco A",
                     conditions=[_condition("annual_rate_percent", "2.4")]),
            _product("DEP-2", "Depósito Dos", "Banco B",
                     conditions=[_condition("annual_rate_percent", "3.1")]),
        )
        texto = compose_catalogue_answer(catalogo, question="¿Qué productos de depósito hay en el catálogo?")
        assert texto is not None
        # Contesta al listado: los dos nombres, y no una recomendación fingida.
        self.assertIn("Depósito Uno", texto)
        self.assertIn("Depósito Dos", texto)
        self.assertNotIn("el que mejor encaja", texto)

    def test_the_minimum_question_picks_the_most_affordable(self):
        catalogo = _catalogue(
            _product("DEP-1", "Depósito Caro", "Banco A", conditions=[
                _condition("minimum_eur", "5000", unit="EUR")]),
            _product("DEP-2", "Depósito Barato", "Banco B", conditions=[
                _condition("minimum_eur", "500", unit="EUR")]),
        )
        texto = compose_catalogue_answer(catalogo, question="¿Cuál pide menos dinero para empezar?")
        assert texto is not None
        self.assertIn("Depósito Barato", texto)
        self.assertIn("500", texto)

    def test_the_source_url_is_cited_once_not_per_condition(self):
        catalogo = _catalogue(_product("DEP-1", "Depósito Uno", conditions=[
            _condition("annual_rate_percent", "3.1", url="https://a.example/x"),
            _condition("term_months", "12", unit="MONTHS", url="https://a.example/x"),
        ]))
        texto = compose_catalogue_answer(catalogo, question="¿Qué TAE tiene?")
        assert texto is not None
        self.assertEqual(texto.count("https://a.example/x"), 1)

    def test_it_respects_the_issuer_named_in_the_question(self):
        """Fallo medido con el catálogo real: a «el depósito de EBN» se
        recomendaba el de Openbank porque tenía la tasa más alta del conjunto."""
        catalogo = _catalogue(
            _product("DEP-02", "Depósito Open 6 meses", "Openbank", conditions=[
                _condition("annual_rate_percent", "2.75")]),
            _product("DEP-04", "Depósito Sinycon Plus", "EBN Banco", conditions=[
                _condition("annual_rate_percent", "2.4")]),
        )
        texto = compose_catalogue_answer(catalogo, question="¿Qué TAE tiene el depósito de EBN Banco?")
        assert texto is not None
        self.assertIn("Sinycon Plus", texto)
        self.assertNotIn("Depósito Open", texto)

    def test_the_source_is_read_from_source_ids_as_the_real_catalogue_ships_it(self):
        """El catálogo real no trae `sources` sino `source_ids` con las URLs."""
        condicion = {"metric": "annual_rate_percent", "value": "2.4", "state": "known",
                     "unit": "PERCENT", "source_ids": ["https://www.ebnbanco.com/x"],
                     "source_refs": []}
        catalogo = _catalogue(_product("DEP-04", "Depósito Sinycon Plus", "EBN Banco",
                                       conditions=[condicion]))
        texto = compose_catalogue_answer(catalogo, question="¿Qué TAE tiene?")
        assert texto is not None
        self.assertIn("https://www.ebnbanco.com/x", texto)

    def test_a_listing_names_every_product_not_just_the_first_four(self):
        productos = [_product(f"DEP-{i}", f"Depósito {i}", f"Banco {i}",
                              conditions=[_condition("annual_rate_percent", "2.0")])
                     for i in range(6)]
        texto = compose_catalogue_answer(_catalogue(*productos),
                                         question="¿Qué productos de depósito hay?")
        assert texto is not None
        self.assertIn("6 productos", texto)
        for i in range(6):
            self.assertIn(f"Depósito {i}", texto)

    def test_a_compound_risk_scale_is_not_rewritten(self):
        catalogo = _catalogue(_product("DEP-04", "Depósito Uno", conditions=[
            _condition("risk_scale", "1/6", unit="SCALE")]))
        texto = compose_catalogue_answer(catalogo, question="¿Qué riesgo tiene?")
        assert texto is not None
        self.assertIn("1/6", texto)
        self.assertNotIn("de 7", texto)

    def test_an_unknown_value_is_never_published_as_a_figure(self):
        catalogo = _catalogue(_product("DEP-1", "Depósito Uno", conditions=[
            _condition("annual_rate_percent", "9.99", state="unknown")]))
        # Sin ninguna condición `known` no hay recomendación que hacer.
        self.assertIsNone(compose_catalogue_answer(catalogo, question="¿Qué TAE tiene?"))

    def test_a_catalogue_without_use_yields_nothing(self):
        self.assertIsNone(compose_catalogue_answer({"used": False, "products": []}))
        self.assertIsNone(compose_catalogue_answer(None))

    def test_the_disclaimer_is_always_present(self):
        catalogo = _catalogue(_product("DEP-1", "Depósito Uno", conditions=[
            _condition("annual_rate_percent", "3.1")]))
        texto = compose_catalogue_answer(catalogo, question="¿Qué TAE tiene?")
        assert texto is not None
        self.assertIn("no una oferta ni una recomendación personalizada", texto)

    def test_numbers_are_written_the_spanish_way(self):
        catalogo = _catalogue(_product("DEP-1", "Depósito Uno", conditions=[
            _condition("minimum_eur", "5000", unit="EUR")]))
        texto = compose_catalogue_answer(catalogo, question="¿Cuánto hace falta?")
        assert texto is not None
        self.assertIn("5.000", texto)
        self.assertNotIn("5000", texto)


class PendingEvidenceTest(unittest.TestCase):
    def test_a_product_without_transcribed_conditions_is_named_as_pending(self):
        catalogo = _catalogue(_product("ETF-01", "ETF Sintético"))
        texto = pending_evidence_answer(catalogo)
        assert texto is not None
        self.assertIn("ETF Sintético", texto)
        self.assertIn("no puedo darte la cifra", texto)

    def test_a_product_with_conditions_is_not_pending(self):
        catalogo = _catalogue(_product("DEP-1", "Depósito Uno", conditions=[
            _condition("annual_rate_percent", "3.1")]))
        self.assertIsNone(pending_evidence_answer(catalogo))


if __name__ == "__main__":
    unittest.main()
