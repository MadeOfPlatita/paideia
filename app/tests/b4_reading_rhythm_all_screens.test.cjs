// Auditoría del ritmo de lectura en TODA la aplicación, no solo en el chat.
//
// Lección medida en pantalla: la respuesta del chat se veía como un bloque
// monolítico porque no existía NINGUNA regla CSS para sus <p>. El mismo defecto
// aparecía en otras pantallas —la revisión de la tarjeta de producto, la vista
// previa de Privacidad, las condiciones de la ficha— y ningún test lo notaba,
// porque los tests miraban el texto, no el ritmo vertical.
//
// Qué comprueba este test, y por qué así:
//
// El navegador da a los <p> 1em de margen arriba y abajo. Un bloque se lee como
// una masa solo cuando alguien pone ese margen a CERO y no devuelve el hueco por
// otro lado. Es exactamente el mecanismo que produjo el bug. Por eso la condición
// que se exige es esta, y solo esta:
//
//     si un contenedor anula el margen de sus párrafos,
//     tiene que declarar también una separación positiva para ellos.
//
// Es una condición decidible sobre el CSS, sin simulador de cascada de por medio
// (un simulador propio se equivoca y entonces el test se autoengaña: pasó durante
// la escritura de este fichero). No marca como roto un contenedor que se apoya en
// el margen del navegador: eso está bien y no hay que llenarlo de CSS.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const STATIC = path.join(__dirname, '..', 'static');
const CSS_FILES = ['styles.css', 'spacing.css', 'dark_theme.css', 'comparison_report.css',
  'context_help.css', 'receipt_print.css'];

// ————————————————————————— lectura del CSS —————————————————————————

function parseSheet(file, source) {
  const rules = [];
  let order = 0;

  const clean = source
    .replace(/\/\*[\s\S]*?\*\//g, '')
    // `@charset` y `@import` no llevan bloque: sin quitarlos, el `:root` que viene
    // detrás queda pegado a ellos y su selector deja de ser `:root`.
    .replace(/^\s*@(charset|import)[^;]*;/gm, '');

  const matchingBrace = (from) => {
    let depth = 0;
    for (let i = from; i < clean.length; i += 1) {
      if (clean[i] === '{') depth += 1;
      else if (clean[i] === '}') {
        depth -= 1;
        if (depth === 0) return i;
      }
    }
    return clean.length;
  };

  const walk = (start, end) => {
    let index = start;
    while (index < end) {
      const open = clean.indexOf('{', index);
      if (open < 0 || open >= end) return;
      const prelude = clean.slice(index, open).trim();
      const close = matchingBrace(open);
      index = close + 1;
      if (!prelude) continue;

      if (prelude.startsWith('@')) {
        // Los @media de ancho pequeño no son el caso base: se saltan enteros.
        if (/max-width/.test(prelude)) continue;
        // @media print, @media screen, @supports: se recorren por dentro.
        walk(open + 1, close);
        continue;
      }

      const decls = {};
      for (const part of clean.slice(open + 1, close).split(';')) {
        const at = part.indexOf(':');
        if (at < 0) continue;
        decls[part.slice(0, at).trim().toLowerCase()] = part.slice(at + 1).trim();
      }
      for (const raw of prelude.split(',')) {
        const selector = raw.trim().replace(/\s+/g, ' ');
        if (selector) rules.push({ file, selector, decls, order: order++ });
      }
    }
  };

  walk(0, clean.length);
  return rules;
}

const RULES = CSS_FILES.flatMap((file) => {
  const full = path.join(STATIC, file);
  return fs.existsSync(full) ? parseSheet(file, fs.readFileSync(full, 'utf8')) : [];
});

// ————————————————————————— predicados —————————————————————————

// Longitud CSS simple -> píxeles. `em`/`rem` a 16px, que es la raíz declarada.
function toPx(value) {
  if (typeof value !== 'string') return null;
  const token = value.trim().split(/\s+/)[0];
  const match = /^(-?[\d.]+)(px|rem|em)?$/.exec(token);
  if (!match) return null;
  const unit = match[2] || '';
  if (unit === '%' || token === 'auto') return null;
  return unit === 'px' || unit === '' ? parseFloat(match[1]) : parseFloat(match[1]) * 16;
}

// ¿La regla selecciona directamente el bloque de texto (p, p.clase, .clase p...)?
// Solo `p` y `li`: un `dd` casi nunca es prosa secuencial —va emparejado con su
// `dt` en una rejilla o lista de definición— y su margen a cero es deliberado.
function targetsParagraphs(selector) {
  return /(^|[\s,>])(p|li)($|[\s,:.>[+~])/.test(selector)
    || /:is\([^)]*\b(p|li)\b[^)]*\)/.test(selector);
}

// Margen que una regla impone al párrafo: [arriba, abajo] en píxeles, o null.
function declaredMargins(decls) {
  const expand = (value) => {
    const tokens = String(value).trim().split(/\s+/);
    if (tokens.length === 1) return [tokens[0], tokens[0], tokens[0], tokens[0]];
    if (tokens.length === 2) return [tokens[0], tokens[1], tokens[0], tokens[1]];
    if (tokens.length === 3) return [tokens[0], tokens[1], tokens[2], tokens[1]];
    return [tokens[0], tokens[1], tokens[2], tokens[3]];
  };
  const shorthand = 'margin' in decls ? expand(decls.margin) : null;
  const top = 'margin-top' in decls ? decls['margin-top'] : (shorthand ? shorthand[0] : undefined);
  const bottom = 'margin-bottom' in decls ? decls['margin-bottom'] : (shorthand ? shorthand[2] : undefined);
  if (top === undefined && bottom === undefined) return null;
  return [toPx(top), toPx(bottom)];
}

// ¿La regla anula el margen del bloque de texto? (cero arriba y cero abajo)
function zeroesParagraphMargin(rule, paragraphClass) {
  const selector = rule.selector;
  // Una regla puede anular el margen por la clase del párrafo (`.field-help`,
  // `p.field-help`) sin nombrar la etiqueta, que es justo como estaba escrito
  // `.field-help { margin: 0 }`. Si no se acepta ese caso, el detector se pierde
  // el bug real.
  const byClass = paragraphClass
    && new RegExp(`\\.${paragraphClass.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&')}(?![\\w-])`).test(selector);
  if (!targetsParagraphs(selector) && !byClass) return false;
  // Los resets de extremos son deliberados: quitan el aire de los bordes de la
  // caja, no el de en medio.
  if (/:(first|last)-(child|of-type)/.test(selector)) return false;
  const margins = declaredMargins(rule.decls);
  if (!margins) return false;
  const [top, bottom] = margins;
  return top === 0 && bottom === 0;
}

// Último compuesto de un selector: lo que hay a la derecha del último combinador.
function lastCompound(selector) {
  const parts = selector.split(/[\s>+~]+/).filter(Boolean);
  return parts.length ? parts[parts.length - 1] : '';
}

// ¿La regla declara una separación positiva entre bloques? Devuelve el valor en
// píxeles o null. `container` es el nombre del contenedor que se está auditando:
// se exige que la regla sea SUYA y no de un descendiente lejano.
function declaresSpacing(rule, container) {
  const selector = rule.selector;
  const decls = rule.decls;

  // a) hermanos con margen superior: `x + y`, `x ~ y`
  if (/(^|[\s,>])(\*|p|li|dd|ul|ol|dl)(\.[\w-]+)?\s*[+~]\s*(\*|p|li|dd|ul|ol|dl)/.test(selector)) {
    const value = 'margin-top' in decls ? decls['margin-top'] : decls.margin;
    const px = toPx(value);
    if (px !== null && px > 0) return px;
  }

  // b) margen positivo en el propio bloque de texto
  if (targetsParagraphs(selector)) {
    const margins = declaredMargins(decls);
    if (margins) {
      const positive = margins.filter((value) => value !== null && value > 0);
      if (positive.length) return Math.max(...positive);
    }
  }

  // c) rejilla o fila flexible con hueco, pero solo si el hueco es del propio
  // contenedor. El `gap: 1px` de las barras del código de barras del justificante
  // no separa párrafos; contarlo daba un falso «1px» en el justificante.
  if (decls.display === 'grid' || decls.display === 'flex') {
    if (!lastCompound(selector).includes(container)) return null;
    const px = toPx(decls.gap || decls['row-gap']);
    if (px !== null && px > 0) return px;
  }
  return null;
}

// Reglas que participan en un contenedor: las que nombran su clase (o su id) como
// token completo en cualquier punto del selector. Se exige token completo para que
// `#receipt-print .doc-box dd` no cuente como una regla de `.receipt`: en el
// justificante impreso el id y la clase son cosas distintas.
function mentionsContainer(selector, container, paragraphClass) {
  const classToken = (name) => new RegExp(`\\.${name.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&')}(?![\\w-])`);
  const token = container.startsWith('#') ? new RegExp(`${container.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&')}(?![\\w-])`) : classToken(container);
  if (token.test(selector)) return true;
  if (paragraphClass && classToken(paragraphClass).test(selector)) return true;
  return false;
}

function scopedTo(container, paragraphClass) {
  return RULES.filter((rule) => rule.selector.split(',')
    .some((part) => mentionsContainer(part.trim(), container, paragraphClass)));
}

// Diagnóstico de un contenedor: qué reglas anulan el margen y qué separación hay.
function auditContainer(container, paragraphClass) {
  const scope = scopedTo(container, paragraphClass);
  const zeroing = scope.filter((rule) => zeroesParagraphMargin(rule, paragraphClass));
  let spacing = null;
  for (const rule of scope) {
    const value = declaresSpacing(rule, container);
    if (value !== null && (spacing === null || value > spacing.value)) {
      spacing = { value, selector: rule.selector, file: rule.file };
    }
  }
  return { zeroing, spacing };
}

// ————————————————————————— los contenedores reales —————————————————————————

// Cada entrada es un contenedor que app.js pinta con VARIOS párrafos hermanos,
// sacado de leer los render. `paragraphClass` es la clase del párrafo que pinta y
// solo se usa para localizar reglas dirigidas a esa clase.
const CONTAINERS = [
  { label: 'respuesta del chat', container: '#chat-feedback', paragraphClass: '' },
  { label: 'trazabilidad plegada del chat', container: 'chat-limitations', paragraphClass: 'field-help' },
  { label: 'detalle de la ficha en el chat', container: 'chat-card-detail', paragraphClass: 'field-help' },
  { label: 'herramientas del chat', container: 'chat-tools', paragraphClass: 'field-help' },
  { label: 'resumen del catálogo en el chat', container: 'chat-catalogue', paragraphClass: 'field-help' },
  { label: 'avisos .note', container: 'note', paragraphClass: '' },
  { label: 'avisos .info-note', container: 'info-note', paragraphClass: 'small' },
  { label: 'avisos .warning-note', container: 'warning-note', paragraphClass: '' },
  { label: 'avisos .error-note', container: 'error-note', paragraphClass: '' },
  { label: 'avisos .success-note', container: 'success-note', paragraphClass: '' },
  { label: 'bandeja de selección', container: 'selection-tray', paragraphClass: 'small' },
  { label: 'revisión de la tarjeta de producto', container: 'product-review', paragraphClass: 'product-review-label' },
  { label: 'vista previa de Privacidad', container: 'privacy-preview', paragraphClass: 'small' },
  { label: 'ayuda de campo en varios párrafos', container: 'field-help', paragraphClass: 'field-help' },
  { label: 'justificante del ensayo', container: 'receipt', paragraphClass: '' },
  // `.profile-answer-box` queda fuera a propósito: no son dos párrafos de prosa
  // sino un rótulo y su valor, y el aire lo pone `.profile-answer-value` con su
  // propio margen. Medido en navegador: 6px, correcto.
  { label: 'panel de la ficha de producto', container: 'detail-panel', paragraphClass: '' },
];

test('todo contenedor que anula el margen de sus párrafos devuelve el hueco', () => {
  const broken = [];
  const audited = [];
  for (const entry of CONTAINERS) {
    const { zeroing, spacing } = auditContainer(entry.container, entry.paragraphClass);
    if (!zeroing.length) {
      audited.push(`${entry.label}: se apoya en el margen del navegador (1em), correcto`);
      continue;
    }
    if (spacing) {
      audited.push(`${entry.label}: ${spacing.value}px por ${spacing.file} → ${spacing.selector}`);
      continue;
    }
    broken.push(`${entry.label} (${entry.container}): `
      + zeroing.map((rule) => `${rule.file}: ${rule.selector}`).join(' + ')
      + ' anula el margen y no hay ninguna regla que lo devuelva');
  }
  assert.deepStrictEqual(broken, [],
    'bloques que se leerían como una masa de texto:\n  ' + broken.join('\n  ')
    + '\n\nauditado:\n  ' + audited.join('\n  '));
});

test('la separación devuelta es suficiente para distinguir dos ideas', () => {
  // 6px es el mínimo de la escala del proyecto: por debajo, dos párrafos se leen
  // como una línea partida y el bloque vuelve a parecer monolítico.
  const MIN_PX = 6;
  const tooTight = [];
  for (const entry of CONTAINERS) {
    const { zeroing, spacing } = auditContainer(entry.container, entry.paragraphClass);
    if (!zeroing.length || !spacing) continue;
    if (spacing.value < MIN_PX) tooTight.push(`${entry.label}: ${spacing.value}px`);
  }
  assert.deepStrictEqual(tooTight, [],
    `hueco por debajo de ${MIN_PX}px: ` + tooTight.join(', '));
});

test('cada hallazgo arreglado sigue teniendo su regla', () => {
  // Guarda nominal, solo para las reglas que SOSTIENEN el arreglo: sin ellas el
  // hueco sería 0 y el bloque volvería a leerse como una masa. (La separación de
  // `.product-review` no está aquí porque el margen del navegador ya la cubriría;
  // esa regla es una decisión de jerarquía, no un rescate.)
  const cases = [
    ['la ayuda de campo en varios párrafos (Privacidad)', 'p.field-help + p.field-help'],
    ['la vista previa de Privacidad', '.privacy-preview > * + *'],
    ['la respuesta del chat', '#chat-feedback > p'],
    ['las condiciones de la ficha en una columna', 'ul.detail-list'],
    ['la revisión de la tarjeta: rótulo separado de su lista', '.product-review-label'],
  ];
  const missing = cases
    .filter(([, needle]) => !RULES.some((rule) => rule.selector.includes(needle)))
    .map(([label]) => label);
  assert.deepStrictEqual(missing, [], 'falta la regla de: ' + missing.join(', '));
});

test('ningún contenedor de lectura usa white-space: pre sobre prosa', () => {
  // Un `pre` convierte cada salto de línea del texto en un salto literal: si el
  // original no traía saltos, sale un bloque sin pausas. Solo se admite donde el
  // texto es, literalmente, una tabla o una marca gráfica.
  const allowed = /\.mono|\.visually-hidden|\.data-table|\.doc-watermark|\.doc-barcode|\.scenario-chart/;
  const offenders = RULES
    .filter((rule) => /^(pre|pre-wrap|pre-line|break-spaces)/.test(rule.decls['white-space'] || ''))
    .filter((rule) => !allowed.test(rule.selector))
    .map((rule) => `${rule.file}: ${rule.selector} { white-space: ${rule.decls['white-space']} }`);
  assert.deepStrictEqual(offenders, [],
    'white-space: pre sobre prosa amontona el texto: ' + offenders.join(' | '));
});

test('la prosa de contenido tiene una medida de línea legible', () => {
  // 45–90 caracteres por línea es el rango legible; por encima de ~90 la vista se
  // cansa antes de terminar la frase. Medido antes del arreglo: 100 en la ficha,
  // 124 en una ayuda de campo, 158 en una nota de escenario. Los títulos quedan
  // fuera: un h1 a 22ch es una decisión tipográfica deliberada, no prosa.
  const prose = RULES.filter((rule) => {
    const value = rule.decls['max-width'];
    if (typeof value !== 'string' || !/^[\d.]+ch$/.test(value)) return false;
    return /(^|[\s,>(])(p|li|dd|figcaption)([\s,:.>)]|$)/.test(rule.selector)
      || /:is\([^)]*\bp\b[^)]*\)/.test(rule.selector);
  });
  assert.ok(prose.length > 0, 'debe haber una medida declarada para la prosa');
  for (const rule of prose) {
    const ch = parseFloat(rule.decls['max-width']);
    assert.ok(ch >= 40 && ch <= 90,
      `medida fuera del rango legible (${rule.decls['max-width']}): ${rule.file}: ${rule.selector}`);
  }
  const rootRules = RULES.filter((rule) => rule.selector.includes(':root'));
  assert.ok(rootRules.some((rule) => /^[\d.]+ch$/.test(rule.decls['--measure'] || '')),
    'debe existir un token --measure para que todas las pantallas usen el mismo valor');
});

test('la rejilla de dos columnas de .detail-list no se aplica a las listas <ul>', () => {
  // Un <ul class="detail-list"> repartía sus <li> de dos en dos y en orden de
  // columna: se leía «TAE / Plazo» en la misma línea y el orden de lectura se
  // rompía. La rejilla solo vale para los pares <dt>/<dd> de un <dl>.
  const ulRule = RULES.find((rule) => /ul\.detail-list/.test(rule.selector)
    && rule.decls['grid-template-columns']);
  assert.ok(ulRule, 'debe existir una regla ul.detail-list que anule la rejilla de dos columnas');
  assert.strictEqual(ulRule.decls['grid-template-columns'], 'minmax(0, 1fr)',
    'ul.detail-list debe ser de una sola columna: ' + ulRule.decls['grid-template-columns']);
});

test('la medida del chat y la del resto de la app son el mismo valor', () => {
  const token = RULES.filter((rule) => rule.selector.includes(':root'))
    .map((rule) => rule.decls['--measure']).find(Boolean);
  const chat = RULES.filter((rule) => rule.selector.includes('#chat-feedback')
    && typeof rule.decls['max-width'] === 'string');
  assert.ok(token, 'falta --measure en :root');
  assert.ok(chat.length > 0, 'el chat debe conservar su propia medida');
  assert.strictEqual(chat[0].decls['max-width'], token,
    `el chat mide ${chat[0].decls['max-width']} y el resto de la app ${token}: deben coincidir`);
});

test('el lector de CSS no se salta reglas después de un @media', () => {
  // Un bug real mientras se escribía este fichero: al abrir un @media de ancho
  // pequeño quedaba un frame en la pila y TODAS las reglas siguientes se saltaban
  // en silencio, así que el test daba por buenos contenedores rotos. Se comprueba
  // con reglas conocidas que viven al final de styles.css y en spacing.css.
  assert.ok(RULES.some((rule) => rule.selector === '.glossary-item dd'),
    'el lector debe llegar a las reglas del final de styles.css');
  assert.ok(RULES.some((rule) => rule.file === 'spacing.css' && rule.selector.includes('p + p')),
    'el lector debe llegar a las reglas de hermanos de spacing.css');
  assert.ok(RULES.length > 400, 'se han leído muy pocas reglas: ' + RULES.length);
});
