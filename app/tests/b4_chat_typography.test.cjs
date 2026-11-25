// La tipografía del chat de Paideia: la respuesta es texto para LEER, no un muro.
//
// Lección medida EN PANTALLA: la respuesta salía como un bloque monolítico de ~20
// líneas sin un solo salto de párrafo. La causa era que no existía NINGUNA regla
// para los <p> de #chat-feedback, así que se pegaban unos a otros.
//
// Este test fija el contrato tipográfico mínimo y está pensado para ponerse ROJO si
// alguien borra o anula la separación entre párrafos:
//   - interlineado 1.5–1.6 (USWDS y WCAG 1.4.12 piden ≥1.5 para cuerpo de texto).
//   - medida de línea acotada (USWDS: 45–90 caracteres, objetivo 66). Sin límite el
//     panel da ~110 caracteres por línea.
//   - margen entre párrafos distinto de 0 y en la banda 0.75em–1em.
//   - primer párrafo sin aire arriba y último sin aire abajo.
//   - listas con sangría y margen entre items.
//   - los colores salen de variables del tema (nada de #hex ni rgb() fijos), para
//     que el tema oscuro no se rompa.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const STYLES = path.join(__dirname, '..', 'static', 'styles.css');
const DARK = path.join(__dirname, '..', 'static', 'dark_theme.css');

// Los comentarios del CSS contienen selectores y nombres de propiedad (explican el
// porqué de cada valor); si no se quitan, el analizador los mete dentro del selector
// y no encuentra ninguna regla.
function sinComentarios(fuente) {
  return fuente.replace(/\/\*[\s\S]*?\*\//g, '');
}

function css() {
  return sinComentarios(fs.readFileSync(STYLES, 'utf8'));
}

// Devuelve el cuerpo de la primera regla cuyo selector sea exactamente `selector`
// (comparando selectores normalizados, sin espacios de más).
function bloque(fuente, selector) {
  const normaliza = (s) => s.replace(/\s+/g, ' ').trim();
  const buscado = normaliza(selector);
  const regex = /([^{}]+)\{([^}]*)\}/g;
  let m;
  while ((m = regex.exec(fuente)) !== null) {
    if (normaliza(m[1]) === buscado) return m[2];
  }
  return null;
}

// Igual que `bloque`, pero acepta que el selector sea una lista y devuelve la
// primera regla que CONTENGA el selector buscado como alternativa exacta.
function bloqueQueContiene(fuente, selector) {
  const normaliza = (s) => s.replace(/\s+/g, ' ').trim();
  const buscado = normaliza(selector);
  const regex = /([^{}]+)\{([^}]*)\}/g;
  let m;
  while ((m = regex.exec(fuente)) !== null) {
    const selectores = m[1].split(',').map(normaliza);
    if (selectores.includes(buscado)) return m[2];
  }
  return null;
}

function valor(cuerpo, propiedad) {
  const m = new RegExp(`(?:^|;)\\s*${propiedad}\\s*:\\s*([^;]+)`, 'i').exec(cuerpo || '');
  return m ? m[1].trim() : null;
}

// Regresión principal: si esta regla desaparece o su margen vuelve a 0, el muro
// de texto vuelve y el usuario lo describe como «muy apretada».
test('la respuesta separa sus párrafos con un margen real, no con 0', () => {
  const fuente = css();
  const cuerpo = bloqueQueContiene(fuente, '#chat-feedback > p');
  assert.ok(cuerpo, 'falta la regla `#chat-feedback > p`: los párrafos se pegarían');

  const margen = valor(cuerpo, 'margin');
  assert.ok(margen, 'la regla de los párrafos debe declarar `margin`');

  // `margin: 0 0 0.85em` -> taquigrafía de 3 valores: superior, laterales, INFERIOR.
  const taquigrafia = margen.split(/\s+/);
  const inferior = taquigrafia.length === 1
    ? taquigrafia[0]
    : (taquigrafia.length === 2 ? taquigrafia[0] : taquigrafia[2]);
  assert.notStrictEqual(inferior, '0', 'el margen inferior entre párrafos no puede ser 0');
  assert.notStrictEqual(inferior, '0px', 'el margen inferior entre párrafos no puede ser 0px');

  // Banda pedida: 0.75em–1em entre párrafos de un mismo bloque.
  const em = /^([\d.]+)em$/.exec(inferior);
  assert.ok(em, `el margen entre párrafos debe ir en em (crece al agrandar el texto, WCAG 1.4.4); es «${inferior}»`);
  const n = Number(em[1]);
  assert.ok(n >= 0.75 && n <= 1,
    `el margen entre párrafos debe estar entre 0.75em y 1em; es ${n}em`);
});

test('el interlineado del chat está en la banda 1.5–1.6', () => {
  const cuerpo = bloque(css(), '#chat-feedback');
  assert.ok(cuerpo, 'falta la regla `#chat-feedback`');

  const lh = valor(cuerpo, 'line-height');
  assert.ok(lh, 'debe declararse `line-height` para el chat');
  const n = Number(lh);
  assert.ok(Number.isFinite(n), `line-height debe ser un número sin unidad; es «${lh}»`);
  assert.ok(n >= 1.5 && n <= 1.6,
    `line-height debe estar entre 1.5 y 1.6 (USWDS cuerpo de texto); es ${n}`);
});

test('la medida de línea está acotada: el texto no llega a 150 caracteres', () => {
  const fuente = css();
  // El tope puede estar en la regla de los párrafos o en la del contenedor.
  const candidatos = [bloqueQueContiene(fuente, '#chat-feedback > p'), bloque(fuente, '#chat-feedback')]
    .filter(Boolean);
  const topes = candidatos.map(c => valor(c, 'max-width')).filter(Boolean)
    .map(v => /^([\d.]+)ch$/.exec(v))
    .filter(Boolean)
    .map(m => Number(m[1]));

  assert.ok(topes.length, 'debe acotarse el ancho de la respuesta en `ch` (medida de línea)');
  const tope = Math.min(...topes);
  assert.ok(tope <= 90,
    `la medida no debe pasar de 90 caracteres (USWDS); es ${tope}ch`);
  assert.ok(tope >= 45,
    `la medida no debe quedarse por debajo de 45 caracteres (USWDS); es ${tope}ch`);
});

test('el primer párrafo no lleva aire arriba y el último no lo lleva abajo', () => {
  const fuente = css();
  const primero = bloque(fuente, '#chat-feedback > p:first-of-type');
  assert.ok(primero, 'falta `#chat-feedback > p:first-of-type`');
  assert.strictEqual(valor(primero, 'margin-top'), '0',
    'el primer párrafo no debe tener margen superior');

  // El último se marca con :last-child, no con :last-of-type: medido en navegador,
  // `:last-of-type` quitaba el margen a un párrafo SEGUIDO de una lista y la lista
  // se le echaba encima.
  const ultimo = bloque(fuente, '#chat-feedback > p:last-child');
  assert.ok(ultimo, 'falta `#chat-feedback > p:last-child` (evita el hueco inferior)');
  assert.strictEqual(valor(ultimo, 'margin-bottom'), '0',
    'el último párrafo no debe dejar hueco debajo');
  assert.strictEqual(bloque(fuente, '#chat-feedback > p:last-of-type'), null,
    ':last-of-type vuelve a colar el solape con las listas: usa :last-child');
});

test('las listas del chat tienen sangría y margen entre items', () => {
  const fuente = css();
  // Las reglas de lista excluyen las que el render pinta con clase propia; se busca
  // cualquier regla cuyo selector empiece por #chat-feedback y nombre ol/ul.
  const reglas = [];
  const regex = /([^{}]+)\{([^}]*)\}/g;
  let m;
  while ((m = regex.exec(fuente)) !== null) {
    const selector = m[1];
    if (!selector.includes('#chat-feedback')) continue;
    if (!/\b(ol|ul)\b/.test(selector)) continue;
    if (!/padding-left/.test(m[2])) continue;          // solo las que dan sangría
    reglas.push(m[2]);
  }
  assert.ok(reglas.length, 'no hay ninguna regla para las listas dentro de #chat-feedback');

  const conSangria = reglas.some(c => {
    const p = valor(c, 'padding-left');
    return p && /^[\d.]+(em|rem|px)$/.test(p) && parseFloat(p) > 0;
  });
  assert.ok(conSangria, 'las listas deben tener sangría (padding-left > 0)');

  const conMargenItem = reglas.some(c => {
    const mg = valor(c, 'margin');
    return mg && /0\s+0\s+[\d.]+(em|rem|px)/.test(mg.replace(/\s+/g, ' '));
  });
  assert.ok(conMargenItem, 'debe haber margen entre items de lista');
});

test('los colores del chat salen de variables del tema, no de valores fijos', () => {
  const fuente = css();
  // Todo el bloque del chat, desde su comentario de cabecera hasta `.field`.
  const inicio = fuente.indexOf('#chat-feedback');
  const fin = fuente.indexOf('\n.field {', inicio);
  assert.ok(inicio > 0 && fin > inicio, 'no se localiza el bloque de reglas del chat');
  const bloqueChat = fuente.slice(inicio, fin);

  // Ningún color literal: ni #hex, ni rgb()/hsl().
  const hex = bloqueChat.match(/#[0-9a-fA-F]{3,8}\b/g);
  assert.strictEqual(hex, null, `hay colores fijos en el chat: ${hex && hex.join(', ')}`);
  const funciones = bloqueChat.match(/\b(rgb|rgba|hsl|hsla)\(/g);
  assert.strictEqual(funciones, null, `hay colores fijos en el chat: ${funciones && funciones.join(', ')}`);

  // Y los que se declaran usan var(--...).
  for (const decl of bloqueChat.match(/(?:^|;)\s*color\s*:\s*([^;]+)/g) || []) {
    assert.match(decl, /var\(--/,
      `un color del chat no usa variable del tema: «${decl.trim()}»`);
  }
});

test('el tema oscuro no duplica ni pisa las reglas del chat', () => {
  const oscuro = fs.readFileSync(DARK, 'utf8');
  assert.ok(!oscuro.includes('#chat-feedback'),
    'dark_theme.css no debe redefinir #chat-feedback: los colores ya llegan por variables');
  // Y las variables que usa el chat existen en el tema oscuro, así que hereda bien.
  for (const variable of ['--ink', '--muted']) {
    assert.ok(oscuro.includes(`${variable}:`),
      `falta ${variable} en dark_theme.css: el chat se quedaría sin ese color`);
  }
});
