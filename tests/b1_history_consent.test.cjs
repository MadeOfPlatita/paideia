#!/usr/bin/env node
"use strict";

/*
 * B1.3–B1.6 — historial de Pai: consentimiento, alcance, borrado y privacidad.
 *
 * Prueba SOLO de lectura sobre el producto: sirve api/_static y un fixture
 * loopback sintético. No usa Groq, ni red externa, ni .env, ni credenciales.
 *
 * Qué acredita:
 *   B1.3  El historial está desactivado por defecto y su casilla es un control
 *         aparte del consentimiento de la pregunta y del mapa.
 *   B1.4  El texto visible dice cuántos turnos (dos), dónde (esta pestaña, sin
 *         guardado automático) y qué se reenvía.
 *   B1.5  Sin consentimiento no viaja `history`; con consentimiento viaja solo
 *         lo ya mostrado y como máximo dos turnos (4 mensajes).
 *   B1.6  Desmarcar deja de reenviar y deja de conservar; borrar es visible,
 *         inmediato y no toca el mapa ni la copia local; tras borrar el
 *         siguiente turno parte limpio. Los errores no filtran contenido.
 *   B1.8  Una espera retenida más de 12 s avisa de estado incierto sin afirmar
 *         que no se envió, conserva la pregunta y no lanza otro POST; 429 y
 *         504 se distinguen y tampoco reintentan solos.
 *
 * Uso:
 *   node tests/b1_history_consent.test.cjs
 *   B1_SHOTS=/ruta/capturas node tests/b1_history_consent.test.cjs
 *
 * Salida: PASS/FAIL por comprobación. 1 si falla el producto, 2 si falla el
 * arnés (navegador, servidor o DOM no disponibles).
 */

const { spawn } = require("node:child_process");
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const crypto = require("node:crypto");

const ROOT = path.resolve(__dirname, "..");
const REPO_STATIC_ROOT = path.join(ROOT, "api", "_static");
const STATIC_ROOT = process.env.B1_STATIC_ROOT
  ? path.resolve(process.env.B1_STATIC_ROOT)
  : REPO_STATIC_ROOT;
const APP_JS = path.join(STATIC_ROOT, "app.js");
const PROFILE_MODEL = require(path.join(STATIC_ROOT, "profile_model.js"));

const STORAGE_KEY = "paideia.profile.v2";
const CHAT_PATH = "/api/chat";
const SHOTS = process.env.B1_SHOTS || path.join(os.tmpdir(), "b1-history-shots");
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/* Marcadores inequívocos para buscar fugas en DOM, almacenamiento y logs. */
const Q = {
  t1: "MARCA-B1-T1 pregunto por el interes compuesto",
  t2: "MARCA-B1-T2 pregunto por la inflacion",
  t3: "MARCA-B1-T3 pregunto por el colchon",
  t4: "MARCA-B1-T4 pregunto por el horizonte",
  t5: "MARCA-B1-T5 pregunto por el riesgo",
  t6: "MARCA-B1-T6 pregunto tras borrar",
  t7: "MARCA-B1-T7 borrado en vuelo",
  t8: "MARCA-B1-T8 turno limpio",
  t9: "MARCA-B1-T9 sin consentimiento",
  t10: "MARCA-B1-T10 reenvio tras desmarcar",
  t11: "MARCA-B1-T11 error del servidor",
  t12: "MARCA-B1-T12 respuesta malformada",
  t13: "MARCA-B1-T13 red caida",
  t15: "MARCA-B1-T15 espera agotada en el navegador",
  t16: "MARCA-B1-T16 limite de uso",
  t17: "MARCA-B1-T17 timeout del proveedor",
  t18: "MARCA-B1-T18 pregunta editada tras espera",
  t19: "MARCA-B1-T19 timeout no iniciado",
  t20: "MARCA-B1-T20 timeout completado",
  t21: "MARCA-B1-T21 pregunta A en vuelo",
  t22: "MARCA-B1-T22 pregunta B editada en vuelo",
  t23: "MARCA-B1-T23 turno encolado que expira",
  t24: "MARCA-B1-T24 foco durante el envio",
};
const ANSWER = (n) => `Respuesta sintetica ${n}; no es una IA real.`;

/* ------------------------------------------------------------------------- */
/* Resultados y evidencia                                                    */
/* ------------------------------------------------------------------------- */

const results = [];
const evidence = {
  started_at: new Date().toISOString(),
  static_root: STATIC_ROOT,
  app_js_sha256: null,
  app_js_mtime: null,
  app_js_sha256_end: null,
  changed_during_test: false,
  shots: [],
  requests: [],
  checks: [],
  console: [],
};

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function record(id, title, pass, expected, actual, detail) {
  const item = { id, title, pass, expected, actual };
  if (detail !== undefined) item.detail = detail;
  results.push(item);
  evidence.checks.push(item);
  console.log(`${pass ? "PASS" : "FAIL"} ${id} — ${title}`);
  if (!pass) {
    console.log(`     esperado: ${expected}`);
    console.log(`     real:     ${actual}`);
  }
  return pass;
}

function observation(id, title, actual) {
  const item = { id, title, pass: null, observation: true, actual };
  results.push(item);
  evidence.checks.push(item);
  console.log(`OBS  ${id} — ${title}`);
  if (actual) console.log(`     ${actual}`);
}

function recordHarness(id, title, pass, detail) {
  const item = { id, title, pass, harness: true, actual: detail };
  results.push(item);
  evidence.checks.push(item);
  console.log(`${pass ? "PASS" : "HARNESS-FAIL"} ${id} — ${title}`);
  if (!pass) console.log(`     detalle:  ${detail}`);
}

function summarize() {
  const failed = results.filter((item) => item.pass === false);
  const productFailed = failed.filter((item) => !item.harness);
  const harnessFailed = failed.filter((item) => item.harness);
  console.log("\n" + "=".repeat(78));
  console.log(
    `Resumen: ${results.length} comprobaciones, ${results.filter((i) => i.pass === true).length} PASS, ` +
      `${productFailed.length} fallo(s) de producto, ${harnessFailed.length} fallo(s) de arnés.`
  );
  if (harnessFailed.length) console.log("ESTADO: ARNÉS INCOMPLETO — los fallos de producto no son concluyentes.");
  else if (productFailed.length) console.log("ESTADO: RED — los fallos son del producto, no del arnés.");
  else console.log("ESTADO: VERDE — no se reprodujeron defectos en B1.3–B1.8.");
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
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "b1-history-chrome-"));
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
    "--window-size=1280,1000",
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
    await client.send("Log.enable");
    await client.send("Network.enable");
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
  const networkChatPosts = [];
  client.on("Page.javascriptDialogOpening", (params) => {
    dialogs.push(params.message || "");
    client.send("Page.handleJavaScriptDialog", { accept: true }).catch(() => {});
  });
  client.on("Network.requestWillBeSent", (params) => {
    const request = params.request || {};
    if (request.method === "POST" && /\/api\/chat$/.test(request.url || "")) {
      networkChatPosts.push({ url: request.url, at: new Date().toISOString() });
    }
  });
  client.on("Runtime.consoleAPICalled", (params) => {
    const text = (params.args || [])
      .map((arg) => (arg && (arg.value !== undefined ? String(arg.value) : arg.description || arg.type)) || "")
      .join(" ");
    evidence.console.push({ source: "console", type: params.type, text });
  });
  client.on("Log.entryAdded", (params) => {
    const entry = params.entry || {};
    evidence.console.push({ source: "log", level: entry.level, text: entry.text || "" });
  });
  client.on("Runtime.exceptionThrown", (params) => {
    const details = params.exceptionDetails || {};
    evidence.console.push({
      source: "exception",
      text: details.exception?.description || details.text || "",
    });
  });
  return {
    targetId,
    client,
    dialogs,
    networkChatPosts,
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
    async reload() {
      await client.send("Page.reload", { ignoreCache: true });
      await waitFor(
        async () => {
          try {
            return (await this.js("document.readyState")) === "complete";
          } catch {
            return false;
          }
        },
        15000,
        "recarga"
      );
    },
    async shot(name, selector) {
      const target = selector || "#chat-panel";
      await this.js(`(() => { const n = document.querySelector(${JSON.stringify(target)}); if (n) n.scrollIntoView({block:'center'}); return true; })()`);
      await sleep(300);
      const { data } = await client.send("Page.captureScreenshot", {
        format: "png",
        fromSurface: true,
        captureBeyondViewport: false,
      });
      const file = path.join(SHOTS, name);
      fs.writeFileSync(file, Buffer.from(data, "base64"));
      evidence.shots.push({ name, file, bytes: fs.statSync(file).size, selector: target });
      return file;
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

async function bodyText(page) {
  return page.js("document.body ? document.body.innerText : ''");
}

async function textOf(page, selector) {
  return page.js(`(() => { const node = document.querySelector(${JSON.stringify(selector)}); return node ? node.textContent : null; })()`);
}

async function clickText(page, text) {
  const outcome = await page.js(`(() => {
    const nodes = [...document.querySelectorAll('button, a')];
    const target = nodes.find((node) => node.textContent.trim() === ${JSON.stringify(text)} && !node.disabled);
    if (!target) return { ok: false, visible: nodes.filter((node) => node.offsetParent !== null).map((node) => node.textContent.trim()).slice(0, 60) };
    target.click();
    return { ok: true, tag: target.tagName };
  })()`);
  if (!outcome.ok) throw new Error(`No se encontró el control «${text}». Visibles: ${outcome.visible.join(" | ")}`);
}

async function setCheckbox(page, id, checked = true) {
  const outcome = await page.js(`(() => {
    const node = document.getElementById(${JSON.stringify(id)});
    if (!node) return { ok: false, reason: 'missing' };
    if (node.checked !== ${checked}) node.click();
    return { ok: true, checked: node.checked, disabled: node.disabled };
  })()`);
  if (!outcome.ok) throw new Error(`No existe #${id}`);
  return outcome;
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
  await waitFor(
    async () => {
      const node = await page.js("(() => { const n = document.getElementById('chat-history-consent'); return n ? { disabled: n.disabled } : null; })()");
      return node && node.disabled === false;
    },
    15000,
    "capacidad de historial disponible"
  );
}

async function openFresh(page, origin) {
  await page.navigate(`${origin}/#inicio`);
  await waitApp(page);
  await page.js("localStorage.clear()");
  await page.reload();
  await waitApp(page);
}

/* ------------------------------------------------------------------------- */
/* Snapshot local ficticio                                                   */
/* ------------------------------------------------------------------------- */

function buildSeedSnapshot() {
  const profile = PROFILE_MODEL.createEmptyProfile();
  const answers = [
    ["respuestas.objetivo", PROFILE_MODEL.makeAnswer("declarado", "aprender_conceptos")],
    ["respuestas.horizonte", PROFILE_MODEL.makeAnswer("declarado", "1_3_anos")],
    ["detalle_economico.importe_objetivo", PROFILE_MODEL.makeAmountAnswer("1234.56")],
    ["detalle_economico.colchon_liquido", PROFILE_MODEL.makeAmountAnswer("500")],
  ];
  for (const [key, answer] of answers) {
    if (!answer || !PROFILE_MODEL.setAnswer(profile, key, answer)) {
      throw new Error(`No se pudo construir el snapshot ficticio: ${key}`);
    }
  }
  const snapshot = PROFILE_MODEL.makeSnapshot(profile, {});
  if (!snapshot) throw new Error("Snapshot ficticio inválido");
  return JSON.stringify(snapshot);
}

async function seedProfile(page) {
  const raw = buildSeedSnapshot();
  await page.js(`localStorage.setItem(${JSON.stringify(STORAGE_KEY)}, ${JSON.stringify(raw)})`);
  await page.reload();
  await waitApp(page);
}

/* ------------------------------------------------------------------------- */
/* Fixture loopback sintético                                                */
/* ------------------------------------------------------------------------- */

function fixtureStatus(historyEnabled) {
  return {
    mode: "local_prototype",
    ai: {
      connected: false,
      status: "test_only",
      message: "Proveedor ficticio de prueba; sin red externa.",
      capabilities: {
        context: true,
        catalogue: false,
        history: historyEnabled === true,
        synthetic_only: true,
        structured_education: false,
      },
      quota: { calls_day: 0, calls_per_day: 20 },
    },
    catalogue: { candidate_count: 0, publication_ready: 0 },
    storage: "fixture_loopback",
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

async function startFixture(options = {}) {
  const statusPayload = options.status || fixtureStatus(true);
  const state = { chatRequests: [], queue: [], successCount: 0 };
  const server = http.createServer(async (request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    const sendJson = (status, payload) => {
      const body = Buffer.from(JSON.stringify(payload), "utf8");
      response.writeHead(status, {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "Content-Length": body.length,
      });
      response.end(body);
    };

    if (url.pathname === "/api/status" && request.method === "GET") {
      sendJson(200, statusPayload);
      return;
    }
    if (url.pathname === CHAT_PATH && request.method === "POST") {
      const raw = await readRequestBody(request);
      let body = null;
      try {
        body = JSON.parse(raw);
      } catch {
        body = null;
      }
      const step = state.queue.shift() || {};
      const entry = {
        seq: state.chatRequests.length + 1,
        raw,
        body,
        at: new Date().toISOString(),
        step: step.destroy
          ? "network_destroy"
          : step.kind
            ? step.kind
            : step.status
              ? `http_${step.status}`
              : "success",
      };
      state.chatRequests.push(entry);
      evidence.requests.push(entry);

      if (step.destroy) {
        request.socket.destroy();
        return;
      }
      if (step.delay) await sleep(step.delay);
      if (response.destroyed || response.writableEnded) return;
      if (step.kind === "raw") {
        response.writeHead(step.status || 200, { "Content-Type": "application/json; charset=utf-8" });
        response.end(step.raw);
        return;
      }
      if (step.status === 202) {
        sendJson(202, step.payload);
        return;
      }
      if (step.status && step.status >= 400) {
        sendJson(step.status, step.payload);
        return;
      }
      state.successCount += 1;
      const answer = step.answer || ANSWER(state.successCount);
      entry.answer = answer;
      entry.providerMode = "test_only";
      sendJson(200, {
        provider_mode: "test_only",
        external_sent: false,
        answer,
        answer_text_state: "shown",
        catalogue: { used: false, products: [] },
        answer_provenance: { limitations: [] },
        refused: false,
        truncated: false,
      });
      return;
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
    close: () => new Promise((resolve) => server.close(resolve)),
  };
}

/* ------------------------------------------------------------------------- */
/* Acciones de producto                                                      */
/* ------------------------------------------------------------------------- */

async function submitChat(page, options) {
  const { message, consent = true, contextConsent = false, historyConsent = false } = options;
  await page.js(`(() => {
    const message = document.getElementById('chat-message');
    if (message.value !== ${JSON.stringify(message)}) {
      message.value = ${JSON.stringify(message)};
      message.dispatchEvent(new Event('input', { bubbles: true }));
    }
  })()`);
  await setCheckbox(page, "chat-consent", consent);
  await setCheckbox(page, "chat-context-consent", contextConsent);
  await setCheckbox(page, "chat-history-consent", historyConsent);
  await page.js("document.querySelector('.chat-form').requestSubmit()");
}

async function waitChatIdle(page) {
  await sleep(120);
  await waitFor(
    async () => {
      const state = await page.js(`(() => {
        const feedback = (document.getElementById('chat-feedback') || {}).textContent || '';
        const button = document.querySelector('.chat-form button[type="submit"]');
        return { feedback, disabled: button ? button.disabled : true };
      })()`);
      return !state.disabled && state.feedback.length > 0 && !/Intentando contactar/i.test(state.feedback);
    },
    20000,
    "chat inactivo"
  );
  const text = await textOf(page, "#chat-feedback");
  return text || "";
}

async function submitAndCapture(page, fixture, options) {
  const before = fixture.state.chatRequests.length;
  await submitChat(page, options);
  await waitFor(() => fixture.state.chatRequests.length > before, 10000, "POST de chat");
  const request = fixture.state.chatRequests[before];
  const feedback = await waitChatIdle(page);
  return { request, feedback, index: before };
}

async function chatHistoryLength(page) {
  return page.js("(window.PaideiaChatContext && PaideiaChatContext.history().length) || 0");
}

async function chatHistory(page) {
  return page.js("(window.PaideiaChatContext && PaideiaChatContext.history()) || []");
}

function messagesOf(history) {
  return (history || []).map((item) => `${item.role}:${item.content}`);
}

function expectedMessages(turns) {
  const result = [];
  for (const turn of turns) {
    result.push(`user:${turn.q}`);
    result.push(`assistant:${turn.a}`);
  }
  return result;
}

function sameJson(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function payloadKeys(body) {
  return body && typeof body === "object" ? Object.keys(body).sort() : [];
}

/* ------------------------------------------------------------------------- */
/* B1.3 · desactivado por defecto y control separado                         */
/* ------------------------------------------------------------------------- */

async function testDefaultsAndSeparation(page, fixture) {
  console.log("\n--- B1.3 · desactivado por defecto y control separado ---");
  await openFresh(page, fixture.origin);
  await seedProfile(page);

  const initial = await page.js(`(() => {
    const consent = document.getElementById('chat-consent');
    const context = document.getElementById('chat-context-consent');
    const history = document.getElementById('chat-history-consent');
    const historyLabel = history ? history.closest('label') : null;
    const consentLabel = consent ? consent.closest('label') : null;
    return {
      consent: consent ? { checked: consent.checked, disabled: consent.disabled } : null,
      context: context ? { checked: context.checked, disabled: context.disabled } : null,
      history: history ? { checked: history.checked, disabled: history.disabled } : null,
      historyLabelText: historyLabel ? historyLabel.innerText.trim() : null,
      consentLabelContainsHistory: !!(consentLabel && history && consentLabel.contains(history)),
      contextLabelContainsHistory: !!((document.getElementById('chat-context-consent') || {}).closest && document.getElementById('chat-context-consent').closest('label').contains(history)),
      historyVisible: !!(history && history.offsetParent !== null),
      statusNote: (document.getElementById('chat-context-capabilities') || {}).textContent || '',
      callouts: [...document.querySelectorAll('.warning-note')].map((node) => node.textContent),
    };
  })()`);

  record(
    "B1.3a",
    "el historial nace desmarcado aunque el proveedor ficticio lo permita",
    initial.history && initial.history.checked === false,
    "checkbox #chat-history-consent con checked === false",
    JSON.stringify(initial.history)
  );
  record(
    "B1.3b",
    "el consentimiento de la pregunta también nace desmarcado",
    initial.consent && initial.consent.checked === false,
    "checkbox #chat-consent con checked === false",
    JSON.stringify(initial.consent)
  );
  record(
    "B1.3c",
    "la casilla de historial es un control aparte, fuera del consentimiento de la pregunta y del mapa",
    initial.history &&
      initial.history.checked === false &&
      initial.consentLabelContainsHistory === false &&
      initial.contextLabelContainsHistory === false,
    "tres checkbox distintos, con etiquetas propias; historial no anidado en la etiqueta de la pregunta",
    JSON.stringify({
      consentLabelContainsHistory: initial.consentLabelContainsHistory,
      contextLabelContainsHistory: initial.contextLabelContainsHistory,
    })
  );
  record(
    "B1.3d",
    "el control de historial es visible y está junto al formulario",
    initial.historyVisible === true,
    "offsetParent distinto de null",
    String(initial.historyVisible)
  );
  record(
    "B1.3e",
    "el aviso de capacidades informa de que el historial está habilitado en este proveedor de prueba",
    /historial:\s*habilitado/i.test(initial.statusNote || ""),
    "«historial: habilitado» en #chat-context-capabilities",
    JSON.stringify(initial.statusNote)
  );
  record(
    "B1.3f",
    "el aviso del formulario declara que mapa e historial son opcionales y con consentimiento aparte",
    initial.callouts.some((text) => /historial[\s\S]{0,80}consentimiento aparte/i.test(text)),
    "callout «Mapa e historial: opcionales y con consentimiento aparte»",
    JSON.stringify(initial.callouts.filter((text) => /historial/i.test(text)))
  );

  record(
    "B1.3i",
    "cargar el chat no hace ninguna petición de chat antes de un consentimiento",
    fixture.state.chatRequests.length === 0,
    "0 POST /api/chat tras cargar y sembrar el perfil",
    `${fixture.state.chatRequests.length} POST`
  );
  await setCheckbox(page, "chat-history-consent", true);
  await sleep(400);
  record(
    "B1.3j",
    "marcar solo la casilla de historial no envía nada: el envío exige pulsar el botón",
    fixture.state.chatRequests.length === 0,
    "0 POST /api/chat tras marcar la casilla",
    `${fixture.state.chatRequests.length} POST`
  );
  await setCheckbox(page, "chat-history-consent", false);
  await sleep(150);

  const externalResources = await page.js(
    "performance.getEntriesByType('resource').map((entry) => entry.name).filter((name) => /^https?:/.test(name) && !name.startsWith(location.origin))"
  );
  record(
    "B1.3k",
    "la página no carga recursos externos: todo el recorrido ocurre en loopback",
    Array.isArray(externalResources) && externalResources.length === 0,
    "0 recursos http(s) fuera del origen del fixture",
    JSON.stringify(externalResources)
  );

  await page.shot("01-chat-consentimientos.png", "#chat-history-consent");
  return initial;
}

/* ------------------------------------------------------------------------- */
/* B1.4 · información clara                                                  */
/* ------------------------------------------------------------------------- */

async function testClarity(page, fixture, initial) {
  console.log("\n--- B1.4 · información clara ---");
  const label = initial.historyLabelText || "";
  const checks = {
    dosTurnos: /dos turnos/i.test(label),
    estaPestana: /esta pestaña/i.test(label),
    sinGuardado: /sin guardado automático/i.test(label),
    reenviar: /reenviar/i.test(label),
    ficticios: /fictici/i.test(label),
    objetoExplicito: /(preguntas?|respuestas?|mensajes?)/i.test(label),
  };
  record(
    "B1.4a",
    "la etiqueta dice cuántos turnos se conservan (máximo dos)",
    checks.dosTurnos,
    "texto con «dos turnos»",
    JSON.stringify(label)
  );
  record(
    "B1.4b",
    "la etiqueta dice dónde vive (solo esta pestaña) y que no hay guardado automático",
    checks.estaPestana && checks.sinGuardado,
    "«en esta pestaña» + «sin guardado automático»",
    JSON.stringify(label)
  );
  record(
    "B1.4c",
    "la etiqueta dice que el historial se reenvía",
    checks.reenviar,
    "texto con «reenviar»",
    JSON.stringify(label)
  );
  record(
    "B1.4d",
    "la etiqueta nombra explícitamente qué se conserva (preguntas/respuestas/mensajes)",
    checks.objetoExplicito,
    "término explícito sobre el contenido conservado, no solo «turnos»",
    JSON.stringify(label)
  );
  record(
    "B1.4e",
    "la etiqueta aclara que es una prueba con contenido ficticio",
    checks.ficticios,
    "texto con «ficticios»/«prueba»",
    JSON.stringify(label)
  );

  await page.navigate(`${fixture.origin}/#privacidad`);
  await waitFor(async () => await page.js("!!document.getElementById('profile-persist-toggle')"), 10000, "privacidad");
  const privacyText = await bodyText(page);
  const historyLine = (privacyText.match(/Historial:[^\n]*/) || [""])[0];
  record(
    "B1.4f",
    "la página de privacidad explica que el historial vive en memoria de la pestaña y no se guarda en almacenamiento local",
    /memoria de esta pestaña/i.test(historyLine) && /no se guarda en el almacenamiento local/i.test(historyLine),
    "línea «Historial: … memoria de esta pestaña … no se guarda en el almacenamiento local»",
    JSON.stringify(historyLine)
  );
  record(
    "B1.4g",
    "la página de privacidad dice que solo se reenvía con su propia autorización",
    /solo se reenvía con su propia autorización/i.test(historyLine),
    "frase «solo se reenvía con su propia autorización»",
    JSON.stringify(historyLine)
  );
  await page.shot("02-privacidad-historial.png", "#main-content");

  await page.navigate(`${fixture.origin}/#inicio`);
  await waitApp(page);
}

/* ------------------------------------------------------------------------- */
/* B1.5 · sin consentimiento no viaja; con consentimiento, dos turnos        */
/* ------------------------------------------------------------------------- */

async function testPayloadScope(page, fixture) {
  console.log("\n--- B1.5 · alcance de lo enviado ---");
  const turns = [];

  const t1 = await submitAndCapture(page, fixture, {
    message: Q.t1,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  record(
    "B1.5a",
    "sin consentimiento de historial el cuerpo no lleva la propiedad history",
    t1.request.body && !("history" in t1.request.body),
    "POST /api/chat sin clave history",
    JSON.stringify(payloadKeys(t1.request.body))
  );
  record(
    "B1.5b",
    "sin consentimiento de historial tampoco se envía context_consent (no se activa el mapa por arrastre)",
    t1.request.body && !("context_consent" in t1.request.body) && !("context" in t1.request.body),
    "sin context_consent ni context",
    JSON.stringify(payloadKeys(t1.request.body))
  );
  record(
    "B1.5c",
    "tras un turno sin consentimiento la memoria de historial sigue vacía",
    (await chatHistoryLength(page)) === 0,
    "PaideiaChatContext.history().length === 0",
    String(await chatHistoryLength(page))
  );

  const t2 = await submitAndCapture(page, fixture, {
    message: Q.t2,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  record(
    "B1.5d",
    "con consentimiento de historial se envía context_consent con context=false y history=true",
    t2.request.body &&
      sameJson(t2.request.body.context_consent, {
        notice_version: "paideia-chat-context-map-v1",
        context: false,
        history: true,
      }),
    "context_consent={notice_version:'paideia-chat-context-map-v1', context:false, history:true}",
    JSON.stringify(t2.request.body && t2.request.body.context_consent)
  );
  record(
    "B1.5e",
    "activar el historial no envía el mapa ni campos del perfil",
    t2.request.body && !("context" in t2.request.body) && !("detalle_economico" in t2.request.body),
    "sin propiedad context en el cuerpo",
    JSON.stringify(payloadKeys(t2.request.body))
  );
  record(
    "B1.5f",
    "en el primer turno consentido el historial viaja vacío (aún no hay turnos anteriores)",
    t2.request.body && Array.isArray(t2.request.body.history) && t2.request.body.history.length === 0,
    "history=[]",
    JSON.stringify(t2.request.body && t2.request.body.history)
  );
  await waitFor(async () => (await chatHistoryLength(page)) === 2, 5000, "historial de dos mensajes");
  turns.push({ q: Q.t2, a: t2.request.answer });
  record(
    "B1.5g",
    "tras el turno consentido la memoria guarda exactamente la pregunta y la respuesta mostradas",
    sameJson(await chatHistory(page), [
      { role: "user", content: Q.t2 },
      { role: "assistant", content: t2.request.answer },
    ]),
    "dos entradas user/assistant con el texto visible",
    JSON.stringify(await chatHistory(page))
  );
  const visibleAfterT2 = await textOf(page, "#chat-feedback");
  record(
    "B1.5h",
    "la respuesta guardada es la que se muestra en el chat",
    visibleAfterT2.includes(t2.request.answer),
    "el texto de la respuesta aparece en #chat-feedback",
    JSON.stringify(visibleAfterT2)
  );
  await page.shot("03-historial-consentido.png", "#chat-feedback");

  const t3 = await submitAndCapture(page, fixture, {
    message: Q.t3,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  record(
    "B1.5i",
    "el segundo turno reenvía el turno anterior completo y en orden",
    t3.request.body && sameJson(t3.request.body.history, [
      { role: "user", content: Q.t2 },
      { role: "assistant", content: t2.request.answer },
    ]),
    "history=[user T2, assistant respuesta de T2]",
    JSON.stringify(t3.request.body && t3.request.body.history)
  );
  turns.push({ q: Q.t3, a: t3.request.answer });

  const t4 = await submitAndCapture(page, fixture, {
    message: Q.t4,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  record(
    "B1.5j",
    "el tercer turno reenvía como máximo dos turnos (4 mensajes)",
    t4.request.body &&
      Array.isArray(t4.request.body.history) &&
      t4.request.body.history.length === 4 &&
      sameJson(messagesOf(t4.request.body.history), expectedMessages(turns.slice(-2))),
    "history con exactamente los dos turnos anteriores (4 mensajes, el más antiguo fuera)",
    JSON.stringify(t4.request.body && t4.request.body.history)
  );
  turns.push({ q: Q.t4, a: t4.request.answer });

  const t5 = await submitAndCapture(page, fixture, {
    message: Q.t5,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  const sent5 = t5.request.body && t5.request.body.history;
  record(
    "B1.5k",
    "el tope se mantiene: el turno más antiguo se descarta y no se reenvía",
    Array.isArray(sent5) &&
      sent5.length === 4 &&
      sameJson(messagesOf(sent5), expectedMessages(turns.slice(-2))) &&
      !JSON.stringify(sent5).includes(Q.t2),
    "4 mensajes = T3+T4; T2 ya no viaja",
    JSON.stringify(sent5)
  );
  record(
    "B1.5l",
    "lo reenviado coincide con texto ya mostrado (sin campos ocultos ni perfil)",
    sent5 &&
      sent5.every(
        (item) =>
          item.role === (item.content === Q.t3 || item.content === Q.t4 ? "user" : "assistant") &&
          (Object.keys(item).sort().join(",") === "content,role")
      ),
    "cada entrada solo tiene role/content y proviene de un turno visible",
    JSON.stringify(sent5)
  );
  turns.push({ q: Q.t5, a: t5.request.answer });
  await waitFor(async () => (await chatHistoryLength(page)) === 4, 5000, "historial con tope");

  return { turns, t5 };
}

/* ------------------------------------------------------------------------- */
/* B1.6 · borrado visible, inmediato y sin tocar el mapa                     */
/* ------------------------------------------------------------------------- */

async function testClear(page, fixture, turns) {
  console.log("\n--- B1.6 · borrado visible e inmediato ---");
  const storedBefore = await page.js(`localStorage.getItem(${JSON.stringify(STORAGE_KEY)})`);
  const clearVisible = await page.js(`(() => {
    const node = document.getElementById('chat-history-clear');
    if (!node) return null;
    const rect = node.getBoundingClientRect();
    return {
      text: node.textContent.trim(),
      visible: node.offsetParent !== null && rect.width > 0 && rect.height > 0,
      disabled: node.disabled,
      width: Math.round(rect.width),
      height: Math.round(rect.height),
      top: Math.round(rect.top),
    };
  })()`);
  record(
    "B1.6a",
    "«Borrar historial de esta pestaña» es un botón visible junto al formulario",
    clearVisible && clearVisible.visible && clearVisible.text === "Borrar historial de esta pestaña",
    "botón visible con ese texto exacto",
    JSON.stringify(clearVisible)
  );

  const immediate = await page.js(`(() => {
    const before = PaideiaChatContext.history().length;
    document.getElementById('chat-history-clear').click();
    return {
      before,
      after: PaideiaChatContext.history().length,
      feedback: document.getElementById('chat-feedback').textContent,
    };
  })()`);
  record(
    "B1.6b",
    "el borrado vacía la memoria de forma inmediata (mismo tick del clic)",
    immediate.before === 4 && immediate.after === 0,
    "history.length 4 → 0 en el mismo clic",
    JSON.stringify(immediate)
  );
  record(
    "B1.6c",
    "el borrado deja un mensaje visible que dice qué se borró y qué no",
    /Historial borrado de esta pestaña/i.test(immediate.feedback || "") &&
      /ya enviados al proveedor no se borran/i.test(immediate.feedback || ""),
    "mensaje «Historial borrado de esta pestaña. Los mensajes ya enviados al proveedor no se borran.»",
    JSON.stringify(immediate.feedback)
  );
  await page.shot("04-historial-borrado.png", "#chat-feedback");

  const storedAfter = await page.js(`localStorage.getItem(${JSON.stringify(STORAGE_KEY)})`);
  record(
    "B1.6d",
    "borrar el historial no toca la copia local del mapa (byte a byte)",
    storedBefore !== null && storedAfter === storedBefore,
    "paideia.profile.v2 idéntica antes y después",
    `antes=${storedBefore === null ? "null" : storedBefore.length + " bytes"} después=${storedAfter === null ? "null" : storedAfter.length + " bytes"}`
  );

  await page.navigate(`${fixture.origin}/#perfil`);
  await waitFor(async () => await page.js("!!document.querySelector('.profile-summary')"), 10000, "resumen del perfil");
  const profileText = await bodyText(page);
  const summaryText = await textOf(page, ".profile-summary");
  const profileHeading = await page.js("(document.querySelector('#page-title') || {}).textContent || ''");
  record(
    "B1.6e",
    "borrar el historial no borra el mapa en memoria: el perfil sigue mostrando sus respuestas",
    /Aprender conceptos/i.test(summaryText || "") && /Entre 1 y 3 años/i.test(summaryText || ""),
    "el resumen del perfil conserva objetivo y horizonte ficticios",
    JSON.stringify({ heading: profileHeading, summary: (summaryText || "").slice(0, 600), page: profileText.slice(0, 300) })
  );
  await page.shot("05-mapa-intacto.png", ".profile-summary");

  await page.navigate(`${fixture.origin}/#inicio`);
  await waitApp(page);
  const historyAfterNav = await chatHistoryLength(page);
  record(
    "B1.6f",
    "el historial sigue borrado tras cambiar de sección y volver al chat",
    historyAfterNav === 0,
    "history.length === 0 tras navegar",
    String(historyAfterNav)
  );

  const t6 = await submitAndCapture(page, fixture, {
    message: Q.t6,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  record(
    "B1.6g",
    "tras borrar, el siguiente turno parte limpio: no reenvía ningún mensaje anterior",
    t6.request.body &&
      Array.isArray(t6.request.body.history) &&
      t6.request.body.history.length === 0 &&
      !t6.request.raw.includes(Q.t2) &&
      !t6.request.raw.includes(Q.t3) &&
      !t6.request.raw.includes(Q.t4) &&
      !t6.request.raw.includes(Q.t5),
    "history=[] y sin marcadores anteriores en el cuerpo",
    JSON.stringify(t6.request.body && t6.request.body.history)
  );
  record(
    "B1.6h",
    "tras borrar, la memoria solo contiene el turno nuevo",
    sameJson(await chatHistory(page), [
      { role: "user", content: Q.t6 },
      { role: "assistant", content: t6.request.answer },
    ]),
    "dos entradas nuevas, sin turnos previos",
    JSON.stringify(await chatHistory(page))
  );

  return { t6, storedBefore, storedAfter };
}

/* ------------------------------------------------------------------------- */
/* B1.6 · borrado en vuelo: la respuesta en curso no resucita el historial   */
/* ------------------------------------------------------------------------- */

async function testClearInFlight(page, fixture) {
  console.log("\n--- B1.6 · borrado mientras hay una respuesta en curso ---");
  const beforeCount = fixture.state.chatRequests.length;
  const historyBefore = await chatHistory(page);
  fixture.state.queue.push({ delay: 1600, kind: "success", answer: ANSWER(6) });
  await submitChat(page, {
    message: Q.t7,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  await waitFor(() => fixture.state.chatRequests.length > beforeCount, 10000, "POST en vuelo");
  const inFlightBody = fixture.state.chatRequests[beforeCount].body;
  await sleep(300);
  const clicked = await page.js(`(() => {
    const button = document.getElementById('chat-history-clear');
    if (!button) return false;
    button.click();
    return true;
  })()`);
  const during = await chatHistoryLength(page);
  const feedbackDuring = await textOf(page, "#chat-feedback");
  const settled = await waitChatIdle(page);
  const after = await chatHistoryLength(page);

  record(
    "B1.6i",
    "el borrado se puede pulsar con una petición en vuelo y vacía la memoria al instante",
    clicked === true && during === 0,
    "clic efectivo y history.length === 0 antes de que llegue la respuesta",
    JSON.stringify({ clicked, during, feedbackDuring })
  );
  record(
    "B1.6j",
    "la respuesta que llegaba después del borrado no se vuelve a guardar (guarda de revisión)",
    after === 0,
    "history.length === 0 tras asentarse la respuesta",
    JSON.stringify({ after, settled: settled.slice(0, 200), inFlightHistory: inFlightBody.history })
  );
  record(
    "B1.6k",
    "la respuesta en vuelo se sigue mostrando, pero no queda en memoria",
    /Respuesta sintetica 6/i.test(settled || "") && after === 0,
    "texto visible de la respuesta y 0 entradas guardadas",
    JSON.stringify({ settled: settled.slice(0, 240), after })
  );

  const t8 = await submitAndCapture(page, fixture, {
    message: Q.t8,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  record(
    "B1.6l",
    "el turno siguiente al borrado en vuelo también parte limpio",
    t8.request.body && Array.isArray(t8.request.body.history) && t8.request.body.history.length === 0,
    "history=[]",
    JSON.stringify(t8.request.body && t8.request.body.history)
  );
  return t8;
}

/* ------------------------------------------------------------------------- */
/* B1.6 · desmarcar: deja de reenviar y deja de conservar                    */
/* ------------------------------------------------------------------------- */

async function testUncheck(page, fixture, previousTurn) {
  console.log("\n--- B1.6 · desmarcar el consentimiento ---");
  await waitFor(async () => (await chatHistoryLength(page)) === 2, 5000, "historial previo al desmarcado");
  const historyBefore = await chatHistory(page);
  const feedbackBefore = await textOf(page, "#chat-feedback");
  const bodyBefore = await bodyText(page);

  await setCheckbox(page, "chat-history-consent", false);
  await sleep(250);
  const feedbackAfter = await textOf(page, "#chat-feedback");
  const bodyAfter = await bodyText(page);
  const consentStates = await page.js(`(() => ({
    chat: document.getElementById('chat-consent').checked,
    context: document.getElementById('chat-context-consent').checked,
    history: document.getElementById('chat-history-consent').checked
  }))()`);

  record(
    "B1.6m",
    "desmarcar el historial no altera el consentimiento de la pregunta ni el del mapa",
    consentStates.chat === true && consentStates.context === false && consentStates.history === false,
    "chat=true, context=false, history=false",
    JSON.stringify(consentStates)
  );

  const t9 = await submitAndCapture(page, fixture, {
    message: Q.t9,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  record(
    "B1.6n",
    "tras desmarcar, el siguiente envío no lleva history ni context_consent",
    t9.request.body && !("history" in t9.request.body) && !("context_consent" in t9.request.body),
    "cuerpo sin history ni context_consent",
    JSON.stringify(payloadKeys(t9.request.body))
  );
  record(
    "B1.6o",
    "el turno enviado sin consentimiento no se añade a la memoria",
    sameJson(await chatHistory(page), historyBefore),
    "la memoria queda igual que antes del envío",
    JSON.stringify({ antes: historyBefore.length, despues: (await chatHistory(page)).length })
  );

  const uncheckExplains =
    feedbackAfter !== feedbackBefore ||
    bodyAfter.replace(/\s+/g, " ").trim() !== bodyBefore.replace(/\s+/g, " ").trim();
  record(
    "B1.6p",
    "al desmarcar, la interfaz explica en el momento que se deja de reenviar",
    uncheckExplains && /historial/i.test(feedbackAfter || ""),
    "cambio visible en #chat-feedback (o en la página) que mencione el historial al desmarcar",
    JSON.stringify({ feedbackAntes: feedbackBefore, feedbackDespues: feedbackAfter })
  );

  await page.shot("06-historial-desmarcado.png", "#chat-history-consent");

  const t10 = await submitAndCapture(page, fixture, {
    message: Q.t10,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  record(
    "B1.6q",
    "al volver a marcar, reenvía solo lo que sigue en memoria (no el turno sin consentimiento)",
    t10.request.body &&
      sameJson(messagesOf(t10.request.body.history), expectedMessages([previousTurn])) &&
      !t10.request.raw.includes(Q.t9),
    "history = turno T8; T9 no aparece",
    JSON.stringify(t10.request.body && t10.request.body.history)
  );
  return t10;
}

/* ------------------------------------------------------------------------- */
/* B1.6 · persistencia: almacenamiento, URL y logs                           */
/* ------------------------------------------------------------------------- */

async function testPersistence(page, fixture) {
  console.log("\n--- B1.6 · sin persistencia del historial ---");
  const dump = await page.js(`(async () => {
    const local = {};
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i);
      local[key] = localStorage.getItem(key);
    }
    const session = {};
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const key = sessionStorage.key(i);
      session[key] = sessionStorage.getItem(key);
    }
    let databases = null;
    try { databases = indexedDB.databases ? await indexedDB.databases() : null; } catch (_) { databases = "error"; }
    return {
      local,
      session,
      cookie: document.cookie,
      href: location.href,
      name: window.name,
      databases,
    };
  })()`);

  const serialized = JSON.stringify(dump);
  const markers = Object.values(Q).concat(
    evidence.requests.map((request) => request.answer).filter(Boolean)
  );
  const leaked = markers.filter((marker) => serialized.includes(marker));
  record(
    "B1.6r",
    "el historial no queda en localStorage, sessionStorage, cookies, URL ni IndexedDB",
    leaked.length === 0,
    "ningún marcador de pregunta o respuesta en el almacenamiento ni en la URL",
    JSON.stringify({ leaked, localKeys: Object.keys(dump.local), sessionKeys: Object.keys(dump.session), href: dump.href, cookie: dump.cookie })
  );
  record(
    "B1.6s",
    "la copia local existente es solo del mapa, no del historial",
    Object.keys(dump.local).length === 1 && Object.keys(dump.local)[0] === STORAGE_KEY,
    `una sola clave ${STORAGE_KEY}`,
    JSON.stringify(Object.keys(dump.local))
  );

  const historyBeforeReload = await chatHistoryLength(page);
  await page.reload();
  await waitApp(page);
  const historyAfterReload = await chatHistoryLength(page);
  const bodyAfterReload = await bodyText(page);
  record(
    "B1.6t",
    "recargar la pestaña pierde el historial: no se restaura desde ningún almacén",
    historyBeforeReload > 0 && historyAfterReload === 0 && !markers.some((marker) => bodyAfterReload.includes(marker)),
    "history.length === 0 y ningún marcador visible tras recargar",
    JSON.stringify({ antes: historyBeforeReload, despues: historyAfterReload })
  );

  const logLeaks = evidence.console.filter((entry) => markers.some((marker) => (entry.text || "").includes(marker)));
  record(
    "B1.6u",
    "los logs del navegador no contienen preguntas ni respuestas del historial",
    logLeaks.length === 0,
    "0 entradas de consola/log con marcadores",
    JSON.stringify({ entradas: evidence.console.length, fugas: logLeaks })
  );
  observation(
    "OBS-6u",
    "entradas de consola capturadas durante toda la sesión",
    `${evidence.console.length} entrada(s): ${JSON.stringify(evidence.console.slice(0, 8))}`
  );

  return dump;
}

/* ------------------------------------------------------------------------- */
/* B1.6 · errores del chat sin fuga de contenido                             */
/* ------------------------------------------------------------------------- */

async function testErrors(page, fixture, t10) {
  console.log("\n--- B1.6 · errores del chat ---");
  const historyBefore = await chatHistory(page);
  const requestsBefore = fixture.state.chatRequests.length;

  fixture.state.queue.push({
    status: 500,
    payload: { error: { code: "CHAT_PROVIDER_UNAVAILABLE", message: "Fallo sintetico del proveedor; no hay reintento automatico.", retryable: false } },
  });
  const t11 = await submitAndCapture(page, fixture, {
    message: Q.t11,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  const body11 = await page.js("document.body.innerText");
  record(
    "B1.7a",
    "un error 500 muestra el mensaje del servidor y no la pregunta ni el historial",
    /Fallo sintetico del proveedor/i.test(t11.feedback || "") &&
      !(t11.feedback || "").includes(Q.t11) &&
      !(t11.feedback || "").includes(Q.t10) &&
      !body11.includes(Q.t11) &&
      !body11.includes(Q.t10),
    "feedback con el mensaje de error, sin MARCA-B1-T11 ni MARCA-B1-T10 en el DOM",
    JSON.stringify({ feedback: t11.feedback, domHasT11: body11.includes(Q.t11), domHasT10: body11.includes(Q.t10) })
  );
  record(
    "B1.7b",
    "el error no añade el turno fallido a la memoria",
    sameJson(await chatHistory(page), historyBefore),
    "la memoria no cambia tras el error",
    JSON.stringify({ antes: historyBefore.length, despues: (await chatHistory(page)).length })
  );
  await page.shot("07-error-chat.png", "#chat-feedback");

  fixture.state.queue.push({ kind: "raw", status: 200, raw: '{"answer":"FUGA_MARCADOR_JSON sin cerrar' });
  const t12 = await submitAndCapture(page, fixture, {
    message: Q.t12,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  const body12 = await page.js("document.body.innerText");
  record(
    "B1.7c",
    "una respuesta malformada no vuelca su contenido ni el historial en la interfaz",
    /formato esperado/i.test(t12.feedback || "") &&
      !(t12.feedback || "").includes("FUGA_MARCADOR_JSON") &&
      !(t12.feedback || "").includes(Q.t12) &&
      !body12.includes("FUGA_MARCADOR_JSON"),
    "mensaje genérico «La respuesta del servicio local no tenía el formato esperado.»",
    JSON.stringify({ feedback: t12.feedback, domHasMarker: body12.includes("FUGA_MARCADOR_JSON") })
  );

  await page.client.send("Network.setBlockedURLs", { urls: [`${fixture.origin}${CHAT_PATH}`] });
  const networkBefore = page.networkChatPosts.length;
  const serverBefore = fixture.state.chatRequests.length;
  await submitChat(page, {
    message: Q.t13,
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  await waitFor(() => page.networkChatPosts.length > networkBefore, 10000, "intento POST bloqueado");
  const t13Feedback = await waitChatIdle(page);
  await page.client.send("Network.setBlockedURLs", { urls: [] });
  const body13 = await page.js("document.body.innerText");
  const networkAttempts = page.networkChatPosts.length - networkBefore;
  const serverAttempts = fixture.state.chatRequests.length - serverBefore;
  const serverDuringErrors = serverBefore - requestsBefore;
  record(
    "B1.7d",
    "una caída de red muestra un mensaje genérico sin pregunta ni historial",
    /No se pudo conectar con el servicio local/i.test(t13Feedback || "") &&
      !(t13Feedback || "").includes(Q.t13) &&
      !body13.includes(Q.t13) &&
      !body13.includes(Q.t12),
    "mensaje de conexión local, sin marcadores",
    JSON.stringify({ feedback: t13Feedback, networkAttempts, serverAttempts })
  );

  record(
    "B1.7e",
    "no hay reintentos automáticos: cada envío produce un único intento POST",
    networkAttempts === 1 && serverAttempts === 0 && serverDuringErrors === 2,
    "2 POST para los dos errores HTTP y 1 intento de red para la caída; ninguno se repite",
    `${serverDuringErrors} POST para 2 errores HTTP; ${networkAttempts} intento(s) de red y ${serverAttempts} petición(es) al servidor en la caída`
  );

  /* Sonda adversaria: el servidor incluido nunca manda contenido en error.message,
     pero el cliente lo renderiza tal cual. Se documenta como límite, no como fallo. */
  fixture.state.queue.push({
    status: 400,
    payload: {
      error: {
        code: "CHAT_CONTEXT_NOT_ALLOWED",
        message: `Error de prueba que repite ${Q.t10} y ${ANSWER(8)}`,
        retryable: false,
      },
    },
  });
  const echo = await submitAndCapture(page, fixture, {
    message: "MARCA-B1-T14 sonda de eco",
    consent: true,
    contextConsent: false,
    historyConsent: true,
  });
  observation(
    "OBS-7f",
    "el cliente muestra literalmente error.message del servidor (sin redacción propia)",
    echo.feedback.includes(Q.t10)
      ? "La sonda confirma que un servidor que ecoara historial en error.message lo haría visible. El servidor incluido usa mensajes estáticos (backend_services.py:344-385,426), así que no ocurre en el stack real."
      : "El cliente no mostró el eco; el mensaje se filtró o transformó."
  );

  return { t11, t12, echo, feedback13: t13Feedback };
}

/* ------------------------------------------------------------------------- */
/* B1.8 · espera agotada en el navegador y errores 429/504                   */
/* ------------------------------------------------------------------------- */

async function testUncertainTimeoutAndHttpErrors(page, fixture) {
  console.log("\n--- B1.8 · espera agotada y errores 429/504 ---");

  const beforeTimeout = fixture.state.chatRequests.length;
  fixture.state.queue.push({ delay: 14000, kind: "success", answer: ANSWER(21) });
  const started = Date.now();
  await submitChat(page, {
    message: Q.t15,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  await waitFor(() => fixture.state.chatRequests.length > beforeTimeout, 10000, "POST retenido");
  const timeoutFeedback = await waitChatIdle(page);
  const elapsed = Date.now() - started;
  const afterTimeout = await page.js(`(() => {
    const button = document.querySelector('.chat-form button[type="submit"]');
    const feedback = document.getElementById('chat-feedback');
    return {
      text: document.getElementById('chat-message').value,
      button: button ? button.textContent : null,
      disabled: button ? button.disabled : null,
      role: feedback ? feedback.getAttribute('role') : null,
      live: feedback ? feedback.getAttribute('aria-live') : null,
    };
  })()`);
  const postsAtTimeout = fixture.state.chatRequests.length;
  await sleep(2500);
  const postsAfterWait = fixture.state.chatRequests.length;

  record(
    "B1.8a",
    "una espera retenida más de 12 s termina con aviso de estado incierto, no con «no enviado»",
    elapsed >= 11000 && elapsed <= 16000 &&
      /pudo llegar al servidor y al proveedor/i.test(timeoutFeedback || "") &&
      /no se sabe si el turno llegó a completarse/i.test(timeoutFeedback || "") &&
      !/no se ha enviado|no se envió/i.test(timeoutFeedback || ""),
    "aviso de incertidumbre tras 12 s, sin afirmar que no se envió",
    JSON.stringify({ elapsed, feedback: timeoutFeedback })
  );
  record(
    "B1.8b",
    "la pregunta retenida sigue en el campo y el botón queda disponible como reenvío manual",
    afterTimeout.text === Q.t15 && afterTimeout.disabled === false && afterTimeout.button === "Reenviar pregunta",
    "texto intacto, botón habilitado y etiquetado «Reenviar pregunta»",
    JSON.stringify(afterTimeout)
  );
  record(
    "B1.8c",
    "el aviso de espera agotada se anuncia como alerta y no provoca un POST adicional",
    afterTimeout.role === "alert" && afterTimeout.live === "assertive" && postsAfterWait === postsAtTimeout && postsAtTimeout === beforeTimeout + 1,
    "role=alert, aria-live=assertive y exactamente 1 POST para el envío",
    JSON.stringify({ postsAtTimeout, postsAfterWait, role: afterTimeout.role, live: afterTimeout.live })
  );

  /* B1.9 · regresiones del ciclo 2: el aviso sigue al mensaje exacto enviado */
  await page.js(`(() => {
    const message = document.getElementById('chat-message');
    message.value = ${JSON.stringify(Q.t18)};
    message.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  const afterEdit = await page.js(`(() => {
    const button = document.querySelector('.chat-form button[type="submit"]');
    const feedback = document.getElementById('chat-feedback');
    return {
      text: document.getElementById('chat-message').value,
      button: button ? button.textContent : null,
      feedback: feedback ? feedback.textContent : '',
    };
  })()`);
  record(
    "B1.9a",
    "editar tras un timeout retira el aviso obsoleto y no presenta la pregunta nueva como reenvío",
    afterEdit.button === "Enviar pregunta" &&
      afterEdit.text === Q.t18 &&
      !/La pregunta se conserva|Se mantiene el turno en cola|mismo ticket/i.test(afterEdit.feedback) &&
      /envío anterior|pregunta anterior/i.test(afterEdit.feedback) &&
      /no se ha enviado|todavía no se ha enviado/i.test(afterEdit.feedback),
    "botón «Enviar pregunta», texto nuevo en el campo y aviso referido al envío anterior",
    JSON.stringify(afterEdit)
  );

  await page.navigate(`${fixture.origin}/#privacidad`);
  await page.navigate(`${fixture.origin}/#inicio`);
  await waitFor(async () => await page.js("!!document.getElementById('chat-message')"), 10000, "chat tras navegar");
  const afterNavigate = await page.js(`(() => {
    const button = document.querySelector('.chat-form button[type="submit"]');
    const feedback = document.getElementById('chat-feedback');
    return {
      text: document.getElementById('chat-message').value,
      button: button ? button.textContent : null,
      feedback: feedback ? feedback.textContent : '',
    };
  })()`);
  record(
    "B1.9b",
    "al volver a la página, la pregunta editada sigue sin etiquetarse como reenvío ni como conservada",
    afterNavigate.button === "Enviar pregunta" &&
      afterNavigate.text === Q.t18 &&
      !/Reenviar pregunta|La pregunta se conserva|Se mantiene el turno en cola|mismo ticket/i.test(afterNavigate.feedback) &&
      /envío anterior|pregunta anterior/i.test(afterNavigate.feedback) &&
      /no se ha enviado|todavía no se ha enviado/i.test(afterNavigate.feedback),
    "botón «Enviar pregunta» y aviso del envío anterior tras volver a inicio",
    JSON.stringify(afterNavigate)
  );

  const before429 = fixture.state.chatRequests.length;
  fixture.state.queue.push({
    status: 429,
    payload: { error: { code: "CHAT_RATE_LIMITED", message: "No se pudo completar la llamada al proveedor; no hay reintento automático." } },
  });
  const r429 = await submitAndCapture(page, fixture, {
    message: Q.t16,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  const text429 = await page.js("document.getElementById('chat-message').value");
  record(
    "B1.8d",
    "un 429 se muestra como límite de uso, distinto de un timeout, y conserva la pregunta",
    /límite de uso \(429\)/i.test(r429.feedback || "") &&
      /no es un timeout/i.test(r429.feedback || "") &&
      !/tiempo de espera/i.test(r429.feedback || "") &&
      text429 === Q.t16 &&
      fixture.state.chatRequests.length === before429 + 1,
    "mensaje de límite 429, sin lenguaje de timeout, y un solo POST",
    JSON.stringify({ feedback: r429.feedback, text: text429, posts: fixture.state.chatRequests.length - before429 })
  );

  const before504 = fixture.state.chatRequests.length;
  fixture.state.queue.push({
    status: 504,
    payload: { error: { code: "CHAT_TIMEOUT", message: "No se pudo completar la llamada al proveedor; no hay reintento automático." } },
  });
  const r504 = await submitAndCapture(page, fixture, {
    message: Q.t17,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  const text504 = await page.js("document.getElementById('chat-message').value");
  record(
    "B1.8e",
    "un 504 se muestra como timeout del proveedor con estado no confirmado, y conserva la pregunta",
    /tiempo de espera \(504\)/i.test(r504.feedback || "") &&
      /pudo llegar al proveedor/i.test(r504.feedback || "") &&
      /no está confirmado/i.test(r504.feedback || "") &&
      (r504.feedback || "") !== (r429.feedback || "") &&
      text504 === Q.t17 &&
      fixture.state.chatRequests.length === before504 + 1,
    "mensaje de timeout 504, distinto del 429, y un solo POST",
    JSON.stringify({ feedback: r504.feedback, text: text504, posts: fixture.state.chatRequests.length - before504 })
  );

  /* Editar mientras el turno anterior sigue en vuelo: el aviso debe hablar del
     envío anterior, no afirmar que la pregunta que queda en el cuadro se conserva. */
  const beforeInFlight = fixture.state.chatRequests.length;
  fixture.state.queue.push({
    delay: 700,
    status: 504,
    payload: { error: { code: "CHAT_TIMEOUT", message: "No se pudo completar la llamada al proveedor; no hay reintento automático." } },
  });
  await submitChat(page, {
    message: Q.t21,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  await waitFor(() => fixture.state.chatRequests.length > beforeInFlight, 10000, "POST en vuelo B1.9");
  await page.js(`(() => {
    const message = document.getElementById('chat-message');
    message.value = ${JSON.stringify(Q.t22)};
    message.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  const inFlightFeedback = await waitChatIdle(page);
  const afterInFlightEdit = await page.js(`(() => {
    const button = document.querySelector('.chat-form button[type="submit"]');
    const feedback = document.getElementById('chat-feedback');
    return {
      text: document.getElementById('chat-message').value,
      button: button ? button.textContent : null,
      feedback: feedback ? feedback.textContent : '',
      active: document.activeElement ? document.activeElement.id || document.activeElement.tagName : null,
    };
  })()`);
  record(
    "B1.9c",
    "si se edita durante el vuelo, el timeout no afirma que la pregunta anterior se conserva",
    afterInFlightEdit.text === Q.t22 &&
      afterInFlightEdit.button === "Enviar pregunta" &&
      /envío anterior|pregunta enviada/i.test(inFlightFeedback) &&
      /no se ha enviado|todavía no se ha enviado/i.test(inFlightFeedback) &&
      !/La pregunta se conserva/i.test(inFlightFeedback),
    "texto B en el campo, botón «Enviar pregunta» y aviso que distingue el envío anterior",
    JSON.stringify({ feedback: inFlightFeedback, ...afterInFlightEdit })
  );

  /* Un ticket usado en un intento que pierde la espera pudo quedar reclamado y
     cerrado: no se conserva como si siguiera en cola ni se adjunta al siguiente envío. */
  fixture.state.queue.push({
    status: 202,
    payload: { status: "queued", queue: { ticket: "d".repeat(32), position: 2, code: "queued" }, provider_mode: "external" },
  });
  const beforeQueued = fixture.state.chatRequests.length;
  await submitChat(page, {
    message: Q.t23,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  await waitFor(() => fixture.state.chatRequests.length > beforeQueued, 10000, "POST de 202");
  await waitFor(
    async () => (await page.js("(document.querySelector('.chat-form button[type=\"submit\"]') || {}).textContent")) === "Reenviar turno en cola",
    10000,
    "202 procesado"
  );
  const queued = await page.js(`(() => {
    const button = document.querySelector('.chat-form button[type="submit"]');
    const feedback = document.getElementById('chat-feedback');
    return { button: button ? button.textContent : null, feedback: feedback ? feedback.textContent : "" };
  })()`);
  fixture.state.queue.push({ delay: 14000, kind: "success", answer: ANSWER(22) });
  const beforeQueuedTimeout = fixture.state.chatRequests.length;
  await submitChat(page, {
    message: Q.t23,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  await waitFor(() => fixture.state.chatRequests.length > beforeQueuedTimeout, 10000, "POST de ticket retenido");
  const queuedTimeoutFeedback = await waitChatIdle(page);
  const queuedAfterTimeout = await page.js(`(() => {
    const button = document.querySelector('.chat-form button[type="submit"]');
    const feedback = document.getElementById('chat-feedback');
    return { text: document.getElementById('chat-message').value, button: button ? button.textContent : null, feedback: feedback ? feedback.textContent : "" };
  })()`);
  const queuedResendRequest = fixture.state.chatRequests[beforeQueuedTimeout];
  record(
    "B1.9d",
    "el ticket de un envío sin confirmar no se presenta como cola válida ni promete reutilización",
    queued.button === "Reenviar turno en cola" &&
      queuedAfterTimeout.text === Q.t23 &&
      queuedAfterTimeout.button === "Reenviar pregunta" &&
      queuedResendRequest.body.ticket === "d".repeat(32) &&
      !/Se mantiene el turno en cola|mismo ticket/i.test(queuedTimeoutFeedback) &&
      /no se reutiliza/i.test(queuedTimeoutFeedback) &&
      /podría duplicar|podrías duplicar/i.test(queuedTimeoutFeedback) &&
      /rechazad/i.test(queuedTimeoutFeedback),
    "el intento usa el ticket, pero tras el timeout se descarta y se avisa de duplicado o rechazo",
    JSON.stringify({ queued, feedback: queuedTimeoutFeedback, after: queuedAfterTimeout })
  );

  const beforeAfterTicket = fixture.state.chatRequests.length;
  fixture.state.queue.push({ kind: "success", answer: ANSWER(23) });
  await submitChat(page, {
    message: Q.t23,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  await waitFor(() => fixture.state.chatRequests.length > beforeAfterTicket, 10000, "POST posterior al ticket");
  await waitChatIdle(page);
  const afterTicketRequest = fixture.state.chatRequests[beforeAfterTicket];
  record(
    "B1.9e",
    "un reenvío manual posterior no adjunta el ticket posiblemente consumido",
    afterTicketRequest.body && !("ticket" in afterTicketRequest.body),
    "el POST posterior no contiene ticket",
    JSON.stringify({ keys: afterTicketRequest.body ? Object.keys(afterTicketRequest.body) : null })
  );

  /* send_state es por intento de transporte: ni not_started ni completed
     demuestran el resultado del turno completo. */
  const beforeNotStarted = fixture.state.chatRequests.length;
  fixture.state.queue.push({
    status: 504,
    payload: { error: { code: "CHAT_TIMEOUT", message: "No se pudo completar la llamada al proveedor.", send_state: "not_started" } },
  });
  const rNotStarted = await submitAndCapture(page, fixture, {
    message: Q.t19,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  record(
    "B1.9f",
    "un 504 con not_started no afirma que el turno entero no se enviara",
    !/no llegó a recibir|no se envió|no se ha enviado/i.test(rNotStarted.feedback || "") &&
      /no iniciado/i.test(rNotStarted.feedback || "") &&
      /no demuestra|no confirma/i.test(rNotStarted.feedback || "") &&
      fixture.state.chatRequests.length === beforeNotStarted + 1,
    "menciona el intento no iniciado y advierte de que no demuestra el resultado del turno",
    JSON.stringify({ feedback: rNotStarted.feedback, posts: fixture.state.chatRequests.length - beforeNotStarted })
  );

  const beforeCompleted = fixture.state.chatRequests.length;
  fixture.state.queue.push({
    status: 504,
    payload: { error: { code: "CHAT_TIMEOUT", message: "No se pudo completar la llamada al proveedor.", send_state: "completed" } },
  });
  const rCompleted = await submitAndCapture(page, fixture, {
    message: Q.t20,
    consent: true,
    contextConsent: false,
    historyConsent: false,
  });
  record(
    "B1.9g",
    "un 504 con completed no afirma que el proveedor procesara el turno",
    !/llegó completa|procesó|procesad[oa]/i.test(rCompleted.feedback || "") &&
      /completado/i.test(rCompleted.feedback || "") &&
      /no confirma|no demuestra/i.test(rCompleted.feedback || "") &&
      fixture.state.chatRequests.length === beforeCompleted + 1,
    "menciona el intento completado y advierte de que no confirma el procesamiento",
    JSON.stringify({ feedback: rCompleted.feedback, posts: fixture.state.chatRequests.length - beforeCompleted })
  );

  /* El foco del botón enviado no debe caer en BODY al deshabilitarlo. */
  fixture.state.queue.push({ delay: 600, kind: "success", answer: ANSWER(24) });
  const beforeFocus = fixture.state.chatRequests.length;
  await page.js(`(() => {
    const message = document.getElementById('chat-message');
    message.value = ${JSON.stringify(Q.t24)};
    message.dispatchEvent(new Event('input', { bubbles: true }));
    const button = document.querySelector('.chat-form button[type="submit"]');
    button.focus();
    document.querySelector('.chat-form').requestSubmit();
  })()`);
  await waitFor(() => fixture.state.chatRequests.length > beforeFocus, 10000, "POST de foco");
  const focusDuring = await page.js(`(() => {
    const active = document.activeElement;
    return { id: active ? active.id : null, tag: active ? active.tagName : null };
  })()`);
  await waitChatIdle(page);
  const focusAfter = await page.js(`(() => {
    const active = document.activeElement;
    return { id: active ? active.id : null, tag: active ? active.tagName : null };
  })()`);
  record(
    "B1.9h",
    "al deshabilitar el botón durante el envío el foco no queda en BODY",
    focusDuring.tag !== "BODY" && focusDuring.tag !== null &&
      focusAfter.tag !== "BODY" && focusAfter.tag !== null,
    "el foco permanece en un control del chat durante y después del envío",
    JSON.stringify({ during: focusDuring, after: focusAfter })
  );
}

/* ------------------------------------------------------------------------- */
/* B1.3 · proveedor sin capacidad de historial                               */
/* ------------------------------------------------------------------------- */

async function testCapabilityDisabled(browser, fixture) {
  console.log("\n--- B1.3 · proveedor sin capacidad de historial ---");
  const page = await browser.newPage();
  try {
    await page.navigate(`${fixture.origin}/#inicio`);
    await page.navigate(`${fixture.origin}/#inicio`);
    await waitFor(async () => await page.js("!!document.getElementById('chat-consent')"), 15000, "chat renderizado");
    await waitFor(
      async () => {
        const text = await page.js("(document.getElementById('status-chip') || {}).textContent || ''");
        return !/Comprobando/i.test(text);
      },
      15000,
      "estado"
    );
    await waitFor(
      async () => await page.js("!!document.getElementById('chat-history-consent')"),
      10000,
      "control de historial"
    );
    const state = await page.js(`(() => {
      const history = document.getElementById('chat-history-consent');
      return {
        checked: history.checked,
        disabled: history.disabled,
        note: (document.getElementById('chat-context-capabilities') || {}).textContent || '',
      };
    })()`);
    record(
      "B1.3g",
      "si el proveedor no ofrece historial, la casilla está desactivada y desmarcada",
      state.checked === false && state.disabled === true,
      "checked=false y disabled=true",
      JSON.stringify(state)
    );
    record(
      "B1.3h",
      "el aviso de capacidades dice «historial: desactivado»",
      /historial:\s*desactivado/i.test(state.note || ""),
      "«historial: desactivado»",
      JSON.stringify(state.note)
    );
    await page.shot("08-historial-no-disponible.png", "#chat-history-consent");
  } finally {
    try {
      await browser.browser.send("Target.closeTarget", { targetId: page.targetId }, 5000);
    } catch {
      /* noop */
    }
    page.client.close();
  }
}

/* ------------------------------------------------------------------------- */
/* Evidencia HTTP resumida                                                   */
/* ------------------------------------------------------------------------- */

function printHttpEvidence() {
  console.log("\n--- Evidencia HTTP (cuerpos POST /api/chat) ---");
  for (const request of evidence.requests) {
    const body = request.body || {};
    const summary = {
      seq: request.seq,
      message: body.message ? `${String(body.message).slice(0, 44)}…` : null,
      keys: payloadKeys(body),
      history_len: Array.isArray(body.history) ? body.history.length : null,
      history_messages: Array.isArray(body.history)
        ? body.history.map((item) => `${item.role}:${String(item.content).slice(0, 34)}`)
        : null,
      context_consent: body.context_consent || null,
      has_context: "context" in body,
      result: request.step,
    };
    console.log(JSON.stringify(summary));
  }
  const requestFile = path.join(SHOTS, "b1_http_evidence.json");
  fs.writeFileSync(requestFile, JSON.stringify(evidence.requests, null, 2));
  evidence.requests_file = requestFile;
  console.log(`Cuerpos completos: ${requestFile}`);
}

/* ------------------------------------------------------------------------- */
/* Main                                                                      */
/* ------------------------------------------------------------------------- */

async function main() {
  fs.mkdirSync(SHOTS, { recursive: true });
  evidence.app_js_sha256 = sha256(APP_JS);
  evidence.app_js_mtime = fs.statSync(APP_JS).mtime.toISOString();
  evidence.source_app_js_sha256 = sha256(path.join(REPO_STATIC_ROOT, "app.js"));
  evidence.source_static_root = REPO_STATIC_ROOT;
  console.log(
    `app.js medido: sha256=${evidence.app_js_sha256} mtime=${evidence.app_js_mtime} root=${STATIC_ROOT}`
  );
  if (evidence.source_app_js_sha256 !== evidence.app_js_sha256) {
    console.log(
      `AVISO: la copia medida no coincide con api/_static (${evidence.source_app_js_sha256}). ` +
        "La medición corresponde a la instantánea congelada, no al árbol vivo."
    );
  }

  let browser = null;
  let fixture = null;
  let disabledFixture = null;
  try {
    browser = await launchBrowser();
    recordHarness("H-0a", "Chromium headless arranca y expone CDP", true, `pid=${browser.child.pid}`);

    fixture = await startFixture();
    recordHarness("H-0b", "fixture loopback sirve la app y la API ficticia", true, fixture.origin);

    disabledFixture = await startFixture({ status: fixtureStatus(false) });
    recordHarness("H-0c", "segundo fixture con historial no disponible", true, disabledFixture.origin);

    const page = await browser.newPage();
    const initial = await testDefaultsAndSeparation(page, fixture);
    await testClarity(page, fixture, initial);
    const scope = await testPayloadScope(page, fixture);
    const clear = await testClear(page, fixture, scope.turns);
    const afterFlight = await testClearInFlight(page, fixture);
    const afterUncheck = await testUncheck(page, fixture, { q: Q.t8, a: afterFlight.request.answer });
    await testErrors(page, fixture, afterUncheck);
    await testPersistence(page, fixture);
    await testUncertainTimeoutAndHttpErrors(page, fixture);
    await testCapabilityDisabled(browser, disabledFixture);

    printHttpEvidence();

    evidence.app_js_sha256_end = sha256(APP_JS);
    evidence.changed_during_test = evidence.app_js_sha256_end !== evidence.app_js_sha256;
    if (evidence.changed_during_test) {
      console.log(
        `\nAVISO: app.js cambió durante la prueba (${evidence.app_js_sha256} → ${evidence.app_js_sha256_end}). ` +
          "Repetir la medición."
      );
    }
    const reportFile = path.join(SHOTS, "b1_evidence.json");
    evidence.finished_at = new Date().toISOString();
    fs.writeFileSync(reportFile, JSON.stringify(evidence, null, 2));
    console.log(`Evidencia: ${reportFile}`);
    console.log(`Capturas: ${SHOTS}`);
    if (clear.storedBefore === null || clear.storedAfter === null) {
      console.log("AVISO: el mapa no estaba sembrado al medir el borrado.");
    }
  } catch (error) {
    recordHarness("H-0z", "el arnés terminó sin excepción", false, error.stack || String(error));
    evidence.app_js_sha256_end = sha256(APP_JS);
  } finally {
    if (browser) await browser.close();
    if (fixture) await fixture.close();
    if (disabledFixture) await disabledFixture.close();
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
