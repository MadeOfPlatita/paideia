"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Defectos de la misma familia que la sección transcrita vacía: estado que se
// pinta una sola vez, secciones que solo se repintan desde una carga asíncrona
// y campos del API que se leen sin validar. Cada prueba ejecuta la función real
// con un DOM mínimo; no se comprueba el código fuente por expresiones regulares.
const CODE = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');

function grab(name) {
  const signature = `function ${name}(`;
  const start = CODE.indexOf(signature);
  if (start < 0) throw new Error(`missing function ${name}`);
  const end = CODE.indexOf('\n}\n', start);
  if (end < 0) throw new Error(`unterminated function ${name}`);
  return CODE.slice(start, end + 3);
}

function grabConst(name) {
  const start = CODE.indexOf(`const ${name}`);
  if (start < 0) throw new Error(`missing const ${name}`);
  const lineEnd = CODE.indexOf('\n', start);
  const brace = CODE.indexOf('{', start);
  // Sin llaves antes del fin de línea (`const RATE_VALUE = /…/;`) se corta por
  // la línea: buscar el `{` siguiente engancharía la constante de después.
  if (brace < 0 || brace > lineEnd) return CODE.slice(start, lineEnd);
  let depth = 0;
  for (let index = brace; index < CODE.length; index += 1) {
    if (CODE[index] === '{') depth += 1;
    else if (CODE[index] === '}') {
      depth -= 1;
      if (depth === 0) {
        const close = CODE[index + 1] === ')' ? index + 2 : index + 1;
        return CODE.slice(start, close);
      }
    }
  }
  throw new Error(`unterminated const ${name}`);
}

// `const ratePercent = (value) => ...` no lleva llaves: se corta por la línea.
function grabLine(name) {
  const start = CODE.indexOf(`const ${name}`);
  if (start < 0) throw new Error(`missing const ${name}`);
  const end = CODE.indexOf('\n', start);
  if (end < 0) throw new Error(`unterminated const ${name}`);
  return CODE.slice(start, end);
}

class Node {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.listeners = {};
    this.text = '';
    this.attrs = {};
    this.className = '';
    this.dataset = {};
    this.hidden = false;
    this.disabled = false;
  }
  // app.js asigna ids de dos formas: setAttribute('id', …) en los contenedores
  // y `nodo.id = …` en los botones generados. El setter cubre las dos para que
  // getElementById() encuentre también los botones repintados.
  get id() { return this.attrs.id || null; }
  set id(value) { this.attrs.id = value; this._setById(value); }
  _setById(value) { byId[value] = this; }
  setAttribute(key, value) { this.attrs[key] = value; this[key] = value; if (key === 'id') byId[value] = this; }
  getAttribute(key) { return Object.prototype.hasOwnProperty.call(this.attrs, key) ? this.attrs[key] : null; }
  removeAttribute(key) { delete this.attrs[key]; }
  appendChild(node) { this.children.push(node); return node; }
  append(...nodes) { nodes.forEach((node) => this.appendChild(node)); }
  replaceChildren(...nodes) { this.children = nodes; this.text = ''; }
  addEventListener(event, handler) { (this.listeners[event] = this.listeners[event] || []).push(handler); }
  querySelector() { return null; }
  querySelectorAll() { return []; }
  focus() {}
  scrollIntoView() {}
  set textContent(value) { this.text = String(value); this.children = []; if (value === '') this.text = ''; }
  get textContent() { return this.text + this.children.map((node) => node.textContent).join(''); }
  set innerText(value) { this.textContent = value; }
  get innerText() { return this.textContent; }
}

let byId = {};

function makeContext(overrides = {}) {
  byId = {};
  const document = {
    createElement: (tag) => new Node(tag),
    createElementNS: (ns, tag) => new Node(tag),
    createTextNode: (text) => { const node = new Node('#text'); node.text = String(text); return node; },
    getElementById: (id) => byId[id] || null,
    querySelectorAll: () => [],
    querySelector: () => null,
    body: new Node('body'),
    activeElement: null,
  };
  const conditionsLoad = require('../static/conditions_load.js');
  const ctx = {
    document,
    console,
    URL,
    Map, Set, JSON, Number, String, Array, Object, Math, Date, Intl, BigInt, Error, TypeError,
    window: {
      PaideiaConditionsLoad: conditionsLoad,
      ContextHelp: { createHelp: () => new Node('span') },
      requestAnimationFrame: (fn) => fn(),
      location: { hash: '#biblioteca' },
    },
    state: {
      route: 'biblioteca',
      conditions: { loaded: true, loading: false, error: null, byId: new Map(), referenceDate: '2026-11-23' },
      library: { query: '', family: '', items: [], count: 0, loading: false, error: null, requestId: 0, loaded: true, onlyDocumented: false },
      catalogueCache: new Map(),
      selectedIds: [],
      compareResult: null, compareIds: [], compareError: null, compareBusy: false, compareRequestId: 0,
      diagnosis: { requestId: 0, ids: [], busy: false, error: false, result: null },
      detail: { id: null, product: null, loading: false, error: null, requestId: 0 },
    },
    ...overrides,
  };
  vm.createContext(ctx);
  return { ctx, byId: () => byId, document };
}

// Carga un conjunto de funciones y constantes reales en el contexto.
function load(ctx, names, consts = []) {
  const source = [...consts.map(grabConst), ...names.map(grab)].join('\n\n');
  vm.runInContext(source, ctx);
}

function loadLines(ctx, names, lineConsts = []) {
  const source = [...lineConsts.map(grabLine), ...names.map(grab)].join('\n\n');
  vm.runInContext(source, ctx);
}

function product(overrides = {}) {
  return {
    id: 'DEP-1', name: 'Depósito uno', family: 'deposito', issuer: 'Banco',
    identity_state: 'verified', primary_url: null, as_of: '2026-11-01',
    conditions_state: 'documented', conflicts: [], unknown_fields: [],
    ...overrides,
  };
}

const LIBRARY_NAMES = [
  'el', 'textElement', 'callout', 'button', 'routeLink', 'errorBox', 'badge', 'familyLabel',
  'identityKind', 'identityLabel', 'conditionsLabel', 'issuerLabel', 'productName',
  'appendPrimarySource', 'isSafePrimaryUrl', 'formatEuros', 'formatRate', 'conditionOf',
  'conditionStateText', 'conditionRowText', 'headlineMetric', 'rateSummary', 'productCard', 'section',
  'renderCatalogueResultsBody', 'renderCatalogueResults',
];

function libraryUi(conditionsState) {
  const ui = makeContext();
  ui.ctx.state.conditions = conditionsState;
  load(ui.ctx, LIBRARY_NAMES, ['FAMILIES', 'CONDITION_ROWS']);
  const holder = new Node('section');
  holder.setAttribute('id', 'catalogue-results');
  ui.byId()['catalogue-results'] = holder;
  return { ...ui, holder };
}

function plainText(node) {
  return node.innerText;
}

test('un fallo al cargar las condiciones no se pinta como «ningún candidato con tasa»', () => {
  const ui = libraryUi({ loaded: false, loading: false, error: new Error('sin red'), byId: new Map(), referenceDate: null });
  ui.ctx.state.library.items = [product({ id: 'ACC-01', family: 'cuenta_remunerada' }), product({ id: 'DEP-02' })];
  ui.ctx.state.library.count = 2;

  ui.ctx.renderCatalogueResultsBody(ui.holder);
  const text = plainText(ui.holder);

  assert.doesNotMatch(text, /0 de 2 con tasa documentada/);
  assert.doesNotMatch(text, /Ningún candidato de esta búsqueda tiene una tasa documentada/);
  assert.match(text, /no se pudo comprobar cuántos tienen tasa documentada/);
  // Los candidatos se siguen mostrando: un fallo de red no los borra.
  assert.equal(ui.holder.children.filter((node) => node.className === 'result-list').length, 1);
});

test('el filtro de tasa documentada no vacía la biblioteca si las condiciones fallaron', () => {
  const ui = libraryUi({ loaded: false, loading: false, error: new Error('sin red'), byId: new Map(), referenceDate: null });
  ui.ctx.state.library.items = [product({ id: 'ACC-01', family: 'cuenta_remunerada' }), product({ id: 'DEP-02' })];
  ui.ctx.state.library.count = 2;
  ui.ctx.state.library.onlyDocumented = true;

  ui.ctx.renderCatalogueResultsBody(ui.holder);
  const text = plainText(ui.holder);

  assert.match(text, /no se oculta ningún candidato/);
  assert.doesNotMatch(text, /Ningún candidato de esta búsqueda tiene una tasa documentada/);
  assert.equal(ui.holder.children.filter((node) => node.className === 'result-list').length, 1);
});

test('con las condiciones cargadas el filtro vuelve a aplicarse y a contar bien', () => {
  const conditions = { loaded: true, loading: false, error: null, byId: new Map(), referenceDate: '2026-11-23' };
  conditions.byId.set('DEP-AC', {
    product_id: 'DEP-AC', family: 'deposito', display_name: 'Depósito activo',
    source: { url: 'https://example.invalid/dep', retrieved_at: '2026-11-02' },
    conditions: [{ metric: 'annual_rate_percent', state: 'known', value: '2.50', unit: 'PERCENT', notes: [] }],
    rate_tiers: [],
  });
  conditions.byId.set('DEP-ST', {
    product_id: 'DEP-ST', family: 'deposito', display_name: 'Depósito vencido',
    source: { url: 'https://example.invalid/dep2', retrieved_at: '2026-11-02' },
    conditions: [{ metric: 'annual_rate_percent', state: 'stale', value: '3.00', unit: 'PERCENT', notes: [] }],
    rate_tiers: [],
  });
  const ui = libraryUi(conditions);
  ui.ctx.state.library.items = [product({ id: 'DEP-AC' }), product({ id: 'DEP-ST' })];
  ui.ctx.state.library.count = 2;

  ui.ctx.renderCatalogueResultsBody(ui.holder);
  assert.match(plainText(ui.holder), /1 de 2 con tasa documentada/);
  assert.equal(ui.holder.children.filter((node) => node.className === 'result-list').length, 1);

  // renderCatalogueResults() limpia el contenedor antes de delegar aquí; se
  // reproduce ese contrato para no acumular dos listas.
  ui.holder.replaceChildren();
  ui.ctx.state.library.onlyDocumented = true;
  ui.ctx.renderCatalogueResultsBody(ui.holder);
  assert.match(plainText(ui.holder), /1 de 2 con tasa documentada/);
  const lists = ui.holder.children.filter((node) => node.className === 'result-list');
  assert.equal(lists.length, 1);
  // El filtro deja solo el depósito con tasa vigente, no los dos.
  assert.equal(lists[0].children.length, 1);
});

test('la lista de transcritos se repinta al cambiar la selección, no solo al cargar condiciones', () => {
  const ui = makeContext();
  ui.ctx.state.conditions.byId.set('DEP-EBN-12', {
    product_id: 'DEP-EBN-12', family: 'deposito', display_name: 'Depósito transcrito',
    provider: 'EBN Banco', identity_state: 'verified', origin: 'curated_conditions',
    source: { url: 'https://example.invalid/ebn', retrieved_at: '2026-11-03' },
    conditions: [{ metric: 'annual_rate_percent', state: 'known', value: '3.10', unit: 'PERCENT', notes: [] }],
    rate_tiers: [],
  });
  load(ui.ctx, [...LIBRARY_NAMES, 'renderCuratedCatalogue'], ['FAMILIES', 'CONDITION_ROWS']);

  const curated = new Node('section');
  curated.setAttribute('id', 'curated-results');
  ui.byId()['curated-results'] = curated;
  const tray = new Node('div');
  tray.setAttribute('id', 'library-selection');
  ui.byId()['library-selection'] = tray;

  ui.ctx.renderCuratedCatalogue();
  const buttonBefore = ui.byId()['choose-DEP-EBN-12'];
  assert.equal(buttonBefore.getAttribute('aria-pressed'), 'false');

  // toggleSelection() marca el id y repinta biblioteca y catálogo; debe
  // incluir también la sección transcrita.
  load(ui.ctx, ['toggleSelection', 'renderLibrarySelection', 'renderSelectionTray']);
  ui.ctx.state.selectedIds = [];
  ui.ctx.toggleSelection('DEP-EBN-12');

  assert.deepEqual([...ui.ctx.state.selectedIds], ['DEP-EBN-12']);
  const buttonAfter = ui.byId()['choose-DEP-EBN-12'];
  assert.equal(buttonAfter.getAttribute('aria-pressed'), 'true', 'el botón transcrito debe reflejar la selección');
  assert.match(buttonAfter.textContent, /Quitar de comparar/);
});

test('el aviso de capacidades del chat tiene un solo texto, antes y después de /api/status', () => {
  const ui = makeContext();
  load(ui.ctx, ['chatCapabilitiesText']);
  const capabilities = { context: true, history: false, catalogue: true, structured_education: false };
  const installed = ui.ctx.chatCapabilitiesText(capabilities);
  const refreshed = ui.ctx.chatCapabilitiesText(capabilities);
  assert.equal(installed, refreshed);
  assert.match(installed, /catálogo: puede consultar fichas documentadas/);
  assert.match(installed, /historial: desactivado/);
  // Sin capacidades declaradas el texto sigue siendo uno solo y no inventa.
  assert.equal(ui.ctx.chatCapabilitiesText(undefined), ui.ctx.chatCapabilitiesText(null));
  assert.match(ui.ctx.chatCapabilitiesText(undefined), /catálogo: no disponible/);
});

test('una serie de cálculo vacía se explica en lugar de dejar el resultado en blanco', () => {
  const ui = makeContext();
  load(ui.ctx, ['el', 'textElement', 'callout', 'errorBox', 'currencyFromApi', 'formatCurrency',
    'formatPercentValue', 'svgNode', 'makeScenarioChart', 'fillScenarioOutput'], ['FAMILIES']);
  const holder = new Node('section');
  const scenario = {
    status: 'current', version: 1,
    submitted: { principal: '1000', annual_rate_percent: '2', years: 1, monthly_contribution: '0', method: 'compound', inflation_percent: '0' },
    result: {
      hypothetical: true, not_prediction: true, currency: 'EUR',
      assumptions: { annual_rate_percent: '2' },
      summary: { contributions: '1000.00', final_balance: '1000.00', interest: '0.00', inflation_adjusted: '1000.00' },
      series: [],
    },
  };

  assert.doesNotThrow(() => ui.ctx.fillScenarioOutput(holder, scenario, ''));
  assert.match(plainText(holder), /no contiene el resumen y la serie esperados/);
});

test('una respuesta de cálculo sin assumptions no rompe el pintado', () => {
  const ui = makeContext();
  load(ui.ctx, ['el', 'textElement', 'callout', 'errorBox', 'currencyFromApi', 'formatCurrency',
    'formatPercentValue', 'svgNode', 'makeScenarioChart', 'fillScenarioOutput'], ['FAMILIES']);
  const holder = new Node('section');
  const scenario = {
    status: 'current', version: 1,
    submitted: { principal: '1000', annual_rate_percent: '2', years: 1, monthly_contribution: '0', method: 'compound', inflation_percent: '0' },
    result: {
      hypothetical: true, not_prediction: true, currency: 'EUR',
      summary: { contributions: '1000.00', final_balance: '1000.00', interest: '0.00', inflation_adjusted: '1000.00' },
      series: [{ month: 0, contributions: '1000.00', balance: '1000.00', real_balance: '1000.00' }],
    },
  };

  assert.doesNotThrow(() => ui.ctx.fillScenarioOutput(holder, scenario, ''));
  assert.match(plainText(holder), /Resultado del supuesto/);
});

test('el validador de la respuesta de cálculo rechaza series vacías o incompletas', () => {
  const ui = makeContext();
  load(ui.ctx, ['calculationResponseUsable']);
  const base = {
    hypothetical: true, not_prediction: true, currency: 'EUR',
    summary: { contributions: '1000.00', final_balance: '1000.00', interest: '0.00', inflation_adjusted: '1000.00' },
    series: [{ month: 0, contributions: '1000.00', balance: '1000.00', real_balance: '1000.00' }],
  };
  assert.equal(ui.ctx.calculationResponseUsable(base), true);
  assert.equal(ui.ctx.calculationResponseUsable({ ...base, series: [] }), false);
  assert.equal(ui.ctx.calculationResponseUsable({ ...base, series: [null] }), false);
  assert.equal(ui.ctx.calculationResponseUsable({ ...base, series: [{ contributions: '1000.00', balance: '1000.00', real_balance: '1000.00' }] }), false);
  assert.equal(ui.ctx.calculationResponseUsable({ ...base, summary: null }), false);
  assert.equal(ui.ctx.calculationResponseUsable({ ...base, summary: { contributions: '1000.00' } }), false);
  assert.equal(ui.ctx.calculationResponseUsable({ ...base, hypothetical: false }), false);
  assert.equal(ui.ctx.calculationResponseUsable(null), false);
});

test('un fallo de carga de condiciones no se presenta como «condiciones no documentadas»', () => {
  const ui = makeContext();
  ui.ctx.state.conditions = { loaded: false, loading: false, error: new Error('sin red'), byId: new Map(), referenceDate: null };
  load(ui.ctx, ['isSafePrimaryUrl', 'conditionSourceRef', 'hasDocumentedConditionsSource', 'simulationConditionsLabel']);

  const label = ui.ctx.simulationConditionsLabel(product({ id: 'ACC-01' }));
  assert.doesNotMatch(label, /Condiciones no documentadas/);
  assert.match(label, /No se pudieron cargar las condiciones/);

  // Con las condiciones cargadas y el producto ausente, la ausencia sí es un dato.
  ui.ctx.state.conditions = { loaded: true, loading: false, error: null, byId: new Map(), referenceDate: '2026-11-23' };
  assert.match(ui.ctx.simulationConditionsLabel(product({ id: 'ACC-01' })), /Condiciones no documentadas/);
});

test('el justificante no afirma que no hay condiciones cuando la carga falló', () => {
  const ui = makeContext();
  ui.ctx.state.conditions = { loaded: false, loading: false, error: new Error('sin red'), byId: new Map(), referenceDate: null };
  load(ui.ctx, ['el', 'conditionStateText', 'isSafePrimaryUrl', 'receiptConditionsTable'], ['CONDITION_ROWS', 'FAMILIES']);

  const table = ui.ctx.receiptConditionsTable('ACC-01');
  assert.match(plainText(table), /No se pudieron cargar las condiciones/);
  assert.doesNotMatch(plainText(table), /Ninguna condición transcrita/);

  ui.ctx.state.conditions = { loaded: true, loading: false, error: null, byId: new Map(), referenceDate: '2026-11-23' };
  assert.match(plainText(ui.ctx.receiptConditionsTable('ACC-01')), /Ninguna condición transcrita/);
});

test('una condición nula en la respuesta no rompe la revisión del ensayo', () => {
  const ui = makeContext();
  ui.ctx.state.conditions.byId.set('DEP-1', {
    product_id: 'DEP-1', family: 'deposito', display_name: 'Depósito uno',
    source: { url: 'https://example.invalid/x', retrieved_at: '2026-11-01' },
    conditions: [null, { metric: 'annual_rate_percent', state: 'known', value: '2.00', unit: 'PERCENT', notes: [] }],
    rate_tiers: [],
  });
  load(ui.ctx, ['el', 'textElement', 'badge', 'callout', 'section', 'appendPrimarySource', 'appendList',
    'isSafePrimaryUrl', 'familyLabel', 'identityLabel', 'identityKind', 'issuerLabel', 'productName',
    'formatEuros', 'formatRate', 'conditionSourceRef', 'hasDocumentedConditionsSource',
    'simulationConditionsLabel', 'conditionStateText', 'simulationProductReview'], ['CONDITION_ROWS', 'FAMILIES']);

  const holder = new Node('section');
  assert.doesNotThrow(() => ui.ctx.simulationProductReview(holder, product({ id: 'DEP-1' })));
  assert.match(plainText(holder), /Depósito uno/);
});

test('una condición nula en la respuesta no rompe la ficha de producto', () => {
  const ui = makeContext();
  ui.ctx.state.conditions.byId.set('DEP-1', {
    product_id: 'DEP-1', family: 'deposito', display_name: 'Depósito uno',
    source: { url: 'https://example.invalid/x', retrieved_at: '2026-11-01' },
    conditions: [null, { metric: 'annual_rate_percent', state: 'known', value: '2.00', unit: 'PERCENT', notes: [] }],
    rate_tiers: [null, { condition: 'sin_requisito', condition_label: 'Sin requisito', tae: '2.00', tin: '1.98' }],
  });
  load(ui.ctx, [...LIBRARY_NAMES, 'renderProductDetail', 'productEffectiveDate', 'conditionConsultedAt',
    'conditionValidityText', 'appendList'], ['FAMILIES', 'CONDITION_ROWS']);

  const holder = new Node('section');
  holder.setAttribute('id', 'product-detail');
  ui.byId()['product-detail'] = holder;
  ui.ctx.state.route = 'biblioteca';
  ui.ctx.state.detail = { id: 'DEP-1', product: product({ id: 'DEP-1' }), loading: false, error: null };

  assert.doesNotThrow(() => ui.ctx.renderProductDetail());
  assert.match(plainText(holder), /Tasa anual \(TAE\): 2,00 %/);
});

test('las razones de la comparación se filtran en lugar de romper el pintado', () => {
  const ui = makeContext();
  ui.ctx.state.selectedIds = ['ACC-01', 'ACC-02'];
  ui.ctx.state.compareIds = ['ACC-01', 'ACC-02'];
  ui.ctx.state.compareBusy = false;
  ui.ctx.state.compareError = null;
  ui.ctx.state.compareResult = {
    items: [product({ id: 'ACC-01', family: 'cuenta_remunerada' }), product({ id: 'ACC-02', family: 'cuenta_remunerada' })],
    reasons: 'un motivo que no es una lista',
  };
  load(ui.ctx, ['el', 'textElement', 'callout', 'badge', 'familyLabel', 'identityLabel', 'identityKind',
    'conditionsLabel', 'issuerLabel', 'productName', 'appendList',
    'appendPrimarySource', 'isSafePrimaryUrl', 'safeComparisonProduct', 'comparisonCard',
    'conditionOf', 'headlineMetric', 'rateSummary', 'conditionConsultedAt', 'conditionValidityText',
    'productEffectiveDate', 'renderComparisonResultBody'], ['FAMILIES', 'CONDITION_ROWS']);

  const holder = new Node('section');
  assert.doesNotThrow(() => ui.ctx.renderComparisonResultBody(holder));
  assert.match(plainText(holder), /Solo se comparan datos de identidad y condiciones documentadas/);
});

test('una referencia de fuente nula en el diagnóstico no rompe la vista', () => {
  const ui = makeContext();
  ui.ctx.state.selectedIds = ['DEP-EBN-12', 'DEP-SELF-12'];
  ui.ctx.state.catalogueCache.set('DEP-EBN-12', { id: 'DEP-EBN-12', name: 'EBN', family: 'deposito' });
  ui.ctx.state.catalogueCache.set('DEP-SELF-12', { id: 'DEP-SELF-12', name: 'SELF', family: 'deposito' });
  ui.ctx.state.diagnosis = {
    requestId: 1, ids: ['DEP-EBN-12', 'DEP-SELF-12'], busy: false, error: false,
    result: {
      criterion: 'deposit_tae_12m_eur',
      items: [
        { product_id: 'DEP-EBN-12', eligible: true, value: '3.1', reason_codes: [], source_refs: [null] },
        { product_id: 'DEP-SELF-12', eligible: true, value: '2.75', reason_codes: [], source_refs: [] },
      ],
    },
  };
  loadLines(ui.ctx, ['el', 'textElement', 'button', 'callout', 'productName', 'diagnosisApplicable',
    'renderDiagnosis', 'isSafePrimaryUrl'], ['ratePercent']);
  vm.runInContext(grabConst('RATE_VALUE') + '\n' + grabConst('DIAGNOSIS_REASONS'), ui.ctx);

  const holder = new Node('section');
  holder.setAttribute('id', 'compare-diagnosis');
  ui.byId()['compare-diagnosis'] = holder;
  assert.doesNotThrow(() => ui.ctx.renderDiagnosis());
  assert.match(plainText(holder), /TAE 3,10 %/);
});
