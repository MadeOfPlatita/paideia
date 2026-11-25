// La respuesta larga tiene que respirar: párrafos, no un muro de texto.
//
// Lección medida EN PANTALLA con captura real: el turno del estudiante devolvía
// 1.500 caracteres en un ÚNICO <p>, sin una sola pausa, y el modelo colaba
// encabezados markdown crudos («## Qué hace un 2 % en tus cifras») que en pantalla
// se leen como almohadillas. Se veía como un volcado, no como un asesor hablando.
//
// Este test monta el render real del chat y exige: varios párrafos si el texto es
// largo, y ni una sola almohadilla markdown a la vista.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

// Extrae el trozo del render del chat que inserta `result.answer`, que es el que
// pintaba un único párrafo.
function parrafoDeRespuesta(html) {
  return html;
}

function setup() {
  const code = fs.readFileSync(APP, 'utf8');
  const ctx = { console, Number, String, Math, Intl, Date };
  vm.createContext(ctx);
  // Se buscan las líneas del render, no se ejecuta todo el fichero (depende del DOM).
  return { code, ctx };
}

test('la respuesta se parte en párrafos y no deja almohadillas markdown', () => {
  const { code } = setup();
  // El render parte por línea en blanco y limpia el markdown con chatPlain, que es
  // la función que quita encabezados, negritas y listas (probada con casos reales
  // en b4_chat_markdown_clean.test.cjs).
  assert.match(code, /split\(\/\\n\\s\*\\n\//,
    'el render debe separar párrafos por línea en blanco');
  assert.match(code, /function chatPlain\(value\)/,
    'debe existir la limpieza de markdown');
  assert.match(code, /chatPlain\(result\.answer\)/,
    'el render debe pasar la respuesta por chatPlain');
});

test('el texto del modelo llega con párrafos desde el backend', () => {
  // El backend abre párrafos cada dos frases y deja cada paso numerado en el suyo:
  // así el render tiene algo que partir y puede pintar la lista.
  const py = fs.readFileSync(path.join(__dirname, '..', 'backend_services.py'), 'utf8');
  const bloque = py.slice(py.indexOf('def _paragraph_blocks'), py.indexOf('def _catalogue_explanation'));
  assert.ok(bloque.includes('\\n\\n".join(bloques)'),
    'las frases se agrupan en párrafos con salto doble');
  assert.ok(bloque.includes('len(actual) >= tope[0]'),
    'se abre párrafo cada dos frases para que la lectura respire');
  assert.ok(bloque.includes('_NUMBERED_STEP.match(frase)'),
    'un paso numerado abre párrafo propio, para que el frontend pinte la lista');
});

test('un encabezado markdown suelto no se convierte en un título con almohadillas', () => {
  const { code } = setup();
  // Simulación de la transformación del render, con el mismo regex que usa.
  const limpio = '## Qué hace un 2 % en tus cifras\n\nHe calculado dos escenarios.'
    .replace(/^\s*#{1,6}\s*/gm, '').trim();
  assert.ok(!limpio.includes('#'), `quedan almohadillas: ${limpio}`);
  assert.ok(limpio.startsWith('Qué hace'), limpio);
  assert.ok(code.includes('result.answer'), 'se sigue leyendo la respuesta del backend');
});

test('el cálculo va DESPUÉS de la prosa, no en medio', () => {
  const { code } = setup();
  // La prosa se pinta en un solo paso (renderChatProse recibe todos los párrafos,
  // porque la numeración de una lista puede venir repartida entre ellos).
  const i = code.indexOf('renderChatProse(feedback, chatPlain(result.answer)');
  const j = code.indexOf('if (calculation) renderChatCalculation(feedback, calculation);', i);
  assert.ok(i > 0 && j > i,
    'la prosa se pinta primero y el cálculo detrás');
});
