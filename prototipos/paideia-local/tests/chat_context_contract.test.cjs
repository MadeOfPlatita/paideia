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
  assert.match(chat, /state\.status\?\.ai\?\.capabilities/);
  assert.match(chat, /no disponible/i);
  assert.match(chat, /mapa/i);
});
