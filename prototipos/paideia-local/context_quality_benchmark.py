"""Benchmark sintético A/B/C; sin cliente, CLI, credenciales ni red propia."""
import copy
import json
import math
from pathlib import Path
from financial_quality import FINANCIAL_EDUCATION_PROMPT, assess_financial_text

MAX_BYTES = 16 * 1024
MAX_CALLS = 18
MAX_TOKENS = 256
DATASET = Path(__file__).resolve().parents[2] / 'docs/validacion-04/03-benchmark/dataset.json'
EDUCATIONAL_PROMPT = (
    'Eres Pai, asistente educativo en español. Separa hechos, hipótesis y datos '
    'desconocidos; no clasifiques personas; no inventes productos o recomendaciones. '
    + FINANCIAL_EDUCATION_PROMPT +
    'La rentabilidad pasada no garantiza resultados futuros. No hagas '
    'cálculos: usa únicamente resultados de cálculo externos aportados; si faltan, '
    'indícalo. No ejecutes operaciones ni presentes garantías o asesoramiento personalizado. '
    'Responde en un máximo de tres frases, sin tablas.'
)


def build_requests(model):
    """Materializa solo los seis casos sintéticos versionados, nunca perfiles de entrada."""
    if not isinstance(model, str) or not model.strip():
        raise ValueError('Modelo explícito requerido')
    data = json.loads(DATASET.read_text(encoding='utf-8'))
    if data.get('synthetic_only') is not True or len(data['cases']) != 6:
        raise ValueError('Dataset sintético inválido')
    result = []
    for case in data['cases']:
        if case.get('synthetic') is not True:
            raise ValueError('Caso no sintético')
        # Estados sintéticos explícitos inspirados en perfil 05, no un perfil de navegador.
        state_fixture = {'declarado_cero': {'estado': 'declarado', 'valor': '0'},
                         'desconocido': {'estado': 'no_se'},
                         'omitido': {'estado': 'omitido'},
                         'sin_preguntar': {'estado': 'sin_preguntar'}}
        profile = copy.deepcopy(case['profile'])
        profile['estados_sinteticos_05'] = state_fixture
        relevant = copy.deepcopy(case['relevant_projection'])
        if case['case_id'] == 'SYN-05-DATOS-NO-DECLARADOS':
            relevant['estados_sinteticos_05'] = copy.deepcopy(state_fixture)
        for variant in ('A', 'B', 'C'):
            context = None if variant == 'A' else (relevant if variant == 'B' else profile)
            question = case['question']
            if case['case_id'] == 'SYN-01-LIQUIDEZ':
                question += ' ¿Es correcto afirmar que ahorrar es guardar dinero sin riesgo? Explica también la inflación.'
            user = 'Evidencia sintética: ' + json.dumps(case['fixed_evidence'], ensure_ascii=False, sort_keys=True)
            if context is not None:
                user += '\nContexto sintético: ' + json.dumps(context, ensure_ascii=False, sort_keys=True)
            user += '\nPregunta: ' + question
            payload = {'model': model, 'messages': [{'role': 'system', 'content': EDUCATIONAL_PROMPT},
                                                   {'role': 'user', 'content': user}],
                       'max_tokens': MAX_TOKENS, 'reasoning_effort': 'low', 'include_reasoning': False}
            size = len(json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
            if size > MAX_BYTES:
                raise ValueError('Solicitud supera 16 KiB')
            result.append({'case_id': case['case_id'], 'variant': variant, 'payload': payload,
                           'request_bytes': size, 'expected_facts': copy.deepcopy(case['expected_facts']),
                           'critical_errors': copy.deepcopy(case['critical_errors'])})
    return result


def run_benchmark(provider, model, *, max_calls=18, test_only=False):
    """Callback(payload) -> {status, text, usage?}; sin retries ni transporte propio."""
    if not callable(provider) or type(max_calls) is not int or not 0 <= max_calls <= MAX_CALLS:
        raise ValueError('Callback y presupuesto entero entre 0 y 18 requeridos')
    requests = build_requests(model)
    if type(test_only) is not bool:
        raise ValueError('test_only debe ser booleano')
    report = {'attempted_calls': 0, 'results': [], 'stop_reason': 'complete', 'winner': None,
              'provenance': 'test_only' if test_only else 'provider_unverified',
              'real_model_result_count': 0 if test_only else None}
    for request in requests:
        if report['attempted_calls'] >= max_calls:
            report['stop_reason'] = 'budget_exhausted'
            break
        report['attempted_calls'] += 1
        try:
            response = provider(copy.deepcopy(request['payload']))
        except Exception:
            report['stop_reason'] = 'provider_error'
            break
        if not isinstance(response, dict) or type(response.get('status')) is not int:
            report['stop_reason'] = 'invalid_response'
            break
        status = response['status']
        if status != 200:
            reason = response.get('error_code')
            known = {'response_truncated', 'model_refused', 'model_unfinished', 'unauthorized',
                     'invalid_response', 'timeout', 'disabled', 'rate_limited', 'transport_error',
                     'not_configured', 'provider_rejected', 'provider_unavailable', 'invalid_request'}
            reason = reason if type(reason) is str and reason in known else None
            report['stop_reason'] = ('http_429' if status == 429 else
                                     reason if reason in {'response_truncated', 'model_refused', 'model_unfinished'} else 'provider_error')
            diagnostic = response.get('diagnostic')
            safe = {}
            if type(diagnostic) is dict:
                for key in ('http_status', 'tool_call_count'):
                    value = diagnostic.get(key)
                    if type(value) is int and 0 <= value <= 65536:
                        safe[key] = value
                for key in ('has_content', 'has_reasoning'):
                    if type(diagnostic.get(key)) is bool:
                        safe[key] = diagnostic[key]
                finish = diagnostic.get('finish_reason')
                if type(finish) is str and finish in {'stop', 'length', 'tool_calls', 'content_filter'}:
                    safe['finish_reason'] = finish
            report['failed_case'] = {'case_id': request['case_id'], 'variant': request['variant'],
                                     'callback_status': status, 'error_code': reason, 'diagnostic': safe}
            break
        if not isinstance(response.get('text'), str) or not response['text'].strip():
            report['stop_reason'] = 'invalid_response'
            break
        flags = assess_financial_text(response['text'])
        if flags:
            report['stop_reason'] = 'financial_quality_rejected'
            report['failed_case'] = {'case_id': request['case_id'], 'variant': request['variant'],
                                     'callback_status': status, 'quality_flags': list(flags)}
            break
        report['results'].append({'case_id': request['case_id'], 'variant': request['variant'],
                                  'text': response['text'],
                                  'latency_ms': response.get('latency_ms') if type(response.get('latency_ms')) in (int, float) and math.isfinite(response['latency_ms']) and response['latency_ms'] >= 0 else None,
                                  'usage': response.get('usage'),
                                  'cost': response.get('cost'), 'request_bytes': request['request_bytes'],
                                  'human_review': None})
    return report
