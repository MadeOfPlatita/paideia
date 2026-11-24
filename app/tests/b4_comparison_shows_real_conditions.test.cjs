// Comparador: las dos tarjetas NO pueden salir idénticas y vacías.
//
// Bug real reportado con una captura: al comparar dos letras del Tesoro
// (vencimiento 15-01-2027 y 05-02-2027), las dos tarjetas decían exactamente lo
// mismo: «Desconocida en los metadatos», «No disponibles; no se infieren»,
// «Pendientes de validación». Cero información y dos productos distintos.
//
// La causa: `comparisonCard` tenía seis valores escritos a mano y solo leía
// `annual_rate_percent` y `term_months`; las letras no tienen ninguna de las dos
// (su tasa es `marginal_rate_percent` y su plazo, `maturity_date`), así que todo
// caía en el texto fijo. Cada letra tiene 10 condiciones reales en el catálogo.
//
// Este test monta la tarjeta real del comparador con las condiciones reales de
// dos letras y exige que se distingan.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

// Extrae una función completa por su firma, como hacen los demás tests de UI.
// Las del bloque de chat van indentadas dos espacios, así que el cierre es
// `\n  }\n` y no `\n}\n`: se busca el primer cierre cuya llave devuelva el
// balance a cero, sin depender de la indentación.
function grab(code, name) {
  const signature = `function ${name}(`;
  const start = code.indexOf(signature);
  if (start < 0) throw new Error(`missing function ${name}`);
  // Desde la llave de apertura de la función, contar hasta que el balance cierre.
  const apertura = code.indexOf('{', start);
  if (apertura < 0) throw new Error(`missing body of ${name}`);
  let balance = 0;
  for (let i = apertura; i < code.length; i += 1) {
    const ch = code[i];
    if (ch === '{') balance += 1;
    else if (ch === '}') {
      balance -= 1;
      if (balance === 0) return code.slice(start, i + 1);
    }
  }
  throw new Error(`unterminated function ${name}`);
}

// Extrae un `const NOMBRE = ...;` de módulo (la tabla de etiquetas). Se corta por
// el primer cierre de línea que termina la declaración, no por un offset fijo.
function grabConst(code, name) {
  const start = code.indexOf(`const ${name} =`);
  if (start < 0) throw new Error(`missing const ${name}`);
  const finObjeto = code.indexOf('\n};', start);
  const finSimple = code.indexOf('\n', code.indexOf('=', start));
  const end = finObjeto >= 0 && finObjeto < (finSimple + 400) ? finObjeto + 3 : finSimple + 1;
  return code.slice(start, end);
}

function setup() {
  const code = fs.readFileSync(APP, 'utf8');
  const byId = {};
  class Node {
    constructor(tag) {
      this.tag = tag; this.children = []; this.listeners = {}; this.text = '';
      this.attrs = {}; this.className = ''; this.id = ''; this.style = {};
    }
    setAttribute(key, value) {
      this.attrs[key] = value; this[key] = value;
      if (key === 'id') byId[value] = this;
    }
    appendChild(node) { this.children.push(node); return node; }
    append(...nodes) { nodes.forEach((node) => this.appendChild(node)); }
    replaceChildren(...nodes) { this.children = nodes; this.text = ''; }
    addEventListener(event, fn) { this.listeners[event] = fn; }
    querySelector() { return null; }
    querySelectorAll() { return []; }
    focus() {}
    set textContent(value) { this.text = String(value); this.children = []; }
    get textContent() { return this.text + this.children.map((node) => node.textContent).join(''); }
    get classList() { return { add() {}, remove() {}, toggle() {}, contains: () => false }; }
  }
  const document = {
    createElement: (tag) => new Node(tag),
    createTextNode: (text) => { const node = new Node('#text'); node.textContent = text; return node; },
    getElementById: (id) => byId[id] || null,
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener() {},
  };
  const conditionsLoad = require('../static/conditions_load.js');
  const ctx = {
    document, URL, console,
    window: {
      PaideiaConditionsLoad: conditionsLoad,
      ContextHelp: { createHelp: () => new Node('span') },
      location: { hash: '' },
    },
    FAMILIES: Object.freeze({
      cuenta_remunerada: 'Cuenta remunerada', deposito: 'Depósito',
      letra_deuda_publica: 'Letra de deuda pública', fondo_tradicional: 'Fondo tradicional',
      etf_ucits: 'ETF UCITS',
    }),
    state: {
      conditions: { loaded: true, loading: false, error: null, byId: new Map(), referenceDate: '2026-11-24' },
      selectedIds: ['DEBT-01', 'DEBT-02'], catalogueCache: new Map(), route: 'comparar',
    },
  };
  vm.createContext(ctx);
  // Se evalúan bloques completos entre marcadores reales del archivo (nunca por
  // offsets fijos ni contando llaves: hay llaves dentro de cadenas de regex).
  const bloque = (desde, hasta) => {
    const inicio = code.indexOf(desde);
    const fin = code.indexOf(hasta, inicio);
    if (inicio < 0 || fin < 0) throw new Error(`bloque no encontrado: ${desde} .. ${hasta}`);
    return code.slice(inicio, fin);
  };
  const fuente = [
    bloque('function isSafePrimaryUrl', 'class ApiFailure'),    // validación de la URL de la fuente
    bloque('function el(', 'function setStatusChip'),          // el, button, textElement, badge, labels
    bloque('function familyLabel', 'function apiErrorText'),    // familyLabel, identity*, productName, CONDITION_ROWS
    bloque('function appendPrimarySource', 'function renderContext'), // enlace a la fuente primaria
    bloque('function appendList(', 'function renderProductDetail'), // appendList
    bloque('const CHAT_ISO_DATE', 'const CHAT_MONEY'),          // regex y helpers de formato del chat
    bloque('function conditionOf', 'async function loadConditions'),
    // comparisonCard arrastra consigo METRIC_ES, humanMetricLabel y comparisonValue,
    // que están declarados justo después en el archivo.
    bloque('function comparisonCard', 'function renderComparisonResult'),
  ].join('\n\n');
  vm.runInContext(fuente, ctx);
  return { ctx, byId };
}

function textOf(node) {
  let out = node.textContent || '';
  for (const child of node.children || []) out += ' ' + textOf(child);
  return out;
}

// Dos letras del Tesoro con las condiciones REALES del catálogo (10 cada una).
function letra(productId, name, isin, maturity, price, marginalRate) {
  return {
    product_id: productId,
    display_name: name,
    family: 'letra_deuda_publica',
    identity_state: 'verified',
    conditions: [
      { metric: 'isin', state: 'known', value: isin, unit: 'TEXT' },
      { metric: 'maturity_date', state: 'known', value: maturity, unit: 'DATE' },
      { metric: 'minimum_price_percent', state: 'known', value: price, unit: 'PERCENT' },
      { metric: 'average_price_percent', state: 'known', value: price, unit: 'PERCENT' },
      { metric: 'marginal_rate_percent', state: 'known', value: marginalRate, unit: 'PERCENT' },
      { metric: 'average_rate_percent', state: 'known', value: marginalRate, unit: 'PERCENT' },
      { metric: 'auction_date', state: 'known', value: '2026-10-13', unit: 'DATE' },
      { metric: 'settlement_date', state: 'known', value: '2026-10-16', unit: 'DATE' },
      { metric: 'outstanding_balance', state: 'known', value: '8780.5', unit: 'TEXT' },
      { metric: 'awarded_nominal_eur', state: 'known', value: '75169000000', unit: 'EUR' },
    ],
  };
}

test('dos letras del Tesoro se comparan con datos distintos, no con texto fijo', () => {
  const { ctx } = setup();
  const a = letra('DEBT-01', 'Letra del Tesoro — vencimiento 15-01-2027',
    'ES0L02701156', '2027-01-15', '99.336', '2.645');
  const b = letra('DEBT-02', 'Letra del Tesoro — vencimiento 05-02-2027',
    'ES0L02702055', '2027-02-05', '99.120', '2.710');
  ctx.state.conditions.byId.set('DEBT-01', a);
  ctx.state.conditions.byId.set('DEBT-02', b);

  const cardA = ctx.comparisonCard({
    id: 'DEBT-01', name: a.display_name, family: 'letra_deuda_publica',
    issuer: 'Tesoro Público', identity_state: 'verified',
  });
  const cardB = ctx.comparisonCard({
    id: 'DEBT-02', name: b.display_name, family: 'letra_deuda_publica',
    issuer: 'Tesoro Público', identity_state: 'verified',
  });

  const textoA = textOf(cardA);
  const textoB = textOf(cardB);

  // 1. Cada tarjeta trae sus datos reales.
  assert.ok(textoA.includes('ES0L02701156'), `falta el ISIN de la primera: ${textoA}`);
  assert.ok(textoB.includes('ES0L02702055'), `falta el ISIN de la segunda: ${textoB}`);
  assert.ok(textoA.includes('2027-01-15'), `falta el vencimiento de la primera: ${textoA}`);
  assert.ok(textoB.includes('2027-02-05'), `falta el vencimiento de la segunda: ${textoB}`);

  // 2. La tasa marginal, que es la que estas fichas sí tienen, aparece.
  assert.ok(/2,64|2,6|2\.645/.test(textoA), `falta la tasa de la primera: ${textoA}`);
  assert.ok(/2,71|2,7|2\.710/.test(textoB), `falta la tasa de la segunda: ${textoB}`);

  // 3. Lo esencial: las dos tarjetas NO son iguales.
  assert.notStrictEqual(textoA, textoB,
    'las dos tarjetas de letras distintas salen idénticas: el comparador no compara nada');

  // 4. No se cuela el texto fijo que hacía parecer que no había datos.
  assert.ok(!textoA.includes('Desconocida en los metadatos'),
    `sigue el texto fijo de «desconocida»: ${textoA}`);
  assert.ok(!textoA.includes('Pendientes de validación; no se infieren'),
    `sigue el texto fijo de «pendientes»: ${textoA}`);

  // 5. Los datos comparables están etiquetados en castellano.
  for (const etiqueta of ['Rentabilidad', 'Plazo / vencimiento', 'Precio', 'ISIN']) {
    assert.ok(textoA.includes(etiqueta), `falta la etiqueta ${etiqueta}: ${textoA}`);
  }
});

test('un producto sin condiciones lo dice una vez, no seis veces', () => {
  const { ctx } = setup();
  const card = ctx.comparisonCard({
    id: 'DEP-VACIO', name: 'Depósito sin transcribir', family: 'deposito',
    issuer: 'Banco Sintético', identity_state: 'proposed',
  });
  const texto = textOf(card);
  assert.ok(texto.includes('no tiene condiciones transcritas'), texto);
  assert.ok(!texto.includes('Desconocida en los metadatos'), texto);
  const huecos = (texto.match(/No disponible|No evaluada|Desconocida|Pendientes/g) || []).length;
  assert.strictEqual(huecos, 0, `quedan ${huecos} huecos con texto fijo: ${texto}`);
});

test('una tasa vencida se declara vencida y no se lee como vigente', () => {
  const { ctx } = setup();
  ctx.state.conditions.byId.set('DEP-X', {
    product_id: 'DEP-X', family: 'deposito',
    conditions: [{ metric: 'annual_rate_percent', state: 'stale', value: '3.10', unit: 'PERCENT' }],
  });
  const texto = textOf(ctx.comparisonCard({
    id: 'DEP-X', name: 'Depósito vencido', family: 'deposito', issuer: 'Banco X',
  }));
  assert.ok(texto.includes('vencida'), `no se declara vencida: ${texto}`);
});

test('una métrica sin traducir no se publica como identificador', () => {
  const { ctx } = setup();
  ctx.state.conditions.byId.set('FND-X', {
    product_id: 'FND-X', family: 'fondo_tradicional',
    conditions: [{ metric: 'metrica_nueva_sin_traducir', state: 'known', value: 'dato real', unit: 'TEXT' }],
  });
  const texto = textOf(ctx.comparisonCard({
    id: 'FND-X', name: 'Fondo X', family: 'fondo_tradicional', issuer: 'Gestora X',
  }));
  // El DATO sí se muestra: no se esconde información documentada.
  assert.ok(texto.includes('dato real'), `se escondió un dato documentado: ${texto}`);
  // Pero la etiqueta no publica el identificador interno en inglés.
  assert.ok(!texto.includes('metrica_nueva_sin_traducir'),
    `se publicó el identificador crudo: ${texto}`);
  assert.ok(!texto.includes('metrica nueva sin traducir'),
    `se publicó el identificador con guiones vueltos espacios: ${texto}`);
  assert.ok(/no catalogada/i.test(texto), `no se declara que la métrica no está catalogada: ${texto}`);
});

test('la tarjeta no depende de funciones internas de la sección de chat', () => {
  // BUG REAL: `comparisonValue` llamaba a `chatConditionValue`, que vive dentro de
  // `renderHome`. En el navegador eso lanzaba «chatConditionValue is not defined»
  // dentro de `comparisonCard`, la excepción se propagaba y el comparador quedaba
  // en blanco: ni tarjetas ni mensaje de error. En los tests no se veía porque el
  // trozo evaluado incluía esa función.
  //
  // Aquí se evalúa SOLO el bloque del comparador, sin el del chat, y se exige que
  // formatee por sí mismo.
  const code = fs.readFileSync(APP, 'utf8');
  const fuente = [
    'function isSafePrimaryUrl', 'function el(', 'function familyLabel',
    'function appendPrimarySource', 'function appendList(', 'function conditionOf',
    'function comparisonCard',
  ].map((desde, i) => {
    const cortes = ['class ApiFailure', 'function setStatusChip', 'function apiErrorText',
      'function renderContext', 'function renderProductDetail', 'async function loadConditions',
      'function renderComparisonResult'];
    const inicio = code.indexOf(desde);
    const fin = code.indexOf(cortes[i], inicio);
    assert.ok(inicio > 0 && fin > inicio, `bloque no encontrado: ${desde}`);
    return code.slice(inicio, fin);
  }).join('\n\n');

  // El bloque no debe LLAMAR a nada del chat (los comentarios que explican el
  // fallo sí pueden nombrarlo). Se busca una llamada real: identificador seguido
  // de paréntesis.
  const sinComentarios = fuente
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");
  assert.ok(!/\bchatConditionValue\s*\(|\bchatConditionName\s*\(|\bchatText\s*\(/.test(sinComentarios),
    'el comparador sigue llamando a funciones de la sección de chat');

  const byId = {};
  const ctx = {
    document: {
      createElement: (tag) => {
        const node = { tag, children: [], text: '', className: '', attrs: {}, style: {},
          setAttribute(k, v) { node.attrs[k] = v; }, appendChild(c) { node.children.push(c); return c; },
          append(...cs) { cs.forEach((c) => node.children.push(c)); },
          replaceChildren() { node.children = []; }, addEventListener() {}, querySelector: () => null,
          querySelectorAll: () => [], focus() {},
          set textContent(v) { node.text = String(v); node.children = []; },
          get textContent() { return node.text + node.children.map((c) => c.textContent).join(''); },
          get classList() { return { add() {}, remove() {}, toggle() {}, contains: () => false }; } };
        return node;
      },
      createTextNode: (t) => ({ textContent: t, children: [] }),
      getElementById: (id) => byId[id] || null,
    },
    URL, console,
    window: { PaideiaConditionsLoad: require('../static/conditions_load.js'),
      ContextHelp: { createHelp: () => ({ children: [] }) }, location: { hash: '' } },
    FAMILIES: Object.freeze({ deposito: 'Depósito', letra_deuda_publica: 'Letra de deuda pública' }),
    state: { conditions: { loaded: true, error: null, byId: new Map() } },
  };
  vm.createContext(ctx);
  vm.runInContext(fuente, ctx);

  ctx.state.conditions.byId.set('DEBT-X', {
    product_id: 'DEBT-X', family: 'letra_deuda_publica',
    conditions: [{ metric: 'marginal_rate_percent', state: 'known', value: '2.645', unit: 'PERCENT' }],
  });
  // No debe lanzar: si lanza, el comparador se queda en blanco en producción.
  const card = ctx.comparisonCard({ id: 'DEBT-X', name: 'Letra X', family: 'letra_deuda_publica' });
  assert.ok(textOf(card).includes('2,645'), textOf(card));
});
