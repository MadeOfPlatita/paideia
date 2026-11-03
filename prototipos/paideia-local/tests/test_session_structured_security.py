"""Offline structured session security checks; all data and missions synthetic."""
import json
import threading
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import mission_budget
from mission_budget import MissionBudget, load_mission
from secure_groq_session import Session
from structured_session_fixture import StructuredSessionFixture
from backend_services import LocalChatService, ServiceProblem
from chat_admission import AdmissionPolicy, InMemoryBudgetState, InterfazChatAdmission

CONSENT = {'notice_version':'paideia-chat-remote-v1', 'accepted_chat_processing':True, 'purpose':'free_chat', 'approved_fields':[]}
SELECTION = {'version':'paideia-education-v1', 'intent':'explain', 'claim_ids':['risk']}

def response(content=None, finish='stop', **extra):
    msg = {'role':'assistant', 'content':json.dumps(SELECTION) if content is None else content, **extra}
    return json.dumps({'choices':[{'finish_reason':finish, 'message':msg}]}).encode()

class StructuredSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        manifest = Path(self.tmp.name) / 'MISSION.json'
        manifest.write_text(json.dumps({'schema':'paideia-mission.v1', 'mission_id':'paideia-ia-20261029T220831Z', 'start_utc':'2026-10-29T22:08:31.985015+00:00', 'deadline_utc':'2026-10-29T23:08:31.985015+00:00', 'max_external_attempts':24}), encoding='utf8')
        self.patch = patch.object(mission_budget, 'NEW_MANIFEST', manifest)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.config = load_mission(manifest)
        self.now = self.config.start + timedelta(seconds=1)
        self.budget = MissionBudget(self.config)
        self.addCleanup(self.budget.close)
        self.fixture = StructuredSessionFixture(200, response())
        self.session = Session('FAKE-KEY-ONLY', test_only=True, transport=self.fixture, clock=lambda:self.now, mission_budget=self.budget)
        policy = AdmissionPolicy(1, 0, 24, 24, 120, 120, scope='synthetic')
        self.gate = InterfazChatAdmission(policy, lambda:self.now, budget_state=InMemoryBudgetState.new_empty(scope='synthetic'))
        self.service = LocalChatService(provider=self.session.provider, enabled=True, test_only=True, admission=self.gate, structured_session_test_only=True)

    def call(self, **extra):
        return self.service.chat({'message':'SYNTHETIC ONLY', 'consent':CONSENT, **extra})

    def test_closed_request_and_consent_before_reservation(self):
        for extra in ({'profile':{}}, {'structured_mode':True}, {'context':{}}, {'history':[]}, {'tools':[]}):
            with self.subTest(extra=extra), self.assertRaises(ServiceProblem): self.call(**extra)
        with self.assertRaises(ServiceProblem): self.service.chat({'message':'x'})
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 24)

    def test_closed_ticket_cannot_be_reused(self):
        ticket = self.gate.submit()['ticket']
        self.call(ticket=ticket)
        with self.assertRaises(ServiceProblem): self.call(ticket=ticket)
        self.assertEqual(len(self.fixture.requests), 1)
        self.assertEqual(self.budget.remaining(), 23)

    def test_revoke_and_expiry_before_attempt(self):
        self.session.revoke()
        with self.assertRaises(ServiceProblem): self.call()
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 24)

    def test_expiry_before_attempt(self):
        self.now = self.config.cutoff
        with self.assertRaises(ServiceProblem): self.call()
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 24)

    def test_bad_responses_no_retry_or_echo_and_admission_completed(self):
        tool = [{'id':'x', 'type':'function', 'function':{'name':'x', 'arguments':'{}'}}]
        variants = [(429, b'SYNTHETIC_SECRET'), (200, response('{"version":"x","version":"y"}')),
                    (200, response(finish='length')), (200, response(refusal='SYNTHETIC_SECRET')),
                    (200, response(tool_calls=tool)), (200, response(content='SYNTHETIC_SECRET'))]
        for index, (status, data) in enumerate(variants):
            with self.subTest(index=index):
                self.fixture.status, self.fixture.body = status, data
                before = len(self.fixture.requests)
                with self.assertRaises(ServiceProblem) as caught: self.call()
                self.assertNotIn('SYNTHETIC_SECRET', str(caught.exception))
                self.assertEqual(len(self.fixture.requests), before + 1)
                self.assertEqual(self.gate.status()['active'], 0)
        self.assertEqual(self.budget.remaining(), 24 - len(variants))

    def test_provider_replacement_during_claim_is_rejected_and_ticket_completed(self):
        class Impostor:
            calls = 0
            def structured_chat(self, messages):
                from providers import ChatResult
                self.calls += 1
                return ChatResult(json.dumps(SELECTION), None, (), 'stop')
        impostor = Impostor()
        ticket = self.gate.submit()['ticket']
        claim = self.gate.claim
        def swap_after_claim(value):
            result = claim(value)
            self.service._provider = impostor
            return result
        with patch.object(self.gate, 'claim', side_effect=swap_after_claim):
            with self.assertRaises(ServiceProblem):
                self.call(ticket=ticket)
        self.assertEqual(impostor.calls, 0)
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 24)
        self.assertEqual(self.gate.status(ticket)['code'], 'completed')
        # Admission reserves its first call at promotion; rejecting before
        # the synthetic transport does not refund that separate reservation.
        self.assertEqual(self.gate.status()['calls_day'], 1)
        self.assertEqual(self.gate.status()['active'], 0)

    def test_method_overrides_during_claim_never_dispatch(self):
        from secure_groq_session import _SingleFlightProvider
        calls = []
        def impostor(*args, **kwargs):
            calls.append(True)
            return json.dumps(SELECTION)
        for target in (self.session.provider, _SingleFlightProvider):
            with self.subTest(target=type(target).__name__):
                ticket = self.gate.submit()['ticket']
                claim = self.gate.claim
                from contextlib import ExitStack
                with ExitStack() as overrides:
                    def swap_after_claim(value):
                        result = claim(value)
                        overrides.enter_context(patch.object(target, 'structured_chat', impostor))
                        return result
                    with patch.object(self.gate, 'claim', side_effect=swap_after_claim):
                        with self.assertRaises(ServiceProblem): self.call(ticket=ticket)
                self.assertEqual(calls, [])
                self.assertEqual(self.gate.status(ticket)['code'], 'completed')
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 24)

    def test_service_mode_change_during_claim_is_rejected(self):
        for field, changed in (('_test_only', False), ('_structured_mode', False),
                               ('_structured_session_test_only', False), ('_enabled', False),
                               ('_tools_enabled', True), ('_context_enabled', True),
                               ('_history_enabled', True), ('_admission', None)):
            with self.subTest(field=field):
                original = getattr(self.service, field)
                ticket = self.gate.submit()['ticket']
                claim = self.gate.claim
                def mutate_after_claim(value):
                    result = claim(value)
                    setattr(self.service, field, changed)
                    return result
                try:
                    with patch.object(self.gate, 'claim', side_effect=mutate_after_claim):
                        with self.assertRaises(ServiceProblem): self.call(ticket=ticket)
                finally:
                    setattr(self.service, field, original)
                self.assertEqual(self.gate.status(ticket)['code'], 'completed')
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 24)
        self.assertEqual(self.gate.status()['active'], 0)

    def test_mission_replacement_during_claim_is_rejected(self):
        ticket = self.gate.submit()['ticket']
        claim = self.gate.claim
        def mutate_after_claim(value):
            result = claim(value)
            self.session._mission_budget = None
            return result
        try:
            with patch.object(self.gate, 'claim', side_effect=mutate_after_claim):
                with self.assertRaises(ServiceProblem): self.call(ticket=ticket)
        finally:
            self.session._mission_budget = self.budget
        self.assertEqual(self.gate.status(ticket)['code'], 'completed')
        self.assertEqual(self.gate.status()['active'], 0)
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 24)

    def test_fixture_impostor_cannot_assemble(self):
        class Impostor:
            test_only = True
            def post(self, **kwargs): raise AssertionError('must not run')
        with self.assertRaises(ValueError):
            Session('FAKE', test_only=True, transport=Impostor(), clock=lambda:self.now, mission_budget=self.budget)

    def test_revocation_after_fake_connect_prevents_post_but_consumes_slot(self):
        connected, proceed = threading.Event(), threading.Event()
        self.fixture.connect_entered, self.fixture.connect_release = connected, proceed
        errors = []
        def worker():
            try: self.call()
            except ServiceProblem as exc: errors.append(exc.code)
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(connected.wait(3))
            self.session.revoke()
        finally:
            proceed.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ['CHAT_STRUCTURED_INVALID_RESPONSE'])
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 23)
        self.assertEqual(self.gate.status()['active'], 0)

    def test_cutoff_during_fake_connect_consumes_slot_without_post(self):
        connected, proceed = threading.Event(), threading.Event()
        self.fixture.connect_entered, self.fixture.connect_release = connected, proceed
        errors = []
        def worker():
            try: self.call()
            except ServiceProblem as exc: errors.append(exc.code)
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(connected.wait(3))
            self.now = self.config.cutoff
        finally:
            proceed.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ['CHAT_STRUCTURED_INVALID_RESPONSE'])
        self.assertEqual(self.fixture.requests, [])
        self.assertEqual(self.budget.remaining(), 23)

    def test_ledger_corruption_during_fake_connect_prevents_post(self):
        connected, proceed = threading.Event(), threading.Event()
        self.fixture.connect_entered, self.fixture.connect_release = connected, proceed
        errors = []
        def worker():
            try: self.call()
            except ServiceProblem as exc: errors.append(exc.code)
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(connected.wait(3))
            self.budget.path.write_bytes(b'{}')
        finally:
            proceed.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ['CHAT_STRUCTURED_INVALID_RESPONSE'])
        self.assertEqual(self.fixture.requests, [])
        with self.assertRaises(ValueError): self.budget.remaining()

    def test_revoke_after_fake_post_does_not_retract_inflight_result(self):
        posted, proceed = threading.Event(), threading.Event()
        self.fixture.post_entered, self.fixture.post_release = posted, proceed
        results = []
        def worker():
            try: results.append(self.call())
            except ServiceProblem as exc: results.append(exc.code)
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(posted.wait(3))
            self.session.revoke()
        finally:
            proceed.set()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(self.fixture.requests), 1)
        self.assertEqual(results[0]['structured_education']['items'][0]['id'], 'risk')
        with self.assertRaises(ServiceProblem): self.call()
        self.assertEqual(len(self.fixture.requests), 1)

    def test_quota_survives_restart(self):
        for _ in range(24): self.call()
        with self.assertRaises(ServiceProblem): self.call()
        self.assertEqual(len(self.fixture.requests), 24)
        self.budget.close()
        with MissionBudget(self.config) as reopened: self.assertEqual(reopened.remaining(), 0)
