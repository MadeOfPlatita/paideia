'use strict';
// Afirmaciones cerradas del servidor (contrato paideia-education-v2).
// Pinta solo textos que llegan del servidor; nunca prosa libre del modelo.
// Construye nodos con createElement/textContent: ningún HTML crudo del servidor.
(function (root, factory) {
  const api = factory(root);
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.PaideiaClaims = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (root) {
  const STATES = Object.freeze(['shown', 'empty', 'rejected']);
  const EMPTY_TEXT = 'No hay una explicación cerrada para esta pregunta con los datos disponibles.';
  const REJECTED_TEXT = 'La respuesta del modelo no se pudo validar con los datos del servidor y no se muestra. No se reproduce su texto.';
  const MARKER = 'data-paideia-claims';
  const LABELS = Object.freeze({
    shown: 'Afirmaciones cerradas para esta respuesta',
    empty: 'Sin explicación cerrada para esta respuesta',
    rejected: 'Respuesta del modelo no validada'
  });

  const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);

  // Afirmaciones utilizables: id y texto no vacíos, sin duplicados de id. Se
  // conserva el orden del servidor: claims_channel compone en el orden del
  // catálogo, que es pedagógico; reordenar por id lo rompería. El orden es
  // determinista porque el DTO lo es, así que el render sigue siendo idempotente.
  function usableItems(claims) {
    if (!Array.isArray(claims.items)) return [];
    const seen = new Set();
    const items = [];
    for (const item of claims.items) {
      if (!isObject(item)) continue;
      if (typeof item.id !== 'string' || item.id.length === 0) continue;
      if (typeof item.text !== 'string' || item.text.trim().length === 0) continue;
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      items.push({ id: item.id, text: item.text });
    }
    return items;
  }

  // Retira solo los bloques propios; el resto del contenedor del chat no se toca.
  function forget(container) {
    if (!container.children) return;
    const children = Array.prototype.slice.call(container.children);
    for (const child of children) {
      if (!child || typeof child.getAttribute !== 'function') continue;
      if (child.getAttribute(MARKER) === null) continue;
      if (typeof container.removeChild === 'function') container.removeChild(child);
    }
  }

  function blockElement(document, tag, className, state) {
    const block = document.createElement(tag);
    block.className = className;
    block.setAttribute('role', 'group');
    block.setAttribute('aria-label', LABELS[state]);
    block.setAttribute(MARKER, state);
    return block;
  }

  function notice(document, state, text) {
    const block = blockElement(document, 'div', 'info-note claims-block', state);
    const paragraph = document.createElement('p');
    paragraph.textContent = text;
    block.appendChild(paragraph);
    return block;
  }

  function shownBlock(document, claims, items) {
    const block = blockElement(document, 'section', 'paper-section claims-block', 'shown');
    if (typeof claims.version === 'string' && /^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$/.test(claims.version)) {
      block.setAttribute('data-claims-version', claims.version);
    }
    const list = document.createElement('ul');
    list.className = 'text-list';
    for (const item of items) {
      const entry = document.createElement('li');
      entry.setAttribute('data-claim-id', item.id);
      entry.textContent = item.text;
      list.appendChild(entry);
    }
    block.appendChild(list);
    return block;
  }

  // true si escribió un bloque (shown, empty o rejected); false si el campo no es
  // utilizable. En ambos casos retira el bloque propio anterior: nunca lanza.
  function render(container, claims) {
    if (!container || typeof container !== 'object' || typeof container.appendChild !== 'function') return false;
    const document = container.ownerDocument || (root && root.document) || null;
    if (!document || typeof document.createElement !== 'function') return false;

    forget(container);

    if (!isObject(claims)) return false;
    const state = typeof claims.state === 'string' ? claims.state : '';

    if (state === 'shown') {
      const items = usableItems(claims);
      container.appendChild(items.length ? shownBlock(document, claims, items) : notice(document, 'empty', EMPTY_TEXT));
      return true;
    }
    if (state === 'empty') {
      container.appendChild(notice(document, 'empty', EMPTY_TEXT));
      return true;
    }
    if (state === 'rejected') {
      container.appendChild(notice(document, 'rejected', REJECTED_TEXT));
      return true;
    }
    return false;
  }

  return Object.freeze({ render, states: STATES });
});
