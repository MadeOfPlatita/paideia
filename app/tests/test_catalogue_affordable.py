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

    def test_without_an_amount_it_asks_instead_of_recommending(self):
        """Cambió a propósito: antes recomendaba sin saber cuánto dinero hay.

        Ese comportamiento es justo el que produjo el fallo del estudiante con
        2.000 € al que se le ofrecían depósitos de 5.000 €. Ahora, sin la cantidad,
        se pregunta y se adelanta la ficha del producto que hay.
        """
        catalogo = {"used": True, "products": [EBN, PIBANK]}
        texto = compose_catalogue_answer(catalogo, question="¿Qué depósito me conviene?") or ""
        self.assertIn("¿Cuánto dinero", texto)
        self.assertIn("3,10", texto)

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


class ExpiredRateTest(unittest.TestCase):
    """La tasa de Pibank está en estado `stale`: la promoción caducó.

    Fallo medido en producción: al recomendar ese depósito, la respuesta decía «para
    eso encaja Depósito Pibank» y NO daba ninguna TAE, porque el compositor descarta
    las condiciones no `known`. El producto quedaba sin cifra y sin explicación.
    """

    def _pibank_vencido(self):
        return {
            "id": "DEP-03", "name": "Depósito Pibank a 12 meses", "issuer": "Pibank",
            "conditions_state": "documented_not_current",
            "conditions": [
                _cond("annual_rate_percent", "3.03"),
                _cond("term_months", "12", "MONTHS"),
                _cond("minimum_note", "Sin mínimo", "TEXT"),
            ],
        }

    def test_an_expired_rate_is_declared_expired_with_its_figure(self):
        producto = self._pibank_vencido()
        for condition in producto["conditions"]:
            if condition["metric"] == "annual_rate_percent":
                condition["state"] = "stale"
        catalogo = {"used": True, "products": [producto]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA) or ""
        # La cifra aparece, pero declarada vencida: no se presenta como vigente…
        self.assertIn("3,03", texto)
        self.assertIn("vencida", texto.lower())
        # …y no se inventa un interés con un tipo caducado.
        self.assertNotIn("15,15", texto)

    def test_a_live_rate_is_preferred_over_an_expired_one(self):
        vencido = self._pibank_vencido()
        for condition in vencido["conditions"]:
            if condition["metric"] == "annual_rate_percent":
                condition["state"] = "stale"
        vivo = _deposit("DEP-EBN-12", "Depósito Nuevo Ahorro 12 meses", "EBN Banco", "3.10", "1000")
        catalogo = {"used": True, "products": [vencido, vivo]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA) or ""
        # Se recomienda el que tiene tasa viva, no el vencido.
        self.assertIn("Nuevo Ahorro", texto)
        self.assertNotIn("encaja **Depósito Pibank", texto)

    def test_if_only_expired_rates_exist_it_says_so_plainly(self):
        producto = self._pibank_vencido()
        for condition in producto["conditions"]:
            if condition["metric"] == "annual_rate_percent":
                condition["state"] = "stale"
        catalogo = {"used": True, "products": [producto]}
        texto = compose_catalogue_answer(catalogo, question=PREGUNTA) or ""
        # No se deja al usuario con un producto sin cifra: se le dice qué pasa.
        self.assertRegex(texto, r"ya no está en vigor|Confírmalo antes de contratar")


class AskingBeforeRecommendingTest(unittest.TestCase):
    """Un asesor pregunta cuando la respuesta depende de algo que no le han dicho.

    El prompt del sistema ya lo pedía («si falta un dato que cambia la respuesta,
    pide solo ese dato»), pero cuando el turno usa el catálogo la prosa del modelo se
    retiene y compone `compose_catalogue_answer`, así que esa política se perdía: la
    app recomendaba sin saber cuánto dinero hay ni para cuándo.
    """

    def test_without_an_amount_it_asks_for_it(self):
        texto = compose_catalogue_answer({"used": True, "products": [PIBANK]},
                                         question="¿Qué depósito me conviene?") or ""
        self.assertIn("¿Cuánto dinero", texto)
        # Y no deja al usuario sin nada: adelanta el dato que sí tiene.
        self.assertIn("3,03", texto)

    def test_with_an_amount_but_no_horizon_it_asks_for_the_horizon(self):
        texto = compose_catalogue_answer({"used": True, "products": [PIBANK]},
                                         question="Tengo 2000 euros, ¿qué depósito me conviene?") or ""
        self.assertIn("¿Para cuándo", texto)

    def test_with_both_data_points_it_does_not_ask(self):
        texto = compose_catalogue_answer(
            {"used": True, "products": [PIBANK]},
            question="Tengo 2000 euros y necesito 1500 dentro de un año") or ""
        self.assertNotIn("me falta un dato", texto)
        # Y hace el razonamiento completo.
        self.assertIn("500", texto)

    def test_a_horizon_in_words_counts_as_known(self):
        for pregunta in ("Tengo 2000 euros para un año",
                         "Tengo 2000 euros a 6 meses",
                         "Tengo 2000 euros y no lo toco en dos años"):
            with self.subTest(pregunta=pregunta):
                texto = compose_catalogue_answer({"used": True, "products": [PIBANK]},
                                                 question=pregunta) or ""
                self.assertNotIn("¿Para cuándo", texto)

    def test_a_listing_question_does_not_ask_for_anything(self):
        """A «¿qué depósitos hay?» no se le pide el dinero: quiere saber qué hay."""
        texto = compose_catalogue_answer({"used": True, "products": [PIBANK]},
                                         question="¿Qué productos de depósito hay?") or ""
        self.assertNotIn("¿Cuánto dinero", texto)
        self.assertIn("Pibank", texto)

    def test_a_request_for_a_concrete_datum_does_not_ask_for_money(self):
        """«¿Qué TAE tiene el depósito de EBN?» pide una cifra, no una recomendación.

        Pedir el importe disponible aquí sería no contestar lo que se ha preguntado.
        """
        for pregunta in ("¿Qué TAE tiene el depósito de EBN Banco?",
                         "dame la ficha del depósito",
                         "detalla DEP-KNOWN",
                         "¿qué comisiones tiene el fondo Olea Neutral?",
                         "¿cuál es el TER del ETF de iShares?"):
            with self.subTest(pregunta=pregunta):
                texto = compose_catalogue_answer({"used": True, "products": [PIBANK]},
                                                 question=pregunta) or ""
                self.assertNotIn("¿Cuánto dinero", texto,
                                 f"preguntó por el dinero en una consulta de dato: {texto}")


class RememberingPreviousTurnsTest(unittest.TestCase):
    """No se vuelve a preguntar un dato que la persona ya dio.

    Fallo medido en producción: turno 1 «Tengo 2000 euros ahorrados»; turno 2 «¿Qué
    depósito me conviene?» → el chat volvía a preguntar «¿cuánto dinero tienes?». El
    compositor solo miraba el mensaje actual, no el historial.
    """

    def test_it_does_not_ask_for_money_already_given(self):
        texto = compose_catalogue_answer(
            {"used": True, "products": [PIBANK]},
            question="¿Qué depósito me conviene?",
            previous_questions=["Tengo 2000 euros ahorrados"]) or ""
        self.assertNotIn("¿Cuánto dinero", texto)
        # Y usa la cifra del turno anterior.
        self.assertIn("2.000", texto)

    def test_it_does_not_ask_for_a_horizon_already_given(self):
        texto = compose_catalogue_answer(
            {"used": True, "products": [PIBANK]},
            question="¿Qué depósito me conviene?",
            previous_questions=["Tengo 2000 euros y lo necesito dentro de un año"]) or ""
        self.assertNotIn("¿Cuánto dinero", texto)
        self.assertNotIn("¿Para cuándo", texto)

    def test_with_both_data_in_history_it_reasons_fully(self):
        texto = compose_catalogue_answer(
            {"used": True, "products": [PIBANK]},
            question="¿Qué depósito me conviene?",
            previous_questions=["Tengo 2000 euros y lo necesito dentro de un año"]) or ""
        # Razonamiento completo: la cifra y el interés calculado.
        self.assertIn("2.000", texto)
        self.assertIn("60", texto)
        self.assertIn("intereses", texto)

    def test_the_current_message_wins_over_the_history(self):
        """Si cambia de cantidad, manda la nueva."""
        texto = compose_catalogue_answer(
            {"used": True, "products": [PIBANK]},
            question="Al final tengo 3000 euros para un año, ¿qué depósito me conviene?",
            previous_questions=["Tengo 2000 euros"]) or ""
        self.assertIn("3.000", texto)
        self.assertNotIn("2.000", texto)

    def test_a_term_is_not_mistaken_for_an_expense(self):
        """«lo necesito en 6 meses» no es un gasto de 6 €."""
        from catalogue_answer import extract_expense_eur
        self.assertIsNone(extract_expense_eur("lo necesito en 6 meses"))
        self.assertEqual(extract_expense_eur("necesito 1500 para el año"), 1500.0)
        # Pero un gasto con cifra y plazo sí se lee.
        self.assertEqual(extract_expense_eur("necesito 1500 en 6 meses"), 1500.0)

    def test_the_horizon_is_read_in_months(self):
        from catalogue_answer import _horizon_months
        casos = {"dentro de un año": 12, "en 6 meses": 6, "año y medio": 18,
                 "para 2 años": 24, "tengo 12 meses": None}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(_horizon_months(texto), esperado)


if __name__ == "__main__":
    unittest.main()
