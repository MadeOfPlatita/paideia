// El comparador escribe los números en castellano, venga la unidad como venga.
//
// Medido EN PANTALLA con dos Letras del Tesoro: la misma tarjeta decía
//
//     «Rentabilidad 2,645 %»      (bien)
//     «Precio 99,336 %»           (bien)
//     «Saldo en circulación 8780.5»   <- punto decimal inglés, sin unidad
//     «Precio medio 99,339 %»         (bien)
//
// El saldo se quedaba crudo porque su unidad en el catálogo es «millones EUR», no
// «EUR», y el formateador solo entendía una lista cerrada de unidades
// (PERCENT/MONTHS/EUR). Todo lo demás caía al valor tal cual.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

function cargarComparisonValue() {
  const src = fs.readFileSync(APP, 'utf8');
  const i = src.indexOf('function comparisonValue');
  assert.ok(i > 0, 'no se encontró comparisonValue');
  // Hasta la función siguiente, por su marca real.
  const j = src.indexOf('function renderComparisonResult()', i);
  assert.ok(j > i, 'no se encontró el final de comparisonValue');
  const ctx = vm.createContext({ Number, Intl, String });
  vm.runInContext(src.slice(i, j), ctx);
  return (cond) => vm.runInContext(
    'comparisonValue(' + JSON.stringify(cond) + ')', ctx);
}

test('el saldo vivo se escribe con separador de miles y su unidad', () => {
  const f = cargarComparisonValue();
  const salida = f({ metric: 'saldo_vivo', value: '8780.5', unit: 'millones EUR', state: 'known' });
  assert.ok(!salida.includes('8780.5'),
    `no puede quedar el punto decimal inglés: ${salida}`);
  assert.match(salida, /8\.780,5/,
    `debe llevar separador de miles español: ${salida}`);
  assert.match(salida, /M€/, `debe declarar la unidad: ${salida}`);
});

test('un porcentaje con unidad compuesta se formatea como porcentaje', () => {
  const f = cargarComparisonValue();
  const salida = f({ metric: 'precio_medio', value: '99.339', unit: '% del nominal', state: 'known' });
  assert.match(salida, /99,339\s*%/, salida);
  assert.ok(!salida.includes('99.339'), salida);
});

test('un porcentaje simple también', () => {
  const f = cargarComparisonValue();
  assert.match(f({ metric: 'annual_rate_percent', value: '2.645', unit: 'PERCENT', state: 'known' }),
    /2,645\s*%/, 'la rentabilidad de la letra');
});

test('un importe grande en euros lleva separadores', () => {
  const f = cargarComparisonValue();
  const salida = f({ metric: 'nominal_adjudicado', value: '751690000', unit: 'EUR', state: 'known' });
  assert.match(salida, /751\.690\.000/, salida);
});

test('un plazo se dice en meses', () => {
  const f = cargarComparisonValue();
  assert.match(f({ metric: 'term_months', value: '12', unit: 'MONTHS', state: 'known' }),
    /12\s*meses/, 'el plazo');
});

test('lo vencido y lo desconocido se declaran, no se disfrazan', () => {
  const f = cargarComparisonValue();
  assert.match(f({ metric: 'annual_rate_percent', value: '3.0', unit: 'PERCENT', state: 'stale' }),
    /vencida/, 'una tasa vencida se marca');
  assert.strictEqual(f({ metric: 'x', value: '', unit: 'PERCENT', state: 'unknown' }),
    'sin valor documentado');
});

test('un texto libre no se toca', () => {
  const f = cargarComparisonValue();
  assert.strictEqual(f({ metric: 'x', value: 'Según la ficha', unit: 'TEXT', state: 'known' }),
    'Según la ficha');
});
