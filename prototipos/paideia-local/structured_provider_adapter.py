"""Offline-only bridge from synthetic ChatResult to a closed editorial selection.

This is not a Groq protocol implementation and must not be used for real models.
"""
import json
from enum import Enum
from providers import ChatResult, ProviderError, ToolCall, build_chat_request
from structured_education import EDITORIAL, VERSION


def _fixture_data(value, depth=0):
    if depth > 8:
        return False
    if value is None or type(value) in (bool, int, float, str):
        return not isinstance(value, str) or len(value) <= 32768
    if type(value) is list:
        return len(value) <= 100 and all(_fixture_data(x, depth + 1) for x in value)
    if type(value) is dict:
        return len(value) <= 100 and all(type(k) is str and len(k) <= 1024 and _fixture_data(v, depth + 1) for k, v in value.items())
    return False


def _fixture_outcome(value):
    if type(value) is ProviderError:
        return type(value.code) is str
    if type(value) is not ChatResult:
        return False
    return (type(value.answer) is str and len(value.answer) <= 32768
            and (value.reasoning is None or type(value.reasoning) is str and len(value.reasoning) <= 32768)
            and (value.refusal is None or type(value.refusal) is str and len(value.refusal) <= 32768)
            and (value.finish_reason is None or type(value.finish_reason) is str and len(value.finish_reason) <= 128)
            and type(value.tool_calls) is tuple and len(value.tool_calls) <= 32
            and all(type(c) is ToolCall and type(c.id) is str and type(c.name) is str
                    and len(c.id) <= 1024 and len(c.name) <= 1024
                    and type(c.arguments) is dict and _fixture_data(c.arguments) for c in value.tool_calls))


MAX_RESPONSE_BYTES = 4096


class BrowserFixture(Enum):
    CONTEXT = 'context'
    QUALITY = 'quality'
    SCENARIO = 'scenario'


class FakeChatProvider:
    """Scripted fixture: no transport, environment lookup, or network access."""
    __slots__ = ('result', 'calls', 'requests', 'scripted', 'outcomes', 'tools', 'browser')
    test_only = True

    def __init__(self, result, *, test_only=False, scripted=False, outcomes=None, browser=None):
        if test_only is not True:
            raise ValueError('explicit test_only required')
        if type(scripted) is not bool:
            raise ValueError('invalid fixture mode')
        if outcomes is not None and (type(outcomes) is not tuple or not 1 <= len(outcomes) <= 32
                                     or scripted or any(not _fixture_outcome(x) for x in outcomes)):
            raise ValueError('invalid fixture outcomes')
        if browser is not None and (type(browser) is not BrowserFixture or scripted or outcomes is not None):
            raise ValueError('invalid browser fixture')
        self.browser = browser
        self.result = result
        self.outcomes = outcomes
        self.scripted = scripted
        self.calls = 0
        self.requests = []
        self.tools = []

    def chat(self, messages, *, tools=None):
        if (type(self.calls) is not int or type(self.requests) is not list or type(self.tools) is not list
                or type(self.scripted) is not bool):
            raise ValueError('invalid fixture state')
        self.calls += 1
        self.requests.append(messages)
        self.tools.append(tools)
        if self.browser is not None:
            if type(self.browser) is not BrowserFixture:
                raise ProviderError('invalid_response')
            build_chat_request(messages, tools=tools)
            if self.browser is BrowserFixture.SCENARIO:
                users = [m['content'] for m in messages if m['role'] == 'user']
                if not users or not users[-1].startswith('SYNTHETIC TEST ONLY'):
                    raise ProviderError('invalid_request')
                if messages[-1]['role'] == 'tool':
                    try:
                        balance = json.loads(messages[-1]['content'])['untrusted_tool_result']['data']['summary']['final_balance']
                        if type(balance) is not str or balance != '1030.00':
                            raise ValueError('unexpected synthetic result')
                    except (ValueError, TypeError, KeyError):
                        raise ProviderError('invalid_response') from None
                    return ChatResult('TEST ONLY — resultado determinista: saldo final ' + balance + ' EUR. No es una respuesta de una IA real.', None, (), 'stop')
                return ChatResult('', None, (ToolCall('test-calc-1', 'calculate_scenario', {
                    'principal':'1000.00', 'annual_rate_percent':'3.00', 'years':1,
                    'monthly_contribution':'0.00', 'method':'compound', 'inflation_percent':'2.00'}),), 'tool_calls')
            prefix = 'SYNTHETIC TEST ONLY:' if self.browser is BrowserFixture.QUALITY else 'SYNTHETIC TEST ONLY'
            if not messages[-1]['content'].startswith(prefix):
                raise ProviderError('invalid_request')
            if self.browser is BrowserFixture.CONTEXT:
                answer = 'TEST ONLY: respuesta sintética de prueba, no IA real.'
            elif self.browser is BrowserFixture.QUALITY:
                text = messages[-1]['content']
                if 'unsafe' in text:
                    answer = 'Ahorrar significa conservar dinero sin riesgo de perder el capital.'
                elif 'prefix-denial' in text:
                    answer = 'TEST ONLY — No es posible ahorrar sin riesgo.'
                else:
                    answer = 'TEST ONLY — Ahorrar es reservar ingresos; los riesgos dependen de dónde se guarden y la inflación puede reducir su poder adquisitivo.'
            else:
                raise ProviderError('invalid_request')
            return ChatResult(answer, None, (), 'stop')
        if self.outcomes is not None:
            if (type(self.outcomes) is not tuple or not 1 <= len(self.outcomes) <= 32
                    or any(not _fixture_outcome(x) for x in self.outcomes)):
                raise ProviderError('invalid_response')
            if self.calls > len(self.outcomes):
                raise ProviderError('invalid_response')
            outcome = self.outcomes[self.calls - 1]
            if type(outcome) is ProviderError:
                if type(outcome.code) is not str:
                    raise ProviderError('invalid_response')
                raise ProviderError(outcome.code)
            return outcome
        if self.scripted:
            query = messages[-1]['content']
            base = {'version':'paideia-education-v1', 'intent':'explain', 'claim_ids':['saving_investing','risk','inflation']}
            if not query.startswith('SYNTHETIC TEST ONLY:'):
                base = {'invalid': True}
            elif 'forged' in query:
                base['answer'] = 'Ahorrar es sin riesgo; texto falsificado.'
            elif 'calculate' in query:
                base.update(intent='calculate', claim_ids=['simulation'])
            return ChatResult(json.dumps(base), None, (), 'stop')
        if not _fixture_outcome(self.result) or type(self.result) is not ChatResult:
            raise ProviderError('invalid_response')
        return self.result


# Bind implementation once; instance/class method replacement is never dispatched.
_fake_chat = FakeChatProvider.chat


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate')
        result[key] = value
    return result


def _reject_constant(_value):
    raise ValueError('constant')


def parse_selection(result):
    """Project a raw ChatResult to the closed editorial contract, without I/O."""
    try:
        if (not _fixture_outcome(result) or type(result) is not ChatResult
                or type(result.finish_reason) is not str or result.finish_reason != 'stop'
                or result.refusal is not None or type(result.tool_calls) is not tuple
                or result.tool_calls != () or type(result.answer) is not str):
            raise ValueError('invalid')
        if len(result.answer.encode('utf-8', errors='strict')) > MAX_RESPONSE_BYTES:
            raise ValueError('too large')
        selection = json.loads(result.answer, object_pairs_hook=_unique, parse_constant=_reject_constant)
        if type(selection) is not dict or set(selection) != {'version', 'intent', 'claim_ids'}:
            raise ValueError('invalid')
        ids = selection['claim_ids']
        if (type(selection['version']) is not str or selection['version'] != VERSION
                or type(selection['intent']) is not str or selection['intent'] not in ('explain', 'calculate')
                or type(ids) is not list or not 1 <= len(ids) <= len(EDITORIAL)
                or any(type(i) is not str or i not in EDITORIAL for i in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError('invalid')
        return selection
    except Exception:
        raise ProviderError('invalid_response') from None


class StructuredProviderAdapter:
    __slots__ = ('_provider', 'test_only')

    def __init__(self, provider, *, test_only=False):
        if test_only is not True or type(provider) is not FakeChatProvider:
            raise ValueError('explicit fake test_only provider required')
        self.test_only = True
        self._provider = provider

    @property
    def requests(self):
        return self._provider.requests

    @property
    def result(self):
        return self._provider.result

    @result.setter
    def result(self, value):
        self._provider.result = ChatResult(json.dumps(value), None, (), 'stop')

    def select_education(self, messages):
        try:
            if (type(messages) is not list or len(messages) not in (1, 2)
                    or any(type(m) is not dict or set(m) != {'role', 'content'}
                           or type(m['content']) is not str or type(m['role']) is not str for m in messages)
                    or [m['role'] for m in messages] not in (['user'], ['system', 'user'])):
                raise ValueError('invalid messages')
            if type(self._provider) is not FakeChatProvider or self.test_only is not True:
                raise ValueError('invalid fixture state')
            return parse_selection(_fake_chat(self._provider, messages))
        except Exception:
            raise ProviderError('invalid_response') from None
