#!/usr/bin/env node
"use strict";

/*
 * B8 — pruebas conductuales de privacidad.
 *
 * Este archivo es SOLO de prueba: no importa ni modifica código de producción,
 * no lee .env y no usa red externa. Todo ocurre en 127.0.0.1.
 *
 * Qué demuestra:
 *   B8-1  El aviso visible debe coincidir con lo que se envía: con consentimiento
 *         de contexto y campos marcados el navegador manda solo esos campos en
 *         POST /api/chat; el texto no puede negar el envío del mapa.
 *   B8-2  Con la IA pública deshabilitada (servidor WSGI real, /api/chat -> 405)
 *         la interfaz no debe hacer POST y el aviso «no se envía nada» debe ser
 *         coherente con el tráfico real.
 *   B8-3  Borrar el perfil no borra el historial del chat; el diálogo y la página
 *         de privacidad deben delimitar ese alcance y mencionar lo ya enviado
 *         al proveedor.
 *   B8-4  Dos pestañas del mismo origen: tras borrar en A, el evento storage
 *         desactiva el autoguardado de B y la copia no resucita; A no puede
 *         seguir afirmando «Copia local borrada» si la clave reapareciera.
 *
 * Uso:
 *   node tests/b8_privacy_regression.test.cjs
 *   PYTHON=/ruta/python CHROME_PATH=/ruta/chrome node tests/b8_privacy_regression.test.cjs
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
const PROFILE_MODEL = require(path.join(STATIC_ROOT, "profile_model.js"));

const STORAGE_KEY = "paideia.profile.v2";
const CHAT_PATH = "/api/chat";
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/* ------------------------------------------------------------------------- */
/* Resultados                                                                */
/* ------------------------------------------------------------------------- */

const results = [];

function record(id, title, pass, expected, actual) {
  results.push({ id, title, pass, expected, actual });
  const tag = pass ? "PASS" : "FAIL";
  console.log(`${tag} ${id} — ${title}`);
  if (!pass) {
    console.log(`     esperado: ${expected}`);
    console.log(`     real:     ${actual}`);
  }
}

function recordHarness(id, title, pass, detail) {
  results.push({ id, title, pass, harness: true, actual: detail });
  const tag = pass ? "PASS" : "HARNESS-FAIL";
  console.log(`${tag} ${id} — ${title}`);
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
    console.log("ESTADO: VERDE — no se reprodujeron los defectos B8.");
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
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "b8-privacy-chrome-"));
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
  if (!outcome.ok) {
    throw new Error(`No se encontró el control «${text}». Visibles: ${outcome.visible.join(" | ")}`);
  }
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

async function storageValue(page) {
  return page.js(`localStorage.getItem(${JSON.stringify(STORAGE_KEY)})`);
}

async function waitStorage(page, present, timeout = 8000) {
  await waitFor(
    async () => {
      const value = await storageValue(page);
      return present ? value !== null : value === null;
    },
    timeout,
    present ? "clave local escrita" : "clave local borrada"
  );
}

async function enableAndSaveProfile(page, origin) {
  await page.navigate(`${origin}/#privacidad`);
  await waitFor(async () => await page.js("!!document.getElementById('profile-persist-toggle')"), 10000, "privacidad");
  const disabled = await page.js("document.getElementById('profile-persist-toggle').disabled");
  if (disabled) throw new Error("El interruptor de guardado está desactivado: el perfil no cargó");
  await setCheckbox(page, "profile-persist-toggle", true);
  await clickText(page, "Guardar perfil local");
  await waitStorage(page, true);
}

/* ------------------------------------------------------------------------- */
/* Servidor fixture (solo loopback, datos ficticios)                          */
/* ------------------------------------------------------------------------- */

function fixtureStatus() {
  return {
    mode: "local_prototype",
    ai: {
      connected: true,
      status: "configured_not_verified",
      message: "Proveedor ficticio de prueba; sin red externa.",
      capabilities: {
        context: true,
        history: true,
        synthetic_only: false,
        structured_education: false,
      },
      quota: { calls_day: 0, calls_per_day: 20 },
    },
    catalogue: { candidate_count: 3, publication_ready: 0 },
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
  const statusPayload = options.status || fixtureStatus();
  const state = { chatRequests: [] };
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
      state.chatRequests.push({ raw, body, at: Date.now() });
      sendJson(200, {
        provider_mode: "test_only",
        external_sent: false,
        answer: "Respuesta sintética ficticia. No es una IA real.",
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
/* Servidor WSGI real (API pública), sin modificar archivos                  */
/* ------------------------------------------------------------------------- */

async function startRealServer() {
  const python = process.env.PYTHON || "python";
  const script = [
    "import sys, os, socketserver",
    "sys.path.insert(0, os.path.join(os.getcwd(), 'api'))",
    "import index",
    "from wsgiref.simple_server import make_server, WSGIServer",
    "class S(socketserver.ThreadingMixIn, WSGIServer):",
    "    daemon_threads = True",
    "class L:",
    "    def __init__(self, app): self.app = app",
    "    def __call__(self, env, sr):",
    "        print('REQ %s %s' % (env.get('REQUEST_METHOD'), env.get('PATH_INFO')), flush=True)",
    "        return self.app(env, sr)",
    "httpd = make_server('127.0.0.1', 0, L(index.app), server_class=S)",
    "print('PORT %d' % httpd.server_port, flush=True)",
    "httpd.serve_forever()",
  ].join("\n");

  const child = spawn(python, ["-u", "-c", script], {
    cwd: ROOT,
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  let stdout = "";
  let stderr = "";
  const requests = [];
  let port = null;

  const consume = (chunk) => {
    stdout += chunk.toString();
    const lines = stdout.split(/\r?\n/);
    stdout = lines.pop() || "";
    for (const line of lines) {
      const portMatch = /^PORT (\d+)$/.exec(line.trim());
      if (portMatch) port = Number(portMatch[1]);
      const requestMatch = /^REQ (\S+) (\S+)$/.exec(line.trim());
      if (requestMatch) requests.push({ method: requestMatch[1], path: requestMatch[2] });
    }
  };
  child.stdout.on("data", consume);
  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
    if (stderr.length > 20000) stderr = stderr.slice(-20000);
  });

  await waitFor(() => port, 15000, `arranque WSGI real (${python})`);
  return {
    origin: `http://127.0.0.1:${port}`,
    requests,
    close: () =>
      new Promise((resolve) => {
        try {
          child.kill();
        } catch {
          /* noop */
        }
        setTimeout(resolve, 300);
      }),
    stderr: () => stderr,
  };
}

/* ------------------------------------------------------------------------- */
/* Acciones de producto                                                      */
/* ------------------------------------------------------------------------- */

async function submitChat(page, options) {
  const {
    message,
    consent = true,
    contextConsent = false,
    historyConsent = false,
    fields = [],
  } = options;
  await page.js(`(() => {
    const message = document.getElementById('chat-message');
    message.value = ${JSON.stringify(message)};
    message.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  await setCheckbox(page, "chat-consent", consent);
  for (const id of fields) await setCheckbox(page, id, true);
  await setCheckbox(page, "chat-context-consent", contextConsent);
  await setCheckbox(page, "chat-history-consent", historyConsent);
  await page.js("document.querySelector('.chat-form').requestSubmit()");
}

async function waitChatResponse(page) {
  await waitFor(
    async () => {
      const text = await page.js("(document.getElementById('chat-feedback') || {}).textContent || ''");
      return text.length > 0 && !/Intentando contactar/i.test(text);
    },
    10000,
    "respuesta del chat"
  );
}

async function chatHistoryLength(page) {
  return page.js("(window.PaideiaChatContext && PaideiaChatContext.history().length) || 0");
}

/* ------------------------------------------------------------------------- */
/* B8-2: IA pública deshabilitada no debe hacer POST                        */
/* ------------------------------------------------------------------------- */

async function testDisabledPublicChat(browser, real) {
  console.log("\n--- B8-2 · IA pública deshabilitada ---");
  const page = await browser.newPage();
  try {
    await page.navigate(`${real.origin}/#inicio`);
    await waitApp(page);
    await waitFor(
      async () => {
        const note = await textOf(page, "#chat-provider-note");
        return note && note.includes("no se envía nada");
      },
      10000,
      "aviso de IA no configurada"
    );

    const note = await textOf(page, "#chat-provider-note");
    const contextConsentDisabled = await page.js("document.getElementById('chat-context-consent').disabled");
    const historyConsentDisabled = await page.js("document.getElementById('chat-history-consent').disabled");
    const before = real.requests.filter((item) => item.method === "POST" && item.path === CHAT_PATH).length;

    recordHarness(
      "H-2a",
      "el servidor WSGI real responde y la interfaz ve la IA deshabilitada",
      /no se envía nada/.test(note || "") && contextConsentDisabled && historyConsentDisabled,
      `note=${JSON.stringify(note)} contextDisabled=${contextConsentDisabled} historyDisabled=${historyConsentDisabled}`
    );

    await submitChat(page, { message: "Pregunta ficticia sin IA pública.", consent: true });
    await sleep(900);

    const after = real.requests.filter((item) => item.method === "POST" && item.path === CHAT_PATH);
    const feedback = await textOf(page, "#chat-feedback");
    const postCount = after.length - before;

    record(
      "B8-2a",
      "con IA pública deshabilitada, «Enviar pregunta» no hace POST al servidor",
      postCount === 0,
      "0 peticiones POST /api/chat; el aviso dice que no se envía nada",
      `${postCount} petición(es) POST /api/chat; feedback=${JSON.stringify(feedback)}`
    );
    record(
      "OBS-2b",
      "observación: el aviso «no se envía nada» es coherente porque no hubo POST",
      postCount === 0 && /no se envía nada/.test(note || ""),
      "el aviso no se contradice con el tráfico real",
      `note=${JSON.stringify(note)}; POST reales=${postCount}`
    );
    if (after.length) {
      console.log(`     evidencia: ${JSON.stringify(after)}`);
    }
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
/* B8-1: aviso de mapa frente a campos realmente enviados                    */
/* ------------------------------------------------------------------------- */

async function testStatusWithoutAi(browser, fixture) {
  console.log("\n--- B8-2b · estado sin bloque de IA (fail-closed) ---");
  const page = await browser.newPage();
  try {
    await page.navigate(`${fixture.origin}/#inicio`);
    await waitApp(page);
    await waitFor(
      async () => {
        const note = await textOf(page, "#chat-provider-note");
        return note && note.length > 0 && !/Comprobando/.test(note);
      },
      10000,
      "aviso del chat con estado incompleto"
    );
    const note = await textOf(page, "#chat-provider-note");
    const before = fixture.state.chatRequests.length;
    await submitChat(page, { message: "Pregunta ficticia con estado incompleto.", consent: true });
    await sleep(900);
    const postCount = fixture.state.chatRequests.length - before;
    record(
      "B8-2b",
      "un /api/status sin bloque ai no habilita el envío",
      postCount === 0 && /no se envía nada/.test(note || ""),
      "0 peticiones POST /api/chat y aviso «no se envía nada»",
      `${postCount} petición(es); note=${JSON.stringify(note)}`
    );
    if (fixture.state.chatRequests.length) {
      console.log(`     evidencia: ${JSON.stringify(fixture.state.chatRequests.map((item) => item.body))}`);
    }
  } finally {
    try {
      await browser.browser.send("Target.closeTarget", { targetId: page.targetId }, 5000);
    } catch {
      /* noop */
    }
    page.client.close();
  }
}

async function testMapNoticeVsPayload(browser, fixture) {
  console.log("\n--- B8-1 · mapa: aviso visible vs cuerpo enviado ---");
  const page = await browser.newPage();
  try {
    await openFresh(page, fixture.origin);
    await seedProfile(page);
    fixture.state.chatRequests.length = 0;

    // El resumen del perfil también hace una afirmación absoluta.
    await page.navigate(`${fixture.origin}/#perfil`);
    await waitFor(async () => await page.js("!!document.querySelector('.profile-summary')"), 10000, "resumen del perfil");
    const summaryText = await bodyText(page);
    const summaryDeniesMap = summaryText.includes("Este mapa no se envía al chat");

    await page.navigate(`${fixture.origin}/#inicio`);
    await waitApp(page);
    await waitFor(
      async () => await page.js("document.getElementById('chat-context-field-0') && !document.getElementById('chat-context-field-0').disabled"),
      10000,
      "campo de contexto habilitado"
    );

    const consentText = await page.js(
      "document.getElementById('chat-consent').closest('label').textContent"
    );
    const warningTexts = await page.js(
      "[...document.querySelectorAll('.warning-note')].map((node) => node.textContent).join(' || ')"
    );
    const consentDeniesMap = /No se enviará mi mapa de perfil/i.test(consentText || "");
    const calloutSaysSelected = /se envían solo los campos que selecciones/i.test(warningTexts || "");
    const fieldValue = await page.js(
      "document.getElementById('chat-context-field-0').closest('label').textContent"
    );

    recordHarness(
      "H-1a",
      "el chat carga perfil ficticio y ofrece el campo de mapa seleccionable",
      Boolean(fieldValue && fieldValue.includes("Objetivo")),
      `campo=${JSON.stringify(fieldValue)}`
    );

    const externalResources = await page.js(
      "performance.getEntriesByType('resource').map((entry) => entry.name).filter((name) => /^https?:/.test(name) && !name.startsWith(location.origin))"
    );
    recordHarness(
      "H-1b",
      "la página no carga recursos externos (solo mismo origen loopback)",
      Array.isArray(externalResources) && externalResources.length === 0,
      JSON.stringify(externalResources)
    );

    // Sin consentimiento de chat no debe salir ninguna petición, aunque el campo esté marcado.
    const postsBeforeNoConsent = fixture.state.chatRequests.length;
    await submitChat(page, {
      message: "Pregunta ficticia B8 sin consentimiento de chat.",
      consent: false,
      contextConsent: false,
      fields: ["chat-context-field-0"],
    });
    await sleep(350);
    const noConsentPosts = fixture.state.chatRequests.length - postsBeforeNoConsent;
    record(
      "B8-1a0",
      "sin consentimiento de chat no hay POST aunque haya un campo del mapa marcado",
      noConsentPosts === 0,
      "0 peticiones POST /api/chat sin la casilla de consentimiento",
      `${noConsentPosts} petición(es) POST /api/chat`
    );

    // Primer envío: campo marcado pero SIN consentimiento de contexto.
    await submitChat(page, {
      message: "Pregunta ficticia B8 sin contexto.",
      consent: true,
      contextConsent: false,
      fields: ["chat-context-field-0"],
    });
    await waitFor(() => fixture.state.chatRequests.length >= 1, 10000, "primer POST de chat");
    await waitChatResponse(page);
    const firstBody = fixture.state.chatRequests[0].body;

    record(
      "B8-1a",
      "sin consentimiento de contexto no se envía ningún campo del mapa",
      Boolean(firstBody) && firstBody.context === undefined,
      "payload sin propiedad context",
      `payload=${JSON.stringify(firstBody)}`
    );

    // Segundo envío: consentimiento de contexto + un campo marcado.
    await submitChat(page, {
      message: "Pregunta ficticia B8 con un campo seleccionado.",
      consent: true,
      contextConsent: true,
      fields: ["chat-context-field-0"],
    });
    await waitFor(() => fixture.state.chatRequests.length >= 2, 10000, "segundo POST de chat");
    await waitChatResponse(page);
    const secondBody = fixture.state.chatRequests[1].body;
    const sentFields = secondBody && secondBody.context ? secondBody.context.fields : null;
    const sentKeys = sentFields && typeof sentFields === "object" ? Object.keys(sentFields) : [];
    const projectedValue = sentFields ? sentFields["respuestas.objetivo"] : null;

    record(
      "B8-1b",
      "con consentimiento se envía exactamente el campo seleccionado, no el perfil completo",
      sentKeys.length === 1 &&
        sentKeys[0] === "respuestas.objetivo" &&
        projectedValue &&
        projectedValue.estado === "declarado" &&
        projectedValue.valor === "aprender_conceptos" &&
        !("detalle_economico" in (secondBody || {})),
      "context.fields={respuestas.objetivo} y ninguna otra rama del perfil",
      `context=${JSON.stringify(secondBody && secondBody.context)}`
    );
    if (secondBody && secondBody.context) {
      console.log(`     evidencia: POST ${CHAT_PATH} context=${JSON.stringify(secondBody.context)}`);
    }

    record(
      "OBS-1c",
      "observación: la frase de consentimiento ya no niega el envío de los campos seleccionados",
      !consentDeniesMap,
      "el texto describe el envío limitado a los campos marcados y no afirma que el mapa no se envía",
      `texto visible=${JSON.stringify(consentText)}`
    );

    record(
      "OBS-1d",
      "observación: el callout del chat reconoce que se envían campos seleccionados",
      calloutSaysSelected,
      "se registra la frase que contradice el consentimiento anterior",
      `callouts=${JSON.stringify(warningTexts.slice(0, 500))}`
    );

    record(
      "B8-1e",
      "aviso fiel: no se puede afirmar «No se enviará mi mapa» mientras el POST contiene el mapa",
      !(consentDeniesMap && sentKeys.length > 0),
      "si el cuerpo lleva respuestas.objetivo, el aviso no puede negar el envío del mapa",
      `avisoNiegaMapa=${consentDeniesMap} camposEnviados=${JSON.stringify(sentKeys)} valor=${JSON.stringify(projectedValue)}`
    );

    record(
      "B8-1f",
      "el resumen del perfil no puede afirmar «Este mapa no se envía al chat» si el chat lo envía",
      !(summaryDeniesMap && sentKeys.length > 0),
      "la frase del resumen debe ser coherente con el envío consentido de campos",
      `resumenNiegaMapa=${summaryDeniesMap} camposEnviados=${JSON.stringify(sentKeys)}`
    );
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
/* B8-3: borrado del perfil, historial y mensajes precisos                  */
/* ------------------------------------------------------------------------- */

async function testDeletionScopeAndHistory(browser, fixture) {
  console.log("\n--- B8-3 · borrado del perfil e historial separado ---");
  const page = await browser.newPage();
  try {
    await openFresh(page, fixture.origin);
    await seedProfile(page);
    fixture.state.chatRequests.length = 0;

    // Turno ficticio con historial autorizado.
    await submitChat(page, {
      message: "Turno ficticio B8 para historial.",
      consent: true,
      historyConsent: true,
    });
    await waitFor(() => fixture.state.chatRequests.length >= 1, 10000, "POST de historial");
    await waitChatResponse(page);
    await waitFor(async () => (await chatHistoryLength(page)) === 2, 5000, "historial en memoria");

    // Guardar copia local para probar que el control de historial es distinto.
    await enableAndSaveProfile(page, fixture.origin);
    const storedBeforeHistoryClear = await storageValue(page);

    await page.navigate(`${fixture.origin}/#inicio`);
    await waitFor(async () => await page.js("!!document.getElementById('chat-history-clear')"), 10000, "control de historial");
    await clickText(page, "Borrar historial de esta pestaña");
    await waitFor(async () => (await chatHistoryLength(page)) === 0, 5000, "historial borrado");
    const storedAfterHistoryClear = await storageValue(page);

    record(
      "B8-3a",
      "«Borrar historial de esta pestaña» es un control distinto y no borra la copia del mapa",
      storedBeforeHistoryClear !== null && storedAfterHistoryClear !== null,
      "la copia local sigue existiendo tras borrar solo el historial",
      `antes=${storedBeforeHistoryClear !== null} después=${storedAfterHistoryClear !== null}`
    );

    // Segundo turno para volver a tener historial y luego borrar el perfil.
    await submitChat(page, {
      message: "Segundo turno ficticio B8.",
      consent: true,
      historyConsent: true,
    });
    await waitFor(() => fixture.state.chatRequests.length >= 2, 10000, "segundo POST de historial");
    await waitChatResponse(page);
    await waitFor(async () => (await chatHistoryLength(page)) === 2, 5000, "historial reconstruido");

    await page.navigate(`${fixture.origin}/#privacidad`);
    await waitFor(async () => await page.js("!!document.getElementById('profile-persist-toggle')"), 10000, "privacidad");
    const privacyText = await bodyText(page);
    await clickText(page, "Revocar y borrar copia");
    await waitStorage(page, false);
    const dialogText = page.dialogs[page.dialogs.length - 1] || "";
    const historyAfterDelete = await chatHistoryLength(page);
    const feedbackAfterDelete = await textOf(page, "#profile-storage-feedback");

    record(
      "B8-3b",
      "«Revocar y borrar copia» elimina la copia local del mapa",
      (await storageValue(page)) === null,
      "la clave paideia.profile.v2 queda eliminada",
      `clave=${JSON.stringify(await storageValue(page))}`
    );

    record(
      "B8-3c",
      "borrar el perfil deja el historial del chat en memoria (separación real de datos)",
      historyAfterDelete === 2,
      "el historial sigue siendo un dato aparte, no se borra con el perfil",
      `historial tras borrar perfil=${historyAfterDelete}`
    );

    const dialogMentionsChat = /(historial|chat|proveedor)/i.test(dialogText);
    const privacyExplainsDeletionScope =
      /(borrar|eliminar|borrado)[\s\S]{0,240}(historial|mensajes|consultas)[\s\S]{0,180}(no se|no afecta|permanece|proveedor|enviad)/i.test(privacyText) ||
      /(historial|mensajes|consultas)[\s\S]{0,240}(no se borra|no se elimina|permanece|se conserva|ya enviad)/i.test(privacyText);

    record(
      "B8-3d",
      "el diálogo de borrado delimita el alcance: mapa, historial del chat y proveedor",
      dialogMentionsChat,
      "el mensaje debe decir qué se borra y qué no (historial/chat/proveedor)",
      `diálogo=${JSON.stringify(dialogText)}`
    );

    record(
      "B8-3e",
      "la página de privacidad explica que borrar localmente no borra lo ya enviado al proveedor",
      privacyExplainsDeletionScope,
      "debe explicar el alcance del borrado: historial/mensajes ya enviados al proveedor",
      `¿explica alcance?=${privacyExplainsDeletionScope} texto=${JSON.stringify(privacyText.slice(0, 900))}`
    );

    const feedbackMentionsChat = /(historial|chat|proveedor)/i.test(feedbackAfterDelete || "");

    record(
      "B8-3f",
      "el mensaje tras borrar aclara que el historial del chat sigue en memoria",
      feedbackMentionsChat,
      "debe precisar que solo se borró la copia del mapa y que el historial del chat es otro dato",
      `feedback=${JSON.stringify(feedbackAfterDelete)} historial=${historyAfterDelete}`
    );
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
/* B8-4: dos pestañas y resurrección de la copia                            */
/* ------------------------------------------------------------------------- */

async function testTwoTabsResurrection(browser, fixture) {
  console.log("\n--- B8-4 · dos pestañas: borrar en A y autoguardado en B ---");
  const pageA = await browser.newPage();
  const pageB = await browser.newPage();
  try {
    await openFresh(pageA, fixture.origin);
    await seedProfile(pageA);

    await openFresh(pageB, fixture.origin);
    // openFresh limpia el almacenamiento; volver a sembrar para B y recargar A.
    await pageB.navigate(`${fixture.origin}/#inicio`);
    await waitApp(pageB);
    await seedProfile(pageB);
    await pageA.reload();
    await waitApp(pageA);

    await enableAndSaveProfile(pageA, fixture.origin);
    await enableAndSaveProfile(pageB, fixture.origin);
    await waitStorage(pageA, true);
    await waitStorage(pageB, true);

    // B conserva historial propio en memoria antes de que A revoque.
    const postsBeforeHistory = fixture.state.chatRequests.length;
    await pageB.navigate(`${fixture.origin}/#inicio`);
    await waitApp(pageB);
    await submitChat(pageB, {
      message: "Turno ficticio B8 en la pestaña B.",
      consent: true,
      historyConsent: true,
    });
    await waitFor(() => fixture.state.chatRequests.length > postsBeforeHistory, 10000, "POST de historial en B");
    await waitChatResponse(pageB);
    await waitFor(async () => (await chatHistoryLength(pageB)) === 2, 5000, "historial en B");
    await pageB.navigate(`${fixture.origin}/#privacidad`);
    await waitFor(async () => await pageB.js("!!document.getElementById('profile-persist-toggle')"), 10000, "privacidad B");

    recordHarness(
      "H-4a",
      "las dos pestañas comparten origen y tienen una copia guardada antes de borrar",
      (await storageValue(pageA)) !== null && (await storageValue(pageB)) !== null,
      `A=${(await storageValue(pageA)) !== null} B=${(await storageValue(pageB)) !== null}`
    );

    // A revoca y borra.
    await pageA.navigate(`${fixture.origin}/#privacidad`);
    await waitFor(async () => await pageA.js("!!document.getElementById('profile-persist-toggle')"), 10000, "privacidad A");
    await clickText(pageA, "Revocar y borrar copia");
    await waitStorage(pageA, false);
    const feedbackA = await textOf(pageA, "#profile-storage-feedback");

    record(
      "B8-4a",
      "A borra la copia y la clave desaparece del origen compartido",
      (await storageValue(pageA)) === null,
      "localStorage.getItem('paideia.profile.v2') === null",
      `clave=${JSON.stringify(await storageValue(pageA))}`
    );

    // La revocación debe propagarse por el evento storage, no solo por el texto de A.
    const revocationSeenByB = await waitFor(
      async () => {
        const text = await textOf(pageB, "#profile-storage-feedback");
        return /otra pestaña/i.test(text || "") && /revoc/i.test(text || "");
      },
      5000,
      "aviso de revocación en B"
    ).then(() => true).catch(() => false);
    record(
      "B8-4d",
      "la pestaña B recibe la revocación de A por storage y desactiva el autoguardado",
      revocationSeenByB,
      "el evento storage actualiza el aviso de B y su permiso de guardado",
      `feedback B=${JSON.stringify(await textOf(pageB, "#profile-storage-feedback"))}`
    );

    record(
      "B8-4e",
      "la revocación de A no borra el historial del chat que B mantiene en su pestaña",
      (await chatHistoryLength(pageB)) === 2,
      "el historial de B sigue teniendo dos entradas y solo se borra con su control propio",
      `historial B=${await chatHistoryLength(pageB)}`
    );

    // B sigue con su consentimiento y autoguarda al editar una respuesta.
    await pageB.navigate(`${fixture.origin}/#perfil`);
    await waitFor(async () => await pageB.js("!!document.querySelector('.profile-summary')"), 10000, "resumen B");
    await clickText(pageB, "Editar");
    await waitFor(async () => await pageB.js("!!document.querySelector('.profile-form')"), 10000, "formulario B");
    await pageB.js("document.querySelectorAll('input[name=\"profile-answer\"]')[1].click()");
    await clickText(pageB, "Guardar respuesta");
    await sleep(500);

    const resurrectedRaw = await storageValue(pageA);
    let resurrected = null;
    try {
      resurrected = resurrectedRaw ? JSON.parse(resurrectedRaw) : null;
    } catch {
      resurrected = null;
    }
    const objective = resurrected?.profile?.respuestas?.objetivo?.valor || null;

    record(
      "B8-4b",
      "el autoguardado de la pestaña B no resucita la copia borrada por A",
      resurrectedRaw === null,
      "la clave debe seguir ausente tras editar en B; no hay consentimiento vigente en A",
      `clave tras editar B=${resurrectedRaw === null ? "null" : "presente"} objetivo=${JSON.stringify(objective)}`
    );

    const textA = await bodyText(pageA);
    record(
      "B8-4c",
      "A no puede seguir mostrando «Copia local borrada» si la clave ya reapareció",
      !(resurrectedRaw !== null && /Copia local borrada/i.test(textA || "")),
      "el mensaje de A debe seguir siendo cierto o actualizarse al reaparecer la copia",
      `clavePresente=${resurrectedRaw !== null} feedbackA=${JSON.stringify(feedbackA)}`
    );

    // Evidencia adicional: el valor resucitado es el estado de B, no una lectura huérfana.
    if (resurrectedRaw !== null) {
      console.log(
        `     evidencia: clave reescrita por B con objetivo=${JSON.stringify(objective)}; ` +
          `A feedback=${JSON.stringify(feedbackA)}`
      );
    }
  } finally {
    for (const page of [pageA, pageB]) {
      try {
        await browser.browser.send("Target.closeTarget", { targetId: page.targetId }, 5000);
      } catch {
        /* noop */
      }
      page.client.close();
    }
  }
}

/* ------------------------------------------------------------------------- */
/* Main                                                                      */
/* ------------------------------------------------------------------------- */

async function main() {
  let browser = null;
  let fixture = null;
  let real = null;
  let stale = null;
  try {
    browser = await launchBrowser();
    recordHarness("H-0a", "Chromium headless arranca y expone CDP", true, `pid=${browser.child.pid}`);

    fixture = await startFixture();
    recordHarness("H-0b", "fixture loopback sirve la app y la API ficticia", true, fixture.origin);

    real = await startRealServer();
    recordHarness("H-0c", "servidor WSGI público real arranca en loopback", true, real.origin);

    stale = await startFixture({ status: { mode: "local_prototype" } });
    await testDisabledPublicChat(browser, real);
    await testStatusWithoutAi(browser, stale);
    await testMapNoticeVsPayload(browser, fixture);
    await testDeletionScopeAndHistory(browser, fixture);
    await testTwoTabsResurrection(browser, fixture);
  } catch (error) {
    recordHarness("H-0z", "el arnés terminó sin excepción", false, error.stack || String(error));
  } finally {
    if (browser) await browser.close();
    if (real) await real.close();
    if (fixture) await fixture.close();
    if (stale) await stale.close();
  }
  return summarize();
}

main()
  .then((code) => {
    process.exitCode = code;
    // Chrome puede dejar handles; cerramos de forma determinista.
    setTimeout(() => process.exit(code), 100);
  })
  .catch((error) => {
    console.error("Fallo fatal del arnés:", error);
    process.exit(2);
  });
