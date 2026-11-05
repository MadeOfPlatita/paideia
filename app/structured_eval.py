"""Tiny hand-labelled synthetic contract/relevance check, not a model evaluation."""
import json
from providers import ChatResult, ProviderError
from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter

# Expected labels are independent from the scripted outputs; exact set match is
# intentionally strict. These examples are not representative or expert-validated.
FIXTURES = (
    ('inflation', '{"version":"paideia-education-v1","intent":"explain","claim_ids":["inflation"]}', 'explain', frozenset({'inflation'})),
    ('risk', '{"version":"paideia-education-v1","intent":"explain","claim_ids":["risk"]}', 'explain', frozenset({'risk'})),
    ('inflation but irrelevant selection', '{"version":"paideia-education-v1","intent":"explain","claim_ids":["risk"]}', 'explain', frozenset({'inflation'})),
    ('invalid output', 'not JSON', 'explain', frozenset({'risk'})),
)

def evaluate():
    contract_valid = relevant = 0
    for query, answer, intent, expected in FIXTURES:
        fake = FakeChatProvider(ChatResult(answer, None, (), 'stop'), test_only=True)
        adapter = StructuredProviderAdapter(fake, test_only=True)
        try:
            result = adapter.select_education([{'role':'user', 'content':query}])
        except ProviderError:
            continue
        contract_valid += 1
        if result['intent'] == intent and frozenset(result['claim_ids']) == expected:
            relevant += 1
    return {'label':'synthetic_test_only', 'cases':len(FIXTURES),
            'contract_valid':contract_valid, 'relevant_among_valid':relevant,
            'relevance_denominator':contract_valid, 'winner':None,
            'limitation':'Hand-labelled toy fixtures; not a model quality measurement.'}

if __name__ == '__main__':
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
