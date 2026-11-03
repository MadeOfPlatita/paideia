"""Closed, server-owned editorial projection for synthetic offline trials only."""
import domain

VERSION = "paideia-education-v1"
# Locally authored educational copy; no external review or product endorsement implied.
EDITORIAL = {
    "saving_investing": "Ahorrar e invertir son decisiones distintas; una inversión puede perder valor y sus resultados son inciertos.",
    "risk": "Los riesgos dependen del producto, de la entidad y de la custodia; conviene revisar sus condiciones antes de decidir.",
    "inflation": "La inflación puede reducir el poder adquisitivo del dinero aunque su importe nominal no cambie.",
    "guarantees": "La existencia y el alcance de una garantía dependen de las condiciones aplicables; no deben suponerse sin verificarlas.",
    "simulation": "Una simulación es hipotética y depende de sus supuestos; no predice resultados futuros ni incluye necesariamente costes o impuestos.",
}


def render_selection(selection, scenario=None, *, scenario_present=False):
    """Render a closed provider selection using only this request's user inputs."""
    if type(selection) is not dict or set(selection) != {"version", "intent", "claim_ids"}:
        raise ValueError("invalid selection")
    if type(selection['version']) is not str or selection['version'] != VERSION:
        raise ValueError("invalid version")
    intent = selection['intent']
    if type(intent) is not str or intent not in ('explain', 'calculate'):
        raise ValueError("invalid intent")
    ids = selection['claim_ids']
    if (type(ids) is not list or not 1 <= len(ids) <= len(EDITORIAL)
            or any(type(i) is not str or i not in EDITORIAL for i in ids)
            or len(ids) != len(set(ids))):
        raise ValueError("invalid claims")
    calculation = None
    if intent == 'calculate':
        if not scenario_present or type(scenario) is not dict or set(scenario) != domain.CALCULATION_FIELDS:
            raise ValueError("invalid scenario")
        if any(type(value) is not (int if key == 'years' else str) for key, value in scenario.items()):
            raise ValueError("invalid scenario types")
        domain.parse_amount(scenario['principal'], 'principal')
        domain.parse_amount(scenario['monthly_contribution'], 'monthly_contribution')
        domain.parse_percent(scenario['annual_rate_percent'], 'annual_rate_percent')
        domain.parse_percent(scenario['inflation_percent'], 'inflation_percent')
        if not 1 <= scenario['years'] <= 40 or scenario['method'] not in ('simple', 'compound'):
            raise ValueError("invalid scenario values")
        calculation = {'source': 'deterministic_local', 'data': domain.calculate_scenario(scenario)}
    elif scenario_present:
        raise ValueError("unexpected scenario")
    items = [{'id': i, 'text': EDITORIAL[i]} for i in ids]
    return {'answer': '\n\n'.join(item['text'] for item in items),
            'provider_mode': 'test_only', 'external_sent': False,
            'structured_education': {'version': VERSION, 'kind': 'editorial',
                                     'items': items, 'calculation': calculation}}
