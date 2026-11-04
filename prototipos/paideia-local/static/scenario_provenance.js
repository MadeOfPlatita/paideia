/* Procedencia local de una tasa documentada: construye una copia explícita y sin campos ajenos. */
(function (root) {
  'use strict';
  const RATE = 'annual_rate_percent';
  const TERM = 'term_months';
  const RATE_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;
  const URL_HTTPS = /^https:\/\/[^\s<>"']+$/;

  function text(value, max) {
    return typeof value === 'string' ? value.trim().slice(0, max) : '';
  }
  function date(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return '';
    const [year, month, day] = value.split('-').map(Number);
    if (year < 1900 || year > 2100 || month < 1 || month > 12 || day < 1) return '';
    return day <= new Date(Date.UTC(year, month, 0)).getUTCDate() ? value : '';
  }
  function url(value) {
    return typeof value === 'string' && value.length <= 2048 && URL_HTTPS.test(value) ? value : '';
  }
  function rateText(value) {
    if (typeof value === 'number') return Number.isFinite(value) ? String(value) : '';
    if (typeof value !== 'string') return '';
    const trimmed = value.trim();
    return RATE_PATTERN.test(trimmed) ? trimmed : '';
  }
  function rateNumber(value) {
    const normalized = rateText(value);
    if (!normalized) return null;
    const number = Number(normalized);
    return Number.isFinite(number) ? number : null;
  }
  function conditionView(condition) {
    if (!condition || typeof condition !== 'object') return null;
    const value = rateText(condition.value);
    return {
      metric: text(condition.metric, 40),
      value: value === '' ? null : value,
      state: text(condition.state, 20),
      reason: text(condition.reason, 80),
      effective_from: date(condition.effective_from),
      effective_to: date(condition.effective_to),
      retrieved_at: date(condition.retrieved_at)
    };
  }
  function tierView(tier, index, selectedCondition) {
    if (!tier || typeof tier !== 'object') return null;
    const condition = text(tier.condition, 60);
    return {
      label: text(tier.condition_label || tier.condition || tier.label, 180),
      condition,
      tae: rateText(tier.tae),
      tin: rateText(tier.tin),
      selected: Boolean(selectedCondition && condition === selectedCondition) || (!selectedCondition && index === 0)
    };
  }
  function buildSource(options) {
    const input = options && typeof options === 'object' ? options : {};
    const product = input.product && typeof input.product === 'object' ? input.product : {};
    const entry = input.conditionEntry && typeof input.conditionEntry === 'object' ? input.conditionEntry : {};
    const condition = input.rateCondition && typeof input.rateCondition === 'object' ? input.rateCondition : null;
    const term = input.termCondition && typeof input.termCondition === 'object' ? input.termCondition : null;
    const entrySource = entry.source && typeof entry.source === 'object' ? entry.source : null;
    const conditionUrl = entrySource ? url(entrySource.url) : '';
    const catalogueUrl = url(product.primary_url);
    const kind = entrySource ? text(entrySource.kind, 40) : '';
    const notes = condition && Array.isArray(condition.notes) ? condition.notes.map((note) => text(note, 200)) : [];
    const secondary = Boolean((kind && kind !== 'official') || notes.some((note) => /fuente secundaria/i.test(note)));
    const tiers = Array.isArray(entry.rate_tiers)
      ? entry.rate_tiers.slice(0, 8).map((tier, index) => tierView(tier, index, null)).filter(Boolean)
      : [];
    const selectedTier = Array.isArray(entry.rate_tiers)
      ? entry.rate_tiers.find((tier) => tier && tier.condition === 'sin_requisito') || entry.rate_tiers[0] || null
      : null;
    const selectedCondition = selectedTier ? text(selectedTier.condition, 60) : '';
    const selectedLabel = selectedTier ? text(selectedTier.condition_label || selectedTier.condition, 180) : '';
    for (const tier of tiers) tier.selected = Boolean(selectedCondition && tier.condition === selectedCondition);
    const termValue = term && term.state === 'known' ? Number(term.value) : NaN;
    const source = {
      product: text(product.name, 160),
      product_id: text(product.id, 80),
      url: conditionUrl || catalogueUrl,
      url_origin: conditionUrl ? 'condition_source' : (catalogueUrl ? 'catalogue_record' : ''),
      retrieved_at: date(condition && condition.retrieved_at) || date(entrySource && entrySource.retrieved_at),
      kind,
      secondary,
      document_date: entrySource ? date(entrySource.document_date) : '',
      condition: conditionView(condition),
      selected_tier: selectedLabel,
      selected_condition: selectedCondition,
      tiers,
      term_months: Number.isInteger(termValue) && termValue >= 1 && termValue <= 120 ? termValue : null,
      rate_at_seed: rateText(input.rate !== undefined ? input.rate : condition && condition.value)
    };
    if (!source.product && !source.url && !source.retrieved_at) return null;
    return source;
  }
  function sourceAfterEdit(source, form) {
    if (!source || typeof source !== 'object') return null;
    const pinned = source.rate_at_seed !== undefined && source.rate_at_seed !== null && source.rate_at_seed !== ''
      ? source.rate_at_seed
      : (source.condition && source.condition.value);
    const current = form && typeof form === 'object' ? form.annual_rate_percent : undefined;
    const pinnedNumber = rateNumber(pinned);
    const currentNumber = rateNumber(current);
    if (pinnedNumber === null || currentNumber === null) return null;
    return pinnedNumber === currentNumber ? source : null;
  }
  function copySource(source) {
    if (!source || typeof source !== 'object') return null;
    return JSON.parse(JSON.stringify(source));
  }
  const api = { buildSource, sourceAfterEdit, copySource, RATE, TERM };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.PaideiaScenarioProvenance = api;
})(typeof window === 'undefined' ? null : window);
