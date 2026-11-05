#!/usr/bin/env node
"use strict";

/*
 * B9 — regresión de robustez y accesibilidad funcional.
 *
 * Este archivo es SOLO de prueba: no importa ni modifica código de producción,
 * no lee .env y no usa red externa. Todo ocurre en 127.0.0.1.
 *
 * Qué demuestra:
 *   B9-1  El skip-link recibe el primer Tab y enfoca #main-content sin cambiar
 *         de ruta.
 *   B9-2  Una API retenida corta por timeout (10–15 s) con error reintentable y
 *         aria-busy=false.
 *   B9-3  Tras «Intentar de nuevo» el foco no cae en BODY y la carga/éxito se
 *         anuncian en una región role=status persistente. Cubre biblioteca,
 *         reintento de escenarios y reintento del catálogo del ensayo.
 *   B9-4  El refresco asíncrono de condiciones no roba el foco (biblioteca ni
 *         ensayo).
 *   B9-5  Los errores de formulario marcan aria-invalid/aria-describedby y
 *         enfocan el primer control inválido (perfil, escenario, ensayo),
 *         también en el envío vacío (formularios con novalidate).
 *   B9-6  El stepper del ensayo no desborda a 320 px ni al 200 % de texto, y a
 *         320 px + 200 % la página no gana scroll horizontal por topbar/nav.
 *   B9-7  Escribir en el escenario no reanuncia la tabla de comparación ni
 *         reescribe la región viva del informe con el mismo texto.
 *   B9-8  Cancelar/confirmar una confirmación en línea devuelve el foco al
 *         disparador.
 *   B9-9  El error de escenarios ofrece reintento, el submit se bloquea
 *         mientras pending (sin POST duplicados) y deshabilitar el botón
 *         enfocado no manda el foco a BODY.
 *   B9-10 La biblioteca no salta de h1 a h3.
 *   B9-11 El chip de estado se refresca tras un éxito de API y se recupera con
 *         un único reintento automático cuando /api/status falla después.
 *   B9-12 El comparador no duplica POST mientras está ocupado.
 *
 * Uso:
 *   node tests/b9_accessibility.test.cjs
 *   PYTHON=/ruta/python CHROME_PATH=/ruta/chrome node tests/b9_accessibility.test.cjs
 *   B9_ONLY=B9-3c,B9-5d node tests/b9_accessibility.test.cjs   (solo esas comprobaciones)
 *
 * Salida: PASS/FAIL por comprobación. Sale 1 si hay fallos de producto, 2 si
 * falla el arnés (navegador, servidor o DOM no disponibles).
 */

const { spawn } = require("node:child_process");
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");

const ROOT = path.resolve(__dirname, "..");
const STATIC_ROOT = path.join(ROOT, "api", "_static");
const SOURCE_STATIC = path.join(ROOT, "prototipos", "paideia-local", "static");
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/* ------------------------------------------------------------------------- */
/* Resultados                                                                */
/* ------------------------------------------------------------------------- */

const results = [];

function record(id, title, pass, expected, actual) {
  results.push({ id, title, pass, expected, actual });
  console.log(`${pass ? "PASS" : "FAIL"} ${id} — ${title}`);
  if (!pass) {
    console.log(`     esperado: ${expected}`);
    console.log(`     real:     ${actual}`);
  }
}

function recordHarness(id, title, pass, detail) {
  results.push({ id, title, pass, harness: true, actual: detail });
  console.log(`${pass ? "PASS" : "HARNESS-FAIL"} ${id} — ${title}`);
  if (!pass) console.log(`     detalle:  ${detail}`);
}

function summarize() {
  const failed = results.filter((item) => !item.pass);
  const productFailed = failed.filter((item) => !item.harness);
  const harnessFailed = failed.filter((item) => item.harness);
  console.log("\n" + "=".repeat(78));
  console.log(
    `Resumen: ${results.length} comprobaciones, ${results.length - failed.length} PASS, ` +
      `${productFailed.length} fallo(s) de producto, ${harnessFailed.length} fallo(s) de arnés.`
  );
  if (harnessFailed.length) {
    console.log("ESTADO: ARNÉS INCOMPLETO — los fallos de producto no son concluyentes.");
  } else if (productFailed.length) {
    console.log("ESTADO: RED — los fallos son del producto, no del arnés.");
  } else {
    console.log("ESTADO: VERDE — no se reprodujeron los defectos B9.");
  }
  console.log("=".repeat(78));
  return harnessFailed.length ? 2 : productFailed.length ? 1 : 0;
}

/* ------------------------------------------------------------------------- */
/* CDP mínimo (WebSocket nativo de Node)                                     */
/* ------------------------------------------------------------------------- */

class Cdp {
  static async open(url) {
    const ws = new WebSocket(url);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = (event) => reject(new Error(`No se pudo abrir CDP ${url}: ${event.message || "error"}`));
    });
    return new Cdp(ws);
  }

  constructor(ws) {
    this.ws = ws;
    this.nextId = 1;
    this.pending = new Map();
    this.handlers = new Map();
    ws.onmessage = (event) => this.onMessage(event);
    ws.onclose = () => {
      for (const { reject, timer } of this.pending.values()) {
        clearTimeout(timer);
        reject(new Error("CDP cerrado"));
      }
      this.pending.clear();
    };
  }

  on(method, handler) {
    if (!this.handlers.has(method)) this.handlers.set(method, new Set());
    this.handlers.get(method).add(handler);
    return () => this.handlers.get(method)?.delete(handler);
  }

  onMessage(event) {
    let message;
    try {
      message = JSON.parse(typeof event.data === "string" ? event.data : Buffer.from(event.data).toString("utf8"));
    } catch {
      return;
    }
    if (message.id !== undefined) {
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      clearTimeout(pending.timer);
      if (message.error) pending.reject(new Error(`${message.error.message} (${message.error.code})`));
      else pending.resolve(message.result);
      return;
    }
    for (const handler of this.handlers.get(message.method) || []) {
      try {
        handler(message.params || {});
      } catch (error) {
        console.error(`CDP handler ${message.method}: ${error.message}`);
      }
    }
  }

  send(method, params = {}, timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Timeout CDP ${method}`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    try {
      this.ws.close();
    } catch {
      /* noop */
    }
  }
}

function findBrowserExecutable() {
  const explicit = process.env.CHROME_PATH;
  if (explicit && fs.existsSync(explicit)) return explicit;
  const candidates = [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}

async function launchBrowser() {
  const executable = findBrowserExecutable();
  if (!executable) throw new Error("No se encontró Chrome/Edge. Define CHROME_PATH.");
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "b9-a11y-chrome-"));
  const args = [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-sync",
    "--metrics-recording-only",
    "--no-pings",
    "--disable-features=OptimizationHints,Translate",
    "--remote-debugging-port=0",
    "--remote-allow-origins=*",
    `--user-data-dir=${userDataDir}`,
    "--window-size=1280,900",
    "about:blank",
  ];
  const child = spawn(executable, args, { stdio: ["ignore", "ignore", "pipe"] });
  let stderr = "";
  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
    if (stderr.length > 20000) stderr = stderr.slice(-20000);
  });

  const portFile = path.join(userDataDir, "DevToolsActivePort");
  let port = null;
  let browserPath = null;
  for (let attempt = 0; attempt < 200; attempt += 1) {
    if (child.exitCode !== null) break;
    if (fs.existsSync(portFile)) {
      const lines = fs.readFileSync(portFile, "utf8").trim().split(/\r?\n/);
      if (lines.length >= 2 && /^\d+$/.test(lines[0])) {
        port = Number(lines[0]);
        browserPath = lines[1];
        break;
      }
    }
    await sleep(100);
  }
  if (!port || !browserPath) {
    child.kill();
    throw new Error(`Chrome no publicó DevToolsActivePort. stderr: ${stderr.slice(-1500)}`);
  }

  const browser = await Cdp.open(`ws://127.0.0.1:${port}${browserPath}`);
  const pages = [];

  async function newPage() {
    const { targetId } = await browser.send("Target.createTarget", { url: "about:blank" });
    let info = null;
    for (let attempt = 0; attempt < 100; attempt += 1) {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      const list = await response.json();
      info = list.find((entry) => entry.id === targetId && entry.webSocketDebuggerUrl);
      if (info) break;
      await sleep(50);
    }
    if (!info) throw new Error(`No se encontró el target ${targetId}`);
    const client = await Cdp.open(info.webSocketDebuggerUrl);
    await client.send("Page.enable");
    await client.send("Runtime.enable");
    const page = createPage(client, targetId);
    pages.push(page);
    return page;
  }

  async function close() {
    for (const page of pages) {
      try {
        await browser.send("Target.closeTarget", { targetId: page.targetId }, 5000);
      } catch {
        /* noop */
      }
      page.client.close();
    }
    browser.close();
    try {
      child.kill();
    } catch {
      /* noop */
    }
    await sleep(300);
    try {
      fs.rmSync(userDataDir, { recursive: true, force: true });
    } catch {
      /* noop */
    }
  }

  return { child, port, browser, newPage, close, stderr: () => stderr };
}

function createPage(client, targetId) {
  const dialogs = [];
  client.on("Page.javascriptDialogOpening", (params) => {
    dialogs.push(params.message || "");
    client.send("Page.handleJavaScriptDialog", { accept: true }).catch(() => {});
  });
  return {
    targetId,
    client,
    dialogs,
    async js(expression) {
      const response = await client.send("Runtime.evaluate", {
        expression,
        returnByValue: true,
        awaitPromise: true,
        userGesture: true,
      });
      if (response.exceptionDetails) {
        const description =
          response.exceptionDetails.exception?.description ||
          response.exceptionDetails.text ||
          "excepción de página";
        throw new Error(description);
      }
      return response.result.value;
    },
    async navigate(url) {
      await client.send("Page.navigate", { url });
      await waitFor(
        async () => {
          try {
            return (await this.js("document.readyState")) === "complete";
          } catch {
            return false;
          }
        },
        15000,
        `carga ${url}`
      );
    },
    async key(key, code, keyCode) {
      const base = { key, code, windowsVirtualKeyCode: keyCode, nativeVirtualKeyCode: keyCode };
      await client.send("Input.dispatchKeyEvent", { type: "keyDown", ...base });
      await client.send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
    },
    async tab() {
      await this.key("Tab", "Tab", 9);
    },
    async enter() {
      const base = { key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 };
      await client.send("Input.dispatchKeyEvent", { type: "keyDown", ...base, text: "\r", unmodifiedText: "\r" });
      await client.send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
    },
  };
}

async function waitFor(check, timeoutMs, label) {
  const start = Date.now();
  let lastError = null;
  while (Date.now() - start < timeoutMs) {
    try {
      const value = await check();
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await sleep(100);
  }
  throw new Error(`Timeout esperando ${label}${lastError ? `: ${lastError.message}` : ""}`);
}

async function textOf(page, selector) {
  return page.js(`(() => { const node = document.querySelector(${JSON.stringify(selector)}); return node ? node.textContent : null; })()`);
}

async function visibleButtons(page) {
  return page.js(
    `[...document.querySelectorAll('button, a')].filter(n => n.offsetParent !== null).map(n => n.textContent.trim()).slice(0, 80)`
  );
}

async function clickText(page, text) {
  const outcome = await page.js(`(() => {
    const nodes = [...document.querySelectorAll('button, a')];
    const target = nodes.find((node) => node.textContent.trim() === ${JSON.stringify(text)} && !node.disabled);
    if (!target) return { ok: false, visible: [...document.querySelectorAll('button, a')].filter(n => n.offsetParent !== null).map(n => n.textContent.trim()).slice(0, 80) };
    target.click();
    return { ok: true, tag: target.tagName };
  })()`);
  if (!outcome.ok) throw new Error(`No se encontró «${text}». Visibles: ${outcome.visible.join(" | ")}`);
}

async function focusText(page, text) {
  const outcome = await page.js(`(() => {
    const nodes = [...document.querySelectorAll('button, a')];
    const target = nodes.find((node) => node.textContent.trim() === ${JSON.stringify(text)} && !node.disabled);
    if (!target) return { ok: false };
    target.focus();
    return { ok: true, id: target.id || null };
  })()`);
  if (!outcome.ok) throw new Error(`No se pudo enfocar «${text}»`);
}

async function activeInfo(page) {
  return page.js(`(() => {
    const a = document.activeElement;
    return a ? { tag: a.tagName, id: a.id || null, cls: typeof a.className === 'string' ? a.className : null, text: (a.textContent || '').trim().slice(0, 100) } : null;
  })()`);
}

async function waitApp(page) {
  await waitFor(async () => await page.js("!!document.getElementById('chat-consent')"), 15000, "chat renderizado");
  await waitFor(
    async () => {
      const text = await page.js("(document.getElementById('status-chip') || {}).textContent || ''");
      return !/Comprobando/i.test(text);
    },
    15000,
    "estado del servicio"
  );
}

async function inputValue(page, selector) {
  return page.js(`(() => { const node = document.querySelector(${JSON.stringify(selector)}); return node ? node.value : null; })()`);
}

async function setInput(page, selector, value) {
  await page.js(`(() => {
    const node = document.querySelector(${JSON.stringify(selector)});
    if (!node) throw new Error('No existe ${selector}');
    node.value = ${JSON.stringify(value)};
    node.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
}

async function setSelect(page, selector, value) {
  await page.js(`(() => {
    const node = document.querySelector(${JSON.stringify(selector)});
    if (!node) throw new Error('No existe ${selector}');
    node.value = ${JSON.stringify(value)};
    node.dispatchEvent(new Event('change', { bubbles: true }));
  })()`);
}

async function fillScenario(page, suffix = "") {
  for (const [field, value] of [
    ["principal", "1000"],
    ["rate", "2"],
    ["years", "5"],
    ["contribution", "50"],
    ["inflation", "2"],
  ]) {
    await setInput(page, `#scenario-${field}${suffix}`, value);
  }
}

function requestCount(fixture, key) {
  return fixture.state[`${key}Requests`].length + fixture.state.hangs.filter((entry) => entry.key === key).length;
}

/* ------------------------------------------------------------------------- */
/* Servidor fixture (solo loopback, datos ficticios)                          */
/* ------------------------------------------------------------------------- */

const PRODUCTS = [
  {
    id: "11111111-1111-4111-8111-111111111111",
    name: "Depósito ficticio Alfa",
    family: "deposito",
    issuer: "Banco Ficticio Uno",
    identity_state: "proposed",
    conditions_state: "pending",
    primary_url: "https://example.invalid/alfa",
    isin: "ES0000000001",
    conflicts: [],
    unknown_fields: [],
  },
  {
    id: "22222222-2222-4222-8222-222222222222",
    name: "Cuenta ficticia Beta",
    family: "cuenta_remunerada",
    issuer: "Banco Ficticio Dos",
    identity_state: "proposed",
    conditions_state: "pending",
    primary_url: "https://example.invalid/beta",
    isin: "ES0000000002",
    conflicts: [],
    unknown_fields: [],
  },
  {
    id: "33333333-3333-4333-8333-333333333333",
    name: "Fondo ficticio Gamma",
    family: "fondo_tradicional",
    issuer: "Gestora Ficticia",
    identity_state: "proposed",
    conditions_state: "pending",
    primary_url: "https://example.invalid/gamma",
    isin: "ES0000000003",
    conflicts: [],
    unknown_fields: [],
  },
];

function statusPayload() {
  return {
    mode: "local_prototype",
    ai: {
      connected: true,
      status: "configured_not_verified",
      message: "Proveedor ficticio de prueba; sin red externa.",
      capabilities: { context: true, history: true, synthetic_only: false, structured_education: false },
      quota: { calls_day: 0, calls_per_day: 20 },
    },
    catalogue: { candidate_count: PRODUCTS.length, publication_ready: 0 },
    storage: "fixture_loopback",
  };
}

function calculationPayload(body) {
  return {
    hypothetical: true,
    not_prediction: true,
    assumptions: {
      principal: String(body && body.principal) || "1000",
      annual_rate_percent: String(body && body.annual_rate_percent) || "2",
      years: Number(body && body.years) || 5,
      monthly_contribution: String(body && body.monthly_contribution) || "50",
      inflation_percent: String(body && body.inflation_percent) || "2",
      method: (body && body.method) || "compound",
    },
    summary: {
      contributions: "4000.00",
      final_balance: "4300.00",
      interest: "300.00",
      inflation_adjusted: "3900.00",
    },
    series: [
      { month: 0, contributions: "1000.00", balance: "1000.00", real_balance: "1000.00" },
      { month: 12, contributions: "1600.00", balance: "1650.00", real_balance: "1570.00" },
      { month: 60, contributions: "4000.00", balance: "4300.00", real_balance: "3900.00" },
    ],
  };
}

function mimeType(file) {
  const ext = path.extname(file).toLowerCase();
  return (
    {
      ".html": "text/html; charset=utf-8",
      ".js": "text/javascript; charset=utf-8",
      ".css": "text/css; charset=utf-8",
      ".svg": "image/svg+xml",
      ".json": "application/json; charset=utf-8",
      ".png": "image/png",
      ".woff2": "font/woff2",
    }[ext] || "application/octet-stream"
  );
}

function readRequestBody(request) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    request.on("data", (chunk) => {
      size += chunk.length;
      if (size > 1024 * 1024) {
        reject(new Error("Cuerpo demasiado grande"));
        request.destroy();
        return;
      }
      chunks.push(chunk);
    });
    request.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    request.on("error", reject);
  });
}

async function startFixture() {
  const state = {
    modes: { status: "ok", catalogue: "ok", conditions: "ok", compare: "ok", calculate: "ok" },
    delays: { catalogue: 0, compare: 0, calculate: 0 },
    hangs: [],
    statusRequests: [],
    chatRequests: [],
    compareRequests: [],
    calculateRequests: [],
  };

  const server = http.createServer(async (request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    const sendJson = (status, payload) => {
      if (response.writableEnded) return;
      const body = Buffer.from(JSON.stringify(payload), "utf8");
      response.writeHead(status, {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "Content-Length": body.length,
      });
      response.end(body);
    };
    const keyFor = (pathname, method) => {
      if (pathname === "/api/status" && method === "GET") return "status";
      if (pathname === "/api/catalogue" && method === "GET") return "catalogue";
      if (pathname === "/api/conditions" && method === "GET") return "conditions";
      if (pathname === "/api/compare" && method === "POST") return "compare";
      if (pathname === "/api/calculate" && method === "POST") return "calculate";
      return null;
    };

    const key = keyFor(url.pathname, request.method);
    if (key === "status") state.statusRequests.push({ at: Date.now() });
    if (key) {
      const mode = state.modes[key];
      if (mode === "hang") {
        state.hangs.push({ key, response, at: Date.now() });
        return;
      }
      if (mode === "fail") {
        sendJson(500, { error: { code: "TEST_FAILURE", message: "Fallo ficticio de prueba.", retryable: true } });
        return;
      }
      const delay = state.delays[key] || 0;
      if (delay) await sleep(delay);

      if (key === "status") {
        sendJson(200, statusPayload());
        return;
      }
      if (key === "catalogue") {
        sendJson(200, { items: PRODUCTS, count: PRODUCTS.length });
        return;
      }
      if (key === "conditions") {
        sendJson(200, { reference_date: "2026-11-01", products: [] });
        return;
      }
      if (key === "compare") {
        const raw = await readRequestBody(request);
        let body = null;
        try {
          body = JSON.parse(raw);
        } catch {
          body = null;
        }
        state.compareRequests.push({ raw, body, at: Date.now() });
        const ids = body && Array.isArray(body.product_ids) ? body.product_ids : [];
        const items = PRODUCTS.filter((product) => ids.includes(product.id));
        sendJson(200, { items, reasons: ["Comparación ficticia de metadatos."], quantitative_ready: false });
        return;
      }
      if (key === "calculate") {
        const raw = await readRequestBody(request);
        let body = null;
        try {
          body = JSON.parse(raw);
        } catch {
          body = null;
        }
        state.calculateRequests.push({ raw, body, at: Date.now() });
        sendJson(200, calculationPayload(body));
        return;
      }
    }
    if (url.pathname.startsWith("/api/products/")) {
      const id = decodeURIComponent(url.pathname.slice("/api/products/".length));
      const product = PRODUCTS.find((item) => item.id === id);
      if (product) {
        sendJson(200, { product });
        return;
      }
    }
    if (url.pathname.startsWith("/api/")) {
      sendJson(404, { error: { code: "NOT_FOUND", message: "Fixture sin ruta.", retryable: false } });
      return;
    }

    const relative = url.pathname === "/" ? "index.html" : decodeURIComponent(url.pathname.replace(/^\/+/, ""));
    const file = path.resolve(STATIC_ROOT, relative);
    if (!file.startsWith(path.resolve(STATIC_ROOT) + path.sep) && file !== path.join(STATIC_ROOT, "index.html")) {
      sendJson(403, { error: { code: "FORBIDDEN", message: "Fuera de estáticos.", retryable: false } });
      return;
    }
    try {
      const data = fs.readFileSync(file);
      response.writeHead(200, {
        "Content-Type": mimeType(file),
        "Cache-Control": "no-store",
        "Content-Length": data.length,
      });
      response.end(data);
    } catch {
      sendJson(404, { error: { code: "NOT_FOUND", message: "Archivo no encontrado.", retryable: false } });
    }
  });

  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const origin = `http://127.0.0.1:${server.address().port}`;
  return {
    origin,
    state,
    release(key) {
      const remaining = [];
      for (const entry of state.hangs) {
        if (entry.key !== key) {
          remaining.push(entry);
          continue;
        }
        if (entry.response.writableEnded) continue;
        let payload = { products: [], reference_date: "2026-11-01" };
        if (key === "catalogue") payload = { items: PRODUCTS, count: PRODUCTS.length };
        if (key === "status") payload = statusPayload();
        if (key === "compare") payload = { items: [], reasons: ["liberado"], quantitative_ready: false };
        if (key === "calculate") payload = calculationPayload(null);
        const body = Buffer.from(JSON.stringify(payload), "utf8");
        entry.response.writeHead(200, {
          "Content-Type": "application/json; charset=utf-8",
          "Cache-Control": "no-store",
          "Content-Length": body.length,
        });
        entry.response.end(body);
      }
      state.hangs = remaining;
    },
    close: () =>
      new Promise((resolve) => {
        for (const entry of state.hangs) {
          try {
            entry.response.destroy();
          } catch {
            /* noop */
          }
        }
        try {
          server.closeAllConnections();
        } catch {
          /* noop */
        }
        server.close(resolve);
      }),
  };
}

/* ------------------------------------------------------------------------- */
/* Escenarios                                                                */
/* ------------------------------------------------------------------------- */

async function openPage(browser, fixture, hash) {
  const page = await browser.newPage();
  await page.navigate(`${fixture.origin}/${hash}`);
  await waitFor(async () => await page.js("!!document.getElementById('status-chip')"), 15000, "shell");
  return page;
}

async function closePage(browser, page) {
  try {
    await browser.browser.send("Target.closeTarget", { targetId: page.targetId }, 5000);
  } catch {
    /* noop */
  }
  page.client.close();
}

function assert(condition, detail) {
  if (!condition) throw new Error(detail);
}

async function testSkipLink(browser, fixture) {
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('.product-card')"), 10000, "tarjetas");
    await page.js("window.scrollTo(0, 0); document.activeElement && document.activeElement.blur();");
    await page.tab();
    const first = await activeInfo(page);
    record(
      "B9-1a",
      "el primer Tab desde la carga alcanza el skip-link",
      Boolean(first && first.cls && first.cls.includes("skip-link")),
      "activeElement = a.skip-link",
      JSON.stringify(first)
    );

    await page.js("document.querySelector('.skip-link').focus()");
    const beforeHash = await page.js("location.hash");
    await page.enter();
    await sleep(300);
    const afterHash = await page.js("location.hash");
    const after = await activeInfo(page);
    record(
      "B9-1b",
      "Enter en el skip-link conserva la ruta y enfoca #main-content",
      afterHash === beforeHash && after && after.id === "main-content",
      `hash=${beforeHash} y activeElement=#main-content`,
      `hash=${afterHash} active=${JSON.stringify(after)}`
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testTimeout(browser, fixture) {
  fixture.state.modes.status = "hang";
  fixture.state.modes.catalogue = "hang";
  fixture.state.modes.conditions = "ok";
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    const started = Date.now();
    await waitFor(
      async () => await page.js("!!document.querySelector('#catalogue-results .error-note button')"),
      20000,
      "error por timeout con reintento"
    );
    const elapsed = Date.now() - started;
    const busy = await page.js("document.getElementById('catalogue-results').getAttribute('aria-busy')");
    const retryText = await textOf(page, "#catalogue-results .error-note button");
    const chip = await textOf(page, "#status-chip");
    record(
      "B9-2a",
      "una API retenida corta por timeout (10–15 s) con error reintentable",
      elapsed >= 9000 && elapsed <= 16000 && busy === "false" && /Intentar de nuevo/i.test(retryText || "") && /sin respuesta/i.test(chip || ""),
      "error reintentable tras 10–15 s, aria-busy=false y chip de error",
      `elapsed=${elapsed}ms ariaBusy=${busy} retry=${JSON.stringify(retryText)} chip=${JSON.stringify(chip)}`
    );

    fixture.state.modes.status = "ok";
    fixture.state.modes.catalogue = "ok";
    await focusText(page, "Intentar de nuevo");
    await page.js("document.activeElement.click()");
    await waitFor(async () => (await textOf(page, "#catalogue-results"))?.includes("3 candidatos"), 10000, "recuperación");
    record(
      "B9-2b",
      "el error por timeout se recupera con «Intentar de nuevo»",
      true,
      "3 candidatos tras reintentar",
      "3 candidatos"
    );
  } finally {
    fixture.state.modes.status = "ok";
    fixture.state.modes.catalogue = "ok";
    await closePage(browser, page);
  }
}

async function testRetryFocus(browser, fixture) {
  fixture.state.modes.catalogue = "fail";
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('#catalogue-results .error-note button')"), 10000, "error biblioteca");
    fixture.state.modes.catalogue = "ok";
    await focusText(page, "Intentar de nuevo");
    await page.js("document.activeElement.click()");
    await waitFor(async () => (await textOf(page, "#catalogue-results"))?.includes("3 candidatos"), 10000, "resultados");
    const active = await activeInfo(page);
    record(
      "B9-3a",
      "tras «Intentar de nuevo» el foco va al contenedor de resultados, no a BODY",
      active && active.id === "catalogue-results" && (await page.js("document.getElementById('catalogue-results').tabIndex")) === -1,
      "activeElement=#catalogue-results[tabindex=-1]",
      JSON.stringify(active)
    );
  } finally {
    fixture.state.modes.catalogue = "ok";
    await closePage(browser, page);
  }
}

async function testScenarioRetryFocus(browser, fixture) {
  fixture.state.modes.calculate = "fail";
  const page = await openPage(browser, fixture, "#escenarios");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('scenario-principal')"), 10000, "formulario");
    await fillScenario(page, "");
    await page.js("document.querySelectorAll('.scenario-form')[0].requestSubmit()");
    await waitFor(async () => await page.js("!!document.querySelector('#scenario-output .error-note button')"), 10000, "reintento de escenario");
    fixture.state.modes.calculate = "ok";
    fixture.state.delays.calculate = 400;
    await focusText(page, "Intentar de nuevo");
    const focused = await activeInfo(page);
    await page.enter();
    await sleep(120);
    const during = await activeInfo(page);
    await waitFor(async () => await page.js("!!document.querySelector('#scenario-output .scenario-summary')"), 10000, "resultado del escenario");
    await sleep(150);
    const after = await activeInfo(page);
    const tabIndex = await page.js("document.getElementById('scenario-output').tabIndex");
    record(
      "B9-3c",
      "tras reintentar el cálculo de escenarios el foco no cae en BODY",
      Boolean(focused && focused.tag === "BUTTON" && during && during.id === "scenario-output" && after && after.id === "scenario-output" && tabIndex === -1),
      "«Intentar de nuevo» enfocado → foco en #scenario-output[tabindex=-1] durante el cálculo y tras el 200",
      `focus=${JSON.stringify(focused)} during=${JSON.stringify(during)} after=${JSON.stringify(after)} tabIndex=${tabIndex}`
    );
  } finally {
    fixture.state.modes.calculate = "ok";
    fixture.state.delays.calculate = 0;
    await closePage(browser, page);
  }
}

async function testSimulationRetryFocus(browser, fixture) {
  fixture.state.modes.catalogue = "fail";
  const page = await openPage(browser, fixture, "#simulacion");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('#simulation-candidates .error-note button')"), 10000, "error de catálogo del ensayo");
    fixture.state.modes.catalogue = "ok";
    await focusText(page, "Intentar de nuevo");
    const focused = await activeInfo(page);
    await page.enter();
    await waitFor(async () => await page.js("!!document.getElementById('simulation-product')"), 10000, "selector recuperado");
    await sleep(150);
    const after = await activeInfo(page);
    record(
      "B9-3d",
      "tras reintentar el catálogo del ensayo el foco va a un control útil, no a BODY",
      Boolean(focused && focused.tag === "BUTTON" && after && after.id === "simulation-product"),
      "«Intentar de nuevo» enfocado → foco en #simulation-product",
      `focus=${JSON.stringify(focused)} after=${JSON.stringify(after)}`
    );
  } finally {
    fixture.state.modes.catalogue = "ok";
    await closePage(browser, page);
  }
}

async function testAnnouncements(browser, fixture) {
  fixture.state.modes.catalogue = "fail";
  fixture.state.delays.catalogue = 300;
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('#catalogue-results .error-note button')"), 10000, "error biblioteca");
    const attrs = await page.js(`(() => {
      const node = document.getElementById('app-status');
      return node ? { role: node.getAttribute('role'), live: node.getAttribute('aria-live') } : null;
    })()`);
    fixture.state.modes.catalogue = "ok";
    await focusText(page, "Intentar de nuevo");
    await page.js("document.activeElement.click()");
    await sleep(120);
    const loading = await textOf(page, "#app-status");
    await waitFor(async () => (await textOf(page, "#catalogue-results"))?.includes("3 candidatos"), 10000, "resultados");
    await sleep(100);
    const success = await textOf(page, "#app-status");
    record(
      "B9-3b",
      "la carga y el éxito se anuncian en una región role=status persistente",
      attrs && attrs.role === "status" && attrs.live === "polite" && /cargando/i.test(loading || "") && /candidatos/i.test(success || ""),
      "región persistente role=status aria-live=polite con «Cargando…» y «N candidatos»",
      `attrs=${JSON.stringify(attrs)} loading=${JSON.stringify(loading)} success=${JSON.stringify(success)}`
    );
  } finally {
    fixture.state.modes.catalogue = "ok";
    fixture.state.delays.catalogue = 0;
    await closePage(browser, page);
  }
}

async function testConditionsFocusLibrary(browser, fixture) {
  fixture.state.modes.conditions = "hang";
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('#catalogue-results .product-card')"), 10000, "tarjetas");
    const focused = await page.js(`(() => {
      const node = [...document.querySelectorAll('#catalogue-results button')].find(b => b.textContent.trim() === 'Ver detalle');
      if (!node) return null;
      node.focus();
      return { id: node.id || null, text: node.textContent.trim() };
    })()`);
    assert(focused, "no hay botón Ver detalle");
    fixture.release("conditions");
    await sleep(700);
    const active = await activeInfo(page);
    record(
      "B9-4a",
      "el refresco asíncrono de condiciones no roba el foco en la biblioteca",
      active && active.tag === "BUTTON" && active.text === "Ver detalle",
      "el foco sigue en el botón «Ver detalle»",
      JSON.stringify(active)
    );
  } finally {
    fixture.state.modes.conditions = "ok";
    await closePage(browser, page);
  }
}

async function testConditionsFocusSimulation(browser, fixture) {
  fixture.state.modes.conditions = "hang";
  const page = await openPage(browser, fixture, "#simulacion");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('simulation-product')"), 10000, "selector del ensayo");
    await page.js("document.getElementById('simulation-product').focus()");
    fixture.release("conditions");
    await sleep(700);
    const active = await activeInfo(page);
    record(
      "B9-4b",
      "el refresco de condiciones en el ensayo no manda el foco al h1",
      active && active.id === "simulation-product",
      "activeElement=#simulation-product",
      JSON.stringify(active)
    );
  } finally {
    fixture.state.modes.conditions = "ok";
    await closePage(browser, page);
  }
}

async function testProfileError(browser, fixture) {
  const page = await openPage(browser, fixture, "#perfil");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('.profile-form')"), 10000, "formulario de perfil");
    await page.js("document.querySelector('.profile-form').requestSubmit()");
    await waitFor(async () => (await textOf(page, "#profile-error"))?.length > 0, 5000, "error de perfil");
    const info = await page.js(`(() => {
      const active = document.activeElement;
      return {
        activeTag: active ? active.tagName : null,
        activeName: active ? active.getAttribute('name') : null,
        activeId: active ? active.id : null,
        invalid: active ? active.getAttribute('aria-invalid') : null,
        describedBy: active ? active.getAttribute('aria-describedby') : null,
      };
    })()`);
    record(
      "B9-5a",
      "el error del perfil marca aria-invalid/aria-describedby y enfoca el primer control",
      info.invalid === "true" && /profile-error/.test(info.describedBy || "") && info.activeTag === "INPUT",
      "primer input con aria-invalid=true y aria-describedby→#profile-error",
      JSON.stringify(info)
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testScenarioError(browser, fixture) {
  const page = await openPage(browser, fixture, "#escenarios");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('scenario-principal')"), 10000, "formulario de escenario");
    await fillScenario(page, "");
    await setInput(page, "#scenario-principal", "01");
    await page.js("document.querySelectorAll('.scenario-form')[0].requestSubmit()");
    await waitFor(async () => (await textOf(page, "#scenario-form-error"))?.length > 0, 5000, "error de escenario");
    const info = await page.js(`(() => {
      const input = document.getElementById('scenario-principal');
      const active = document.activeElement;
      return {
        invalid: input.getAttribute('aria-invalid'),
        describedBy: input.getAttribute('aria-describedby'),
        activeId: active ? active.id : null,
      };
    })()`);
    record(
      "B9-5b",
      "el error del escenario marca el campo y lo enfoca",
      info.invalid === "true" && /scenario-form-error/.test(info.describedBy || "") && info.activeId === "scenario-principal",
      "capital con aria-invalid=true, aria-describedby→#scenario-form-error y foco",
      JSON.stringify(info)
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testSimulationAmountError(browser, fixture) {
  const page = await openPage(browser, fixture, "#simulacion");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('simulation-product')"), 10000, "selector");
    await setSelect(page, "#simulation-product", PRODUCTS[0].id);
    await clickText(page, "Elegir referencia");
    await waitFor(async () => await page.js("!!document.querySelector('button') && [...document.querySelectorAll('button')].some(b => b.textContent.trim() === 'Continuar con el importe ficticio')"), 10000, "paso 2");
    await clickText(page, "Continuar con el importe ficticio");
    await waitFor(async () => await page.js("!!document.getElementById('simulation-amount')"), 10000, "importe");
    await page.js("document.querySelector('#simulation-amount').closest('form').requestSubmit()");
    await setInput(page, "#simulation-amount", "1e3");
    await page.js("document.querySelector('#simulation-amount').closest('form').requestSubmit()");
    await waitFor(async () => (await textOf(page, "#simulation-amount-error"))?.length > 0, 5000, "error de importe");
    const info = await page.js(`(() => {
      const input = document.getElementById('simulation-amount');
      const active = document.activeElement;
      return {
        invalid: input.getAttribute('aria-invalid'),
        describedBy: input.getAttribute('aria-describedby'),
        activeId: active ? active.id : null,
      };
    })()`);
    record(
      "B9-5c",
      "el error de importe del ensayo marca y enfoca el campo",
      info.invalid === "true" && /simulation-amount-error/.test(info.describedBy || "") && info.activeId === "simulation-amount",
      "importe con aria-invalid=true, aria-describedby→#simulation-amount-error y foco",
      JSON.stringify(info)
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testScenarioEmptySubmit(browser, fixture) {
  const page = await openPage(browser, fixture, "#escenarios");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('scenario-principal')"), 10000, "formulario");
    const before = fixture.state.calculateRequests.length;
    await page.js("document.querySelectorAll('.scenario-form')[0].requestSubmit()");
    await waitFor(async () => (await textOf(page, "#scenario-form-error"))?.length > 0, 5000, "error de envío vacío");
    const info = await page.js(`(() => {
      const form = document.querySelectorAll('.scenario-form')[0];
      const input = document.getElementById('scenario-principal');
      const active = document.activeElement;
      return {
        invalid: input.getAttribute('aria-invalid'),
        describedBy: input.getAttribute('aria-describedby'),
        error: (document.getElementById('scenario-form-error') || {}).textContent || '',
        activeId: active ? active.id : null,
        novalidate: form.hasAttribute('novalidate'),
      };
    })()`);
    const posts = fixture.state.calculateRequests.length - before;
    record(
      "B9-5d",
      "el envío vacío del escenario marca aria-invalid/aria-describedby y no se pierde en la validación nativa",
      info.invalid === "true" && /scenario-form-error/.test(info.describedBy || "") && info.error.length > 0 && info.activeId === "scenario-principal" && info.novalidate === true && posts === 0,
      "novalidate + capital con aria-invalid=true, aria-describedby→#scenario-form-error, foco y 0 POST",
      `${JSON.stringify(info)} posts=${posts}`
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testSimulationEmptyAmount(browser, fixture) {
  const page = await openPage(browser, fixture, "#simulacion");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('simulation-product')"), 10000, "selector");
    await setSelect(page, "#simulation-product", PRODUCTS[0].id);
    await clickText(page, "Elegir referencia");
    await waitFor(async () => await page.js("[...document.querySelectorAll('button')].some(b => b.textContent.trim() === 'Continuar con el importe ficticio')"), 10000, "paso 2");
    await clickText(page, "Continuar con el importe ficticio");
    await waitFor(async () => await page.js("!!document.getElementById('simulation-amount')"), 10000, "importe");
    await page.js("document.querySelector('#simulation-amount').closest('form').requestSubmit()");
    await waitFor(async () => (await textOf(page, "#simulation-amount-error"))?.length > 0, 5000, "error de importe vacío");
    const info = await page.js(`(() => {
      const form = document.querySelector('#simulation-amount').closest('form');
      const input = document.getElementById('simulation-amount');
      const active = document.activeElement;
      return {
        invalid: input.getAttribute('aria-invalid'),
        describedBy: input.getAttribute('aria-describedby'),
        error: (document.getElementById('simulation-amount-error') || {}).textContent || '',
        activeId: active ? active.id : null,
        novalidate: form.hasAttribute('novalidate'),
      };
    })()`);
    record(
      "B9-5e",
      "el importe vacío del ensayo marca aria-invalid/aria-describedby y no se pierde en la validación nativa",
      info.invalid === "true" && /simulation-amount-error/.test(info.describedBy || "") && info.error.length > 0 && info.activeId === "simulation-amount" && info.novalidate === true,
      "novalidate + importe con aria-invalid=true, aria-describedby→#simulation-amount-error y foco",
      JSON.stringify(info)
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testStepper(browser, fixture) {
  const page = await openPage(browser, fixture, "#simulacion");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('.sim-progress li')"), 10000, "stepper");
    const measure = () =>
      page.js(`[...document.querySelectorAll('.sim-progress li')].map(li => ({ text: li.textContent.trim(), w: li.clientWidth, sw: li.scrollWidth }))`);

    await page.client.send("Emulation.setDeviceMetricsOverride", { width: 320, height: 800, deviceScaleFactor: 1, mobile: false });
    await sleep(250);
    const at320 = await measure();
    const overflow320 = at320.filter((item) => item.sw > item.w + 1);
    record(
      "B9-6a",
      "el stepper del ensayo es legible a 320 px sin desbordar",
      overflow320.length === 0,
      "scrollWidth ≤ clientWidth en cada paso",
      JSON.stringify(at320)
    );

    await page.client.send("Emulation.clearDeviceMetricsOverride");
    await page.js("document.documentElement.style.fontSize = '32px'");
    await sleep(250);
    const at200 = await measure();
    const overflow200 = at200.filter((item) => item.sw > item.w + 1);
    record(
      "B9-6b",
      "el stepper del ensayo no desborda al 200 % de texto",
      overflow200.length === 0,
      "scrollWidth ≤ clientWidth en cada paso al 200 %",
      JSON.stringify(at200)
    );

    // 320 px y 200 % a la vez: el desbordamiento de 3 px venía de topbar/nav, no del stepper.
    await page.client.send("Emulation.setDeviceMetricsOverride", { width: 320, height: 800, deviceScaleFactor: 1, mobile: false });
    await sleep(250);
    const pageWidth = await page.js(`(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      nav: [...document.querySelectorAll('.nav-link')].filter(n => n.scrollWidth > n.clientWidth + 1).map(n => n.textContent.trim()),
      steps: [...document.querySelectorAll('.sim-progress li')].filter(li => li.scrollWidth > li.clientWidth + 1).map(li => li.textContent.trim()),
      offenders: [...document.querySelectorAll('body *')].filter(n => n.getBoundingClientRect().width > 0 && n.getBoundingClientRect().right > window.innerWidth + 0.5)
        .map(n => ({ tag: n.tagName, cls: typeof n.className === 'string' ? n.className : '', id: n.id || null, right: Math.round(n.getBoundingClientRect().right), w: Math.round(n.getBoundingClientRect().width), text: (n.textContent || '').trim().slice(0, 30) })).slice(0, 8),
      topbar: (() => { const a = document.querySelector('.topbar-actions'); const c = document.getElementById('status-chip'); const b = document.querySelector('.brand'); const cs = a ? getComputedStyle(a) : null; return a && c && b ? { actionsW: Math.round(a.getBoundingClientRect().width), actionsLeft: Math.round(a.getBoundingClientRect().left), maxWidth: cs.maxWidth, chipW: Math.round(c.getBoundingClientRect().width), chipSW: c.scrollWidth, chipWhiteSpace: getComputedStyle(c).whiteSpace, brandW: Math.round(b.getBoundingClientRect().width) } : null; })()
    }))()`);
    record(
      "B9-6c",
      "a 320 px y 200 % no hay scroll horizontal de página por la topbar/nav",
      pageWidth.scrollWidth <= pageWidth.innerWidth && pageWidth.nav.length === 0 && pageWidth.steps.length === 0,
      "scrollWidth ≤ ancho de ventana, sin nav ni pasos desbordados",
      JSON.stringify(pageWidth)
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testScenarioLiveRegion(browser, fixture) {
  const page = await openPage(browser, fixture, "#escenarios");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('scenario-comparison-summary')"), 10000, "resumen de escenarios");
    const setup = await page.js(`(() => {
      const summary = document.getElementById('scenario-comparison-summary');
      const status = document.getElementById('scenario-comparison-status');
      const reportStatus = document.querySelector('#scenario-report-host [role=status]');
      window.__b9StatusMutations = 0;
      window.__b9ReportMutations = 0;
      if (status) {
        new MutationObserver((records) => {
          for (const record of records) {
            if (record.type === 'characterData') window.__b9StatusMutations += 1;
            else if (record.type === 'childList' && (record.addedNodes.length || record.removedNodes.length)) window.__b9StatusMutations += 1;
          }
        }).observe(status, { subtree: true, childList: true, characterData: true });
      }
      if (reportStatus) {
        new MutationObserver((records) => {
          for (const record of records) {
            if (record.type === 'characterData') window.__b9ReportMutations += 1;
            else if (record.type === 'childList' && (record.addedNodes.length || record.removedNodes.length)) window.__b9ReportMutations += 1;
          }
        }).observe(reportStatus, { subtree: true, childList: true, characterData: true });
      }
      return { ariaLive: summary.getAttribute('aria-live'), statusText: status ? status.textContent : null, hasStatus: !!status, hasReportStatus: !!reportStatus };
    })()`);
    for (const char of ["1", "0", "0", "0", "0"]) {
      await page.js(`(() => {
        const input = document.getElementById('scenario-principal');
        input.value = input.value + ${JSON.stringify(char)};
        input.dispatchEvent(new Event('input', { bubbles: true }));
      })()`);
      await sleep(140);
    }
    await sleep(200);
    const after = await page.js(`(() => ({
      mutations: window.__b9StatusMutations,
      statusText: (document.getElementById('scenario-comparison-status') || {}).textContent || null,
      reportMutations: window.__b9ReportMutations,
      reportText: ((document.querySelector('#scenario-report-host [role=status]') || {}).textContent) || null
    }))()`);
    record(
      "B9-7a",
      "escribir en el escenario no reanuncia la tabla de comparación",
      setup.ariaLive === null && setup.hasStatus && after.mutations === 0 && after.statusText === setup.statusText,
      "la tabla sin aria-live y una región corta sin mutaciones al teclear",
      `setup=${JSON.stringify(setup)} after=${JSON.stringify(after)}`
    );
    record(
      "B9-7b",
      "escribir en el escenario no reescribe la región viva del informe con el mismo texto",
      setup.hasReportStatus && after.reportMutations === 0,
      "0 mutaciones en #scenario-report-host [role=status] al teclear",
      `setup=${JSON.stringify(setup)} reportMutations=${after.reportMutations} reportText=${JSON.stringify(after.reportText)}`
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testInlineConfirmationFocus(browser, fixture) {
  const page = await openPage(browser, fixture, "#escenarios");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('scenario-principal')"), 10000, "formulario");
    await setInput(page, "#scenario-principal", "1000");

    await focusText(page, "Cargar ejemplo ficticio en A");
    await page.js("document.activeElement.click()");
    await waitFor(async () => await page.js("!!document.getElementById('scenario-start')"), 5000, "confirmación A");
    await focusText(page, "Cancelar");
    await page.js("document.activeElement.click()");
    await sleep(150);
    const afterCancel = await activeInfo(page);
    record(
      "B9-8a",
      "cancelar la confirmación en línea devuelve el foco al disparador",
      afterCancel && afterCancel.text === "Cargar ejemplo ficticio en A",
      "foco en «Cargar ejemplo ficticio en A»",
      JSON.stringify(afterCancel)
    );

    await focusText(page, "Cargar ejemplo ficticio en A");
    await page.js("document.activeElement.click()");
    await focusText(page, "Confirmar sustitución");
    await page.js("document.activeElement.click()");
    await sleep(250);
    const afterConfirm = await activeInfo(page);
    record(
      "B9-8b",
      "confirmar la sustitución devuelve el foco al disparador",
      afterConfirm && afterConfirm.text === "Cargar ejemplo ficticio en A",
      "foco en «Cargar ejemplo ficticio en A»",
      JSON.stringify(afterConfirm)
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testScenarioRetry(browser, fixture) {
  fixture.state.modes.calculate = "fail";
  const page = await openPage(browser, fixture, "#escenarios");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('scenario-principal')"), 10000, "formulario");
    await fillScenario(page, "");
    await page.js("document.querySelectorAll('.scenario-form')[0].requestSubmit()");
    await waitFor(async () => await page.js("!!document.querySelector('#scenario-output .error-note button')"), 10000, "reintento de escenario");
    const retryLabel = await textOf(page, "#scenario-output .error-note button");
    fixture.state.modes.calculate = "ok";
    await focusText(page, "Intentar de nuevo");
    await page.js("document.activeElement.click()");
    await waitFor(async () => await page.js("!!document.querySelector('#scenario-output .scenario-summary')"), 10000, "resultado del escenario");
    await sleep(150);
    const announced = await textOf(page, "#app-status");
    record(
      "B9-9a",
      "el error de escenarios ofrece «Intentar de nuevo» y recupera con anuncio",
      /Intentar de nuevo/i.test(retryLabel || "") && /escenario a/i.test(announced || ""),
      "botón de reintento y anuncio «Escenario A calculado»",
      `retry=${JSON.stringify(retryLabel)} status=${JSON.stringify(announced)}`
    );
  } finally {
    fixture.state.modes.calculate = "ok";
    await closePage(browser, page);
  }
}

async function testScenarioBusy(browser, fixture) {
  fixture.state.modes.calculate = "hang";
  const page = await openPage(browser, fixture, "#escenarios");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('scenario-principal')"), 10000, "formulario");
    await fillScenario(page, "");
    const before = requestCount(fixture, "calculate");
    for (let i = 0; i < 3; i += 1) {
      await page.js("document.querySelectorAll('.scenario-form')[0].requestSubmit()");
      await sleep(60);
    }
    await sleep(400);
    const posts = requestCount(fixture, "calculate") - before;
    const disabled = await page.js("document.querySelectorAll('.scenario-form')[0].querySelector('button[type=submit]').disabled");
    record(
      "B9-9b",
      "el escenario bloquea el submit mientras pending y no duplica POST",
      posts === 1 && disabled === true,
      "1 POST y submit disabled=true",
      `posts=${posts} disabled=${disabled}`
    );
  } finally {
    fixture.state.modes.calculate = "ok";
    await closePage(browser, page);
  }
}

async function testScenarioSubmitFocus(browser, fixture) {
  const page = await openPage(browser, fixture, "#escenarios");
  try {
    await waitFor(async () => await page.js("!!document.getElementById('scenario-principal')"), 10000, "formulario");
    await fillScenario(page, "");
    fixture.state.delays.calculate = 400;
    await focusText(page, "Calcular escenario A");
    const focused = await activeInfo(page);
    await page.enter();
    await sleep(120);
    const during = await activeInfo(page);
    await waitFor(async () => await page.js("!!document.querySelector('#scenario-output .scenario-summary')"), 10000, "resultado del escenario");
    await sleep(150);
    const after = await activeInfo(page);
    record(
      "B9-9c",
      "al calcular, deshabilitar el botón enfocado no manda el foco a BODY",
      Boolean(focused && focused.id === "scenario-submit" && during && during.id === "scenario-output" && after && after.id === "scenario-output"),
      "botón enfocado → foco en #scenario-output durante el cálculo y tras el resultado",
      `focus=${JSON.stringify(focused)} during=${JSON.stringify(during)} after=${JSON.stringify(after)}`
    );
  } finally {
    fixture.state.delays.calculate = 0;
    await closePage(browser, page);
  }
}

async function testHeadingLevels(browser, fixture) {
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('#catalogue-results .product-card')"), 10000, "tarjetas");
    const levels = await page.js(
      `[...document.querySelectorAll('#main-content h1, #main-content h2, #main-content h3, #main-content h4')].map(h => Number(h.tagName.slice(1)))`
    );
    record(
      "B9-10a",
      "la biblioteca no salta de h1 a h3",
      levels[0] === 1 && levels[1] === 2,
      "secuencia de encabezados 1, 2, 3…",
      JSON.stringify(levels.slice(0, 8))
    );
  } finally {
    await closePage(browser, page);
  }
}

async function testStatusChipRefresh(browser, fixture) {
  fixture.state.modes.status = "fail";
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    await waitFor(async () => /sin respuesta/i.test((await textOf(page, "#status-chip")) || ""), 10000, "chip en error");
    fixture.state.modes.status = "ok";
    await setSelect(page, "#catalogue-family", "deposito");
    await waitFor(async () => /Prototipo local/i.test((await textOf(page, "#status-chip")) || ""), 10000, "chip recuperado");
    const chip = await textOf(page, "#status-chip");
    record(
      "B9-11a",
      "el chip de estado se refresca tras un éxito de API",
      /Prototipo local/i.test(chip || "") && !/sin respuesta/i.test(chip || ""),
      "chip «Prototipo local · …» sin pulsar «Revisar estado»",
      JSON.stringify(chip)
    );
  } finally {
    fixture.state.modes.status = "ok";
    await closePage(browser, page);
  }
}

async function testStatusAutoRefresh(browser, fixture) {
  fixture.state.modes.status = "hang";
  const base = fixture.state.statusRequests.length;
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('#catalogue-results .product-card')"), 10000, "tarjetas con el estado aún en vuelo");
    const cards = await page.js("document.querySelectorAll('#catalogue-results .product-card').length");
    await waitFor(async () => /sin respuesta/i.test((await textOf(page, "#status-chip")) || ""), 20000, "chip en error tras el timeout");
    const afterFailure = fixture.state.statusRequests.length - base;
    fixture.state.modes.status = "ok";
    await waitFor(async () => /Prototipo local/i.test((await textOf(page, "#status-chip")) || ""), 8000, "chip recuperado sin interacción");
    const chip = await textOf(page, "#status-chip");
    const afterRecovery = fixture.state.statusRequests.length - base;
    await sleep(2600);
    const stable = fixture.state.statusRequests.length - base;
    record(
      "B9-11b",
      "el chip se recupera solo cuando el catálogo cargó antes de que fallara /api/status",
      cards > 0 && afterFailure === 1 && afterRecovery === 2 && stable === 2 && /Prototipo local/i.test(chip || ""),
      "20 tarjetas + 1 fallo + 1 reintento automático (2 peticiones en total, sin bucle)",
      `cards=${cards} fallo=${afterFailure} recuperado=${afterRecovery} estable=${stable} chip=${JSON.stringify(chip)}`
    );
  } finally {
    fixture.state.modes.status = "ok";
    await closePage(browser, page);
  }
}

async function testCompareBusy(browser, fixture) {
  const page = await openPage(browser, fixture, "#biblioteca");
  try {
    await waitFor(async () => await page.js("!!document.querySelector('#catalogue-results .product-card')"), 10000, "tarjetas");
    await page.js(`(() => {
      const buttons = [...document.querySelectorAll('#catalogue-results button')].filter(b => b.textContent.trim() === 'Añadir a comparar');
      buttons[0].click();
      buttons[1].click();
    })()`);
    await page.js("location.hash = '#comparar'");
    await waitFor(async () => await page.js("!!document.getElementById('compare-result')"), 10000, "comparador");
    fixture.state.modes.compare = "hang";
    const before = requestCount(fixture, "compare");
    const clickCompare = () =>
      page.js(`(() => {
        const b = [...document.querySelectorAll('button')].find((node) => node.textContent.trim() === 'Comparar metadatos');
        if (!b) throw new Error('sin botón Comparar metadatos');
        b.focus();
        b.click();
        return b.disabled;
      })()`);
    const disabledOnClick = await clickCompare();
    await clickCompare();
    await clickCompare();
    await sleep(500);
    const posts = requestCount(fixture, "compare") - before;
    const disabled = await page.js(
      `(() => { const b = [...document.querySelectorAll('button')].find((node) => node.textContent.trim() === 'Comparar metadatos'); return b ? b.disabled : null; })()`
    );
    record(
      "B9-12a",
      "el comparador bloquea envíos duplicados mientras está ocupado",
      posts === 1 && disabled === true,
      "1 POST y botón disabled=true",
      `posts=${posts} disabled=${disabled} inicial=${disabledOnClick}`
    );
  } finally {
    fixture.state.modes.compare = "ok";
    await closePage(browser, page);
  }
}

function testCopies() {
  const files = ["app.js", "index.html", "styles.css", "comparison_report.js"];
  const differing = files.filter((file) => {
    const source = fs.readFileSync(path.join(SOURCE_STATIC, file));
    const copy = fs.readFileSync(path.join(STATIC_ROOT, file));
    return !source.equals(copy);
  });
  record(
    "B9-0",
    "las copias api/_static y prototipos/paideia-local/static son idénticas",
    differing.length === 0,
    "app.js, index.html, styles.css y comparison_report.js byte a byte iguales",
    differing.length ? `difieren: ${differing.join(", ")}` : "idénticas"
  );
}

/* ------------------------------------------------------------------------- */
/* Main                                                                      */
/* ------------------------------------------------------------------------- */

const SCENARIO_TITLES = {
  "B9-1a": "el primer Tab desde la carga alcanza el skip-link",
  "B9-1b": "Enter en el skip-link conserva la ruta y enfoca #main-content",
  "B9-2a": "una API retenida corta por timeout (10–15 s) con error reintentable",
  "B9-2b": "el error por timeout se recupera con «Intentar de nuevo»",
  "B9-3a": "tras «Intentar de nuevo» el foco va al contenedor de resultados, no a BODY",
  "B9-3c": "tras reintentar el cálculo de escenarios el foco no cae en BODY",
  "B9-3d": "tras reintentar el catálogo del ensayo el foco va a un control útil, no a BODY",
  "B9-3b": "la carga y el éxito se anuncian en una región role=status persistente",
  "B9-4a": "el refresco asíncrono de condiciones no roba el foco en la biblioteca",
  "B9-4b": "el refresco de condiciones en el ensayo no manda el foco al h1",
  "B9-5a": "el error del perfil marca aria-invalid/aria-describedby y enfoca el primer control",
  "B9-5b": "el error del escenario marca el campo y lo enfoca",
  "B9-5c": "el error de importe del ensayo marca y enfoca el campo",
  "B9-5d": "el envío vacío del escenario marca aria-invalid/aria-describedby y no se pierde en la validación nativa",
  "B9-5e": "el importe vacío del ensayo marca aria-invalid/aria-describedby y no se pierde en la validación nativa",
  "B9-6a": "el stepper del ensayo es legible a 320 px sin desbordar",
  "B9-6b": "el stepper del ensayo no desborda al 200 % de texto",
  "B9-6c": "a 320 px y 200 % no hay scroll horizontal de página por la topbar/nav",
  "B9-7a": "escribir en el escenario no reanuncia la tabla de comparación",
  "B9-7b": "escribir en el escenario no reescribe la región viva del informe con el mismo texto",
  "B9-8a": "cancelar la confirmación en línea devuelve el foco al disparador",
  "B9-8b": "confirmar la sustitución devuelve el foco al disparador",
  "B9-9a": "el error de escenarios ofrece «Intentar de nuevo» y recupera con anuncio",
  "B9-9b": "el escenario bloquea el submit mientras pending y no duplica POST",
  "B9-9c": "al calcular, deshabilitar el botón enfocado no manda el foco a BODY",
  "B9-10a": "la biblioteca no salta de h1 a h3",
  "B9-11a": "el chip de estado se refresca tras un éxito de API",
  "B9-11b": "el chip se recupera solo cuando el catálogo cargó antes de que fallara /api/status",
  "B9-12a": "el comparador bloquea envíos duplicados mientras está ocupado",
};

const ONLY = (process.env.B9_ONLY || "").split(",").map((item) => item.trim()).filter(Boolean);

async function runScenario(ids, fn) {
  if (ONLY.length && !ids.some((id) => ONLY.includes(id))) return;
  try {
    await fn();
  } catch (error) {
    for (const id of ids) {
      if (!results.some((item) => item.id === id)) {
        record(id, SCENARIO_TITLES[id] || "comprobación no completada", false, "comprobación ejecutada", error.message);
      }
    }
  }
}

async function main() {
  let browser = null;
  let fixture = null;
  try {
    testCopies();
    browser = await launchBrowser();
    recordHarness("H-0a", "Chromium headless arranca y expone CDP", true, `pid=${browser.child.pid}`);
    fixture = await startFixture();
    recordHarness("H-0b", "fixture loopback sirve la app y la API ficticia", true, fixture.origin);

    await runScenario(["B9-1a", "B9-1b"], () => testSkipLink(browser, fixture));
    await runScenario(["B9-2a", "B9-2b"], () => testTimeout(browser, fixture));
    await runScenario(["B9-3a"], () => testRetryFocus(browser, fixture));
    await runScenario(["B9-3c"], () => testScenarioRetryFocus(browser, fixture));
    await runScenario(["B9-3d"], () => testSimulationRetryFocus(browser, fixture));
    await runScenario(["B9-3b"], () => testAnnouncements(browser, fixture));
    await runScenario(["B9-4a"], () => testConditionsFocusLibrary(browser, fixture));
    await runScenario(["B9-4b"], () => testConditionsFocusSimulation(browser, fixture));
    await runScenario(["B9-5a"], () => testProfileError(browser, fixture));
    await runScenario(["B9-5b"], () => testScenarioError(browser, fixture));
    await runScenario(["B9-5c"], () => testSimulationAmountError(browser, fixture));
    await runScenario(["B9-5d"], () => testScenarioEmptySubmit(browser, fixture));
    await runScenario(["B9-5e"], () => testSimulationEmptyAmount(browser, fixture));
    await runScenario(["B9-6a", "B9-6b", "B9-6c"], () => testStepper(browser, fixture));
    await runScenario(["B9-7a", "B9-7b"], () => testScenarioLiveRegion(browser, fixture));
    await runScenario(["B9-8a", "B9-8b"], () => testInlineConfirmationFocus(browser, fixture));
    await runScenario(["B9-9a"], () => testScenarioRetry(browser, fixture));
    await runScenario(["B9-9b"], () => testScenarioBusy(browser, fixture));
    await runScenario(["B9-9c"], () => testScenarioSubmitFocus(browser, fixture));
    await runScenario(["B9-10a"], () => testHeadingLevels(browser, fixture));
    await runScenario(["B9-11a"], () => testStatusChipRefresh(browser, fixture));
    await runScenario(["B9-11b"], () => testStatusAutoRefresh(browser, fixture));
    await runScenario(["B9-12a"], () => testCompareBusy(browser, fixture));
  } catch (error) {
    recordHarness("H-0z", "el arnés terminó sin excepción", false, error.stack || String(error));
  } finally {
    if (browser) await browser.close();
    if (fixture) await fixture.close();
  }
  return summarize();
}

main()
  .then((code) => {
    process.exitCode = code;
    setTimeout(() => process.exit(code), 100);
  })
  .catch((error) => {
    console.error("Fallo fatal del arnés:", error);
    process.exit(2);
  });
