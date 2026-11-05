(async () => {
  const checks = [];
  const ok = (condition, name) => { checks.push({ name, pass: !!condition }); if (!condition) throw new Error(name); };
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const wait = async (fn, label) => { for (let i = 0; i < 300; i += 1) { if (fn()) return; await sleep(20); } throw new Error('timeout: ' + label); };
  const card = (name) => [...document.querySelectorAll('.product-card, .comparison-product')].find((item) => item.querySelector('h3') && item.querySelector('h3').textContent.trim() === name);
  const clickText = (root, text) => { const target = [...root.querySelectorAll('button')].find((item) => item.textContent.trim() === text); if (!target) throw new Error('missing button: ' + text); target.click(); return target; };
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const response = await originalFetch(...args);
    if (String(args[0]) !== '/api/conditions') return response;
    const data = await response.clone().json();
    const acc = data.products.find((product) => product.product_id === 'ACC-01');
    const rate = acc.conditions.find((condition) => condition.metric === 'annual_rate_percent');
    rate.value = '';
    rate.notes = [];
    return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
  };
  try {
    location.hash = '#biblioteca';
    await wait(() => card('Cuenta Contigo') && card('Depósito Open 6 meses'), 'biblioteca');
    const accText = card('Cuenta Contigo').textContent;
    ok(accText.includes('no trae una cifra de tasa utilizable'), 'la tasa vacía se declara no utilizable');
    ok(!accText.includes('0,00 %'), 'la tasa vacía no se pinta como 0 %');
    ok(card('Depósito Open 6 meses').textContent.includes('TAE documentada: 2,75 %'), 'las demás tasas siguen mostrándose');
    clickText(card('Cuenta Contigo'), 'Ver detalle');
    await wait(() => document.getElementById('product-detail').textContent.includes('Tasa anual (TAE)'), 'detalle de ACC-01');
    const detail = document.getElementById('product-detail').textContent;
    ok(detail.includes('No disponible TAE'), 'el detalle no convierte la tasa vacía en cero');
    ok(!detail.includes('0,00 %'), 'el detalle no muestra 0 %');
    ok(![...document.querySelectorAll('#product-detail button')].some((item) => item.textContent.trim() === 'Explorar escenarios con esta tasa'), 'sin cifra utilizable no se ofrece sembrar un escenario');
    return { ok: true, checks };
  } catch (error) {
    return { ok: false, error: String(error), checks };
  } finally {
    window.fetch = originalFetch;
  }
})()
