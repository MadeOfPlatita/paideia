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


HORIZONTE_LABELS = {
    'menos_6_meses': 'menos de 6 meses',
    '6_12_meses': 'entre 6 y 12 meses',
    '1_3_anos': 'entre 1 y 3 años',
    'mas_3_anos': 'más de 3 años',
    'sin_fecha': 'sin fecha fijada',
}
OBJETIVO_LABELS = {
    'colchon_imprevistos': 'un colchón para imprevistos',
    'gasto_previsto': 'un gasto previsto',
    'ahorro_largo_plazo': 'ahorro a largo plazo',
    'entender_riesgo': 'entender el riesgo',
    'comparar_familias': 'comparar familias de producto',
    'aprender_conceptos': 'aprender conceptos',
    'curiosear': 'explorar sin objetivo fijo',
}


def _euros(valor):
    def miles(numero):
        entero, _, decimales = numero.partition('.')
        salida = ''
        while len(entero) > 3:
            salida = '.' + entero[-3:] + salida
            entero = entero[:-3]
        salida = entero + salida
        return salida + (',' + decimales if decimales else '')
    return miles(valor['min_eur']) + '–' + miles(valor['max_eur']) + ' €'


def profile_echo(fields):
    """Frase del servidor con los campos declarados del mapa, sin inventar nada.

    Solo viaja lo que la persona marcó como `declarado`; `no_se`, `omitido` y
    `sin_preguntar` no aparecen. Devuelve "" si no hay ningún dato declarado.
    """
    partes = []
    horizonte = fields.get('respuestas.horizonte') or {}
    if horizonte.get('estado') == 'declarado' and horizonte.get('valor') in HORIZONTE_LABELS:
        partes.append('horizonte ' + HORIZONTE_LABELS[horizonte['valor']])
    objetivo = fields.get('respuestas.objetivo') or {}
    if objetivo.get('estado') == 'declarado' and objetivo.get('valor') in OBJETIVO_LABELS:
        partes.append('objetivo ' + OBJETIVO_LABELS[objetivo['valor']])
    importe = fields.get('detalle_economico.importe_objetivo') or {}
    if importe.get('estado') == 'declarado' and type(importe.get('valor')) is dict:
        partes.append('importe objetivo ' + _euros(importe['valor']))
    colchon = fields.get('detalle_economico.colchon_liquido') or {}
    if colchon.get('estado') == 'declarado' and type(colchon.get('valor')) is dict:
        partes.append('colchón disponible ' + _euros(colchon['valor']))
    if not partes:
        return ''
    return 'Según el mapa que tú has autorizado: ' + '; '.join(partes) + '.'
