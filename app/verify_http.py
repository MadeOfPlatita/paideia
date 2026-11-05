"""Acceptance checks against the actual loopback prototype; never calls external hosts."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


def verify(base):
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', 'localhost'} or parsed.path not in {'', '/'} or parsed.query or parsed.fragment or parsed.username:
        raise ValueError('Only an HTTP loopback base URL is permitted')
    base = base.rstrip('/')
    results = []

    def request(path, body=None, origin=None):
        headers = {}
        if body is not None:
            headers = {'Content-Type': 'application/json', 'Origin': origin or base}
        req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
        try:
            response = urllib.request.urlopen(req, timeout=8)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read(2_000_000)
            content_type = response.headers.get('Content-Type', '')
            return response.status, dict(response.headers), json.loads(raw) if 'application/json' in content_type else raw.decode('utf-8')

    def check(name, action):
        try:
            action()
            results.append({'name': name, 'ok': True})
        except Exception as exc:
            results.append({'name': name, 'ok': False, 'error': str(exc)})

    def home():
        status, headers, html = request('/')
        assert status == 200, status
        assert '<html' in html.lower() and 'Paideia' in html
        csp = next((value for key, value in headers.items() if key.lower() == 'content-security-policy'), '')
        assert csp and 'unsafe-eval' not in csp and 'unsafe-inline' not in csp, csp
        assert 'http-equiv="refresh"' not in html.lower()
    check('real_html_and_blocking_csp', home)

    def service_status():
        status, _, payload = request('/api/status')
        assert status == 200, status
        assert payload['ai']['connected'] is False
        assert payload['catalogue']['publication_ready'] == 0
        assert payload['storage'] == 'local_snapshot_not_postgresql'
    check('honest_service_status', service_status)

    def catalogue():
        status, _, payload = request('/api/catalogue')
        assert status == 200, status
        assert payload['count'] == len(payload['items']) == 20
        assert payload['not_for_publication'] is True
        assert len({item['id'] for item in payload['items']}) == len(payload['items'])
        for item in payload['items']:
            assert item['publication_ready'] is False
            assert item['conditions_state'] == 'pending'
            assert urllib.parse.urlsplit(item['primary_url']).scheme == 'https'
            assert not ({'available_fields', 'rate', 'tae', 'nav', 'price'} & set(item))
    check('candidate_metadata_not_verified_quotes', catalogue)

    def filter_family():
        status, _, payload = request('/api/catalogue?family=etf_ucits')
        assert status == 200 and payload['count'] == 4
        assert all(item['family'] == 'etf_ucits' for item in payload['items'])
    check('family_filter', filter_family)

    def empty_search():
        status, _, payload = request('/api/catalogue?q=zzzz_no_product_zzzz')
        assert status == 200 and payload['count'] == 0
    check('empty_search_not_fabricated', empty_search)

    def detail():
        status, _, payload = request('/api/products/ACC-01')
        assert status == 200 and payload['product']['id'] == 'ACC-01'
    check('real_candidate_detail', detail)

    def missing():
        status, _, payload = request('/api/products/UNKNOWN_ID')
        assert status == 404 and payload['error']['request_id']
    check('missing_product_safe_error', missing)

    def compare():
        status, _, payload = request('/api/compare', {'product_ids': ['ACC-01', 'DEP-01']})
        assert status == 200 and len(payload['items']) == 2
        assert payload['comparison_kind'] == 'educational_metadata_only'
        assert payload['quantitative_ready'] is False and payload['reasons']
    check('cross_family_metadata_not_false_ranking', compare)

    def duplicate():
        status, _, payload = request('/api/compare', {'product_ids': ['ACC-01', 'ACC-01']})
        assert status == 400 and 'error' in payload
    check('duplicate_comparison_rejected', duplicate)

    def comparability_diagnosis():
        status, _, payload = request('/api/compare', {'product_ids': ['DEP-01', 'DEP-02'], 'criterion': 'deposit_tae_12m_eur'})
        assert status == 200, status
        diagnosis = payload['comparability']
        assert payload['quantitative_ready'] is False and diagnosis['quantitative_ready'] is False
        assert diagnosis['policy_version'] is None and diagnosis['not_for_publication'] is True
        assert all(item['value'] is None and 'METRIC_MISSING' in item['reason_codes']
                   and 'FRESHNESS_POLICY_NOT_CONFIGURED' in item['reason_codes'] for item in diagnosis['items'])
    check('comparability_explains_missing_facts_and_unapproved_policy', comparability_diagnosis)

    def client_facts():
        status, _, payload = request('/api/compare', {'product_ids': ['DEP-01', 'DEP-02'],
            'criterion': 'deposit_tae_12m_eur', 'facts': []})
        assert status == 400 and payload['error']['code'] == 'INVALID_REQUEST'
    check('client_cannot_upload_comparison_facts', client_facts)

    def calculate(rate, contribution, method, years=1):
        status, _, payload = request('/api/calculate', {'principal': '1000.00', 'annual_rate_percent': rate, 'years': years, 'monthly_contribution': contribution, 'method': method, 'inflation_percent': '0.00'})
        assert status == 200, (status, payload)
        assert payload['hypothetical'] is True and payload['not_prediction'] is True
        assert payload['series'] and payload['series'][0]['month'] == 0
        return payload

    def zero():
        payload = calculate('0.00', '100.00', 'compound')
        expected = Decimal('1000.00') + Decimal('100.00') * 12
        assert Decimal(payload['summary']['final_balance']) == expected
        assert Decimal(payload['summary']['contributions']) == expected
        assert Decimal(payload['summary']['interest']) == 0
    check('zero_rate_end_month_contributions', zero)

    def annual():
        payload = calculate('3.00', '0.00', 'compound')
        expected = (Decimal('1000.00') * (1 + Decimal('3.00') / 100)).quantize(Decimal('.01'))
        assert Decimal(payload['summary']['final_balance']) == expected
    check('annual_effective_percent_not_ratio', annual)

    def loss():
        payload = calculate('-10.00', '0.00', 'compound')
        assert Decimal(payload['summary']['final_balance']) < Decimal(payload['summary']['contributions'])
        assert Decimal(payload['summary']['interest']) < 0
    check('negative_return_is_visible_loss', loss)

    def simple():
        payload = calculate('3.00', '0.00', 'simple', 2)
        expected = (Decimal('1000.00') * (1 + Decimal('3.00') / 100 * 2)).quantize(Decimal('.01'))
        assert Decimal(payload['summary']['final_balance']) == expected
    check('simple_interest_two_years', simple)

    def invalid():
        status, _, payload = request('/api/calculate', {'principal': 'NaN', 'annual_rate_percent': '3', 'years': 1, 'monthly_contribution': '0', 'method': 'compound', 'inflation_percent': '0'})
        assert status == 400 and payload['error']['retryable'] is False
    check('nan_rejected_without_retry', invalid)

    def chat():
        status, _, payload = request('/api/chat', {'message': 'SYNTHETIC TEST ONLY'})
        assert status == 503 and payload['error']['code'] == 'CHAT_NOT_CONFIGURED'
        assert 'reply' not in payload
    check('no_fabricated_ai_response', chat)

    def foreign_origin():
        status, _, payload = request('/api/compare', {'product_ids': ['ACC-01', 'DEP-01']}, origin='https://outside.invalid')
        assert status in {400, 403}, status
    check('foreign_origin_rejected', foreign_origin)

    def traversal():
        status, _, _ = request('/%2e%2e/%2e%2e/docs/REQUISITOS.md')
        assert status in {400, 403, 404}, status
    check('encoded_traversal_rejected', traversal)
    return {'checked_at': datetime.now(timezone.utc).isoformat(), 'base_url': base, 'scope': 'actual_local_http_not_external_llm_or_load', 'checks': results, 'passed': sum(x['ok'] for x in results), 'total': len(results), 'ok': all(x['ok'] for x in results)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8765')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = verify(args.base_url)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
