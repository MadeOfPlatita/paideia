'use strict';
// El aviso de omisión debe decir el motivo real, no uno genérico de fuente oficial.
const test = require('node:test');
const assert = require('node:assert/strict');
const notice = require('../static/chat_withheld_notice.js');

const OFFICIAL = /fuente oficial|vigencia/i;

test('una cifra retenida se explica como cifra, no como fuente oficial', () => {
  const text = notice.notice({ reason: 'figure', hasCalculation: false, catalogueUsed: false });
  assert.match(text, /cifra|porcentaje|importe/i);
  assert.doesNotMatch(text, OFFICIAL);
});

test('una atribución retenida se explica como atribución', () => {
  const text = notice.notice({ reason: 'attribution', hasCalculation: false, catalogueUsed: false });
  assert.match(text, /fuente|vigencia|confirmaci/i);
});

test('un identificador retenido se explica como identificador', () => {
  const text = notice.notice({ reason: 'identifier', hasCalculation: false, catalogueUsed: false });
  assert.match(text, /identificador/i);
});

test('un texto sin forma comprobable se explica sin inventar el motivo', () => {
  const text = notice.notice({ reason: 'invalid', hasCalculation: false, catalogueUsed: false });
  assert.match(text, /forma|comprobar|verificar/i);
  assert.doesNotMatch(text, OFFICIAL);
});

test('un turno de calculadora se explica como calculadora', () => {
  const text = notice.notice({ reason: '', hasCalculation: true, catalogueUsed: false });
  assert.match(text, /calculadora|motor/i);
});

test('un turno de catálogo se explica como catálogo', () => {
  const text = notice.notice({ reason: 'figure', hasCalculation: false, catalogueUsed: true });
  assert.match(text, /catálogo/i);
});

test('un motivo desconocido no se convierte en una acusación de fuente oficial', () => {
  for (const reason of ['', 'raro', undefined]) {
    const text = notice.notice({ reason, hasCalculation: false, catalogueUsed: false });
    assert.ok(typeof text === 'string' && text.length > 20);
    assert.doesNotMatch(text, OFFICIAL);
    assert.match(text, /no se muestra|omitido/i);
  }
});

test('la entrada inválida no rompe el aviso', () => {
  for (const value of [null, undefined, 42, 'x', []]) {
    const text = notice.notice(value);
    assert.ok(typeof text === 'string' && text.length > 20);
    assert.doesNotMatch(text, OFFICIAL);
  }
});
