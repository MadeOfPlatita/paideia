import unittest
from backend_services import LocalChatService, ServiceProblem
from chat_context import NOTICE as CONTEXT_NOTICE, VERSION as CONTEXT_VERSION
from providers import ChatResult

CONSENT = {'notice_version':'paideia-chat-remote-v1','accepted_chat_processing':True,'purpose':'free_chat','approved_fields':[]}
EXTRA = {'notice_version':CONTEXT_NOTICE,'context':True,'history':True}
CONTEXT = {'version':CONTEXT_VERSION,'fields':{'detalle_economico.importe_objetivo':{'estado':'declarado','valor':{'min_eur':'0','max_eur':'0','moneda':'EUR'}}}}
from structured_provider_adapter import FakeChatProvider

def Fake():
    return FakeChatProvider(ChatResult('Respuesta ficticia', '', (), 'stop'), test_only=True)
class ContextTests(unittest.TestCase):
    def test_history_rejects_more_than_two_previous_turns(self):
        from chat_context import validate_history
        with self.assertRaises(ValueError):
            validate_history([{'role': role, 'content': 'ficticio'} for role in ('user','assistant') * 3])

    def test_status_advertises_disabled_capabilities(self):
        status = LocalChatService().status()
        self.assertEqual(status['capabilities'], {'context': False, 'history': False, 'synthetic_only': True, 'structured_education': False})

    def test_direct_service_rejects_large_utf8_request(self):
        p = Fake()
        s = LocalChatService(provider=p, enabled=True, test_only=True, history_enabled=True)
        payload = {'message': '🧪' * 2000, 'consent': CONSENT,
                   'context_consent': {**EXTRA, 'context': False},
                   'history': [{'role': r, 'content': '🧪' * 1000} for r in ('user','assistant') * 2]}
        with self.assertRaises(ServiceProblem): s.chat(payload)
        self.assertEqual(p.requests, [])

    def test_context_and_history_are_opt_in_server_and_consent(self):
        p=Fake(); payload={'message':'Pregunta ficticia','consent':CONSENT,'context_consent':EXTRA,'context':CONTEXT,'history':[{'role':'user','content':'Pregunta anterior ficticia'},{'role':'assistant','content':'Respuesta anterior ficticia'}]}
        with self.assertRaises(ServiceProblem): LocalChatService(provider=p,enabled=True,test_only=True).chat(payload)
        s=LocalChatService(provider=p,enabled=True,test_only=True,context_enabled=True,history_enabled=True)
        self.assertEqual(s.chat(payload)['provider_mode'], 'test_only')
        self.assertIn('0',str(p.requests[0])); self.assertNotIn('No recibes ningún perfil personal',str(p.requests[0]))
        self.assertEqual([m['role'] for m in p.requests[0]],['system','user','assistant','user'])
        self.assertEqual(len(p.requests),1)
        for modified in ({**payload,'context_consent':{**EXTRA,'history':False}}, {**payload,'history':[{'role':'system','content':'hack'}]}, {**payload,'context':{'version':'chat-context-test-v1','fields':{'url':'https://example.com'}}}):
            with self.assertRaises(ServiceProblem): s.chat(modified)
        self.assertEqual(len(p.requests),1)
    def test_http_synthetic_context_roundtrip_and_limits(self):
        from test_backend_integration import running_server, request
        from providers import build_chat_request
        p=Fake(); s=LocalChatService(provider=p,enabled=True,test_only=True,context_enabled=True,history_enabled=True)
        payload={'message':'Pregunta ficticia','consent':CONSENT,'context_consent':EXTRA,'context':CONTEXT,'history':[{'role':'user','content':'antes'},{'role':'assistant','content':'respuesta'}]}
        with running_server(chat_service=s) as server:
            status, body=request(server,'/api/chat',payload)
            self.assertEqual(status,200); self.assertEqual(body['provider_mode'],'test_only'); self.assertFalse(body['external_sent'])
            self.assertEqual(request(server,'/api/chat',{**payload,'message':'a'*17000})[0],413)
            self.assertEqual(request(server,'/api/chat',{**payload,'history':[{'role':'assistant','content':'hack'}]})[0],400)
        build_chat_request(p.requests[0]); self.assertEqual(len(p.requests),1)

    def test_flags_cannot_enable_external_provider(self):
        with self.assertRaises(ValueError): LocalChatService(enabled=True,context_enabled=True)
        with self.assertRaises(ValueError): LocalChatService(provider=object(),enabled=True,test_only=True,context_enabled=True)

    def test_context_allowed_for_enabled_external_provider(self):
        class External:
            def chat(self, messages):
                return ChatResult('Respuesta', '', (), 'stop')
        service = LocalChatService(provider=External(), enabled=True, context_enabled=True)
        self.assertTrue(service.status()['capabilities']['context'])
        self.assertFalse(service.status()['capabilities']['synthetic_only'])
        with self.assertRaises(ValueError):
            LocalChatService(provider=External(), enabled=False, context_enabled=True)

    def test_context_notice_version_rejects_old_synthetic_notice(self):
        p=Fake(); s=LocalChatService(provider=p,enabled=True,test_only=True,context_enabled=True)
        old = {**EXTRA, 'notice_version': 'paideia-chat-context-test-v1'}
        payload = {'message':'Pregunta ficticia','consent':CONSENT,'context_consent':old,'context':CONTEXT}
        with self.assertRaises(ServiceProblem): s.chat(payload)
        self.assertEqual(p.requests, [])
