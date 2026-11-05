"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Ejecuta funciones reales de la biblioteca/ficha con un DOM mínimo, sin navegador ni red.
function grab(code, name) {
  const signature = `function ${name}(`;
  const start = code.indexOf(signature);
  if (start < 0) throw new Error(`missing function ${name}`);
  const end = code.indexOf('\n}\n', start);
  if (end < 0) throw new Error(`unterminated function ${name}`);
  return code.slice(start, end + 3);
}

function setup() {
  const code = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
  const byId = {};
  class Node {
    constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this.text = ''; this.attrs = {}; }
    setAttribute(key, value) { this.attrs[key] = value; this[key] = value; if (key === 'id') byId[value] = this; }
    appendChild(node) { this.children.push(node); return node; }
    append(...nodes) { nodes.forEach((node) => this.appendChild(node)); }
    replaceChildren(...nodes) { this.children = nodes; this.text = ''; }
    addEventListener(event, fn) { this.listeners[event] = fn; }
    querySelector() { return null; }
    focus() {}
    set textContent(value) { this.text = String(value); this.children = []; }
    get textContent() { return this.text + this.children.map((node) => node.textContent).join(''); }
  }
  const document = {
    createElement: (tag) => new Node(tag),
    createTextNode: (text) => { const node = new Node('#text'); node.textContent = text; return node; },
    getElementById: (id) => byId[id],
  };
  const conditionsLoad = require('../static/conditions_load.js');
  const ctx = {
    document, URL, console,
    window: { PaideiaConditionsLoad: conditionsLoad, ContextHelp: { createHelp: () => new Node('span') } },
    FAMILIES: Object.freeze({
      cuenta_remunerada: 'Cuenta remunerada', deposito: 'Depósito',
      letra_deuda_publica: 'Letra de deuda pública', fondo_tradicional: 'Fondo tradicional',
      etf_ucits: 'ETF UCITS',
    }),
    state: {
      detail: { id: null, product: null, loading: false, error: null },
      conditions: { loaded: true, loading: false, error: null, byId: new Map(), referenceDate: '2026-11-04' },
      selectedIds: [], catalogueCache: new Map(),
    },
  };
  vm.createContext(ctx);
  // La tabla de filas de la ficha es una constante de módulo, no una función.
  const tablaInicio = code.indexOf('const CONDITION_ROWS');
  const tablaFin = code.indexOf('\n});', tablaInicio);
  if (tablaInicio < 0 || tablaFin < 0) throw new Error('missing CONDITION_ROWS');
  vm.runInContext(code.slice(tablaInicio, tablaFin + 4), ctx);
  const names = [
    'isSafePrimaryUrl', 'el', 'button', 'textElement', 'badge', 'familyLabel',
    'identityLabel', 'identityKind', 'conditionsLabel', 'issuerLabel', 'productName',
    'section', 'appendPrimarySource', 'appendList', 'conditionOf', 'conditionConsultedAt',
    'conditionValidityText', 'productEffectiveDate', 'formatRate', 'conditionStateText',
    'rateSummary', 'productCard', 'renderProductDetail', 'callout', 'errorBox', 'routeLink',
    'formatEuros', 'conditionRowText',
  ];
  vm.runInContext(names.map((name) => grab(code, name)).join('\n\n'), ctx);
  return {
    ...ctx, byId,
    card(product) { return ctx.productCard(product); },
    detail(product) {
      const holder = new Node('section');
      holder.setAttribute('id', 'product-detail');
      byId['product-detail'] = holder;
      ctx.state.route = 'biblioteca';
      ctx.state.detail = { id: product.id, product, loading: false, error: null };
      ctx.renderProductDetail();
      return holder;
    },
  };
}

const CONDITION_URL = 'https://example.invalid/synthetic/cond';
const PRIMARY_URL = 'https://example.invalid/synthetic/DEP-REVIEW';

function product(overrides = {}) {
  return {
    id: 'DEP-REVIEW', name: 'Depósito con conflicto', family: 'deposito',
    issuer: 'Banco Sintético', isin: null, identity_state: 'proposed',
    primary_url: PRIMARY_URL, as_of: '2026-11-03', publication_ready: false,
    conditions_state: 'pending',
    conflicts: ['Conflicto real: dos plazos distintos para la misma entidad.'],
    unknown_fields: ['plazos disponibles', 'fecha efectiva de cada oferta'],
    review_state: 'conflicts_and_unknown_fields',
    ...overrides,
  };
}

function conditionsEntry(overrides = {}) {
  return {
    product_id: 'DEP-REVIEW', family: 'deposito', display_name: 'Depósito con conflicto',
    provider: 'Banco Sintético', identity_state: 'verified', origin: 'curated_conditions',
    source: { url: CONDITION_URL, kind: 'official', retrieved_at: '2026-11-03' },
    conditions: [{
      metric: 'annual_rate_percent', state: 'known', value: '3.10', unit: 'PERCENT',
      reason: 'CURATED_OFFICIAL', source_ids: [CONDITION_URL],
      effective_from: '2026-11-01', effective_to: '2026-12-01', retrieved_at: '2026-11-03',
      notes: [],
    }],
    rate_tiers: [],
    ...overrides,
  };
}

function anchors(node) {
  const found = [];
  (function walk(current) {
    if (!current) return;
    if (current.tag === 'a') found.push(current);
    for (const child of current.children || []) walk(child);
  })(node);
  return found;
}

test('search result card shows real conflicts, unknown fields and the condition source link', () => {
  const ui = setup();
  ui.state.conditions.byId.set('DEP-REVIEW', conditionsEntry());

  const card = ui.card(product());

  const text = card.textContent;
  assert.ok(text.includes('Conflicto real: dos plazos distintos para la misma entidad.'), text);
  assert.ok(text.includes('plazos disponibles'), text);
  assert.ok(text.includes('fecha efectiva de cada oferta'), text);
  assert.match(text, /Conflictos/);
  assert.match(text, /Campos desconocidos/);
  assert.match(text, /Fuente de las condiciones/);
  assert.ok(anchors(card).some((link) => link.href === CONDITION_URL),
    JSON.stringify(anchors(card).map((link) => link.href)));
});

test('search result card does not invent absence when the API lists no review items', () => {
  const ui = setup();
  const card = ui.card(product({ conflicts: [], unknown_fields: [], review_state: 'no_pending_review_items' }));
  const text = card.textContent;
  assert.match(text, /no enumera|no consta|sin enumerar/i);
  assert.doesNotMatch(text, /sin conflictos|no hay conflictos|ningún campo desconocido/i);
});

test('product detail shows real conflicts, unknown fields and the condition source link', () => {
  const ui = setup();
  ui.state.conditions.byId.set('DEP-REVIEW', conditionsEntry());

  const holder = ui.detail(product());

  const text = holder.textContent;
  assert.ok(text.includes('Conflicto real: dos plazos distintos para la misma entidad.'), text);
  assert.ok(text.includes('plazos disponibles'), text);
  assert.ok(text.includes('fecha efectiva de cada oferta'), text);
  assert.ok(anchors(holder).some((link) => link.href === CONDITION_URL),
    JSON.stringify(anchors(holder).map((link) => link.href)));
});

test('product detail links the condition source even when no condition rows are listed', () => {
  const ui = setup();
  ui.state.conditions.byId.set('DEP-REVIEW', conditionsEntry({ conditions: [] }));

  const holder = ui.detail(product());

  assert.ok(anchors(holder).some((link) => link.href === CONDITION_URL),
    JSON.stringify(anchors(holder).map((link) => link.href)));
  assert.match(holder.textContent, /Fuente de las condiciones/);
});

test('an unknown condition with a stray value is never rendered as a documented rate', () => {
  const ui = setup();
  ui.state.conditions.byId.set('DEP-REVIEW', conditionsEntry({
    conditions: [{
      metric: 'annual_rate_percent', state: 'unknown', value: '3.10', unit: 'PERCENT',
      reason: 'RATE_NOT_DOCUMENTED', source_ids: [], retrieved_at: '2026-11-03', notes: [],
    }],
  }));

  const holder = ui.detail(product());
  const card = ui.card(product());

  assert.doesNotMatch(holder.textContent, /3\.10 TAE/);
  assert.doesNotMatch(holder.textContent, /documentada por la fuente/);
  assert.doesNotMatch(card.textContent, /3\.10/);
  assert.match(holder.textContent, /sin cifra utilizable|sin dato/);
});

test('conflict and unknown-field text is rendered as inert text, not markup', () => {
  const ui = setup();
  const payload = '<img src=x onerror="alert(1)"> conflicto';
  const field = '<script>alert(2)</script> campo';
  const card = ui.card(product({ conflicts: [payload], unknown_fields: [field] }));
  const holder = ui.detail(product({ conflicts: [payload], unknown_fields: [field] }));

  for (const node of [card, holder]) {
    assert.ok(node.textContent.includes(payload), node.textContent);
    assert.ok(node.textContent.includes(field), node.textContent);
    const tags = [];
    (function walk(current) {
      if (!current) return;
      if (current.tag) tags.push(current.tag);
      for (const child of current.children || []) walk(child);
    })(node);
    assert.ok(!tags.includes('img') && !tags.includes('script'), JSON.stringify(tags));
  }
});

test('product detail never labels unknown conditions as documented', () => {
  const ui = setup();
  ui.state.conditions.byId.set('DEP-REVIEW', conditionsEntry({
    conditions: [{
      metric: 'annual_rate_percent', state: 'unknown', value: null, unit: 'PERCENT',
      reason: 'RATE_NOT_DOCUMENTED', source_ids: [], retrieved_at: '2026-11-03', notes: [],
    }],
  }));

  const holder = ui.detail(product());

  assert.doesNotMatch(holder.textContent, /Condiciones documentadas/);
  assert.doesNotMatch(holder.textContent, /constan en la fuente citada/);
  assert.match(holder.textContent, /no todas documentadas|sin dato/);
});

test('the real conflict note from the conditions record is visible in card and detail', () => {
  const ui = setup();
  const note = 'La misma página mezcla 2,50 % TAE/6 meses y 1,25 % TAE/12 meses.';
  ui.state.conditions.byId.set('DEP-REVIEW', conditionsEntry({
    conditions: [{
      metric: 'annual_rate_percent', state: 'conflict', value: null, unit: 'PERCENT',
      reason: 'SOURCE_CONFLICT', source_ids: [CONDITION_URL], retrieved_at: '2026-11-03',
      notes: [note],
    }],
  }));

  const card = ui.card(product());
  const holder = ui.detail(product());

  assert.ok(card.textContent.includes(note), card.textContent);
  assert.ok(holder.textContent.includes(note), holder.textContent);
  assert.doesNotMatch(card.textContent, /TAE documentada/);
  assert.doesNotMatch(holder.textContent, /Condiciones documentadas/);
});
