"use strict";

const API = Object.freeze({
  status: "/api/status",
  catalogue: "/api/catalogue",
  product: "/api/products/",
  conditions: "/api/conditions",
  compare: "/api/compare",
  calculate: "/api/calculate",
  chat: "/api/chat"
});
const PROFILE_MODEL = typeof window !== "undefined" && window.PaideiaProfileModel
  ? window.PaideiaProfileModel
  : (typeof module !== "undefined" && module.exports ? require("./profile_model.js") : null);
if (!PROFILE_MODEL) throw new Error("No se pudo cargar el modelo local de perfil.");
const PROFILE_FIELDS = PROFILE_MODEL.ASKED_QUESTION_KEYS;
const PROFILE_LABELS = Object.freeze(Object.fromEntries(PROFILE_MODEL.QUESTION_DEFS.map((question) => [question.key, question.label])));
const PROFILE_QUESTIONS = PROFILE_MODEL.QUESTION_DEFS;
const CORE_QUESTION_KEYS = PROFILE_MODEL.CORE_QUESTION_KEYS;
const ECONOMIC_QUESTION_KEYS = PROFILE_MODEL.ECONOMIC_QUESTION_KEYS;
const RISK_QUESTION_KEYS = PROFILE_MODEL.RISK_QUESTION_KEYS;
const PROFILE_QUESTION_BY_KEY = new Map(PROFILE_QUESTIONS.map((question) => [question.key, question]));
const PREVIEW_FIELDS = PROFILE_FIELDS;
const FAMILIES = Object.freeze({
  cuenta_remunerada: "Cuenta remunerada",
  deposito: "Depósito",
  letra_deuda_publica: "Letra de deuda pública",
  fondo_tradicional: "Fondo tradicional",
  etf_ucits: "ETF UCITS"
});
function isSafePrimaryUrl(value) {
  if (typeof value !== "string" || value.length > 2048) return false;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" && Boolean(parsed.hostname) && !parsed.username && !parsed.password;
  } catch (_) {
    return false;
  }
}

class ApiFailure extends Error {
  constructor(message, status, code, retryable, sendState) {
    super(message || "La solicitud no pudo completarse.");
    this.name = "ApiFailure";
    this.status = status;
    this.code = code || "LOCAL_API_ERROR";
    this.retryable = Boolean(retryable);
    this.sendState = ["not_started", "unknown", "completed"].includes(sendState) ? sendState : null;
  }
}

const API_TIMEOUT_MS = 45000;

async function apiRequest(path, options = {}) {
  const request = { method: options.method || "GET", headers: { Accept: "application/json" } };
  if (options.body !== undefined) {
    request.headers["Content-Type"] = "application/json";
    request.body = JSON.stringify(options.body);
  }
  const controller = typeof AbortController === "function" ? new AbortController() : null;
  let timedOut = false;
  const timer = controller
    ? setTimeout(() => { timedOut = true; controller.abort(); }, API_TIMEOUT_MS)
    : null;
  if (controller) request.signal = controller.signal;
  let response;
  let body = null;
  try {
    response = await fetch(path, request);
    try { body = await response.json(); } catch (_) { body = null; }
  } catch (error) {
    if (timedOut) throw new ApiFailure("El servicio local tardó demasiado en responder. Vuelve a intentarlo.", 0, "LOCAL_TIMEOUT", true);
    throw new ApiFailure("No se pudo conectar con el servicio local. Comprueba que el prototipo esté iniciado.", 0, "LOCAL_UNREACHABLE", true);
  } finally {
    if (timer !== null) clearTimeout(timer);
  }
  if (!response.ok) {
    const error = body && body.error ? body.error : {};
    throw new ApiFailure(typeof error.message === "string" ? error.message : "El servicio local devolvió un error sin detalle.", response.status, error.code, error.retryable, error.send_state);
  }
  if (!body || typeof body !== "object") throw new ApiFailure("La respuesta del servicio local no tenía el formato esperado.", response.status, "INVALID_RESPONSE", false);
  if (path !== API.status && typeof refreshStatusAfterApiSuccess === "function") refreshStatusAfterApiSuccess();
  return body;
}

function chatIsConfigured() {
  if (state.statusError) return false;
  if (state.status === null) return false;
  const ai = state.status?.ai;
  if (!ai || typeof ai.status !== "string") return false;
  return ai.status === "configured_not_verified" || ai.status === "test_only";
}

function chatProviderNote() {
  const quota = state.status?.ai?.quota;
  const quotaText = quota && Number.isInteger(quota.calls_day) && Number.isInteger(quota.calls_per_day)
    ? ` Llamadas usadas hoy: ${quota.calls_day} de ${quota.calls_per_day}.` : "";
  if (chatIsConfigured()) return "Proveedor configurado. Cada envío requiere tu consentimiento; no hay reintentos automáticos." + quotaText;
  if (state.statusError) return "No se pudo comprobar la IA: no se envía nada; el botón no hará ninguna petición de chat al servidor. Los cálculos y la biblioteca funcionan sin IA." + quotaText;
  if (state.status === null) return "Comprobando la IA: todavía no se envía nada. Los cálculos y la biblioteca funcionan sin IA." + quotaText;
  return "Chat IA no configurado: no se envía nada; el botón no hará ninguna petición de chat al servidor. Los cálculos y la biblioteca funcionan sin IA." + quotaText;
}

const state = {
  route: "inicio",
  profile: PROFILE_MODEL.createEmptyProfile(),
  profileLegacy: {},
  profileComplete: false,
  profileMode: "core",
  profileStep: 0,
  profileConfirmKey: null,
  profileEditKey: null,
  profileOptIn: false,
  storageNotice: "",
  storageProblem: false,
  storageRevokedElsewhere: false,
  storageExternalCopy: false,
  profileUnsaved: false,
  status: null,
  statusError: null,
  library: { query: "", family: "", items: [], count: 0, loading: false, error: null, requestId: 0, loaded: false },
  conditions: { loaded: false, loading: false, error: null, byId: new Map(), referenceDate: null },
  catalogueCache: new Map(),
  selectedIds: [],
  onlyDocumented: false,
  compareResult: null,
  compareIds: [],
  compareError: null,
  compareBusy: false,
  compareRequestId: 0,
  diagnosis: { requestId: 0, ids: [], busy: false, error: false, result: null },
  detail: { id: null, product: null, loading: false, error: null, requestId: 0 },
  scenario: { status: "dirty", version: 0, result: null, error: null, submitted: null, form: { principal: "", annual_rate_percent: "", years: "", monthly_contribution: "", inflation_percent: "", method: "compound" } },
  scenarioSeed: null,
  scenarioSecond: { status: "dirty", version: 0, result: null, error: null, submitted: null, form: { principal: "", annual_rate_percent: "", years: "", monthly_contribution: "", inflation_percent: "", method: "compound" } },
  simulation: { step: 0, products: [], loaded: false, loading: false, error: null, requestId: 0, chosenId: "", product: null, amount: "", understood: false, receiptAt: "" },
  previewFields: new Set(),
  previewAcknowledged: false,
  chatBusy: false,
  chatMessage: "",
  chatTicket: null,
  chatTicketQuery: null,
  chatUncertain: false,
  chatUncertainQuery: null,
  chatUncertainTicket: false,
  libraryTimer: null
};

function el(tag, attrs = {}, children = []) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "className") element.className = value;
    else if (key === "value") element.value = value;
    else if (key === "checked") element.checked = Boolean(value);
    else if (key === "disabled") element.disabled = Boolean(value);
    else if (key === "tabIndex") element.tabIndex = value;
    else if (key === "htmlFor") element.htmlFor = value;
    else element.setAttribute(key, value === true ? "" : String(value));
  }
  const list = Array.isArray(children) ? children : [children];
  for (const child of list) {
    if (child === null || child === undefined || child === false) continue;
    element.appendChild(typeof child === "string" || typeof child === "number" ? document.createTextNode(String(child)) : child);
  }
  return element;
}

function button(text, handler, className = "button button-secondary", options = {}) {
  const item = el("button", { type: options.type || "button", className, disabled: options.disabled, "aria-pressed": options.pressed === undefined ? null : String(options.pressed) }, text);
  if (handler) item.addEventListener("click", handler);
  return item;
}

function routeLink(text, hash, className = "button button-secondary") {
  return el("a", { href: hash, className }, text);
}

function textElement(tag, text, className) {
  return el(tag, className ? { className } : {}, String(text));
}

function addText(parent, tag, text, className) {
  const item = textElement(tag, text, className);
  parent.appendChild(item);
  return item;
}

function field(labelText, control, helpText, id) {
  const wrapper = el("div", { className: "field" });
  wrapper.appendChild(el("label", { htmlFor: id || control.id }, labelText));
  wrapper.appendChild(control);
  if (helpText) wrapper.appendChild(textElement("p", helpText, "field-help"));
  return wrapper;
}

function badge(text, kind = "") {
  return el("span", { className: `badge${kind ? ` badge-${kind}` : ""}` }, text);
}

function setStatusChip(text, kind = "") {
  const chip = document.getElementById("status-chip");
  if (!chip) return;
  chip.textContent = text;
  chip.className = `status-chip${kind ? ` is-${kind}` : ""}`;
}

function familyLabel(family) {
  return FAMILIES[family] || (family ? String(family).replaceAll("_", " ") : "Familia no indicada");
}

function identityLabel(product) {
  return product && product.identity_state === "verified" ? "Identidad verificada" : "Identidad propuesta";
}

function identityKind(product) {
  return product && product.identity_state === "verified" ? "verified" : "proposed";
}

function conditionsLabel(product) {
  return product && product.conditions_state === "pending" ? "Condiciones pendientes" : "Condiciones no validadas para publicar";
}

// Filas de la ficha: qué métrica se muestra, cómo se llama y cómo se formatea.
// Solo entran las que la transcripción trae con valor; el resto no genera fila.
const CONDITION_ROWS = Object.freeze({
  annual_rate_percent: { label: "Tasa anual (TAE)", format: (v) => `${formatRate(v)}` },
  term_months: { label: "Plazo", format: (v) => `${v} meses` },
  isin: { label: "ISIN", format: (v) => v },
  ter_percent: { label: "TER", format: (v) => `${formatRate(v)} anual` },
  management_fee_percent: { label: "Comisión de gestión", format: (v) => `${formatRate(v)} anual` },
  custody_fee_percent: { label: "Comisión de depositario", format: (v) => `${formatRate(v)} anual` },
  entry_fee_percent: { label: "Comisión de entrada", format: (v) => formatRate(v) },
  exit_fee_percent: { label: "Comisión de salida", format: (v) => formatRate(v) },
  performance_fee_percent: { label: "Comisión de éxito", format: (v) => formatRate(v) },
  risk_scale: { label: "Riesgo (SRI)", format: (v) => v },
  minimum_eur: { label: "Inversión mínima", format: (v) => `${formatEuros(v)} €` },
  maximum_eur: { label: "Importe máximo", format: (v) => `${formatEuros(v)} €` },
  maximum_note: { label: "Importe máximo", format: (v) => v },
  nav_eur: { label: "Valor liquidativo", format: (v) => `${formatEuros(v)} €` },
  marginal_rate_percent: { label: "Tipo marginal", format: (v) => `${formatRate(v)}` },
  minimum_price_percent: { label: "Precio mínimo aceptado", format: (v) => `${formatRate(v)} del nominal` },
  maturity_date: { label: "Vencimiento", format: (v) => v },
  holding_period_years: { label: "Periodo recomendado", format: (v) => `${v} años` },
  withholding_percent: { label: "Retención fiscal", format: (v) => `${formatRate(v)}` },
  category: { label: "Categoría", format: (v) => v },
  manager: { label: "Gestora", format: (v) => v },
  depositary: { label: "Depositaria", format: (v) => v },
  base_currency: { label: "Divisa base", format: (v) => v },
  replication: { label: "Réplica", format: (v) => v },
  sfdr_article: { label: "Artículo SFDR", format: (v) => v },
  ucits: { label: "UCITS", format: (v) => v },
  nominal_rate_percent: { label: "TIN (nominal)", format: (v) => formatRate(v) },
  subsequent_rate_percent: { label: "TAE tras la promoción", format: (v) => formatRate(v) },
  subsequent_nominal_rate_percent: { label: "TIN tras la promoción", format: (v) => formatRate(v) },
  settlement: { label: "Liquidación de intereses", format: (v) => v },
  declared_fees: { label: "Comisiones declaradas", format: (v) => (/^[0-9.,]+$/.test(v) ? formatRate(v) : v) },
  deposit_guarantee_fund: { label: "Garantía de depósitos", format: (v) => `${formatEuros(v)} €` },
  eligibility: { label: "Elegibilidad", format: (v) => v },
  availability: { label: "Disponibilidad", format: (v) => v },
  account_domicile: { label: "Domicilio de la cuenta", format: (v) => v },
  outstanding_balance: { label: "Saldo vivo", format: (v) => (/^[0-9.]+$/.test(v) ? `${formatEuros(v)} M€` : v) },
  launch_date: { label: "Fecha de lanzamiento", format: (v) => v },
  early_cancellation: { label: "Cancelación anticipada", format: (v) => v },
  interest_basis: { label: "Base de cálculo", format: (v) => v },
  cnmv_registry: { label: "Registro CNMV", format: (v) => v },
  distribution_policy: { label: "Reparto", format: (v) => v },
  promotion_window: { label: "Fin de la promoción", format: (v) => v },
  ownership: { label: "Titularidad", format: (v) => v },
  annual_cost_figure: { label: "Cifra anual de gastos", format: (v) => formatRate(v) },
  cost_impact_1y_percent: { label: "Coste estimado a 1 año", format: (v) => formatRate(v) },
  cost_impact_5y_percent: { label: "Coste estimado a 5 años", format: (v) => formatRate(v) },
  subscription_redemption: { label: "Suscripción y reembolso", format: (v) => v },
  recommended_horizon: { label: "Horizonte recomendado", format: (v) => v },
  document_date: { label: "Fecha del documento", format: (v) => v },
  retail_access: { label: "Acceso minorista", format: (v) => v },
  requirement: { label: "Requisito", format: (v) => v },
  direct_debits: { label: "Domiciliaciones", format: (v) => v },
  lock_in: { label: "Permanencia", format: (v) => v },
  renewal: { label: "Renovación", format: (v) => v },
  auction_date: { label: "Fecha de subasta", format: (v) => v },
  settlement_date: { label: "Fecha de liquidación", format: (v) => v },
  average_price_percent: { label: "Precio medio", format: (v) => `${formatRate(v)} del nominal` },
  average_rate_percent: { label: "Tipo medio", format: (v) => formatRate(v) },
  awarded_nominal_eur: { label: "Nominal adjudicado", format: (v) => `${formatEuros(v)} €` },
  spain_registry: { label: "Registro en España", format: (v) => v },
  registry_countries: { label: "Países de registro", format: (v) => v },
  main_market: { label: "Mercado principal", format: (v) => v },
  fund_assets_eur: { label: "Patrimonio", format: (v) => `${formatEuros(v)} €` },
  fund_investors: { label: "Partícipes", format: (v) => formatEuros(v) },
  securities_lending: { label: "Préstamo de valores", format: (v) => v },
  operating_costs: { label: "Costes de operación", format: (v) => formatRate(v) },
  vehicle_type: { label: "Tipo de vehículo", format: (v) => v },
  last_prospectus_date: { label: "Último folleto", format: (v) => v },
  last_regulation_date: { label: "Último reglamento", format: (v) => v },
  data_date: { label: "Fecha de los datos", format: (v) => v },
  registration_date: { label: "Fecha de registro", format: (v) => v },
  cnmv_registration_date: { label: "Registro CNMV", format: (v) => v },
  share_class_currency: { label: "Divisa de la clase", format: (v) => v },
  minimum_horizon: { label: "Horizonte mínimo", format: (v) => v },
  total_cost_1y_percent: { label: "Coste total a 1 año", format: (v) => formatRate(v) },
});

function formatEuros(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  return number.toLocaleString("es-ES", { maximumFractionDigits: 2 });
}

function conditionRowText(condition) {
  if (!condition || typeof condition.metric !== "string") return "";
  const row = CONDITION_ROWS[condition.metric];
  if (!row) return "";
  if (condition.state !== "known" || condition.value === null || condition.value === undefined || condition.value === "") {
    return `${row.label}: sin dato documentado`;
  }
  const formatted = row.format(String(condition.value));
  return formatted ? `${row.label}: ${formatted}` : `${row.label}: sin dato utilizable`;
}

function issuerLabel(product) {
  return product && typeof product.issuer === "string" && product.issuer.trim() ? product.issuer : "Emisor no indicado en este registro";
}

function productName(product) {
  return product && typeof product.name === "string" && product.name.trim() ? product.name : "Producto sin nombre en la respuesta";
}

function apiErrorText(error) {
  if (error instanceof ApiFailure) {
    if (error.code === "CHAT_NOT_CONFIGURED") return "Ahora no puedo responder con IA. No voy a inventar una respuesta. El chat no está conectado en este prototipo.";
    return error.message;
  }
  return "No se pudo cargar esta información desde el servicio local.";
}

/* Solo estos fallos de chat necesitan redacción propia: el resto conserva el
   mensaje del servidor. Ninguno reintenta ni reenvía por su cuenta.
   `send_state` describe un intento de transporte, no el turno completo: un
   turno con herramientas puede tener varias rondas, así que no se usa para
   afirmar que el proveedor recibió o procesó todo el turno. */
function chatFailureNotice(error) {
  if (!(error instanceof ApiFailure)) return null;
  if (error.code === "LOCAL_TIMEOUT") {
    return {
      uncertain: true,
      text: `El navegador dejó de esperar a los ${API_TIMEOUT_MS / 1000} s, pero la petición pudo llegar al servidor y al proveedor. No se sabe si el turno llegó a completarse. No hay reintento automático.`
    };
  }
  if (error.code === "CHAT_TIMEOUT" || error.status === 504) {
    const stateText = error.sendState === "not_started"
      ? "La petición terminó con un timeout del proveedor (504). El último intento de transporte consta como no iniciado, pero ese dato no demuestra que el turno completo no se enviara al proveedor."
      : error.sendState === "completed"
        ? "La petición terminó con un timeout del proveedor (504). El último intento de transporte consta como completado, pero eso no confirma que el proveedor aceptara ni procesara el turno completo."
        : "El proveedor agotó el tiempo de espera (504) y no está confirmado si el turno llegó a completarse; la petición pudo llegar al proveedor.";
    return { uncertain: true, text: stateText + " No hay reintento automático." };
  }
  if (error.code === "CHAT_RATE_LIMITED") {
    return {
      uncertain: false,
      text: "El proveedor rechazó la llamada por límite de uso (429); no es un timeout. No hay reintento automático; espera antes de volver a enviar."
    };
  }
  /* Cupo global de intentos reales: la petición no llegó a salir hacia el proveedor
     porque el contador la detuvo antes de abrir la conexión. */
  if (error.code === "CHAT_MISSION_EXHAUSTED" || error.code === "CHAT_MISSION_CLOSED"
      || error.code === "CHAT_MISSION_UNAVAILABLE") {
    const reason = error.code === "CHAT_MISSION_EXHAUSTED"
      ? "se agotó el cupo de intentos reales de esta prueba"
      : error.code === "CHAT_MISSION_CLOSED"
        ? "la ventana de esta prueba ya está cerrada"
        : "no se pudo verificar el contador de intentos";
    return {
      uncertain: false,
      text: `No se envió la pregunta al proveedor: ${reason}. No hay reintento automático ni consumo de cuota del proveedor.`
    };
  }
  return null;
}

/* La incertidumbre y el ticket pertenecen al texto exacto que se envió. La
   interfaz no los transfiere a una pregunta editada ni presenta esa pregunta
   nueva como si fuera un reenvío de la anterior. */
function chatSubmitLabel() {
  const draft = state.chatMessage.trim();
  if (state.chatTicket && state.chatTicketQuery === draft) return "Reenviar turno en cola";
  if (state.chatUncertain && state.chatUncertainQuery === draft) return "Reenviar pregunta";
  return "Enviar pregunta";
}

function chatInitialStatus() {
  const draft = state.chatMessage.trim();
  if (state.chatUncertain) {
    const sameDraft = state.chatUncertainQuery === draft;
    const ticketNote = state.chatUncertainTicket
      ? " El ticket de cola del intento anterior no se reutiliza: pudo quedar reclamado o cerrado; un reenvío manual podría duplicar el turno o ser rechazado."
      : "";
    return {
      warning: true,
      text: sameDraft
        ? "El último envío quedó sin confirmar: la petición pudo llegar al servidor o al proveedor y no se sabe si el turno llegó a completarse. La pregunta sigue en el cuadro; un reenvío manual podría duplicar el turno o ser rechazado. No se reenvía automáticamente." + ticketNote
        : "El envío anterior quedó sin confirmar: la petición pudo llegar al servidor o al proveedor y no se sabe si el turno llegó a completarse. La pregunta actual todavía no se ha enviado y no se reenvía automáticamente." + ticketNote
    };
  }
  if (state.chatTicket && state.chatTicketQuery === draft) {
    return {
      warning: true,
      text: "Hay un turno en cola pendiente de reenvío manual. No se envía automáticamente; al reenviarlo se usará su ticket."
    };
  }
  return {
    warning: false,
    text: state.chatMessage ? "La pregunta sigue solo en memoria. Aún no se ha enviado." : "Sin respuesta; todavía no se ha enviado nada."
  };
}

function chatFailureDraftText(query, sameDraft, attemptedTicket) {
  const notes = [];
  if (attemptedTicket) {
    notes.push("El ticket de cola usado en este intento no se reutiliza: pudo quedar reclamado o cerrado. Un reenvío manual empezaría un turno nuevo y podría duplicar el turno o ser rechazado.");
  }
  if (sameDraft) {
    notes.push("La pregunta enviada sigue en el cuadro; puedes reenviarla manualmente, pero podría duplicar el turno o ser rechazada.");
  } else {
    notes.push("La pregunta enviada ya no está en el cuadro y no se reenvía automáticamente. La pregunta actual todavía no se ha enviado.");
  }
  return notes.join(" ");
}

function errorBox(message, retryHandler, extraLink) {
  const box = el("div", { className: "error-note", role: "alert" });
  box.appendChild(textElement("p", message));
  const actions = el("div", { className: "error-actions" });
  if (retryHandler) actions.appendChild(button("Intentar de nuevo", retryHandler, "button button-secondary"));
  if (extraLink) actions.appendChild(routeLink(extraLink.text, extraLink.hash, "button-link"));
  box.appendChild(actions);
  return box;
}

function callout(text, className = "note") {
  return el("div", { className, role: className.includes("error") ? "alert" : "note" }, text);
}

function pageFrame(eyebrow, title, lede) {
  const main = document.getElementById("main-content");
  const page = el("div", { className: "page-shell" });
  const header = el("header", { className: "page-heading" });
  header.appendChild(textElement("p", eyebrow, "eyebrow"));
  const h1 = el("h1", { id: "page-title", tabIndex: -1 }, title);
  header.appendChild(h1);
  if (lede) header.appendChild(textElement("p", lede, "lede"));
  page.appendChild(header);
  main.replaceChildren(page);
  return { page, header, heading: h1 };
}

function focusHeading(heading) {
  if (!heading) return;
  window.requestAnimationFrame(() => heading.focus({ preventScroll: true }));
}

function announce(message) {
  const region = document.getElementById("app-status");
  if (!region || typeof message !== "string" || !message) return;
  if (region.textContent !== message) region.textContent = message;
}

function captureFocus() {
  const active = document.activeElement;
  const lost = !active || active === document.body || active === document.documentElement || !active.isConnected;
  return {
    id: active && active.id ? active.id : null,
    hadFocus: !lost
  };
}

function restoreFocus(snapshot, fallback) {
  if (!snapshot || !snapshot.hadFocus) return false;
  const active = document.activeElement;
  const lost = !active || active === document.body || active === document.documentElement || !active.isConnected;
  if (!lost) return false;
  if (snapshot.id) {
    const same = document.getElementById(snapshot.id);
    if (same && !same.disabled && same.isConnected) {
      same.focus({ preventScroll: true });
      return true;
    }
  }
  if (fallback && fallback.isConnected) {
    fallback.focus({ preventScroll: true });
    return true;
  }
  return false;
}

function section(title, intro, className = "paper-section") {
  const wrapper = el("section", { className });
  const header = el("div", { className: "section-head" });
  const titleNode = el("h2", {}, title);
  header.appendChild(titleNode);
  if (intro) header.appendChild(textElement("p", intro));
  wrapper.appendChild(header);
  return wrapper;
}

function appendPrimarySource(parent, product) {
  const source = product && product.primary_url;
  const line = el("p", { className: "source-line" });
  if (isSafePrimaryUrl(source)) {
    line.appendChild(document.createTextNode("Fuente primaria: "));
    line.appendChild(el("a", { href: source, target: "_blank", rel: "noopener noreferrer" }, source));
    line.appendChild(document.createTextNode(" · Se abre solo si eliges el enlace."));
  } else {
    line.appendChild(document.createTextNode("Fuente primaria: no hay una URL HTTPS segura en este registro."));
  }
  parent.appendChild(line);
  return line;
}

function renderContext(route) {
  const copy = {
    inicio: ["La ruta empieza por una pregunta", "Puedes explorar sin compartir perfil. Si haces un mapa, será una referencia editable, no un test."],
    perfil: ["Tu mapa no te puntúa", "Cada respuesta es opcional. Omitir y «No lo sé» quedan diferenciados en el resumen."],
    biblioteca: ["Identidad no es oferta", "La ficha separa quién es el candidato de las condiciones que todavía no se han validado."],
    comparar: ["Comparar también es ver lo que falta", "Aquí se alinean metadatos. No hay ranking, cifras de rendimiento ni recomendación personal."],
    escenarios: ["Una hipótesis a la vez", "El cálculo usa los supuestos que introduzcas. No predice el comportamiento de ningún candidato."],
    simulacion: ["Ensayo, no contratación", "Se conserva una referencia identificativa real del catálogo; la cantidad del ejercicio es ficticia y local."],
    glosario: ["Palabras antes que promesas", "Las definiciones orientan la lectura; no sustituyen las condiciones de un producto."],
    privacidad: ["Tú marcas el alcance", "La vista previa de contexto se compone aquí, en el navegador. No se envía a una IA ni a una API."]
  }[route] || ["Acompañamiento de Pai", "Explora con calma y separa los datos de los supuestos."];
  const aside = document.getElementById("context-panel");
  const head = el("div", { className: "context-heading" });
  head.appendChild(el("img", { src: "./assets/pai-mark.svg", alt: "", width: 46, height: 46 }));
  const identity = el("div");
  identity.appendChild(el("h2", {}, "Pai"));
  identity.appendChild(textElement("p", "Acompañamiento contextual"));
  head.appendChild(identity);
  const text = el("p", {}, copy[1]);
  const aiStatus = state.status?.ai?.status;
  const limitText = aiStatus === "configured_not_verified"
    ? "Chat IA configurado. Solo se envía lo que autorices en cada pregunta."
    : "Chat IA no conectado. Los cálculos, la biblioteca y el glosario funcionan igual.";
  const limit = el("p", { className: "context-limit" }, limitText);
  const glossary = route !== "glosario" ? routeLink("Consultar el glosario", "#glosario", "button-link") : null;
  aside.replaceChildren(head, text, limit);
  if (glossary) aside.appendChild(glossary);
}

function updateNavigation(route) {
  for (const link of document.querySelectorAll(".nav-link[data-route]")) {
    if (link.dataset.route === route) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

function routeFromHash() {
  const route = window.location.hash.replace(/^#/, "") || "inicio";
  const allowed = new Set(["inicio", "perfil", "biblioteca", "comparar", "escenarios", "simulacion", "glosario", "privacidad"]);
  return allowed.has(route) ? route : "inicio";
}

function displayProfileValue(key, answer = PROFILE_MODEL.getAnswer(state.profile, key)) {
  return PROFILE_MODEL.formatAnswer(key, answer);
}

function formatCurrency(value) {
  const amount = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(amount)) return "No disponible";
  return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 2 }).format(amount);
}

function formatPercentValue(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "No disponible";
  return `${new Intl.NumberFormat("es-ES", { maximumFractionDigits: 4 }).format(amount)} %`;
}

function initStorage() {
  state.storageRevokedElsewhere = false;
  state.storageExternalCopy = false;
  let loaded;
  try { loaded = PROFILE_MODEL.loadStoredProfile(window.localStorage); }
  catch (_) {
    state.storageProblem = true;
    state.storageNotice = "No se puede leer el almacenamiento local; podrían existir copias en este dispositivo.";
    return;
  }
  state.profile = loaded.profile;
  state.profileLegacy = loaded.legacyAnswers || {};
  state.profileOptIn = loaded.optedIn;
  state.profileComplete = !!loaded.hasSavedProfile;
  if (loaded.hasSavedProfile) {
    state.profileMode = "summary";
    state.storageProblem = true;
    state.storageNotice = "Hay una copia guardada en este dispositivo, cargada para revisarla. El guardado automático está desactivado tras recargar; puedes borrar la copia o marcar la casilla y pulsar Guardar para autorizar esta sesión. No se envía a terceros." + (loaded.migrated ? " La versión anterior se ha convertido solo en memoria; revisa las respuestas antiguas." : "");
  }
  if (loaded.error) {
    state.storageProblem = true;
    state.storageNotice = loaded.error === "invalid_saved_profile"
      ? "No se pudo leer un perfil local anterior. No se borró automáticamente; puedes continuar en memoria o borrarlo con confirmación."
      : loaded.error === "legacy_residue"
        ? state.storageNotice + " Permanecen copias anteriores en este dispositivo."
        : "No se pudo comprobar o completar la lectura o migración local. Podrían existir copias en este dispositivo.";
    return;
  }
}

function saveProfileLocally() {
  let result;
  try { result = PROFILE_MODEL.saveStoredProfile(window.localStorage, state.profile, state.profileLegacy, true); }
  catch (_) { result = { ok: false, reason: "storage_unavailable" }; }
  if (result.ok) {
    state.profileOptIn = true;
    state.storageProblem = false;
    state.storageRevokedElsewhere = false;
    state.storageExternalCopy = false;
    state.profileUnsaved = false;
    state.storageNotice = "Perfil guardado solo en este dispositivo.";
    return { ok: true, message: state.storageNotice };
  }
  {
    if (result.snapshotWritten) {
      state.profileOptIn = true;
      state.profileUnsaved = false;
    }
    state.storageProblem = true;
    state.storageNotice = result.snapshotWritten
      ? "Perfil guardado en este dispositivo, pero no se pudo completar o comprobar la eliminación de todas las copias anteriores. Pueden quedar datos locales."
      : "No se pudo confirmar el guardado. Podrían existir copias locales; revisa los permisos del navegador.";
    return { ok: false, snapshotWritten: result.snapshotWritten === true, message: state.storageNotice };
  }
}

function autosaveProfileLocally() {
  let current;
  try { current = window.localStorage.getItem(PROFILE_MODEL.STORAGE_KEY); }
  catch (_) {
    state.storageProblem = true;
    state.storageNotice = "No se pudo comprobar la copia local antes de autoguardar. El guardado automático se ha detenido para no reescribir datos que otra pestaña haya podido borrar; el mapa sigue en memoria.";
    return { ok: false, reason: "storage_read_failed", snapshotWritten: false };
  }
  if (current === null) {
    state.profileOptIn = false;
    state.storageProblem = false;
    state.storageRevokedElsewhere = true;
    state.storageExternalCopy = false;
    state.storageNotice = "Otra pestaña borró la copia local. El guardado automático se ha detenido en esta pestaña; el mapa sigue solo en memoria y el historial del chat no se ha borrado.";
    return { ok: false, reason: "revoked_elsewhere", snapshotWritten: false };
  }
  return saveProfileLocally();
}

function removeSavedProfile() {
  let result;
  try { result = PROFILE_MODEL.clearStoredProfiles(window.localStorage); }
  catch (_) { result = { ok: false, removed: [] }; }
  state.profileOptIn = false;
  state.storageRevokedElsewhere = false;
  state.storageExternalCopy = false;
  if (result.ok) {
    state.storageNotice = "Copia local borrada; el historial del chat de esta pestaña y los mensajes ya enviados al proveedor no se borran con esta acción.";
    state.storageProblem = false;
    state.profileUnsaved = false;
  } else {
    state.storageProblem = true;
    state.storageNotice = "No se pudo borrar toda la copia local. Revisa los permisos de este navegador; el historial del chat no se ha tocado y los mensajes ya enviados al proveedor siguen fuera de este dispositivo.";
  }
  return result;
}

function handleStorageEvent(event) {
  if (!event || event.key !== PROFILE_MODEL.STORAGE_KEY) return;
  if (event.storageArea && event.storageArea !== window.localStorage) return;
  if (event.newValue === null) {
    state.profileOptIn = false;
    state.profileUnsaved = false;
    state.storageRevokedElsewhere = true;
    state.storageExternalCopy = false;
    state.storageNotice = "Otra pestaña revocó el permiso y borró la copia local del mapa. En esta pestaña el mapa sigue solo en memoria; el historial del chat no se ha borrado.";
  } else {
    state.storageExternalCopy = true;
    state.storageRevokedElsewhere = false;
    state.storageNotice = state.profileOptIn
      ? "Otra pestaña actualizó la copia local del mapa. Esta pestaña mantiene su propio mapa en memoria y puede sobrescribir esa copia al autoguardar."
      : "Otra pestaña guardó una copia local del mapa. Esta pestaña no tiene permiso de guardado activo y no la reescribirá automáticamente.";
  }
  const toggle = document.getElementById("profile-persist-toggle");
  if (toggle) toggle.checked = state.profileOptIn;
  const feedback = document.getElementById("profile-storage-feedback");
  if (feedback) {
    feedback.className = "warning-note";
    feedback.replaceChildren(textElement("p", state.storageNotice));
  }
  updateStorageStatusLine();
  renderStorageWarning();
}

function clearProfile() {
  if (!window.confirm("¿Borrar el mapa actual y todas sus copias guardadas en este dispositivo, incluidas las versiones anteriores? No se borra el historial del chat ni los mensajes ya enviados al proveedor. Esta acción no se puede deshacer.")) return;
  state.profile = PROFILE_MODEL.createEmptyProfile();
  state.profileLegacy = {};
  state.profileComplete = false;
  state.profileMode = "core";
  state.profileStep = 0;
  state.profileEditKey = null;
  state.profileOptIn = false;
  state.previewAcknowledged = false;
  removeSavedProfile();
  render();
}

function updateStorageStatusLine() {
  const line = document.getElementById("profile-storage-state");
  if (line) line.textContent = storageStatusText();
}

function storageStatusText() {
  if (state.storageProblem) return "Estado local incompleto o desconocido: podrían quedar copias en este dispositivo.";
  if (state.storageRevokedElsewhere) return "Otra pestaña borró la copia local; aquí el mapa sigue solo en memoria.";
  if (state.profileOptIn) return "Hay un perfil guardado localmente por elección previa.";
  if (state.storageExternalCopy) return "Hay una copia guardada por otra pestaña; aquí el guardado automático sigue desactivado.";
  return "Ahora: solo memoria de esta pestaña.";
}

function saveProfileAfterConsent() {
  const toggle = document.getElementById("profile-persist-toggle");
  const feedback = document.getElementById("profile-storage-feedback");
  if (!toggle || !feedback) return;
  if (!toggle.checked) {
    feedback.replaceChildren(textElement("p", "Marca primero la casilla si quieres conservar el mapa en este dispositivo."));
    return;
  }
  const result = saveProfileLocally();
  feedback.replaceChildren(textElement("p", result.message + (state.profileOptIn ? " Los cambios posteriores se guardarán automáticamente en este navegador mientras siga activado el guardado local. Esto no autoriza ningún envío remoto." : "")));
  feedback.className = result.ok ? "success-note" : "error-note";
  updateStorageStatusLine();
  renderStorageWarning();
}

function renderHome() {
  const { page, heading } = pageFrame("Inicio · explorar sin prisa", "Tu ruta, a tu ritmo", "Prepara tu perfil y después pregunta a Pai. Tu perfil no se comparte sin tu permiso; también puedes explorar sin completarlo.");
  const route = el("ol", { className: "route-strip", "aria-label": "Pasos de exploración" });
  // La navegación lateral ya numera las secciones: aquí no se repiten números.
  [["Prepara tu perfil", "A tu ritmo"], ["Habla con Pai", "Con tu permiso"], ["Explora y compara", "Fuentes y condiciones"]].forEach((item) => {
    const li = el("li");
    li.appendChild(textElement("strong", item[0]));
    li.appendChild(textElement("span", item[1]));
    route.appendChild(li);
  });
  page.appendChild(route);

  const actions = el("div", { className: "home-actions" });
  const explore = el("section");
  explore.appendChild(textElement("p", "EXPLORAR", "eyebrow"));
  explore.appendChild(el("h2", {}, "Explora la biblioteca"));
  explore.appendChild(textElement("p", "Candidatos del catálogo local. La identidad y las condiciones se muestran por separado, sin mezclarlas."));
  explore.appendChild(routeLink("Abrir biblioteca", "#biblioteca", "button button-secondary"));
  const map = el("section");
  map.appendChild(textElement("p", "TU MAPA", "eyebrow"));
  map.appendChild(el("h2", {}, state.profileComplete ? "Tu mapa está listo" : "Empieza por tu mapa"));
  map.appendChild(textElement("p", state.profileComplete ? "Puedes editar cada respuesta o retomar las que dejaste pendientes." : "Unas preguntas sobre objetivos, situación y riesgo. Puedes responder «No lo sé», omitir o pausar cuando quieras."));
  map.appendChild(routeLink(state.profileComplete ? "Revisar mi mapa" : "Crear mi perfil", "#perfil", "button button-primary"));
  actions.append(explore);
  page.appendChild(map);

  const chat = section("Pregunta a Pai", "Escribe tu pregunta. Pai ofrece orientación educativa, no decide por ti.", "paper-section chat-panel");
  chat.id = "chat-panel";
  // Presentación de procedencia del chat: la prosa del modelo nunca se usa para adjudicar
  // fuentes ni tasas cuando el turno consultó el catálogo. Se muestran los datos locales.
  const CHAT_SOURCE_CLASS_LABELS = { official: "Oficial", secondary: "Secundaria", mixed: "Mixta", unknown: "Desconocida" };
  const CHAT_CONDITION_STATE_LABELS = { known: "documentada", stale: "vencida", conflict: "en conflicto", unknown: "desconocida" };
  const CHAT_CONDITIONS_STATE_LABELS = {
    documented: "documentadas", documented_not_current: "documentadas pero no vigentes",
    documented_unattributed: "documentadas sin fuente atribuible", conditions_unknown: "desconocidas",
    identity_only: "solo identidad, sin condiciones"
  };
  const CHAT_ATTRIBUTION_LABELS = {
    resolved: "fuente resuelta", partial: "atribución parcial", unresolved: "sin fuente resoluble",
    inconsistent: "fuente incoherente", none: "sin fuente citada"
  };
  const CHAT_ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
  const CHAT_DECIMAL = /^-?\d+(?:\.\d+)?$/;
  function chatText(value, limit = 300) {
    return typeof value === "string" ? value.slice(0, limit) : "";
  }
  function chatDate(value) {
    if (typeof value !== "string" || !CHAT_ISO_DATE.test(value)) return "";
    const [year, month, day] = value.split("-").map(Number);
    const parsed = new Date(Date.UTC(year, month - 1, day));
    const valid = parsed.getUTCFullYear() === year && parsed.getUTCMonth() === month - 1 && parsed.getUTCDate() === day;
    return valid ? value : "";
  }
  function chatDecimal(value) {
    return typeof value === "string" && CHAT_DECIMAL.test(value) ? value : "";
  }
  function chatConditionValue(condition) {
    const metric = condition && condition.metric;
    const unit = condition && condition.unit;
    const coherent = (metric === "annual_rate_percent" && unit === "PERCENT")
      || (metric === "term_months" && unit === "MONTHS");
    if (!coherent) return "unidad incoherente; no se muestra el valor";
    if (condition.state === "unknown") return "sin valor documentado";
    const value = chatDecimal(condition && condition.value);
    if (!value) return "sin valor documentado";
    return unit === "MONTHS" ? `${value} meses` : `${value} %`;
  }
  function chatConditionName(condition) {
    return condition && condition.metric === "term_months" ? "Plazo" : "TAE";
  }
  const CHAT_MONEY = /^-?\d{1,18}(?:\.\d{1,2})?$/;
  const CHAT_PERCENT = /^-?\d{1,4}(?:\.\d{1,4})?$/;
  const CHAT_CALC_METHODS = { simple: "simple", compound: "compuesto" };
  function chatMoney(value) {
    if (typeof value !== "string" || !CHAT_MONEY.test(value)) return "";
    const negative = value.startsWith("-");
    const [whole, fraction = ""] = (negative ? value.slice(1) : value).split(".");
    return `${negative ? "-" : ""}${whole.replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${(fraction + "00").slice(0, 2)}`;
  }
  function chatPercentValue(value) {
    if (typeof value !== "string" || !CHAT_PERCENT.test(value)) return "";
    const negative = value.startsWith("-");
    const [whole, fraction = ""] = (negative ? value.slice(1) : value).split(".");
    return `${negative ? "-" : ""}${whole},${(fraction + "00").slice(0, 2)}`;
  }
  // Forma cerrada del DTO del motor: si algo no encaja, no se muestra ninguna cifra.
  function chatCalculationView(calculation) {
    if (!calculation || typeof calculation !== "object") return null;
    if (calculation.hypothetical !== true || calculation.not_prediction !== true
        || calculation.currency !== "EUR") return null;
    const assumptions = calculation.assumptions;
    const summary = calculation.summary;
    if (!assumptions || typeof assumptions !== "object" || !summary || typeof summary !== "object") return null;
    if (!Number.isInteger(assumptions.years) || assumptions.years < 1 || assumptions.years > 40) return null;
    if (!Object.prototype.hasOwnProperty.call(CHAT_CALC_METHODS, assumptions.method)) return null;
    if (assumptions.taxes_included !== false || assumptions.fees_included !== false) return null;
    const principal = chatMoney(assumptions.principal);
    const monthly = chatMoney(assumptions.monthly_contribution);
    const rate = chatPercentValue(assumptions.annual_rate_percent);
    const inflation = chatPercentValue(assumptions.inflation_percent);
    const money = {
      contributions: chatMoney(summary.contributions),
      final_balance: chatMoney(summary.final_balance),
      interest: chatMoney(summary.interest),
      inflation_adjusted: chatMoney(summary.inflation_adjusted)
    };
    if (!principal || !monthly || !rate || !inflation) return null;
    if (!money.contributions || !money.final_balance || !money.interest || !money.inflation_adjusted) return null;
    return {
      principal, monthly, rate, inflation,
      years: assumptions.years,
      method: CHAT_CALC_METHODS[assumptions.method],
      money
    };
  }
  function renderChatCalculation(container, calculation) {
    const view = chatCalculationView(calculation);
    container.appendChild(textElement("p", "Resultado del motor determinista local (escenario hipotético):", "chat-provenance-title"));
    if (!view) {
      container.appendChild(textElement("p", "El resultado del motor local no llegó con una forma válida; no se muestran cifras. No se sustituye por la prosa del modelo.", "field-help"));
      return;
    }
    container.appendChild(textElement("p", `Supuestos: principal ${view.principal} EUR; aportación mensual ${view.monthly} EUR; plazo ${view.years} ${view.years === 1 ? "año" : "años"}; método ${view.method}; tasa anual ${view.rate} %; inflación anual ${view.inflation} %.`));
    for (const [label, key] of [["Aportaciones", "contributions"], ["Saldo final", "final_balance"], ["Interés", "interest"], ["Saldo ajustado por inflación", "inflation_adjusted"]]) {
      container.appendChild(textElement("p", `${label}: ${view.money[key]} EUR`));
    }
    container.appendChild(textElement("p", "No incluye impuestos ni comisiones. Es un cálculo determinista con los supuestos mostrados; no es una predicción ni una oferta.", "field-help"));
  }
  function renderChatCatalogue(container, catalogue) {
    const products = catalogue && Array.isArray(catalogue.products) ? catalogue.products.slice(0, 20) : [];
    const box = el("div", { className: "chat-catalogue" });
    box.appendChild(textElement("p", "Datos locales del catálogo con su procedencia; no son una oferta publicable.", "chat-provenance-title"));
    if (!products.length) {
      box.appendChild(textElement("p", "No hay fichas locales en este turno; no se muestra texto del modelo para evitar atribuciones no verificadas."));
      container.appendChild(box);
      return;
    }
    for (const product of products) {
      if (!product || typeof product !== "object" || typeof product.id !== "string") continue;
      const card = el("div", { className: "chat-catalogue-item" });
      card.appendChild(textElement("h3", `${chatText(product.name, 200) || product.id} (${product.id})`));
      const identity = product.identity_state === "verified" ? "identidad verificada" : "identidad propuesta";
      const issuer = chatText(product.issuer, 120);
      card.appendChild(textElement("p", `Familia: ${chatText(product.family, 40) || "no indicada"} · Emisor: ${issuer || "no indicado"} · ${identity}`));
      const conditionsState = CHAT_CONDITIONS_STATE_LABELS[product.conditions_state] || "estado no reconocido";
      const attribution = CHAT_ATTRIBUTION_LABELS[product.attribution_state] || "atribución no reconocida";
      const reference = chatDate(product.conditions_reference_date);
      card.appendChild(textElement("p", `Condiciones ${conditionsState}; ${attribution}${reference ? ` · fecha de referencia: ${reference}` : ""}.`));
      for (const reason of Array.isArray(product.conditions_state_reasons) ? product.conditions_state_reasons.slice(0, 4) : []) {
        if (typeof reason === "string") card.appendChild(textElement("p", reason, "field-help"));
      }
      const conditions = Array.isArray(product.conditions) ? product.conditions.slice(0, 8) : [];
      for (const condition of conditions) {
        if (!condition || typeof condition !== "object") continue;
        const state = CHAT_CONDITION_STATE_LABELS[condition.state] || "desconocida";
        const sourceClass = CHAT_SOURCE_CLASS_LABELS[condition.source_class] || "Desconocida";
        card.appendChild(textElement("p", `${chatConditionName(condition)}: ${chatConditionValue(condition)} — ${state}; clase de fuente: ${sourceClass}.`));
        const retrieved = chatDate(condition.retrieved_at);
        if (retrieved) card.appendChild(textElement("p", `Consulta de la fuente: ${retrieved}.`, "field-help"));
        const from = chatDate(condition.effective_from);
        const to = chatDate(condition.effective_to);
        if (from || to) card.appendChild(textElement("p", `Vigencia: ${from || "sin inicio declarado"} → ${to || "sin fin declarado"}.`, "field-help"));
        const resolution = CHAT_ATTRIBUTION_LABELS[condition.source_resolution] || "atribución no reconocida";
        card.appendChild(textElement("p", `Atribución de la condición: ${resolution}.`, "field-help"));
        for (const note of Array.isArray(condition.limitations) ? condition.limitations.slice(0, 4) : []) {
          if (typeof note === "string") card.appendChild(textElement("p", note, "field-help"));
        }
        for (const note of Array.isArray(condition.notes) ? condition.notes.slice(0, 4) : []) {
          if (typeof note === "string") card.appendChild(textElement("p", note, "field-help"));
        }
        const conditionSources = Array.isArray(condition.sources) ? condition.sources.slice(0, 4) : [];
        for (const conditionSource of conditionSources) {
          if (!conditionSource || typeof conditionSource !== "object" || !isSafePrimaryUrl(conditionSource.url)) continue;
          const conditionSourceTitle = typeof conditionSource.title === "string" && conditionSource.title.trim()
            ? chatText(conditionSource.title.trim(), 160) : "";
          const sourceLine = el("p", { className: "field-help" }, [
            document.createTextNode("Fuente de la condición: "),
            el("a", { href: conditionSource.url, target: "_blank", rel: "noopener noreferrer" },
              conditionSourceTitle ? `${conditionSourceTitle} — ${chatText(conditionSource.url, 300)}` : chatText(conditionSource.url, 300))
          ]);
          card.appendChild(sourceLine);
        }
      }
      const conflicts = Array.isArray(product.conflicts) ? product.conflicts.filter((item) => typeof item === "string").slice(0, 5) : [];
      const unknownFields = Array.isArray(product.unknown_fields) ? product.unknown_fields.filter((item) => typeof item === "string").slice(0, 12) : [];
      if (conflicts.length || unknownFields.length) {
        card.appendChild(textElement("p", "Revisión pendiente declarada por la ficha:", "chat-provenance-title"));
        if (conflicts.length) {
          card.appendChild(textElement("p", "Conflictos que siguen abiertos:", "field-help"));
          for (const conflict of conflicts) card.appendChild(textElement("p", chatText(conflict, 200), "field-help"));
        }
        if (unknownFields.length) {
          card.appendChild(textElement("p", "Campos desconocidos:", "field-help"));
          for (const field of unknownFields) card.appendChild(textElement("p", chatText(field, 120), "field-help"));
        }
      } else {
        card.appendChild(textElement("p", "La ficha no enumera conflictos ni campos desconocidos; eso no equivale a que no existan.", "field-help"));
      }
      const tiers = Array.isArray(product.rate_tiers) ? product.rate_tiers.slice(0, 6) : [];
      if (tiers.length) {
        const list = el("ul", { className: "chat-rate-tiers" });
        for (const tier of tiers) {
          if (!tier || typeof tier !== "object") continue;
          const tae = chatDecimal(tier.tae);
          const tin = chatDecimal(tier.tin);
          const label = chatText(tier.condition_label, 160) || chatText(tier.condition, 64) || "Tramo";
          list.appendChild(textElement("li", `${label}: TAE ${tae ? `${tae} %` : "no disponible"}; TIN ${tin ? `${tin} %` : "no disponible"}.`));
        }
        card.appendChild(list);
        if (product.rate_tiers_validity !== "known") {
          card.appendChild(textElement("p", "Los tramos no constan como vigentes; no se presentan como actuales.", "field-help"));
        }
        const tierDate = chatDate(product.rate_tiers_effective_to);
        if (tierDate) card.appendChild(textElement("p", `Vigencia de los tramos: hasta ${tierDate}.`, "field-help"));
      } else if (product.rate_tiers_state === "invalid" || product.rate_tiers_state === "inconsistent") {
        card.appendChild(textElement("p", "Los tramos no se muestran porque su forma o sus cifras son incoherentes.", "field-help"));
      }
      for (const note of Array.isArray(product.rate_tiers_limitations) ? product.rate_tiers_limitations.slice(0, 4) : []) {
        if (typeof note === "string") card.appendChild(textElement("p", note, "field-help"));
      }
      box.appendChild(card);
    }
    container.appendChild(box);
  }
  function renderChatSources(container, sources, sourcesTotal, sourcesTruncated) {
    const list = el("ul", { className: "chat-sources" });
    const items = Array.isArray(sources) ? sources.slice(0, 20) : [];
    let shown = 0;
    for (const item of items) {
      const source = item && item.source;
      if (!source || typeof source !== "object" || !isSafePrimaryUrl(source.url)) continue;
      const line = el("li");
      line.appendChild(el("a", { href: source.url, target: "_blank", rel: "noopener noreferrer" }, chatText(source.label, 160) || chatText(source.product_id, 40) || "Fuente"));
      const kind = source.kind === "identity" ? "Identidad" : (CHAT_SOURCE_CLASS_LABELS[source.source_class] || "Desconocida");
      const retrieved = chatDate(source.retrieved_at);
      line.appendChild(textElement("span", ` — clase: ${kind}; ${retrieved ? `consultada: ${retrieved}` : "fecha no disponible"}.`));
      const scope = source.claim_scope === "product_identity_only" ? "Acredita identidad, no condiciones." : (source.claim_scope === "condition_documentation_only" ? "Documenta condiciones; no es una oferta vigente." : "");
      if (scope) line.appendChild(textElement("span", ` ${scope}`));
      list.appendChild(line);
      shown += 1;
    }
    if (shown) {
      container.appendChild(textElement("p", "Referencias locales (la clase y la fecha acompañan a cada cita):", "chat-provenance-title"));
      container.appendChild(list);
      const total = Number.isInteger(sourcesTotal) && sourcesTotal > shown ? sourcesTotal : (Number.isInteger(sourcesTruncated) && sourcesTruncated > 0 ? shown + sourcesTruncated : shown);
      if (total > shown) {
        container.appendChild(textElement("p", `Se muestran ${shown} de ${total} referencias locales; ${total - shown} se omiten por el límite agregado de 20 o por no tener una URL HTTPS segura, y no se presentan como inexistentes.`, "field-help"));
      }
    }
  }
  function renderChatProvenance(container, provenance) {
    if (!provenance || typeof provenance !== "object") return;
    container.appendChild(textElement("p", "Trazabilidad: el texto del modelo no se valida semánticamente contra las fuentes.", "field-help"));
    for (const note of Array.isArray(provenance.limitations) ? provenance.limitations.slice(0, 6) : []) {
      if (typeof note === "string") container.appendChild(textElement("p", note, "field-help"));
    }
  }
  chat.appendChild(callout("Si la IA está disponible y das tu consentimiento, tu pregunta se enviará al proveedor. No incluyas nombres, documentos ni datos bancarios.", "warning-note"));
  const form = el("form", { className: "chat-form" });
  const message = el("textarea", { id: "chat-message", name: "message", maxlength: 1200, "aria-describedby": "chat-help chat-feedback" });
  message.value = state.chatMessage;
  const messageField = field("Escribe una pregunta de prueba", message, "El texto solo se enviará tras marcar la casilla y pulsar el botón.", "chat-message");
  messageField.querySelector(".field-help").id = "chat-help";
  form.appendChild(messageField);
  const consent = el("label", { className: "choice", htmlFor: "chat-consent" }, [el("input", { type: "checkbox", id: "chat-consent" }), el("span", {}, "Autorizo enviar esta pregunta al proveedor IA si está configurado y habilitado. No incluiré datos personales. El mapa completo no se envía: solo los campos que marques y autorices aparte." )]);
  form.appendChild(consent);
  const chatOptions = el("details", { id: "pai-context", className: "data-panel" });
  chatOptions.appendChild(el("summary", {}, "Opciones de privacidad para Pai"));
  chatOptions.appendChild(callout("Compartir datos del mapa o historial es opcional y requiere consentimiento aparte. El historial solo está disponible en pruebas sintéticas.", "info-note"));
  const chatCapabilities = state.status?.ai?.capabilities;
  const scenarioEnabled = el("input", {type:"checkbox", id:"chat-scenario-enabled"});
  const testOptions = el("details", { className: "data-panel", id: "pai-test-options" });
  testOptions.appendChild(el("summary", {}, "Opciones de prueba sintética"));
  testOptions.appendChild(el("label", {className:"choice", htmlFor:"chat-scenario-enabled"}, [scenarioEnabled, el("span", {}, "Añadir escenario ficticio para cálculo estructurado (solo prueba local; completa todos los campos).") ]));
  // Los seis campos del cálculo no se muestran hasta que se piden: en Inicio
  // ocupaban media pantalla antes de escribir la primera pregunta.
  const scenarioFields = el("div", {id:"chat-scenario-fields", hidden:""});
  scenarioEnabled.addEventListener("change", () => { scenarioFields.hidden = !scenarioEnabled.checked; });
  const scenarioInputs = {};
  for (const [key,label] of [["principal","Capital inicial EUR"],["annual_rate_percent","Tasa anual %"],["years","Años enteros (1–40)"],["monthly_contribution","Aportación mensual EUR"],["inflation_percent","Inflación anual %"]]) {
    const input=el("input", {id:`chat-scenario-${key}`, type:"text", inputmode:"decimal"});
    scenarioInputs[key]=input; scenarioFields.appendChild(field(label,input,"Solo cifras ficticias; usa punto decimal.",`chat-scenario-${key}`));
  }
  scenarioInputs.method=el("select", {id:"chat-scenario-method"}, [el("option",{value:""},"Selecciona un método"),el("option",{value:"simple"},"Simple"),el("option",{value:"compound"},"Compuesto")]);
  scenarioFields.appendChild(field("Método",scenarioInputs.method,"Selecciona el método ficticio.","chat-scenario-method"));
  testOptions.appendChild(scenarioFields);
  const capabilitiesNote = callout(`Mapa: ${chatCapabilities?.context === true ? "puedes adjuntar los campos que marques" : "no disponible"}; catálogo: ${chatCapabilities?.catalogue === true ? "puede consultar fichas documentadas" : "no disponible"}; historial: ${chatCapabilities?.history === true ? "habilitado" : "desactivado"}.`, "warning-note");
  capabilitiesNote.setAttribute("id", "chat-context-capabilities");
  chatOptions.appendChild(capabilitiesNote);
  const CONTEXT_LABELS = {"respuestas.objetivo":"Objetivo","respuestas.horizonte":"Horizonte","detalle_economico.importe_objetivo":"Importe objetivo","detalle_economico.colchon_liquido":"Colchón líquido"};
  const contextChoices = PaideiaChatContext.fields.map((key, index) => {
    const answer = PROFILE_MODEL.getAnswer(state.profile, key);
    const answered = !!answer && answer.estado === "declarado";
    const available = answered && chatCapabilities?.context === true;
    const box = el("input", {type:"checkbox", id:`chat-context-field-${index}`, disabled:!available});
    const value = answered ? displayProfileValue(key, answer) : "sin responder en tu mapa";
    chatOptions.appendChild(el("label", {className:"choice", htmlFor:`chat-context-field-${index}`}, [box, el("span", {}, `${CONTEXT_LABELS[key] || key}: ${value}`)]));
    return box;
  });
  const contextConsent = el("input", {type:"checkbox", id:"chat-context-consent", disabled:chatCapabilities?.context !== true});
  const historyConsent = el("input", {type:"checkbox", id:"chat-history-consent", disabled:chatCapabilities?.history !== true});
  chatOptions.appendChild(el("label", {className:"choice", htmlFor:"chat-context-consent"}, [contextConsent, el("span", {}, "Autorizo adjuntar a esta pregunta solo los campos de mi mapa que he marcado.")]));
  chatOptions.appendChild(el("label", {className:"choice", htmlFor:"chat-history-consent"}, [historyConsent, el("span", {}, "Autorizo conservar en esta pestaña, solo durante esta prueba con contenido ficticio, mis preguntas y las respuestas de Pai de hasta dos turnos anteriores (cuatro mensajes como máximo) y reenviarlos con la pregunta siguiente; sin guardado automático.")]));
  let historyRevision = 0;
  const historyClear = button("Borrar historial de esta pestaña", () => { historyRevision += 1; PaideiaChatContext.clear(); feedback.textContent = "Historial borrado de esta pestaña. Los mensajes ya enviados al proveedor no se borran."; }, "button button-quiet", {id:"chat-history-clear", type:"button"});
  historyClear.setAttribute("id", "chat-history-clear");
  chatOptions.appendChild(historyClear);
  historyConsent.addEventListener("change", () => {
    feedback.textContent = historyConsent.checked
      ? "Historial activado: se reenviarán hasta dos turnos anteriores, solo en esta pestaña."
      : "Historial desactivado: la próxima pregunta no reenviará turnos anteriores. Lo ya conservado sigue en esta pestaña hasta que pulses «Borrar historial de esta pestaña».";
  });
  const providerNote = textElement("p", chatProviderNote(), "field-help");
  providerNote.id = "chat-provider-note";
  form.appendChild(providerNote);
  const submit = button(chatSubmitLabel(), null, "button button-primary", { type: "submit" });
  submit.setAttribute("id", "chat-submit");
  form.appendChild(el("div", { className: "button-row" }, submit));
  const initialStatus = chatInitialStatus();
  const feedback = textElement(
    "p",
    initialStatus.text,
    initialStatus.warning ? "chat-state warning-note" : "chat-state"
  );
  feedback.id = "chat-feedback";
  feedback.setAttribute("role", "status");
  form.appendChild(feedback);
  let messageRevision = 0;
  const markDraftChanged = () => {
    messageRevision += 1;
    state.chatMessage = message.value;
    const hadTicket = Boolean(state.chatTicket);
    state.chatTicket = null;
    state.chatTicketQuery = null;
    submit.textContent = chatSubmitLabel();
    if (hadTicket) {
      feedback.textContent = "La pregunta o el escenario cambiaron: el turno en cola anterior no se asociará a este contenido y su ticket queda descartado. No se reenvía automáticamente.";
      feedback.className = "chat-state warning-note";
    } else if (state.chatUncertain) {
      const status = chatInitialStatus();
      feedback.textContent = status.text;
      feedback.className = status.warning ? "chat-state warning-note" : "chat-state";
    }
  };
  message.addEventListener("input", markDraftChanged);
  for (const control of [scenarioEnabled, ...Object.values(scenarioInputs)]) {
    for (const eventName of ["input", "change"]) control.addEventListener(eventName, markDraftChanged);
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (state.chatBusy) return;
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");
    const revision = messageRevision;
    const query = message.value.trim();
    state.chatMessage = query;
    if (!query) { feedback.textContent = "Escribe una pregunta antes de continuar."; message.focus(); return; }
    if (query.length > 1200) { feedback.textContent = "La pregunta supera el límite de 1.200 caracteres."; message.focus(); return; }
    if (!document.getElementById("chat-consent").checked) { feedback.textContent = "Marca la confirmación de privacidad antes de enviar el texto."; document.getElementById("chat-consent").focus(); return; }
    if (!chatIsConfigured()) {
      feedback.textContent = state.status === null && !state.statusError
        ? "Todavía no se ha comprobado la configuración de la IA. La pregunta no se ha enviado y no se hará ninguna petición de chat al servidor."
        : "Chat IA no configurado o no verificable: la pregunta no se ha enviado y no se hará ninguna petición de chat al servidor. Los cálculos y la biblioteca siguen disponibles.";
      feedback.className = "chat-state warning-note";
      return;
    }
    const selectedFields = PaideiaChatContext.fields.filter((_, index) => contextChoices[index].checked);
    if (contextConsent.checked && !selectedFields.length) { feedback.textContent = "Marca al menos un campo de tu mapa para adjuntarlo."; return; }
    if (historyConsent.checked && query.length > 1000) { feedback.textContent = "Límite de historial: 1.000 caracteres por mensaje; solo se conservan los dos últimos turnos. Reduce la pregunta o desmarca su envío."; return; }
    const includeContext = contextConsent.checked, includeHistory = historyConsent.checked, historyAtSend = historyRevision;
    const attemptedTicket = state.chatTicket && state.chatTicketQuery === query ? state.chatTicket : null;
    if (!attemptedTicket && state.chatTicket) {
      state.chatTicket = null;
      state.chatTicketQuery = null;
    }
    const submitHadFocus = document.activeElement === submit;
    if (submitHadFocus) {
      try { message.focus({ preventScroll: true }); } catch (_) { message.focus(); }
    }
    submit.disabled = true;
    state.chatBusy = true;
    feedback.textContent = "Intentando contactar el endpoint local /api/chat…";
    try {
      const payload = { message: query, consent: { notice_version: "paideia-chat-remote-v1", accepted_chat_processing: true, purpose: "free_chat", approved_fields: [] } };
      if (includeContext || includeHistory) {
        payload.context_consent = {notice_version:"paideia-chat-context-map-v1", context:includeContext, history:includeHistory};
        if (includeContext) payload.context = PaideiaChatContext.project(state.profile, selectedFields);
        if (includeHistory) payload.history = PaideiaChatContext.history().slice(-4);
        if (typeof TextEncoder !== "undefined" && new TextEncoder().encode(JSON.stringify(payload)).length > 16384) throw new ApiFailure("La petición supera 16 KiB; borra historial o reduce la pregunta. No se ha enviado nada.", 400, "REQUEST_TOO_LARGE", false);
      }
      if (attemptedTicket) payload.ticket = attemptedTicket;
      let submittedScenario = null;
      if (scenarioEnabled.checked) {
        if (state.statusError || state.status?.ai?.status !== "test_only" || state.status?.ai?.capabilities?.structured_education !== true) throw new ApiFailure("El cálculo ficticio requiere modo estructurado de prueba verificado.", 400, "SCENARIO_UNAVAILABLE", false);
        const years = scenarioInputs.years.value.trim();
        if (!/^(?:[1-9]|[1-3][0-9]|40)$/.test(years)) throw new ApiFailure("Completa los años del escenario ficticio (1–40).", 400, "INVALID_SCENARIO", false);
        try { submittedScenario = PaideiaStructuredEducation.scenario({principal:scenarioInputs.principal.value.trim(), annual_rate_percent:scenarioInputs.annual_rate_percent.value.trim(), years:Number(years), monthly_contribution:scenarioInputs.monthly_contribution.value.trim(), method:scenarioInputs.method.value, inflation_percent:scenarioInputs.inflation_percent.value.trim()}); }
        catch (_) { throw new ApiFailure("Completa un escenario ficticio válido antes de enviar.", 400, "INVALID_SCENARIO", false); }
        payload.scenario = submittedScenario;
      }
      const expectedStructured = state.status?.ai?.capabilities?.structured_education === true || (state.statusError && chatCapabilities?.structured_education === true);
      const result = await apiRequest(API.chat, { method: "POST", body: payload });
      if (result.status === "queued" && result.queue && /^[0-9a-f]{32}$/.test(result.queue.ticket)) {
        if (revision !== messageRevision || state.chatMessage.trim() !== query) {
          state.chatTicket = null;
          state.chatTicketQuery = null;
          submit.textContent = "Enviar pregunta";
          feedback.textContent = "La pregunta cambió mientras se esperaba la cola. El turno anterior no se asociará a esta pregunta nueva y no se reenvía automáticamente; su ticket no se conserva aquí.";
          feedback.className = "chat-state warning-note";
          return;
        }
        state.chatTicket = result.queue.ticket;
        state.chatTicketQuery = query;
        state.chatUncertain = false;
        state.chatUncertainQuery = null;
        state.chatUncertainTicket = false;
        const position = Number.isInteger(result.queue.position) ? result.queue.position : "pendiente";
        const budgetNotice = result.queue.code === "quota_exhausted" ? " El cupo está agotado." : "";
        const testNotice = result.provider_mode === "test_only" ? "PRUEBA SINTÉTICA, no IA real. " : "";
        feedback.textContent = `${testNotice}Consulta en cola. Posición: ${position}.${budgetNotice} El texto permanece en este navegador hasta que pulses reenviar; no hay envío automático.`;
        feedback.className = "chat-state warning-note";
        submit.textContent = "Reenviar turno en cola";
      } else {
        if (!["external", "test_only"].includes(result.provider_mode) || typeof result.answer !== "string") {
          throw new ApiFailure("Respuesta del chat no válida.", 200, "INVALID_RESPONSE", false);
        }
        let structured;
        try { structured = PaideiaStructuredEducation.select(result, Boolean(expectedStructured), submittedScenario); }
        catch (_) { throw new ApiFailure("Respuesta educativa estructurada no válida; no se mostrará texto libre.", 502, "INVALID_STRUCTURED_RESPONSE", false); }
        state.chatTicket = null;
        state.chatTicketQuery = null;
        state.chatUncertain = false;
        state.chatUncertainQuery = null;
        state.chatUncertainTicket = false;
        submit.textContent = "Enviar pregunta";
        feedback.replaceChildren();
        if (result.provider_mode === "test_only") feedback.appendChild(textElement("strong", "PRUEBA SINTÉTICA — NO ES UNA IA REAL."));
        if (structured) {
          feedback.appendChild(textElement("p", "Contenido educativo de Paideia; no es redacción libre del modelo."));
          const claimsPayload = result.claims && typeof result.claims === "object" ? result.claims : null;
          if (claimsPayload && typeof PaideiaClaims !== "undefined" && PaideiaClaims
              && typeof PaideiaClaims.render === "function") {
            PaideiaClaims.render(feedback, claimsPayload);
          } else {
            for (const item of structured.items) feedback.appendChild(textElement("p", item.text));
          }
          if (structured.calculation) {
            feedback.appendChild(textElement("p", "Resultado del motor determinista local (escenario hipotético):"));
            const data = structured.calculation.data;
            for (const [label,key] of [["Aportaciones","contributions"],["Saldo final","final_balance"],["Interés","interest"],["Saldo ajustado por inflación","inflation_adjusted"]]) feedback.appendChild(textElement("p", `${label}: ${data.summary[key]} EUR`));
            for (const point of data.series) feedback.appendChild(textElement("p", `Mes ${point.month}: aportaciones ${point.contributions}, saldo ${point.balance}, saldo real ${point.real_balance} EUR`));
          }
        } else {
          const catalogue = result.catalogue && typeof result.catalogue === "object" ? result.catalogue : null;
          const provenance = result.answer_provenance && typeof result.answer_provenance === "object" ? result.answer_provenance : null;
          const textState = typeof result.answer_text_state === "string"
            ? result.answer_text_state
            : (provenance && typeof provenance.text_state === "string" ? provenance.text_state : "");
          const catalogueUsed = Boolean(catalogue && catalogue.used === true);
          const calculation = result.calculation && typeof result.calculation === "object" ? result.calculation : null;
          const withheld = textState.startsWith("withheld") || catalogueUsed;
          const withheldReason = provenance && typeof provenance.withheld_reason === "string" ? provenance.withheld_reason : "";
          if (withheld) {
            // El aviso debe decir el motivo real declarado por el backend; si no consta,
            // no se acusa de «fuente oficial»: solo de no ser verificable localmente.
            const withheldNotice = (typeof PaideiaWithheldNotice !== "undefined" && PaideiaWithheldNotice
              && typeof PaideiaWithheldNotice.notice === "function")
              ? PaideiaWithheldNotice.notice({
                catalogueUsed,
                hasCalculation: Boolean(calculation) || withheldReason === "calculation",
                reason: withheldReason
              })
              : "Se ha omitido el texto del modelo porque no se pudo verificar localmente. No se presenta como dato.";
            feedback.appendChild(textElement("p", withheldNotice));
            if (catalogueUsed && catalogue) renderChatCatalogue(feedback, catalogue);
            if (calculation) renderChatCalculation(feedback, calculation);
          } else if (typeof result.answer === "string" && result.answer) {
            feedback.appendChild(textElement("p", result.answer));
            if (calculation) renderChatCalculation(feedback, calculation);
          }
          if (result.claims && typeof PaideiaClaims !== "undefined" && PaideiaClaims
              && typeof PaideiaClaims.render === "function") {
            PaideiaClaims.render(feedback, result.claims);
          }
          renderChatSources(feedback, result.sources, result.sources_total, result.sources_truncated);
          renderChatProvenance(feedback, provenance);
          if (!withheld && includeHistory && historyConsent.checked && historyAtSend === historyRevision && result.provider_mode === "test_only" && result.answer) {
            try { PaideiaChatContext.add(query, result.answer); }
            catch (_) { feedback.appendChild(textElement("p", "Este turno no se conservó: excede el límite de historial. Borra el historial para continuar.")); }
          }
        }
        if (!structured && result.refused) feedback.appendChild(textElement("p", "El proveedor ha rechazado esta consulta."));
        if (!structured && result.truncated) feedback.appendChild(textElement("p", "Respuesta incompleta: se alcanzó el límite de salida."));
        if (!structured && Array.isArray(result.tool_events) && result.tool_events.length) {
          feedback.appendChild(textElement("p", "Herramientas: " + result.tool_events.map(item => `${item.name || "rechazada"} (${item.state})`).join("; ")));
        }
        feedback.className = "chat-state note";
      }
    } catch (error) {
      const notice = chatFailureNotice(error);
      if (notice) {
        const sameDraft = revision === messageRevision && message.value.trim() === query;
        state.chatTicket = null;
        state.chatTicketQuery = null;
        state.chatUncertain = notice.uncertain;
        state.chatUncertainQuery = notice.uncertain ? query : null;
        state.chatUncertainTicket = notice.uncertain && Boolean(attemptedTicket);
        feedback.textContent = notice.text + " " + chatFailureDraftText(query, sameDraft, Boolean(attemptedTicket));
        feedback.className = "chat-state error-note";
        feedback.setAttribute("role", "alert");
        feedback.setAttribute("aria-live", "assertive");
        submit.textContent = chatSubmitLabel();
      } else {
        state.chatTicket = null;
        state.chatTicketQuery = null;
        state.chatUncertain = false;
        state.chatUncertainQuery = null;
        state.chatUncertainTicket = false;
        submit.textContent = "Enviar pregunta";
        feedback.textContent = apiErrorText(error);
        feedback.className = "chat-state error-note";
        feedback.setAttribute("role", "alert");
        feedback.setAttribute("aria-live", "assertive");
      }
    } finally {
      state.chatBusy = false;
      submit.disabled = false;
      // El contador de llamadas del día solo cambia tras enviar: se refresca aquí
      // para que el aviso no siga diciendo «0 de 60» después de una respuesta.
      if (typeof checkLocalStatus === "function") checkLocalStatus();
      if (submitHadFocus) {
        const active = document.activeElement;
        if (!active || active === document.body || active === document.documentElement) {
          try { message.focus({ preventScroll: true }); } catch (_) { message.focus(); }
        }
      }
    }
  });
  chat.appendChild(form);
  page.appendChild(chatOptions);
  page.appendChild(chat);
  if (state.status?.ai?.status === "test_only" && chatCapabilities?.structured_education === true) page.appendChild(testOptions);
  if (state.storageNotice) page.appendChild(callout(state.storageNotice, state.storageProblem ? "warning-note" : "note"));
  page.appendChild(actions);
  return heading;
}

function profileChoiceControl(question, selectedValue) {
  const group = el("fieldset", { className: "choice-list" });
  group.appendChild(el("legend", {}, question.title));
  for (const option of question.options) {
    const id = `profile-${question.key}-${option.value}`;
    const radio = el("input", { type: "radio", id, name: "profile-answer", value: option.value, checked: selectedValue === option.value });
    group.appendChild(el("label", { className: "choice", htmlFor: id }, [radio, el("span", {}, option.label)]));
  }
  group.appendChild(textElement("p", question.help, "field-help"));
  return group;
}

function profileOptionalAmount(parent, id, labelText, existingAnswer, options = {}) {
  const answer = existingAnswer && existingAnswer.estado === "declarado" ? existingAnswer.valor : null;
  const rawValue = answer && options.percent
    ? answer.min_pct
    : answer && options.flow ? answer.importe.min_eur
      : answer && answer.min_eur;
  const input = el("input", {
    type: "text", id, maxlength: "13", inputmode: "decimal", autocomplete: "off",
    value: rawValue || "", "aria-describedby": `${id}-help`
  });
  const entry = field(labelText, input, options.help || "Introduce una cifra o elige «No lo sé» u «Omitir» en este campo.", id);
  entry.querySelector(".field-help").id = `${id}-help`;
  parent.appendChild(entry);
  const status = el("select", { id: `${id}-state`, "aria-label": `Estado de ${labelText}` }, [
    el("option", { value: "" }, "Sin responder"),
    el("option", { value: "no_se", selected: existingAnswer && existingAnswer.estado === "no_se" }, "No lo sé"),
    el("option", { value: "omitido", selected: existingAnswer && existingAnswer.estado === "omitido" }, "Omitir")
  ]);
  const stateField = field("Respuesta", status, "Para continuar, introduce una cifra o elige «No lo sé» u «Omitir».", status.id);
  parent.appendChild(stateField);
  const setDisabled = () => {
    input.disabled = Boolean(status.value);
    if (status.value) input.value = "";
  };
  status.addEventListener("change", setDisabled);
  input.addEventListener("input", () => { if (input.value) status.value = ""; });
  setDisabled();
  return { input, status };
}

function readOptionalAnswer(control, makeKnown) {
  if (control.status.value === "no_se") return PROFILE_MODEL.makeAnswer("no_se");
  if (control.status.value === "omitido") return PROFILE_MODEL.makeAnswer("omitido");
  const raw = control.input.value.trim();
  if (!raw) return PROFILE_MODEL.makeAnswer("sin_preguntar");
  return makeKnown(raw);
}

function profileQuestionControl(question) {
  const current = PROFILE_MODEL.getAnswer(state.profile, question.key);
  const value = current && current.estado === "declarado" ? current.valor : null;
  if (question.kind === "amount" || question.kind === "flow") {
    const raw = value && question.kind === "flow" ? value.importe.min_eur : value && value.min_eur;
    const input = el("input", { type: "text", id: `profile-${question.key}`, maxlength: "13", inputmode: "decimal", autocomplete: "off", value: raw || "", "aria-describedby": `profile-${question.key}-help` });
    const wrapper = field(question.title, input, question.help, input.id);
    wrapper.querySelector(".field-help").id = `profile-${question.key}-help`;
    return {
      wrapper,
      readAnswer() {
        const rawValue = input.value.trim();
        if (!rawValue) return PROFILE_MODEL.makeAnswer("sin_preguntar");
        return question.kind === "flow" ? PROFILE_MODEL.makeFlowAnswer(rawValue, "mensual") : PROFILE_MODEL.makeAmountAnswer(rawValue);
      },
      focus: input
    };
  }
  if (question.kind === "experience") {
    const group = el("fieldset", { className: "choice-list" });
    group.appendChild(el("legend", {}, question.title));
    const selectedLevel = value && value.nivel;
    for (const option of question.options) {
      const id = `profile-${question.key}-${option.value}`;
      const radio = el("input", { type: "radio", id, name: "profile-answer", value: option.value, checked: selectedLevel === option.value });
      group.appendChild(el("label", { className: "choice", htmlFor: id }, [radio, el("span", {}, option.label)]));
    }
    group.appendChild(textElement("p", question.help, "field-help"));
    return {
      wrapper: group,
      readAnswer() {
        const level = group.querySelector('input[name="profile-answer"]:checked');
        if (!level) return undefined;
        // Ningún cuestionario pide ya temas de interés: el campo se envía vacío para
        // conservar la forma guardada sin inventar una selección.
        return PROFILE_MODEL.makeAnswer("declarado", { nivel: level.value, temas_interes: [] });
      },
      focus: group.querySelector('input[name="profile-answer"]')
    };
  }
  if (question.kind === "debt") {
    const wrapper = el("div", { className: "profile-nested-fields" });
    const group = el("fieldset", { className: "choice-list" });
    group.appendChild(el("legend", {}, question.title));
    const debtStatus = current && current.estado === "declarado" ? value.situacion : "";
    [["sin_deuda", "No tengo deuda declarada"], ["con_deuda", "Sí, estoy pagando deuda"]].forEach(([key, labelText]) => {
      const id = `profile-debt-${key}`;
      const radio = el("input", { type: "radio", id, name: "profile-debt-status", value: key, checked: debtStatus === key });
      group.appendChild(el("label", { className: "choice", htmlFor: id }, [radio, el("span", {}, labelText)]));
    });
    group.appendChild(textElement("p", question.help, "field-help"));
    wrapper.appendChild(group);
    const details = el("div", { className: "profile-nested-fields" });
    const balance = profileOptionalAmount(details, "profile-debt-balance", "Saldo total aproximado (€)", value && value.situacion === "con_deuda" ? value.saldo_eur : null, { help: "Opcional. Un saldo declarado de 0 € sigue siendo una deuda declarada." });
    const payment = profileOptionalAmount(details, "profile-debt-payment", "Cuota habitual mensual (€)", value && value.situacion === "con_deuda" ? value.cuota : null, { flow: true });
    const cost = profileOptionalAmount(details, "profile-debt-cost", "Coste anual aproximado (%)", value && value.situacion === "con_deuda" ? value.coste_anual_pct : null, { percent: true, help: "Opcional. Porcentaje entre 0 y 100; no saber el coste no equivale a 0 %." });
    const syncDetails = () => { details.hidden = !group.querySelector('input[name="profile-debt-status"]:checked') || group.querySelector('input[name="profile-debt-status"]:checked').value !== "con_deuda"; };
    group.addEventListener("change", syncDetails);
    syncDetails();
    wrapper.appendChild(details);
    return {
      wrapper,
      readAnswer() {
        const selected = group.querySelector('input[name="profile-debt-status"]:checked');
        if (!selected) return PROFILE_MODEL.makeAnswer("sin_preguntar");
        if (selected.value === "sin_deuda") return PROFILE_MODEL.makeAnswer("declarado", { situacion: "sin_deuda" });
        const balanceAnswer = readOptionalAnswer(balance, PROFILE_MODEL.makeAmountAnswer);
        const paymentAnswer = readOptionalAnswer(payment, (raw) => PROFILE_MODEL.makeFlowAnswer(raw, "mensual"));
        const costAnswer = readOptionalAnswer(cost, PROFILE_MODEL.makePercentAnswer);
        if (!balanceAnswer || !paymentAnswer || !costAnswer) return null;
        return PROFILE_MODEL.makeAnswer("declarado", { situacion: "con_deuda", saldo_eur: balanceAnswer, cuota: paymentAnswer, coste_anual_pct: costAnswer });
      },
      focus: group.querySelector('input[name="profile-debt-status"]')
    };
  }
  if (question.kind === "commitments") {
    const wrapper = el("div", { className: "profile-nested-fields" });
    const group = el("fieldset", { className: "choice-list" });
    group.appendChild(el("legend", {}, question.title));
    const commitmentStatus = value ? String(value.hay_compromiso) : "";
    [["false", "No"], ["true", "Sí"]].forEach(([key, labelText]) => {
      const id = `profile-commitment-${key}`;
      const radio = el("input", { type: "radio", id, name: "profile-commitment-status", value: key, checked: commitmentStatus === key });
      group.appendChild(el("label", { className: "choice", htmlFor: id }, [radio, el("span", {}, labelText)]));
    });
    group.appendChild(textElement("p", question.help, "field-help"));
    wrapper.appendChild(group);
    const details = el("div", { className: "profile-nested-fields" });
    const total = profileOptionalAmount(details, "profile-commitment-total", "Importe total aproximado (€)", value && value.hay_compromiso ? value.total_eur : null);
    const term = el("select", { id: "profile-commitment-term" }, [
      el("option", { value: "fecha_no_clara" }, "Fecha no clara / sin precisar"),
      el("option", { value: "menos_3_meses" }, "Menos de 3 meses"),
      el("option", { value: "3_6_meses" }, "3–6 meses"),
      el("option", { value: "6_12_meses" }, "6–12 meses")
    ]);
    if (value && value.hay_compromiso) term.value = value.plazo;
    details.appendChild(field("Plazo aproximado", term, "No hace falta indicar qué gasto o compra es.", term.id));
    const syncDetails = () => { details.hidden = !group.querySelector('input[name="profile-commitment-status"]:checked') || group.querySelector('input[name="profile-commitment-status"]:checked').value !== "true"; };
    group.addEventListener("change", syncDetails);
    syncDetails();
    wrapper.appendChild(details);
    return {
      wrapper,
      readAnswer() {
        const selected = group.querySelector('input[name="profile-commitment-status"]:checked');
        if (!selected) return PROFILE_MODEL.makeAnswer("sin_preguntar");
        if (selected.value === "false") return PROFILE_MODEL.makeAnswer("declarado", { hay_compromiso: false });
        const totalAnswer = readOptionalAnswer(total, PROFILE_MODEL.makeAmountAnswer);
        if (!totalAnswer) return null;
        return PROFILE_MODEL.makeAnswer("declarado", { hay_compromiso: true, total_eur: totalAnswer, plazo: term.value || "fecha_no_clara" });
      },
      focus: group.querySelector('input[name="profile-commitment-status"]')
    };
  }
  const selectedValue = value;
  return {
    wrapper: profileChoiceControl(question, selectedValue),
    readAnswer() {
      const chosen = document.querySelector('input[name="profile-answer"]:checked');
      return chosen
        ? question.kind === "capacity" ? PROFILE_MODEL.makeLossCapacityAnswer(chosen.value) : PROFILE_MODEL.makeAnswer("declarado", chosen.value)
        : undefined;
    },
    focus: null
  };
}

function profileQuestionKeysForMode() {
  if (state.profileMode === "core") return PROFILE_FIELDS;
  if (state.profileMode === "economy") return ECONOMIC_QUESTION_KEYS;
  if (state.profileMode === "risk") return RISK_QUESTION_KEYS;
  return [];
}

function currentProfileQuestion() {
  if (state.profileMode === "edit") return PROFILE_QUESTION_BY_KEY.get(state.profileEditKey) || null;
  const keys = profileQuestionKeysForMode();
  const key = keys[Math.max(0, Math.min(state.profileStep, keys.length - 1))];
  return PROFILE_QUESTION_BY_KEY.get(key) || null;
}

function profileLegacyFieldAnswered(question) {
  if (question && question.legacyKey && state.profileLegacy[question.legacyKey]) delete state.profileLegacy[question.legacyKey];
}

function recordProfileAnswer(key, answer) {
  if (!PROFILE_MODEL.setAnswer(state.profile, key, answer)) return false;
  profileLegacyFieldAnswered(PROFILE_QUESTION_BY_KEY.get(key));
  if (state.profileOptIn) {
    const result = autosaveProfileLocally();
    if (!result.ok && !result.snapshotWritten && result.reason !== "revoked_elsewhere") state.profileUnsaved = true;
  }
  if (state.profileMode === "edit") {
    state.profileMode = "summary";
    state.profileComplete = true;
    state.profileEditKey = null;
  } else {
    // Se confirma en un box con la pregunta y la respuesta antes de avanzar.
    state.profileConfirmKey = key;
  }
  render();
  return true;
}

function profileConfirmAnswered() {
  const keys = profileQuestionKeysForMode();
  state.profileConfirmKey = null;
  if (state.profileStep < keys.length - 1) state.profileStep += 1;
  else {
    state.profileMode = "summary";
    state.profileComplete = true;
  }
  render();
}

function enterProfileMode(mode, resume = false) {
  state.profileMode = mode;
  const firstPending = mode === "core" && resume ? PROFILE_FIELDS.findIndex(key => PROFILE_MODEL.getAnswer(state.profile, key).estado === "sin_preguntar") : 0;
  state.profileStep = Math.max(0, firstPending);
  state.profileConfirmKey = null;
  state.profileEditKey = null;
  state.profileComplete = false;
  render();
}

function renderLegacyAnswers(summary) {
  const legacyKeys = Object.keys(state.profileLegacy);
  if (!legacyKeys.length) return;
  const note = section("Respuestas anteriores sin equivalencia exacta", "Se conservaron para no convertir categorías antiguas en respuestas financieras nuevas. Revísalas o déjalas como legado local.", "data-panel");
  const list = el("ul", { className: "text-list" });
  const keyToQuestion = { objective: "respuestas.objetivo", horizon: "respuestas.horizonte", knowledge: "respuestas.experiencia", risk: "riesgo.tolerancia" };
  for (const oldKey of legacyKeys) {
    const question = PROFILE_QUESTION_BY_KEY.get(keyToQuestion[oldKey]);
    const label = PROFILE_MODEL.LEGACY_VALUES[oldKey] && PROFILE_MODEL.LEGACY_VALUES[oldKey][state.profileLegacy[oldKey]];
    const item = el("li");
    item.appendChild(document.createTextNode(`${question ? question.label : oldKey}: ${label || "Respuesta anterior"}. `));
    item.appendChild(button("Actualizar respuesta", () => {
      state.profileMode = "edit";
      state.profileEditKey = question.key;
      state.profileComplete = false;
      render();
    }, "text-button"));
    list.appendChild(item);
  }
  note.appendChild(list);
  summary.appendChild(note);
}

function renderProfileSummary(page) {
  const summary = section("Tu mapa para explorar", "Editable y descriptivo. Lo no respondido permanece así; no es un test ni una recomendación.", "summary-card");
  const list = el("dl", { className: "profile-summary" });
  PROFILE_FIELDS.forEach((key) => {
    const row = el("div", { className: "profile-summary-row" });
    row.appendChild(el("dt", {}, PROFILE_LABELS[key]));
    row.appendChild(el("dd", {}, displayProfileValue(key)));
    row.appendChild(button("Editar", () => {
      state.profileMode = "edit";
      state.profileEditKey = key;
      state.profileComplete = false;
      render();
    }, "text-button"));
    list.appendChild(row);
  });
  summary.appendChild(list);
  renderLegacyAnswers(summary);
  summary.appendChild(callout("Solo se guarda si das permiso explícito en Privacidad. Este mapa no se envía por defecto: solo saldrían los campos que marques y autorices en el chat, nunca el mapa completo. No solicita nombre, DNI, cuenta ni credenciales.", "info-note"));
  const continueToPai = routeLink("Continuar con Pai", "#inicio", "button button-primary");
  continueToPai.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    window.addEventListener("hashchange", () => {
      requestAnimationFrame(() => {
        if (location.hash === "#inicio") document.getElementById("chat-message")?.focus();
      });
    }, { once: true });
  });
  summary.appendChild(el("div", { className: "button-row" }, [
    button(PROFILE_FIELDS.some(key => PROFILE_MODEL.getAnswer(state.profile, key).estado === "sin_preguntar") ? "Continuar donde lo dejé" : "Revisar cuestionario", () => enterProfileMode("core", true), "button button-secondary"),
    continueToPai,
    routeLink("Seguir explorando", "#biblioteca", "button button-secondary")
  ]));
  page.appendChild(summary);
}

function renderProfileConfirmation(page, heading) {
  const keys = profileQuestionKeysForMode();
  const key = state.profileConfirmKey;
  const question = PROFILE_QUESTION_BY_KEY.get(key);
  const index = Math.max(0, keys.indexOf(key));
  const answer = PROFILE_MODEL.getAnswer(state.profile, key);
  const panel = el("section", { className: "question-panel profile-confirm" });
  panel.appendChild(textElement("p", "PREGUNTA ANTERIOR", "eyebrow"));
  panel.appendChild(el("div", { className: "step-progress" }, [
    el("progress", { max: keys.length, value: index + 1, "aria-label": `Pregunta ${index + 1} de ${keys.length} respondida` }),
    textElement("span", `Pregunta ${index + 1} de ${keys.length} respondida`)
  ]));
  panel.appendChild(el("h2", { className: "profile-confirm-question" }, question ? question.title : "Respuesta guardada"));
  const caja = el("div", { className: "profile-answer-box" });
  caja.appendChild(el("p", { className: "profile-answer-label" }, "Tu respuesta"));
  caja.appendChild(el("p", { className: "profile-answer-value" }, displayProfileValue(key, answer)));
  panel.appendChild(caja);
  const estado = answer && answer.estado;
  if (estado === "no_se" || estado === "omitido" || estado === "sin_preguntar") {
    panel.appendChild(textElement("p", "Puedes cambiarla cuando quieras; no se interpreta como un dato.", "small muted"));
  }
  const actions = el("div", { className: "button-row" });
  const ultima = index >= keys.length - 1;
  actions.appendChild(button(ultima ? "Continuar y revisar" : "Continuar", () => profileConfirmAnswered(), "button button-primary"));
  actions.appendChild(button("Cambiar respuesta", () => {
    state.profileConfirmKey = null;
    render();
  }, "button button-secondary"));
  panel.appendChild(actions);
  page.appendChild(panel);
  return heading;
}

function renderProfile() {
  const { page, heading } = pageFrame("Tu mapa · editable", "Tu mapa para explorar", "Cuatro preguntas: qué quieres explorar, tu horizonte, tu experiencia y un importe orientativo. Responde, elige «No lo sé» u «Omitir» para avanzar. Puedes pausar y retomar sin perder lo respondido.");
  if (state.profileMode === "summary" || state.profileComplete) {
    state.profileMode = "summary";
    renderProfileSummary(page);
    page.appendChild(el("p", { className: "small muted" }, "La biblioteca, el comparador, los escenarios y el ensayo se pueden usar sin responder ni guardar el mapa."));
    return heading;
  }
  if (state.profileConfirmKey && state.profileMode !== "edit") {
    renderProfileConfirmation(page, heading);
    return heading;
  }
  const question = currentProfileQuestion();
  if (!question) {
    state.profileMode = "summary";
    state.profileComplete = true;
    renderProfileSummary(page);
    return heading;
  }
  const keys = state.profileMode === "edit" ? [] : profileQuestionKeysForMode();
  const index = state.profileMode === "edit" ? 0 : state.profileStep;
  const panel = el("section", { className: "question-panel" });
  if (state.profileMode === "edit") {
    panel.appendChild(textElement("p", "EDITAR RESPUESTA", "eyebrow"));
  } else {
    const label = question.branch === "core" ? "1 · OBJETIVO Y CONOCIMIENTOS" : question.branch === "economy" ? "2 · SITUACIÓN ECONÓMICA" : "3 · RIESGO E IMPACTO DE PÉRDIDAS";
    panel.appendChild(textElement("p", label, "eyebrow"));
    const progressText = `${index + 1} de ${keys.length}`;
    panel.appendChild(el("div", { className: "step-progress" }, [
      el("progress", { max: keys.length, value: index + 1, "aria-label": `Pregunta ${progressText}` }),
      textElement("span", `Pregunta ${progressText}`)
    ]));
  }
  const control = profileQuestionControl(question);
  const form = el("form", { className: "profile-form" });
  form.appendChild(control.wrapper);
  const formError = textElement("p", "", "form-error");
  formError.id = "profile-error";
  formError.setAttribute("role", "alert");
  form.appendChild(formError);
  const actions = el("div", { className: "button-row" });
  actions.appendChild(button(state.profileMode === "edit" ? "Guardar respuesta" : index === keys.length - 1 ? "Terminar y revisar" : "Continuar", null, "button button-primary", { type: "submit" }));
  actions.appendChild(button("No lo sé", () => recordProfileAnswer(question.key, PROFILE_MODEL.makeAnswer("no_se")), "button button-secondary"));
  actions.appendChild(button("Omitir", () => recordProfileAnswer(question.key, PROFILE_MODEL.makeAnswer("omitido")), "button-link"));
  form.appendChild(actions);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (state.profileMode === "edit" && event.submitter && event.submitter.textContent === "Volver al resumen") {
      state.profileMode = "summary";
      state.profileComplete = true;
      state.profileEditKey = null;
      render();
      return;
    }
    const answer = control.readAnswer();
    if (!PROFILE_MODEL.canContinueAnswer(question.key, answer)) {
      formError.textContent = "Responde o selecciona una opción válida antes de continuar. Si no sabes o prefieres no responder, elige «No lo sé» u «Omitir». En los detalles visibles, indica un valor válido o elige su estado explícitamente.";
      const focusTarget = control.focus || control.wrapper.querySelector("input, select");
      if (focusTarget) {
        focusTarget.setAttribute("aria-invalid", "true");
        const ids = new Set((focusTarget.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
        ids.add(formError.id);
        focusTarget.setAttribute("aria-describedby", [...ids].join(" "));
        focusTarget.focus();
      }
      return;
    }
    recordProfileAnswer(question.key, answer);
  });
  panel.appendChild(form);
  const why = el("details", { className: "why-question" });
  why.appendChild(el("summary", {}, "¿Por qué lo preguntamos?"));
  const storageHelp = state.profileOptIn
    ? "Por tu permiso previo, los cambios se intentan guardar automáticamente en este navegador. Este permiso no autoriza ningún envío remoto."
    : state.storageProblem
      ? "La respuesta actual está en memoria, pero el estado del almacenamiento local es desconocido y podrían quedar copias. Nunca se incorpora automáticamente a una consulta."
      : "La respuesta solo queda en memoria en esta pestaña hasta que decidas guardarla; nunca se incorpora automáticamente a una consulta.";
  why.appendChild(textElement("p", `${question.help} ${storageHelp}`));
  panel.appendChild(why);
  page.appendChild(panel);
  const actionsBelow = el("div", { className: "button-row" });
  if (state.profileMode !== "edit") actionsBelow.appendChild(button("Pausar y ver el resumen", () => {
    state.profileMode = "summary";
    state.profileComplete = true;
    state.profileEditKey = null;
    render();
  }, "button button-secondary"));
  if (state.profileMode === "edit") actionsBelow.appendChild(button("Volver al resumen", () => {
    state.profileMode = "summary";
    state.profileComplete = true;
    state.profileEditKey = null;
    render();
  }, "button-link"));
  else if (index > 0) actionsBelow.appendChild(button("Pregunta anterior", () => { state.profileConfirmKey = null; state.profileStep = Math.max(0, state.profileStep - 1); render(); }, "button-link"));
  actionsBelow.appendChild(routeLink("Volver a explorar sin completar", "#biblioteca", "button-link"));
  page.appendChild(actionsBelow);
  return heading;
}


function renderSelectionTray(parent) {
  const tray = el("section", { className: "selection-tray", "aria-label": "Selección para comparar" });
  const title = el("p");
  title.appendChild(el("strong", {}, `Selección para comparar · ${state.selectedIds.length} de 4`));
  tray.appendChild(title);
  if (state.selectedIds.length) {
    const list = el("ul", { className: "selection-tags" });
    for (const id of state.selectedIds) {
      const product = state.catalogueCache.get(id);
      const item = el("li");
      item.appendChild(document.createTextNode(product ? productName(product) : id));
      item.appendChild(button("Quitar", () => toggleSelection(id), "button-link"));
      list.appendChild(item);
    }
    tray.appendChild(list);
  }
  const help = state.selectedIds.length < 2 ? "Elige al menos dos candidatos. La selección no cambia sin que pulses aquí." : "La comparación mantiene el orden de selección y no calcula un ganador.";
  tray.appendChild(textElement("p", `${help} La selección y los filtros son temporales y se pierden al recargar la página.`, "small"));
  tray.appendChild(el("div", { className: "button-row" }, button(state.selectedIds.length >= 2 ? "Preparar comparación" : "Selecciona 2 para comparar", () => { window.location.hash = "#comparar"; }, "button button-secondary", { disabled: state.selectedIds.length < 2 })));
  parent.appendChild(tray);
}

function toggleSelection(id) {
  const current = state.selectedIds.indexOf(id);
  if (current >= 0) state.selectedIds.splice(current, 1);
  else if (state.selectedIds.length < 4) state.selectedIds.push(id);
  else {
    const message = document.getElementById("selection-message");
    if (message) message.textContent = "El máximo de la comparación es cuatro candidatos.";
    return;
  }
  state.compareResult = null;
  state.compareIds = [];
  state.compareError = null;
  state.compareRequestId += 1;
  state.compareBusy = false;
  state.diagnosis = { requestId: state.diagnosis.requestId + 1, ids: [], busy: false, error: false, result: null };
  if (state.route === "biblioteca") {
    renderLibrarySelection();
    renderCatalogueResults();
  } else if (state.route === "comparar") {
    renderComparePage(false);
  }
}

function renderLibrarySelection() {
  const holder = document.getElementById("library-selection");
  if (!holder) return;
  holder.replaceChildren();
  renderSelectionTray(holder);
}

function conditionOf(productId, metric) {
  const entry = state.conditions.byId.get(productId);
  if (!entry || !Array.isArray(entry.conditions)) return null;
  return entry.conditions.find((item) => item && item.metric === metric) || null;
}

function conditionConsultedAt(productId) {
  const rate = conditionOf(productId, "annual_rate_percent");
  if (rate && typeof rate.retrieved_at === "string" && rate.retrieved_at) return rate.retrieved_at;
  const entry = state.conditions.byId.get(productId);
  return entry && entry.source && typeof entry.source.retrieved_at === "string" ? entry.source.retrieved_at : "";
}

function conditionValidityText(productId) {
  const rate = conditionOf(productId, "annual_rate_percent");
  if (!rate) return "Sin vigencia documentada para la tasa.";
  const prefix = rate.state === "stale" ? "vencida · " : "";
  if (rate.effective_from && rate.effective_to) return `${prefix}del ${rate.effective_from} al ${rate.effective_to}`;
  if (rate.effective_to) return `${prefix}hasta ${rate.effective_to}`;
  if (rate.effective_from) return `${prefix}desde ${rate.effective_from}, sin fecha de fin documentada`;
  return "sin fechas de vigencia documentadas";
}

function productEffectiveDate(product) {
  if (!product || product.origin === "curated_conditions") return "";
  return typeof product.as_of === "string" && product.as_of ? product.as_of : "";
}

function formatRate(value) {
  const formatted = window.PaideiaConditionsLoad.formatRate(value);
  return formatted || "No disponible";
}

function conditionStateText(condition) {
  const reasons = {
    CURATED_OFFICIAL: "fuente oficial",
    CURATED_SECONDARY_PRESS: "fuente secundaria",
    DOCUMENTED_PROMO_TAE: "promoción documentada",
    DOCUMENTED_RATE: "tasa documentada",
    DOCUMENTED_REPORTED_TERMS_SNAPSHOT: "condiciones del documento",
    PROMOTION_EXPIRED: "vigencia terminada",
    SOURCE_CONFLICT: "fuentes en conflicto",
    MULTIPLE_RATES_DOCUMENTED: "varias tasas en el mismo documento",
    IDENTITY_NOT_VERIFIED: "identidad no verificada",
    RATE_NOT_DOCUMENTED: "sin tasa en el documento",
    RATE_UNPARSEABLE: "tasa no interpretable",
    RETRIEVAL_TOO_OLD: "consulta demasiado antigua",
    CURATED_TERM: "plazo documentado",
    TERM_NOT_DOCUMENTED: "sin plazo documentado",
    MULTIPLE_TERMS_DOCUMENTED: "varios plazos en el documento",
    DOCUMENTED_OFFICIAL_DOCUMENT_IDENTITY: "documento oficial"
  };
  const stateLabel = { known: "documentada por la fuente", stale: "vencida", conflict: "en conflicto", unknown: "sin dato" }[condition.state] || condition.state;
  return `${stateLabel}; ${reasons[condition.reason] || "documentado"}`;
}

function rateSummary(productId) {
  return window.PaideiaConditionsLoad.rateSummary(state.conditions, conditionOf(productId, "annual_rate_percent"));
}

async function loadConditions(force = false) {
  if (!force && (state.conditions.loaded || state.conditions.loading)) return;
  if (state.conditions.loading) return;
  state.conditions = window.PaideiaConditionsLoad.begin();
  try {
    state.conditions = window.PaideiaConditionsLoad.succeed(await apiRequest(API.conditions));
  } catch (error) {
    state.conditions = window.PaideiaConditionsLoad.fail(error);
  }
  if (state.route === "biblioteca") { renderCuratedCatalogue(); renderCatalogueResults(); renderProductDetail(); }
  if (state.route === "comparar") renderComparisonResult();
  if (state.route === "simulacion") {
    const amountInput = document.getElementById("simulation-amount");
    const draft = amountInput ? amountInput.value : null;
    const snapshot = captureFocus();
    render({ preserveFocus: true });
    if (draft !== null) {
      const nextInput = document.getElementById("simulation-amount");
      if (nextInput) nextInput.value = draft;
    }
    restoreFocus(snapshot, document.getElementById("main-content"));
  }
}

function renderCuratedCatalogue() {
  const holder = document.getElementById("curated-results");
  if (!holder) return;
  holder.replaceChildren();
  const items = [...state.conditions.byId.values()].filter((entry) => entry && entry.origin === "curated_conditions");
  if (!items.length) return;
  holder.appendChild(el("h2", {}, "Productos con condiciones transcritas"));
  holder.appendChild(textElement("p", "No forman parte de los 20 candidatos originales: se añadieron desde una fuente con URL y fecha de consulta.", "small muted"));
  const list = el("div", { className: "result-list" });
  for (const entry of items) {
    const product = {
      id: entry.product_id,
      name: entry.display_name,
      family: entry.family,
      issuer: entry.provider || null,
      identity_state: entry.identity_state === "verified" ? "verified" : "proposed",
      primary_url: entry.source && entry.source.url,
      as_of: entry.source && entry.source.retrieved_at,
      conditions_state: "pending",
      conflicts: [],
      unknown_fields: []
    };
    state.catalogueCache.set(product.id, product);
    list.appendChild(productCard(product));
  }
  holder.appendChild(list);
}

function productCard(product) {
  const card = el("article", { className: "product-card" });
  card.appendChild(el("h3", {}, productName(product)));
  const meta = el("div", { className: "product-meta" });
  meta.appendChild(el("span", {}, familyLabel(product.family)));
  meta.appendChild(el("span", {}, issuerLabel(product)));
  if (product.isin) meta.appendChild(el("span", {}, `ISIN ${product.isin}`));
  card.appendChild(meta);
  const badges = el("div", { className: "badge-row" }, [badge(identityLabel(product), identityKind(product)), badge(conditionsLabel(product), "pending")]);
  card.appendChild(badges);
  const rate = rateSummary(product.id);
  const rateLine = textElement("p", rate.text, "small");
  rateLine.id = `rate-${product.id}`;
  card.appendChild(rateLine);
  const rateCondition = conditionOf(product.id, "annual_rate_percent");
  if (rateCondition && Array.isArray(rateCondition.notes)) {
    for (const note of rateCondition.notes.slice(0, 2)) {
      if (typeof note === "string" && note.trim()) card.appendChild(textElement("p", note.slice(0, 200), "small muted"));
    }
  }
  card.appendChild(textElement("p", "Candidato de investigación · No es una oferta publicable. La tasa solo se muestra si está documentada con fuente y fecha.", "small muted"));
  appendPrimarySource(card, product);
  const conditionEntry = state.conditions.byId.get(product.id);
  const conditionSourceUrl = conditionEntry && conditionEntry.source && isSafePrimaryUrl(conditionEntry.source.url)
    ? conditionEntry.source.url : "";
  if (conditionSourceUrl) {
    card.appendChild(el("p", { className: "source-line" }, [
      document.createTextNode("Fuente de las condiciones: "),
      el("a", { href: conditionSourceUrl, target: "_blank", rel: "noopener noreferrer" }, conditionSourceUrl),
      document.createTextNode(conditionEntry.source.retrieved_at ? ` · consultada el ${conditionEntry.source.retrieved_at}` : " · sin fecha de consulta declarada"),
    ]));
  }
  const conflicts = Array.isArray(product.conflicts) ? product.conflicts.filter((item) => typeof item === "string").slice(0, 5) : [];
  const unknownFields = Array.isArray(product.unknown_fields) ? product.unknown_fields.filter((item) => typeof item === "string").slice(0, 12) : [];
  const review = el("div", { className: "product-review" });
  if (conflicts.length) {
    review.appendChild(textElement("p", "Conflictos que siguen abiertos:", "small"));
    for (const conflict of conflicts) review.appendChild(textElement("p", conflict.slice(0, 200), "small muted"));
  }
  if (unknownFields.length) {
    review.appendChild(textElement("p", "Campos desconocidos:", "small"));
    for (const field of unknownFields) review.appendChild(textElement("p", field.slice(0, 120), "small muted"));
  }
  if (!conflicts.length && !unknownFields.length) {
    review.appendChild(textElement("p", "La respuesta de API no enumera conflictos ni campos desconocidos; eso no equivale a que no existan.", "small muted"));
  }
  review.appendChild(textElement("p", "Identidad y condiciones se muestran por separado; los huecos no se completan.", "small muted"));
  card.appendChild(review);
  const actions = el("div", { className: "product-actions" });
  const selected = state.selectedIds.includes(product.id);
  const choose = button(selected ? "Quitar de comparar" : "Añadir a comparar", () => toggleSelection(product.id), "button button-secondary", { pressed: selected, disabled: !selected && state.selectedIds.length >= 4 });
  choose.id = `choose-${product.id}`;
  const details = button("Ver detalle", () => loadProductDetail(product.id), "button-link");
  details.id = `detail-${product.id}`;
  actions.append(choose, details);
  card.appendChild(actions);
  return card;
}

function renderCatalogueResults() {
  const results = document.getElementById("catalogue-results");
  if (!results || state.route !== "biblioteca") return;
  const snapshot = captureFocus();
  results.replaceChildren();
  results.setAttribute("tabindex", "-1");
  results.appendChild(el("h2", { className: "visually-hidden" }, "Candidatos del catálogo"));
  try {
    renderCatalogueResultsBody(results);
  } finally {
    restoreFocus(snapshot, results);
  }
}

function renderCatalogueResultsBody(results) {
  results.setAttribute("aria-busy", String(state.library.loading));
  if (state.library.loading) {
    results.appendChild(textElement("p", "Cargando candidatos del catálogo local…", "loading-state"));
    return;
  }
  if (state.library.error) {
    results.appendChild(errorBox(apiErrorText(state.library.error), () => loadCatalogueForLibrary(), { text: "Ver estado local", hash: "#inicio" }));
    return;
  }
  if (!state.library.loaded) {
    results.appendChild(textElement("p", "El catálogo aún no se ha consultado.", "loading-state"));
    return;
  }
  const conditionsNotice = window.PaideiaConditionsLoad.catalogueNotice(state.conditions);
  if (conditionsNotice) {
    results.appendChild(conditionsNotice.kind === "error"
      ? errorBox(conditionsNotice.message, conditionsNotice.retry ? () => loadConditions(true) : null)
      : textElement("p", conditionsNotice.message, "loading-state"));
  }
  const countText = state.library.count === 1 ? "1 candidato" : `${state.library.count} candidatos`;
  results.appendChild(textElement("p", `${countText} devueltos por la API · Todos son metadatos de investigación interna.`, "small muted"));
  if (!state.library.items.length) {
    const empty = el("div", { className: "info-note", role: "status" });
    empty.appendChild(textElement("p", "No hay resultados con estos filtros."));
    empty.appendChild(textElement("p", "Quita la búsqueda o cambia de familia; no se rellenan resultados con datos de muestra.", "small"));
    empty.appendChild(button("Quitar filtros", () => {
      state.library.query = "";
      state.library.family = "";
      const search = document.getElementById("catalogue-search");
      const family = document.getElementById("catalogue-family");
      if (search) search.value = "";
      if (family) family.value = "";
      loadCatalogueForLibrary();
    }, "button button-secondary"));
    results.appendChild(empty);
    return;
  }
  const documented = (id) => ((state.conditions.byId.get(id) || {}).conditions || []).length > 0;
  const withRate = (id) => {
    const rate = conditionOf(id, "annual_rate_percent");
    return Boolean(rate) && rate.state === "known";
  };
  const todos = state.library.items.filter((product) => product && typeof product.id === "string");
  const conDatos = todos.filter((product) => documented(product.id));
  const conTasa = todos.filter((product) => withRate(product.id));
  results.appendChild(textElement("p",
    `${conTasa.length} de ${todos.length} con tasa documentada · ${conDatos.length} con alguna condición documentada. El resto solo aporta metadatos de identidad.`,
    "small muted"));
  const visibles = state.library.onlyDocumented === true ? conTasa : todos;
  if (!visibles.length) {
    results.appendChild(callout("Ningún candidato de esta búsqueda tiene una tasa documentada. Quita el filtro para ver los metadatos disponibles.", "info-note"));
    return;
  }
  const list = el("div", { className: "result-list" });
  visibles.forEach((product) => {
    state.catalogueCache.set(product.id, product);
    list.appendChild(productCard(product));
  });
  results.appendChild(list);
}

async function loadCatalogueForLibrary() {
  const invalid = Array.from(state.library.query).length > 100;
  const feedback = document.getElementById("catalogue-search-error");
  const search = document.getElementById("catalogue-search");
  if (feedback) feedback.textContent = invalid ? "La búsqueda admite como máximo 100 caracteres. Acorta el texto para consultar." : "";
  if (search) search.setAttribute("aria-invalid", String(invalid));
  if (invalid) {
    state.library.requestId += 1;
    state.library.loading = false;
    renderCatalogueResults();
    return;
  }
  const seq = ++state.library.requestId;
  state.library.loading = true;
  state.library.error = null;
  state.library.loaded = false;
  announce("Cargando catálogo…");
  renderCatalogueResults();
  const params = new URLSearchParams();
  if (state.library.query.trim()) params.set("q", state.library.query.trim());
  if (state.library.family) params.set("family", state.library.family);
  const path = `${API.catalogue}${params.toString() ? `?${params.toString()}` : ""}`;
  try {
    const data = await apiRequest(path);
    if (seq !== state.library.requestId) return;
    if (!Array.isArray(data.items)) throw new ApiFailure("El catálogo no devolvió una lista de candidatos.", 200, "INVALID_CATALOGUE", false);
    state.library.items = data.items;
    state.library.count = Number.isFinite(data.count) ? data.count : data.items.length;
    state.library.loaded = true;
  } catch (error) {
    if (seq !== state.library.requestId) return;
    state.library.error = error;
  } finally {
    if (seq === state.library.requestId) {
      state.library.loading = false;
      renderCatalogueResults();
      renderLibrarySelection();
      announce(state.library.error
        ? "No se pudo cargar el catálogo"
        : `${state.library.count === 1 ? "1 candidato" : `${state.library.count} candidatos`} en la biblioteca`);
    }
  }
}

function loadProductDetail(id) {
  state.detail = { id, product: null, loading: true, error: null, requestId: state.detail.requestId + 1 };
  const seq = state.detail.requestId;
  announce("Cargando ficha…");
  renderProductDetail();
  apiRequest(`${API.product}${encodeURIComponent(id)}`).then((data) => {
    if (state.detail.requestId !== seq) return;
    if (!data.product || typeof data.product !== "object") throw new ApiFailure("La respuesta no incluyó los metadatos del producto.", 200, "INVALID_PRODUCT", false);
    state.detail.product = data.product;
    if (typeof data.product.id === "string") state.catalogueCache.set(data.product.id, data.product);
  }).catch((error) => {
    if (state.detail.requestId === seq) state.detail.error = error;
  }).finally(() => {
    if (state.detail.requestId === seq) {
      state.detail.loading = false;
      renderProductDetail();
      const target = document.getElementById("product-detail");
      if (target) {
        // El panel vive bajo la lista: si no se trae a la vista, «Ver detalle»
        // parece no hacer nada.
        target.scrollIntoView({ block: "start", behavior: "smooth" });
        target.focus({ preventScroll: true });
      }
      announce(state.detail.error ? "No se pudo cargar la ficha" : "Ficha cargada");
    }
  });
}

function appendList(parent, values, emptyText) {
  if (!Array.isArray(values) || !values.length) {
    parent.appendChild(textElement("p", emptyText, "small muted"));
    return;
  }
  const list = el("ul", { className: "text-list" });
  values.forEach((value) => {
    if (typeof value === "string" && value.trim()) list.appendChild(el("li", {}, value));
  });
  parent.appendChild(list);
}

function renderProductDetail() {
  const holder = document.getElementById("product-detail");
  if (!holder || state.route !== "biblioteca") return;
  holder.replaceChildren();
  holder.setAttribute("tabindex", "-1");
  holder.setAttribute("aria-busy", String(state.detail.loading));
  holder.appendChild(textElement("p", "Ficha abierta · detalle consultado a la API", "eyebrow"));
  if (state.detail.loading) { holder.appendChild(textElement("p", "Cargando el detalle del candidato…", "loading-state")); return; }
  if (state.detail.error) { holder.appendChild(errorBox(apiErrorText(state.detail.error), () => loadProductDetail(state.detail.id))); return; }
  const product = state.detail.product;
  if (!product) { holder.appendChild(textElement("p", "Elige «Ver detalle» en una ficha para consultar sus metadatos.")); return; }
  const title = textElement("h2", productName(product));
  holder.appendChild(title);
  const chips = el("div", { className: "badge-row" }, [badge(identityLabel(product), identityKind(product)), badge(conditionsLabel(product), "pending")]);
  holder.appendChild(chips);
  const conditionsFailed = Boolean(state.conditions.error);
  const pairs = [
    ["Familia", familyLabel(product.family)],
    ["Emisor / marca", issuerLabel(product)],
    ["ISIN", product.isin || "No indicado en los metadatos"],
    ["Fecha efectiva del producto", productEffectiveDate(product) || "No consta una fecha efectiva del producto en los metadatos."],
    ["Consulta de la condición", conditionsFailed ? "No disponible: fallo al cargar las condiciones documentadas." : (conditionConsultedAt(product.id) || "No consta fecha de consulta de la condición.")],
    ["Vigencia de la condición", conditionsFailed ? "No disponible: fallo al cargar las condiciones documentadas." : conditionValidityText(product.id)],
    ["Publicación", product.publication_ready === true ? "Estado indicado por API" : "No listo para publicar"],
    ["Alcance", "Identidad de candidato; no acredita condiciones vigentes, elegibilidad ni disponibilidad"]
  ];
  const dl = el("dl", { className: "detail-list" });
  for (const [label, value] of pairs) dl.append(el("dt", {}, label), el("dd", {}, value));
  holder.appendChild(dl);
  appendPrimarySource(holder, product);
  const conditionsNotice = window.PaideiaConditionsLoad.catalogueNotice(state.conditions);
  if (conditionsNotice && conditionsNotice.kind === "error") {
    holder.appendChild(errorBox(conditionsNotice.message, () => loadConditions(true)));
  }
  const conditionEntry = state.conditions.byId.get(product.id);
  const conditionStates = conditionEntry && Array.isArray(conditionEntry.conditions)
    ? conditionEntry.conditions.map((condition) => condition && condition.state) : [];
  const allConditionsDocumented = conditionStates.length > 0 && conditionStates.every((item) => item === "known");
  if (conditionEntry && Array.isArray(conditionEntry.conditions) && conditionEntry.conditions.length) {
    const allDocumented = allConditionsDocumented;
    const block = section(
      allDocumented ? "Condiciones documentadas" : "Condiciones declaradas, no todas documentadas",
      allDocumented
        ? "Solo lo que consta en una fuente con fecha; los huecos no se rellenan."
        : "Los estados vencida, en conflicto o sin dato se muestran tal cual; no se presentan como documentados ni como oferta vigente.",
      "data-panel");
    const list = el("ul", { className: "detail-list" });
    for (const condition of conditionEntry.conditions) {
      const rowText = conditionRowText(condition);
      if (!rowText) continue;
      let text = `${rowText} · ${conditionStateText(condition)}`;
      if (condition.effective_to) text += ` · vigencia hasta ${condition.effective_to}`;
      if (Array.isArray(condition.notes) && condition.notes.length) {
        text += ` · ${condition.notes.filter((note) => typeof note === "string").join(" ").slice(0, 400)}`;
      }
      const item = el("li", {}, text);
      list.appendChild(item);
    }
    block.appendChild(list);
    if (Array.isArray(conditionEntry.rate_tiers) && conditionEntry.rate_tiers.length > 1) {
      const tiers = el("ul", { className: "detail-list" });
      for (const tier of conditionEntry.rate_tiers) {
        tiers.appendChild(el("li", {}, `${formatRate(tier.tae)} TAE / ${formatRate(tier.tin)} TIN · ${tier.condition_label || tier.condition}`));
      }
      block.appendChild(textElement("p", "Tramos de la misma oferta, con su requisito:", "small"));
      block.appendChild(tiers);
    }
    if (conditionEntry.source && isSafePrimaryUrl(conditionEntry.source.url)) {
      block.appendChild(el("p", { className: "source-line" }, [
        document.createTextNode("Fuente de las condiciones: "),
        el("a", { href: conditionEntry.source.url, target: "_blank", rel: "noopener noreferrer" }, conditionEntry.source.url)
      ]));
    }
    holder.appendChild(block);
  } else if (conditionEntry && conditionEntry.source && isSafePrimaryUrl(conditionEntry.source.url)) {
    const block = section("Fuente de las condiciones", "Documenta las condiciones declaradas; no acredita por sí sola que la oferta siga abierta.", "data-panel");
    block.appendChild(el("p", { className: "source-line" }, [
      document.createTextNode("Fuente de las condiciones: "),
      el("a", { href: conditionEntry.source.url, target: "_blank", rel: "noopener noreferrer" }, conditionEntry.source.url),
      document.createTextNode(conditionEntry.source.retrieved_at ? ` · consultada el ${conditionEntry.source.retrieved_at}` : " · sin fecha de consulta declarada"),
    ]));
    if (conditionEntry.conditions_state && conditionEntry.conditions_state !== "documented") {
      block.appendChild(textElement("p", "Las condiciones no constan como documentadas y vigentes; no se presentan como oferta.", "field-help"));
    }
    holder.appendChild(block);
  }
  const conflicts = section("Conflictos que siguen abiertos", "No se resuelven ni se corrigen en silencio.", "data-panel");
  appendList(conflicts, product.conflicts, "La respuesta de API no enumera conflictos.");
  holder.appendChild(conflicts);
  const unknown = section("Datos que siguen desconocidos", "La ausencia de un campo no equivale a cero ni a ausencia de riesgo.", "data-panel");
  appendList(unknown, product.unknown_fields, "La respuesta de API no enumera campos desconocidos.");
  holder.appendChild(unknown);
  holder.appendChild(callout(allConditionsDocumented && conditionEntry && conditionEntry.source && isSafePrimaryUrl(conditionEntry.source.url)
    ? "Las condiciones mostradas constan en la fuente citada; no acreditan disponibilidad, elegibilidad ni que la oferta siga abierta. Ningún dato se completa por inferencia."
    : "Lo mostrado son condiciones declaradas o datos ausentes, no una oferta vigente: una tasa vencida, en conflicto o sin dato se muestra tal cual y no acredita disponibilidad ni elegibilidad.", "warning-note"));
  const concepts = el("p", {}, "Entender los conceptos: ");
  for (const key of ["tae", "tin", "liquidez", "riesgo"]) concepts.appendChild(window.ContextHelp.createHelp(key));
  holder.appendChild(concepts);
}

function renderLibrary() {
  const { page, heading } = pageFrame("Explorar · catálogo interno", "Biblioteca de candidatos", "Busca y filtra por familia. Son 20 candidatos de investigación interna si la API devuelve el conjunto completo; ninguno está listo para publicar.");
  page.appendChild(callout("Solo se muestran tasas documentadas con fuente y fecha. «Oferta vencida», «conflicto entre fuentes» o «sin tasa documentada» se muestran tal cual: no se completan huecos ni se convierten en ofertas publicables.", "warning-note"));
  const controls = el("div", { className: "catalogue-controls" });
  const search = el("input", { type: "search", id: "catalogue-search", maxlength: 100, autocomplete: "off", value: state.library.query, "aria-describedby": "catalogue-search-error" });
  controls.appendChild(field("Buscar por nombre o emisor", search, "La consulta se envía solo a la API local.", search.id));
  controls.appendChild(el("p", { id: "catalogue-search-error", className: "form-error", role: "status" }));
  const select = el("select", { id: "catalogue-family" });
  select.appendChild(el("option", { value: "" }, "Todas las familias"));
  Object.entries(FAMILIES).forEach(([value, label]) => select.appendChild(el("option", { value, selected: state.library.family === value }, label)));
  controls.appendChild(field("Familia", select, "Familias del contrato local.", select.id));
  const onlyDocumented = el("input", { type: "checkbox", id: "catalogue-only-documented", checked: state.library.onlyDocumented === true });
  const onlyLabel = el("label", { className: "choice", htmlFor: "catalogue-only-documented" }, [onlyDocumented, el("span", {}, "Solo con tasa documentada")]);
  onlyDocumented.addEventListener("change", () => {
    state.library.onlyDocumented = onlyDocumented.checked;
    renderCatalogueResults();
  });
  controls.appendChild(onlyLabel);
  page.appendChild(controls);
  const selection = el("div", { id: "library-selection" });
  page.appendChild(selection);
  const selectionMessage = textElement("p", "", "form-error");
  selectionMessage.id = "selection-message";
  selectionMessage.setAttribute("role", "status");
  page.appendChild(selectionMessage);
  const results = el("section", { id: "catalogue-results", className: "catalogue-results", "aria-label": "Candidatos del catálogo" });
  page.appendChild(results);
  // La ficha abierta va junto a la lista de candidatos, no al final del documento.
  const detail = el("section", { id: "product-detail", className: "data-panel detail-panel", "aria-label": "Detalle del candidato", tabindex: -1 });
  page.appendChild(detail);
  const curatedSection = el("section", { id: "curated-results", className: "catalogue-results", "aria-label": "Productos con condiciones transcritas" });
  page.appendChild(curatedSection);
  search.addEventListener("input", () => {
    state.library.query = search.value;
    clearTimeout(state.libraryTimer);
    if (Array.from(search.value).length > 100) loadCatalogueForLibrary();
    else state.libraryTimer = window.setTimeout(() => loadCatalogueForLibrary(), 280);
  });
  select.addEventListener("change", () => {
    state.library.family = select.value;
    loadCatalogueForLibrary();
  });
  renderLibrarySelection();
  renderCatalogueResults();
  renderProductDetail();
  if (Array.from(state.library.query).length > 100 || !state.library.loaded || state.library.error) loadCatalogueForLibrary();
  loadConditions();
  return heading;
}

function renderCompareSelection(target) {
  target.replaceChildren();
  if (!state.selectedIds.length) {
    target.appendChild(textElement("p", "Todavía no hay candidatos seleccionados."));
    target.appendChild(routeLink("Elegir candidatos en la biblioteca", "#biblioteca", "button button-secondary"));
    return;
  }
  const list = el("div", { className: "compare-selection", "aria-label": "Candidatos seleccionados" });
  state.selectedIds.forEach((id) => {
    const product = state.catalogueCache.get(id);
    const item = el("span", { className: "compare-product-remove" });
    item.appendChild(document.createTextNode(product ? productName(product) : id));
    item.appendChild(button("Quitar", () => toggleSelection(id), "button-link"));
    list.appendChild(item);
  });
  target.appendChild(list);
  target.appendChild(textElement("p", `${state.selectedIds.length} de 4 seleccionados · se requieren 2 a 4 IDs distintos.`, "small muted"));
  if (state.selectedIds.length < 2) target.appendChild(routeLink("Añadir otro candidato", "#biblioteca", "button-link"));
}

function safeComparisonProduct(product) {
  return product && typeof product.id === "string" && typeof product.name === "string";
}

function comparisonCard(product) {
  const card = el("article", { className: "comparison-product" });
  card.appendChild(el("h3", {}, productName(product)));
  card.appendChild(textElement("p", `${familyLabel(product.family)} · ${issuerLabel(product)}`, "comparison-issuer"));
  card.appendChild(el("div", { className: "badge-row" }, [badge(identityLabel(product), identityKind(product)), badge(conditionsLabel(product), "pending")]));
  const rows = el("dl", { className: "comparison-rows" });
  const rate = rateSummary(product.id);
  const term = conditionOf(product.id, "term_months");
  const fields = [
    ["ISIN", product.isin || "No indicado en el metadato"],
    ["Disponibilidad / liquidez", "Desconocida en los metadatos disponibles."],
    ["Plazo", term && term.state === "known" ? `${term.value} meses (documentado)` : "No disponible en la respuesta de comparación."],
    ["Costes", "No disponibles; no se infieren."],
    ["Condiciones / garantía", "Pendientes de validación; no se infieren."],
    ["Posible pérdida", "No evaluada en estos metadatos; no se deduce por familia."],
    ["Rendimiento", rate.text],
    ["Fecha de consulta de la condición", conditionConsultedAt(product.id) || "No consta fecha de consulta de la condición."],
    ["Vigencia de la condición", conditionValidityText(product.id)],
    ["Fecha efectiva del producto", productEffectiveDate(product) || "No consta una fecha efectiva del producto en los metadatos."]
  ];
  for (const [label, value] of fields) rows.append(el("dt", {}, label), el("dd", {}, value));
  card.appendChild(rows);
  appendPrimarySource(card, product);
  const unknown = el("details");
  unknown.appendChild(el("summary", {}, "Campos pendientes de conocer"));
  appendList(unknown, product.unknown_fields, "No enumerados por esta respuesta.");
  card.appendChild(unknown);
  const conflicts = el("details");
  conflicts.appendChild(el("summary", {}, "Conflictos"));
  appendList(conflicts, product.conflicts, "No enumerados por esta respuesta.");
  card.appendChild(conflicts);
  const rateEntry = conditionOf(product.id, "annual_rate_percent");
  if (rateEntry && rateEntry.state === "known" && window.PaideiaConditionsLoad.formatRate(rateEntry.value)) {
    const termEntry = conditionOf(product.id, "term_months");
    const years = termEntry && termEntry.state === "known" ? Math.max(1, Math.round(Number(termEntry.value) / 12)) : 1;
    const explore = button("Explorar escenarios con esta tasa", () => {
      const conditionEntry = state.conditions.byId.get(product.id);
      const source = window.PaideiaScenarioProvenance.buildSource({
        product: { id: product.id, name: productName(product), primary_url: product.primary_url },
        conditionEntry,
        rateCondition: rateEntry,
        termCondition: termEntry && termEntry.state === "known" ? termEntry : null,
        rate: rateEntry.value
      });
      state.scenarioSeed = { name: productName(product), rate: source && source.rate_at_seed ? source.rate_at_seed : String(rateEntry.value), years, source };
      window.location.hash = "#escenarios";
    }, "button-link");
    explore.id = `explore-${product.id}`;
    card.appendChild(explore);
  }
  return card;
}

function renderComparisonResult() {
  const holder = document.getElementById("compare-result");
  if (!holder || state.route !== "comparar") return;
  const snapshot = captureFocus();
  holder.replaceChildren();
  holder.setAttribute("tabindex", "-1");
  try {
    renderComparisonResultBody(holder);
  } finally {
    restoreFocus(snapshot, holder);
  }
}

function renderComparisonResultBody(holder) {
  holder.setAttribute("aria-busy", String(state.compareBusy));
  if (state.compareBusy) { holder.appendChild(textElement("p", "Alineando metadatos del servicio local…", "loading-state")); return; }
  if (state.compareError) { holder.appendChild(errorBox(apiErrorText(state.compareError), () => loadComparison())); return; }
  const conditionsNotice = window.PaideiaConditionsLoad.comparisonNotice(state.conditions);
  if (conditionsNotice) {
    holder.appendChild(conditionsNotice.kind === "error"
      ? errorBox(conditionsNotice.message, conditionsNotice.retry ? () => loadConditions(true) : null)
      : textElement("p", conditionsNotice.message, "loading-state"));
    return;
  }
  if (!state.compareResult || JSON.stringify(state.compareIds) !== JSON.stringify(state.selectedIds)) return;
  const result = state.compareResult;
  if (!Array.isArray(result.items)) { holder.appendChild(callout("La API no devolvió los metadatos comparables esperados.", "error-note")); return; }
  const columns = el("div", { className: "comparison-columns" });
  result.items.filter(safeComparisonProduct).forEach((product) => columns.appendChild(comparisonCard(product)));
  holder.appendChild(columns);
  const message = result.reasons && result.reasons.length ? result.reasons.join(" ") : "Solo se comparan metadatos educativos.";
  holder.appendChild(callout(`${message} No se ordenan candidatos ni se calcula una recomendación.`, "info-note"));
  const documentedRates = result.items.filter(safeComparisonProduct).filter((product) => rateSummary(product.id).kind === "verified").length;
  let comparisonNote;
  if (result.quantitative_ready === true) {
    comparisonNote = "La API marca quantitative_ready=true para el criterio documentado; la comparación se limita a esa métrica y no es una oferta ni una recomendación.";
  } else if (documentedRates) {
    comparisonNote = `Se muestran ${documentedRates} ${documentedRates === 1 ? "tasa documentada" : "tasas documentadas"} con fuente y fecha. La API no emite un ranking cuantitativo completo (quantitative_ready=false): no se ordenan ni se calcula una recomendación. Los huecos no se rellenan con ceros ni con NAV.`;
  } else {
    comparisonNote = "No consta una tasa documentada que mostrar en esta comparación. La API no emite un ranking cuantitativo (quantitative_ready=false) y los huecos no se rellenan con ceros ni con NAV.";
  }
  holder.appendChild(callout(comparisonNote, "warning-note"));
  const concepts = el("p", {}, "Conceptos de la comparación: ");
  for (const key of ["tae", "tin", "liquidez", "riesgo"]) concepts.appendChild(window.ContextHelp.createHelp(key));
  holder.appendChild(concepts);
}

function renderComparePage(focus = true) {
  if (state.route !== "comparar") return;
  if (state.selectedIds.length >= 2 && !state.compareResult && !state.compareBusy && !state.compareError) {
    loadComparison();
  }
  const { page, heading } = pageFrame("Compare · condiciones documentadas cuando existen", "Comparar candidatos", "Selecciona entre dos y cuatro candidatos distintos en la biblioteca. Las columnas siguen el mismo orden y muestran los campos que faltan.");
  page.appendChild(callout("Comparación educativa. Solo se muestran cifras documentadas con fuente y fecha; «vencido», «en conflicto» o «sin dato» se enseñan tal cual. No es un ranking financiero.", "warning-note"));
  const selection = el("section", { className: "paper-section" });
  selection.appendChild(el("h2", {}, "Tu selección"));
  const selected = el("div", { id: "compare-selection" });
  selection.appendChild(selected);
  const actions = el("div", { className: "button-row" });
  const compareButton = button("Comparar metadatos", () => loadComparison(), "button button-primary", { disabled: state.selectedIds.length < 2 || state.selectedIds.length > 4 || state.compareBusy });
  compareButton.id = "compare-submit";
  actions.appendChild(compareButton);
  actions.appendChild(routeLink("Cambiar selección", "#biblioteca", "button-link"));
  selection.appendChild(actions);
  page.appendChild(selection);
  const result = el("section", { id: "compare-result", className: "compare-result", "aria-label": "Resultado de comparación" });
  page.appendChild(result);
  page.appendChild(el("section", { id: "compare-diagnosis", className: "paper-section", "aria-live": "polite" }));
  renderCompareSelection(selected);
  renderComparisonResult();
  renderDiagnosis();
  loadConditions();
  if (focus) return heading;
  return null;
}

const DIAGNOSIS_REASONS = Object.freeze({
  FRESHNESS_POLICY_NOT_CONFIGURED: "No hay política de actualidad configurada.", FRESHNESS_BOUNDS_UNCONFIGURED: "No hay límites de actualidad configurados.",
  METRIC_MISSING: "Falta el dato para este criterio.", METRIC_NOT_APPLICABLE: "El dato no es aplicable.",
  FAMILY_MISMATCH: "La familia no coincide con el criterio.", SCOPE_MISMATCH: "El alcance no coincide.",
  UNIT_MISMATCH: "La unidad no coincide.", CURRENCY_UNKNOWN: "La moneda es desconocida.", CURRENCY_MISMATCH: "La moneda no coincide.",
  PERIOD_UNKNOWN: "El plazo es desconocido.", PERIOD_MISMATCH: "El plazo no coincide.", NUMERIC_BASIS_MISMATCH: "La base numérica no coincide.",
  DATA_CONFLICT: "Hay datos en conflicto.", RIGHTS_BLOCKED: "El permiso de uso está bloqueado.", RIGHTS_UNRESOLVED: "El permiso de uso está sin resolver.",
  RETRIEVED_AT_FUTURE: "La fecha de consulta está en el futuro.", SOURCE_STALE: "La fuente excede el límite de actualidad.",
  EFFECTIVE_DATE_UNKNOWN: "La fecha efectiva es desconocida.", EFFECTIVE_DATE_FUTURE: "La fecha efectiva está en el futuro.",
  METRIC_STALE: "El dato excede el límite de actualidad.", VALIDITY_UNKNOWN: "La vigencia es desconocida.",
  NOT_YET_EFFECTIVE: "El dato aún no está vigente.", FACT_EXPIRED: "El dato ha caducado.", SYNTHETIC_FACT_REJECTED: "Se rechazó un dato sintético.",
  DATA_STALE: "La oferta documentada está vencida."
});

function diagnosisApplicable(ids) {
  return ids.length >= 2 && ids.length <= 4 && ids.every(id => state.catalogueCache.get(id)?.family === "deposito");
}

function renderDiagnosis() {
  const holder = document.getElementById("compare-diagnosis");
  if (!holder) return;
  holder.replaceChildren();
  holder.appendChild(el("h2", {}, "Diagnóstico cuantitativo"));
  if (!diagnosisApplicable(state.selectedIds)) {
    holder.appendChild(textElement("p", "El diagnóstico TAE para depósitos a 12 meses en EUR solo se ofrece si todos los candidatos seleccionados son depósitos. No se aplica a otras familias."));
    return;
  }
  holder.appendChild(textElement("p", "Criterio consultado: TAE de depósito a 12 meses en EUR. No presupone que los candidatos tengan ese plazo; no es una oferta ni un ranking."));
  const d = state.diagnosis;
  holder.appendChild(button("Diagnosticar TAE a 12 meses en EUR", () => loadDiagnosis(), "button button-secondary", { disabled: d.busy }));
  if (d.busy) holder.appendChild(textElement("p", "Consultando el diagnóstico local…", "loading-state"));
  else if (d.error) holder.appendChild(callout("No se pudo obtener un diagnóstico válido. Puedes volver a solicitarlo manualmente.", "error-note"));
  else if (d.result && JSON.stringify(d.ids) === JSON.stringify(state.selectedIds)) {
    for (const item of d.result.items) {
      const group = el("section");
      group.appendChild(el("h3", {}, `${item.product_id} · ${productName(state.catalogueCache.get(item.product_id))}`));
      group.appendChild(textElement("p", item.eligible ? "El servicio marca el dato elegible para este criterio; no se muestra como oferta." : "No elegible para comparación cuantitativa con este criterio."));
      if (!item.reason_codes.length) group.appendChild(textElement("p", "El servicio no indicó motivos de exclusión."));
      const reasons = el("ul", { className: "text-list" });
      for (const code of item.reason_codes) reasons.appendChild(el("li", {}, `${code}: ${DIAGNOSIS_REASONS[code] || "Motivo no reconocido; consulta el servicio local."}`));
      group.appendChild(reasons);
      if (item.source_refs.length) group.appendChild(textElement("p", `Referencias del diagnóstico: ${JSON.stringify(item.source_refs)}`, "small"));
      else group.appendChild(textElement("p", "El diagnóstico no aporta referencias de fuente para este dato.", "small muted"));
      holder.appendChild(group);
    }
  }
}

async function loadDiagnosis() {
  const ids = [...state.selectedIds];
  if (!diagnosisApplicable(ids) || state.diagnosis.busy) return;
  const requestId = state.diagnosis.requestId + 1;
  state.diagnosis = { requestId, ids, busy: true, error: false, result: null };
  renderDiagnosis();
  try {
    const response = await apiRequest(API.compare, { method: "POST", body: { product_ids: ids, criterion: "deposit_tae_12m_eur" } });
    if (state.diagnosis.requestId !== requestId || JSON.stringify(ids) !== JSON.stringify(state.selectedIds)) return;
    const result = response.comparability;
    if (!result || result.criterion !== "deposit_tae_12m_eur" || !Array.isArray(result.items) || result.items.length !== ids.length ||
        result.items.some((item, index) => !item || item.product_id !== ids[index] || typeof item.eligible !== "boolean" || !Array.isArray(item.reason_codes) || item.reason_codes.some(code => typeof code !== "string" || !/^[A-Z_]+$/.test(code)) || !Array.isArray(item.source_refs))) throw new Error("invalid diagnosis");
    state.diagnosis.result = result;
  } catch (_) {
    if (state.diagnosis.requestId === requestId) state.diagnosis.error = true;
  } finally {
    if (state.diagnosis.requestId === requestId) { state.diagnosis.busy = false; renderDiagnosis(); }
  }
}

async function loadComparison() {
  if (state.compareBusy) return;
  if (state.selectedIds.length < 2 || state.selectedIds.length > 4) return;
  const ids = [...state.selectedIds];
  const requestId = ++state.compareRequestId;
  state.compareBusy = true;
  state.compareError = null;
  const compareButton = document.getElementById("compare-submit");
  if (compareButton) compareButton.disabled = true;
  announce("Comparando metadatos…");
  renderComparisonResult();
  try {
    const data = await apiRequest(API.compare, { method: "POST", body: { product_ids: ids } });
    if (requestId !== state.compareRequestId) return;
    state.compareResult = data;
    state.compareIds = ids;
  } catch (error) {
    if (requestId !== state.compareRequestId) return;
    state.compareError = error;
    state.compareResult = null;
    state.compareIds = [];
  } finally {
    if (requestId === state.compareRequestId) {
      state.compareBusy = false;
      renderComparisonResult();
      const button = document.getElementById("compare-submit");
      if (button) button.disabled = state.selectedIds.length < 2 || state.selectedIds.length > 4;
      announce(state.compareError ? "No se pudo comparar" : "Comparación lista");
    }
  }
}

function numberField(id, label, help, attrs = {}) {
  const input = el("input", { type: "number", id, step: attrs.step || "0.01", min: attrs.min, max: attrs.max, required: true, inputmode: "decimal", autocomplete: "off" });
  return { input, wrapper: field(label, input, help, id) };
}

function currencyFromApi(value) {
  // Server money is an exact cents string; Number would silently lose digits.
  if (typeof value !== "string" || !/^-?\d+\.\d{2}$/.test(value)) return "No disponible";
  const negative = value.startsWith("-");
  const [integer, cents] = (negative ? value.slice(1) : value).split(".");
  const grouped = new Intl.NumberFormat("es-ES").format(BigInt(integer));
  return `${negative ? "-" : ""}${grouped},${cents}\u00a0€`;
}

function svgNode(name, attrs = {}, text = null) {
  const item = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attrs)) item.setAttribute(key, String(value));
  if (text !== null) item.textContent = String(text);
  return item;
}

function makeScenarioChart(series, chartId = "chart") {
  const svg = svgNode("svg", { class: "scenario-chart", viewBox: "0 0 760 330", role: "img", "aria-labelledby": `${chartId}-title ${chartId}-desc` });
  svg.append(svgNode("title", { id: `${chartId}-title` }, "Evolución del escenario introducido"));
  svg.append(svgNode("desc", { id: `${chartId}-desc` }, "Tres líneas muestran aportaciones acumuladas, saldo hipotético y saldo ajustado por inflación, a partir de la respuesta del cálculo local."));
  const valid = series.filter((point) => point && Number.isFinite(Number(point.month)) && Number.isFinite(Number(point.contributions)) && Number.isFinite(Number(point.balance)) && Number.isFinite(Number(point.real_balance)));
  if (valid.length < 2) return svg;
  const left = 74, right = 735, top = 24, bottom = 280;
  const xMax = Math.max(1, ...valid.map((point) => Number(point.month)));
  const values = valid.flatMap((point) => [Number(point.contributions), Number(point.balance), Number(point.real_balance)]);
  let minY = Math.min(0, ...values), maxY = Math.max(0, ...values);
  if (minY === maxY) { minY -= 1; maxY += 1; }
  const pad = (maxY - minY) * 0.08;
  minY -= pad; maxY += pad;
  const x = (month) => left + (Number(month) / xMax) * (right - left);
  const y = (amount) => bottom - ((Number(amount) - minY) / (maxY - minY)) * (bottom - top);
  const zeroY = y(0);
  svg.append(svgNode("line", { x1: left, y1: top, x2: left, y2: bottom, class: "axis" }));
  svg.append(svgNode("line", { x1: left, y1: zeroY, x2: right, y2: zeroY, class: "axis" }));
  for (let i = 0; i <= 3; i += 1) {
    const amount = minY + (maxY - minY) * i / 3;
    const yy = y(amount);
    svg.append(svgNode("line", { x1: left, y1: yy, x2: right, y2: yy, class: "gridline" }));
    svg.append(svgNode("text", { x: left - 9, y: yy + 4, "text-anchor": "end" }, new Intl.NumberFormat("es-ES", { notation: "compact", maximumFractionDigits: 1 }).format(amount)));
  }
  svg.append(svgNode("text", { x: left, y: 312, "text-anchor": "start" }, "0 meses"));
  svg.append(svgNode("text", { x: right, y: 312, "text-anchor": "end" }, `${xMax} meses`));
  const pathFor = (fieldName) => valid.map((point, index) => `${index === 0 ? "M" : "L"}${x(point.month).toFixed(2)} ${y(point[fieldName]).toFixed(2)}`).join(" ");
  svg.append(svgNode("path", { d: pathFor("contributions"), class: "series-contributions" }));
  svg.append(svgNode("path", { d: pathFor("balance"), class: "series-balance" }));
  svg.append(svgNode("path", { d: pathFor("real_balance"), class: "series-real" }));
  return svg;
}

function focusResultsRegion(holder, preferred) {
  if (!holder || !holder.isConnected) return false;
  if (preferred && preferred.isConnected && !preferred.disabled) {
    preferred.focus({ preventScroll: true });
    return true;
  }
  holder.setAttribute("tabindex", "-1");
  holder.focus({ preventScroll: true });
  return true;
}

function buildScenarioOutput(scenario = state.scenario, suffix = "") {
  const holder = document.getElementById(`scenario-output${suffix}`);
  if (!holder) return;
  const active = document.activeElement;
  const hadFocusInside = Boolean(active && holder.contains(active));
  fillScenarioOutput(holder, scenario, suffix);
  if (hadFocusInside) focusResultsRegion(holder, holder.querySelector(".error-note button"));
}

function fillScenarioOutput(holder, scenario, suffix) {
  holder.replaceChildren();
  holder.setAttribute("aria-busy", String(scenario.status === "pending"));
  holder.dataset.status = scenario.status;
  if (scenario.status === "pending") { holder.appendChild(textElement("p", "Calculando con los supuestos indicados…", "loading-state")); return; }
  if (scenario.status === "error") {
    holder.appendChild(errorBox(
      apiErrorText(scenario.error),
      scenario.submitted ? () => submitScenario({ ...scenario.submitted }, scenario, suffix) : null
    ));
    return;
  }
  if (scenario.status !== "current") { holder.appendChild(textElement("p", "Introduce los supuestos y calcula este escenario.", "small muted")); return; }
  const data = scenario.result;
  if (!data) return;
  if (!data.summary || !Array.isArray(data.series)) { holder.appendChild(callout("La respuesta del cálculo no contiene el resumen y la serie esperados.", "error-note")); return; }
  const wrap = el("section", { className: "data-panel" });
  wrap.appendChild(el("h2", {}, "Resultado del supuesto"));
  wrap.appendChild(callout("Hipótesis introducida por ti · no es predicción · bruto, sin fiscalidad ni costes de producto.", "warning-note"));
  const assumptions = scenario.submitted;
  if (assumptions) {
    wrap.appendChild(el("h3", {}, "Supuestos usados"));
    const used = el("dl", { className: "detail-list" });
    const methodName = assumptions.method === "simple" ? "Simple" : "Compuesto";
    const usedValues = [
      ["Capital inicial", formatCurrency(assumptions.principal)],
      ["Tasa anual", formatPercentValue(assumptions.annual_rate_percent)],
      ["Horizonte", `${assumptions.years} años`],
      ["Aportación mensual", formatCurrency(assumptions.monthly_contribution)],
      ["Método", methodName],
      ["Inflación supuesta", formatPercentValue(assumptions.inflation_percent)]
    ];
    usedValues.forEach(([label, value]) => used.append(el("dt", {}, label), el("dd", {}, value)));
    wrap.appendChild(used);
  }
  const stats = el("dl", { className: "scenario-summary" });
  const metrics = [
    ["Capital aportado", currencyFromApi(data.summary.contributions)],
    ["Saldo final hipotético", currencyFromApi(data.summary.final_balance)],
    ["Diferencia del escenario", currencyFromApi(data.summary.interest)],
    ["Saldo ajustado por inflación", currencyFromApi(data.summary.inflation_adjusted)]
  ];
  metrics.forEach(([label, value]) => {
    const item = el("div", { className: "scenario-stat" });
    item.append(el("dt", {}, label), el("dd", {}, value));
    stats.appendChild(item);
  });
  wrap.appendChild(stats);
  const interest = Number(data.summary.interest);
  if (Number(data.assumptions.annual_rate_percent) === 0) wrap.appendChild(callout("Tasa supuesta cero: no se genera interés nominal; la inflación introducida puede cambiar el valor real.", "info-note"));
  const loss = Number(data.summary.final_balance) < Number(data.summary.contributions) || (Number.isFinite(interest) && interest < 0);
  if (loss) wrap.appendChild(callout("Con estos supuestos, el saldo final queda por debajo de lo aportado. La pérdida posible no se oculta.", "error-note"));
  const figure = el("figure", { className: "chart-wrap" });
  figure.appendChild(makeScenarioChart(data.series, `chart${suffix || '-a'}`));
  const legend = el("ul", { className: "chart-legend", "aria-label": "Series del gráfico" });
  legend.append(el("li", {}, [el("span", { className: "legend-mark contributions", "aria-hidden": "true" }), document.createTextNode("Capital aportado")]), el("li", {}, [el("span", { className: "legend-mark", "aria-hidden": "true" }), document.createTextNode("Saldo hipotético")]), el("li", {}, [el("span", { className: "legend-mark real", "aria-hidden": "true" }), document.createTextNode("Saldo ajustado por inflación")]));
  figure.appendChild(legend);
  figure.appendChild(el("figcaption", {}, "La curva representa el cálculo de este formulario, no un dato observado de un producto."));
  wrap.appendChild(figure);
  const tableSection = el("section");
  tableSection.appendChild(el("h3", {}, "Valores del escenario"));
  tableSection.appendChild(textElement("p", "Mismos valores que el gráfico; meses de cierre anual y mes final.", "small muted"));
  const tableWrap = el("div", { className: "table-wrap" });
  const table = el("table", { className: "data-table" });
  const head = el("thead");
  const row = el("tr");
  ["Mes", "Aportado", "Saldo", "Saldo real"].forEach((label) => row.appendChild(el("th", { scope: "col" }, label)));
  head.appendChild(row);
  table.appendChild(head);
  const body = el("tbody");
  const lastMonth = Number(data.series[data.series.length - 1].month);
  const rows = data.series.filter((point) => Number(point.month) === 0 || Number(point.month) % 12 === 0 || Number(point.month) === lastMonth);
  rows.forEach((point) => {
    const tr = el("tr");
    const contributionCell = el("td", { "data-label": "Aportado" }, currencyFromApi(point.contributions));
    const balanceCell = el("td", { "data-label": "Saldo" }, currencyFromApi(point.balance));
    const realCell = el("td", { "data-label": "Saldo real" }, currencyFromApi(point.real_balance));
    tr.append(el("th", { scope: "row" }, `${point.month} meses`), contributionCell, balanceCell, realCell);
    body.appendChild(tr);
  });
  table.appendChild(body);
  tableWrap.appendChild(table);
  tableSection.appendChild(tableWrap);
  wrap.appendChild(tableSection);
  holder.appendChild(wrap);
}

function readScenarioForm(form, suffix = "") {
  const idFor = (name) => `scenario-${name}${suffix}`;
  const value = (id) => form.querySelector(`#${id}`).value.trim();
  const fail = (name, message) => {
    const error = new Error(message);
    error.fieldId = idFor(name);
    throw error;
  };
  const principal = value(idFor("principal"));
  const rate = value(idFor("rate"));
  const years = value(idFor("years"));
  const contribution = value(idFor("contribution"));
  const inflation = value(idFor("inflation"));
  const method = value(idFor("method"));
  const amounts = [principal, rate, years, contribution, inflation];
  const names = ["principal", "rate", "years", "contribution", "inflation"];
  const invalidIndex = amounts.findIndex((item) => item === "" || !Number.isFinite(Number(item)));
  if (invalidIndex !== -1) fail(names[invalidIndex], "Completa todos los campos con números válidos.");
  const moneyPattern = /^(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?$/;
  const ratePattern = /^-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,4})?$/;
  const moneyIndex = [principal, contribution].findIndex((item) => !moneyPattern.test(item) || Number(item) > 1000000000);
  if (moneyIndex !== -1) fail(moneyIndex === 0 ? "principal" : "contribution", "Capital y aportación: escribe importes de 0 a 1.000.000.000 €, con hasta dos decimales y sin exponentes.");
  const rateIndex = [rate, inflation].findIndex((item) => !ratePattern.test(item) || Number(item) <= -100 || Number(item) > 1000);
  if (rateIndex !== -1) fail(rateIndex === 0 ? "rate" : "inflation", "Tasa e inflación: escribe valores mayores que −100 y hasta 1000 %, con hasta cuatro decimales y sin exponentes.");
  if (!Number.isInteger(Number(years)) || Number(years) < 1 || Number(years) > 40) fail("years", "El horizonte debe ser un número entero de 1 a 40 años.");
  if (!new Set(["simple", "compound"]).has(method)) fail("method", "Elige un método de cálculo disponible.");
  return { principal, annual_rate_percent: rate, years: Number(years), monthly_contribution: contribution, method, inflation_percent: inflation };
}

function clearScenarioFieldErrors(form) {
  if (!form) return;
  for (const control of form.querySelectorAll('[aria-invalid="true"]')) {
    control.removeAttribute("aria-invalid");
    const describedBy = (control.getAttribute("aria-describedby") || "")
      .split(/\s+/)
      .filter((id) => id && !/^scenario-form-error/.test(id));
    if (describedBy.length) control.setAttribute("aria-describedby", describedBy.join(" "));
    else control.removeAttribute("aria-describedby");
  }
}

function markScenarioFieldError(form, fieldId, errorNode) {
  if (!form || !fieldId || !errorNode) return null;
  const control = document.getElementById(fieldId);
  if (!control || !form.contains(control)) return null;
  control.setAttribute("aria-invalid", "true");
  const ids = new Set((control.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
  ids.add(errorNode.id);
  control.setAttribute("aria-describedby", [...ids].join(" "));
  control.focus();
  return control;
}

// Public read-only snapshot: only current versions expose a server response.
function scenarioComparisonSnapshot() {
  return { schema: "paideia.scenario-comparison", schema_version: 1,
    scenarios: [state.scenario, state.scenarioSecond].map((scenario, index) => ({
      id: index ? "B" : "A", status: scenario.status, version: scenario.version,
      inputs: { ...scenario.form },
      result: scenario.status === "current" ? JSON.parse(JSON.stringify(scenario.result)) : null,
      source: scenario.source ? JSON.parse(JSON.stringify(scenario.source)) : null
    })) };
}
window.getScenarioComparisonSnapshot = scenarioComparisonSnapshot;
function renderScenarioComparisonSummary() {
  const holder = document.getElementById("scenario-comparison-summary");
  if (!holder) return;
  holder.replaceChildren(el("h2", {}, "Comparación de escenarios"));
  const tableWrap = el("div", { className: "table-wrap" });
  const table = el("table", { className: "data-table" });
  const header = el("tr");
  ["Escenario", "Estado", "Horizonte", "Aportado", "Saldo nominal", "Saldo real"].forEach(label => header.appendChild(el("th", { scope: "col" }, label)));
  table.appendChild(el("thead", {}, header));
  const body = el("tbody");
  const labels = { dirty: "Pendiente de calcular", pending: "Calculando", error: "Error de cálculo", current: "Actualizado" };
  [state.scenario, state.scenarioSecond].forEach((scenario, index) => {
    const row = el("tr");
    row.appendChild(el("th", { scope: "row" }, index ? "B" : "A"));
    row.appendChild(el("td", { "data-label": "Estado" }, labels[scenario.status]));
    row.appendChild(el("td", { "data-label": "Horizonte" }, scenario.form.years ? `${scenario.form.years} años` : "—"));
    [["contributions", "Aportado"], ["final_balance", "Saldo nominal"], ["inflation_adjusted", "Saldo real"]].forEach(([key, label]) => row.appendChild(el("td", { "data-label": label }, scenario.status === "current" ? currencyFromApi(scenario.result.summary[key]) : "—")));
    body.appendChild(row);
  });
  table.appendChild(body); tableWrap.appendChild(table); holder.appendChild(tableWrap);
  holder.appendChild(textElement("p", "Capital aportado: suma del capital inicial y las aportaciones. Saldo nominal: importe final sin ajustar. Saldo real: saldo ajustado por la inflación supuesta.", "small muted"));
  if ([state.scenario, state.scenarioSecond].every(s => s.status === "current")) {
    holder.appendChild(el("h3", {}, "Qué cambia de A a B"));
    const a = state.scenario.submitted, b = state.scenarioSecond.submitted;
    const fields = [
      ["principal", "Capital inicial", formatCurrency], ["annual_rate_percent", "Tasa anual", formatPercentValue],
      ["years", "Horizonte", value => `${value} años`], ["monthly_contribution", "Aportación mensual", formatCurrency],
      ["method", "Método", value => value === "simple" ? "Simple" : "Compuesto"], ["inflation_percent", "Inflación supuesta", formatPercentValue]
    ];
    const differences = fields.filter(([key]) => key === "method" ? a[key] !== b[key] : Number(a[key]) !== Number(b[key]));
    if (!differences.length) holder.appendChild(el("p", {}, "Los supuestos son iguales."));
    else {
      const list = el("ul");
      differences.forEach(([key, label, format]) => list.appendChild(el("li", {}, `${label}: ${format(a[key])} → ${format(b[key])}`)));
      holder.appendChild(list);
    }
  }
  if ([state.scenario, state.scenarioSecond].every(s => s.status === "current") && Number(state.scenario.form.years) !== Number(state.scenarioSecond.form.years)) {
    holder.appendChild(textElement("p", "Los horizontes son distintos: los saldos corresponden a momentos diferentes.", "warning-note"));
  }
  const statusNode = document.getElementById("scenario-comparison-status");
  if (statusNode) {
    const statusText = [state.scenario, state.scenarioSecond]
      .map((scenario, index) => `Escenario ${index ? "B" : "A"}: ${labels[scenario.status].toLowerCase()}`)
      .join(" · ");
    if (statusNode.textContent !== statusText) statusNode.textContent = statusText;
  }
}
window.addEventListener("scenario-comparison-change", renderScenarioComparisonSummary);
function scenarioChanged(scenario, suffix) {
  scenario.version += 1;
  scenario.status = "dirty";
  scenario.result = null;
  scenario.submitted = null;
  scenario.error = null;
  scenario.source = window.PaideiaScenarioProvenance.sourceAfterEdit(scenario.source, scenario.form);
  const submitButton = document.getElementById(`scenario-submit${suffix}`);
  if (submitButton) submitButton.disabled = false;
  buildScenarioOutput(scenario, suffix);
  window.dispatchEvent(new CustomEvent("scenario-comparison-change"));
}
async function submitScenario(payload, scenario = state.scenario, suffix = "") {
  if (!payload) return;
  if (scenario.status === "pending") return;
  const version = ++scenario.version;
  scenario.status = "pending";
  scenario.result = null;
  scenario.error = null;
  scenario.submitted = { ...payload };
  const submitButton = document.getElementById(`scenario-submit${suffix}`);
  const outputHolder = document.getElementById(`scenario-output${suffix}`);
  // Deshabilitar el botón enfocado movería el foco a BODY: llévalo antes a la región de resultado.
  if (submitButton && submitButton === document.activeElement && outputHolder) focusResultsRegion(outputHolder);
  if (submitButton) submitButton.disabled = true;
  announce(`Calculando escenario ${suffix ? "B" : "A"}…`);
  buildScenarioOutput(scenario, suffix);
  window.dispatchEvent(new CustomEvent("scenario-comparison-change"));
  try {
    const data = await apiRequest(API.calculate, { method: "POST", body: payload });
    if (version !== scenario.version) return;
    if (data.hypothetical !== true || data.not_prediction !== true || !data.summary || !Array.isArray(data.series)) throw new ApiFailure("La respuesta no declara el resultado como hipotético y no predictivo, o no incluye la serie esperada.", 200, "INVALID_CALCULATION", false);
    scenario.result = data;
    scenario.status = "current";
  } catch (error) {
    if (version !== scenario.version) return;
    scenario.error = error;
    scenario.result = null;
    scenario.status = "error";
  } finally {
    if (version === scenario.version) {
      buildScenarioOutput(scenario, suffix);
      window.dispatchEvent(new CustomEvent("scenario-comparison-change"));
      const button = document.getElementById(`scenario-submit${suffix}`);
      if (button) button.disabled = false;
      announce(scenario.status === "current"
        ? `Escenario ${suffix ? "B" : "A"} calculado`
        : `No se pudo calcular el escenario ${suffix ? "B" : "A"}`);
    }
  }
}

function renderScenario() {
  const seed = state.scenarioSeed;
  if (seed) {
    state.scenarioSeed = null;
    state.scenario.form = { ...state.scenario.form, annual_rate_percent: seed.rate, years: String(seed.years) };
    state.scenario = { ...state.scenario, status: "dirty", version: 0, result: null, error: null, submitted: null, source: seed.source || null };
  }
  const { page, heading } = pageFrame("Escenarios · supuestos editables", "Prueba otros supuestos", "Los números describen una hipótesis tuya. El cálculo no usa tasas de producto y no es una predicción.");
  if (seed) {
    const termNote = seed.source && seed.source.term_months && Number(seed.years) * 12 !== seed.source.term_months
      ? ` El plazo documentado es de ${seed.source.term_months} meses; el horizonte editable se redondea a ${seed.years} año(s) y no se presenta como plazo del producto.`
      : "";
    page.appendChild(callout(`Supuesto importado de «${seed.name}»: tasa anual ${seed.rate} % y horizonte ${seed.years} año(s), ya escritos en el escenario A. Es una hipótesis editable, no una oferta ni una proyección.${termNote} La tasa, el tramo y la fuente se copian solo a este formulario local: el perfil no se incluye y no se envía al proveedor de IA.`, "info-note"));
  }
  page.appendChild(callout("Hipótesis del usuario · no predicción · bruto, sin fiscalidad ni costes de producto. El método compuesto convierte la tasa anual efectiva a mensual; en simple la tasa anual se divide entre 12. Aportaciones al final de cada mes.", "warning-note"));
  page.appendChild(el("p", {}, "Compara dos hipótesis independientes. Cada resultado muestra los valores nominales, reales y aportados del motor local."));
  const guide = el("nav", { "aria-label": "Recorrido de escenarios" });
  [["Empezar/ajustar", "scenario-start"], ["Comparar/entender", "scenario-comparison-summary"], ["Guardar", "scenario-report-host"]].forEach(([label, id]) => {
    const link = el("a", { href: `#${id}` }, label);
    link.addEventListener("click", event => { event.preventDefault(); const target = document.getElementById(id); target.setAttribute("tabindex", "-1"); target.focus({ preventScroll: true }); target.scrollIntoView(); });
    guide.append(link, document.createTextNode(" → "));
  });
  page.appendChild(guide);
  const start = el("div", { id: "scenario-start" });
  page.appendChild(start);
  renderScenarioPanel(start, state.scenario, "", "A");
  renderScenarioPanel(start, state.scenarioSecond, "-b", "B");
  page.appendChild(el("section", { id: "scenario-comparison-summary", className: "paper-section" }));
  page.appendChild(el("p", { id: "scenario-comparison-status", className: "visually-hidden", role: "status", "aria-live": "polite" }));
  renderScenarioComparisonSummary();
  const reportHost = el("section", { id: "scenario-report-host" });
  page.appendChild(reportHost);
  window.mountScenarioReport(reportHost);
  return heading;
}

function renderScenarioPanel(page, scenario, suffix, name) {
  const panel = el("section", { className: "paper-section", "aria-label": `Escenario ${name}` });
  panel.appendChild(el("h2", {}, `Escenario ${name} · controles`));
  const form = el("form", { className: "scenario-form", novalidate: true });
  const principal = numberField(`scenario-principal${suffix}`, "Capital inicial (€)", "Importe que tú introduces. No es un mínimo contractual.", { min: "0" });
  const rate = numberField(`scenario-rate${suffix}`, "Tasa anual supuesta (%)", "No procede de la biblioteca ni de una oferta. Introduce un supuesto; puede ser negativo.", { min: "-99.9999", max: "1000", step: "0.0001" });
  const years = numberField(`scenario-years${suffix}`, "Horizonte (años)", "Número entero entre 1 y 40.", { min: "1", max: "40", step: "1" });
  const contribution = numberField(`scenario-contribution${suffix}`, "Aportación mensual (€)", "El backend la coloca al final de cada mes.", { min: "0" });
  const inflation = numberField(`scenario-inflation${suffix}`, "Inflación anual supuesta (%)", "Supuesto separado; no representa una previsión de inflación.", { min: "-99.9999", max: "1000", step: "0.0001" });
  const method = el("select", { id: `scenario-method${suffix}` }, [el("option", { value: "compound" }, "Compuesto"), el("option", { value: "simple" }, "Simple")]);
  const methodField = field("Método", method, "Convención definida por el cálculo local.", method.id);
  methodField.appendChild(window.ContextHelp.createHelp("interes-compuesto"));
  inflation.wrapper.appendChild(window.ContextHelp.createHelp("inflacion"));
  form.append(principal.wrapper, rate.wrapper, years.wrapper, contribution.wrapper, methodField, inflation.wrapper);
  principal.input.value = scenario.form.principal;
  rate.input.value = scenario.form.annual_rate_percent;
  years.input.value = scenario.form.years;
  contribution.input.value = scenario.form.monthly_contribution;
  inflation.input.value = scenario.form.inflation_percent;
  method.value = scenario.form.method || "compound";
  const error = textElement("p", "", "form-error full-width");
  error.id = `scenario-form-error${suffix}`;
  error.setAttribute("role", "alert");
  form.appendChild(error);
  const submit = button(`Calcular escenario ${name}`, null, "button button-primary", { type: "submit", disabled: scenario.status === "pending" });
  submit.id = `scenario-submit${suffix}`;
  form.appendChild(el("div", { className: "button-row full-width" }, submit));
  const edited = () => {
    scenario.form = {
      principal: principal.input.value,
      annual_rate_percent: rate.input.value,
      years: years.input.value,
      monthly_contribution: contribution.input.value,
      inflation_percent: inflation.input.value,
      method: method.value
    };
    error.textContent = "";
    clearScenarioFieldErrors(form);
    scenarioChanged(scenario, suffix);
  };
  if (name === "A") {
    const confirmation = el("div", { className: "full-width", "aria-live": "polite" });
    const applyExample = () => {
      principal.input.value = "1000"; rate.input.value = "2"; years.input.value = "5";
      contribution.input.value = "50"; inflation.input.value = "2"; method.value = "compound";
      confirmation.replaceChildren(); edited(); example.focus();
    };
    const example = button("Cargar ejemplo ficticio en A", () => {
      const hasInput = [principal.input, rate.input, years.input, contribution.input, inflation.input].some(input => input.value !== "");
      if (!hasInput && scenario.status === "dirty" && !scenario.version) { applyExample(); return; }
      confirmation.replaceChildren(textElement("p", "¿Quieres sustituir el escenario A por el ejemplo ficticio?"),
        button("Confirmar sustitución", applyExample), button("Cancelar", () => { confirmation.replaceChildren(); example.focus(); }));
    });
    form.append(example, confirmation);
  }
  if (name === "B") {
    const confirmation = el("div", { className: "full-width", "aria-live": "polite" });
    const copy = () => {
      const source = document.querySelectorAll(".scenario-form")[0];
      try { readScenarioForm(source); }
      catch (failure) { document.getElementById("scenario-form-error").textContent = failure.message; confirmation.replaceChildren(); copyButton.focus(); return; }
      document.getElementById("scenario-form-error").textContent = "";
      ["principal", "rate", "years", "contribution", "inflation", "method"].forEach(id => {
        form.querySelector(`#scenario-${id}-b`).value = source.querySelector(`#scenario-${id}`).value;
      });
      scenario.source = window.PaideiaScenarioProvenance.copySource(
        window.PaideiaScenarioProvenance.sourceAfterEdit(state.scenario.source, state.scenario.form)
      );
      confirmation.replaceChildren(); edited(); copyButton.focus();
    };
    const copyButton = button("Copiar A a B para probar un cambio", () => {
      const source = document.querySelectorAll(".scenario-form")[0];
      try { readScenarioForm(source); }
      catch (failure) { document.getElementById("scenario-form-error").textContent = failure.message; copyButton.focus(); return; }
      if ([principal.input, rate.input, years.input, contribution.input, inflation.input].some(input => input.value !== "") || scenario.status !== "dirty" || scenario.version) {
        confirmation.replaceChildren(textElement("p", "¿Quieres sustituir el escenario B con los campos actuales de A?"),
          button("Confirmar sustitución", copy), button("Cancelar", () => { confirmation.replaceChildren(); copyButton.focus(); }));
      } else copy();
    });
    form.append(copyButton, confirmation);
  }
  form.addEventListener("input", edited);
  method.addEventListener("change", edited);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    // Calcular B con el formulario vacío es lo normal: se parte de A para
    // comparar un cambio, en vez de obligar a rellenar seis campos a mano.
    if (name === "B" && [principal.input, rate.input, years.input, contribution.input, inflation.input].every((input) => input.value === "")) {
      const source = document.querySelectorAll(".scenario-form")[0];
      try {
        readScenarioForm(source);
        ["principal", "rate", "years", "contribution", "inflation", "method"].forEach((id) => {
          form.querySelector(`#scenario-${id}-b`).value = source.querySelector(`#scenario-${id}`).value;
        });
        edited();
      } catch (_) {
        // Si A tampoco está completo, el error de validación de B lo explicará.
      }
    }
    try {
      const payload = readScenarioForm(form, suffix);
      error.textContent = "";
      clearScenarioFieldErrors(form);
      submitScenario(payload, scenario, suffix);
    } catch (failure) {
      scenarioChanged(scenario, suffix);
      error.textContent = failure.message;
      markScenarioFieldError(form, failure.fieldId, error);
    }
  });
  panel.appendChild(form);
  page.appendChild(panel);
  page.appendChild(el("div", { id: `scenario-output${suffix}`, className: "scenario-output", "aria-label": `Resultado escenario ${name}` }));
  buildScenarioOutput(scenario, suffix);
}

function renderSimulationProgress(page) {
  // Guiones suaves: Chrome no dispone de diccionario de partición en español y, sin ellos,
  // la columna estrecha parte palabras sin guion («Comprensi/ón»). Si la palabra cabe, no se ven.
  const labels = ["Refe\u00ADrencia", "Condi\u00ADciones", "Impor\u00ADte", "Compren\u00ADsión", "Justifi\u00ADcante"];
  const list = el("ol", { className: "sim-progress", "aria-label": "Pasos del ensayo" });
  labels.forEach((label, index) => {
    const item = el("li", { "aria-current": state.simulation.step === index ? "step" : null });
    item.appendChild(textElement("span", `${index + 1} / 5`));
    item.appendChild(document.createTextNode(label));
    list.appendChild(item);
  });
  page.appendChild(list);
}

async function loadSimulationCatalogue() {
  const seq = ++state.simulation.requestId;
  state.simulation.loading = true;
  state.simulation.error = null;
  announce("Cargando catálogo del ensayo…");
  renderSimulationCandidates();
  try {
    const data = await apiRequest(API.catalogue);
    if (seq !== state.simulation.requestId) return;
    if (!Array.isArray(data.items)) throw new ApiFailure("El catálogo no devolvió candidatos para el ensayo.", 200, "INVALID_CATALOGUE", false);
    state.simulation.products = data.items.filter((item) => item && typeof item.id === "string");
    state.simulation.products.forEach((product) => state.catalogueCache.set(product.id, product));
    state.simulation.loaded = true;
  } catch (error) {
    if (seq === state.simulation.requestId) state.simulation.error = error;
  } finally {
    if (seq === state.simulation.requestId) {
      state.simulation.loading = false;
      renderSimulationCandidates();
      announce(state.simulation.error ? "No se pudo cargar el catálogo del ensayo" : "Catálogo del ensayo listo");
    }
  }
}

function renderSimulationCandidates() {
  const holder = document.getElementById("simulation-candidates");
  if (!holder || state.route !== "simulacion" || state.simulation.step !== 0) return;
  const active = document.activeElement;
  const hadFocusInside = Boolean(active && holder.contains(active));
  fillSimulationCandidates(holder);
  if (!hadFocusInside) return;
  const preferred = holder.querySelector(".error-note button") || document.getElementById("simulation-product");
  focusResultsRegion(holder, preferred);
}

function fillSimulationCandidates(holder) {
  holder.replaceChildren();
  holder.setAttribute("aria-busy", String(state.simulation.loading));
  if (state.simulation.loading) { holder.appendChild(textElement("p", "Cargando candidatos del catálogo local…", "loading-state")); return; }
  if (state.simulation.error) { holder.appendChild(errorBox(apiErrorText(state.simulation.error), () => loadSimulationCatalogue())); return; }
  if (!state.simulation.loaded) { holder.appendChild(textElement("p", "Aún no se ha cargado el catálogo.", "loading-state")); return; }
  if (!state.simulation.products.length) { holder.appendChild(callout("La API no devolvió candidatos. No hay una ficha de referencia para ensayar.", "info-note")); return; }
  const select = el("select", { id: "simulation-product" });
  select.appendChild(el("option", { value: "" }, "Elige un candidato de la API"));
  state.simulation.products.forEach((product) => select.appendChild(el("option", { value: product.id, selected: state.simulation.chosenId === product.id }, `${product.name || product.id} — ${familyLabel(product.family)}`)));
  holder.appendChild(field("Producto de referencia", select, "Solo referencia identificativa; no implica disponibilidad ni contratación.", select.id));
  const feedback = textElement("p", "", "form-error");
  feedback.id = "simulation-select-error";
  feedback.setAttribute("role", "status");
  holder.appendChild(feedback);
  select.addEventListener("change", () => {
    state.simulation.chosenId = select.value;
    chooseButton.disabled = !state.simulation.chosenId;
  });
  const chooseButton = button("Elegir referencia", () => {
    const product = state.simulation.products.find((item) => item.id === state.simulation.chosenId);
    if (!product) { feedback.textContent = "Elige un candidato antes de continuar."; select.focus(); return; }
    state.simulation.product = product;
    state.simulation.step = 1;
    render();
  }, "button button-primary", { disabled: !state.simulation.chosenId });
  holder.appendChild(el("div", { className: "button-row" }, chooseButton));
}

/* Fuente de las condiciones: la de la ficha transcrita (`entry.source`) o, en las
   condiciones derivadas del snapshot, la URL resuelta por el registro de fuentes
   (`source_refs` / `source_ids`). Antes solo se miraba `entry.source`, así que un
   producto con tasa documentada y fuente enlazada se mostraba como «sin condiciones». */
function conditionSourceRef(entry) {
  if (entry && entry.source && isSafePrimaryUrl(entry.source.url) && entry.source.retrieved_at) {
    return { url: entry.source.url, retrieved_at: entry.source.retrieved_at };
  }
  const conditions = entry && Array.isArray(entry.conditions) ? entry.conditions : [];
  for (const condition of conditions) {
    if (!condition || typeof condition !== "object") continue;
    const fallbackDate = condition.retrieved_at || (entry && entry.retrieved_at) || null;
    const refs = Array.isArray(condition.source_refs) ? condition.source_refs : [];
    for (const ref of refs) {
      if (ref && isSafePrimaryUrl(ref.url)) {
        return { url: ref.url, retrieved_at: ref.accessed || fallbackDate };
      }
    }
    const ids = Array.isArray(condition.source_ids) ? condition.source_ids : [];
    for (const id of ids) {
      if (typeof id === "string" && isSafePrimaryUrl(id)) {
        return { url: id, retrieved_at: fallbackDate };
      }
    }
  }
  return null;
}

function hasDocumentedConditionsSource(entry) {
  const ref = conditionSourceRef(entry);
  return Boolean(ref && ref.url && ref.retrieved_at);
}

function simulationConditionsLabel(product) {
  const entry = state.conditions.byId.get(product.id);
  if (!entry || !Array.isArray(entry.conditions) || !entry.conditions.length || !hasDocumentedConditionsSource(entry)) return "Condiciones no documentadas";
  const states = new Set(entry.conditions.map((item) => item && item.state));
  if (states.has("conflict")) return "En conflicto";
  if (states.has("stale")) return "Obsoleta";
  if (states.has("unknown")) return "Sin dato";
  return "Documentada";
}

function simulationProductReview(parent, product) {
  parent.appendChild(el("h2", {}, productName(product)));
  parent.appendChild(textElement("p", `${familyLabel(product.family)} · ${issuerLabel(product)}`, "muted"));
  const conditionEntry = state.conditions.byId.get(product.id);
  const conditionStates = conditionEntry && Array.isArray(conditionEntry.conditions)
    ? conditionEntry.conditions.map((item) => item.state)
    : [];
  parent.appendChild(el("div", { className: "badge-row" }, [
    badge(identityLabel(product), identityKind(product)),
    badge(simulationConditionsLabel(product), conditionStates.some((state) => state !== "known") || !conditionStates.length ? "pending" : "verified")
  ]));
  const details = el("dl", { className: "detail-list" });
  details.append(el("dt", {}, "ISIN"), el("dd", {}, product.isin || "No indicado en los metadatos"));
  details.append(el("dt", {}, "Fecha asociada"), el("dd", {}, product.as_of || "No consta una fecha efectiva inequívoca"));
  details.append(el("dt", {}, "Disponibilidad"), el("dd", {}, "No acreditada por la identidad del candidato."));
  details.append(el("dt", {}, "Condiciones contractuales"), el("dd", {}, conditionEntry && conditionEntry.conditions && conditionEntry.conditions.length && hasDocumentedConditionsSource(conditionEntry)
    ? "Documentadas con fuente y fecha. Su estado puede ser vencido, en conflicto o sin dato; no equivalen a una oferta vigente."
    : "Pendientes; no se simulan tipos, plazos, costes ni garantías."));
  parent.appendChild(details);
  appendPrimarySource(parent, product);
  if (conditionEntry && Array.isArray(conditionEntry.conditions) && conditionEntry.conditions.length && hasDocumentedConditionsSource(conditionEntry)) {
    const documented = section("Hechos documentados", "Solo lo que consta en una fuente con fecha; los huecos no se rellenan ni se convierten en oferta vigente.", "data-panel");
    const list = el("ul", { className: "detail-list" });
    for (const condition of conditionEntry.conditions) {
      let text = "";
      if (condition.metric === "annual_rate_percent") {
        const value = condition.state === "known" ? `${formatRate(condition.value)} TAE` : "sin cifra utilizable";
        text = `Tasa anual (TAE): ${value} · ${conditionStateText(condition)}`;
      } else if (condition.metric === "term_months") {
        text = `Plazo: ${condition.state === "known" ? `${condition.value} meses` : "no documentado"} · ${conditionStateText(condition)}`;
      } else {
        text = `${condition.metric} · ${conditionStateText(condition)}`;
      }
      if (condition.effective_to) text += ` · vigencia hasta ${condition.effective_to}`;
      if (Array.isArray(condition.notes) && condition.notes.length) text += ` · ${condition.notes.join(" ")}`;
      list.appendChild(el("li", {}, text));
    }
    documented.appendChild(list);
    if (Array.isArray(conditionEntry.rate_tiers) && conditionEntry.rate_tiers.length > 1) {
      const tiers = el("ul", { className: "detail-list" });
      for (const tier of conditionEntry.rate_tiers) {
        tiers.appendChild(el("li", {}, `${formatRate(tier.tae)} TAE / ${formatRate(tier.tin)} TIN · ${tier.condition_label || tier.condition}`));
      }
      documented.appendChild(textElement("p", "Tramos de la misma oferta, con su requisito:", "small"));
      documented.appendChild(tiers);
    }
    const conditionRef = conditionSourceRef(conditionEntry);
    if (conditionRef && conditionRef.url) {
      const sourceLine = el("p", { className: "source-line" });
      sourceLine.appendChild(document.createTextNode(`Fuente de las condiciones: ${conditionRef.url}`));
      if (conditionRef.retrieved_at) sourceLine.appendChild(document.createTextNode(` · consultada el ${conditionRef.retrieved_at}`));
      documented.appendChild(sourceLine);
    }
    parent.appendChild(documented);
  } else {
    parent.appendChild(callout("No hay condiciones documentadas para este producto; se mantiene como referencia de identidad. Los hechos vencidos, en conflicto o sin dato no se presentan como oferta vigente.", "info-note"));
  }
  const unknown = section("Qué queda por comprobar", "El ensayo no completa estos huecos con supuestos.", "data-panel");
  appendList(unknown, product.unknown_fields, "El registro no enumera campos desconocidos.");
  parent.appendChild(unknown);
  appendList(parent, product.conflicts, "Sin conflictos enumerados en la respuesta.");
}

function simulationBack() {
  if (state.simulation.step === 3) state.simulation.understood = false;
  if (state.simulation.step > 0 && state.simulation.step < 4) state.simulation.step -= 1;
  render();
}

function receiptReference() {
  const producto = (state.simulation.product && state.simulation.product.id) || "SIN-PRODUCTO";
  const sello = state.simulation.receiptAt || new Date().toLocaleString("es-ES");
  const compacto = sello.replace(/[^0-9]/g, "").slice(0, 12);
  return `ENS-${compacto || "000000000000"}-${producto}`;
}

function receiptConditionsTable(productId) {
  const tabla = el("table");
  const cabecera = el("thead");
  const fila = el("tr");
  ["Condición", "Valor", "Estado", "Fuente"].forEach((texto) => fila.appendChild(el("th", {}, texto)));
  cabecera.appendChild(fila);
  tabla.appendChild(cabecera);
  const cuerpo = el("tbody");
  const entry = state.conditions.byId.get(productId) || {};
  const condiciones = Array.isArray(entry.conditions) ? entry.conditions : [];
  const filas = condiciones.length ? condiciones : [null];
  filas.forEach((condition) => {
    const filaCuerpo = el("tr");
    if (!condition) {
      filaCuerpo.appendChild(el("td", { colspan: "4" }, "Ninguna condición transcrita para este producto."));
    } else {
      const row = CONDITION_ROWS[condition.metric];
      const etiqueta = row ? row.label : condition.metric;
      const valor = condition.state === "known" && condition.value !== null && condition.value !== undefined
        ? (row ? row.format(String(condition.value)) : String(condition.value))
        : "Sin dato documentado";
      filaCuerpo.appendChild(el("td", {}, etiqueta));
      filaCuerpo.appendChild(el("td", {}, valor || "Sin dato utilizable"));
      filaCuerpo.appendChild(el("td", {}, conditionStateText(condition)));
      const fuente = entry.source && isSafePrimaryUrl(entry.source.url)
        ? `${entry.source.url}${entry.source.retrieved_at ? ` · ${entry.source.retrieved_at}` : ""}`
        : "Sin fuente utilizable";
      filaCuerpo.appendChild(el("td", {}, fuente));
    }
    cuerpo.appendChild(filaCuerpo);
  });
  tabla.appendChild(cuerpo);
  return tabla;
}

function receiptBarcode(reference) {
  const tira = el("div", { className: "doc-barcode", "aria-hidden": "true" });
  const limpio = reference.replace(/[^A-Z0-9]/gi, "");
  for (let i = 0; i < limpio.length; i += 1) {
    const codigo = limpio.charCodeAt(i);
    const ancho = 1 + (codigo % 3);
    const barra = el("i");
    barra.style.width = `${ancho}px`;
    tira.appendChild(barra);
    const hueco = el("i");
    hueco.style.width = `${1 + ((codigo >> 2) % 2)}px`;
    hueco.style.background = "transparent";
    tira.appendChild(hueco);
  }
  return tira;
}

function docBox(titulo, pares) {
  const caja = el("div", { className: "doc-box" });
  caja.appendChild(el("h3", {}, titulo));
  const lista = el("dl");
  pares.forEach(([clave, valor]) => {
    lista.appendChild(el("dt", {}, clave));
    lista.appendChild(el("dd", {}, valor));
  });
  caja.appendChild(lista);
  return caja;
}

function docSection(numero, titulo) {
  const cabecera = el("h2");
  cabecera.appendChild(el("i", {}, `${numero}.`));
  cabecera.appendChild(document.createTextNode(titulo));
  return cabecera;
}

function buildReceiptDocument() {
  const producto = state.simulation.product;
  const referencia = receiptReference();
  const emitido = state.simulation.receiptAt || "No consta";
  const doc = el("div", { className: "receipt-doc" });

  const marca = el("div", { className: "doc-watermark", "aria-hidden": "true" });
  marca.appendChild(el("span", {}, "ENSAYO FICTICIO"));
  doc.appendChild(marca);

  const head = el("div", { className: "doc-head" });
  const izquierda = el("div");
  izquierda.appendChild(el("div", { className: "doc-brand" }, "Paideia"));
  izquierda.appendChild(el("div", { className: "doc-brand-sub" },
    "Laboratorio de educación financiera · Universidad de Málaga · Documento emitido por el propio interesado"));
  const derecha = el("div", { className: "doc-head-right" });
  derecha.appendChild(document.createTextNode("Expediente"));
  derecha.appendChild(el("strong", {}, referencia));
  derecha.appendChild(document.createTextNode("Emisión"));
  derecha.appendChild(el("strong", {}, emitido));
  derecha.appendChild(document.createTextNode("Serie"));
  derecha.appendChild(el("strong", {}, "ENS-FIC"));
  head.appendChild(izquierda);
  head.appendChild(derecha);
  doc.appendChild(head);
  doc.appendChild(el("div", { className: "doc-seal" }, "Sin validez contractual · no es una oferta"));

  const titulo = el("div", { className: "doc-title" });
  titulo.appendChild(el("h1", {}, "Justificante de ejercicio ficticio"));
  titulo.appendChild(el("span", {}, "Ejemplar del interesado"));
  doc.appendChild(titulo);

  const rejilla = el("div", { className: "doc-grid" });
  rejilla.appendChild(docBox("Interesado", [
    ["Titular", "No identificado: el ejercicio se hace en el navegador"],
    ["Domicilio", "No consta · no se recogen datos personales"],
    ["Condición", "Consumidor en simulación educativa"],
  ]));
  rejilla.appendChild(docBox("Operación", [
    ["Naturaleza", "Simulación: no hay solicitud ni contratación"],
    ["Canal", "Navegador del interesado, sin envío a terceros"],
    ["Fecha de efecto", "Ninguna: el documento no produce efectos"],
  ]));
  doc.appendChild(rejilla);

  doc.appendChild(docSection(1, "Objeto del documento"));
  doc.appendChild(el("p", {},
    "Este documento deja constancia de un ejercicio educativo realizado con datos ficticios sobre un producto del catálogo interno. No documenta una contratación, no acredita la disponibilidad del producto y no genera obligación alguna para ninguna de las partes, porque no hay partes intervinientes."));

  doc.appendChild(docSection(2, "Producto de referencia"));
  const tablaProducto = el("table");
  const cabeceraProducto = el("thead");
  const filaCabecera = el("tr");
  ["Campo", "Contenido"].forEach((texto) => filaCabecera.appendChild(el("th", {}, texto)));
  cabeceraProducto.appendChild(filaCabecera);
  tablaProducto.appendChild(cabeceraProducto);
  const cuerpoProducto = el("tbody");
  const filasProducto = producto ? [
    ["Denominación", productName(producto)],
    ["Familia", familyLabel(producto)],
    ["Entidad de referencia", issuerLabel(producto)],
    ["ISIN", producto.isin || "No indicado en el metadato"],
    ["Identidad", identityLabel(producto)],
    ["Fuente de identidad", isSafePrimaryUrl(producto.primary_url) ? producto.primary_url : "Sin URL utilizable"],
  ] : [["Producto", "No consta"]];
  filasProducto.forEach(([clave, valor]) => {
    const fila = el("tr");
    fila.appendChild(el("th", {}, clave));
    fila.appendChild(el("td", {}, valor));
    cuerpoProducto.appendChild(fila);
  });
  tablaProducto.appendChild(cuerpoProducto);
  doc.appendChild(tablaProducto);

  doc.appendChild(docSection(3, "Condiciones económicas documentadas"));
  doc.appendChild(receiptConditionsTable(producto ? producto.id : ""));
  doc.appendChild(el("p", { className: "doc-small" },
    "Solo se transcriben las condiciones publicadas por la fuente, con su estado y su fecha. Lo que la fuente no publica figura como «sin dato documentado»: no se estima ni se completa por inferencia."));

  doc.appendChild(docSection(4, "Importe del ejercicio"));
  const importe = el("div", { className: "doc-amount" });
  importe.appendChild(el("span", {}, "Cantidad imaginada"));
  importe.appendChild(el("strong", {}, formatCurrency(state.simulation.amount)));
  doc.appendChild(importe);
  doc.appendChild(el("p", { className: "doc-small" },
    "El importe se conserva solo en esta pestaña para el justificante. No se ha ordenado ningún movimiento, no se ha abierto cuenta y no se ha transmitido a ninguna entidad."));

  doc.appendChild(docSection(5, "Advertencias y exclusiones"));
  const aviso = el("div", { className: "doc-warning" },
    "Documento de ensayo. No es un contrato, ni una oferta vinculante, ni una confirmación de operación, ni una recomendación personalizada de inversión.");
  doc.appendChild(aviso);
  const exclusiones = el("ul", { className: "doc-exclusions" });
  [
    "No acredita disponibilidad del producto ni vigencia de sus condiciones.",
    "No recoge fiscalidad, comisiones de terceros, garantías ni evaluación de idoneidad.",
    "No sustituye la información precontractual ni el contrato de la entidad.",
    "No existe firma válida: las líneas siguientes son formato, no consentimiento.",
  ].forEach((texto) => exclusiones.appendChild(el("li", {}, texto)));
  doc.appendChild(exclusiones);

  doc.appendChild(docSection(6, "Firma y trazabilidad"));
  const firmas = el("div", { className: "doc-signs" });
  const firmaInteresado = el("div", { className: "doc-sign" }, "El interesado");
  firmaInteresado.appendChild(el("small", {}, "Sin firma válida · ejercicio no contratado"));
  const firmaEntidad = el("div", { className: "doc-sign" }, "Entidad de referencia");
  firmaEntidad.appendChild(el("small", {}, "No interviene ni suscribe este documento"));
  firmas.appendChild(firmaInteresado);
  firmas.appendChild(firmaEntidad);
  doc.appendChild(firmas);

  const codigo = el("div", { className: "doc-code" });
  codigo.appendChild(receiptBarcode(referencia));
  const textoCodigo = el("div", { className: "doc-code-text" });
  textoCodigo.appendChild(document.createTextNode(referencia));
  textoCodigo.appendChild(el("br"));
  textoCodigo.appendChild(document.createTextNode("Emitido en local · no verificable por terceros"));
  codigo.appendChild(textoCodigo);
  doc.appendChild(codigo);

  doc.appendChild(el("div", { className: "doc-footer" },
    "Paideia · justificante de ejercicio ficticio generado en el navegador. No se ha transmitido a ninguna entidad ni tiene validez contractual."));
  return doc;
}

function mountReceiptDocument() {
  let contenedor = document.getElementById("receipt-print");
  if (!contenedor) {
    contenedor = el("section", { id: "receipt-print", "aria-hidden": "true" });
    document.body.appendChild(contenedor);
  }
  contenedor.replaceChildren(buildReceiptDocument());
}

function clearReceiptDocument() {
  const contenedor = document.getElementById("receipt-print");
  if (contenedor) contenedor.remove();
  document.body.classList.remove("receipt-printing");
}

function printReceiptDocument() {
  mountReceiptDocument();
  document.body.classList.add("receipt-printing");
  const limpiar = () => {
    document.body.classList.remove("receipt-printing");
    window.removeEventListener("afterprint", limpiar);
  };
  window.addEventListener("afterprint", limpiar);
  window.print();
}

function renderSimulation() {
  const { page, heading } = pageFrame("Simulación · operación ficticia", "Ensayo de una decisión", "Usa un candidato del catálogo como referencia de identidad. La cantidad y el ejercicio son ficticios; no hay contratación ni solicitud.");
  page.appendChild(callout("ENSAYO FICTICIO · No se enviará nada ni se moverá dinero. No introduzcas identificadores, credenciales, cuenta, tarjeta ni datos de pago.", "warning-note"));
  renderSimulationProgress(page);
  if (state.conditions.error) page.appendChild(errorBox(apiErrorText(state.conditions.error), () => loadConditions(true)));
  if (!state.conditions.loaded && !state.conditions.loading && !state.conditions.error) loadConditions();
  if (state.simulation.step === 0) {
    const panel = el("section", { className: "paper-section" });
    panel.appendChild(el("h2", {}, "1. Elige un producto de referencia"));
    panel.appendChild(textElement("p", "La selección solo identifica una ficha de investigación. No acredita que se pueda contratar ni que las condiciones estén vigentes."));
    const candidates = el("div", { id: "simulation-candidates" });
    panel.appendChild(candidates);
    page.appendChild(panel);
    renderSimulationCandidates();
    if (!state.simulation.loaded && !state.simulation.loading && !state.simulation.error) loadSimulationCatalogue();
  } else if (state.simulation.step === 1) {
    const panel = el("section", { className: "paper-section" });
    panel.appendChild(el("h2", {}, "2. Revisa qué se sabe y qué no"));
    if (state.simulation.product) simulationProductReview(panel, state.simulation.product);
    panel.appendChild(callout("La respuesta del catálogo aporta metadatos de identidad, no una oferta. El ensayo no convertirá campos pendientes en condiciones.", "warning-note"));
    panel.appendChild(el("div", { className: "button-row" }, [button("Volver", simulationBack, "button button-secondary"), button("Continuar con el importe ficticio", () => { state.simulation.step = 2; render(); }, "button button-primary")]));
    page.appendChild(panel);
  } else if (state.simulation.step === 2) {
    const panel = el("section", { className: "paper-section" });
    panel.appendChild(el("h2", {}, "3. Elige un importe para el ejercicio"));
    const form = el("form", { novalidate: true });
    const amount = el("input", { type: "number", id: "simulation-amount", min: "0.01", step: "0.01", required: true, inputmode: "decimal", "aria-describedby": "simulation-amount-help" });
    if (state.simulation.amount) amount.value = state.simulation.amount;
    form.appendChild(field("Importe imaginado (€)", amount, "Solo se conserva en esta pestaña para el justificante. No se transmite al backend.", amount.id));
    const help = form.querySelector(".field-help");
    help.id = "simulation-amount-help";
    const error = textElement("p", "", "form-error");
    error.id = "simulation-amount-error";
    error.setAttribute("role", "alert");
    form.appendChild(error);
    const clearAmountError = () => {
      error.textContent = "";
      amount.removeAttribute("aria-invalid");
      amount.setAttribute("aria-describedby", "simulation-amount-help");
    };
    amount.addEventListener("input", clearAmountError);
    form.appendChild(el("div", { className: "button-row" }, [button("Volver", simulationBack, "button button-secondary"), button("Continuar", null, "button button-primary", { type: "submit" })]));
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const raw = amount.value.trim();
      const numeric = Number(raw);
      if (!raw || !Number.isFinite(numeric) || numeric <= 0 || !/^\d{1,10}(?:\.\d{1,2})?$/.test(raw)) {
        error.textContent = "Introduce un importe mayor que cero, con hasta dos decimales.";
        amount.setAttribute("aria-invalid", "true");
        amount.setAttribute("aria-describedby", "simulation-amount-help simulation-amount-error");
        amount.focus();
        return;
      }
      state.simulation.amount = raw;
      state.simulation.step = 3;
      render();
    });
    panel.appendChild(form);
    panel.appendChild(callout("Este importe no se usa para calcular un rendimiento ni se envía a /api/calculate.", "info-note"));
    page.appendChild(panel);
  } else if (state.simulation.step === 3) {
    const panel = el("section", { className: "paper-section" });
    panel.appendChild(el("h2", {}, "4. Confirma que comprendes los límites"));
    const check = el("input", { type: "checkbox", id: "simulation-understood", checked: state.simulation.understood });
    const confirm = el("label", { className: "choice", htmlFor: "simulation-understood" }, [check, el("span", {}, "Entiendo que esto es un ensayo ficticio: no es una oferta, no se enviará una solicitud, no se abrirá una cuenta ni se moverá dinero. La disponibilidad, los costes, las garantías y la posibilidad de pérdida no quedan resueltos por esta ficha. Los hechos documentados, aunque estén vencidos, en conflicto o sin dato, no son una oferta vigente." )]);
    panel.appendChild(confirm);
    const actions = el("div", { className: "button-row" });
    actions.append(button("Volver", simulationBack, "button button-secondary"), button("Terminar ensayo y crear justificante", () => {
      if (!check.checked) return;
      state.simulation.understood = true;
      state.simulation.receiptAt = new Date().toLocaleString("es-ES");
      state.simulation.step = 4;
      render();
    }, "button button-primary", { disabled: !state.simulation.understood }));
    check.addEventListener("change", () => {
      state.simulation.understood = check.checked;
      actions.querySelector(".button-primary").disabled = !check.checked;
    });
    panel.append(confirm, actions);
    page.appendChild(panel);
  } else {
    const receipt = el("section", { className: "receipt", "data-printable": "receipt", "aria-labelledby": "receipt-title" });
    receipt.appendChild(textElement("p", "JUSTIFICANTE DE EJERCICIO · ENSAYO FICTICIO", "receipt-kicker"));
    receipt.appendChild(el("h2", { id: "receipt-title" }, "Ensayo terminado"));
    receipt.appendChild(textElement("p", state.simulation.receiptAt ? `Creado localmente en esta pestaña · ${state.simulation.receiptAt}` : "Creado localmente en esta pestaña.", "receipt-stamp"));
    if (state.simulation.product) {
      receipt.appendChild(el("h3", {}, productName(state.simulation.product)));
      receipt.appendChild(textElement("p", `${familyLabel(state.simulation.product.family)} · ${issuerLabel(state.simulation.product)}`));
      receipt.appendChild(textElement("p", `ISIN: ${state.simulation.product.isin || "no indicado"}`));
      const conditionEntry = state.conditions.byId.get(state.simulation.product.id);
      if (conditionEntry && conditionEntry.source && isSafePrimaryUrl(conditionEntry.source.url)) {
        const sourceLine = el("p", { className: "source-line" });
        sourceLine.appendChild(document.createTextNode(`Hechos documentados: ${conditionEntry.source.url}`));
        if (conditionEntry.source.retrieved_at) sourceLine.appendChild(document.createTextNode(` · consultada el ${conditionEntry.source.retrieved_at}`));
        receipt.appendChild(sourceLine);
      }
      appendPrimarySource(receipt, state.simulation.product);
    }
    receipt.appendChild(textElement("p", `Importe imaginado: ${formatCurrency(state.simulation.amount)}`));
    receipt.appendChild(el("p", { className: "receipt-warning" }, "No se ha enviado una solicitud, abierto una cuenta ni movido dinero. Esto no es un contrato ni una confirmación de operación."));
    receipt.appendChild(textElement("p", "La identidad del candidato no acredita disponibilidad ni condiciones vigentes. Los hechos documentados pueden estar vencidos, en conflicto o sin dato y no se presentan como oferta vigente. El ejercicio no contiene fiscalidad, costes de producto ni evaluación de riesgo."));
    const actions = el("div", { className: "button-row no-print" });
    actions.append(button("Imprimir justificante HTML", () => printReceiptDocument(), "button button-primary"), button("Terminar / volver a empezar", () => {
      state.simulation = { step: 0, products: state.simulation.products, loaded: state.simulation.loaded, loading: false, error: null, requestId: state.simulation.requestId, chosenId: "", product: null, amount: "", understood: false, receiptAt: "" };
      render();
    }, "button button-secondary"));
    page.append(receipt, actions);
    mountReceiptDocument();
  }
  return heading;
}

function renderGlossary() {
  const { page, heading } = pageFrame("Glosario · palabras breves", "Un glosario para leer con calma", "Definiciones orientativas. Las condiciones reales de cada producto deben comprobarse en sus documentos aplicables.");
  const terms = [
    ...Object.values(window.ContextHelp.definitions).map(({ label, definition }) => [label, definition]),
    ["Plazo / vencimiento", "Periodo indicado para una condición o instrumento. La fecha de vencimiento no prueba que se pueda contratar hoy."],
    ["Costes", "Comisiones, gastos y costes de transacción que pueden afectar el resultado. Una cifra aislada no garantiza que incluya todos los costes."],

    ["Nominal y real", "Nominal es el importe expresado en euros del periodo. Real intenta expresar poder adquisitivo tras ajustar por inflación; sigue siendo un cálculo hipotético."],
    ["ISIN", "Código internacional que identifica un valor o una clase de instrumento. Por sí solo no informa de precio, riesgo, disponibilidad o permiso de distribución."],
    ["Fondo de inversión", "Vehículo que agrupa aportaciones bajo una política de inversión. Sus condiciones, costes, riesgo y clase dependen de documentación concreta."],
    ["ETF UCITS", "Fondo cotizado sujeto a un marco UCITS/OICVM. Que cotice en bolsa no elimina el riesgo ni significa que sea adecuado o esté disponible para una persona concreta."],
    ["Garantía de depósitos", "Protección legal aplicable a depósitos que cumplan ciertos requisitos, con límites y entidad/país responsables. No es una garantía general para fondos, ETF o valores."],
    ["Candidato de investigación", "Registro usado para explorar identidad y fuentes. No equivale a producto publicado, oferta comercial ni condiciones vigentes."]
  ];
  const list = el("dl", { className: "glossary-list" });
  terms.forEach(([term, definition]) => list.appendChild(el("div", { className: "glossary-item" }, [el("dt", {}, term), el("dd", {}, definition)])));
  page.appendChild(list);
  page.appendChild(callout("Este glosario es breve y no constituye asesoramiento financiero, fiscal o jurídico.", "info-note"));
  return heading;
}

function updatePreview(holder) {
  holder.replaceChildren();
  const selected = PREVIEW_FIELDS.filter((fieldName) => state.previewFields.has(fieldName));
  if (!selected.length) {
    holder.appendChild(textElement("p", "No has seleccionado campos. Esta vista previa no enviará nada."));
    return;
  }
  const list = el("dl", { className: "detail-list" });
  selected.forEach((key) => list.append(el("dt", {}, PROFILE_LABELS[key]), el("dd", {}, displayProfileValue(key))));
  holder.appendChild(list);
  holder.appendChild(textElement("p", "Vista previa local de los campos elegidos. No se hace ninguna petición de red.", "small muted"));
}

function renderPrivacy() {
  const { page, heading } = pageFrame("Privacidad · memoria primero", "Tu perfil y tu alcance", "El mapa vive en memoria durante esta sesión. Guardarlo en este dispositivo requiere una acción explícita; la vista previa de contexto no se envía.");
  const storage = section("Guardar perfil en este dispositivo", "Opt-in independiente. Antes de activarlo, terminar o revisar el cuestionario no guarda el perfil.", "paper-section");
  const stateText = storageStatusText();
  storage.appendChild(el("p", { id: "profile-storage-state", role: "status" }, stateText));

  const toggleId = "profile-persist-toggle";
  const toggle = el("input", { type: "checkbox", id: toggleId, checked: state.profileOptIn, disabled: !state.profileComplete });
  storage.appendChild(el("label", { className: "choice", htmlFor: toggleId }, [toggle, el("span", {}, "Quiero permitir el almacenamiento local del mapa revisado en este dispositivo." )]));
  storage.appendChild(textElement("p", "Al marcar la casilla y pulsar Guardar se crea una copia local, incluidos los estados aún no preguntados. Después, los cambios posteriores se guardarán automáticamente en este navegador durante esta sesión mientras siga activado el guardado local. Al recargar, la copia se conserva para revisión pero el guardado automático queda desactivado hasta que vuelvas a marcar la casilla y pulsar Guardar. El almacenamiento local es independiente del procesamiento local y no autoriza ningún envío remoto." + (state.profileComplete ? "" : " Revisa el mapa primero para activar el guardado opt-in."), "field-help"));
  const feedback = el("div", { id: "profile-storage-feedback", className: "note", role: "status" });
  feedback.appendChild(textElement("p", state.storageNotice || "Todavía no se ha guardado nada en esta visita."));
  storage.appendChild(feedback);
  const save = button("Guardar perfil local", saveProfileAfterConsent, "button button-primary", { disabled: !state.profileComplete });
  storage.appendChild(el("div", { className: "button-row" }, [save, button("Revocar y borrar copia", () => {
    if (!window.confirm("¿Revocar el permiso y borrar la copia local del mapa de este dispositivo, incluidas las versiones anteriores? No se borra el historial del chat de esta pestaña ni los mensajes ya enviados al proveedor; el historial se elimina con su propio control. Esta acción no se puede deshacer.")) return;
    toggle.checked = false;
    const result = removeSavedProfile();
    feedback.className = result.ok ? "success-note" : "error-note";
    feedback.replaceChildren(textElement("p", state.storageNotice));
    updateStorageStatusLine();
    renderStorageWarning();
  }, "button button-secondary")]));
  toggle.addEventListener("change", () => {
    if (!toggle.checked) {
      if (state.profileOptIn && !window.confirm("¿Borrar el perfil guardado en este dispositivo, incluidas las versiones anteriores? No se borra el historial del chat ni los mensajes ya enviados al proveedor.")) {
        toggle.checked = true;
        return;
      }
      const result = state.profileOptIn ? removeSavedProfile() : { ok: true };
      state.profileOptIn = false;
      feedback.className = result.ok ? "note" : "error-note";
      feedback.replaceChildren(textElement("p", result.ok && !state.storageProblem ? "Guardado desactivado. El perfil actual sigue solo en memoria." : "El estado local es incompleto o desconocido; podrían quedar copias."));
    } else {
      state.profileOptIn = false;
      feedback.className = "info-note";
      feedback.replaceChildren(textElement("p", "El consentimiento está marcado, pero todavía no se ha guardado. Pulsa «Guardar perfil local» para escribir la copia."));
    }
    updateStorageStatusLine();
    renderStorageWarning();
  });
  page.appendChild(storage);

  const transmission = section("Qué sale de este navegador", "El chat es la única función que puede enviar texto a un proveedor externo. La biblioteca, el comparador, los escenarios y el ensayo usan el servicio local.", "paper-section");
  const transmissionList = el("ul", { className: "text-list" });
  for (const item of [
    "Pregunta: se envía solo cuando marcas el consentimiento del chat y pulsas «Enviar pregunta». Si la IA no está configurada, la pregunta no se envía y no se hace ninguna petición de chat al servidor.",
    "Mapa: no se envía por defecto. Con el consentimiento de contexto se envían únicamente los campos que marques, nunca el mapa completo ni los estados no preguntados.",
    "Historial: es opcional y separado del mapa. Vive en la memoria de esta pestaña y solo se reenvía con su propia autorización; no se guarda en el almacenamiento local.",
    "Proveedor: lo ya enviado queda fuera de este navegador y no se puede borrar desde aquí. La retención depende de las condiciones del proveedor configurado.",
    "Almacenamiento local: guardar el mapa en este dispositivo no autoriza ningún envío remoto."
  ]) transmissionList.appendChild(el("li", {}, item));
  transmission.appendChild(transmissionList);
  page.appendChild(transmission);

  page.appendChild(callout("Alcance del borrado: «Revocar y borrar copia» elimina solo la copia local del mapa y las versiones anteriores. No borra el historial del chat de esta pestaña ni los mensajes o consultas ya enviados al proveedor; el historial se elimina aparte con «Borrar historial de esta pestaña» y lo ya enviado queda fuera de este navegador.", "info-note"));

  const preview = section("Vista previa local de contexto", "Elige exactamente qué campos incluirías en una explicación futura. El valor mostrado solo se lee desde la memoria de esta pestaña.", "paper-section");
  preview.appendChild(callout("Sin conexión a IA. Confirmar aquí no envía datos ni activa ningún chat. /api/context-preview se reserva para fixtures sintéticas; esta interfaz no lo llama.", "warning-note"));
  const fields = el("div", { className: "privacy-field-list" });
  PREVIEW_FIELDS.forEach((key) => {
    const id = `preview-${key}`;
    const check = el("input", { type: "checkbox", id, checked: state.previewFields.has(key) });
    const label = el("label", { className: "choice", htmlFor: id }, [check, el("span", {}, PROFILE_LABELS[key])]);
    check.addEventListener("change", () => {
      if (check.checked) state.previewFields.add(key); else state.previewFields.delete(key);
      state.previewAcknowledged = false;
      const previewHolder = document.getElementById("privacy-preview");
      if (previewHolder) updatePreview(previewHolder);
      const acknowledgement = document.getElementById("preview-acknowledged");
      if (acknowledgement) acknowledgement.checked = false;
      const confirmButton = document.getElementById("preview-confirm");
      if (confirmButton) confirmButton.disabled = true;
      const result = document.getElementById("preview-result");
      if (result) result.textContent = "La selección cambió. La vista previa sigue local; confirma de nuevo si quieres dejar constancia en esta sesión.";
    });
    fields.appendChild(label);
  });
  preview.appendChild(fields);
  const previewHolder = el("div", { id: "privacy-preview", className: "privacy-preview", "aria-live": "polite" });
  updatePreview(previewHolder);
  preview.appendChild(previewHolder);
  const ackId = "preview-acknowledged";
  const ack = el("input", { type: "checkbox", id: ackId, checked: state.previewAcknowledged });
  preview.appendChild(el("label", { className: "choice", htmlFor: ackId }, [ack, el("span", {}, "He revisado la vista previa y entiendo que no se enviará nada ahora." )]));
  const result = textElement("p", state.previewAcknowledged ? "La decisión solo se recuerda en esta sesión." : "Sin confirmación. No se ha enviado nada.", "chat-state");
  result.id = "preview-result";
  result.setAttribute("role", "status");
  const confirm = button("Confirmar solo para esta sesión", () => {
    if (!ack.checked) return;
    state.previewAcknowledged = true;
    result.textContent = "Decisión recordada solo en memoria. No se ha enviado nada y no se ha llamado a /api/context-preview.";
  }, "button button-secondary", { disabled: !ack.checked });
  confirm.id = "preview-confirm";
  ack.addEventListener("change", () => { confirm.disabled = !ack.checked; state.previewAcknowledged = false; result.textContent = "Sin confirmación. No se ha enviado nada."; });
  preview.append(el("div", { className: "button-row" }, [confirm]), result);
  page.appendChild(preview);
  page.appendChild(callout("No pedimos nombre, DNI, IBAN, tarjeta, credenciales ni datos de pago. Borrar el perfil no afecta a los datos del catálogo del servicio local.", "info-note"));
  return heading;
}

let statusCheckInFlight = false;
let statusAutoRetryTimer = null;
let statusSuccessDuringCheck = false;
const STATUS_AUTO_RETRY_MS = 1500;

function cancelStatusAutoRetry() {
  if (statusAutoRetryTimer !== null) {
    clearTimeout(statusAutoRetryTimer);
    statusAutoRetryTimer = null;
  }
}

function refreshStatusAfterApiSuccess() {
  if (statusCheckInFlight) {
    // La comprobación en curso puede fallar aunque la API ya responda: permite un reintento único.
    statusSuccessDuringCheck = true;
    return;
  }
  if (state.statusError) checkLocalStatus();
}

async function checkLocalStatus() {
  if (statusCheckInFlight) return;
  cancelStatusAutoRetry();
  statusCheckInFlight = true;
  statusSuccessDuringCheck = false;
  setStatusChip("Comprobando servicio local…");
  state.statusError = null;
  try {
    const status = await apiRequest(API.status);
    state.status = status;
    const caps = status.ai?.capabilities;
    const capabilityNote = document.getElementById("chat-context-capabilities");
    if (capabilityNote) capabilityNote.textContent = `Mapa: ${caps?.context === true ? "puedes adjuntar los campos que marques" : "no disponible"}; historial: ${caps?.history === true ? "habilitado" : "desactivado"}.`;
    const providerNote = document.getElementById("chat-provider-note");
    if (providerNote) providerNote.textContent = chatProviderNote();
    for (const [id, available] of [["chat-context-consent", caps?.context === true], ["chat-history-consent", caps?.history === true]]) {
      const control = document.getElementById(id);
      if (control) { control.disabled = !available; if (!available) control.checked = false; }
    }
    PaideiaChatContext.fields.forEach((key, index) => {
      const control = document.getElementById(`chat-context-field-${index}`);
      if (!control) return;
      const answer = PROFILE_MODEL.getAnswer(state.profile, key);
      const available = caps?.context === true && !!answer && answer.estado === "declarado";
      control.disabled = !available;
      if (!available) control.checked = false;
    });
    const mode = status.mode === "local_prototype" ? "Prototipo local"
      : status.mode === "public_demo" || status.mode === "public_serverless" ? "Versión pública"
      : "Servicio local";
    const aiConfigured = status.ai?.status === "configured_not_verified";
    // Sin IA configurada el aviso vive en el panel de Pai, no en la cabecera:
    // «IA no conectada» arriba desanima sin explicar nada.
    setStatusChip(aiConfigured ? `${mode} · IA configurada` : mode, "ready");
    if (state.route) renderContext(state.route);
    // El primer render ocurre sin estado; si el servicio resulta ser de prueba con
    // cálculo estructurado, el bloque sintético debe aparecer sin cambiar de ruta.
    if (state.route === "inicio" && status.ai?.status === "test_only"
        && status.ai?.capabilities?.structured_education === true
        && !document.getElementById("pai-test-options")) {
      // El estado llega tarde y el render sustituye el DOM: se conserva lo que el
      // usuario ya tenía abierto o enfocado para no moverle el cursor ni la vista.
      const focused = document.activeElement?.id === "chat-message";
      const openOptions = document.getElementById("pai-context")?.open === true;
      render({ preserveFocus: true });
      if (openOptions) { const panel = document.getElementById("pai-context"); if (panel) panel.open = true; }
      if (focused) document.getElementById("chat-message")?.focus();
    }
  } catch (error) {
    state.statusError = error;
    setStatusChip("Servicio local sin respuesta", "error");
    const providerNote = document.getElementById("chat-provider-note");
    if (providerNote) providerNote.textContent = chatProviderNote();
    // Una sola comprobación automática: la API ya respondió a otra petición, así que
    // el fallo puede ser transitorio. Sin bucles: si este reintento también falla, no se repite.
    if (statusSuccessDuringCheck && statusAutoRetryTimer === null) {
      statusAutoRetryTimer = setTimeout(() => {
        statusAutoRetryTimer = null;
        if (state.statusError && !statusCheckInFlight) checkLocalStatus();
      }, STATUS_AUTO_RETRY_MS);
    }
  } finally {
    statusCheckInFlight = false;
  }
}

function renderStorageWarning() {
  const main = document.getElementById("main-content");
  const previous = document.getElementById("profile-autosave-warning");
  if (previous) previous.remove();
  const crossTabWarning = state.storageRevokedElsewhere || state.storageExternalCopy;
  if (!state.storageProblem && !crossTabWarning) return;
  if (crossTabWarning && !state.storageProblem && state.route === "privacidad") return;
  const warning = el("div", { id: "profile-autosave-warning", className: state.storageProblem ? "error-note" : "warning-note", role: "alert" });
  if (state.profileUnsaved) warning.appendChild(textElement("p", "No se pudo confirmar el guardado automático. El mapa mostrado contiene cambios en memoria; la copia guardada podría ser una versión anterior. Al recargar puedes perder esos cambios."));
  warning.appendChild(textElement("p", state.storageNotice));
  if (state.profileOptIn) warning.appendChild(button("Reintentar guardado local", () => {
    saveProfileLocally();
    render();
  }, "button button-secondary"));
  main.prepend(warning);
}

let lastRenderedRoute = null;

function render(options = {}) {
  if (state.route === "simulacion" && routeFromHash() !== "simulacion") clearReceiptDocument();
  const focusSnapshot = captureFocus();
  const route = routeFromHash();
  if (state.route === "simulacion" && route !== "simulacion") state.simulation.understood = false;
  if (state.route === "comparar" && route !== "comparar" && state.diagnosis.busy) {
    state.diagnosis = { requestId: state.diagnosis.requestId + 1, ids: [], busy: false, error: false, result: null };
  }
  const routeChanged = lastRenderedRoute !== null && lastRenderedRoute !== route;
  lastRenderedRoute = route;
  state.route = route;
  updateNavigation(route);
  renderContext(route);
  const titles = { inicio: "Inicio", perfil: "Tu mapa", biblioteca: "Biblioteca", comparar: "Comparar", escenarios: "Escenarios", simulacion: "Ensayo ficticio", glosario: "Glosario", privacidad: "Privacidad" };
  document.title = `Paideia · ${titles[route] || "Cuaderno de ruta"}`;
  let heading;
  if (route === "inicio") heading = renderHome();
  else if (route === "perfil") heading = renderProfile();
  else if (route === "biblioteca") heading = renderLibrary();
  else if (route === "comparar") heading = renderComparePage();
  else if (route === "escenarios") heading = renderScenario();
  else if (route === "simulacion") heading = renderSimulation();
  else if (route === "glosario") heading = renderGlossary();
  else heading = renderPrivacy();
  renderStorageWarning();
  if (route === "perfil" && state.profileConfirmKey) {
    // El foco va al botón del box para poder seguir con el teclado.
    const primary = document.querySelector(".profile-confirm .button-primary");
    if (primary) primary.focus();
  } else if (routeChanged) {
    focusHeading(heading);
  } else if (!options.preserveFocus && focusSnapshot.hadFocus) {
    const active = document.activeElement;
    if (!active || active === document.body || active === document.documentElement || !active.isConnected) focusHeading(heading);
  }
}

function startApp() {
  initStorage();
  const skipLink = document.querySelector(".skip-link");
  if (skipLink) skipLink.addEventListener("click", (event) => {
    event.preventDefault();
    const main = document.getElementById("main-content");
    if (main) main.focus();
  });
  document.getElementById("status-retry").addEventListener("click", checkLocalStatus);
  document.getElementById("clear-profile").addEventListener("click", clearProfile);
  window.addEventListener("hashchange", render);
  window.addEventListener("storage", handleStorageEvent);
  render();
  checkLocalStatus();
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { isSafePrimaryUrl, validateProfileSnapshot: PROFILE_MODEL.validateSnapshot, profileModel: PROFILE_MODEL };
}
if (typeof document !== "undefined") startApp();
