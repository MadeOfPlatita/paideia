// Los números se escriben igual en toda la respuesta.
//
// Medido EN PANTALLA con la pregunta «¿qué TAE tiene el depósito de EBN Banco?»:
// la misma respuesta decía
//
//     «Para eso encaja …: 3,10 % TAE a 12 meses. Pide un mínimo de 5.000 €.»
//     «Depósito Nuevo Ahorro 12 meses — TAE: 3.1 % · Plazo: 12 meses ·
//      Inversión mínima: 5000 €.»
//
// Formato español en el texto y formato máquina en la ficha, en el mismo turno. Se
// ve descuidado y el punto decimal inglés choca con el resto de la aplicación.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

function cargar() {
  const src = fs.readFileSync(APP, 'utf8');
  const ctx = vm.createContext({});
  // Las constantes y las dos funciones de formato, extraídas por sus marcas reales.
  const k = src.indexOf('const CHAT_DECIMAL');
  const finConst = src.indexOf('\n', k);
  const i = src.indexOf('function chatDecimal(value)');
  const j = src.indexOf('// Etiqueta y formato por metrica', i);
  assert.ok(k > 0 && i > k && j > i, 'no se encontraron las funciones de formato');
  vm.runInContext(src.slice(k, finConst) + '\n' + src.slice(i, j), ctx);
  return (valor) => vm.runInContext('chatDecimalEs(' + JSON.stringify(valor) + ')', ctx);
}

test('una tasa se escribe con coma y dos decimales', () => {
  const f = cargar();
  assert.strictEqual(f('3.1'), '3,10');
  assert.strictEqual(f('2.5'), '2,50');
  assert.strictEqual(f('2'), '2,00');
});

test('un importe lleva separador de miles español', () => {
  const f = cargar();
  assert.strictEqual(f('5000'), '5.000,00');
  assert.strictEqual(f('400000'), '400.000,00');
  assert.strictEqual(f('1000000'), '1.000.000,00');
});

test('no se inventa nada con los casos límite', () => {
  const f = cargar();
  assert.strictEqual(f('0'), '0,00');
  assert.strictEqual(f('-3.5'), '-3,50');
  assert.strictEqual(f('1234.56'), '1.234,56');
  // Un valor que no es un número no se formatea: se deja fuera.
  assert.strictEqual(f('sin dato'), '');
  assert.strictEqual(f(''), '');
  assert.strictEqual(f(null), '');
});

test('la ficha de la tarjeta usa el formateador español', () => {
  const src = fs.readFileSync(APP, 'utf8');
  // Los tres casos con unidad numérica pasan por chatDecimalEs.
  const bloque = src.slice(src.indexOf('function chatConditionValue'),
                           src.indexOf('function chatConditionName'));
  for (const unidad of ['PERCENT', 'MONTHS', 'EUR']) {
    const trozo = bloque.slice(bloque.indexOf(`unit === "${unidad}"`));
    const siguiente = trozo.slice(0, trozo.indexOf('}'));
    assert.ok(siguiente.includes('chatDecimalEs('),
      `${unidad} debe formatearse con chatDecimalEs, no con el valor crudo`);
  }
});
