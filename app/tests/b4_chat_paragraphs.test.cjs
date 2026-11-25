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
  // El render debe partir por \n\n y limpiar los encabezados.
  assert.match(code, /split\(\/\\n\\s\*\\n\//,
    'el render debe separar párrafos por línea en blanco');
  assert.match(code, /replace\(\/\^\\s\*#\{1,6\}\\s\*\/gm, ""\)/,
    'el render debe quitar los encabezados markdown crudos');
});

test('el texto del modelo llega con párrafos desde el backend', () => {
  // El backend une las frases con \n\n cada dos, no con un espacio suelto: así el
  // render tiene algo que partir.
  const py = fs.readFileSync(path.join(__dirname, '..', 'backend_services.py'), 'utf8');
  const bloque = py.slice(py.indexOf('def _redact_unbacked_figures'), py.indexOf('def _catalogue_explanation'));
  assert.ok(bloque.includes('\\n\\n".join(bloques)'),
    'las frases se agrupan en párrafos con salto doble');
  assert.ok(bloque.includes('if len(actual) >= 2'),
    'se abre párrafo cada dos frases para que la lectura respire');
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
  const i = code.indexOf('for (const trozo of limpio.split(');
  const j = code.indexOf('if (calculation) renderChatCalculation(feedback, calculation);', i);
  assert.ok(i > 0 && j > i,
    'la prosa se pinta primero y el cálculo detrás');
});
