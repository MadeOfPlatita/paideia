// La cifra del catálogo va SIEMPRE con su fuente y su fecha.
//
// Medido EN PANTALLA recorriendo la biblioteca de producción: 22 fichas, 25 fuentes
// distintas y CERO fechas. La tarjeta decía «TAE documentada: 3,10 %» y
// «Documentadas con fuente», sin decir de cuándo era el dato.
//
// El criterio del producto es «catálogo fiable con fuente y fecha»: una cifra sin
// fecha no se puede situar en el tiempo y el usuario no sabe si está viendo algo de
// esta semana o algo de hace tres años. Este test fija que la fecha acompaña.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

function cargarEvidencia() {
  const src = fs.readFileSync(APP, 'utf8');
  // La función que compone la línea de evidencia de la tarjeta.
  const i = src.indexOf('function headlineMetric');
  assert.ok(i > 0, 'no se encontró rateEvidence');
  const j = src.indexOf('\n}', i) + 2;
  const ctx = vm.createContext({ String });
  vm.runInContext(src.slice(i, j), ctx);
  return ctx;
}

test('la tarjeta declara la fecha de consulta junto a la cifra', () => {
  const src = fs.readFileSync(APP, 'utf8');
  // La línea de evidencia debe incluir la fecha: no basta con «documentada».
  assert.match(src, /consultada el \$\{cuando\}/,
    'la cifra debe ir acompañada de su fecha de consulta');
  assert.match(src, /sin fecha de consulta/,
    'si no hay fecha, se declara en vez de omitirse');
});

test('la fuente y la fecha viajan en el DTO de la condición', () => {
  const src = fs.readFileSync(APP, 'utf8');
  const bloque = src.slice(src.indexOf('function headlineMetric'),
                           src.indexOf('function headlineMetric') + 1600);
  // La fecha se resuelve con `conditionConsultedAt`, que lee `retrieved_at` de la
  // condición y, si no está, de su fuente. Se comprueba la cadena completa: que la
  // tarjeta la use Y que la resolución lea el campo real del DTO.
  assert.ok(bloque.includes('conditionConsultedAt'),
    'la tarjeta debe resolver la fecha con conditionConsultedAt');
  const resolutor = src.slice(src.indexOf('function conditionConsultedAt'),
                              src.indexOf('function conditionConsultedAt') + 700);
  assert.ok(resolutor.includes('retrieved_at'),
    'conditionConsultedAt debe leer retrieved_at del DTO');
  assert.ok(resolutor.includes('entry.source'),
    'y también la fuente del registro, como respaldo');
});

test('una cifra sin fecha no se presenta como dato verificado sin más', () => {
  const src = fs.readFileSync(APP, 'utf8');
  const bloque = src.slice(src.indexOf('function headlineMetric'),
                           src.indexOf('function headlineMetric') + 1400);
  // El texto de la fecha es obligatorio en la rama que devuelve «verified».
  const rama = bloque.slice(bloque.indexOf('kind: "verified"') - 260,
                            bloque.indexOf('kind: "verified"') + 60);
  assert.ok(/fecha/.test(rama),
    `la rama «verified» debe mencionar la fecha: ${rama}`);
});
