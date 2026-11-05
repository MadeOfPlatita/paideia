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
    await wait(() => card('Cuenta Contigo') && document.querySelector('#catalogue-results .error-note'), 'biblioteca con condiciones fallando');
    const catalogueError = document.querySelector('#catalogue-results .error-note');
    ok(catalogueError.textContent.includes('No se pudieron cargar las condiciones documentadas'), 'la biblioteca explica el fallo de condiciones');
    ok(catalogueError.textContent.includes('no equivale a falta de dato'), 'el fallo no se confunde con ausencia de tasa');
    ok(catalogueError.textContent.includes('Intentar de nuevo'), 'la biblioteca ofrece reintento');
    ok(!document.getElementById('catalogue-results').textContent.includes('Sin tasa documentada para este producto.'), 'no se afirma falta de tasa durante el fallo');
    ok(card('Cuenta Contigo').textContent.includes('No se pudieron cargar las condiciones documentadas'), 'la ficha tampoco presenta el fallo como falta de tasa');
    ok(!card('Cuenta Contigo').textContent.includes('TAE documentada'), 'no se inventa una tasa durante el fallo');
    const requestsBefore = conditionRequests;
    failConditions = false;
    clickText(catalogueError, 'Intentar de nuevo');
    await wait(() => card('Cuenta Contigo') && card('Cuenta Contigo').textContent.includes('TAE documentada: 2,61 %'), 'recuperación de condiciones');
    ok(conditionRequests === requestsBefore + 1, 'el reintento consulta condiciones una sola vez');
    ok(!document.querySelector('#catalogue-results .error-note'), 'el error desaparece al recuperar');

    clickText(card('Cuenta Contigo'), 'Añadir a comparar');
    clickText(card('Depósito Open 6 meses'), 'Añadir a comparar');
    location.hash = '#comparar';
    await wait(() => document.getElementById('compare-selection') && document.getElementById('compare-selection').textContent.includes('2 de 4'), 'selección de dos');
    clickText(document, 'Comparar metadatos');
    await wait(() => card('Cuenta Contigo') && card('Depósito Open 6 meses'), 'tarjetas de comparación');
    const comparison = document.getElementById('compare-result').textContent;
    ok(comparison.includes('TAE documentada: 2,61 %'), 'la tasa documentada se muestra en el comparador');
    ok(!comparison.includes('no se muestran tasas'), 'el comparador no contradice las tasas mostradas');
    ok(!comparison.includes('no se muestran tasas, NAV ni ceros'), 'el aviso antiguo contradictorio no permanece');
    const acc = card('Cuenta Contigo');
    ok(/consulta de la condición/i.test(acc.textContent), 'la tarjeta distingue la fecha de consulta');
    ok(acc.textContent.includes('2026-10-26'), 'la tarjeta usa retrieved_at de la condición');
    ok(acc.textContent.includes('Vigencia de la condición'), 'la tarjeta muestra la vigencia');
    ok(acc.textContent.includes('2026-11-18'), 'la tarjeta cita la fecha de fin real');
    ok(acc.textContent.includes('Fecha efectiva del producto'), 'la tarjeta distingue la fecha efectiva del producto');
    ok(acc.textContent.includes('No consta una fecha efectiva del producto'), 'un as_of nulo no oculta la fecha de consulta');
    ok(!acc.textContent.includes('Fecha asociada'), 'no se mezclan consulta y fecha efectiva bajo una etiqueta ambigua');
    return { ok: true, checks, conditionRequests, comparisonText: comparison, accCard: acc.textContent };
  } catch (error) {
    return { ok: false, error: String(error), checks, conditionRequests };
  } finally {
    window.fetch = originalFetch;
  }
})()
