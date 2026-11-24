"use strict";
// renderHome no puede abortarse: si lo hace, la app se queda SIN CHAT.
//
// Bug real, introducido y detectado la misma noche: `chatHistoryConsentText()`
// usaba `chatCapabilities`, que es una constante LOCAL de renderHome y no una
// global. Al llamarla desde dentro lanzaba `ReferenceError: chatCapabilities is
// not defined`, renderHome se abortaba a mitad y el panel del chat NUNCA se
// montaba.
//
// Lo grave no fue el error, sino que pasaba en silencio: la página cargaba, la
// biblioteca y el glosario funcionaban, y no había ningún mensaje de error. La
// app parecía correcta pero no se podía hablar con Pai.
//
// Las 128 pruebas de Node no lo detectaron porque ninguna ejecuta renderHome
// completa. Esta sí.

const test = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const path = require("node:path");

const SONDA = path.join(__dirname, "_render_home_probe.js");
const APP = path.join(__dirname, "..", "static", "app.js");

const CAPACIDADES = {
  ai: {
    status: "configured_not_verified",
    capabilities: { context: true, history: true, catalogue: true, structured_education: false },
  },
};

const SIN_HISTORIAL = {
  ai: {
    status: "configured_not_verified",
    capabilities: { context: true, history: false, catalogue: true, structured_education: false },
  },
};

function renderHome(status) {
  const salida = execFileSync(process.execPath, [SONDA, APP, JSON.stringify(status)], {
    encoding: "utf8",
    timeout: 60_000,
  });
  return JSON.parse(salida);
}

test("renderHome termina sin lanzar y monta el chat completo", () => {
  const salida = renderHome(CAPACIDADES);

  assert.equal(salida.error, null,
    `renderHome lanzó "${salida.error}": la app se queda sin chat`);

  // El chat entero: panel, cuadro de texto, botón, casillas y aviso.
  for (const id of ["chat-panel", "chat-message", "chat-submit", "chat-feedback",
                    "chat-history-consent", "chat-context-consent", "chat-consent"]) {
    assert.ok(salida.ids.includes(id), `no se montó #${id}; ids: ${salida.ids.join(", ")}`);
  }
});

test("renderHome monta el chat también con history desactivado", () => {
  // Producción publicaba history:false hasta anoche. Ese camino no puede romperse.
  const salida = renderHome(SIN_HISTORIAL);

  assert.equal(salida.error, null,
    `con history:false renderHome lanzó "${salida.error}"`);
  assert.ok(salida.ids.includes("chat-message"), "el chat debe existir igualmente");
  assert.ok(salida.ids.includes("chat-history-consent"), "la casilla debe existir (deshabilitada)");
});

test("renderHome funciona sin estado de IA (servicio caído)", () => {
  // Si /api/status no contesta, la app debe seguir mostrando el chat en modo aviso.
  const salida = renderHome({});

  assert.equal(salida.error, null,
    `sin status renderHome lanzó "${salida.error}": la app quedaría inservible`);
  assert.ok(salida.ids.includes("chat-message"), "el chat debe montarse aunque no haya estado");
});

test("el aviso del historial dice la verdad en los dos casos", () => {
  // El texto de la casilla depende de la capacidad, que solo se conoce al llegar
  // /api/status. Antes se quedaba con «no disponible» mientras la casilla sí
  // aparecía habilitada: dos mensajes opuestos en el mismo control.
  const salida = renderHome(CAPACIDADES);
  const avisos = salida.aviso_historial;

  assert.ok(avisos, "el sondeo debe devolver el texto del aviso");
  // Con historial: habla de reenviar turnos y no de que no esté disponible.
  assert.match(avisos.con, /reenviar/i,
    `con history:true el aviso debe hablar de reenviar: "${avisos.con}"`);
  assert.doesNotMatch(avisos.con, /no disponible/i,
    `con history:true no puede decir «no disponible»: "${avisos.con}"`);
  // Sin historial: lo dice con claridad y no promete nada.
  assert.match(avisos.sin, /no disponible/i,
    `con history:false debe decirlo: "${avisos.sin}"`);
  assert.doesNotMatch(avisos.sin, /Autorizo reenviar/i,
    `con history:false no puede prometer reenvío: "${avisos.sin}"`);
});
