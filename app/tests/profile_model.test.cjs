"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const Profile = require("../static/profile_model.js");
const profile05SchemaPath = path.join(__dirname, "../../docs/planificacion-03/05-perfil-conversacion/perfil.schema.json");
const profile05Schema = JSON.parse(fs.readFileSync(profile05SchemaPath, "utf8"));

function legacyProfile(overrides = {}) {
  return {
    income: null,
    expenses: null,
    knowledge: null,
    objective: null,
    horizon: null,
    risk: null,
    ...overrides
  };
}

class MemoryStorage {
  constructor(entries = {}) {
    this.values = new Map(Object.entries(entries));
    this.writes = 0;
    this.removals = [];
  }
  getItem(key) { return this.values.has(key) ? this.values.get(key) : null; }
  setItem(key, value) { this.writes += 1; this.values.set(key, String(value)); }
  removeItem(key) { this.removals.push(key); this.values.delete(key); }
}

test("frontend answer paths remain anchored to the existing profile05 schema", () => {
  assert.equal(profile05Schema.$id, "urn:paideia:perfil-educativo:1.0.0");
  for (const { key, profile05Path } of Profile.PROFILE05_MAPPING) {
    assert.equal(key, profile05Path);
    const [section, answer] = profile05Path.split(".");
    assert.ok(profile05Schema.properties[section]?.properties?.[answer], profile05Path);
  }
});

test("blank profile uses the profile05 paths and starts every answer as not asked", () => {
  const profile = Profile.createEmptyProfile();
  assert.equal(Profile.validateProfile(profile), true);
  assert.equal(profile.version_esquema, "1.0.0");
  assert.equal(profile.tipo, "mapa_educativo");
  assert.deepEqual(profile.supuestos_escenario, []);
  for (const { key } of Profile.PROFILE05_MAPPING) {
    assert.deepEqual(Profile.getAnswer(profile, key), { estado: "sin_preguntar" }, key);
  }
});

test("declared zero, unknown, omitted and not-asked remain distinct", () => {
  const profile = Profile.createEmptyProfile();
  Profile.setAnswer(profile, "detalle_economico.colchon_liquido", Profile.makeAmountAnswer("0"));
  Profile.setAnswer(profile, "detalle_economico.importe_objetivo", Profile.makeAnswer("no_se"));
  Profile.setAnswer(profile, "detalle_economico.ingresos_netos", Profile.makeAnswer("omitido"));
  assert.deepEqual(Profile.getAnswer(profile, "detalle_economico.colchon_liquido"), {
    estado: "declarado",
    valor: { min_eur: "0", max_eur: "0", moneda: "EUR" }
  });
  assert.deepEqual(Profile.getAnswer(profile, "detalle_economico.importe_objetivo"), { estado: "no_se" });
  assert.deepEqual(Profile.getAnswer(profile, "detalle_economico.ingresos_netos"), { estado: "omitido" });
  assert.deepEqual(Profile.getAnswer(profile, "detalle_economico.gastos_esenciales"), { estado: "sin_preguntar" });
  assert.equal(Profile.validateProfile(profile), true);
});

test("decimal inputs stay strings and accept the configured inclusive boundary", () => {
  assert.equal(Profile.parseDecimal("0"), "0");
  assert.equal(Profile.parseDecimal("0,50"), "0.50");
  assert.equal(Profile.parseDecimal("00012.30"), "12.30");
  assert.equal(Profile.parseDecimal("9999999999.99"), "9999999999.99");
  assert.equal(Profile.parseDecimal("10000000000"), null);
  assert.equal(Profile.parseDecimal("-0.01"), null);
  assert.equal(Profile.parseDecimal("1.234"), null);
  assert.equal(Profile.parseDecimal("1e3"), null);
  assert.equal(Profile.parseDecimal("Infinity"), null);
  assert.equal(Profile.parseDecimal(""), null);
  assert.equal(typeof Profile.makeAmountAnswer("0.10").valor.min_eur, "string");
});

test("flow amounts retain the declared monthly periodicity and exact decimal text", () => {
  const answer = Profile.makeFlowAnswer("1234.50", "mensual");
  assert.deepEqual(answer, {
    estado: "declarado",
    valor: {
      importe: { min_eur: "1234.50", max_eur: "1234.50", moneda: "EUR" },
      periodicidad: "mensual"
    }
  });
  assert.equal(Profile.validateProfile(Profile.setAnswer(Profile.createEmptyProfile(), "detalle_economico.ingresos_netos", answer)), true);
});

test("debt subanswers retain independent zero, unknown and omitted states", () => {
  const profile = Profile.createEmptyProfile();
  const debt = Profile.makeAnswer("declarado", {
    situacion: "con_deuda",
    saldo_eur: Profile.makeAmountAnswer("0"),
    cuota: Profile.makeAnswer("no_se"),
    coste_anual_pct: Profile.makeAnswer("omitido")
  });
  assert.ok(Profile.setAnswer(profile, "detalle_economico.deuda", debt));
  assert.deepEqual(Profile.getAnswer(profile, "detalle_economico.deuda"), debt);
  assert.equal(Profile.validateProfile(profile), true);
  assert.equal(Profile.makePercentAnswer("100").valor.max_pct, "100");
  assert.equal(Profile.makePercentAnswer("100.01"), null);
});

test("no-debt, no commitment and distinct risk answers use profile05 values", () => {
  const profile = Profile.createEmptyProfile();
  Profile.setAnswer(profile, "detalle_economico.deuda", Profile.makeAnswer("declarado", { situacion: "sin_deuda" }));
  Profile.setAnswer(profile, "detalle_economico.compromisos_proximos", Profile.makeAnswer("declarado", { hay_compromiso: false }));
  Profile.setAnswer(profile, "riesgo.tolerancia", Profile.makeAnswer("declarado", "preferiria_salir"));
  const lossAnswer = Profile.makeLossCapacityAnswer("afectaria_gasto_esencial_o_compromiso");
  assert.deepEqual(lossAnswer, Profile.makeAnswer("declarado", {
    escenario_id: "caida_100_de_1000",
    impacto: "afectaria_gasto_esencial_o_compromiso"
  }));
  assert.equal(Profile.makeLossCapacityAnswer("invalid"), null);
  Profile.setAnswer(profile, "riesgo.capacidad_perdidas", lossAnswer);
  assert.equal(Profile.validateProfile(profile), true);
  assert.deepEqual(Profile.getAnswer(profile, "detalle_economico.deuda").valor, { situacion: "sin_deuda" });
  assert.equal(Profile.getAnswer(profile, "riesgo.tolerancia").valor, "preferiria_salir");
  assert.equal(Profile.getAnswer(profile, "riesgo.capacidad_perdidas").valor.impacto, "afectaria_gasto_esencial_o_compromiso");
  assert.equal(Profile.formatAnswer("riesgo.capacidad_perdidas", lossAnswer), "Afectaría un gasto esencial o un compromiso");
  const invalid = structuredClone(profile);
  invalid.detalle_economico.compromisos_proximos = Profile.makeAnswer("declarado", {
    hay_compromiso: true,
    total_eur: Profile.makeAmountAnswer("10"),
    plazo: "un_ano"
  });
  assert.equal(Profile.validateProfile(invalid), false);
});

test("profile and snapshot validators reject malformed, extra and numeric-decimal values", () => {
  const profile = Profile.createEmptyProfile();
  const badNumber = structuredClone(profile);
  badNumber.detalle_economico.colchon_liquido = {
    estado: "declarado",
    valor: { min_eur: 0, max_eur: 0, moneda: "EUR" }
  };
  assert.equal(Profile.validateProfile(badNumber), false);
  const extra = structuredClone(profile);
  extra.personal = "synthetic-only";
  assert.equal(Profile.validateProfile(extra), false);
  const snapshot = Profile.makeSnapshot(profile);
  assert.equal(snapshot.version, 2);
  assert.ok(Profile.validateSnapshot(snapshot));
  assert.equal(Profile.validateSnapshot({ ...snapshot, version: 1 }), null);
  assert.equal(Profile.validateSnapshot({ ...snapshot, extra: true }), null);
});

test("v1 migration preserves exact compatible answers and leaves added fields unanswered", () => {
  const old = {
    version: 1,
    profile: legacyProfile({
      income: "0.00",
      expenses: "1200.25",
      knowledge: "beginner",
      objective: "planned_purchase",
      horizon: "1-3",
      risk: "unknown"
    })
  };
  const migrated = Profile.migrateLegacySnapshot(old);
  assert.ok(migrated);
  assert.equal(migrated.version, 2);
  assert.deepEqual(Profile.getAnswer(migrated.profile, "detalle_economico.ingresos_netos"), {
    estado: "declarado",
    valor: { importe: { min_eur: "0.00", max_eur: "0.00", moneda: "EUR" }, periodicidad: "mensual" }
  });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "detalle_economico.gastos_esenciales").valor.importe, {
    min_eur: "1200.25", max_eur: "1200.25", moneda: "EUR"
  });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "respuestas.objetivo"), { estado: "declarado", valor: "gasto_previsto" });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "respuestas.horizonte"), { estado: "declarado", valor: "1_3_anos" });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "respuestas.experiencia"), {
    estado: "declarado", valor: { nivel: "empezando", temas_interes: [] }
  });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "riesgo.tolerancia"), { estado: "no_se" });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "riesgo.capacidad_perdidas"), { estado: "sin_preguntar" });
  assert.deepEqual(migrated.legacyAnswers, {});
});

test("v1 migration keeps ambiguous legacy choices instead of guessing a new answer", () => {
  const migrated = Profile.migrateLegacySnapshot({
    version: 1,
    profile: legacyProfile({ objective: "understand", horizon: "lt1", knowledge: "experienced", risk: "high" })
  });
  assert.ok(migrated);
  assert.deepEqual(Profile.getAnswer(migrated.profile, "respuestas.objetivo"), { estado: "sin_preguntar" });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "respuestas.horizonte"), { estado: "sin_preguntar" });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "respuestas.experiencia"), { estado: "sin_preguntar" });
  assert.deepEqual(Profile.getAnswer(migrated.profile, "riesgo.tolerancia"), { estado: "sin_preguntar" });
  assert.deepEqual(migrated.legacyAnswers, {
    objective: "understand", horizon: "lt1", knowledge: "experienced", risk: "high"
  });
});

test("reload after failed deletion keeps the copy but never restores permission", () => {
  const storage = new MemoryStorage();
  const profile = Profile.createEmptyProfile();
  assert.equal(Profile.saveStoredProfile(storage, profile, {}, true).ok, true);
  const saved = storage.getItem(Profile.STORAGE_KEY);
  storage.removeItem = () => { throw new Error("synthetic denial"); };
  assert.equal(Profile.clearStoredProfiles(storage).ok, false);
  const writes = storage.writes;
  const loaded = Profile.loadStoredProfile(storage);
  assert.equal(loaded.optedIn, false);
  assert.equal(loaded.hasSavedProfile, true);
  assert.equal(storage.getItem(Profile.STORAGE_KEY), saved);
  assert.equal(storage.writes, writes);
});

// Migration contract: legacy copies are converted in memory only; a new session requires explicit save.
test("migration from an existing saved v1 snapshot is read-only until explicit save", () => {
  const legacyKey = Profile.LEGACY_STORAGE_KEYS[0];
  const storage = new MemoryStorage({
    [legacyKey]: JSON.stringify({ version: 1, profile: legacyProfile({ income: "0" }) })
  });
  const loaded = Profile.loadStoredProfile(storage);
  assert.equal(loaded.optedIn, false);
  assert.equal(loaded.hasSavedProfile, true);
  assert.equal(loaded.migrated, true);
  assert.deepEqual(Profile.getAnswer(loaded.profile, "detalle_economico.ingresos_netos").valor.importe.min_eur, "0");
  assert.equal(storage.getItem(Profile.STORAGE_KEY), null);
  assert.ok(storage.getItem(legacyKey));
  assert.equal(storage.writes, 0);
  assert.deepEqual(storage.removals, []);
  assert.equal(Profile.saveStoredProfile(storage, loaded.profile, loaded.legacyAnswers, true).ok, true);
  assert.ok(storage.getItem(Profile.STORAGE_KEY));
  assert.ok(storage.removals.includes(legacyKey));
});

test("empty storage and persistence-off do not create a saved profile or consent", () => {
  const storage = new MemoryStorage();
  const loaded = Profile.loadStoredProfile(storage);
  assert.equal(loaded.optedIn, false);
  assert.equal(loaded.migrated, false);
  const result = Profile.saveStoredProfile(storage, Profile.createEmptyProfile(), {}, false);
  assert.deepEqual(result, { ok: false, reason: "opt_in_required" });
  assert.equal(storage.writes, 0);
  assert.equal(storage.getItem(Profile.STORAGE_KEY), null);
});

test("saved profile deletion clears the current and every supported legacy format", () => {
  const entries = { [Profile.STORAGE_KEY]: "v2" };
  Profile.LEGACY_STORAGE_KEYS.forEach((key) => { entries[key] = "legacy"; });
  const storage = new MemoryStorage(entries);
  const result = Profile.clearStoredProfiles(storage);
  assert.equal(result.ok, true);
  assert.equal(storage.getItem(Profile.STORAGE_KEY), null);
  for (const key of Profile.LEGACY_STORAGE_KEYS) assert.equal(storage.getItem(key), null);
  assert.deepEqual(storage.removals.sort(), [Profile.STORAGE_KEY, ...Profile.LEGACY_STORAGE_KEYS].sort());
});
