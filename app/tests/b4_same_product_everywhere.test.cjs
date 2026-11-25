// La pantalla y el texto tienen que hablar del MISMO producto.
//
// P0 medido en producción: a «¿qué TAE tiene el depósito de EBN Banco?» el JSON de
// /api/chat devolvía **3,10 % (Depósito Nuevo Ahorro 12 meses, EBN Banco)** en el
// texto compuesto, y la pantalla enseñaba **2,4 % (Sinycon)**. Dos superficies del
// mismo turno daban productos distintos y ninguno de los dos era lo que se veía.
//
// Causa: la tarjeta del catálogo tomaba `products[0]`, el primero del array, mientras
// el texto lo componía `compose_catalogue_answer`, que elige con `_pick_best` según
// la pregunta. Nadie transmitía cuál se había elegido.
//
// Este test fija el contrato: si el servidor manda `recommended_product_id`, la
// tarjeta enseña ESE producto y no el primero.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const APP = path.join(__dirname, '..', 'static', 'app.js');
const BACK = path.join(__dirname, '..', 'backend_services.py');
const RECO = path.join(__dirname, '..', 'catalogue_recommendation.py');

test('la tarjeta respeta el producto que recomienda el servidor', () => {
  const code = fs.readFileSync(APP, 'utf8');
  // Debe leer el id recomendado y buscar ESE, no tomar el primero.
  assert.match(code, /recommendedProductId/,
    'la tarjeta debe recibir el id recomendado');
  assert.match(code, /validos\.find\(p => p\.id === pedido\)/,
    'debe buscar el producto por id, no tomar el primero del array');
  // Y `products[0]` solo puede quedar como respaldo, nunca como criterio.
  const bloque = code.slice(code.indexOf('const pedido ='),
                            code.indexOf('const condiciones = Array.isArray(principal.conditions)'));
  assert.ok(bloque.includes('|| validos[0]'),
    'el primero del array queda solo como respaldo si no llega el id');
});

test('el backend publica el id recomendado en el DTO', () => {
  const py = fs.readFileSync(BACK, 'utf8');
  assert.ok(py.includes('"recommended_product_id": recommended_product_id('),
    'el DTO debe llevar recommended_product_id');
  // Y la marca de que el texto lo compuso la app (si no, el frontend no lo pinta).
  assert.ok(py.includes('"answer_origin": result.get("answer_origin")'),
    'el DTO debe llevar answer_origin, no solo el dict interno');
});

test('la recomendación por producto nombrado no cae en el de mayor tasa', () => {
  const py = fs.readFileSync(RECO, 'utf8');
  // Si la pregunta nombra un producto concreto, se devuelve ese.
  assert.ok(py.includes('if len(validos) == 1:'),
    'con un solo producto nombrado, la recomendación es ese');
  // Y se aplica el mismo orden de filtros que la composición del texto.
  for (const filtro of ['_mentions_issuer', '_is_current', '_minimum_eur', '_pick_best']) {
    assert.ok(py.includes(filtro), `debe reutilizar ${filtro} del catálogo`);
  }
});

test('el filtro por emisor usa el campo real del DTO', () => {
  const ans = fs.readFileSync(path.join(__dirname, '..', 'catalogue_answer.py'), 'utf8');
  // El emisor viaja en `provider`; con solo `issuer` nunca coincidía.
  assert.ok(ans.includes('product.get("provider") or product.get("issuer")'),
    'el emisor se lee de provider (el campo real), no solo de issuer');
});

test('una pregunta de listado no pide el importe antes de listar', () => {
  const ans = fs.readFileSync(path.join(__dirname, '..', 'catalogue_answer.py'), 'utf8');
  const inicio = ans.indexOf('def _question_intent');
  const bloque = ans.slice(inicio, inicio + 3000);
  // «¿Qué depósitos hay?» — el plural entre «qué» y el verbo.
  assert.ok(bloque.includes('hay|tienes'),
    'debe reconocer «qué <plural> hay/tienes» como listado');
  // Pero «¿qué TAE tiene el depósito?» NO es listado: una métrica no es familia.
  assert.ok(bloque.includes('tae|tin|tasa'),
    'una pregunta por una métrica no puede tratarse como listado');
});

