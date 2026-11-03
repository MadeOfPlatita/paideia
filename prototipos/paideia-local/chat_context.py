"""Strict synthetic-only chat projection and untrusted conversation DTOs."""
import json
import re
from decimal import Decimal

NOTICE = 'paideia-chat-context-map-v1'
VERSION = 'chat-context-map-v1'
CHOICES = {
    'respuestas.objetivo': {'colchon_imprevistos','gasto_previsto','ahorro_largo_plazo','entender_riesgo','comparar_familias','aprender_conceptos','curiosear'},
    'respuestas.horizonte': {'menos_6_meses','6_12_meses','1_3_anos','mas_3_anos','sin_fecha'},
}
AMOUNTS = {'detalle_economico.importe_objetivo', 'detalle_economico.colchon_liquido'}
FIELDS = frozenset(CHOICES) | AMOUNTS
DECIMAL = re.compile(r'(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?\Z')


def validate_context(context):
    if type(context) is not dict or set(context) != {'version','fields'} or context['version'] != VERSION:
        raise ValueError('context version')
    fields = context['fields']
    if type(fields) is not dict or not fields or not set(fields) <= FIELDS:
        raise ValueError('fields')
    for key, answer in fields.items():
        if type(answer) is not dict or answer.get('estado') not in {'declarado','no_se','omitido','sin_preguntar'}:
            raise ValueError('answer')
        if answer['estado'] != 'declarado':
            if set(answer) != {'estado'}: raise ValueError('state')
            continue
        if set(answer) != {'estado','valor'}: raise ValueError('value')
        value = answer['valor']
        if key in CHOICES:
            if type(value) is not str or value not in CHOICES[key]: raise ValueError('choice')
        else:
            if type(value) is not dict or set(value) != {'min_eur','max_eur','moneda'} or value['moneda'] != 'EUR': raise ValueError('amount')
            if any(type(value[k]) is not str or not DECIMAL.fullmatch(value[k]) for k in ('min_eur','max_eur')): raise ValueError('decimal')
            if Decimal(value['min_eur']) > Decimal(value['max_eur']): raise ValueError('range')
    return json.dumps(context, ensure_ascii=False, separators=(',', ':'))


def validate_history(history):
    if type(history) is not list or len(history) > 4 or len(history) % 2:
        raise ValueError('history size')
    for i, item in enumerate(history):
        if (type(item) is not dict or set(item) != {'role','content'} or item['role'] != ('user' if i % 2 == 0 else 'assistant')
                or type(item['content']) is not str or not 1 <= len(item['content']) <= 1000):
            raise ValueError('history message')
    if sum(len(m['content']) for m in history) > 6000: raise ValueError('history characters')
    return [{'role': item['role'], 'content': item['content']} for item in history]
