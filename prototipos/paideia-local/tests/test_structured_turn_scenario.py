import unittest
from unittest.mock import patch
import domain
from backend_services import LocalChatService, ServiceProblem
from test_structured_education import FakeEducationProvider, CONSENT, SCENARIO, VALID

CALCULATE = {**VALID, 'intent': 'calculate', 'claim_ids': ['simulation']}

class TurnScenarioTests(unittest.TestCase):
    def service(self, selection=CALCULATE):
        provider = FakeEducationProvider(selection)
        return LocalChatService(provider=provider, enabled=True, test_only=True, structured_mode=True), provider

    def test_current_turn_scenario_only_and_no_reuse(self):
        service, provider = self.service()
        expected = domain.calculate_scenario(SCENARIO)
        with patch.object(domain, 'calculate_scenario', wraps=domain.calculate_scenario) as calc:
            response = service.chat({'message': 'calculate', 'consent': CONSENT, 'scenario': SCENARIO})
            calc.assert_called_once_with(SCENARIO)
            self.assertEqual(response['structured_education']['calculation']['data'], expected)
            with self.assertRaises(ServiceProblem):
                service.chat({'message': 'calculate again', 'consent': CONSENT})
            calc.assert_called_once_with(SCENARIO)
        self.assertEqual(len(provider.requests), 2)
        self.assertNotIn('principal', str(provider.requests))

    def test_provider_cannot_forge_scenario_or_reference(self):
        for extra in ({'scenario': SCENARIO}, {'scenario_id':'previous'}, {'result': {'final_balance':'999'}}, {'refusal':'no'}):
            with self.subTest(extra=extra):
                service, provider = self.service({**CALCULATE, **extra})
                with patch.object(domain, 'calculate_scenario') as calc, self.assertRaises(ServiceProblem):
                    service.chat({'message':'calculate', 'consent':CONSENT, 'scenario':SCENARIO})
                calc.assert_not_called()
                self.assertLessEqual(len(provider.requests), 1)

    def test_provider_scenario_without_user_scenario_is_rejected(self):
        service, provider = self.service({**CALCULATE, 'scenario':SCENARIO})
        with patch.object(domain, 'calculate_scenario') as calc, self.assertRaises(ServiceProblem):
            service.chat({'message':'calculate', 'consent':CONSENT})
        calc.assert_not_called()
        self.assertEqual(len(provider.requests), 1)

    def test_invalid_request_scenarios_and_legacy_rejected(self):
        scenarios = [None, [], {**SCENARIO, 'years':True}, {**SCENARIO, 'principal':1000},
                     {**SCENARIO, 'principal':'NaN'}, {**SCENARIO, 'extra':'x'},
                     {k:v for k,v in SCENARIO.items() if k != 'method'}]
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                service, provider = self.service()
                with patch.object(domain, 'calculate_scenario') as calc, self.assertRaises(ServiceProblem):
                    service.chat({'message':'calculate', 'consent':CONSENT, 'scenario':scenario})
                calc.assert_not_called()
                self.assertLessEqual(len(provider.requests), 1)
        from structured_provider_adapter import FakeChatProvider
        from providers import ChatResult
        provider = FakeChatProvider(ChatResult('TEST ONLY', None, (), 'stop'), test_only=True)
        legacy = LocalChatService(provider=provider, enabled=True, test_only=True)
        with self.assertRaises(ServiceProblem):
            legacy.chat({'message':'x', 'consent':CONSENT, 'scenario':SCENARIO})
        self.assertEqual(provider.requests, [])

    def test_explain_rejects_scenario_without_calculation(self):
        service, provider = self.service(VALID)
        with patch.object(domain, 'calculate_scenario') as calc, self.assertRaises(ServiceProblem):
            service.chat({'message':'explain', 'consent':CONSENT, 'scenario':SCENARIO})
        calc.assert_not_called()
        self.assertEqual(len(provider.requests), 1)
