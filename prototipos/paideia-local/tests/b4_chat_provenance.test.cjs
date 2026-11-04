"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Ejecuta la sección real de chat con un shim DOM mínimo, sin navegador ni red.
function setup(fetch, status) {
  const code = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
  const byId = {};
  class Node {
    constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this.text = ''; this.checked = false; this.value = ''; }
    setAttribute(k, v) { this[k] = v; if (k === 'id') byId[v] = this; }
    appendChild(n) { this.children.push(n); return n; }
    append(...nodes) { nodes.forEach(n => this.appendChild(n)); }
    replaceChildren(...nodes) { this.children = nodes; this.text = ''; }
    addEventListener(event, fn) { this.listeners[event] = fn; }
    querySelector(selector) { return selector === '.field-help' ? this.children.find(x => x.className === 'field-help') : null; }
    focus() {}
    set textContent(s) { this.text = String(s); this.children = []; }
    get textContent() { return this.text + this.children.map(n => n.textContent).join(''); }
  }
  const document = {
    createElement: tag => new Node(tag),
    createTextNode: text => { const n = new Node('#text'); n.textContent = text; return n; },
    getElementById: id => byId[id],
  };
  const ctx = {
    document, fetch, URL, console,
    PaideiaChatContext: require('../static/chat_context_model.js'),
    PaideiaStructuredEducation: require('../static/structured_education_ui.js'),
    PROFILE_MODEL: require('../static/profile_model.js'),
    state: {
      chatMessage: '', chatTicket: null, chatBusy: false,
      // La puerta de envío aceptada en B8 exige un estado de IA concluyente.
      status: status || { ai: { status: 'configured_not_verified', capabilities: { context: true, history: true } } },
      profile: require('../static/profile_model.js').createEmptyProfile(),
    },
    API: { chat: '/api/chat' },
  };
  vm.createContext(ctx);
  const common = code.slice(code.indexOf('function isSafePrimaryUrl'), code.indexOf('const state ='))
    + code.slice(code.indexOf('function el('), code.indexOf('function setStatusChip'))
    + code.slice(code.indexOf('function displayProfileValue'), code.indexOf('function formatCurrency', code.indexOf('function displayProfileValue')))
    + code.slice(code.indexOf('function apiErrorText'), code.indexOf('function errorBox'));
  const start = code.indexOf('  const chat = section("Pregunta a Pai"');
  const chat = code.slice(start, code.indexOf('  if (state.storageNotice)', start));
  vm.runInContext(common + '\nfunction section(){ return el("section"); }\nfunction callout(s){ return el("div",{},s); }\nconst page = el("main");\n'
    + chat + '\nglobalThis.form = form; globalThis.submit = submit; globalThis.message = message; globalThis.feedback = feedback;', ctx);
  return {
    ...ctx, byId, consent: byId['chat-consent'],
    async send() { return ctx.form.listeners.submit({ preventDefault() {} }); },
    input(value) { ctx.message.value = value; ctx.message.listeners.input(); },
  };
}

function response(status, body) {
  return { ok: status >= 200 && status < 300, status, async json() { return body; } };
}

function condition(overrides = {}) {
  return {
    metric: 'annual_rate_percent',
    state: 'known',
    value: '3.10',
    unit: 'PERCENT',
    reason: 'CURATED_OFFICIAL',
    source_class: 'official',
    source_resolution: 'resolved',
    retrieved_at: '2026-11-03',
    effective_from: '2026-11-01',
    effective_to: '2026-12-01',
    limitations: [],
    notes: [],
    ...overrides,
  };
}

function catalogue(products, overrides = {}) {
  return { used: true, reference_date: '2026-11-04', products, ...overrides };
}

const WITHHELD = {
  answer: 'La TAE vigente es 9,99 % y la fuente es oficial.',
  answer_text_state: 'withheld_catalogue_evidence',
  answer_provenance: {
    text_validation: 'not_performed',
    text_state: 'withheld_catalogue_evidence',
    tool_sources_present: true,
    catalogue_evidence_present: true,
    limitations: [
      'El texto del modelo se ha omitido porque la consulta usó datos del catálogo; se muestran los datos locales con su fuente, clase y fechas.',
    ],
  },
  tool_events: [{ name: 'get_product_detail', state: 'executed' }],
};

test('catalogue evidence is shown with class, dates and value; unsafe model text is hidden', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only',
    ...WITHHELD,
    catalogue: catalogue([{
      id: 'DEP-KNOWN', name: 'Depósito conocido', family: 'deposito',
      issuer: 'Banco Sintético', identity_state: 'verified',
      conditions_state: 'documented', attribution_state: 'resolved',
      conditions: [condition()],
      rate_tiers: [{ condition: 'sin_requisito', condition_label: 'Sin domiciliar ingresos', tae: '2.75', tin: '2.73' }],
      rate_tiers_state: 'documented', rate_tiers_validity: 'known',
      rate_tiers_retrieved_at: '2026-11-03', rate_tiers_effective_to: '2026-12-01',
    }]),
    sources: [{ tool: 'get_product_detail', source: {
      source_ref: { id: 'condition:DEP-KNOWN:0' }, product_id: 'DEP-KNOWN',
      label: 'Depósito conocido — condiciones', url: 'https://example.invalid/dep-known',
      source_class: 'official', claim_scope: 'condition_documentation_only',
      retrieved_at: '2026-11-03', effective_from: '2026-11-01', effective_to: '2026-12-01',
    } }],
  }));
  ui.input('Pregunta sintética'); ui.consent.checked = true; await ui.send();

  const text = ui.feedback.textContent;
  for (const expected of ['Depósito conocido', '3.10', 'Oficial', '2026-11-03',
    '2026-11-01', '2026-12-01', 'documentada', 'texto del modelo']) {
    assert.ok(text.includes(expected), `missing ${expected} in: ${text}`);
  }
  assert.doesNotMatch(text, /9,99/);
  assert.doesNotMatch(text, /TAE vigente es/);
});

test('a secondary source is labelled secondary and never official', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only',
    answer: 'Texto no mostrado.',
    answer_text_state: 'withheld_catalogue_evidence',
    catalogue: catalogue([{
      id: 'DEP-PRESS', name: 'Depósito de prensa', family: 'deposito',
      issuer: 'Banco Sintético', identity_state: 'proposed',
      conditions_state: 'documented', attribution_state: 'resolved',
      conditions: [condition({
        source_class: 'secondary', reason: 'CURATED_SECONDARY_PRESS',
        notes: ['Fuente secundaria: confirmación en página oficial pendiente.'],
      })],
      rate_tiers: [], rate_tiers_state: 'absent', rate_tiers_validity: 'absent',
    }]),
    sources: [],
  }));
  ui.input('Pregunta sintética'); ui.consent.checked = true; await ui.send();

  const text = ui.feedback.textContent;
  assert.ok(text.includes('Secundaria'), text);
  assert.ok(text.includes('Secundaria') && !text.includes('Clase: Oficial'), text);
});

test('a conceptual turn keeps its text and shows the provenance limitation', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'external',
    answer: 'Explicación conceptual de la inflación.',
    answer_text_state: 'shown_unverified',
    catalogue: { used: false, products: [] },
    answer_provenance: {
      text_validation: 'not_performed',
      text_state: 'shown_unverified',
      limitations: [
        'El texto de la respuesta no se valida semánticamente contra las fuentes ni contra las condiciones; solo las citas de la herramienta son datos locales.',
      ],
    },
  }));
  ui.input('¿Qué es la inflación?'); ui.consent.checked = true; await ui.send();

  const text = ui.feedback.textContent;
  assert.ok(text.includes('Explicación conceptual de la inflación.'), text);
  assert.ok(text.includes('no se valida semánticamente'), text);
  assert.doesNotMatch(text, /PRUEBA SINTÉTICA/, 'external mode must not be labelled synthetic');
});

test('a withheld flag hides text even if the payload also carries prose', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only',
    answer: 'TEXTO PELIGROSO QUE NO DEBE MOSTRARSE',
    answer_text_state: 'withheld_catalogue_evidence',
    catalogue: catalogue([]),
    sources: [],
  }));
  ui.input('Pregunta sintética'); ui.consent.checked = true; await ui.send();

  assert.doesNotMatch(ui.feedback.textContent, /TEXTO PELIGROSO/);
  assert.match(ui.feedback.textContent, /No hay fichas locales|no devolvió|Sin fichas/);
});

test('an unbacked official-rate claim is hidden without catalogue evidence', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'external',
    answer: 'TEXTO PELIGROSO: la TAE vigente es 9,99 % según la fuente oficial.',
    answer_text_state: 'withheld_unbacked_claim',
    catalogue: { used: false, products: [] },
    answer_provenance: {
      text_validation: 'not_performed',
      text_state: 'withheld_unbacked_claim',
      limitations: ['Se ha omitido una afirmación de fuente oficial o vigencia sin datos locales que la respalden.'],
    },
  }));
  ui.input('¿Qué tasa hay?'); ui.consent.checked = true; await ui.send();

  assert.doesNotMatch(ui.feedback.textContent, /TEXTO PELIGROSO/);
  assert.doesNotMatch(ui.feedback.textContent, /9,99/);
  assert.match(ui.feedback.textContent, /sin datos locales/);
});

test('unsafe source links are suppressed while their class is not invented', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only',
    ...WITHHELD,
    catalogue: catalogue([]),
    sources: [{ tool: 'get_product_detail', source: {
      label: 'Fuente mala', url: 'javascript:alert(1)', source_class: 'unknown',
      claim_scope: 'condition_documentation_only',
    } }],
  }));
  ui.input('Pregunta sintética'); ui.consent.checked = true; await ui.send();

  assert.doesNotMatch(ui.feedback.textContent, /Fuente mala/);
  assert.doesNotMatch(ui.feedback.textContent, /Clase: Oficial/);
});

test('calculator turn renders the local engine result and assumptions, never model prose', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only',
    answer: '',
    answer_text_state: 'withheld_unbacked_claim',
    catalogue: { used: false, products: [] },
    calculation: {
      hypothetical: true, not_prediction: true, currency: 'EUR',
      assumptions: {
        principal: '1000.00', annual_rate_percent: '3', years: 2,
        monthly_contribution: '0.00', method: 'compound', inflation_percent: '2',
        annual_rate_convention: 'effective_annual_rate',
        monthly_contribution_timing: 'end_of_month',
        taxes_included: false, fees_included: false,
      },
      summary: {
        contributions: '1000.00', final_balance: '1060.90',
        interest: '60.90', inflation_adjusted: '1019.70',
      },
      disclaimer: 'Escenario hipotético calculado por el motor determinista local; no es una predicción ni una oferta.',
    },
    answer_provenance: {
      text_validation: 'not_performed', text_state: 'withheld_unbacked_claim',
      withheld_reason: 'calculation',
      limitations: ['Se ha omitido el texto del modelo en este turno de calculadora.'],
    },
  }));
  ui.input('Calcula 1000 euros al 3 % dos años'); ui.consent.checked = true; await ui.send();

  const text = ui.feedback.textContent;
  for (const expected of ['motor determinista local', '1.000,00', '1.060,90', '60,90',
    '1.019,70', '3,00 %', '2 años', 'compuesto', '0,00']) {
    assert.ok(text.includes(expected), `missing ${expected} in: ${text}`);
  }
  assert.match(text, /Interés:\s*60,90 EUR/);
  assert.match(text, /Saldo final:\s*1\.060,90 EUR/);
  assert.doesNotMatch(text, /El interés obtenido/);
});

test('a malformed calculation is not rendered and declares the limit', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only',
    answer: '',
    answer_text_state: 'withheld_unbacked_claim',
    catalogue: { used: false, products: [] },
    calculation: {
      hypothetical: true, not_prediction: true, currency: 'EUR',
      assumptions: { principal: '1000.00', annual_rate_percent: '3', years: 2,
        monthly_contribution: '0.00', method: 'compound', inflation_percent: '2' },
      summary: { contributions: '1000.00', final_balance: '1060.90',
        interest: '60.90', inflation_adjusted: '1019.70', injected: '9999.99' },
    },
    answer_provenance: { text_state: 'withheld_unbacked_claim', withheld_reason: 'calculation',
      limitations: [] },
  }));
  ui.input('Calcula'); ui.consent.checked = true; await ui.send();

  const text = ui.feedback.textContent;
  assert.doesNotMatch(text, /1\.060,90/);
  assert.doesNotMatch(text, /9999,99/);
  assert.match(text, /no llegó con una forma válida|forma válida/);
});

test('chat catalogue cards show the real conflicts, unknown fields and condition source links', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only',
    answer: '', answer_text_state: 'withheld_catalogue_evidence',
    catalogue: catalogue([{
      id: 'DEP-REVIEW', name: 'Depósito con conflicto', family: 'deposito',
      issuer: 'Banco Sintético', identity_state: 'proposed',
      conditions_state: 'documented_not_current', attribution_state: 'resolved',
      conditions: [condition({ source_class: 'official',
        sources: [{ url: 'https://example.invalid/synthetic/cond', class: 'official',
          retrieved_at: '2026-11-03', resolution: 'resolved' }] })],
      rate_tiers: [], rate_tiers_state: 'absent', rate_tiers_validity: 'absent',
      conflicts: ['Conflicto real: dos plazos distintos para la misma entidad.'],
      unknown_fields: ['plazos disponibles', 'fecha efectiva de cada oferta'],
      review_state: 'conflicts_and_unknown_fields',
      conditions_state_reasons: ['Revisión pendiente: conflictos declarados.'],
    }]),
    sources: [],
    answer_provenance: { text_state: 'withheld_catalogue_evidence',
      withheld_reason: 'catalogue_evidence', limitations: [] },
  }));
  ui.input('Detalle'); ui.consent.checked = true; await ui.send();

  const text = ui.feedback.textContent;
  assert.ok(text.includes('Conflicto real: dos plazos distintos para la misma entidad.'), text);
  assert.ok(text.includes('plazos disponibles'), text);
  assert.ok(text.includes('fecha efectiva de cada oferta'), text);
  assert.match(text, /Conflictos/);
  assert.match(text, /Campos desconocidos/);
  const anchors = [];
  (function walk(node) { if (node && node.tag === 'a') anchors.push(node);
    for (const child of (node && node.children) || []) walk(child); })(ui.feedback);
  assert.ok(anchors.some(link => link.href === 'https://example.invalid/synthetic/cond'),
    JSON.stringify(anchors.map(a => a.href)));
});

test('aggregate source truncation is declared instead of silently slicing to 20', async () => {
  const sources = Array.from({ length: 20 }, (_, index) => ({
    tool: 'search_products',
    source: { source_ref: { id: `identity:SIN-${index}` }, kind: 'identity',
      claim_scope: 'product_identity_only', url: `https://example.invalid/${index}`,
      retrieved_at: '2026-11-03' },
  }));
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only', answer: 'texto no mostrado',
    answer_text_state: 'withheld_catalogue_evidence',
    catalogue: catalogue([]), sources, sources_total: 22, sources_truncated: 2,
    answer_provenance: { text_state: 'withheld_catalogue_evidence', limitations: [] },
  }));
  ui.input('Pregunta'); ui.consent.checked = true; await ui.send();

  assert.match(ui.feedback.textContent, /20 de 22/);
  assert.match(ui.feedback.textContent, /2 se omiten|2 referencias/);
});

test('an incoherent metric/unit or unknown-with-value is not shown as a usable figure', async () => {
  const ui = setup(async () => response(200, {
    provider_mode: 'test_only', answer: 'texto no mostrado',
    answer_text_state: 'withheld_catalogue_evidence',
    catalogue: catalogue([{
      id: 'DEP-BAD', name: 'Depósito mal formado', family: 'deposito',
      issuer: 'Banco Sintético', identity_state: 'proposed',
      conditions_state: 'conditions_unknown', attribution_state: 'unresolved',
      conditions: [
        condition({ metric: 'annual_rate_percent', unit: 'MONTHS', value: '12' }),
        condition({ metric: 'term_months', state: 'unknown', unit: 'MONTHS', value: '99' }),
      ],
      rate_tiers: [], rate_tiers_state: 'absent', rate_tiers_validity: 'absent',
    }]), sources: [],
    answer_provenance: { text_state: 'withheld_catalogue_evidence', limitations: [] },
  }));
  ui.input('Detalle'); ui.consent.checked = true; await ui.send();

  const text = ui.feedback.textContent;
  assert.match(text, /unidad incoherente/);
  assert.match(text, /sin valor documentado/);
  assert.doesNotMatch(text, /12 meses/);
  assert.doesNotMatch(text, /99 meses/);
});
