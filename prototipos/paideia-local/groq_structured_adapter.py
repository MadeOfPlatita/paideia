"""Offline request-builder exercise only; never a Groq transport or service provider."""
import json
from providers import build_chat_request, ProviderError, MAX_REQUEST_BYTES
from structured_education import EDITORIAL, VERSION
from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter


def build_structured_request(messages):
    """Build a bounded candidate body offline; this does not send it."""
    if (type(messages) is not list or len(messages) not in (1, 2)
            or any(type(m) is not dict or set(m) != {'role', 'content'}
                   or type(m['role']) is not str or type(m['content']) is not str for m in messages)
            or [m['role'] for m in messages] not in (['user'], ['system', 'user'])):
        raise ValueError('invalid request')
    body = json.loads(build_chat_request(messages))
    body['response_format'] = {
        'type': 'json_schema',
        'json_schema': {
            'name': 'paideia_education_v1', 'strict': False,
            'schema': {
                'type': 'object', 'additionalProperties': False,
                'required': ['version', 'intent', 'claim_ids'],
                'properties': {
                    'version': {'type': 'string', 'enum': [VERSION]},
                    'intent': {'type': 'string', 'enum': ['explain', 'calculate']},
                    'claim_ids': {'type': 'array', 'minItems': 1, 'maxItems': len(EDITORIAL),
                                  'uniqueItems': True,
                                  'items': {'type': 'string', 'enum': list(EDITORIAL)}},
                },
            },
        },
    }
    encoded = json.dumps(body, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
    if len(encoded) > MAX_REQUEST_BYTES:
        raise ValueError('invalid request')
    return encoded


class OfflineGroqStructuredAdapter:
    """Exercise the existing request builder and closed selection on one fixture call."""
    __slots__ = ('_fixture',)

    def __init__(self, fixture):
        if type(fixture) is not FakeChatProvider:
            raise ValueError('explicit fake provider required')
        self._fixture = fixture

    def select_education(self, messages):
        try:
            if type(self._fixture) is not FakeChatProvider:
                raise ValueError('invalid fixture')
            # Build only: the resulting bytes are neither stored nor transmitted.
            build_structured_request(messages)
            return StructuredProviderAdapter(self._fixture, test_only=True).select_education(messages)
        except Exception:
            pass
        raise ProviderError('invalid_response')
