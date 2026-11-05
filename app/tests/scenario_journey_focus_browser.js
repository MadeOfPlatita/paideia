(async () => {
  const checks = [];
  const check = (pass, name, details = {}) => checks.push({name, pass: !!pass, ...details});
  const originalFetch = window.fetch;
  let calls = 0;
  window.fetch = (...args) => { calls++; return originalFetch(...args); };
  try {
    const before = JSON.stringify(window.getScenarioComparisonSnapshot());
    const hash = location.hash;
    for (const [label, id] of [['Empezar/ajustar','scenario-start'], ['Comparar/entender','scenario-comparison-summary'], ['Guardar','scenario-report-host']]) {
      const link = [...document.querySelectorAll('nav[aria-label="Recorrido de escenarios"] a')].find(a => a.textContent.trim() === label);
      const target = document.getElementById(id);
      if (link) link.click();
      check(!!link && !!target && document.activeElement === target, `foco ${label}`, {active: document.activeElement?.id || document.activeElement?.tagName});
      check(location.hash === hash && hash === '#escenarios', `ruta ${label}`);
      check(JSON.stringify(window.getScenarioComparisonSnapshot()) === before && calls === 0, `sin cambios ni solicitudes ${label}`);
    }
    return {ok: checks.every(c => c.pass), checks, viewport: {client:document.documentElement.clientWidth, scroll:document.documentElement.scrollWidth, inner:innerWidth}};
  } catch (error) { return {ok:false, checks, error:String(error)}; }
  finally { window.fetch = originalFetch; }
})()