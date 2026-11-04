'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

test('B5 ensayo usa hechos documentados y no los confunde con oferta vigente', () => {
  const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
  assert.match(source, /function simulationConditionsLabel/);
  assert.match(source, /Hechos documentados/);
  assert.match(source, /vencidos, en conflicto o sin dato/);
  assert.match(source, /no se presentan como oferta vigente/);
  assert.match(source, /state\.conditions\.byId\.get\(product\.id\)/);
  assert.match(source, /Los hechos documentados pueden estar vencidos/);
});

test('B5 no declara ausentes las condiciones cuando la fuente llega resuelta', () => {
  const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
  // Las condiciones del snapshot no traen `entry.source`: su fuente llega en
  // `source_refs`/`source_ids`. Mirar solo `entry.source` mostraba «Condiciones no
  // documentadas» con una tasa documentada delante.
  assert.match(source, /function conditionSourceRef/);
  assert.match(source, /condition\.source_refs/);
  assert.match(source, /const ref = conditionSourceRef\(entry\)/);
  assert.match(source, /const conditionRef = conditionSourceRef\(conditionEntry\)/);
});

test('B5 mantiene cierre explícito de que no se envió nada', () => {
  const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
  assert.match(source, /No se ha enviado una solicitud, abierto una cuenta ni movido dinero/);
  assert.match(source, /Esto no es un contrato ni una confirmación de operación/);
});
