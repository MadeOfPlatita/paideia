"""Regresión documental del contrato; no llama a un modelo ni a una API."""
import copy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, FormatChecker

BUNDLE = json.loads((Path(__file__).resolve().parents[1] / '01-pai-tools' / 'contratos.json').read_text(encoding='utf-8'))
SCHEMA = {**BUNDLE, '$ref': '#/$defs/ConversationTurnRequest'}
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
BASE = {
    'contract_version': '0.1',
    'request_id': '11111111-1111-4111-8111-111111111111',
    'conversation_id': '22222222-2222-4222-8222-222222222222',
    'turn_id': '33333333-3333-4333-8333-333333333333',
    'message': 'Explica qué es un depósito.', 'history': [],
    'consent': {'notice_version': 'test-only', 'accepted_chat_processing': True,
                'store_local_profile': False, 'share_profile_with_model': False,
                'confirmed_at': '2026-10-26T12:00:00Z'},
}

class ConsentContractTests(unittest.TestCase):
    def test_remote_turn_rejects_processing_consent_false(self):
        request = copy.deepcopy(BASE)
        request['consent']['accepted_chat_processing'] = False
        self.assertFalse(VALIDATOR.is_valid(request), 'El contrato remoto no debe aceptar procesamiento rechazado')

    def test_explicit_consent_without_profile_is_valid(self):
        self.assertTrue(VALIDATOR.is_valid(BASE))

    def test_missing_consent_is_invalid(self):
        request = copy.deepcopy(BASE)
        del request['consent']
        self.assertFalse(VALIDATOR.is_valid(request))

    def test_unselected_profile_is_invalid(self):
        request = copy.deepcopy(BASE)
        request['profile_context'] = {'knowledge_level': 'beginner'}
        self.assertFalse(VALIDATOR.is_valid(request))

if __name__ == '__main__':
    unittest.main(verbosity=2)
