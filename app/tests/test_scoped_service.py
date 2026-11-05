"""Real loopback HTTP, injected synthetic provider only; never an external call."""
import inspect
import unittest
import app
from backend_services import LocalChatService, CatalogueComparisonService
from pai_tools import ToolDispatcher
from providers import ChatResult, ToolCall
from test_backend_integration import running_server, request
from test_functional05_http import make_gate, calculation_provider, CONSENT
from test_pai_runtime import TestOnlyFakeProvider


class ScopedServiceTests(unittest.TestCase):
    def test_calculator_scope_rejects_catalogue_call_and_client_scope_override(self):
        provider = TestOnlyFakeProvider([ChatResult('',None,(ToolCall('blocked_catalogue','get_product_detail',{'product_id':'ACC-01'}),),'tool_calls')])
        service = LocalChatService(provider=provider,enabled=True,test_only=False,
            dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()),
            tools_enabled=True,tools_scope='calculator_only',admission=make_gate())
        with running_server(chat_service=service) as server:
            status,body=request(server,'/api/chat',{'message':'TEST ONLY','consent':CONSENT,'tools_scope':'catalogue'})
            self.assertEqual(status,400)
            self.assertEqual(provider.requests,[])
            status,body=request(server,'/api/chat',{'message':'TEST ONLY','consent':CONSENT})
            self.assertEqual(status,502)
            self.assertEqual(body['error']['code'],'CHAT_TOOL_ERROR')
        self.assertEqual(len(provider.requests),1)

    def test_invalid_server_scope_is_rejected_as_configuration_error(self):
        for value in (None, [], True, 'arbitrary'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                LocalChatService(tools_scope=value)

    def test_calculator_only_http_does_not_require_catalogue_permission(self):
        self.assertIn('tools_scope',inspect.signature(LocalChatService).parameters, 'Explicit server-side calculator scope is missing')
        provider = calculation_provider()
        service = LocalChatService(provider=provider, enabled=True, test_only=False,
            dispatcher=ToolDispatcher(app.SnapshotRepository(), CatalogueComparisonService()),
            tools_enabled=True, tools_scope='calculator_only', admission=make_gate())
        with running_server(chat_service=service) as server:
            status,body = request(server,'/api/chat',{'message':'TEST ONLY: calculate','consent':CONSENT})
        self.assertEqual(status,200)
        self.assertEqual(body['tool_events'][0]['name'],'calculate_scenario')
        self.assertEqual([d['function']['name'] for d in provider.tools[0]],['calculate_scenario'])
        self.assertEqual(body['sources'],[])
