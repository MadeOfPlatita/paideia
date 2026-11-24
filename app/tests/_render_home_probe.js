"use strict";
// Ejecuta renderHome de la app real sobre un DOM mínimo y dice qué se montó.
//
// Sirve para detectar el fallo más caro posible: que renderHome se aborte y la app
// se quede SIN CHAT sin mostrar ningún error. Ocurrió una vez (una función usaba
// una constante local que no estaba en su ámbito) y ninguna prueba lo vio, porque
// ninguna ejecutaba renderHome completa.
//
// En vez de arrancar la app entera (startApp busca medio HTML), se evalúa app.js en
// un contexto con un DOM mínimo y se llama a renderHome directamente.
//
// Uso: node _render_home_probe.js <ruta/app.js> <status JSON>

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const appPath = process.argv[2];
const status = JSON.parse(process.argv[3]);

class Node {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.attributes = {};
    this.listeners = {};
    this.textContent = "";
    this.className = "";
    this.value = "";
    this.checked = false;
    this.disabled = false;
    this.id = "";
    this.style = {};
    this.hidden = false;
  }
  setAttribute(k, v) { this.attributes[k] = v; if (k === "id") this.id = v; }
  getAttribute(k) { return this.attributes[k]; }
  removeAttribute(k) { delete this.attributes[k]; }
  hasAttribute(k) { return k in this.attributes; }
  appendChild(n) { this.children.push(n); return n; }
  append(...n) { this.children.push(...n); }
  insertBefore(n) { this.children.push(n); return n; }
  replaceChildren(...n) { this.children = n; }
  remove() {}
  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true; }
  querySelector(sel) {
    // El render real busca descendientes por clase; basta con devolver un nodo
    // cuando el selector es de clase, para que no reviente por un `null`.
    if (String(sel).startsWith(".")) return new Node("div");
    return null;
  }
  querySelectorAll() { return []; }
  closest() { return null; }
  focus() {}
  blur() {}
  scrollIntoView() {}
  click() {}
  setSelectionRange() {}
  getBoundingClientRect() { return { height: 10, width: 10, top: 0, left: 0 }; }
  get classList() { return { add() {}, remove() {}, toggle() {}, contains() { return false; } }; }
  get dataset() { return {}; }
  get options() { return []; }
  get firstChild() { return this.children[0] || null; }
}

// El HTML mínimo que consume renderHome: cabecera de estado y panel lateral.
const byId = {};
function crear(id, tag) {
  const nodo = new Node(tag);
  nodo.id = id;
  byId[id] = nodo;
  return nodo;
}

const body = new Node("body");
for (const [id, tag] of [["status-retry", "button"], ["clear-profile", "button"],
                         ["main-content", "main"], ["skip-link", "a"],
                         ["context-panel", "aside"], ["app-main", "main"]]) {
  body.appendChild(crear(id, tag));
}

const doc = {
  title: "",
  body,
  documentElement: new Node("html"),
  createElement: (t) => new Node(t),
  createElementNS: (_ns, t) => new Node(t),
  createTextNode: (t) => { const n = new Node("#text"); n.textContent = t; return n; },
  getElementById: (id) => byId[id] || null,
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener() {},
  removeEventListener() {},
  createEvent: () => ({ initEvent() {}, preventDefault() {} }),
  activeElement: null,
  readyState: "loading",
};

const sandbox = {
  console, JSON, Math, Date, Array, Object, String, Number, Boolean, RegExp, Error, TypeError,
  Promise, Map, Set, WeakMap, WeakSet, Symbol, Intl, isNaN, isFinite, parseInt, parseFloat,
  setTimeout: (f) => { try { f(); } catch (_) {} return 0; },
  clearTimeout() {}, setInterval() { return 0; }, clearInterval() {},
  queueMicrotask: (f) => { try { f(); } catch (_) {} },
  fetch: () => new Promise(() => {}),
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  location: { hash: "#inicio", pathname: "/", search: "", reload() {}, assign() {} },
  navigator: { language: "es-ES", userAgent: "node" },
  document: doc,
  matchMedia: () => ({ matches: false, addEventListener() {} }),
  requestAnimationFrame: (f) => { try { f(); } catch (_) {} return 0; },
  cancelAnimationFrame() {},
  getComputedStyle: () => ({ getPropertyValue: () => "" }),
  URL, URLSearchParams, TextDecoder, TextEncoder, AbortController,
  structuredClone: (v) => JSON.parse(JSON.stringify(v)),
  addEventListener() {},
  removeEventListener() {},
  innerWidth: 1280,
  innerHeight: 800,
  scrollTo() {},
  print() {},
  open: () => null,
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.self = sandbox;

const ctx = vm.createContext(sandbox);

const carpeta = path.dirname(appPath);
for (const fichero of ["profile_model.js", "chat_context_model.js", "chat_withheld_notice.js",
  "structured_education_ui.js", "claims_view.js", "conditions_load.js",
  "scenario_provenance.js", "comparison_report.js", "context_help.js"]) {
  const ruta = path.join(carpeta, fichero);
  if (fs.existsSync(ruta)) {
    try { vm.runInContext(fs.readFileSync(ruta, "utf8"), ctx, { filename: fichero }); }
    catch (_) { /* un auxiliar caído no debe ocultar el fallo de renderHome */ }
  }
}

// readyState "loading": app.js define todo pero no arranca sola.
vm.runInContext(fs.readFileSync(appPath, "utf8"), ctx, { filename: "app.js" });

// `state` vive dentro del módulo; se le pasa el status por la API pública.
if (typeof ctx.applyStatus === "function") {
  ctx.applyStatus(status);
} else if (ctx.state) {
  ctx.state.status = status;
  ctx.state.route = "inicio";
}

let error = null;
try {
  if (ctx.state) ctx.state.route = "inicio";
  ctx.renderHome();
} catch (e) {
  error = String((e && e.message) || e);
}

function recoger(nodo, acc) {
  if (!nodo || typeof nodo !== "object") return acc;
  if (nodo.id) acc.ids.push(String(nodo.id));
  if (nodo.className) acc.clases.push(String(nodo.className));
  for (const hijo of nodo.children || []) recoger(hijo, acc);
  return acc;
}

const acc = recoger(body, { ids: [], clases: [] });
for (const nodo of Object.values(byId)) recoger(nodo, acc);

// Texto del aviso de historial: su contenido depende de la capacidad del servicio.
function buscarTexto(nodo, acc) {
  if (!nodo || typeof nodo !== "object") return acc;
  if (String(nodo.className || "").includes("choice") || nodo.tag === "label") {
    acc.push((nodo.textContent || "").replace(/\s+/g, " ") + " " +
             (nodo.children || []).map((h) => h.textContent || "").join(" "));
  }
  for (const hijo of nodo.children || []) buscarTexto(hijo, acc);
  return acc;
}
const avisos = buscarTexto(body, []).join(" ").replace(/\s+/g, " ");

// El aviso del historial se busca por el texto que le pasa chatHistoryConsentText,
// que es lo que hay que verificar: no depende de que el DOM falso propague
// textContent por los padres.
let avisoHistorial = null;
try {
  const conHistorial = ctx.chatHistoryConsentText({ history: true });
  const sinHistorial = ctx.chatHistoryConsentText({ history: false });
  avisoHistorial = { con: String(conHistorial), sin: String(sinHistorial) };
} catch (_) { /* si la funcion no es accesible, queda null */ }

process.stdout.write(JSON.stringify({
  error,
  ids: [...new Set(acc.ids)],
  clases: [...new Set(acc.clases)],
  aviso_historial: avisoHistorial,
}));
