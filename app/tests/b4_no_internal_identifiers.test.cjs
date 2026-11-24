// La interfaz no publica identificadores internos del backend.
//
// Bug real reportado con una captura: el chat decía «Clase de la fuente: Oficial,
// unknown.» — la palabra inglesa «unknown» en medio de una frase en castellano.
// La causa era `tabla[valor] || valor`: el fallback devolvía el valor crudo.
//
// Al revisarlo aparecieron más fugas: `humanMetricLabel` solo traducía 12 de las 76
// métricas reales del catálogo, así que la ficha del comparador pintaba «annual rate
// percent», «custody fee percent», «securities lending», «retail access»… en inglés.
//
// Este test extrae las tablas y funciones reales de app.js y las comprueba contra
// las métricas que el catálogo usa de verdad.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

// Las 76 métricas reales del catálogo, medidas con ConditionsService().describe().
const METRICAS_REALES = [
  'account_domicile', 'annual_cost_figure', 'annual_rate_percent', 'auction_date',
  'availability', 'average_price_percent', 'average_rate_percent', 'awarded_nominal_eur',
  'base_currency', 'category', 'cnmv_registration_date', 'cnmv_registry',
  'cost_impact_1y_percent', 'cost_impact_5y_percent', 'custody_fee_percent', 'data_date',
  'declared_fees', 'deposit_guarantee_fund', 'depositary', 'direct_debits',
  'distribution_policy', 'document_date', 'early_cancellation', 'eligibility',
  'entry_fee_percent', 'exit_fee_percent', 'fund_assets_eur', 'fund_investors',
  'holding_period_years', 'interest_basis', 'isin', 'last_prospectus_date',
  'last_regulation_date', 'launch_date', 'lock_in', 'main_market',
  'management_fee_percent', 'manager', 'marginal_rate_percent', 'maturity_date',
  'maximum_eur', 'maximum_note', 'minimum_eur', 'minimum_horizon', 'minimum_note',
  'minimum_price_percent', 'nav_eur', 'nominal_rate_percent', 'operating_costs',
  'outstanding_balance', 'ownership', 'performance_fee_percent', 'promotion_window',
  'recommended_horizon', 'registration_date', 'registry_countries', 'renewal',
  'replication', 'requirement', 'retail_access', 'risk_scale', 'securities_lending',
  'settlement', 'settlement_date', 'sfdr_article', 'share_class_currency',
  'spain_registry', 'subscription_redemption', 'subsequent_nominal_rate_percent',
  'subsequent_rate_note', 'subsequent_rate_percent', 'ter_percent', 'term_months',
  'ucits', 'vehicle_type', 'withholding_percent',
];

// Valores de enum que el backend emite de verdad. Cualquier fallback que devuelva
// el valor crudo se detecta porque coincide con la entrada.
const ESTADOS_FUENTE = ['official', 'secondary', 'mixed', 'unknown', 'identity',
  'curated', 'inferred', 'press_documented', 'condition_source', 'press'];

function setup() {
  const code = fs.readFileSync(APP, 'utf8');
  const ctx = { console };
  vm.createContext(ctx);
  // Se evalúan solo las constantes de traducción y sus funciones, que son de nivel
  // de módulo (no viven dentro de renderHome).
  const bloque = (desde, hasta) => {
    const inicio = code.indexOf(desde);
    const fin = code.indexOf(hasta, inicio);
    assert.ok(inicio > 0 && fin > inicio, `bloque no encontrado: ${desde}`);
    return code.slice(inicio, fin);
  };
  vm.runInContext(
    bloque('const SOURCE_CLASS_ES = {', 'function renderChatProvenance')
    + '\n'
    + bloque('const METRIC_ES = {', '// Valor legible de una condición para el comparador'),
    ctx,
  );
  return ctx;
}

test('ninguna métrica real del catálogo se pinta en inglés', () => {
  const ctx = setup();
  const sinTraducir = METRICAS_REALES.filter((metrica) => {
    const etiqueta = ctx.humanMetricLabel(metrica);
    // Se considera fuga si la etiqueta es el identificador, con guiones bajos
    // vueltos espacios, o contiene palabras inglesas del propio identificador.
    return etiqueta === metrica
      || etiqueta === metrica.replace(/_/g, ' ')
      || /rate percent|fee percent|_|guarantee fund|securities lending|retail access|nav eur|sfdr article|spain registry/.test(etiqueta);
  });
  assert.deepStrictEqual(sinTraducir, [],
    `estas métricas se publican sin traducir: ${sinTraducir.join(', ')}`);
});

test('una métrica desconocida no se publica como identificador', () => {
  const ctx = setup();
  const etiqueta = ctx.humanMetricLabel('metrica_inventada_del_futuro');
  assert.notStrictEqual(etiqueta, 'metrica_inventada_del_futuro');
  assert.ok(!/_/.test(etiqueta), `no debe llevar guiones bajos: ${etiqueta}`);
  assert.ok(/no catalogada|Condición/i.test(etiqueta), etiqueta);
});

test('ninguna clase de fuente se devuelve en crudo', () => {
  const ctx = setup();
  for (const valor of ESTADOS_FUENTE) {
    const texto = ctx.humanSourceClass(valor);
    assert.notStrictEqual(texto, valor, `«${valor}» se devuelve en crudo`);
    assert.ok(!/^[a-z_]+$/.test(texto) || texto.includes(' '),
      `«${valor}» → «${texto}» parece un identificador, no una etiqueta`);
  }
});

test('el caso reportado: «unknown» ya no aparece en castellano', () => {
  const ctx = setup();
  const texto = ctx.humanSourceClass('unknown');
  assert.notStrictEqual(texto.toLowerCase(), 'unknown');
  assert.match(texto, /procedencia|sin identificar/i);
});

test('un valor vacío o ausente no rompe la etiqueta', () => {
  const ctx = setup();
  for (const valor of [null, undefined, '', 0, {}, []]) {
    const etiqueta = ctx.humanMetricLabel(valor);
    assert.strictEqual(typeof etiqueta, 'string');
    assert.ok(etiqueta.length > 0);
    const fuente = ctx.humanSourceClass(valor);
    assert.strictEqual(typeof fuente, 'string');
    assert.ok(fuente.length > 0);
  }
});
