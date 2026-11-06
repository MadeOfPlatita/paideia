"use strict";

(function exposeProfileModel(root, factory) {
  const model = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = model;
  if (root) root.PaideiaProfileModel = model;
})(typeof globalThis !== "undefined" ? globalThis : this, function createProfileModel() {
  const SCHEMA_VERSION = 2;
  const PROFILE05_VERSION = "1.0.0";
  const STORAGE_KEY = "paideia.profile.v2";
  const LEGACY_STORAGE_KEYS = Object.freeze(["paideia.profile.v1", "paideia.profile"]);
  const ANSWER_STATES = new Set(["declarado", "no_se", "omitido", "sin_preguntar"]);
  const MAX_DECIMAL_INTEGER_DIGITS = 10;
  const MAX_DECIMAL = "9999999999.99";
  const MAX_PERCENT = "100";

  const enumValues = Object.freeze({
    objective: ["colchon_imprevistos", "gasto_previsto", "ahorro_largo_plazo", "entender_riesgo", "comparar_familias", "aprender_conceptos", "curiosear"],
    horizon: ["menos_6_meses", "6_12_meses", "1_3_anos", "mas_3_anos", "sin_fecha"],
    liquidity: ["acceso_cualquier_momento", "planificar_fecha", "solo_dinero_ficticio"],
    experience: ["empezando", "leido_o_comparado", "ha_tenido_alguno", "prefiere_no_contar"],
    topics: ["cuentas_remuneradas", "depositos", "deuda_publica", "fondos", "etf"],
    periodicity: ["semanal", "cada_14_dias", "dos_veces_al_mes", "mensual", "anual"],
    commitmentHorizon: ["menos_3_meses", "3_6_meses", "6_12_meses", "fecha_no_clara"],
    tolerance: ["preferiria_salir", "esperaria_con_inquietud", "podria_esperar_aceptando_caidas"],
    lossImpact: ["sin_cambio_en_necesidad_o_meta", "retrasaria_o_reduciria_meta", "afectaria_gasto_esencial_o_compromiso"]
  });

  const choiceOptions = (values, labels) => Object.freeze(values.map((value, index) => Object.freeze({ value, label: labels[index] })));
  const QUESTION_DEFS = Object.freeze([
    Object.freeze({
      key: "respuestas.objetivo", legacyKey: "objective", branch: "core", kind: "choice",
      label: "Objetivo de aprendizaje", title: "¿Qué te gustaría explorar primero?",
      help: "Orienta la conversación con Pai y el orden de los ejemplos; no elige productos por ti.",
      options: choiceOptions(enumValues.objective, ["Entender un colchón para imprevistos", "Preparar un gasto con fecha", "Aprender sobre ahorro a largo plazo", "Entender el riesgo y las posibles pérdidas", "Comparar familias que yo elija", "Aprender conceptos básicos", "Solo curiosear"])
    }),
    Object.freeze({
      key: "respuestas.horizonte", legacyKey: "horizon", branch: "core", kind: "choice",
      label: "Horizonte", title: "Si este ejemplo tuviera una meta, ¿cuándo podrías necesitar ese dinero?",
      help: "Una referencia para explicar plazos; no es una predicción.",
      options: choiceOptions(enumValues.horizon, ["En menos de 6 meses", "Entre 6 y 12 meses", "Entre 1 y 3 años", "En más de 3 años", "No hay fecha; solo quiero aprender"])
    }),
    Object.freeze({
      key: "respuestas.liquidez", legacyKey: "liquidity", branch: "core", kind: "choice", asked: false,
      label: "Necesidad de liquidez", title: "¿Cuánto te importa poder disponer rápidamente del dinero del ejemplo?",
      help: "Disponibilidad no significa ausencia de pérdidas. Puedes usar solo cifras ficticias.",
      options: choiceOptions(enumValues.liquidity, ["Necesitaría poder disponer de él en cualquier momento", "Podría planificar una fecha para disponer de él", "Solo usaré cifras ficticias; no hay dinero real"])
    }),
    Object.freeze({
      key: "respuestas.experiencia", legacyKey: "knowledge", branch: "core", kind: "experience",
      label: "Conocimientos y experiencia", title: "¿Qué conoces y qué te gustaría aprender?",
      help: "La experiencia no demuestra que otro producto sea adecuado. Sirve para ajustar el nivel de las explicaciones.",
      options: choiceOptions(enumValues.experience, ["Estoy empezando", "He leído o comparado, pero no los he tenido", "He tenido alguno y quiero repasar", "Prefiero no contar mi experiencia"])
    }),
    Object.freeze({
      key: "detalle_economico.importe_objetivo", legacyKey: null, branch: "economy", kind: "amount",
      label: "Importe objetivo", title: "¿Tienes un importe aproximado para esa meta?",
      help: "Opcional. Importe en euros; introduce una cifra orientativa, no hace falta que sea exacta."
    }),
    Object.freeze({
      key: "detalle_economico.ingresos_netos", legacyKey: "income", branch: "economy", kind: "flow", asked: false,
      label: "Ingresos netos mensuales", title: "¿En qué importe mensual aproximado están tus ingresos netos?",
      help: "Opcional. No necesitamos nóminas, empleador ni datos bancarios. La periodicidad se fija en mensual para este campo."
    }),
    Object.freeze({
      key: "detalle_economico.gastos_esenciales", legacyKey: "expenses", branch: "economy", kind: "flow", asked: false,
      label: "Gastos esenciales mensuales", title: "¿En qué importe mensual aproximado están tus gastos esenciales?",
      help: "Opcional. Por ejemplo, vivienda, alimentación y transporte. No se calcula solvencia."
    }),
    Object.freeze({
      key: "detalle_economico.deuda", legacyKey: null, branch: "economy", kind: "debt", asked: false,
      label: "Deuda", title: "¿Estás pagando alguna deuda ahora?",
      help: "Opcional. Sin deuda declarada, saldo, cuota y coste desconocidos son estados distintos. No se compara deuda con una inversión."
    }),
    Object.freeze({
      key: "detalle_economico.colchon_liquido", legacyKey: null, branch: "economy", kind: "amount", asked: false,
      label: "Colchón líquido", title: "¿En qué importe aproximado está el dinero que podrías usar con rapidez?",
      help: "Opcional. No fijamos un colchón obligatorio ni deducimos cuánto deberías tener."
    }),
    Object.freeze({
      key: "detalle_economico.compromisos_proximos", legacyKey: null, branch: "economy", kind: "commitments", asked: false,
      label: "Compromisos próximos", title: "¿Prevés algún gasto o compromiso importante durante los próximos 12 meses?",
      help: "Opcional. No hace falta indicar qué vas a comprar; puedes declarar solo un rango total y un plazo."
    }),
    Object.freeze({
      key: "riesgo.tolerancia", legacyKey: "risk", branch: "risk", kind: "choice", asked: false,
      label: "Tolerancia ante cambios", title: "En este ejemplo ficticio, 1.000 € pasan temporalmente a valer 900 €. ¿Qué crees que harías?",
      help: "Describe una reacción/preferencia declarada; no mide capacidad económica ni predice conducta.",
      options: choiceOptions(enumValues.tolerance, ["Me inquietaría y probablemente querría salir", "Me inquietaría, pero esperaría a entender qué ha pasado", "Podría esperar, sabiendo que el valor puede caer más"])
    }),
    Object.freeze({
      key: "riesgo.capacidad_perdidas", legacyKey: null, branch: "risk", kind: "capacity", asked: false,
      label: "Impacto de una pérdida", title: "En ese mismo ejemplo ficticio, si faltaran 100 €, ¿qué efecto tendría en una necesidad o meta importante?",
      help: "Pregunta por impacto, no por cuánto riesgo te gusta. No se deduce de tus ingresos.",
      options: choiceOptions(enumValues.lossImpact, ["No cambiaría una necesidad ni una meta importante", "Me obligaría a retrasar o reducir una meta", "Afectaría un gasto esencial o un compromiso"])
    })
  ]);

  const CORE_QUESTION_KEYS = Object.freeze(QUESTION_DEFS.filter((question) => question.branch === "core").map((question) => question.key));
  const ECONOMIC_QUESTION_KEYS = Object.freeze(QUESTION_DEFS.filter((question) => question.branch === "economy").map((question) => question.key));
  const RISK_QUESTION_KEYS = Object.freeze(QUESTION_DEFS.filter((question) => question.branch === "risk").map((question) => question.key));
  // Preguntas que se muestran. Las marcadas con asked:false siguen existiendo en el
  // modelo para no romper perfiles guardados, pero ya no se piden: ningún flujo de la
  // app usa esas respuestas.
  const ASKED_QUESTION_KEYS = Object.freeze(QUESTION_DEFS.filter((question) => question.asked !== false).map((question) => question.key));
  const QUESTION_BY_KEY = new Map(QUESTION_DEFS.map((question) => [question.key, question]));
  const PROFILE05_MAPPING = Object.freeze(QUESTION_DEFS.map((question) => Object.freeze({ key: question.key, profile05Path: question.key, legacyKey: question.legacyKey })));
  const AMOUNT_PATHS = new Set(["detalle_economico.importe_objetivo", "detalle_economico.colchon_liquido"]);
  const FLOW_PATHS = new Set(["detalle_economico.ingresos_netos", "detalle_economico.gastos_esenciales"]);
  const AMOUNT_ANSWER_PATHS = new Set([...AMOUNT_PATHS, "saldo_eur", "total_eur"]);
  const LEGACY_ENUMS = Object.freeze({
    knowledge: ["beginner", "some", "experienced", "unknown", "skipped"],
    objective: ["buffer", "understand", "planned_purchase", "unknown", "skipped"],
    horizon: ["lt1", "1-3", "3-5", "gt5", "unknown", "skipped"],
    risk: ["low", "moderate", "high", "unknown", "skipped"]
  });
  const LEGACY_VALUES = Object.freeze({
    objective: { buffer: "Crear un colchón", understand: "Entender opciones", planned_purchase: "Planificar un gasto" },
    horizon: { lt1: "Menos de un año", "1-3": "Entre 1 y 3 años", "3-5": "Entre 3 y 5 años", gt5: "Más de 5 años" },
    knowledge: { beginner: "Estoy empezando", some: "Conozco algunos términos", experienced: "Tengo experiencia" },
    risk: { low: "Prefiero evitar altibajos", moderate: "Aceptaría cambios moderados", high: "Aceptaría variaciones importantes" }
  });

  function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
  }

  function exactKeys(value, keys) {
    if (!isRecord(value)) return false;
    const found = Object.keys(value).sort();
    const expected = [...keys].sort();
    return found.length === expected.length && found.every((key, index) => key === expected[index]);
  }

  function compareDecimal(left, right) {
    const [leftWhole, leftFraction = ""] = left.split(".");
    const [rightWhole, rightFraction = ""] = right.split(".");
    const a = BigInt(leftWhole) * 100n + BigInt(leftFraction.padEnd(2, "0"));
    const b = BigInt(rightWhole) * 100n + BigInt(rightFraction.padEnd(2, "0"));
    return a < b ? -1 : a > b ? 1 : 0;
  }

  function normalizeDecimal(raw, allowComma) {
    if (typeof raw !== "string") return null;
    const trimmed = raw.trim();
    if (!trimmed) return null;
    const decimalText = allowComma && trimmed.includes(",") && !trimmed.includes(".") ? trimmed.replace(",", ".") : trimmed;
    if (!/^(?:\d{1,10})(?:\.\d{1,2})?$/.test(decimalText)) return null;
    const [wholeRaw, fraction] = decimalText.split(".");
    const whole = wholeRaw.replace(/^0+(?=\d)/, "");
    const normalized = fraction === undefined ? whole : `${whole}.${fraction}`;
    if (compareDecimal(normalized, MAX_DECIMAL) > 0) return null;
    return normalized;
  }

  function parseDecimal(raw) {
    return normalizeDecimal(raw, true);
  }

  function makeAnswer(status, value) {
    if (!ANSWER_STATES.has(status)) return null;
    if (status === "declarado") {
      if (value === undefined) return null;
      return { estado: status, valor: value };
    }
    if (value !== undefined) return null;
    return { estado: status };
  }

  function makeRange(raw) {
    const value = parseDecimal(raw);
    return value === null ? null : { min_eur: value, max_eur: value, moneda: "EUR" };
  }

  function makeAmountAnswer(raw) {
    const range = makeRange(raw);
    return range ? makeAnswer("declarado", range) : null;
  }

  function makeFlowAnswer(raw, periodicity = "mensual") {
    const range = makeRange(raw);
    if (!range || !enumValues.periodicity.includes(periodicity)) return null;
    return makeAnswer("declarado", { importe: range, periodicidad: periodicity });
  }

  function makePercentAnswer(raw) {
    const value = parseDecimal(raw);
    if (value === null || compareDecimal(value, MAX_PERCENT) > 0) return null;
    return makeAnswer("declarado", { min_pct: value, max_pct: value });
  }

  function makeLossCapacityAnswer(impact) {
    if (!enumValues.lossImpact.includes(impact)) return null;
    return makeAnswer("declarado", { escenario_id: "caida_100_de_1000", impacto: impact });
  }

  function createEmptyProfile() {
    const blank = () => ({ estado: "sin_preguntar" });
    return {
      version_esquema: PROFILE05_VERSION,
      tipo: "mapa_educativo",
      respuestas: {
        objetivo: blank(),
        horizonte: blank(),
        liquidez: blank(),
        experiencia: blank()
      },
      detalle_economico: {
        importe_objetivo: blank(),
        ingresos_netos: blank(),
        gastos_esenciales: blank(),
        deuda: blank(),
        colchon_liquido: blank(),
        compromisos_proximos: blank()
      },
      riesgo: {
        tolerancia: blank(),
        capacidad_perdidas: blank()
      },
      supuestos_escenario: []
    };
  }

  function pathParts(path) {
    return typeof path === "string" && QUESTION_BY_KEY.has(path) ? path.split(".") : null;
  }

  function getAnswer(profile, path) {
    const parts = pathParts(path);
    if (!parts || !isRecord(profile)) return null;
    let current = profile;
    for (const part of parts) {
      if (!isRecord(current) || !Object.prototype.hasOwnProperty.call(current, part)) return null;
      current = current[part];
    }
    return current;
  }

  function setAnswer(profile, path, answer) {
    const parts = pathParts(path);
    if (!parts || !validateAnswerForPath(path, answer)) return null;
    let current = profile;
    for (const part of parts.slice(0, -1)) current = current[part];
    current[parts[parts.length - 1]] = clone(answer);
    return profile;
  }

  function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
  }

  function validateStatusOnly(answer) {
    return isRecord(answer) && ["no_se", "omitido", "sin_preguntar"].includes(answer.estado) && exactKeys(answer, ["estado"]);
  }

  function validDecimal(value, max = MAX_DECIMAL) {
    if (typeof value !== "string" || !/^(?:0|[1-9]\d{0,9})(?:\.\d{1,2})?$/.test(value)) return false;
    return compareDecimal(value, max) <= 0;
  }

  function validateRange(value) {
    if (!exactKeys(value, ["min_eur", "max_eur", "moneda"]) || value.moneda !== "EUR" || !validDecimal(value.min_eur)) return false;
    if (value.max_eur === null) return true;
    return validDecimal(value.max_eur) && compareDecimal(value.max_eur, value.min_eur) >= 0;
  }

  function validateAmountAnswer(answer) {
    if (validateStatusOnly(answer)) return true;
    return isRecord(answer) && answer.estado === "declarado" && exactKeys(answer, ["estado", "valor"]) && validateRange(answer.valor);
  }

  function validateFlowAnswer(answer) {
    if (validateStatusOnly(answer)) return true;
    if (!isRecord(answer) || answer.estado !== "declarado" || !exactKeys(answer, ["estado", "valor"])) return false;
    const flow = answer.valor;
    return exactKeys(flow, ["importe", "periodicidad"]) && validateRange(flow.importe) && enumValues.periodicity.includes(flow.periodicidad);
  }

  function validPercent(value) {
    return validDecimal(value, MAX_PERCENT);
  }

  function validatePercentAnswer(answer) {
    if (validateStatusOnly(answer)) return true;
    if (!isRecord(answer) || answer.estado !== "declarado" || !exactKeys(answer, ["estado", "valor"])) return false;
    const value = answer.valor;
    return exactKeys(value, ["min_pct", "max_pct"]) && validPercent(value.min_pct) && validPercent(value.max_pct) && compareDecimal(value.max_pct, value.min_pct) >= 0;
  }

  function validateEnumAnswer(answer, values) {
    if (validateStatusOnly(answer)) return true;
    return isRecord(answer) && answer.estado === "declarado" && exactKeys(answer, ["estado", "valor"]) && typeof answer.valor === "string" && values.includes(answer.valor);
  }

  function validateExperienceAnswer(answer) {
    if (validateStatusOnly(answer)) return true;
    if (!isRecord(answer) || answer.estado !== "declarado" || !exactKeys(answer, ["estado", "valor"])) return false;
    const value = answer.valor;
    return exactKeys(value, ["nivel", "temas_interes"]) && enumValues.experience.includes(value.nivel) && Array.isArray(value.temas_interes) && value.temas_interes.length <= 5 && new Set(value.temas_interes).size === value.temas_interes.length && value.temas_interes.every((topic) => enumValues.topics.includes(topic));
  }

  function validateNestedAmount(answer) {
    return validateAmountAnswer(answer);
  }

  function validateNestedFlow(answer) {
    return validateFlowAnswer(answer);
  }

  function validateDebtAnswer(answer) {
    if (validateStatusOnly(answer)) return true;
    if (!isRecord(answer) || answer.estado !== "declarado" || !exactKeys(answer, ["estado", "valor"])) return false;
    const debt = answer.valor;
    if (!isRecord(debt) || typeof debt.situacion !== "string") return false;
    if (debt.situacion === "sin_deuda") return exactKeys(debt, ["situacion"]);
    return debt.situacion === "con_deuda" && exactKeys(debt, ["situacion", "saldo_eur", "cuota", "coste_anual_pct"]) && validateNestedAmount(debt.saldo_eur) && validateNestedFlow(debt.cuota) && validatePercentAnswer(debt.coste_anual_pct);
  }

  function validateCommitmentsAnswer(answer) {
    if (validateStatusOnly(answer)) return true;
    if (!isRecord(answer) || answer.estado !== "declarado" || !exactKeys(answer, ["estado", "valor"])) return false;
    const commitments = answer.valor;
    if (!isRecord(commitments) || typeof commitments.hay_compromiso !== "boolean") return false;
    if (commitments.hay_compromiso === false) return exactKeys(commitments, ["hay_compromiso"]);
    return exactKeys(commitments, ["hay_compromiso", "total_eur", "plazo"]) && validateAmountAnswer(commitments.total_eur) && enumValues.commitmentHorizon.includes(commitments.plazo);
  }

  function validateLossCapacityAnswer(answer) {
    if (validateStatusOnly(answer)) return true;
    if (!isRecord(answer) || answer.estado !== "declarado" || !exactKeys(answer, ["estado", "valor"])) return false;
    const value = answer.valor;
    return exactKeys(value, ["escenario_id", "impacto"]) && value.escenario_id === "caida_100_de_1000" && enumValues.lossImpact.includes(value.impacto);
  }

  function validateAnswerForPath(path, answer) {
    if (!pathParts(path) || !isRecord(answer) || !ANSWER_STATES.has(answer.estado)) return false;
    if (answer.estado !== "declarado") return validateStatusOnly(answer);
    if (!exactKeys(answer, ["estado", "valor"])) return false;
    switch (path) {
      case "respuestas.objetivo": return validateEnumAnswer(answer, enumValues.objective);
      case "respuestas.horizonte": return validateEnumAnswer(answer, enumValues.horizon);
      case "respuestas.liquidez": return validateEnumAnswer(answer, enumValues.liquidity);
      case "respuestas.experiencia": return validateExperienceAnswer(answer);
      case "detalle_economico.importe_objetivo":
      case "detalle_economico.colchon_liquido": return validateAmountAnswer(answer);
      case "detalle_economico.ingresos_netos":
      case "detalle_economico.gastos_esenciales": return validateFlowAnswer(answer);
      case "detalle_economico.deuda": return validateDebtAnswer(answer);
      case "detalle_economico.compromisos_proximos": return validateCommitmentsAnswer(answer);
      case "riesgo.tolerancia": return validateEnumAnswer(answer, enumValues.tolerance);
      case "riesgo.capacidad_perdidas": return validateLossCapacityAnswer(answer);
      default: return false;
    }
  }

  function validateProfile(profile) {
    if (!exactKeys(profile, ["version_esquema", "tipo", "respuestas", "detalle_economico", "riesgo", "supuestos_escenario"])) return false;
    if (profile.version_esquema !== PROFILE05_VERSION || profile.tipo !== "mapa_educativo" || !Array.isArray(profile.supuestos_escenario) || profile.supuestos_escenario.length !== 0) return false;
    if (!exactKeys(profile.respuestas, ["objetivo", "horizonte", "liquidez", "experiencia"])) return false;
    if (!exactKeys(profile.detalle_economico, ["importe_objetivo", "ingresos_netos", "gastos_esenciales", "deuda", "colchon_liquido", "compromisos_proximos"])) return false;
    if (!exactKeys(profile.riesgo, ["tolerancia", "capacidad_perdidas"])) return false;
    return QUESTION_DEFS.every((question) => validateAnswerForPath(question.key, getAnswer(profile, question.key)));
  }

  function validateLegacyAnswers(legacyAnswers) {
    if (legacyAnswers === undefined) return true;
    if (!isRecord(legacyAnswers) || Object.keys(legacyAnswers).some((key) => !["objective", "horizon", "knowledge", "risk"].includes(key))) return false;
    return Object.entries(legacyAnswers).every(([key, value]) => LEGACY_ENUMS[key] && LEGACY_ENUMS[key].includes(value) && !["unknown", "skipped"].includes(value));
  }

  function makeSnapshot(profile, legacyAnswers = {}) {
    if (!validateProfile(profile) || !validateLegacyAnswers(legacyAnswers)) return null;
    const snapshot = { version: SCHEMA_VERSION, profile: clone(profile), legacyAnswers: clone(legacyAnswers) };
    return snapshot;
  }

  function validateSnapshot(snapshot) {
    if (!exactKeys(snapshot, ["version", "profile", "legacyAnswers"]) || snapshot.version !== SCHEMA_VERSION) return null;
    if (!validateProfile(snapshot.profile) || !validateLegacyAnswers(snapshot.legacyAnswers)) return null;
    return makeSnapshot(snapshot.profile, snapshot.legacyAnswers);
  }

  function validLegacyAmount(value) {
    if (typeof value !== "string" || !/^\d{1,10}(?:\.\d{1,2})?$/.test(value)) return false;
    const [whole, fraction = ""] = value.split(".");
    return compareDecimal(`${whole}.${fraction}`, "10000000") <= 0;
  }

  function validateLegacyV1Profile(profile) {
    if (!exactKeys(profile, ["income", "expenses", "knowledge", "objective", "horizon", "risk"])) return false;
    for (const key of ["income", "expenses"]) {
      const value = profile[key];
      if (value !== null && value !== "unknown" && value !== "skipped" && !validLegacyAmount(value)) return false;
    }
    for (const [key, values] of Object.entries(LEGACY_ENUMS)) {
      if (profile[key] !== null && (typeof profile[key] !== "string" || !values.includes(profile[key]))) return false;
    }
    return true;
  }

  function legacyState(value) {
    if (value === null) return { estado: "sin_preguntar" };
    if (value === "unknown") return { estado: "no_se" };
    if (value === "skipped") return { estado: "omitido" };
    return null;
  }

  function migrateLegacySnapshot(input) {
    if (!isRecord(input)) return null;
    let oldProfile;
    if (input.version === 1 && exactKeys(input, ["version", "profile"])) oldProfile = input.profile;
    else if (input.version === undefined) oldProfile = input;
    else return null;
    if (!validateLegacyV1Profile(oldProfile)) return null;

    const profile = createEmptyProfile();
    const legacyAnswers = {};
    const setLegacy = (oldKey, targetPath, mapValue) => {
      const value = oldProfile[oldKey];
      const state = legacyState(value);
      if (state) {
        setAnswer(profile, targetPath, state);
        return;
      }
      const mapped = mapValue(value);
      if (mapped !== null) setAnswer(profile, targetPath, makeAnswer("declarado", mapped));
      else legacyAnswers[oldKey] = value;
    };

    for (const [oldKey, targetPath] of [["income", "detalle_economico.ingresos_netos"], ["expenses", "detalle_economico.gastos_esenciales"]]) {
      const value = oldProfile[oldKey];
      const state = legacyState(value);
      if (state) setAnswer(profile, targetPath, state);
      else setAnswer(profile, targetPath, makeFlowAnswer(value, "mensual"));
    }
    setLegacy("objective", "respuestas.objetivo", (value) => ({ buffer: "colchon_imprevistos", planned_purchase: "gasto_previsto" })[value] || null);
    setLegacy("horizon", "respuestas.horizonte", (value) => ({ "1-3": "1_3_anos", "3-5": "mas_3_anos", gt5: "mas_3_anos" })[value] || null);
    setLegacy("knowledge", "respuestas.experiencia", (value) => value === "beginner" ? { nivel: "empezando", temas_interes: [] } : null);
    setLegacy("risk", "riesgo.tolerancia", () => null);

    const migrated = makeSnapshot(profile, legacyAnswers);
    return migrated;
  }

  function parseStoredValue(raw) {
    if (typeof raw !== "string") return null;
    try { return JSON.parse(raw); } catch (_) { return null; }
  }

  function emptyLoadResult(error = null) {
    return { profile: createEmptyProfile(), legacyAnswers: {}, optedIn: false, migrated: false, error };
  }

  function loadStoredProfile(storage) {
    if (!storage || typeof storage.getItem !== "function") return emptyLoadResult("storage_unavailable");
    let currentRaw;
    try { currentRaw = storage.getItem(STORAGE_KEY); }
    catch (_) { return emptyLoadResult("storage_read_failed"); }
    if (currentRaw !== null) {
      const current = validateSnapshot(parseStoredValue(currentRaw));
      if (current) {
        let error = null;
        try {
          if (LEGACY_STORAGE_KEYS.some((key) => storage.getItem(key) !== null)) error = "legacy_residue";
        } catch (_) { error = "storage_read_failed"; }
        return { profile: current.profile, legacyAnswers: current.legacyAnswers || {}, optedIn: false, hasSavedProfile: true, migrated: false, error };
      }
    }

    let invalidLegacy = currentRaw !== null;
    for (const key of LEGACY_STORAGE_KEYS) {
      let raw;
      try { raw = storage.getItem(key); }
      catch (_) { return emptyLoadResult("storage_read_failed"); }
      if (raw === null) continue;
      const migrated = migrateLegacySnapshot(parseStoredValue(raw));
      if (!migrated) { invalidLegacy = true; continue; }
      return {
        profile: migrated.profile,
        legacyAnswers: migrated.legacyAnswers || {},
        optedIn: false,
        hasSavedProfile: true,
        migrated: true,
        error: null
      };
    }
    return invalidLegacy ? emptyLoadResult("invalid_saved_profile") : emptyLoadResult();
  }

  function saveStoredProfile(storage, profile, legacyAnswers = {}, optedIn = false) {
    if (optedIn !== true) return { ok: false, reason: "opt_in_required" };
    const snapshot = makeSnapshot(profile, legacyAnswers);
    if (!snapshot) return { ok: false, reason: "invalid_profile" };
    if (!storage || typeof storage.setItem !== "function") return { ok: false, reason: "storage_unavailable" };
    try { storage.setItem(STORAGE_KEY, JSON.stringify(snapshot)); }
    catch (_) { return { ok: false, reason: "storage_write_failed" }; }
    let cleanupFailed = false;
    for (const key of LEGACY_STORAGE_KEYS) {
      try { storage.removeItem(key); } catch (_) { cleanupFailed = true; }
    }
    for (const key of LEGACY_STORAGE_KEYS) {
      try { if (typeof storage.getItem !== "function" || storage.getItem(key) !== null) cleanupFailed = true; }
      catch (_) { cleanupFailed = true; }
    }
    return cleanupFailed ? { ok: false, reason: "legacy_cleanup_failed", snapshotWritten: true } : { ok: true, reason: null, snapshotWritten: true };
  }

  function clearStoredProfiles(storage) {
    if (!storage || typeof storage.removeItem !== "function") return { ok: false, removed: [] };
    const removed = [];
    let failed = false;
    for (const key of [STORAGE_KEY, ...LEGACY_STORAGE_KEYS]) {
      try { storage.removeItem(key); removed.push(key); }
      catch (_) { failed = true; }
    }
    for (const key of [STORAGE_KEY, ...LEGACY_STORAGE_KEYS]) {
      try { if (typeof storage.getItem !== "function" || storage.getItem(key) !== null) failed = true; }
      catch (_) { failed = true; }
    }
    return { ok: !failed, removed };
  }

  function findOptionLabel(question, value) {
    if (!question) return null;
    for (const option of question.options || []) if (option.value === value) return option.label;
    for (const option of question.topics || []) if (option.value === value) return option.label;
    return null;
  }

  function formatDecimalEuros(value) {
    if (typeof value !== "string" || !/^(?:0|[1-9]\d{0,9})(?:\.\d{1,2})?$/.test(value)) return "Importe no disponible";
    const [whole, fraction = ""] = value.split(".");
    const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `${grouped},${fraction.padEnd(2, "0")} €`;
  }

  function formatDecimalPercent(value) {
    if (typeof value !== "string" || !/^(?:0|[1-9]\d{0,9})(?:\.\d{1,2})?$/.test(value)) return "Porcentaje no disponible";
    return `${value.replace(".", ",")} %`;
  }

  function formatPercentAnswer(answer) {
    if (!answer || answer.estado !== "declarado") return formatState(answer);
    const range = answer.valor;
    if (range.min_pct === range.max_pct) return formatDecimalPercent(range.min_pct);
    return `${formatDecimalPercent(range.min_pct)}–${formatDecimalPercent(range.max_pct)}`;
  }

  function formatNestedAmount(answer) {
    if (!answer || answer.estado !== "declarado") return formatState(answer);
    const range = answer.valor;
    if (range.max_eur === null) return `Desde ${formatDecimalEuros(range.min_eur)}`;
    if (range.min_eur === range.max_eur) return formatDecimalEuros(range.min_eur);
    return `${formatDecimalEuros(range.min_eur)}–${formatDecimalEuros(range.max_eur)}`;
  }

  function formatState(answer) {
    if (!answer || !answer.estado) return "Sin respuesta";
    if (answer.estado === "no_se") return "No lo sé";
    if (answer.estado === "omitido") return "Omitido";
    if (answer.estado === "sin_preguntar") return "Aún no preguntado";
    return "Declarado";
  }

  function formatAnswer(path, answer) {
    if (!answer || answer.estado !== "declarado") return formatState(answer);
    const question = QUESTION_BY_KEY.get(path);
    if (!question) return "Declarado";
    const value = answer.valor;
    switch (question.kind) {
      case "choice":
        return findOptionLabel(question, value) || "Declarado";
      case "capacity":
        return findOptionLabel(question, value.impacto) || "Declarado";
      case "experience": {
        const level = findOptionLabel(question, value.nivel) || value.nivel;
        const topics = value.temas_interes.map((topic) => findOptionLabel(question, topic)).filter(Boolean);
        return topics.length ? `${level} · Temas: ${topics.join(", ")}` : level;
      }
      case "amount":
        return formatNestedAmount(answer);
      case "flow":
        return `${formatNestedAmount({ estado: "declarado", valor: value.importe })} · ${value.periodicidad}`;
      case "debt":
        if (value.situacion === "sin_deuda") return "No tengo deuda declarada";
        return `Con deuda · saldo: ${formatNestedAmount(value.saldo_eur)} · cuota: ${value.cuota.estado === "declarado" ? `${formatNestedAmount({ estado: "declarado", valor: value.cuota.valor.importe })} / ${value.cuota.valor.periodicidad}` : formatState(value.cuota)} · coste anual: ${formatPercentAnswer(value.coste_anual_pct)}`;
      case "commitments":
        if (value.hay_compromiso === false) return "No preveo un compromiso";
        return `Sí · total: ${formatNestedAmount(value.total_eur)} · plazo: ${({ menos_3_meses: "Menos de 3 meses", "3_6_meses": "3–6 meses", "6_12_meses": "6–12 meses", fecha_no_clara: "Fecha no clara" })[value.plazo]}`;
      default:
        return "Declarado";
    }
  }

  function canContinueAnswer(path, answer) {
    if (!validateAnswerForPath(path, answer)) return false;
    const explicitlyAnswered = (value) => {
      if (value === null || typeof value !== "object") return true;
      if (value.estado === "sin_preguntar") return false;
      return Object.values(value).every(explicitlyAnswered);
    };
    return explicitlyAnswered(answer);
  }

  return Object.freeze({
    SCHEMA_VERSION,
    PROFILE05_VERSION,
    STORAGE_KEY,
    LEGACY_STORAGE_KEYS,
    MAX_DECIMAL,
    QUESTION_DEFS,
    CORE_QUESTION_KEYS,
    ECONOMIC_QUESTION_KEYS,
    RISK_QUESTION_KEYS,
    ASKED_QUESTION_KEYS,
    PROFILE05_MAPPING,
    LEGACY_VALUES,
    enumValues,
    createEmptyProfile,
    parseDecimal,
    makeAnswer,
    makeAmountAnswer,
    makeFlowAnswer,
    makePercentAnswer,
    makeLossCapacityAnswer,
    getAnswer,
    setAnswer,
    formatAnswer,
    validateProfile,
    canContinueAnswer,
    makeSnapshot,
    validateSnapshot,
    migrateLegacySnapshot,
    loadStoredProfile,
    saveStoredProfile,
    clearStoredProfiles
  });
});
