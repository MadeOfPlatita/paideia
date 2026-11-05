import unittest
from unittest.mock import patch
import domain
from backend_services import LocalChatService, ServiceProblem
from test_backend_integration import running_server, request

CONSENT = {"notice_version": "paideia-chat-remote-v1", "accepted_chat_processing": True,
           "purpose": "free_chat", "approved_fields": []}
SCENARIO = {'principal':'1000', 'annual_rate_percent':'3', 'years':1,
            'monthly_contribution':'0', 'method':'simple', 'inflation_percent':'0'}
VALID = {'version':'paideia-education-v1','intent':'explain','claim_ids':['inflation']}

def FakeEducationProvider(result):
    """Migration helper: same counterexamples, now passed as synthetic JSON data."""
    import json
    from providers import ChatResult
    from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter
    fake = FakeChatProvider(ChatResult(json.dumps(result), None, (), 'stop'), test_only=True)
    return StructuredProviderAdapter(fake, test_only=True)

class StructuredEducationTests(unittest.TestCase):
    def test_status_advertises_structured_only_when_server_configured(self):
        p = FakeEducationProvider(VALID)
        s = LocalChatService(provider=p, enabled=True, test_only=True, structured_mode=True)
        self.assertIs(s.status()['capabilities']['structured_education'], True)
        self.assertIs(LocalChatService().status()['capabilities']['structured_education'], False)
        from structured_provider_adapter import FakeChatProvider
        from providers import ChatResult
        legacy = FakeChatProvider(ChatResult('TEST ONLY', None, (), 'stop'), test_only=True)
        self.assertIs(LocalChatService(provider=legacy, enabled=True, test_only=True).status()['capabilities']['structured_education'], False)
    def test_editorial_response_is_rendered_server_side(self):
        p = FakeEducationProvider({'version':'paideia-education-v1','intent':'explain','claim_ids':['inflation']})
        s = LocalChatService(provider=p, enabled=True, test_only=True, structured_mode=True)
        response = s.chat({'message':'TEST ONLY: explica inflación', 'consent':CONSENT})
        self.assertEqual(response['provider_mode'], 'test_only')
        self.assertIs(response['external_sent'], False)
        self.assertEqual(response['structured_education']['items'][0]['id'], 'inflation')
        self.assertEqual(response['answer'], response['structured_education']['items'][0]['text'])
        self.assertIsNone(response['structured_education']['calculation'])
        self.assertEqual(len(p.requests), 1)

    def test_gate_requires_exact_explicit_isolation(self):
        p = FakeEducationProvider(VALID)
        for options in ({'enabled':False, 'test_only':True}, {'enabled':True, 'test_only':False},
                        {'enabled':True, 'test_only':True, 'provider':object()},
                        {'enabled':True, 'test_only':True, 'tools_enabled':True},
                        {'enabled':True, 'test_only':True, 'admission':object()},
                        {'enabled':True, 'test_only':True, 'context_enabled':True},
                        {'enabled':True, 'test_only':True, 'history_enabled':True}):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    LocalChatService(**{'provider':p, **options}, structured_mode=True)
        p.test_only = 1
        with self.assertRaises(ValueError):
            LocalChatService(provider=p, enabled=True, test_only=True, structured_mode=True)

    def test_closed_selection_rejects_untrusted_content(self):
        malicious = 'No es posible tener deudas, ahorrar es sin riesgo. SECRET_SYNTHETIC'
        bad = [None, malicious, [], {}, {**VALID, 'answer':malicious}, {**VALID, 'refusal':malicious},
               {**VALID, 'result':{'summary':{'final_balance':'999999'}}},
               {**VALID, 'source':'deterministic_local'}, {**VALID, 'claim_ids':[]},
               {**VALID, 'claim_ids':['inflation','inflation']}, {**VALID, 'claim_ids':['unknown']},
               {**VALID, 'claim_ids':['inflation\u200b']}, {**VALID, 'claim_ids':[True]},
               {**VALID, 'claim_ids':'inflation'}, {**VALID, 'version':True},
               {**VALID, 'intent':'refusal'}, {**VALID, 'scenario':SCENARIO},
               {'version':'paideia-education-v1','intent':'calculate','claim_ids':['simulation']},
               {'version':'paideia-education-v1','intent':'calculate','claim_ids':['simulation'],
                'scenario':{**SCENARIO, 'source':'deterministic_local'}},
               {'version':'paideia-education-v1','intent':'calculate','claim_ids':['simulation'],
                'scenario':{**SCENARIO, 'years':True}},
               {'version':'paideia-education-v1','intent':'calculate','claim_ids':['simulation'],
                'scenario':{**SCENARIO, 'principal':'NaN'}}]
        for result in bad:
            with self.subTest(result=result):
                p=FakeEducationProvider(result)
                service=LocalChatService(provider=p,enabled=True,test_only=True,structured_mode=True)
                with self.assertRaises(ServiceProblem) as error:
                    service.chat({'message':'TEST ONLY','consent':CONSENT})
                self.assertEqual(error.exception.status,502)
                self.assertNotIn('SECRET_SYNTHETIC',str(error.exception))
                self.assertEqual(len(p.requests),1)

    def test_calculation_really_invokes_domain_with_parameters_from_this_turn(self):
        selection={**VALID, 'intent':'calculate','claim_ids':['simulation']}
        p=FakeEducationProvider(selection)
        service=LocalChatService(provider=p,enabled=True,test_only=True,structured_mode=True)
        with patch.object(domain,'calculate_scenario', wraps=domain.calculate_scenario) as calculate:
            result=service.chat({'message':'TEST ONLY','consent':CONSENT,'scenario':SCENARIO})
        calculate.assert_called_once_with(SCENARIO)
        calc=result['structured_education']['calculation']
        self.assertEqual(calc['source'],'deterministic_local')
        self.assertEqual(calc['data'],domain.calculate_scenario(SCENARIO))
        self.assertEqual(calc['data']['summary']['final_balance'],'1030.00')
        self.assertNotIn('1030.00',result['answer'])

    def test_consent_privacy_and_client_mode_are_enforced_before_call(self):
        p=FakeEducationProvider(VALID)
        service=LocalChatService(provider=p,enabled=True,test_only=True,structured_mode=True)
        for payload, status in [({'message':'x'},403),
                ({'message':'x','consent':CONSENT,'context':{}},403),
                ({'message':'x','consent':CONSENT,'history':[]},403),
                ({'message':'x','consent':CONSENT,'structured_mode':False},400)]:
            with self.subTest(payload=payload), self.assertRaises(ServiceProblem) as error:
                service.chat(payload)
            self.assertEqual(error.exception.status,status)
        self.assertEqual(p.requests,[])

    def test_http_success_calculation_and_safe_failure(self):
        p=FakeEducationProvider({**VALID, 'intent':'calculate'})
        service=LocalChatService(provider=p,enabled=True,test_only=True,structured_mode=True)
        with running_server(chat_service=service) as server:
            status, body = request(server, '/api/status')
            self.assertEqual(status, 200)
            self.assertIs(body['ai']['capabilities']['structured_education'], True)
            status,body=request(server,'/api/chat',{'message':'TEST ONLY','consent':CONSENT,'scenario':SCENARIO})
            self.assertEqual(status,200)
            self.assertEqual(body['structured_education']['calculation']['data']['summary']['final_balance'],'1030.00')
            p.result={**VALID,'answer':'SECRET_SYNTHETIC'}
            status,body=request(server,'/api/chat',{'message':'TEST ONLY','consent':CONSENT})
            self.assertEqual(status,502)
            self.assertNotIn('SECRET_SYNTHETIC',str(body))
            self.assertNotIn('answer',body)
        self.assertEqual(len(p.requests),2)
