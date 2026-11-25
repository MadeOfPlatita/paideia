// La interfaz no muestra inglés ni jerga de ingeniería.
//
// Familia de fallos ya vista tres veces en este proyecto: «unknown» suelto en una
// frase castellana, «PROMOTION_EXPIRED» impreso en el informe descargable y
// «quantitative_ready=false» en el comparador. Todos son el mismo error: un valor
// interno (enumerado, código de error, nombre de campo) cae en un texto que lee
// una persona.
//
// Este test no ejecuta la interfaz: recorre las cadenas literales de los módulos
// de app/static/ y las clasifica en dos grupos.
//
//   - Prosa: el literal tiene palabras castellanas y espacios entre ellas. Es lo
//     que se pinta en pantalla, así que se le exige castellano limpio.
//   - Suelto: el literal es un identificador, una clave, un valor de enum o una
//     clase CSS («input», «pending», «status-chip»). Es interno y no se toca.
//
// Antes de juzgar se sustituyen las interpolaciones `${…}` y los literales
// anidados por un marcador: dentro de una plantilla, `source.url` o `true` son
// código, no texto. Solo se juzga lo que queda alrededor.
//
// El último test es la regresión: reintroduce «unknown» en un mensaje visible y
// comprueba que el detector se pone rojo.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const STATIC = path.join(__dirname, '..', 'static');
const MODULOS = [
  'app.js', 'comparison_report.js', 'claims_view.js', 'chat_withheld_notice.js',
  'conditions_load.js', 'profile_model.js', 'structured_education_ui.js',
  'scenario_provenance.js', 'chat_context_model.js', 'context_help.js',
];

// Palabras inglesas que no son también castellanas. Se excluyen a propósito los
// homógrafos («error», «no», «es», «son») y los nombres aceptados en el dominio
// («ETF», «UCITS», «ISIN», «TAE», «TIN», «TER», «EUR»).
const INGLES = new Set([
  'unknown', 'pending', 'expired', 'primary', 'drift', 'evidence', 'status',
  'loading', 'missing', 'stale', 'ready', 'summary', 'balance', 'source',
  'sources', 'backend', 'endpoint', 'timeout', 'ticket', 'ranking', 'fixture',
  'fixtures', 'checksum', 'payload', 'cache', 'slot', 'scope', 'dataset',
  'enabled', 'disabled', 'failed', 'failure', 'warning', 'null', 'undefined',
  'true', 'false', 'income', 'tool', 'tools',
]);

// Jerga de ingeniería: se entiende, pero no se le dice a un estudiante.
const JERGA = new Set([
  'backend', 'endpoint', 'metadatos', 'metadato', 'determinista',
  'semánticamente', 'idempotente', 'serializar', 'payload', 'checksum',
  'preflight', 'toctou', 'fixtures',
]);

// Artículos, preposiciones y pronombres que solo aparecen en una frase
// castellana: su presencia marca el literal como texto de pantalla.
const PROSA = new Set([
  'de', 'la', 'el', 'los', 'las', 'un', 'una', 'que', 'se', 'con', 'para',
  'por', 'sin', 'del', 'al', 'es', 'son', 'tu', 'te', 'su', 'lo', 'le',
  'más', 'pero', 'como', 'si', 'ya', 'está', 'están', 'hay', 'no',
]);

const LITERAL = /'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"|`((?:[^`\\]|\\.)*)`/g;
const PALABRA = /[A-Za-zÁÉÍÓÚÜÑáéíóúüñ_][A-Za-z0-9_ÁÉÍÓÚÜÑáéíóúüñ]*/g;
const MARCADOR = '\u0000';

// Un literal es prosa si tiene al menos dos palabras castellanas separadas por
// un espacio. «pending» o «status-chip» no lo son; «sin tasa documentada» sí.
function esProsa(texto) {
  const plano = texto.replace(/\$\{[^}]*\}/g, ' ');
  const palabras = plano.toLowerCase().match(PALABRA) || [];
  if (palabras.length < 2) return false;
  if (!/\S\s+\S/.test(plano.trim())) return false;
  return palabras.some((palabra) => PROSA.has(palabra));
}

// Devuelve los motivos por los que la parte visible de un literal no vale.
function problemas(texto) {
  // Las interpolaciones y los literales anidados son código, no texto.
  const plano = texto
    .replace(/\$\{[^}]*\}/g, ` ${MARCADOR} `)
    .replace(/"[^"]*"/g, ` ${MARCADOR} `)
    .replace(/'[^']*'/g, ` ${MARCADOR} `)
    // En un documento HTML generado, el CSS y las etiquetas son andamiaje: solo
    // se juzga el texto que queda entre ellas.
    .replace(/<style[\s\S]*?<\/style>/g, ' ')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\{[^{}]*\}/g, ' ');
  const motivos = [];
  const palabras = new Set((plano.match(PALABRA) || []).map((palabra) => palabra.toLowerCase()));
  const ingles = [...palabras].filter((palabra) => INGLES.has(palabra));
  if (ingles.length) motivos.push(`inglés: ${ingles.join(', ')}`);
  const jerga = [...palabras].filter((palabra) => JERGA.has(palabra));
  if (jerga.length) motivos.push(`jerga: ${jerga.join(', ')}`);
  const codigos = plano.match(/\b[A-Z][A-Z0-9]{2,}_[A-Z0-9_]+\b/g);
  if (codigos) motivos.push(`código interno: ${codigos.join(', ')}`);
  const rutas = plano.match(/\/api\/[a-z-]+/g);
  if (rutas) motivos.push(`ruta interna: ${rutas.join(', ')}`);
  return motivos;
}

// Recorre un fuente y devuelve las cadenas visibles que fallan.
function fugas(fuente) {
  const hallazgos = [];
  fuente.split('\n').forEach((linea, indice) => {
    const limpia = linea.trim();
    if (limpia.startsWith('//') || limpia.startsWith('*') || limpia.startsWith('/*')) return;
    LITERAL.lastIndex = 0;
    let coincidencia;
    while ((coincidencia = LITERAL.exec(linea)) !== null) {
      const texto = coincidencia[1] ?? coincidencia[2] ?? coincidencia[3] ?? '';
      if (!esProsa(texto)) continue;
      const motivos = problemas(texto);
      if (motivos.length) hallazgos.push(`${indice + 1}: ${motivos.join(' · ')} → ${texto.slice(0, 90)}`);
    }
  });
  return hallazgos;
}

test('ningún módulo de app/static publica inglés, jerga ni códigos internos', () => {
  const todas = [];
  for (const modulo of MODULOS) {
    const ruta = path.join(STATIC, modulo);
    if (!fs.existsSync(ruta)) continue;
    for (const hallazgo of fugas(fs.readFileSync(ruta, 'utf8'))) {
      todas.push(`${modulo}:${hallazgo}`);
    }
  }
  assert.deepStrictEqual(todas, [], `cadenas visibles que hay que reescribir:\n${todas.join('\n')}`);
});

test('el detector distingue un valor interno de un texto de pantalla', () => {
  // Un atributo, un enum o una clase CSS pueden estar en inglés: no se ven.
  assert.deepStrictEqual(fugas('const box = el("input", {type: "checkbox", id: `field-${n}`});'), []);
  assert.deepStrictEqual(fugas('if (product.conditions_state === "pending") return null;'), []);
  assert.deepStrictEqual(fugas('chip.className = "status-chip is-ready";'), []);
  // Una frase castellana con un enumerado dentro, no.
  const visibles = fugas('feedback.textContent = "Clase de la fuente: Oficial, unknown.";');
  assert.strictEqual(visibles.length, 1, 'la frase debería marcarse');
  assert.match(visibles[0], /unknown/);
});

test('una plantilla con código no se juzga por el código de dentro', () => {
  // `source.url` o `true` viven en la interpolación: son código, no pantalla.
  assert.deepStrictEqual(
    fugas('line.appendChild(document.createTextNode(` · consultada el ${conditionEntry.source.retrieved_at}`));'),
    []);
  assert.deepStrictEqual(
    fugas('const t = `Mapa: ${caps?.context === true ? "puedes adjuntar" : "no disponible"}.`;'),
    []);
  // Pero el texto de fuera sí se juzga.
  const fuera = fugas('const t = `Estado del backend: ${estado}.`;');
  assert.strictEqual(fuera.length, 1, fuera.join('\n'));
});

test('el detector reconoce los casos ya arreglados en este proyecto', () => {
  const casos = [
    'feedback.textContent = "Intentando contactar el endpoint local /api/chat por ahora.";',
    'const nota = "El backend la coloca al final de cada mes.";',
    'const eje = "TAE 2,61 % · vencida · motivo PROMOTION_EXPIRED del catálogo.";',
  ];
  for (const caso of casos) {
    assert.ok(fugas(caso).length >= 1, `no se detectó: ${caso}`);
  }
});

test('la regresión concreta: reintroducir «unknown» en un mensaje visible pone el test rojo', () => {
  // Se simula el diff que causó el bug original: un fallback que devuelve el
  // valor crudo dentro de una frase que el usuario lee.
  const conRegresion = 'review.appendChild(textElement("p", `Clase de la fuente: ${tabla[valor] || valor}, unknown.`));';
  const detectadas = fugas(conRegresion);
  assert.ok(detectadas.length >= 1,
    'si «unknown» vuelve a un mensaje visible, este test tiene que fallar');
  assert.match(detectadas[0], /unknown/);
  // Y el mismo código sin la palabra inglesa pasa.
  assert.deepStrictEqual(
    fugas('review.appendChild(textElement("p", `Clase de la fuente: ${tabla[valor] || valor}, sin identificar.`));'),
    []);
});

test('las etiquetas de estado del informe traducen todos los valores del catálogo', () => {
  // Un enumerado del backend en crudo es el patrón del bug, así que se ejecutan
  // las funciones reales con los valores que emite el catálogo.
  const ESTADOS = ['known', 'stale', 'conflict', 'unknown', 'not_applicable'];
  const comparador = fs.readFileSync(path.join(STATIC, 'comparison_report.js'), 'utf8');
  const contexto = { console, Number, Math, Date, Intl };
  vm.createContext(contexto);
  // El corte empieza en la tabla de estados: conditionStateLabel la consulta.
  const inicio = comparador.indexOf('  var ESTADOS_CONDICION');
  const fin = comparador.indexOf('  function conditionLabel');
  assert.ok(inicio > 0 && fin > inicio, 'no se encontraron las funciones de etiqueta');
  vm.runInContext(comparador.slice(inicio, fin), contexto);
  for (const estado of ESTADOS) {
    const etiqueta = contexto.conditionStateLabel({ state: estado }, '2026-11-24');
    assert.notStrictEqual(etiqueta, estado, `«${estado}» se devuelve en crudo`);
    assert.ok(!/_/.test(etiqueta), `quedan guiones bajos: ${etiqueta}`);
    assert.deepStrictEqual(problemas(etiqueta), [], `«${etiqueta}» no es castellano limpio`);
  }
});
