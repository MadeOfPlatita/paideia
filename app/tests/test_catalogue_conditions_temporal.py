"""Bordes temporales del servicio de condiciones.

Una tasa solo es `known` si la fuente la documenta y sigue vigente. Estas pruebas
fijan el día exacto en que deja de serlo, la antigüedad máxima admitida por
familia y el caso de una tasa sin fecha de vigencia. Todas trabajan con una fecha
de referencia explícita: si dependieran del calendario del equipo, el mismo código
daría otro resultado cada semana y la prueba dejaría de medir el código.

Se cubren dos caminos, porque la app los usa a la vez: el literal del snapshot
(`annual_rate`) y la transcripción curada (`_curated_conditions`), que es de donde
salen las tasas del catálogo real.
"""

import unittest
from datetime import date, timedelta

from catalogue_conditions import annual_rate, derive
from conditions_service import ConditionsService

TODAY = date(2026, 11, 18)


def candidate(**overrides):
    base = {
        "candidate_id": "T-1",
        "family": "cuenta_remunerada",
        "candidate_state": "verified",
        "name_literal": "Producto de prueba",
        "available_fields": {},
        "dates": {"checked_at": "2026-11-18"},
        "conflicts": [],
    }
    base.update(overrides)
    return base


def rate_field(literal, **extra):
    return {"value_literal": literal, "source_ids": [1], **extra}


def curated(valid_to, **overrides):
    record = {
        "candidate_id": "C-1",
        "family": "deposito",
        "name": "Depósito de prueba",
        "term_months": 12,
        "source": {"url": "https://example.invalid/ficha", "kind": "official",
                   "retrieved_at": "2026-11-18"},
        "valid_to": valid_to,
        "tiers": [{"condition": "sin_requisito", "condition_label": "Sin requisito", "tae": "3.10"}],
    }
    record.update(overrides)
    return {"records": [record]}


def curated_rate(valid_to, **overrides):
    report = derive({"candidates": []}, TODAY, curated(valid_to, **overrides))
    return next(c for c in report["products"][0]["conditions"]
                if c["metric"] == "annual_rate_percent")


class ExpiryBoundaryTests(unittest.TestCase):
    """El día del término todavía vale; la oferta caduca al día siguiente."""

    def test_the_documented_last_day_is_still_valid(self):
        # «Válida hasta el 18/11/2026» incluye el 18: es el último día de contratación.
        item = candidate(available_fields={
            "promo_tae": rate_field("2,61 % TAE", effective_to=TODAY.isoformat()),
        })
        condition = annual_rate(item, TODAY)
        self.assertEqual((condition.state, condition.reason), ("known", "DOCUMENTED_PROMO_TAE"))
        self.assertEqual(condition.value, "2.61")

    def test_the_day_after_the_end_is_stale(self):
        item = candidate(available_fields={
            "promo_tae": rate_field("2,61 % TAE",
                                    effective_to=(TODAY - timedelta(days=1)).isoformat()),
        })
        condition = annual_rate(item, TODAY)
        self.assertEqual((condition.state, condition.reason), ("stale", "PROMOTION_EXPIRED"))
        # La cifra se conserva: el usuario ve qué tasa venció, no un hueco.
        self.assertEqual(condition.value, "2.61")

    def test_the_curated_path_shares_the_same_boundary(self):
        still_valid = curated_rate(TODAY.isoformat())
        self.assertEqual((still_valid["state"], still_valid["reason"]),
                         ("known", "CURATED_OFFICIAL"))
        expired = curated_rate((TODAY - timedelta(days=1)).isoformat())
        self.assertEqual((expired["state"], expired["reason"]),
                         ("stale", "PROMOTION_EXPIRED"))
        self.assertEqual(expired["effective_to"], (TODAY - timedelta(days=1)).isoformat())

    def test_a_range_reads_its_end_and_not_its_start(self):
        # Antes se tomaba la primera fecha del literal, así que esta promoción
        # figuraba vencida el mismo día en que empezaba.
        item = candidate(available_fields={
            "promo_tae": rate_field("2,61 % TAE del 21-10-2026 al 18-11-2026"),
        })
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "known", condition.notes)
        self.assertEqual(condition.effective_to, TODAY.isoformat())
        self.assertEqual(annual_rate(item, TODAY + timedelta(days=1)).state, "stale")

    def test_a_slash_date_is_understood_as_the_term(self):
        # Las fuentes escriben la fecha en las tres formas; solo una se comparaba.
        item = candidate(available_fields={
            "promo_tae": rate_field("2,61 % TAE válida hasta el 18/11/2026"),
        })
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.effective_to, TODAY.isoformat())
        self.assertEqual(condition.state, "known")

    def test_a_date_the_literal_does_not_mark_as_a_term_is_not_one(self):
        # «datos a 05-11-2026» es la fecha del dato, no su vigencia. Tomarla por
        # término cerraba ofertas que la fuente seguía publicando.
        item = candidate(available_fields={
            "promo_tae": rate_field("2,61 % TAE (datos a 05-11-2026)"),
        })
        condition = annual_rate(item, TODAY)
        self.assertIsNone(condition.effective_to)
        self.assertEqual(condition.state, "known")

    def test_an_impossible_date_is_not_published_as_an_end(self):
        item = candidate(available_fields={
            "promo_tae": rate_field("2,61 % TAE", effective_to="2026-02-31"),
        })
        condition = annual_rate(item, TODAY)
        self.assertIsNone(condition.effective_to)
        self.assertEqual(condition.state, "known")


class RetrievalAgeTests(unittest.TestCase):
    """Sin término declarado, la antigüedad de la consulta decide: 7 y 30 días."""

    def condition(self, family, days_ago, **extra):
        item = candidate(family=family,
                         dates={"checked_at": (TODAY - timedelta(days=days_ago)).isoformat()},
                         available_fields={"rate": rate_field("2,00 % TAE", **extra)})
        return annual_rate(item, TODAY)

    def test_an_account_holds_seven_full_days(self):
        self.assertEqual(self.condition("cuenta_remunerada", 7).state, "known")
        expired = self.condition("cuenta_remunerada", 8)
        self.assertEqual((expired.state, expired.reason), ("stale", "RETRIEVAL_TOO_OLD"))

    def test_a_deposit_holds_thirty_full_days(self):
        self.assertEqual(self.condition("deposito", 30).state, "known")
        expired = self.condition("deposito", 31)
        self.assertEqual((expired.state, expired.reason), ("stale", "RETRIEVAL_TOO_OLD"))

    def test_the_same_age_is_judged_by_family(self):
        # Una cuenta se mueve cada semana; un depósito, cada mes. Diez días invalidan
        # la primera y no el segundo: es el motivo de que el umbral no sea único.
        days = 10
        self.assertEqual(self.condition("cuenta_remunerada", days).reason, "RETRIEVAL_TOO_OLD")
        self.assertEqual(self.condition("deposito", days).state, "known")

    def test_the_note_names_the_family_limit(self):
        account = self.condition("cuenta_remunerada", 8)
        self.assertIn("7 días", account.notes[0])
        deposit = self.condition("deposito", 31)
        self.assertIn("30 días", deposit.notes[0])

    def test_a_declared_end_outranks_the_age_of_the_consultation(self):
        # Con término escrito manda la vigencia: una consulta antigua de una oferta
        # que sigue abierta no la invalida, y una reciente no la resucita.
        old_but_open = self.condition("deposito", 400, effective_to="2027-03-31")
        self.assertEqual(old_but_open.state, "known")
        self.assertEqual(old_but_open.effective_to, "2027-03-31")

    def test_a_recent_consultation_does_not_revive_an_expired_offer(self):
        expired = self.condition("cuenta_remunerada", 1, effective_to="2026-11-16")
        self.assertEqual((expired.state, expired.reason), ("stale", "PROMOTION_EXPIRED"))


class CuratedRetrievalAgeTests(unittest.TestCase):
    """La transcripción curada también caduca por antigüedad.

    Es el camino de todas las tasas del catálogo real, así que si la regla solo
    viviera en el literal del snapshot no protegería ningún dato servido.
    """

    def record(self, family, days_ago, valid_to=None):
        return curated(valid_to, family=family,
                       source={"url": "https://example.invalid/ficha", "kind": "official",
                               "retrieved_at": (TODAY - timedelta(days=days_ago)).isoformat()})

    def rate(self, family, days_ago, valid_to=None):
        report = derive({"candidates": []}, TODAY, self.record(family, days_ago, valid_to))
        return next(c for c in report["products"][0]["conditions"]
                    if c["metric"] == "annual_rate_percent")

    def test_a_curated_account_past_seven_days_is_stale(self):
        self.assertEqual(self.rate("cuenta_remunerada", 7)["state"], "known")
        expired = self.rate("cuenta_remunerada", 8)
        self.assertEqual((expired["state"], expired["reason"]),
                         ("stale", "RETRIEVAL_TOO_OLD"))
        self.assertIn("7 días", expired["notes"][0])

    def test_a_curated_deposit_past_thirty_days_is_stale(self):
        self.assertEqual(self.rate("deposito", 30)["state"], "known")
        expired = self.rate("deposito", 31)
        self.assertEqual((expired["state"], expired["reason"]),
                         ("stale", "RETRIEVAL_TOO_OLD"))
        self.assertIn("30 días", expired["notes"][0])

    def test_a_declared_end_still_outranks_the_age(self):
        # La vigencia escrita manda sobre la antigüedad de la consulta, igual que en
        # el literal: no se invalida una oferta abierta por haberla consultado antes.
        condition = self.rate("deposito", 400, valid_to="2027-03-31")
        self.assertEqual((condition["state"], condition["reason"]),
                         ("known", "CURATED_OFFICIAL"))

    def test_families_without_their_own_ttl_fall_back_to_the_strictest(self):
        # Un fondo no tiene tasa, pero la función no debe inventar un umbral mayor:
        # ante una familia desconocida se aplica el plazo del depósito.
        from catalogue_conditions import _family_ttl
        self.assertEqual(_family_ttl("fondo_tradicional"), 30)
        self.assertEqual(_family_ttl(None), 30)
        self.assertEqual(_family_ttl("cuenta_remunerada"), 7)


class UndatedRateTests(unittest.TestCase):
    """Una tasa sin fecha de vigencia se juzga solo por la fecha de la consulta."""

    def test_a_fresh_consultation_without_an_end_date_is_known_and_undeclared(self):
        item = candidate(available_fields={"promo_tae": rate_field("2,02 % TAE")})
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "known")
        self.assertIsNone(condition.effective_to)
        self.assertIsNone(condition.effective_from)
        self.assertEqual(condition.retrieved_at, "2026-11-18")

    def test_a_consultation_with_a_timestamp_is_measured_by_its_day(self):
        # La fuente puede anotar la hora. Antes eso lanzaba ValueError y tumbaba la
        # petición entera; la antigüedad solo necesita el día.
        item = candidate(dates={"checked_at": "2026-11-01T09:30:00Z"},
                         available_fields={"promo_tae": rate_field("2,02 % TAE")})
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "stale")
        self.assertEqual(condition.reason, "RETRIEVAL_TOO_OLD")

    def test_a_rate_without_any_date_is_kept_but_flagged(self):
        # Sin fecha de consulta no se puede medir antigüedad; tampoco se afirma que el
        # dato sea actual. Se publica la cifra con la limitación escrita al lado.
        item = candidate(dates={}, available_fields={"promo_tae": rate_field("2,02 % TAE")})
        condition = annual_rate(item, TODAY)
        self.assertEqual(condition.state, "known")
        self.assertIsNone(condition.retrieved_at)
        self.assertIn("no se puede medir su antigüedad", condition.notes[0])

    def test_the_note_does_not_appear_when_a_date_exists(self):
        dated = candidate(available_fields={"promo_tae": rate_field("2,02 % TAE")})
        self.assertEqual(annual_rate(dated, TODAY).notes, ())


class NoCachedStateTests(unittest.TestCase):
    """El estado se deriva con la fecha de cada petición; el servicio no lo guarda."""

    def test_the_same_offer_changes_state_between_two_requests(self):
        # Es el comportamiento que se busca: una promoción caduca sola y nadie tiene
        # que acordarse de marcarla. Si el estado se cacheara, el segundo día seguiría
        # presentándose como vigente.
        service = ConditionsService()
        before = service.describe(today=TODAY)
        after = service.describe(today=TODAY + timedelta(days=40))
        self.assertEqual(before["reference_date"], TODAY.isoformat())
        self.assertEqual(after["reference_date"], (TODAY + timedelta(days=40)).isoformat())
        self.assertNotEqual(before["state_counts"], after["state_counts"])
        self.assertGreater(after["state_counts"].get("stale", 0),
                           before["state_counts"].get("stale", 0))

    def test_a_reference_date_can_be_given_per_call(self):
        service = ConditionsService(reference_date=TODAY)
        self.assertEqual(service.describe()["reference_date"], TODAY.isoformat())
        other = TODAY + timedelta(days=1)
        self.assertEqual(service.describe(today=other)["reference_date"], other.isoformat())


if __name__ == "__main__":
    unittest.main()
