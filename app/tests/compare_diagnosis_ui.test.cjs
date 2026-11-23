"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// El diagnóstico TAE es lo que el usuario lee tras pulsar el botón. Esta prueba
// ejecuta la función real con un DOM mínimo y comprueba que la cifra se ve, que
// no se vuelca JSON crudo y que un motivo desconocido no rompe la vista.
const CODE = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');

function grab(name) {
  const signature = `function ${name}(`;
  const start = CODE.indexOf(signature);
  if (start < 0) throw new Error(`missing function ${name}`);
  const end = CODE.indexOf('\n}\n', start);
  if (end < 0) throw new Error(`unterminated function ${name}`);
  return CODE.slice(start, end + 3);
}

function grabConsts(names) {
  // Las tres constantes viven juntas: se corta desde la primera hasta el cierre
  // del Object.freeze de DIAGNOSIS_REASONS, que es "\n});".
  const start = CODE.indexOf(`const ${names[0]}`);
  if (start < 0) throw new Error(`missing const ${names[0]}`);
  const close = CODE.indexOf('\n});', CODE.indexOf('const DIAGNOSIS_REASONS'));
  if (close < 0) throw new Error('missing end of DIAGNOSIS_REASONS');
  const block = CODE.slice(start, close + 4);
  for (const name of names) {
    if (!block.includes(`const ${name}`)) throw new Error(`missing const ${name} in block`);
  }
  return block;
}

function setup(result, ids) {
  const byId = {};
  class Node {
    constructor(tag) { this.tag = tag; this.children = []; this.text = ''; this.attrs = {}; this.className = ''; this.listeners = {}; }
    setAttribute(key, value) { this.attrs[key] = value; this[key] = value; if (key === 'id') byId[value] = this; }
    appendChild(node) { this.children.push(node); return node; }
    replaceChildren(...nodes) { this.children = nodes; this.text = ''; }
    addEventListener(event, fn) { this.listeners[event] = fn; }
    focus() {}
    set textContent(value) { this.text = String(value); this.children = []; }
    get textContent() { return this.text + this.children.map((node) => node.textContent || '').join(''); }
  }
  const document = {
    createElement: (tag) => new Node(tag),
    createTextNode: (text) => { const node = new Node('#text'); node.textContent = text; return node; },
    getElementById: (id) => byId[id] || null,
  };
  const ctx = {
    document, console, Map, JSON, Number, String, Array, Object,
    state: {
      selectedIds: ids,
      catalogueCache: new Map([
        ['DEP-EBN-12', { id: 'DEP-EBN-12', name: 'Depósito Nuevo Ahorro 12 meses', family: 'deposito' }],
        ['DEP-SELF-12', { id: 'DEP-SELF-12', name: 'Depósito a 12 meses Self Bank', family: 'deposito' }],
      ]),
      diagnosis: { requestId: 1, ids, busy: false, error: false, result },
    },
  };
  vm.createContext(ctx);
  vm.runInContext([grabConsts(['RATE_VALUE', 'ratePercent', 'DIAGNOSIS_REASONS']),
    grab('el'), grab('textElement'), grab('button'), grab('productName'), grab('callout'),
    grab('diagnosisApplicable'), grab('renderDiagnosis')].join('\n'),
    ctx);
  const holder = new Node('section');
  holder.setAttribute('id', 'compare-diagnosis');
  byId['compare-diagnosis'] = holder;
  ctx.renderDiagnosis();
  return holder.textContent;
}

const IDS = ['DEP-EBN-12', 'DEP-SELF-12'];

test('el diagnóstico muestra la TAE de cada producto elegible', () => {
  const text = setup({
    criterion: 'deposit_tae_12m_eur',
    items: [
      { product_id: 'DEP-EBN-12', eligible: true, value: '3.1', reason_codes: [], source_refs: [{ source_ids: ['https://www.ebnbanco.com/ahorro/deposito-nuevo-ahorro/'], retrieved_at: '2026-11-03' }] },
      { product_id: 'DEP-SELF-12', eligible: true, value: '2.75', reason_codes: [], source_refs: [{ source_ids: ['https://www.rankia.com/blog/x'], retrieved_at: '2026-11-03' }] },
    ],
  }, IDS);
  assert.match(text, /TAE 3,10 %/);
  assert.match(text, /TAE 2,75 %/);
  assert.match(text, /Depósito Nuevo Ahorro 12 meses/);
  // La fuente se enlaza como texto, no como JSON serializado.
  assert.doesNotMatch(text, /\[\{"source_ids"/);
  assert.match(text, /https:\/\/www\.ebnbanco\.com\/ahorro\/deposito-nuevo-ahorro\//);
});

test('un producto no elegible explica el motivo en castellano y sin código suelto', () => {
  const text = setup({
    criterion: 'deposit_tae_12m_eur',
    items: [
      { product_id: 'DEP-EBN-12', eligible: false, value: null, reason_codes: ['DATA_STALE'], source_refs: [] },
      { product_id: 'DEP-SELF-12', eligible: true, value: '2.75', reason_codes: [], source_refs: [] },
    ],
  }, IDS);
  assert.match(text, /No elegible para comparación cuantitativa/);
  assert.match(text, /La oferta documentada está vencida\./);
  assert.doesNotMatch(text, /DATA_STALE/);
  assert.match(text, /El diagnóstico no aporta referencias de fuente para este dato\./);
});

test('un motivo no reconocido no rompe la vista ni inventa su significado', () => {
  const text = setup({
    criterion: 'deposit_tae_12m_eur',
    items: [
      { product_id: 'DEP-EBN-12', eligible: false, value: null, reason_codes: ['ALGO_NUEVO'], source_refs: [] },
      { product_id: 'DEP-SELF-12', eligible: false, value: null, reason_codes: [], source_refs: [] },
    ],
  }, IDS);
  assert.match(text, /Motivo no reconocido; consulta el servicio local\./);
});

test('un valor que no es numérico no se pinta como tasa', () => {
  const text = setup({
    criterion: 'deposit_tae_12m_eur',
    items: [
      { product_id: 'DEP-EBN-12', eligible: true, value: '<b>3.1</b>', reason_codes: [], source_refs: [] },
      { product_id: 'DEP-SELF-12', eligible: true, value: '2.75', reason_codes: [], source_refs: [] },
    ],
  }, IDS);
  assert.doesNotMatch(text, /<b>/);
  assert.match(text, /TAE 2,75 %/);
});
