// El markdown del modelo no puede llegar crudo a la pantalla.
//
// Medido EN PANTALLA con la pregunta «¿qué es la TAE y en qué se diferencia del
// TIN?»: la respuesta era correcta pero se veían a la vista
//
//     ## La diferencia en una frase
//     ## Errores comunes  1. Creer que la TAE siempre sube.
//     La TAE (Tasa Anual Equivalente; en inglés *APR*) es el tipo *i* que…
//     - Gastos que paga el cliente
//
// Almohadillas, asteriscos y listas con guion. Eso es lo que hace que una respuesta
// parezca un volcado técnico en vez de una conversación.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

function cargarChatPlain() {
  const src = fs.readFileSync(APP, 'utf8');
  const i = src.indexOf('function chatPlain');
  const j = src.indexOf('function chatMoney', i);
  assert.ok(i > 0 && j > i, 'no se encontró chatPlain en app.js');
  const ctx = { console };
  vm.createContext(ctx);
  vm.runInContext(src.slice(i, j), ctx);
  return ctx.chatPlain;
}

const REAL = [
  'El TIN, por sí solo, no te dice el rendimiento real.',
  '',
  '## La diferencia en una frase',
  '',
  'El TIN es el tipo pactado sin más; la TAE incorpora comisiones.',
  '',
  '## Errores comunes',
  '',
  '1. Creer que la TAE siempre sube.',
  '2. Comparar TIN con TAE.',
  '',
  '- Gastos necesarios para obtener el producto',
  '- Comisiones futuras por incumplimiento',
  '',
  'La TAE (*APR* en inglés) es el tipo *i* que iguala los flujos.',
].join('\n');

test('no quedan almohadillas de encabezado a la vista', () => {
  const chatPlain = cargarChatPlain();
  const limpio = chatPlain(REAL);
  assert.ok(!limpio.includes('#'), `quedan almohadillas: ${limpio}`);
  // El texto del encabezado sí se conserva.
  assert.ok(limpio.includes('La diferencia en una frase'), limpio);
  assert.ok(limpio.includes('Errores comunes'), limpio);
});

test('no quedan asteriscos de negrita ni de cursiva a la vista', () => {
  const chatPlain = cargarChatPlain();
  const limpio = chatPlain(REAL);
  assert.ok(!limpio.includes('*'), `quedan asteriscos: ${limpio}`);
  // Y el contenido se conserva.
  assert.ok(limpio.includes('APR'), limpio);
  assert.ok(limpio.includes('el tipo i que iguala'), limpio);
});

test('las listas se ven con viñeta, no con guion de markdown', () => {
  const chatPlain = cargarChatPlain();
  const limpio = chatPlain(REAL);
  assert.ok(limpio.includes('• Gastos necesarios'), `sin viñeta: ${limpio}`);
  assert.ok(!/^-\s/m.test(limpio), `queda guion de markdown: ${limpio}`);
});

test('la numeración de una lista se conserva', () => {
  const chatPlain = cargarChatPlain();
  const limpio = chatPlain(REAL);
  assert.ok(limpio.includes('1. Creer que la TAE'), limpio);
  assert.ok(limpio.includes('2. Comparar TIN con TAE'), limpio);
});

test('no se come el texto normal ni los importes', () => {
  const chatPlain = cargarChatPlain();
  const limpio = chatPlain('Si dejas 2.000,00 € al 2,00 % acabas con 2.040,00 €.');
  assert.strictEqual(limpio, 'Si dejas 2.000,00 € al 2,00 % acabas con 2.040,00 €.');
});

test('un valor no textual no rompe el render', () => {
  const chatPlain = cargarChatPlain();
  for (const valor of [null, undefined, 42, {}, []]) {
    assert.strictEqual(chatPlain(valor), '', `debe devolver cadena vacía para ${valor}`);
  }
});
