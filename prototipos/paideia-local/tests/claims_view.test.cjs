'use strict';
// Afirmaciones cerradas del servidor: el chat no debe mostrar prosa libre del modelo.
// DOM mínimo en el propio test: el repo no tiene jsdom ni package.json.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const claims = require('../static/claims_view.js');

const EMPTY_TEXT = 'No hay una explicación cerrada para esta pregunta con los datos disponibles.';

function makeDocument() {
  class Element {
    constructor(tag) {
      this.tagName = String(tag).toUpperCase();
      this.children = [];
      this.attrs = Object.create(null);
      this._text = '';
      this.className = '';
      this.ownerDocument = null;
    }
    appendChild(node) { this.children.push(node); return node; }
    append(...nodes) { for (const node of nodes) this.appendChild(node); return this; }
    removeChild(node) {
      const index = this.children.indexOf(node);
      if (index >= 0) this.children.splice(index, 1);
      return node;
    }
    setAttribute(key, value) { this.attrs[key] = String(value); }
    getAttribute(key) { return Object.prototype.hasOwnProperty.call(this.attrs, key) ? this.attrs[key] : null; }
    hasAttribute(key) { return Object.prototype.hasOwnProperty.call(this.attrs, key); }
    set textContent(value) { this._text = String(value); this.children.length = 0; }
    get textContent() { return this._text + this.children.map((child) => child.textContent).join(''); }
  }
  const document = {
    createElement(tag) { const element = new Element(tag); element.ownerDocument = document; return element; },
    createTextNode(text) { const node = new Element('#text'); node.ownerDocument = document; node.textContent = text; return node; },
  };
  return document;
}

function walk(node, found = []) {
  found.push(node);
  for (const child of node.children || []) walk(child, found);
  return found;
}

function byTag(root, tag) {
  return walk(root).filter((node) => node.tagName === tag.toUpperCase());
}

function box() {
  const document = makeDocument();
  return { document, element: document.createElement('div') };
}

function shown(items, overrides = {}) {
  return { version: 'paideia-education-v2', state: 'shown', items, count: items.length, reason: null, ...overrides };
}

test('expone un contrato congelado con los tres estados', () => {
  assert.deepEqual(claims.states, ['shown', 'empty', 'rejected']);
  assert.equal(Object.isFrozen(claims), true);
  assert.equal(Object.isFrozen(claims.states), true);
  assert.equal(typeof claims.render, 'function');
});

test('shown respeta el orden del servidor y renderiza el texto completo sin truncar', () => {
  const { element } = box();
  const long = `${'Texto largo con acentos ñ y cifras 3,10 %. '.repeat(6)}Fin.`;
  const ok = claims.render(element, shown([
    { id: 'zeta', text: 'Primera afirmación cerrada.' },
    { id: 'alfa', text: long },
  ]));

  assert.equal(ok, true);
  assert.equal(element.children.length, 1);
  const block = element.children[0];
  assert.equal(block.getAttribute('role'), 'group');
  assert.ok((block.getAttribute('aria-label') || '').length > 0);
  assert.match(block.className, /paper-section/);

  const lists = byTag(block, 'ul');
  assert.equal(lists.length, 1);
  const items = byTag(block, 'li');
  // El servidor compone en orden de catálogo: la UI no debe reordenar.
  assert.deepEqual(items.map((li) => li.getAttribute('data-claim-id')), ['zeta', 'alfa']);
  assert.deepEqual(items.map((li) => li.textContent), ['Primera afirmación cerrada.', long]);
});

test('shown sin afirmaciones utilizables muestra el aviso neutro', () => {
  for (const items of [[], [null], [{ id: 'solo-id' }], [{ id: '', text: 'x' }], [{ id: 'a', text: '   ' }]]) {
    const { element } = box();
    assert.equal(claims.render(element, shown(items)), true);
    assert.equal(byTag(element, 'ul').length, 0);
    assert.equal(byTag(element, 'li').length, 0);
    assert.equal(element.textContent, EMPTY_TEXT);
  }
});

test('empty muestra el aviso neutro exacto y accesible', () => {
  const { element } = box();
  const ok = claims.render(element, { version: 'paideia-education-v2', state: 'empty', items: [], count: 0, reason: null });

  assert.equal(ok, true);
  assert.equal(element.children.length, 1);
  const block = element.children[0];
  assert.equal(block.getAttribute('role'), 'group');
  assert.ok((block.getAttribute('aria-label') || '').length > 0);
  assert.match(block.className, /info-note/);
  assert.equal(block.textContent, EMPTY_TEXT);
  assert.equal(element.textContent, EMPTY_TEXT);
});

test('rejected avisa sin reproducir el texto del modelo ni el motivo técnico', () => {
  const { element } = box();
  const ok = claims.render(element, {
    version: 'paideia-education-v2',
    state: 'rejected',
    items: [{ id: 'x', text: 'TEXTO DEL MODELO NO VALIDADO' }],
    count: 1,
    reason: 'invalid_claim_id',
  });

  assert.equal(ok, true);
  assert.equal(byTag(element, 'li').length, 0);
  const text = element.textContent;
  assert.doesNotMatch(text, /TEXTO DEL MODELO NO VALIDADO/);
  assert.doesNotMatch(text, /invalid_claim_id/);
  assert.match(text, /no se pudo validar/i);
  assert.match(text, /no se muestra/i);
});

test('un claims ausente degrada sin lanzar y retira el bloque anterior', () => {
  const { element } = box();
  assert.equal(claims.render(element, shown([{ id: 'a', text: 'Afirmación previa.' }])), true);
  assert.equal(element.children.length, 1);

  for (const value of [undefined, null]) {
    assert.equal(claims.render(element, value), false);
    assert.equal(element.children.length, 0);
  }
});

test('una forma inválida de claims degrada sin lanzar y sin dejar nodos', () => {
  const shapes = ['shown', 'raro', 42, true, [], { items: [{ id: 'a', text: 'x' }] }, { state: 'explode', items: [] }];
  for (const value of shapes) {
    const { element } = box();
    assert.equal(claims.render(element, value), false, `forma inesperada: ${JSON.stringify(value)}`);
    assert.equal(element.children.length, 0);
  }
});

test('un contenedor no válido no lanza y devuelve false', () => {
  const valid = shown([{ id: 'a', text: 'Afirmación.' }]);
  for (const container of [null, undefined, {}, 'div', { appendChild: 'no' }]) {
    assert.equal(claims.render(container, valid), false);
  }
});

test('render es idempotente y sustituye el bloque anterior', () => {
  const { element } = box();
  const payload = shown([
    { id: 'b', text: 'Segunda.' },
    { id: 'a', text: 'Primera.' },
  ]);

  assert.equal(claims.render(element, payload), true);
  assert.equal(claims.render(element, payload), true);
  assert.equal(element.children.length, 1);
  assert.equal(byTag(element, 'li').length, 2);
  assert.equal(byTag(element, 'ul').length, 1);
  assert.equal((element.textContent.match(/Primera\./g) || []).length, 1);

  assert.equal(claims.render(element, shown([{ id: 'c', text: 'Tercera.' }])), true);
  assert.equal(element.children.length, 1);
  assert.deepEqual(byTag(element, 'li').map((li) => li.textContent), ['Tercera.']);
});

test('el aviso neutro no se duplica al renderizar empty dos veces', () => {
  const { element } = box();
  const payload = { version: 'paideia-education-v2', state: 'empty', items: [], count: 0, reason: null };
  assert.equal(claims.render(element, payload), true);
  assert.equal(claims.render(element, payload), true);
  assert.equal(element.children.length, 1);
  assert.equal(element.textContent, EMPTY_TEXT);
});

test('conserva los nodos ajenos del contenedor y solo sustituye su bloque', () => {
  const { document, element } = box();
  const previous = document.createElement('p');
  previous.textContent = 'Contenido previo del mensaje.';
  element.appendChild(previous);

  assert.equal(claims.render(element, shown([{ id: 'a', text: 'Afirmación.' }])), true);
  assert.equal(element.children.length, 2);
  assert.equal(element.children[0], previous);

  assert.equal(claims.render(element, { state: 'empty', items: [], count: 0 }), true);
  assert.equal(element.children.length, 2);
  assert.equal(element.children[0], previous);
  assert.equal(element.children[1].textContent, EMPTY_TEXT);

  assert.equal(claims.render(element, null), false);
  assert.equal(element.children.length, 1);
  assert.equal(element.children[0], previous);
});

test('un texto con marcado se muestra literal y no crea ni ejecuta nodos', () => {
  const { element } = box();
  const text = '<img src=x onerror="alert(1)"> y <script>alert(2)</script> fin';
  assert.equal(claims.render(element, shown([{ id: 'xss', text }])), true);

  assert.equal(byTag(element, 'img').length, 0);
  assert.equal(byTag(element, 'script').length, 0);
  assert.equal(byTag(element, 'li')[0].textContent, text);
  assert.equal(element.textContent, text);
});

test('la fuente no usa HTML crudo ni evaluación dinámica', () => {
  const source = fs.readFileSync(path.join(__dirname, '../static/claims_view.js'), 'utf8');
  assert.doesNotMatch(source, /\.(?:inner|outer)HTML\s*=/);
  assert.doesNotMatch(source, /insertAdjacentHTML|document\.write|eval\s*\(|new\s+Function\s*\(/);
});
