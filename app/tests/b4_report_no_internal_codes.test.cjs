// El informe de comparación que el usuario descarga no imprime códigos internos.
//
// Bug real: `conditionLabel` hacía `' · motivo ' + condition.reason` sin traducir,
// así que el PDF que se descarga e imprime decía:
//
//     TAE 2,61 % · vencida · motivo PROMOTION_EXPIRED
//
// Eso se lee como un error del programa, no como una explicación. Y el estado caía
// en `condition.state` crudo para cualquier valor fuera de su tabla de tres.
//
// Este test extrae las dos funciones reales de comparison_report.js y las prueba con
// los seis códigos de motivo que el catálogo emite de verdad.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const MODULO = path.join(__dirname, '..', 'static', 'comparison_report.js');

// Los seis códigos reales de `reason` en el catálogo (medidos con
// ConditionsService().describe() sobre las 22 fichas).
const MOTIVOS_REALES = [
  'CURATED_DOCUMENTED', 'CURATED_OFFICIAL', 'CURATED_SECONDARY_PRESS',
  'CURATED_TERM', 'PROMOTION_EXPIRED', 'RETRIEVAL_TOO_OLD',
];

// Estados que el backend puede emitir.
const ESTADOS = ['known', 'stale', 'conflict', 'unknown', 'not_applicable'];

function setup() {
  const code = fs.readFileSync(MODULO, 'utf8');
  const ctx = { console, Number, Math, Date, Intl };
  vm.createContext(ctx);
  const bloque = (desde, hasta) => {
    const inicio = code.indexOf(desde);
    const fin = code.indexOf(hasta, inicio);
    assert.ok(inicio > 0 && fin > inicio, `bloque no encontrado: ${desde}`);
    return code.slice(inicio, fin);
  };
  // Se evalúan las tablas y las funciones de etiqueta, más `rateText` y
  // `rateDisplay`, que usan para formatear la cifra. El corte va hasta `tierLabel`
  // porque `conditionLabel` está DESPUÉS de `conditionStateLabel`.
  vm.runInContext(bloque('function rateText', 'function tierLabel'), ctx);
  return ctx;
}

test('ningún código de motivo del catálogo se imprime en crudo', () => {
  const ctx = setup();
  const generado = '2026-11-24';
  for (const motivo of MOTIVOS_REALES) {
    const etiqueta = ctx.conditionLabel(
      { state: 'stale', value: '2.61', reason: motivo }, generado);
    // El código en mayúsculas con guiones bajos no puede aparecer en el informe.
    assert.ok(!etiqueta.includes(motivo),
      `el código «${motivo}» se imprime tal cual: ${etiqueta}`);
    assert.ok(!/_/.test(etiqueta), `quedan guiones bajos: ${etiqueta}`);
  }
});

test('el caso reportado: PROMOTION_EXPIRED se lee en castellano', () => {
  const ctx = setup();
  const etiqueta = ctx.conditionLabel(
    { state: 'stale', value: '2.61', reason: 'PROMOTION_EXPIRED' }, '2026-11-24');
  assert.ok(!etiqueta.includes('PROMOTION_EXPIRED'), etiqueta);
  assert.ok(!etiqueta.includes('motivo '), `sobra la palabra «motivo»: ${etiqueta}`);
  assert.match(etiqueta, /caducad|vencid|promoci/i);
});

test('un motivo sin traducir no se publica en crudo', () => {
  const ctx = setup();
  const etiqueta = ctx.conditionLabel(
    { state: 'known', value: '3.1', reason: 'CODIGO_INVENTADO_DEL_FUTURO' }, '2026-11-24');
  assert.ok(!etiqueta.includes('CODIGO_INVENTADO_DEL_FUTURO'), etiqueta);
  assert.match(etiqueta, /no clasificado/i);
});

test('ningún estado se imprime en crudo', () => {
  const ctx = setup();
  for (const estado of ESTADOS) {
    const texto = ctx.conditionStateLabel({ state: estado }, '2026-11-24');
    assert.notStrictEqual(texto, estado, `«${estado}» se devuelve en crudo`);
    assert.ok(!/_/.test(texto), texto);
  }
});

test('CURATED_DOCUMENTED, que es el 96 % del catálogo, no ensucia la etiqueta', () => {
  const ctx = setup();
  const etiqueta = ctx.conditionLabel(
    { state: 'known', value: '2.5', reason: 'CURATED_DOCUMENTED' }, '2026-11-24');
  // No debe añadir un motivo vacío ni un separador colgando.
  assert.ok(!/·\s*$/.test(etiqueta), `separador colgando: ${etiqueta}`);
  assert.ok(!etiqueta.includes('motivo'), etiqueta);
  assert.match(etiqueta, /TAE/);
});

test('una condición vencida por fecha se declara vencida, no solo «stale»', () => {
  const ctx = setup();
  const texto = ctx.conditionStateLabel(
    { state: 'known', effective_to: '2026-01-01' }, '2026-11-24');
  assert.match(texto, /vigencia terminada/i);
});
