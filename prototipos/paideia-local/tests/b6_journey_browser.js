(async () => {
  const checks = [];
  const ok = (condition, name) => { checks.push({ name, pass: !!condition }); if (!condition) throw new Error(name); };
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const wait = async (fn, label) => { for (let i = 0; i < 250; i += 1) { if (fn()) return; await sleep(20); } throw new Error('timeout: ' + label); };
  const edit = (id, value) => { const input = document.getElementById(id); input.value = value; input.dispatchEvent(new Event('input', { bubbles: true })); };
  const snapshot = () => window.getScenarioComparisonSnapshot();
  const clickText = (root, text) => { const target = [...root.querySelectorAll('button')].find((item) => item.textContent.trim() === text); if (!target) throw new Error('missing button: ' + text); target.click(); return target; };
  const card = (name) => [...document.querySelectorAll('.product-card, .comparison-product')].find((item) => item.querySelector('h3') && item.querySelector('h3').textContent.trim() === name);
  const downloadReport = async () => {
    const host = document.getElementById('scenario-report-host');
    const realCreate = URL.createObjectURL.bind(URL);
    const realClick = HTMLAnchorElement.prototype.click;
    let blob = null;
    URL.createObjectURL = (value) => { blob = value; return realCreate(value); };
    HTMLAnchorElement.prototype.click = function () {};
    try {
      clickText(host, 'Descargar informe (HTML)');
      await wait(() => blob, 'descarga HTML');
      return await blob.text();
    } finally {
      URL.createObjectURL = realCreate;
      HTMLAnchorElement.prototype.click = realClick;
    }
  };
  const originalFetch = window.fetch;
  const calculateBodies = [];
  let chatCalls = 0;
  window.fetch = async (...args) => {
    const url = String(args[0]);
    if (url === '/api/calculate') calculateBodies.push(JSON.parse(args[1].body));
    if (url === '/api/chat') chatCalls += 1;
    return originalFetch(...args);
  };
  try {
    location.hash = '#biblioteca';
    await wait(() => card('Cuenta Contigo') && card('Depósito a 12 meses Self Bank') && card('Depósito Open 6 meses'), 'biblioteca con condiciones');
    clickText(card('Cuenta Contigo'), 'Añadir a comparar');
    clickText(card('Depósito a 12 meses Self Bank'), 'Añadir a comparar');
    clickText(card('Depósito Open 6 meses'), 'Añadir a comparar');
    location.hash = '#comparar';
    await wait(() => document.getElementById('compare-selection') && document.getElementById('compare-selection').textContent.includes('3 de 4'), 'selección de tres');
    clickText(document, 'Comparar metadatos');
    await wait(() => card('Cuenta Contigo') && card('Depósito a 12 meses Self Bank'), 'tarjetas de comparación');
    ok(card('Depósito a 12 meses Self Bank').textContent.includes('fuente secundaria, pendiente de confirmar'), 'Self Bank marcada como secundaria en comparación');
    clickText(card('Cuenta Contigo'), 'Explorar escenarios con esta tasa');
    await wait(() => location.hash === '#escenarios' && document.getElementById('scenario-rate') && snapshot().scenarios[0].source, 'semilla ACC-01');
    const seeded = snapshot().scenarios[0];
    ok(seeded.source.product === 'Cuenta Contigo', 'semilla identifica el producto');
    ok(seeded.source.retrieved_at === '2026-10-26', 'semilla usa la fecha de la condición');
    ok(seeded.source.condition && seeded.source.condition.value === '2.61', 'semilla lleva la condición de tasa');
    ok(seeded.source.condition.effective_to === '2026-11-18', 'semilla lleva la vigencia de la condición');
    ok(seeded.source.url_origin === 'catalogue_record', 'semilla distingue la URL del registro');
    ok(seeded.source.secondary === false, 'ACC-01 no se marca como secundaria');
    const independent = window.getScenarioComparisonSnapshot();
    independent.scenarios[0].source.product = 'MUTADO';
    ok(window.getScenarioComparisonSnapshot().scenarios[0].source.product === 'Cuenta Contigo', 'el snapshot no expone la procedencia por referencia');
    const seededJson = JSON.stringify(seeded.source);
    edit('scenario-principal', '1500');
    ok(JSON.stringify(snapshot().scenarios[0].source) === seededJson, 'editar capital conserva la procedencia');
    edit('scenario-inflation', '1');
    ok(JSON.stringify(snapshot().scenarios[0].source) === seededJson, 'editar inflación conserva la procedencia');
    edit('scenario-contribution', '50');
    ok(JSON.stringify(snapshot().scenarios[0].source) === seededJson, 'editar aportación conserva la procedencia');
    clickText(document, 'Copiar A a B para probar un cambio');
    await sleep(80);
    if (document.body.innerText.includes('sustituir el escenario B')) clickText(document, 'Confirmar sustitución');
    await wait(() => snapshot().scenarios[1].source, 'copia de procedencia A a B');
    ok(snapshot().scenarios[1].source.product === 'Cuenta Contigo', 'copiar A a B conserva producto');
    ok(snapshot().scenarios[1].source.retrieved_at === '2026-10-26', 'copiar A a B conserva fecha');
    ok(JSON.stringify(snapshot().scenarios[1].source) === seededJson, 'copiar A a B conserva condición y tramo');
    const copiedJson = JSON.stringify(snapshot().scenarios[1].source);
    edit('scenario-principal-b', '500');
    ok(JSON.stringify(snapshot().scenarios[1].source) === copiedJson, 'editar capital de B conserva su procedencia');
    document.querySelectorAll('.scenario-form')[0].requestSubmit();
    document.querySelectorAll('.scenario-form')[1].requestSubmit();
    await wait(() => snapshot().scenarios.every((item) => item.status === 'current'), 'cálculo de ambos escenarios');
    ok(calculateBodies.length === 2 && calculateBodies.every((body) => Object.keys(body).sort().join(',') === 'annual_rate_percent,inflation_percent,method,monthly_contribution,principal,years'), 'el cálculo no envía la procedencia ni el perfil');

    const accessor = window.getScenarioComparisonSnapshot;
    window.getScenarioComparisonSnapshot = () => {
      const data = JSON.parse(JSON.stringify(accessor()));
      data.profile = 'SECRET_PROFILE_MARKER';
      data.scenarios[0].profile = 'SECRET_PROFILE_MARKER';
      data.scenarios[0].source.owner_email = 'persona@example.com';
      return data;
    };
    const html = await downloadReport();
    window.getScenarioComparisonSnapshot = accessor;
    ok(/^<!doctype html>/i.test(html), 'el archivo descargado es un documento HTML');
    ok(html.includes('Cuenta Contigo'), 'informe cita el producto');
    ok(html.includes('https://doc.renaultbank.es/'), 'informe cita la URL de la fuente');
    ok(html.includes('consultada 2026-10-26'), 'informe cita la fecha de consulta de la condición');
    ok(html.includes('Condición de la tasa') && html.includes('DOCUMENTED_PROMO_TAE'), 'informe traza tasa y motivo');
    ok(html.includes('Vigencia de la tasa') && html.includes('2026-11-18'), 'informe traza vigencia');
    ok(html.includes('sin plazo documentado con el que compararlo'), 'informe declara la ausencia de plazo sin inventarlo');
    ok(!html.includes('<script'), 'informe sin scripts');
    ok(!html.includes('SECRET_PROFILE_MARKER') && !html.includes('persona@example.com'), 'informe sin perfil ni correo');
    const external = performance.getEntriesByType('resource').map((entry) => entry.name).filter((name) => /^https?:/.test(name) && !name.startsWith(location.origin));
    ok(external.length === 0, 'sin recursos externos en el recorrido');

    location.hash = '#comparar';
    await wait(() => card('Cuenta Contigo'), 'vuelta a comparación');
    clickText(card('Cuenta Contigo'), 'Explorar escenarios con esta tasa');
    await wait(() => location.hash === '#escenarios' && document.getElementById('scenario-rate') && snapshot().scenarios[0].source, 'segunda semilla ACC-01');
    edit('scenario-rate', '2.62');
    ok(snapshot().scenarios[0].source === null, 'cambiar la tasa invalida la procedencia');
    edit('scenario-principal', '900');
    ok(snapshot().scenarios[0].source === null, 'un input distinto no resucita una procedencia invalidada');
    location.hash = '#comparar';
    await wait(() => card('Depósito a 12 meses Self Bank'), 'comparación para cambio de producto');
    clickText(card('Depósito a 12 meses Self Bank'), 'Explorar escenarios con esta tasa');
    await wait(() => location.hash === '#escenarios' && document.getElementById('scenario-rate') && snapshot().scenarios[0].source, 'semilla Self Bank');
    ok(snapshot().scenarios[0].source.product === 'Depósito a 12 meses Self Bank', 'cambiar de producto sustituye la procedencia');
    ok(snapshot().scenarios[0].source.secondary === true, 'la nueva procedencia conserva fuente secundaria');

    location.hash = '#comparar';
    await wait(() => card('Depósito Open 6 meses'), 'comparación para Openbank');
    clickText(card('Depósito Open 6 meses'), 'Explorar escenarios con esta tasa');
    await wait(() => location.hash === '#escenarios' && document.getElementById('scenario-rate') && snapshot().scenarios[0].source && snapshot().scenarios[0].source.term_months === 6, 'semilla DEP-02');
    ok(document.getElementById('main-content').textContent.includes('plazo documentado es de 6 meses'), 'la semilla avisa del plazo documentado');
    document.querySelectorAll('.scenario-form')[0].requestSubmit();
    await wait(() => snapshot().scenarios[0].status === 'current', 'cálculo DEP-02');
    const dep02 = await downloadReport();
    ok(dep02.includes('Depósito Open 6 meses') && dep02.includes('consultada 2026-11-03'), 'informe DEP-02 cita producto y consulta');
    ok(dep02.includes('Plazo documentado del producto</th><td>6 meses'), 'informe DEP-02 traza el plazo documentado');
    ok(dep02.includes('no coincide con el plazo documentado'), 'informe DEP-02 advierte horizonte distinto');
    ok(dep02.includes('Sin domiciliar ingresos') && dep02.includes('3,25 %'), 'informe DEP-02 traza tramo y otros tramos');
    ok(dep02.includes('fuente secundaria, pendiente de confirmar') === false, 'DEP-02 no se etiqueta como secundaria');

    location.hash = '#inicio';
    await wait(() => document.getElementById('chat-consent'), 'chat de inicio');
    ok(document.getElementById('chat-consent').checked === false, 'el consentimiento de privacidad empieza desmarcado');
    const message = document.getElementById('chat-message');
    message.value = '¿Qué es la TAE?';
    message.dispatchEvent(new Event('input', { bubbles: true }));
    clickText(document.getElementById('chat-panel'), 'Enviar pregunta');
    await sleep(80);
    ok(document.getElementById('chat-feedback').textContent.includes('Marca la confirmación de privacidad'), 'sin consentimiento no se envía el chat');
    ok(chatCalls === 0, 'el chat no hizo ninguna petición sin consentimiento');
    return { ok: true, checks, report: html, reportDep02: dep02, calculateBodies, snapshot: snapshot() };
  } catch (error) {
    return { ok: false, error: String(error), checks, calculateBodies };
  } finally {
    window.fetch = originalFetch;
  }
})()
