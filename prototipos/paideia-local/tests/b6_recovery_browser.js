(async () => {
  const checks = [];
  const ok = (condition, name) => { checks.push({ name, pass: !!condition }); if (!condition) throw new Error(name); };
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const wait = async (fn, label) => { for (let i = 0; i < 300; i += 1) { if (fn()) return; await sleep(20); } throw new Error('timeout: ' + label); };
  const card = (name) => [...document.querySelectorAll('.product-card, .comparison-product')].find((item) => item.querySelector('h3') && item.querySelector('h3').textContent.trim() === name);
  const clickText = (root, text) => { const target = [...root.querySelectorAll('button')].find((item) => item.textContent.trim() === text); if (!target) throw new Error('missing button: ' + text); target.click(); return target; };
  const originalFetch = window.fetch;
  let failConditions = true;
  let conditionRequests = 0;
  window.fetch = async (...args) => {
    if (String(args[0]) === '/api/conditions') {
      conditionRequests += 1;
      if (failConditions) {
        return new Response(JSON.stringify({ error: { code: 'CONDITIONS_UNAVAILABLE', message: 'Fallo local forzado de condiciones.', retryable: true } }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }
    return originalFetch(...args);
  };
  try {
    location.hash = '#biblioteca';
    await wait(() => card('Cuenta Contigo') && card('Cuenta corriente remunerada'), 'biblioteca con API de condiciones fallando');
    clickText(card('Cuenta Contigo'), 'Añadir a comparar');
    clickText(card('Cuenta corriente remunerada'), 'Añadir a comparar');
    location.hash = '#comparar';
    await wait(() => document.getElementById('compare-selection') && document.getElementById('compare-selection').textContent.includes('2 de 4'), 'selección');
    clickText(document, 'Comparar metadatos');
    await wait(() => document.querySelector('#compare-result .error-note'), 'error de condiciones visible');
    const box = document.querySelector('#compare-result .error-note');
    ok(box.textContent.includes('No se pudieron cargar las condiciones documentadas'), 'el fallo se explica como fallo');
    ok(box.textContent.includes('un fallo de carga no equivale a falta de dato'), 'el fallo no se confunde con falta de dato');
    ok(box.textContent.includes('Intentar de nuevo'), 'hay reintento manual');
    ok(document.querySelectorAll('.comparison-product').length === 0, 'no se pintan tarjetas con tasas ausentes por el fallo');
    const before = conditionRequests;
    failConditions = false;
    clickText(box, 'Intentar de nuevo');
    await wait(() => document.querySelectorAll('.comparison-product').length === 2, 'recuperación tras reintento');
    ok(conditionRequests === before + 1, 'el reintento vuelve a pedir condiciones una vez');
    ok(!document.querySelector('#compare-result .error-note'), 'el error desaparece tras recuperar');
    ok(document.querySelector('#compare-result').textContent.includes('TAE documentada: 2,61 %'), 'la tasa real aparece tras recuperar');
    return { ok: true, checks, conditionRequests };
  } catch (error) {
    return { ok: false, error: String(error), checks, conditionRequests };
  } finally {
    window.fetch = originalFetch;
  }
})()
