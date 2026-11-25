// La respuesta del chat no puede leerse como una tabla.
//
// Lección medida EN PANTALLA (navegador real, no API): durante varias iteraciones di
// por bueno el turno porque la API devolvía texto correcto, mientras en la interfaz
// se veía esto:
//
//     Resultado del motor determinista local (escenario hipotético):
//     Supuestos: principal 2.000,00 EUR; aportación mensual 0,00 EUR; plazo 1 año...
//     Aportaciones: 2.000,00 EUR
//     Saldo final: 2.040,00 EUR
//     Interés: 40,00 EUR
//     Saldo ajustado por inflación: 1.990,24 EUR
//
// Cinco líneas de tabla. Y antes del cálculo, el texto del modelo llegaba mutilado
// (13 frases borradas) dejando encabezados huérfanos: «Qué descarto y por qué.»,
// «Qué sí encaja, por categoría.». Eso es lo que se lee como tabla rota.
//
// Este test monta el render REAL del cálculo y exige prosa, no volcado.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

function setup() {
  const code = fs.readFileSync(APP, 'utf8');
  const ctx = { console, Number, String, Math, Intl, Date };
  vm.createContext(ctx);
  const bloque = (desde, hasta) => {
    const inicio = code.indexOf(desde);
    const fin = code.indexOf(hasta, inicio);
    assert.ok(inicio > 0 && fin > inicio, `bloque no encontrado: ${desde}`);
    return code.slice(inicio, fin);
  };
  // Un solo bloque continuo: chatDecimal, chatMoney, chatText y las constantes del
  // cálculo viven todas dentro de la sección del chat, una detrás de otra.
  vm.runInContext(bloque('function chatDecimal', 'function renderChatCatalogue'), ctx);
  // DOM mínimo: solo hace falta que appendChild acumule y textContent sume.
  ctx.el = (tag, attrs, children) => {
    const node = { tag, className: (attrs && attrs.className) || '', children: [], text: '' };
    node.appendChild = (c) => { node.children.push(c); return c; };
    if (typeof children === 'string') node.text = children;
    Object.defineProperty(node, 'textContent', {
      get() { return node.text + node.children.map((c) => c.textContent).join(''); },
    });
    return node;
  };
  ctx.textElement = (tag, text, className) => ctx.el(tag, { className }, String(text));
  ctx.document = { createTextNode: (t) => ({ textContent: t, children: [] }) };
  return ctx;
}

// El DTO real que se midió en pantalla. Los importes llegan en formato MÁQUINA
// («2000.00»), no formateados: los formatea el render.
const CALCULO = {
  hypothetical: true,
  not_prediction: true,
  currency: 'EUR',
  summary: {
    contributions: '2000.00', final_balance: '2040.00',
    interest: '40.00', inflation_adjusted: '2000.00',
  },
  assumptions: {
    principal: '2000', monthly_contribution: '0',
    annual_rate_percent: '2', inflation_percent: '2', years: 1, method: 'simple',
    taxes_included: false, fees_included: false,
  },
};

test('el cálculo se pinta como frase, no como cinco líneas de tabla', () => {
  const ctx = setup();
  const contenedor = ctx.el('div', {});
  ctx.renderChatCalculation(contenedor, CALCULO);
  const texto = contenedor.textContent;

  // Prosa: la cifra y su significado en una frase.
  assert.match(texto, /Si dejas 2\.000,00 € al 2,00 % durante un año/,
    `no se lee como prosa: ${texto}`);
  assert.match(texto, /acabas con 2\.040,00 €/, texto);
  assert.match(texto, /40,00 € de intereses/, texto);

  // Y NO el volcado línea a línea que se veía en pantalla.
  for (const etiqueta of ['Supuestos: principal', 'Aportaciones: 2.000,00 EUR',
    'Saldo final: 2.040,00 EUR', 'Interés: 40,00 EUR',
    'Saldo ajustado por inflación:']) {
    assert.ok(!texto.includes(etiqueta), `sigue el volcado «${etiqueta}»: ${texto}`);
  }
});

test('avisa de que el tipo es un supuesto, no el de un producto', () => {
  const ctx = setup();
  const contenedor = ctx.el('div', {});
  ctx.renderChatCalculation(contenedor, CALCULO);
  const texto = contenedor.textContent;
  // El usuario nunca dijo «2 %»: lo eligió el modelo para el ejemplo. Presentarlo
  // como un dato del producto sería inventar.
  assert.match(texto, /supuesto/i, texto);
  assert.match(texto, /no el de un producto concreto/i, texto);
});

test('la inflación se explica comparando con lo aportado, no con el saldo final', () => {
  const ctx = setup();
  const contenedor = ctx.el('div', {});
  // Caso real: el saldo real (2.000) es MENOR que lo aportado, así que el interés
  // no cubre la inflación. Antes se comparaba con el saldo final y la frase decía
  // «pierdes 40 €» dando el mismo número que el inicial, sin explicar nada.
  ctx.renderChatCalculation(contenedor, CALCULO);
  const texto = contenedor.textContent;
  assert.match(texto, /inflación/i, texto);
  assert.match(texto, /menos de los 2\.000,00 € que pusiste|te quedas igual/i, texto);
});

test('sin inflación que cambie la conclusión, no se añade ruido', () => {
  const ctx = setup();
  const contenedor = ctx.el('div', {});
  ctx.renderChatCalculation(contenedor, {
    hypothetical: true, not_prediction: true, currency: 'EUR',
    summary: { contributions: '2000.00', final_balance: '2120.00',
      interest: '120.00', inflation_adjusted: '2100.00' },
    assumptions: { principal: '2000', monthly_contribution: '0',
      annual_rate_percent: '6', inflation_percent: '1', years: 1, method: 'simple',
      taxes_included: false, fees_included: false },
  });
  const texto = contenedor.textContent;
  // Gana en términos reales: se dice, pero con la cifra real, no con la nominal.
  assert.match(texto, /ganas \d+,\d\d € en términos reales/, texto);
  assert.match(texto, /no los 120,00 € que parece/, texto);
});

test('un cálculo mal formado no pinta cifras inventadas', () => {
  const ctx = setup();
  const contenedor = ctx.el('div', {});
  ctx.renderChatCalculation(contenedor, { summary: null, assumptions: null });
  const texto = contenedor.textContent;
  assert.ok(!/\d{2,}/.test(texto), `no debe haber cifras: ${texto}`);
  assert.match(texto, /no llegó con una forma válida|no se muestran/i, texto);
});
