"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const model = require('../static/profile_model.js');

test('Continue requires a valid explicit answer; zero and deliberate non-disclosure remain valid', () => {
  assert.equal(typeof model.canContinueAnswer, 'function', 'explicit progression validation must exist');
  const path = 'detalle_economico.importe_objetivo';
  for (const answer of [undefined, null, model.makeAnswer('sin_preguntar')]) {
    assert.equal(model.canContinueAnswer(path, answer), false);
  }
  assert.equal(model.canContinueAnswer(path, model.makeAmountAnswer('0')), true);
  assert.equal(model.canContinueAnswer(path, model.makeAnswer('no_se')), true);
  assert.equal(model.canContinueAnswer(path, model.makeAnswer('omitido')), true);
});

test('Declared debt requires an explicit amount or non-disclosure choice for each visible subquestion', () => {
  assert.equal(typeof model.canContinueAnswer, 'function');
  const value = {situacion:'con_deuda', saldo_eur:model.makeAmountAnswer('0'),
    cuota:model.makeFlowAnswer('0','mensual'), coste_anual_pct:model.makeAnswer('sin_preguntar')};
  assert.equal(model.canContinueAnswer('detalle_economico.deuda', model.makeAnswer('declarado', value)), false);
  value.coste_anual_pct = model.makeAnswer('no_se');
  assert.equal(model.canContinueAnswer('detalle_economico.deuda', model.makeAnswer('declarado', value)), true);
  assert.equal(model.canContinueAnswer('detalle_economico.deuda', model.makeAnswer('declarado', {situacion:'sin_deuda'})), true);
});

test('experience without topics shows only the level', () => {
  const key = 'objetivo.experiencia';
  const answer = model.makeAnswer('declarado', { nivel: 'principiante', temas_interes: [] });
  const texto = model.formatAnswer(key, answer);
  assert.equal(/Sin temas seleccionados/.test(texto), false, texto);
  assert.ok(texto.length > 0, 'debe mostrar el nivel');
});
