'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '../..');
const PROTOTYPE = path.resolve(__dirname, '..');
const API_CORE = path.join(ROOT, 'api', '_core');

const report = require('../static/comparison_report.js');
const provenance = require('../static/scenario_provenance.js');
const conditionsLoad = require('../static/conditions_load.js');

function pythonJSON(script, input) {
  const env = { ...process.env, PYTHONPATH: [PROTOTYPE, API_CORE].join(path.delimiter) };
  const run = spawnSync('python', ['-c', script], { cwd: PROTOTYPE, env, input, encoding: 'utf8' });
  assert.equal(run.status, 0, run.stderr);
  return JSON.parse(run.stdout);
}

// Condiciones reales del catálogo local, con la misma fecha de referencia que usa la app.
const FIXTURE = pythonJSON(`
import datetime, json
from catalogue_conditions import derive
from catalogue_data import CANDIDATES, CURATED
reference = datetime.date(2026, 11, 4)
conditions = derive({"candidates": CANDIDATES}, reference, CURATED)
candidates = {item["candidate_id"]: item for item in CANDIDATES}
products = []
for entry in conditions["products"]:
    candidate = candidates.get(entry["product_id"])
    if candidate:
        effective = (candidate.get("dates") or {}).get("effective") or {}
        products.append({
            "id": entry["product_id"],
            "name": candidate["name_literal"],
            "primary_url": candidate.get("primary_url"),
            "as_of": effective.get("as_of") if isinstance(effective, dict) else None,
        })
    else:
        source = entry.get("source") or {}
        products.append({
            "id": entry["product_id"],
            "name": entry["display_name"],
            "primary_url": source.get("url"),
            "as_of": source.get("retrieved_at"),
        })
print(json.dumps({"conditions": conditions, "products": products}))
`);

const entryOf = (id) => FIXTURE.conditions.products.find((item) => item.product_id === id);
const productOf = (id) => FIXTURE.products.find((item) => item.id === id);
const conditionOf = (id, metric) => entryOf(id).conditions.find((item) => item.metric === metric);

function sourceOf(id, rate) {
  const entry = entryOf(id);
  const condition = entry.conditions.find((item) => item.metric === 'annual_rate_percent');
  return provenance.buildSource({
    product: productOf(id),
    conditionEntry: entry,
    rateCondition: condition,
    termCondition: entry.conditions.find((item) => item.metric === 'term_months') || null,
    rate: rate === undefined ? condition.value : rate
  });
}

function calculation(inputs) {
  return pythonJSON(`
import json, sys, domain
items = json.load(sys.stdin)
print(json.dumps([domain.calculate_scenario({**item, "years": int(item["years"])}) for item in items]))
`, JSON.stringify(inputs));
}

const INPUT_A = { principal: '1000', annual_rate_percent: '2.75', years: '1', monthly_contribution: '20', inflation_percent: '2', method: 'simple' };
const INPUT_B = { principal: '0', annual_rate_percent: '0', years: '1', monthly_contribution: '0', inflation_percent: '0', method: 'compound' };

function snapshotWith(sourceA, sourceB) {
  const results = calculation([INPUT_A, INPUT_B]);
  return {
    schema: 'paideia.scenario-comparison', schema_version: 1,
    scenarios: [INPUT_A, INPUT_B].map((inputs, index) => ({
      id: ['A', 'B'][index], status: 'current', version: 1,
      inputs, result: results[index], source: index ? (sourceB ?? null) : sourceA
    }))
  };
}

test('B6 ACC-01 toma la fecha real de la condición, no un as_of ausente', () => {
  const product = productOf('ACC-01');
  const condition = conditionOf('ACC-01', 'annual_rate_percent');
  assert.equal(product.as_of, null); // la API no publica un as_of respaldado para ACC-01
  assert.equal(condition.retrieved_at, '2026-11-05');
  const source = sourceOf('ACC-01');
  assert.equal(source.retrieved_at, '2026-11-05');
  // La condición viene de la página de la promoción, no del PDF de la ficha.
  assert.equal(source.url, 'https://renaultbank.es/cuenta-contigo-nuevos-clientes/');
  assert.notEqual(source.url, product.primary_url);
  assert.equal(source.condition.value, '2.61');
  assert.equal(source.condition.state, 'known');
  assert.equal(source.condition.effective_to, '2026-11-18');
  assert.equal(source.secondary, false);
});

test('B6 Self Bank conserva su condición de fuente secundaria', () => {
  const entry = entryOf('DEP-SELF-12');
  assert.equal(entry.source.kind, 'secondary_press');
  const source = sourceOf('DEP-SELF-12');
  assert.equal(source.kind, 'secondary_press');
  assert.equal(source.secondary, true);
  assert.equal(source.retrieved_at, '2026-11-03');
  const html = report.render(report.capture(snapshotWith(source)), '2026-11-04T00:00:00.000Z');
  assert.match(html, /fuente secundaria, pendiente de confirmar/i);
});

test('B6 DEP-02 declara tramo, plazo y horizonte distinto sin inventar', () => {
  const source = sourceOf('DEP-02');
  assert.equal(source.term_months, 6);
  assert.equal(source.selected_tier, 'Sin domiciliar ingresos');
  assert.equal(source.tiers.length, 2);
  assert.ok(source.tiers.some((tier) => tier.tae === '3.25' && /nómina/i.test(tier.label)));
  const html = report.render(report.capture(snapshotWith(source)), '2026-11-04T00:00:00.000Z');
  assert.match(html, /2,75 %/);
  assert.match(html, /Sin domiciliar ingresos/);
  assert.match(html, /3,25 %/);
  assert.match(html, /Plazo documentado del producto<\/th><td>6 meses/);
  assert.match(html, /Horizonte del escenario<\/th><td>1 año/);
  assert.match(html, /no coincide con el plazo documentado/i);
});

test('B6 EBN distingue fecha del documento y fecha de consulta', () => {
  const source = sourceOf('DEP-EBN-12');
  assert.equal(source.document_date, '2026-09-29');
  assert.equal(source.retrieved_at, '2026-11-03');
  const html = report.render(report.capture(snapshotWith(source)), '2026-11-04T00:00:00.000Z');
  assert.match(html, /fechado 2026-09-29/);
  assert.match(html, /consultada 2026-11-03/);
  assert.match(html, /coincide con el plazo documentado/i);
});

test('B6 editar capital o inflación conserva procedencia; cambiar la tasa la invalida', () => {
  const source = sourceOf('DEP-02');
  const changedCapital = { ...INPUT_A, principal: '1500', monthly_contribution: '0', inflation_percent: '1', years: '2', method: 'compound' };
  assert.equal(provenance.sourceAfterEdit(source, changedCapital), source);
  assert.equal(provenance.sourceAfterEdit(source, { ...changedCapital, annual_rate_percent: '2.76' }), null);
  assert.equal(provenance.sourceAfterEdit(source, { ...changedCapital, annual_rate_percent: '2.7500' }), source);
  assert.equal(provenance.sourceAfterEdit(null, changedCapital), null);
});

test('B6 copiar A a B conserva una procedencia independiente', () => {
  const source = sourceOf('DEP-SELF-12');
  const copied = provenance.copySource(source);
  assert.deepEqual(copied, source);
  assert.notEqual(copied, source);
  assert.equal(provenance.sourceAfterEdit(copied, { ...INPUT_B, annual_rate_percent: '2.75', principal: '500' }), copied);
  assert.equal(provenance.sourceAfterEdit(copied, { ...INPUT_B, annual_rate_percent: '2.76' }), null);
  assert.equal(source.condition.value, '2.75');
});

test('B6 el fallo de condiciones se distingue de la falta de dato y permite reintentar', () => {
  const loading = conditionsLoad.begin({ loaded: false, loading: false, error: null, byId: new Map(), referenceDate: null });
  assert.equal(loading.loading, true);
  assert.equal(loading.error, null);
  const failed = conditionsLoad.fail(new Error('sin conexión'));
  assert.equal(failed.loaded, false);
  assert.equal(failed.loading, false);
  assert.equal(failed.byId.size, 0);
  assert.equal(failed.error.message, 'sin conexión');
  const notice = conditionsLoad.comparisonNotice(failed);
  assert.equal(notice.kind, 'error');
  assert.equal(notice.retry, true);
  const retry = conditionsLoad.begin(failed);
  assert.equal(retry.error, null);
  assert.equal(retry.loading, true);
  const loaded = conditionsLoad.succeed(FIXTURE.conditions);
  assert.equal(loaded.loaded, true);
  assert.equal(loaded.error, null);
  assert.equal(loaded.byId.size, FIXTURE.conditions.products.length);
  assert.equal(conditionsLoad.comparisonNotice(loaded), null);
  assert.throws(() => conditionsLoad.succeed({ products: 'no-es-lista' }));
});

test('B6 la biblioteca distingue el fallo de condiciones y no convierte tasas vacías en cero', () => {
  const failed = conditionsLoad.fail(new Error('sin conexión'));
  const notice = conditionsLoad.catalogueNotice(failed);
  assert.equal(notice.kind, 'error');
  assert.equal(notice.retry, true);
  assert.match(notice.message, /No se pudieron cargar las condiciones documentadas/i);
  assert.match(notice.message, /no equivale a falta de dato/i);
  assert.equal(conditionsLoad.catalogueNotice(conditionsLoad.begin()).kind, 'loading');
  assert.equal(conditionsLoad.catalogueNotice(conditionsLoad.succeed(FIXTURE.conditions)), null);
  assert.equal(conditionsLoad.formatRate(''), '');
  assert.equal(conditionsLoad.formatRate('   '), '');
  assert.equal(conditionsLoad.formatRate(null), '');
  assert.equal(conditionsLoad.formatRate('2.61'), '2,61 %');
  assert.equal(conditionsLoad.formatRate('0'), '0,00 %');
  const empty = conditionsLoad.rateSummary(conditionsLoad.succeed(FIXTURE.conditions), { state: 'known', value: '', notes: [] });
  assert.equal(empty.kind, 'missing');
  assert.match(empty.text, /(?:no trae|no incluye) una cifra/i);
  const errored = conditionsLoad.rateSummary(failed, null);
  assert.equal(errored.kind, 'error');
  assert.match(errored.text, /No se pudieron cargar las condiciones documentadas/i);
  const real = conditionsLoad.rateSummary(conditionsLoad.succeed(FIXTURE.conditions), conditionOf('ACC-01', 'annual_rate_percent'));
  assert.equal(real.kind, 'verified');
  assert.match(real.text, /2,61 %/);
  assert.doesNotMatch(real.text, /0,00 %/);
});

test('B6 rechaza una URL no HTTPS sin perder la fecha de la condición', () => {
  const source = { ...sourceOf('DEP-02'), url: 'javascript:alert(1)' };
  const html = report.render(report.capture(snapshotWith(source)), '2026-11-04T00:00:00.000Z');
  assert.doesNotMatch(html, /javascript:alert/);
  assert.match(html, /consultada 2026-11-03/);
});

test('B6 el informe real incluye condición, tramo, vigencia y documento sin perfil', () => {
  const source = sourceOf('DEP-02');
  source.profile = 'SECRET_PROFILE_MARKER';
  source.consent = { accepted_chat_processing: true };
  source.owner_email = 'persona@example.com';
  source.tiers[0].label = '<img src=x onerror=alert(1)>';
  const html = report.render(report.capture(snapshotWith(source, sourceOf('DEP-EBN-12'))), '2026-11-04T00:00:00.000Z');
  assert.match(html, /Condición de la tasa/);
  assert.match(html, /documentada; sin fechas de vigencia \(no verificada\)/);
  assert.doesNotMatch(html, /vigente según la fuente/);
  assert.match(html, /Vigencia de la tasa/);
  assert.match(html, /hasta 2026-11-18|sin fecha de fin documentada/);
  assert.match(html, /Fecha del documento/);
  assert.match(html, /Fuentes y fechas/);
  assert.match(html, /No incluye tu mapa de perfil/);
  assert.doesNotMatch(html, /SECRET_PROFILE_MARKER/);
  assert.doesNotMatch(html, /persona@example\.com/);
  assert.doesNotMatch(html, /accepted_chat_processing/);
  assert.doesNotMatch(html, /<img/);
  const documentHtml = report.renderDocument(report.capture(snapshotWith(source)), '2026-11-04T00:00:00.000Z');
  assert.match(documentHtml, /<!doctype html>/i);
  assert.doesNotMatch(documentHtml, /<script/i);
});

test('B6 una condición conocida pero caducada no se presenta como vigente', () => {
  const source = sourceOf('ACC-01');
  assert.equal(source.condition.effective_to, '2026-11-18');
  const expired = report.render(report.capture(snapshotWith(source)), '2026-12-01T00:00:00.000Z');
  assert.doesNotMatch(expired, /vigente según la fuente/i);
  assert.doesNotMatch(expired, /TAE 2,61 % · vigente/i);
  assert.match(expired, /vigencia terminada el 2026-11-18/i);
  assert.match(expired, /no se presenta como oferta vigente/i);
  const current = report.render(report.capture(snapshotWith(source)), '2026-11-04T00:00:00.000Z');
  assert.doesNotMatch(current, /vigente según la fuente/i);
  assert.match(current, /documentada; vigencia declarada hasta 2026-11-18/);
});

test('B6 sin fecha de fin no se afirma vigencia y las fechas imposibles se descartan', () => {
  const source = sourceOf('DEP-EBN-12');
  source.condition.effective_to = '';
  source.condition.retrieved_at = '2026-11-03T10:00:00Z';
  source.condition.effective_from = '2026-13-01';
  source.document_date = '29-09-2026';
  const html = report.render(report.capture(snapshotWith(source)), '2026-11-04T00:00:00.000Z');
  assert.doesNotMatch(html, /vigente según la fuente/i);
  assert.match(html, /sin fecha de fin documentada/i);
  assert.match(html, /La condición no tiene fecha de consulta registrada/i);
  assert.match(html, /Fecha del documento<\/th><td>no indicada en la fuente/i);
  assert.doesNotMatch(html, /2026-11-03T10:00:00Z/);
  assert.doesNotMatch(html, /2026-13-01/);
  assert.doesNotMatch(html, /29-09-2026/);
});

test('B6 valida la fecha de generación del informe', () => {
  const source = sourceOf('ACC-01');
  assert.throws(() => report.render(report.capture(snapshotWith(source)), '2026-02-30T00:00:00.000Z'), /Informe inválido/);
  assert.throws(() => report.render(report.capture(snapshotWith(source)), '2026-11-04T24:00:00.000Z'), /Informe inválido/);
  assert.throws(() => report.render(report.capture(snapshotWith(source)), '2026-11-04T00:00:00Z'), /Informe inválido/);
  assert.doesNotThrow(() => report.render(report.capture(snapshotWith(source)), '2026-11-04T23:59:59.999Z'));
});

test('B6 una tasa vacía no se convierte en 0 %', () => {
  const source = sourceOf('DEP-02');
  source.condition.value = '';
  source.tiers = [{ label: 'Sin requisito', condition: 'sin_requisito', tae: '', tin: '', selected: true }];
  const html = report.render(report.capture(snapshotWith(source)), '2026-11-04T00:00:00.000Z');
  assert.doesNotMatch(html, /0,00 %/);
  assert.match(html, /TAE sin cifra utilizable/);
  assert.equal(report.format('0.00'), '0,00 €');
});

test('B6 la procedencia rechaza fechas imposibles y tasas vacías sin inventar', () => {
  const entry = entryOf('DEP-EBN-12');
  const source = provenance.buildSource({
    product: { id: 'DEP-EBN-12', name: 'Depósito Nuevo Ahorro 12 meses', primary_url: productOf('DEP-EBN-12').primary_url },
    conditionEntry: entry,
    rateCondition: {
      metric: 'annual_rate_percent', state: 'known', value: '', reason: 'CURATED_OFFICIAL',
      effective_from: '2026-13-01', effective_to: '2026-02-30', retrieved_at: '2026-11-03T10:00:00Z'
    },
    termCondition: null,
    rate: ''
  });
  assert.equal(source.condition.value, null);
  assert.equal(source.rate_at_seed, '');
  assert.equal(source.condition.effective_from, '');
  assert.equal(source.condition.effective_to, '');
  assert.equal(source.retrieved_at, '2026-11-03');
  assert.equal(provenance.sourceAfterEdit(source, { annual_rate_percent: '' }), null);
});

