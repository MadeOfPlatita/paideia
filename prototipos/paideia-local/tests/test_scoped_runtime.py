"""Offline scoped-tool regressions, no actual provider/network."""
import unittest
from pai_runtime import ToolChatRunner
from providers import ChatResult, ToolCall
from test_pai_runtime import TestOnlyDispatcher, TestOnlyFakeProvider, scenario_arguments, tool_result


class CalculatorOnlyDispatcher(TestOnlyDispatcher):
    def definitions(self):
        return [d for d in super().definitions() if d['function']['name']=='calculate_scenario']


class ScopedRuntimeTests(unittest.TestCase):
    def test_registered_but_unadvertised_tool_is_rejected_before_dispatch(self):
        dispatcher = CalculatorOnlyDispatcher()
        provider = TestOnlyFakeProvider([
            ChatResult('',None,(ToolCall('unannounced','get_product_detail',{'product_id':'TEST-PROD'}),),'tool_calls'),
        ])
        result = ToolChatRunner(provider,dispatcher).run([{'role':'user','content':'TEST ONLY: unavailable catalogue'}])
        self.assertEqual(dispatcher.calls,[], 'A model must not escalate beyond the advertised subset')
        self.assertEqual(result['finish_reason'],'tool_error')
        self.assertEqual(len(provider.requests),1)

    def test_calculator_only_session_can_complete_without_advertising_catalogue(self):
        dispatcher = CalculatorOnlyDispatcher([tool_result('calculate_scenario', data={'summary':{'final_balance':'1030.00'}})])
        provider = TestOnlyFakeProvider([
            ChatResult('',None,(ToolCall('scoped_calc','calculate_scenario',scenario_arguments()),),'tool_calls'),
            ChatResult('TEST ONLY: 1030.00 EUR',None,(),'stop'),
        ])
        result = ToolChatRunner(provider,dispatcher).run([{'role':'user','content':'TEST ONLY: calculate'}])
        self.assertEqual(result['finish_reason'],'stop')
        self.assertEqual([t['function']['name'] for t in provider.requests[0]['tools']],['calculate_scenario'])
        self.assertEqual(len(dispatcher.calls),1)
