/* Estado de carga de /api/conditions: distingue un fallo de una ausencia de dato. */
(function (root) {
  'use strict';
  const RATE = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;

  function emptyState(loading, error) {
    return { loaded: false, loading: Boolean(loading), error: error || null, byId: new Map(), referenceDate: null };
  }
  function begin() {
    return emptyState(true, null);
  }
  function fail(error) {
    return emptyState(false, error || new Error('No se pudieron cargar las condiciones documentadas.'));
  }
  function succeed(data) {
    if (!data || !Array.isArray(data.products)) throw new Error('invalid conditions');
    const byId = new Map();
    for (const product of data.products) {
      if (product && typeof product.product_id === 'string') byId.set(product.product_id, product);
    }
    return {
      loaded: true,
      loading: false,
      error: null,
      byId,
      referenceDate: typeof data.reference_date === 'string' ? data.reference_date : null
    };
  }
  function catalogueNotice(state) {
    if (!state || state.error) {
      return {
        kind: 'error',
        retry: true,
        message: 'No se pudieron cargar las condiciones documentadas. Sin ellas no consta que falte una tasa: un fallo de carga no equivale a falta de dato.'
      };
    }
    if (!state.loaded) {
      return { kind: 'loading', retry: false, message: 'Cargando condiciones documentadas…' };
    }
    return null;
  }
  function comparisonNotice(state) {
    if (!state || state.error) {
      return {
        kind: 'error',
        retry: true,
        message: 'No se pudieron cargar las condiciones documentadas. Las tasas no se muestran porque un fallo de carga no equivale a falta de dato.'
      };
    }
    if (!state.loaded) {
      return { kind: 'loading', retry: false, message: 'Cargando condiciones documentadas…' };
    }
    return null;
  }
  function rateText(value) {
    if (typeof value === 'number') return Number.isFinite(value) ? String(value) : '';
    if (typeof value !== 'string') return '';
    const trimmed = value.trim();
    return RATE.test(trimmed) ? trimmed : '';
  }
  function formatRate(value) {
    const text = rateText(value);
    if (!text) return '';
    const number = Number(text);
    if (!Number.isFinite(number)) return '';
    return number.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' %';
  }
  function rateSummary(state, condition) {
    const notice = catalogueNotice(state);
    if (notice) return { kind: notice.kind, text: notice.message, retry: notice.retry };
    if (!condition) return { kind: 'missing', text: 'Sin tasa documentada para este producto.', retry: false };
    if (condition.state === 'known') {
      const formatted = formatRate(condition.value);
      if (!formatted) {
        return {
          kind: 'missing',
          retry: false,
          text: 'La condición consta como documentada, pero no trae una cifra de tasa utilizable; no se representa como 0 %.'
        };
      }
      const secondary = Array.isArray(condition.notes)
        && condition.notes.some((note) => typeof note === 'string' && /fuente secundaria/i.test(note));
      return {
        kind: 'verified',
        retry: false,
        text: `TAE documentada: ${formatted}${secondary ? ' · fuente secundaria, pendiente de confirmar' : ''}`
      };
    }
    if (condition.state === 'stale') return { kind: 'stale', retry: false, text: 'Oferta vencida: no se muestra como tasa vigente.' };
    if (condition.state === 'conflict') return { kind: 'conflict', retry: false, text: 'Tasas en conflicto entre fuentes: no se comparan.' };
    return { kind: 'missing', retry: false, text: 'Sin tasa documentada para este producto.' };
  }
  const api = { begin, fail, succeed, catalogueNotice, comparisonNotice, formatRate, rateSummary };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.PaideiaConditionsLoad = api;
})(typeof window === 'undefined' ? null : window);
