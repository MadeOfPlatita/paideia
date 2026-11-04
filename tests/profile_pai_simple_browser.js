#!/usr/bin/env node
"use strict";

/*
 * Prueba de navegador independiente — flujo de usuario nuevo:
 * perfil primero, después «Pregunta a Pai» simple; privacidad sin envíos.
 *
 * CARÁCTER TDD (RED PRIMERO)
 *   Este fichero se escribe ANTES de tocar la interfaz. En el estado actual debe
 *   fallar (exit 1) porque «Pregunta a Pai» mezcla la calculadora de escenarios
 *   ficticios y los campos/consentimiento del mapa. No corrige nada ni sustituye
 *   aserciones por las que hoy pasan: las comprobaciones que ya pasan quedan como
 *   red de seguridad para que el arreglo no las rompa.
 *
 * AISLAMIENTO
 *   - No importa ni modifica código de producción.
 *   - No lee .env ni variables de proveedor; no llama a Groq ni a ninguna IA.
 *   - Sirve el frontend de prototipos/paideia-local/static desde 127.0.0.1 y
 *     proxya /api/* al WSGI público api/index.py, cuya IA es not_configured.
 *   - Chrome headless con perfil temporal propio y puertos efímeros: no interfiere
 *     con otras sesiones ni deja almacenamiento entre ejecuciones.
 *
 * USO
 *   node tests/profile_pai_simple_browser.js
 *   PYTHON=/ruta/python CHROME_PATH=/ruta/chrome node tests/profile_pai_simple_browser.js
 *
 * SALIDA
 *   PASS/FAIL por comprobación con esperado y real. Exit 1 = defecto de producto
 *   (RED TDD). Exit 2 = arnés incompleto (Python/Chrome/servidor no disponibles).
 */

const { spawn } = require("node:child_process");
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");

const ROOT = path.resolve(__dirname, "..");
const STATIC_ROOT = path.join(ROOT, "prototipos", "paideia-local", "static");
const CHAT_PATH = "/api/chat";
const QUESTION = "¿Qué es la TAE? Pregunta ficticia de prueba.";
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".json": "application/json; charset=utf-8",
  ".woff2": "font/woff2",
};

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

async function check(id, title, expected, probe) {
  try {
    const outcome = await probe();
    record(id, title, Boolean(outcome && outcome.pass), expected, outcome && outcome.actual);
  } catch (error) {
    record(id, title, false, expected, `ERROR: ${error.message}`);
  }
}

function summarize() {
  const failed = results.filter((item) => !item.pass);
  console.log("\n" + "=".repeat(78));
  console.log(
    `Resumen: ${results.length} comprobaciones, ${results.length - failed.length} PASS, ` +
      `${failed.length} FAIL.`
  );
  if (failed.length) {
    console.log("ESTADO: RED — la interfaz actual no cumple el flujo perfil→Pai simple.");
    console.log(`Fallan: ${failed.map((item) => item.id).join(", ")}`);
  } else {
    console.log("ESTADO: VERDE — flujo perfil→Pai simple y privacidad cumplen.");
  }
  console.log("=".repeat(78));
  return failed.length ? 1 : 0;
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
  if (typeof WebSocket !== "function") {
    throw new Error("Node sin WebSocket nativo; se requiere Node 20 o superior.");
  }
  const executable = findBrowserExecutable();
  if (!executable) throw new Error("No se encontró Chrome/Edge. Define CHROME_PATH.");
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "pai-simple-chrome-"));
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
    try {
      fs.rmSync(userDataDir, { recursive: true, force: true });
    } catch {
      /* noop */
    }
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
  const network = [];
  client.on("Network.requestWillBeSent", (params) => {
    const request = params.request || {};
    network.push({
      url: String(request.url || ""),
      method: String(request.method || "GET"),
      postData: typeof request.postData === "string" ? request.postData : null,
      at: Date.now(),
    });
  });
  const dialogs = [];
  client.on("Page.javascriptDialogOpening", (params) => {
    dialogs.push(params.message || "");
    client.send("Page.handleJavaScriptDialog", { accept: true }).catch(() => {});
  });
  return {
    targetId,
    client,
    network,
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

async function waitFor(probe, timeoutMs, label) {
  const start = Date.now();
  let lastError = null;
  while (Date.now() - start < timeoutMs) {
    try {
      const value = await probe();
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await sleep(100);
  }
  throw new Error(`Timeout esperando ${label}${lastError ? `: ${lastError.message}` : ""}`);
}

async function waitSelector(page, selector, label, timeout = 15000) {
  await waitFor(
    () => page.js(`!!document.querySelector(${JSON.stringify(selector)})`),
    timeout,
    label
  );
}

async function waitHomeReady(page) {
  await waitSelector(page, "#chat-panel", "panel Pregunta a Pai", 20000);
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
      const note = await page.js("(document.getElementById('chat-provider-note') || {}).textContent || ''");
      return note.trim().length > 0 && !/Comprobando la IA/i.test(note);
    },
    15000,
    "aviso del proveedor resuelto"
  );
}

async function setMessage(page, text) {
  const outcome = await page.js(`(() => {
    const input = document.getElementById('chat-message');
    if (!input) return { ok: false };
    input.value = ${JSON.stringify(text)};
    input.dispatchEvent(new Event('input', { bubbles: true }));
    return { ok: true };
  })()`);
  if (!outcome || !outcome.ok) throw new Error("No existe #chat-message");
}

async function clickId(page, id) {
  const outcome = await page.js(`(() => {
    const node = document.getElementById(${JSON.stringify(id)});
    if (!node) return { ok: false };
    if (node.disabled) return { ok: false, disabled: true };
    node.click();
    return { ok: true };
  })()`);
  if (!outcome || !outcome.ok) throw new Error(`No se pudo pulsar #${id}${outcome?.disabled ? " (desactivado)" : ""}`);
}

async function feedbackText(page) {
  return page.js("(document.getElementById('chat-feedback') || {}).textContent || ''");
}

/* ------------------------------------------------------------------------- */
/* Servidor de estáticos + proxy al WSGI público aislado                     */
/* ------------------------------------------------------------------------- */

async function startFrontProxy(wsgiOrigin) {
  const apiRequests = [];
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, "http://127.0.0.1");
    if (url.pathname.startsWith("/api/")) {
      apiRequests.push({ method: request.method, path: url.pathname, at: Date.now() });
      const target = new URL(wsgiOrigin);
      const proxy = http.request(
        {
          hostname: target.hostname,
          port: target.port,
          path: request.url,
          method: request.method,
          headers: { ...request.headers, host: target.host },
        },
        (proxied) => {
          response.writeHead(proxied.statusCode || 502, proxied.headers);
          proxied.pipe(response);
        }
      );
      proxy.on("error", () => {
        response.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
        response.end(JSON.stringify({ error: { code: "BAD_GATEWAY", message: "WSGI no disponible." } }));
      });
      request.pipe(proxy);
      return;
    }

    let relative;
    try {
      relative = decodeURIComponent(url.pathname).replace(/^\/+/, "") || "index.html";
    } catch {
      response.writeHead(400);
      response.end("Ruta no válida");
      return;
    }
    let file = path.resolve(STATIC_ROOT, relative);
    const staticRoot = path.resolve(STATIC_ROOT);
    if (!file.startsWith(staticRoot + path.sep) && file !== path.join(staticRoot, "index.html")) {
      response.writeHead(403);
      response.end("Fuera de estáticos");
      return;
    }
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) file = path.join(staticRoot, "index.html");
    try {
      const data = fs.readFileSync(file);
      response.writeHead(200, {
        "Content-Type": MIME[path.extname(file).toLowerCase()] || "application/octet-stream",
        "Cache-Control": "no-store",
        "Content-Length": data.length,
      });
      response.end(data);
    } catch (error) {
      response.writeHead(500);
      response.end(`No se pudo leer ${path.basename(file)}: ${error.message}`);
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  return {
    origin: `http://127.0.0.1:${server.address().port}`,
    apiRequests,
    close: () => new Promise((resolve) => server.close(resolve)),
  };
}

async function startWsgi() {
  const python = process.env.PYTHON || "python";
  const script = [
    "import sys, os, socketserver",
    "sys.path.insert(0, os.path.join(os.getcwd(), 'api'))",
    "import index",
    "from wsgiref.simple_server import make_server, WSGIServer",
    "class S(socketserver.ThreadingMixIn, WSGIServer):",
    "    daemon_threads = True",
    "httpd = make_server('127.0.0.1', 0, index.app, server_class=S)",
    "print('PORT %d' % httpd.server_port, flush=True)",
    "httpd.serve_forever()",
  ].join("\n");
  const child = spawn(python, ["-u", "-c", script], {
    cwd: ROOT,
    env: { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONDONTWRITEBYTECODE: "1" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  let stdout = "";
  let stderr = "";
  let port = null;
  child.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
    const match = /PORT (\d+)/.exec(stdout);
    if (match) port = Number(match[1]);
  });
  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
    if (stderr.length > 20000) stderr = stderr.slice(-20000);
  });
  try {
    await waitFor(() => port, 15000, `arranque WSGI (${python})`);
  } catch (error) {
    child.kill();
    throw new Error(`${error.message}. stderr: ${stderr.slice(-1200)}`);
  }
  return {
    origin: `http://127.0.0.1:${port}`,
    close: () =>
      new Promise((resolve) => {
        try {
          child.kill();
        } catch {
          /* noop */
        }
        setTimeout(resolve, 300);
      }),
  };
}

/* ------------------------------------------------------------------------- */
/* Flujo                                                                     */
/* ------------------------------------------------------------------------- */

async function run(page, origin, apiRequests) {
  await page.navigate(`${origin}/#inicio`);
  await waitHomeReady(page);
  await page.js("localStorage.clear(); sessionStorage.clear();");
  await page.reload();
  await waitHomeReady(page);

  /* Precondición de entorno: IA apagada de verdad en el WSGI público. */
  const status = await page.js(`fetch('/api/status', { cache: 'no-store' }).then((r) => r.json()).then((data) => ({ status: data?.ai?.status, connected: data?.ai?.connected }))`);
  if (status.status !== "not_configured" || status.connected !== false) {
    throw new Error(`El WSGI público no declara la IA apagada: ${JSON.stringify(status)}`);
  }

  await check(
    "P1",
    "El paso de perfil aparece antes que Pregunta a Pai en Inicio",
    "enlace «Crear mi perfil» (o «Revisar mi mapa») hacia #perfil, antes del panel de chat",
    async () => {
      const data = await page.js(`(() => {
        const main = document.getElementById('main-content');
        const chat = document.getElementById('chat-panel');
        const links = [...main.querySelectorAll('a')].filter((node) => node.offsetParent !== null);
        const profile = links.find((node) => /crear mi perfil|revisar mi mapa/i.test(node.textContent));
        const before = !!(profile && chat && (profile.compareDocumentPosition(chat) & Node.DOCUMENT_POSITION_FOLLOWING));
        return {
          found: !!profile,
          text: profile ? profile.textContent.trim() : '',
          href: profile ? profile.getAttribute('href') : '',
          chat: !!chat,
          before
        };
      })()`);
      return {
        pass: data.found && data.href === "#perfil" && data.chat && data.before,
        actual: JSON.stringify(data),
      };
    }
  );

  await check(
    "C1",
    "El chat conserva sus controles principales visibles",
    "textarea #chat-message, casilla #chat-consent y botón #chat-submit visibles",
    async () => {
      const data = await page.js(`(() => {
        const ids = ['chat-message', 'chat-consent', 'chat-submit'];
        return ids.map((id) => {
          const node = document.getElementById(id);
          return {
            id,
            present: !!node,
            visible: !!node && node.offsetParent !== null,
            tag: node ? node.tagName : null,
            type: node ? (node.type || null) : null
          };
        });
      })()`);
      const byId = Object.fromEntries(data.map((item) => [item.id, item]));
      return {
        pass: data.every((item) => item.present && item.visible),
        actual: JSON.stringify(byId),
      };
    }
  );

  await check(
    "I2",
    "El consentimiento de envío empieza desmarcado",
    "#chat-consent unchecked en usuario nuevo",
    async () => {
      const checked = await page.js("document.getElementById('chat-consent').checked");
      return { pass: checked === false, actual: `checked=${checked}` };
    }
  );

  await check(
    "I1",
    "Aviso honesto de IA apagada visible en Pregunta a Pai",
    "texto que declara la IA no disponible/configurada y que no se envía nada",
    async () => {
      const text = await page.js("(document.getElementById('chat-panel') || {}).innerText || ''");
      const off = /(no configurad|no disponible|no conectad|desactivad)/i.test(text);
      const noSend = /(no se env[íi]a nada|no se ha enviado|ninguna petición de chat)/i.test(text);
      return {
        pass: /IA/i.test(text) && off && noSend,
        actual: `off=${off} noSend=${noSend} muestra=${JSON.stringify(text.slice(0, 240))}`,
      };
    }
  );

  await check(
    "C2",
    "Pregunta a Pai no contiene la calculadora de escenarios",
    "ningún control con id chat-scenario* dentro de #chat-panel",
    async () => {
      const data = await page.js(`(() => {
        const chat = document.getElementById('chat-panel');
        const nodes = [...chat.querySelectorAll('[id^="chat-scenario"]')];
        return { ids: nodes.map((node) => node.id) };
      })()`);
      return {
        pass: data.ids.length === 0,
        actual: data.ids.length ? `controles: ${data.ids.join(', ')}` : 'sin controles de escenario',
      };
    }
  );

  await check(
    "C3",
    "Pregunta a Pai no muestra textos de la calculadora",
    "sin «Añadir escenario ficticio», «cálculo estructurado», capital, tasa, años, aportación, inflación ni método",
    async () => {
      const text = await page.js("(document.getElementById('chat-panel') || {}).innerText || ''");
      const terms = [
        "Añadir escenario ficticio",
        "cálculo estructurado",
        "Capital inicial EUR",
        "Tasa anual %",
        "Años enteros",
        "Aportación mensual EUR",
        "Inflación anual %",
        "Método",
      ];
      const hits = terms.filter((term) => text.includes(term));
      return { pass: hits.length === 0, actual: hits.length ? `visibles: ${hits.join(' | ')}` : "sin textos de calculadora" };
    }
  );

  await check(
    "C4",
    "Pregunta a Pai no contiene campos ni consentimiento del mapa",
    "sin #chat-context-field-*, sin #chat-context-consent y sin etiquetas de datos del perfil",
    async () => {
      const data = await page.js(`(() => {
        const chat = document.getElementById('chat-panel');
        const ids = [...chat.querySelectorAll('[id^="chat-context-field-"], #chat-context-consent')].map((node) => node.id);
        const mapConsent = [...chat.querySelectorAll('label')].some((label) =>
          /Autorizo adjuntar a esta pregunta solo los campos de mi mapa/i.test(label.textContent));
        const mapData = [...new Set([...chat.querySelectorAll('label, .choice span')]
          .map((node) => node.textContent.trim())
          .filter((value) => /^(Objetivo|Horizonte|Importe objetivo|Colchón líquido):/i.test(value)))];
        return { ids, mapConsent, mapData };
      })()`);
      return {
        pass: data.ids.length === 0 && !data.mapConsent && data.mapData.length === 0,
        actual: JSON.stringify(data),
      };
    }
  );

  /* Perfil accesible y operativo (primero perfil). */
  await page.navigate(`${origin}/#perfil`);
  await check(
    "P2",
    "El perfil es accesible y muestra el cuestionario con salidas",
    "panel de pregunta con «No lo sé» y «Omitir»",
    async () => {
      try {
        await waitSelector(page, "#main-content .question-panel", "cuestionario de perfil", 12000);
      } catch (error) {
        const text = await page.js("(document.getElementById('main-content') || {}).innerText || ''");
        return { pass: false, actual: `${error.message}. Texto: ${JSON.stringify(text.slice(0, 200))}` };
      }
      const data = await page.js(`(() => {
        const panel = document.querySelector('#main-content .question-panel');
        const buttons = [...panel.querySelectorAll('button')].map((node) => node.textContent.trim());
        const legend = panel.querySelector('legend');
        return {
          buttons,
          title: legend ? legend.textContent.trim() : '',
          progress: (panel.querySelector('progress') && panel.querySelector('progress').getAttribute('aria-label')) || ''
        };
      })()`);
      return {
        pass: data.buttons.includes("No lo sé") && data.buttons.includes("Omitir") && Boolean(data.title || data.progress),
        actual: JSON.stringify(data),
      };
    }
  );

  await check(
    "P3",
    "«Omitir» avanza la pregunta sin escribir almacenamiento",
    "pasa de Pregunta 1 a Pregunta 2 y localStorage sigue vacío",
    async () => {
      const before = await page.js("(document.querySelector('#main-content .question-panel progress') || {}).getAttribute ? document.querySelector('#main-content .question-panel progress').getAttribute('aria-label') : ''");
      const clicked = await page.js(`(() => {
        const target = [...document.querySelectorAll('#main-content .question-panel button')]
          .find((node) => node.textContent.trim() === 'Omitir');
        if (!target) return false;
        target.click();
        return true;
      })()`);
      if (!clicked) throw new Error("No se encontró «Omitir» en el cuestionario");
      await waitFor(
        async () => {
          const label = await page.js("(document.querySelector('#main-content .question-panel progress') || {}).getAttribute ? document.querySelector('#main-content .question-panel progress').getAttribute('aria-label') : ''");
          return label && label !== before;
        },
        8000,
        "avance a la pregunta siguiente"
      );
      const after = await page.js("document.querySelector('#main-content .question-panel progress').getAttribute('aria-label')");
      const storage = await page.js("({ local: localStorage.length, session: sessionStorage.length })");
      return {
        pass: /Pregunta 2 de/.test(after) && storage.local === 0 && storage.session === 0,
        actual: `antes=${JSON.stringify(before)} despues=${JSON.stringify(after)} storage=${JSON.stringify(storage)}`,
      };
    }
  );

  await check(
    "P4",
    "Al pausar el perfil se puede continuar con Pai",
    "el resumen lleva al chat y el foco llega a la pregunta",
    async () => {
      const paused = await page.js(`(() => {
        const b = [...document.querySelectorAll('#main-content button')].find(x => x.textContent.trim() === 'Pausar y ver el resumen');
        if (!b) return false; b.click(); return true;
      })()`);
      if (!paused) throw new Error('No se encontró Pausar');
      const clicked = await page.js(`(() => {
        const a = [...document.querySelectorAll('#main-content a')].find(x => x.textContent.trim() === 'Continuar con Pai');
        if (!a) return false; a.click(); return true;
      })()`);
      if (!clicked) return { pass: false, actual: 'Falta el enlace Continuar con Pai' };
      await waitFor(async () => await page.js("location.hash === '#inicio' && !!document.getElementById('chat-message')"), 8000, 'vista de Pai');
      await sleep(300);
      const focused = await page.js("document.activeElement.id");
      return { pass: focused === 'chat-message', actual: `Foco después de la navegación: ${focused}` };
    }
  );

  /* Privacidad del envío, de vuelta en el chat simple. */
  await page.navigate(`${origin}/#inicio`);
  await waitHomeReady(page);

  const postsBefore = () => apiRequests.filter((item) => item.path === CHAT_PATH && item.method === "POST").length;
  const networkChatPosts = () =>
    page.network.filter((item) => item.method === "POST" && item.url.split("?")[0].endsWith(CHAT_PATH)).length;

  await check(
    "I3",
    "Sin consentimiento no se envía nada",
    "0 POST /api/chat y aviso «Marca la confirmación de privacidad»",
    async () => {
      const baseline = postsBefore();
      await setMessage(page, QUESTION);
      await clickId(page, "chat-submit");
      await waitFor(
        async () => /Marca la confirmación de privacidad/i.test(await feedbackText(page)),
        5000,
        "aviso de consentimiento"
      );
      const feedback = await feedbackText(page);
      await sleep(250);
      const posts = postsBefore() - baseline;
      return {
        pass: posts === 0 && networkChatPosts() === 0,
        actual: `POST=${posts} red=${networkChatPosts()} aviso=${JSON.stringify(feedback)}`,
      };
    }
  );

  await check(
    "I4",
    "Con consentimiento e IA apagada tampoco se envía, y se avisa",
    "0 POST /api/chat y texto que declara no configurada/no enviada",
    async () => {
      const baseline = postsBefore();
      await page.js(`(() => {
        const node = document.getElementById('chat-consent');
        if (!node.checked) node.click();
        return node.checked;
      })()`);
      await clickId(page, "chat-submit");
      await waitFor(
        async () => /(no configurad|no disponible|no conectad)/i.test(await feedbackText(page)),
        8000,
        "aviso de IA no configurada"
      );
      await sleep(300);
      const feedback = await feedbackText(page);
      const posts = postsBefore() - baseline;
      const notSent = /(no se ha enviado|no se env[íi]a|ninguna petición de chat)/i.test(feedback);
      return {
        pass: posts === 0 && networkChatPosts() === 0 && notSent,
        actual: `POST=${posts} red=${networkChatPosts()} noEnviada=${notSent} aviso=${JSON.stringify(feedback.slice(0, 260))}`,
      };
    }
  );

  await check(
    "V1",
    "El recorrido de usuario nuevo no guarda perfil ni historial",
    "localStorage y sessionStorage a 0",
    async () => {
      const storage = await page.js("({ local: localStorage.length, session: sessionStorage.length, keys: Object.keys(localStorage) })");
      return {
        pass: storage.local === 0 && storage.session === 0,
        actual: JSON.stringify(storage),
      };
    }
  );

  await check(
    "V2",
    "No hay peticiones fuera del loopback",
    "todas las peticiones http(s) van al servidor local 127.0.0.1",
    async () => {
      const external = page.network
        .map((item) => item.url)
        .filter((url) => /^https?:/i.test(url))
        .filter((url) => {
          try {
            return new URL(url).hostname !== "127.0.0.1";
          } catch {
            return true;
          }
        });
      return {
        pass: external.length === 0,
        actual: external.length ? `externas: ${[...new Set(external)].join(' | ')}` : "solo 127.0.0.1",
      };
    }
  );
}

/* ------------------------------------------------------------------------- */
/* Arranque y cierre                                                         */
/* ------------------------------------------------------------------------- */

async function main() {
  if (!fs.existsSync(path.join(STATIC_ROOT, "index.html"))) {
    throw new Error(`No existe ${path.join(STATIC_ROOT, "index.html")}`);
  }
  const wsgi = await startWsgi();
  let front = null;
  let browser = null;
  try {
    front = await startFrontProxy(wsgi.origin);
    browser = await launchBrowser();
    const page = await browser.newPage();
    await run(page, front.origin, front.apiRequests);
  } finally {
    if (browser) await browser.close();
    if (front) await front.close();
    await wsgi.close();
  }
  return summarize();
}

main()
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    console.error(`\nHARNESS-FAIL — ${error.message}`);
    console.error("ESTADO: ARNÉS INCOMPLETO — no se puede concluir RED/VERDE.");
    process.exitCode = 2;
  });
