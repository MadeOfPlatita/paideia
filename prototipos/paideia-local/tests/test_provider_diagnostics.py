"""Sanitized diagnostics, only synthetic transport and fictional key."""
import json
import unittest
from providers import GroqProvider, ProviderError, TransportResponse, API_KEY_ENV

class ProviderDiagnosticTests(unittest.TestCase):
    def test_reasoning_only_truncation_has_metadata_but_never_reasoning_or_key(self):
        key='SYNTHETIC_DIAGNOSTIC_NOT_A_REAL_KEY'
        private='PRIVATE_SYNTHETIC_REASONING_DO_NOT_LOG'
        class TestOnlyTransport:
            test_only=True
            def post(self,**kwargs):
                return TransportResponse(200,json.dumps({'choices':[{'message':{'role':'assistant','content':None,'reasoning':private},'finish_reason':'length'}]}).encode())
        provider=GroqProvider(TestOnlyTransport(),opt_in=True,environment={API_KEY_ENV:key})
        with self.assertRaises(ProviderError) as caught:
            provider.chat([{'role':'user','content':'Synthetic diagnostic'}])
        self.assertEqual(caught.exception.code,'invalid_response')
        diagnostic=getattr(caught.exception,'diagnostic',None)
        self.assertIsNotNone(diagnostic,'The sanitized parser failure metadata is missing')
        self.assertEqual(diagnostic['http_status'],200)
        self.assertEqual(diagnostic['finish_reason'],'length')
        self.assertFalse(diagnostic['has_content'])
        self.assertTrue(diagnostic['has_reasoning'])
        self.assertNotIn(private,json.dumps(diagnostic))
        self.assertNotIn(key,json.dumps(diagnostic))
