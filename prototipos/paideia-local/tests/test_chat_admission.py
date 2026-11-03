import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission


class FakeClock:
    def __init__(self, now=None):
        self.now = now or datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


class ChatAdmissionTests(unittest.TestCase):
    def test_missing_policy_disables_admission(self):
        admission = InterfazChatAdmission(policy=None, clock=FakeClock())

        result = admission.submit()

        self.assertEqual(result["code"], "disabled")
        self.assertIsNone(result["ticket"])
        self.assertEqual(admission.status()["code"], "disabled")

    def test_configured_policy_without_restored_budget_state_fails_closed(self):
        policy = AdmissionPolicy(2, 10, 5, 20, 60, 30, scope="test")
        admission = InterfazChatAdmission(policy=policy, clock=FakeClock())

        result = admission.submit()

        self.assertEqual(result["code"], "state_unavailable")
        self.assertIsNone(result["ticket"])
        self.assertEqual(admission.status()["code"], "state_unavailable")

    def test_external_atomic_budget_adapter_is_injectable_without_database_dependency(self):
        policy = AdmissionPolicy(2, 10, 5, 20, 60, 30, scope="test")
        backing = InMemoryBudgetState.new_empty(scope="test")

        class ExternalAdapter:
            scope = "test"
            ready = True

            def reserve(self, configured_policy, now):
                return backing.reserve(configured_policy, now)

            def status(self, now):
                return backing.status(now)

        admission = InterfazChatAdmission(policy, FakeClock(), budget_state=ExternalAdapter())

        self.assertEqual(admission.submit()["code"], "admitted")
        self.assertEqual(backing.status(FakeClock()()), {"calls_minute": 1, "calls_day": 1})

    def test_explicit_budget_state_reserves_first_call_before_admitting(self):
        policy = AdmissionPolicy(2, 10, 5, 20, 60, 30, scope="test")
        ledger = InMemoryBudgetState.new_empty(scope="test")
        admission = InterfazChatAdmission(policy, FakeClock(), budget_state=ledger)

        result = admission.submit()

        self.assertEqual(result["code"], "admitted")
        self.assertIsInstance(result["ticket"], str)
        self.assertEqual(admission.status()["active"], 1)
        self.assertEqual(ledger.status(FakeClock()()), {"calls_minute": 1, "calls_day": 1})

    def test_bounded_fifo_queue_returns_positions_and_rejects_overflow(self):
        policy = AdmissionPolicy(1, 2, 10, 20, 60, 30, scope="test")
        admission = InterfazChatAdmission(
            policy, FakeClock(), budget_state=InMemoryBudgetState.new_empty(scope="test"))

        first = admission.submit()
        second = admission.submit()
        third = admission.submit()
        overflow = admission.submit()

        self.assertEqual(first["code"], "admitted")
        self.assertEqual(second["code"], "queued")
        self.assertEqual(second["position"], 1)
        self.assertEqual(third["code"], "queued")
        self.assertEqual(third["position"], 2)
        self.assertEqual(overflow["code"], "queue_full")
        self.assertIsNone(overflow["ticket"])
        self.assertEqual(admission.status()["queued"], 2)

    def test_claim_complete_releases_only_concurrency_and_keeps_fifo(self):
        policy = AdmissionPolicy(1, 3, 10, 20, 60, 30, scope="test")
        ledger = InMemoryBudgetState.new_empty(scope="test")
        admission = InterfazChatAdmission(policy, FakeClock(), budget_state=ledger)
        first, second, third = (admission.submit() for _ in range(3))

        claimed = admission.claim(first["ticket"])
        duplicate_claim = admission.claim(first["ticket"])
        completed = admission.complete(first["ticket"])
        next_claim = admission.claim(second["ticket"])

        self.assertEqual(claimed["code"], "claimed")
        self.assertEqual(duplicate_claim["code"], "duplicate")
        self.assertEqual(completed["code"], "completed")
        self.assertEqual(next_claim["code"], "claimed")
        self.assertEqual(admission.status(third["ticket"])["position"], 1)
        self.assertEqual(ledger.status(FakeClock()()), {"calls_minute": 2, "calls_day": 2})
        self.assertEqual(admission.status()["active"], 1)

    def test_every_provider_round_is_reserved_and_cancel_never_refunds(self):
        policy = AdmissionPolicy(1, 2, 2, 2, 60, 30, scope="test")
        ledger = InMemoryBudgetState.new_empty(scope="test")
        admission = InterfazChatAdmission(policy, FakeClock(), budget_state=ledger)
        ticket = admission.submit()["ticket"]
        self.assertEqual(admission.claim(ticket)["code"], "claimed")

        tool_followup = admission.reserve_provider_call(ticket)
        exhausted = admission.reserve_provider_call(ticket)
        cancelled = admission.cancel(ticket)
        duplicate_cancel = admission.cancel(ticket)

        self.assertEqual(tool_followup["code"], "reserved")
        self.assertEqual(tool_followup["provider_call_number"], 2)
        self.assertEqual(exhausted["code"], "quota_exhausted")
        self.assertEqual(cancelled["code"], "cancelled")
        self.assertEqual(duplicate_cancel["code"], "duplicate")
        self.assertEqual(admission.status()["active"], 0)
        self.assertEqual(ledger.status(FakeClock()()), {"calls_minute": 2, "calls_day": 2})

    def test_claim_lease_expiry_reclaims_slot_and_expired_tickets_are_invalid(self):
        clock = FakeClock()
        policy = AdmissionPolicy(1, 3, 10, 20, 30, 5, scope="test")
        admission = InterfazChatAdmission(
            policy, clock, budget_state=InMemoryBudgetState.new_empty(scope="test"))
        first = admission.submit()["ticket"]
        second = admission.submit()["ticket"]
        self.assertEqual(admission.claim(first)["code"], "claimed")

        clock.now += timedelta(seconds=6)
        second_state = admission.status(second)
        first_state = admission.status(first)
        second_claim = admission.claim(second)
        clock.now += timedelta(seconds=6)
        expired_claim = admission.status(second)
        invalid = admission.claim("not-a-ticket")

        self.assertEqual(second_state["code"], "admitted")
        self.assertEqual(first_state["code"], "expired")
        self.assertEqual(second_claim["code"], "claimed")
        self.assertEqual(expired_claim["code"], "expired")
        self.assertEqual(invalid["code"], "ticket_invalid")
        self.assertEqual(admission.status()["active"], 0)

    def test_lifecycle_calls_report_expired_instead_of_duplicate_for_timed_out_ticket(self):
        clock = FakeClock()
        policy = AdmissionPolicy(1, 1, 10, 20, 5, 3, scope="test")
        admission = InterfazChatAdmission(
            policy, clock, budget_state=InMemoryBudgetState.new_empty(scope="test"))
        ticket = admission.submit()["ticket"]
        clock.now += timedelta(seconds=6)

        completed = admission.complete(ticket)
        cancelled = admission.cancel(ticket)

        self.assertEqual(completed["code"], "expired")
        self.assertEqual(cancelled["code"], "expired")

    def test_unclaimed_and_waiting_tickets_expire_without_background_jobs(self):
        clock = FakeClock()
        policy = AdmissionPolicy(1, 2, 10, 20, 5, 30, scope="test")
        admission = InterfazChatAdmission(
            policy, clock, budget_state=InMemoryBudgetState.new_empty(scope="test"))
        admitted = admission.submit()["ticket"]
        queued = admission.submit()["ticket"]

        clock.now += timedelta(seconds=6)
        admitted_status = admission.status(admitted)
        queued_status = admission.status(queued)
        invalidated_claim = admission.claim(queued)

        self.assertEqual(admitted_status["code"], "expired")
        self.assertEqual(queued_status["code"], "expired")
        self.assertEqual(invalidated_claim["code"], "expired")
        self.assertEqual(admission.status()["active"], 0)
        self.assertEqual(admission.status()["queued"], 0)

    def test_idempotency_duplicate_does_not_spend_another_provider_call(self):
        policy = AdmissionPolicy(2, 2, 5, 20, 60, 30, scope="test")
        ledger = InMemoryBudgetState.new_empty(scope="test")
        admission = InterfazChatAdmission(policy, FakeClock(), budget_state=ledger)

        first = admission.submit(idempotency_key="opaque-request-1")
        duplicate = admission.submit(idempotency_key="opaque-request-1")

        self.assertEqual(first["code"], "admitted")
        self.assertEqual(duplicate["code"], "duplicate")
        self.assertEqual(duplicate["ticket"], first["ticket"])
        self.assertEqual(ledger.status(FakeClock()()), {"calls_minute": 1, "calls_day": 1})

    def test_export_restore_preserves_daily_budget_and_invalid_snapshot_is_rejected(self):
        clock = FakeClock(datetime(2026, 10, 28, 23, 59, 30, tzinfo=timezone.utc))
        policy = AdmissionPolicy(1, 0, 10, 1, 60, 30, scope="provider-model:test")
        original_ledger = InMemoryBudgetState.new_empty(scope=policy.scope)
        original = InterfazChatAdmission(policy, clock, budget_state=original_ledger)
        first = original.submit()["ticket"]
        self.assertEqual(original.claim(first)["code"], "claimed")
        self.assertEqual(original.complete(first)["code"], "completed")

        snapshot = original_ledger.export_state()
        restored = InMemoryBudgetState.restore(snapshot, expected_scope=policy.scope)
        restarted = InterfazChatAdmission(policy, clock, budget_state=restored)
        after_restart = restarted.submit()

        self.assertEqual(after_restart["code"], "quota_exhausted")
        self.assertEqual(restored.status(clock())["calls_day"], 1)
        corrupt = dict(snapshot, calls_day=-1)
        with self.assertRaises(ValueError):
            InMemoryBudgetState.restore(corrupt, expected_scope=policy.scope)

    def test_utc_midnight_resets_minute_and_day_budget_not_local_calendar_date(self):
        clock = FakeClock(datetime(2026, 10, 29, 1, 59, 59,
                                   tzinfo=timezone(timedelta(hours=2))))
        policy = AdmissionPolicy(1, 0, 1, 1, 60, 30, scope="test")
        ledger = InMemoryBudgetState.new_empty(scope="test")
        admission = InterfazChatAdmission(policy, clock, budget_state=ledger)
        first = admission.submit()["ticket"]
        self.assertEqual(admission.complete(first)["code"], "completed")
        self.assertEqual(admission.submit()["code"], "quota_exhausted")

        clock.now += timedelta(seconds=1)
        after_utc_midnight = admission.submit()

        self.assertEqual(after_utc_midnight["code"], "admitted")
        self.assertEqual(ledger.status(clock()), {"calls_minute": 1, "calls_day": 1})

    def test_minute_quota_rolls_over_on_utc_minute_without_resetting_day(self):
        clock = FakeClock(datetime(2026, 10, 28, 12, 0, 59, tzinfo=timezone.utc))
        policy = AdmissionPolicy(1, 0, 1, 3, 60, 30, scope="test")
        ledger = InMemoryBudgetState.new_empty(scope="test")
        admission = InterfazChatAdmission(policy, clock, budget_state=ledger)
        first = admission.submit()["ticket"]
        self.assertEqual(admission.complete(first)["code"], "completed")
        self.assertEqual(admission.submit()["code"], "quota_exhausted")

        clock.now += timedelta(seconds=1)
        second = admission.submit()
        self.assertEqual(second["code"], "admitted")
        self.assertEqual(ledger.status(clock()), {"calls_minute": 1, "calls_day": 2})
        self.assertEqual(admission.complete(second["ticket"])["code"], "completed")
        self.assertEqual(admission.submit()["code"], "quota_exhausted")

    def test_clock_rollback_makes_budget_status_fail_closed(self):
        clock = FakeClock()
        policy = AdmissionPolicy(1, 0, 10, 20, 60, 30, scope="test")
        ledger = InMemoryBudgetState.new_empty(scope="test")
        admission = InterfazChatAdmission(policy, clock, budget_state=ledger)
        ticket = admission.submit()["ticket"]
        self.assertEqual(admission.complete(ticket)["code"], "completed")

        clock.now -= timedelta(seconds=1)

        self.assertEqual(admission.status()["code"], "state_unavailable")
        self.assertEqual(admission.submit()["code"], "state_unavailable")

    def test_clock_exception_fails_closed_without_creating_ticket(self):
        policy = AdmissionPolicy(1, 0, 10, 20, 60, 30, scope="test")
        ledger = InMemoryBudgetState.new_empty(scope="test")

        def broken_clock():
            raise RuntimeError("synthetic clock unavailable")

        admission = InterfazChatAdmission(policy, broken_clock, budget_state=ledger)

        self.assertEqual(admission.submit()["code"], "state_unavailable")
        self.assertEqual(admission.status()["code"], "state_unavailable")
        self.assertEqual(ledger.export_state()["calls_day"], 0)

    def test_queued_status_exposes_daily_quota_exhaustion(self):
        policy = AdmissionPolicy(1, 2, 10, 1, 60, 30, scope="test")
        admission = InterfazChatAdmission(
            policy, FakeClock(), budget_state=InMemoryBudgetState.new_empty(scope="test"))
        first = admission.submit()["ticket"]
        waiting = admission.submit()["ticket"]

        admission.complete(first)
        result = admission.status(waiting)

        self.assertEqual(result["code"], "quota_exhausted")
        self.assertEqual(result["position"], 1)
        self.assertEqual(result["calls_day"], 1)

    def test_one_hundred_concurrent_synthetic_submissions_obey_global_limits(self):
        cases = (
            ("minute_quota", 12, 8, 1, 91),
            ("concurrency", 8, 20, 0, 92),
        )
        for name, max_concurrent, calls_per_minute, expected_quota_rejected, expected_queued in cases:
            with self.subTest(name=name):
                policy = AdmissionPolicy(max_concurrent, 100, calls_per_minute, 50,
                                         60, 30, scope=f"test:{name}")
                ledger = InMemoryBudgetState.new_empty(scope=policy.scope)
                admission = InterfazChatAdmission(policy, FakeClock(), budget_state=ledger)

                with ThreadPoolExecutor(max_workers=100) as pool:
                    results = list(pool.map(
                        lambda number: admission.submit(idempotency_key=f"synthetic-{name}-{number}"),
                        range(100)))

                codes = [result["code"] for result in results]
                status = admission.status()
                self.assertEqual(len(results), 100)
                self.assertEqual(len({result["ticket"] for result in results}), 100)
                self.assertEqual(codes.count("admitted"), 8)
                self.assertEqual(codes.count("quota_exhausted"), expected_quota_rejected)
                self.assertEqual(codes.count("queued"), expected_queued)
                self.assertEqual(status["active"], 8)
                self.assertEqual(status["queued"], 92)
                self.assertLessEqual(status["active"], max_concurrent)
                self.assertLessEqual(status["calls_minute"], calls_per_minute)
                self.assertLessEqual(status["calls_day"], 50)
                self.assertEqual(status["calls_minute"], 8)
                self.assertEqual(status["calls_day"], 8)

                admitted = [result["ticket"] for result in results if result["code"] == "admitted"]
                with ThreadPoolExecutor(max_workers=8) as pool:
                    claims = list(pool.map(admission.claim, admitted))
                self.assertTrue(all(claim["code"] == "claimed" for claim in claims))
                self.assertEqual(admission.status()["active"], 8)
                self.assertEqual(ledger.status(FakeClock()()), {"calls_minute": 8, "calls_day": 8})


if __name__ == "__main__":
    unittest.main()
