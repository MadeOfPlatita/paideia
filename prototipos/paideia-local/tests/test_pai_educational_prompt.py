"""Prompt contract only; synthetic provider, not model-quality evidence."""
import unittest
from backend_services import LocalChatService
from providers import ChatResult
from test_functional05_http import CONSENT, TestOnlyFakeProvider

class EducationalPromptTests(unittest.TestCase):
    def test_chat_instructs_risk_and_inflation_instead_of_universal_savings_guarantee(self):
        provider=TestOnlyFakeProvider([ChatResult('TEST ONLY',None,(),'stop')])
        LocalChatService(provider=provider,enabled=True,test_only=True).chat({'message':'TEST ONLY: ahorro','consent':CONSENT})
        prompt=provider.requests[0][0]['content']
        self.assertIn('inflación',prompt)
        self.assertIn('sin riesgo',prompt)
        self.assertIn('No afirmes',prompt)
        self.assertIn('tres frases',prompt)
        self.assertIn('sin tablas',prompt)
