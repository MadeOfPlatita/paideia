"""El chat no recomienda lo que el usuario no puede contratar.

Fallo real medido. Un estudiante escribió:

    «Soy un estudiante con 2000 euros. Dentro de un año tengo previsto un gasto de
     1500 euros por los estudios. ¿Qué podría hacer si quiero mantener mi ahorro y
     ganar algo de rentabilidad asumiendo poco riesgo?»

El chat le recomendó tres depósitos y calculó la rentabilidad con la TAE del 3,10 %
del «Depósito Nuevo Ahorro» de EBN Banco. Ese depósito exige 5.000 € de mínimo y el
segundo que ofrecía, el de Self Bank, exige 6.000 €. El estudiante tiene 2.000 €.

Es decir: se le calculaba la rentabilidad de un producto que no puede contratar y se
le mandaba a mirar dos fichas inalcanzables. Un asesor no hace eso.

Estas pruebas fijan el contrato:
  1. Se reconoce la cantidad de dinero de la pregunta, en sus formatos reales.
  2. Se descarta el producto cuyo mínimo documentado supera esa cantidad.
  3. Si todos se pasan, se dice con los mínimos reales en vez de recomendar uno.
  4. El interés se calcula sobre el dinero libre, no sobre el gasto comprometido.
  5. La respuesta razona con las cifras, no las enumera.
"""

import unittest

from catalogue_answer import (
    _minimum_eur,
    compose_catalogue_answer,
    extract_amount_eur,
    extract_expense_eur,
)


def _cond(metric, value, unit="PERCENT", url=None):
    condition = {"metric": metric, "value": value, "state": "known", "unit": unit}
    if url:
        condition["sources"] = [{"url": url, "class": "official"}]
    return condition


def _deposit(pid, name, issuer, rate, minimum, term="12", state="documented"):
    conditions = [_cond("annual_rate_percent", rate)]
    if minimum is not None:
        conditions.append(_cond("minimum_eur", minimum, "EUR"))
    if term is not None:
        conditions.append(_cond("term_months", term, "MONTHS"))
    return {
        "id": pid, "name": name, "issuer": issuer, "conditions_state": state,
        "conditions": conditions,
    }


# Los tres productos reales que el chat encontró ese día.
PIBANK = _deposit("DEP-03", "Depósito Pibank a 12 meses", "Pibank", "3.03", "1")
EBN = _deposit("DEP-EBN-12", "Depósito Nuevo Ahorro 12 meses", "EBN Banco", "3.10", "5000")
SELF = _deposit("DEP-SELF-12", "Depósito a 12 meses Self Bank", "Self Bank", "2.50", "6000")

PREGUNTA = (
    "Soy un estudiante con 2000 euros. Dentro de un año tengo previsto un gasto de "
    "1500 euros por los estudios. ¿Que podria hacer si quiero mantener mi ahorro y "
    "ganar algo de rentabilidad asumiendo poco riesgo?"
)


class ReadingAmountsTest(unittest.TestCase):
    def test_it_reads_the_ways_people_write_money(self):
        casos = {
            "tengo 2000 euros": 2000.0,
            "tengo 2.000 €": 2000.0,
            "dispongo de 1.500 euros": 1500.0,
            "son 3000 EUR": 3000.0,
            "tengo 2.000,50 euros": 2000.5,
            "mil euros": 1000.0,
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(extract_amount_eur(texto), esperado)

    def test_a_term_or_a_rate_is_not_money(self):
        # Confundir un plazo o una tasa con el dinero del usuario llevaría a
        # descartar productos por un importe que nadie ha mencionado.
        for texto in ("tengo 12 meses", "una TAE del 3 %", "a 18 meses", "sin dinero"):
            with self.subTest(texto=texto):
                self.assertIsNone(extract_amount_eur(texto))

    def test_it_reads_the_planned_expense(self):
        self.assertEqual(extract_expense_eur("un gasto de 1500 euros por los estudios"), 1500.0)
        self.assertEqual(extract_expense_eur("necesito 1500 para el año"), 1500.0)
        self.assertEqual(extract_expense_eur("un gasto de 1.500 euros"), 1500.0)

    def test_the_minimum_comes_from_any_of_the_catalogue_keys(self):
        self.assertEqual(_minimum_eur(PIBANK), 1.0)
        self.assertEqual(_minimum_eur(EBN), 5000.0)
        self.assertEqual(_minimum_eur(SELF), 6000.0)
        # «Sin mínimo» es 1 €, no «desconocido»: el producto sí se puede contratar.
        sin_minimo = {"conditions": [_cond("minimum_note", "Sin mínimo", "EUR")]}
        self.assertEqual(_minimum_eur(sin_minimo), 1.0)
        # Un producto que no publica mínimo no se descarta (no se inventa el dato).
        self.assertIsNone(_minimum_eur({"conditions": []}))


class NotRecommendingWhatCannotBeAffordedTest(unittest.TestCase):
    def test_it_does_not_recommend_deposits_above_the_users_money(self):
        catalogo = {"used": True, "products": [EBN, SELF, PIBANK]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA)
        assert texto is not None
        # Se recomienda el único alcanzable.
        self.assertIn("Pibank", texto)
        # Y los dos inalcanzables se declaran descartados con su mínimo real.
        self.assertIn("5.000", texto)
        self.assertIn("6.000", texto)
        self.assertIn("descartado", texto.lower())

    def test_the_rate_of_an_unaffordable_product_is_never_the_headline(self):
        """El fallo exacto: se usaba el 3,10 % de un depósito de 5.000 € como si
        fuera contratable con 2.000 €."""
        catalogo = {"used": True, "products": [EBN, SELF, PIBANK]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA) or ""
        # El producto recomendado es Pibank, así que su tasa es la que encabeza.
        self.assertIn("3,03", texto)
        # La tasa del inalcanzable puede nombrarse al explicar el descarte, pero no
        # puede ser la de la recomendación.
        recomendacion = texto.split("encaja")[1].split("\n")[0] if "encaja" in texto else texto
        self.assertNotIn("3,1", recomendacion)

    def test_if_nothing_is_affordable_it_says_so_with_the_real_minimums(self):
        catalogo = {"used": True, "products": [EBN, SELF]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA)
        assert texto is not None
        # No se inventa una recomendación: se explica el muro con los mínimos.
        self.assertIn("5.000", texto)
        self.assertIn("6.000", texto)

    def test_without_an_amount_it_still_recommends_normally(self):
        catalogo = {"used": True, "products": [EBN, PIBANK]}
        texto = compose_catalogue_answer(catalogo, question="¿Qué depósito me conviene?")
        assert texto is not None
        self.assertIn("encaja", texto)

    def test_a_product_without_a_documented_minimum_is_not_discarded(self):
        """No se puede descartar por un mínimo que el catálogo no publica: sería
        inventar el dato en la dirección contraria."""
        sin_minimo = _deposit("DEP-X", "Depósito sin mínimo publicado", "Banco X", "2.0", None)
        catalogo = {"used": True, "products": [sin_minimo]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA)
        assert texto is not None
        self.assertIn("Banco X", texto)


class ConversationalAnswerTest(unittest.TestCase):
    def test_it_reasons_with_the_numbers_instead_of_listing_them(self):
        catalogo = {"used": True, "products": [PIBANK, EBN, SELF]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA) or ""
        # Arranca por la situación del usuario, no por la ficha del producto.
        self.assertTrue(texto.startswith("Con 2.000"), texto[:120])
        # Trabaja la cifra: 500 € libres al 3,03 % son ~15 €.
        self.assertIn("500", texto)
        self.assertIn("15", texto)
        # Y explica el gasto comprometido.
        self.assertIn("1.500", texto)

    def test_it_does_not_repeat_the_same_rate_twice(self):
        """El «demasiado texto numérico» reportado: la tasa salía en la
        recomendación y otra vez en el motivo."""
        catalogo = {"used": True, "products": [PIBANK]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA) or ""
        self.assertEqual(texto.count("3,03"), 1, texto)

    def test_no_technical_jargon_reaches_the_reader(self):
        catalogo = {"used": True, "products": [PIBANK, EBN, SELF]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA) or ""
        for jerga in ("candidato", "atribución", "clase de fuente", "DTO", "condición conocida"):
            with self.subTest(jerga=jerga):
                self.assertNotIn(jerga, texto.lower())


class DesignatedIssuerStillWinsTest(unittest.TestCase):
    def test_it_respects_both_the_issuer_and_the_amount(self):
        """Si se nombra un banco cuyo mínimo no se alcanza, se dice, no se cambia
        de banco en silencio."""
        catalogo = {"used": True, "products": [EBN, PIBANK]}
        texto = compose_catalogue_answer(
            catalogo, question="Con 2000 euros, ¿qué depósito tiene EBN Banco?") or ""
        # EBN pide 5.000: no se puede recomendar, y no se sustituye por Pibank
        # fingiendo que es lo que se preguntó.
        self.assertNotIn("encaja **Depósito Pibank", texto)


if __name__ == "__main__":
    unittest.main()
