'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
test('chat surfaces capabilities from the existing status response', () => {
  const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
  const start = source.indexOf('  const chat = section("Pregunta a Pai"');
  const chat = source.slice(start, source.indexOf('  if (state.storageNotice)', start));
  assert.ok(start > 0);
  // El bloque del chat pinta el aviso de capacidades leyendo /api/status.
  assert.match(chat, /state\.status\?\.ai\?\.capabilities/);
  assert.match(chat, /chatCapabilitiesText/);
  // Y el texto de las capacidades, que vive en su propia función, dice qué se
  // puede hacer y qué no, sin prometer lo que el servicio no ofrece.
  const texto = source.slice(source.indexOf('function chatCapabilitiesText'),
                             source.indexOf('function chatHistoryConsentText'));
  assert.match(texto, /Mapa/);
  assert.match(texto, /catálogo/);
  assert.match(texto, /no disponible/i);
});
