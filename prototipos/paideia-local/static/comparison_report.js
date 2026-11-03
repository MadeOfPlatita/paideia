/* Informe local: solo consume el contrato público; no calcula escenarios. */
(function (root) {
  'use strict';
  const money = /^-?(?:0|[1-9]\d*)\.\d{2}$/;
  const decimal = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;
  const keys = ['final_balance', 'inflation_adjusted', 'contributions', 'interest'];
  const labels = ['Saldo nominal', 'Saldo real', 'Aportaciones totales', 'Interés'];
  function cents(s) { if (typeof s !== 'string' || !money.test(s) || s.length > 200) throw Error('Importe inválido'); return BigInt(s.replace('.', '')); }
  function subtractMoney(b, a) { const n = cents(b) - cents(a); const abs = n < 0n ? -n : n; return (n < 0n ? '-' : '') + String(abs / 100n) + '.' + String(abs % 100n).padStart(2, '0'); }
  function equivalent(a, b) {
    if (typeof a !== 'string' || typeof b !== 'string' || a.length > 32 || b.length > 32 || !decimal.test(a) || !decimal.test(b)) return false;
    const canonical = s => { const neg = s[0] === '-'; if (neg) s = s.slice(1); let [i, f = ''] = s.split('.'); f = f.replace(/0+$/, ''); return (neg && (i !== '0' || f) ? '-' : '') + i + (f ? '.' + f : ''); };
    return canonical(a) === canonical(b);
  }
  function capture(snapshot) {
    if (!snapshot || snapshot.schema !== 'paideia.scenario-comparison' || snapshot.schema_version !== 1 || !Array.isArray(snapshot.scenarios) || snapshot.scenarios.length !== 2) throw Error('Comparación no disponible.');
    return snapshot.scenarios.map((s, idx) => {
      if (!s || s.id !== ['A','B'][idx] || !Number.isSafeInteger(s.version) || s.version < 0) throw Error('Comparación no disponible.');
      if (s.status !== 'current') {
        const messages = {dirty:'tiene cambios sin calcular',pending:'se está calculando',error:'tuvo un error; vuelve a calcularlo'};
        throw Error('Escenario '+s.id+' '+(messages[s.status] || 'no está disponible')+'. Ambos deben estar actualizados.');
      }
      const i = s.inputs, r = s.result, a = r && r.assumptions;
      if (!i || !r || !a || r.hypothetical !== true || r.not_prediction !== true || r.currency !== 'EUR' || a.taxes_included !== false || a.fees_included !== false) throw Error('Respuesta del motor incompatible.');
      if (typeof i.years !== 'string' || !i.years.trim() || !Number.isInteger(Number(i.years)) || Number(i.years) < 1 || Number(i.years) > 40 || a.years !== Number(i.years) || !['simple','compound'].includes(i.method) || a.method !== i.method) throw Error('Los supuestos no coinciden.');
      for (const k of ['principal','annual_rate_percent','monthly_contribution','inflation_percent']) if (!equivalent(i[k], a[k])) throw Error('Los supuestos no coinciden.');
      const amountValid = x => /^(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?$/.test(x) && Number(x) <= 1000000000;
      const rateValid = x => /^-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,4})?$/.test(x) && Number(x) > -100 && Number(x) <= 1000;
      if (!amountValid(i.principal) || !amountValid(i.monthly_contribution) || !rateValid(i.annual_rate_percent) || !rateValid(i.inflation_percent)) throw Error('Supuestos fuera de rango.');
      if (a.monthly_contribution_timing !== 'end_of_month' || a.annual_rate_convention !== (i.method === 'compound' ? 'effective_annual_rate' : 'simple_annual_rate') || a.monthly_rate_conversion !== (i.method === 'compound' ? 'effective_monthly_rate' : 'annual_simple_rate_divided_by_12') || a.working_precision !== '80_significant_decimal_digits' || a.rounding !== 'half_up_to_cents_in_serialized_output; no_cent_rounding_per_month') throw Error('Convenciones del motor incompatibles.');
      if (!r.summary || !Array.isArray(r.series) || r.series.length !== a.years + 1) throw Error('Serie incompleta.');
      const summary = {}; for (const k of keys) { cents(r.summary[k]); summary[k] = r.summary[k]; }
      const series = r.series.map((p, n) => { if (!p || p.month !== n * 12) throw Error('Serie incompleta.'); for (const k of ['balance','real_balance','contributions']) cents(p[k]); return {month:p.month, balance:p.balance, real_balance:p.real_balance, contributions:p.contributions}; });
      const last = series[series.length-1];
      if (last.balance !== summary.final_balance || last.real_balance !== summary.inflation_adjusted || last.contributions !== summary.contributions || cents(series[0].balance) !== cents(a.principal) || cents(series[0].contributions) !== cents(a.principal) || cents(series[0].real_balance) !== cents(a.principal)) throw Error('Resumen y serie no coinciden.');
      return { id:s.id, version:s.version, assumptions:{principal:a.principal,annual_rate_percent:a.annual_rate_percent,years:a.years,monthly_contribution:a.monthly_contribution,inflation_percent:a.inflation_percent,method:a.method}, summary, series };
    });
  }
  function format(s) { const n = cents(s); const abs = n < 0n ? -n : n; return (n < 0n ? '−' : '') + String(abs / 100n).replace(/\B(?=(\d{3})+(?!\d))/g,'.') + ',' + String(abs % 100n).padStart(2,'0') + ' €'; }
  const esc = s => String(s).replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
  function render(data, date) {
    if (!Array.isArray(data) || data.length !== 2 || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(date)) throw Error('Informe inválido');
    const row = cells => '<tr>' + cells.map((c,i) => i ? '<td>'+esc(c)+'</td>' : '<th scope="row">'+esc(c)+'</th>').join('') + '</tr>';
    const table = (heads, rows) => '<table><thead><tr>'+heads.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table>';
    const assumptions = data.map(s => { const a=s.assumptions; return '<section><h2>Escenario '+s.id+' · supuestos</h2>'+table(['Supuesto','Valor'], [row(['Capital inicial',format(a.principal)]),row(['Tasa anual supuesta',a.annual_rate_percent+' %']),row(['Horizonte',a.years+' años']),row(['Aportación mensual',format(a.monthly_contribution)]),row(['Inflación anual supuesta',a.inflation_percent+' %']),row(['Método',a.method==='compound'?'Compuesto: tasa anual efectiva convertida a mensual efectiva':'Simple: tasa anual dividida entre 12'])])+'</section>'; }).join('');
    const summary = table(['Concepto','A','B','Diferencia B − A'],keys.map((k,n)=>row([labels[n],format(data[0].summary[k]),format(data[1].summary[k]),format(subtractMoney(data[1].summary[k],data[0].summary[k]))])));
    const series = data.map(s => '<section><h2>Escenario '+s.id+' · evolución anual</h2>'+table(['Mes','Aportaciones','Saldo nominal','Saldo real'],s.series.map(p=>row([p.month,format(p.contributions),format(p.balance),format(p.real_balance)])))+'</section>').join('');
    return '<article class="comparison-report"><h1>Informe de comparación de escenarios</h1><p>Generado: '+esc(date)+' (UTC)</p><p class="report-warning"><strong>Hipótesis, no predicción.</strong> Importes brutos; impuestos y costes de producto excluidos. No es asesoramiento financiero.</p><p>Aportaciones al final de cada mes. Inflación anual efectiva convertida a mensual efectiva. Cálculo con 80 dígitos significativos; redondeo half-up a céntimos solo al publicar, no cada mes.</p>'+assumptions+'<section><h2>Resumen y diferencias B − A</h2><p>Las diferencias restan las cifras publicadas en céntimos; si los horizontes difieren, comparan los finales de cada escenario, no un mismo instante.</p>'+summary+'</section>'+series+'</article>';
  }
  function renderDocument(data, date) {
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Informe de comparación de escenarios</title><style>body{max-width:70rem;margin:2rem auto;padding:0 1rem;color:#111;font:16px/1.45 Arial,sans-serif}h2{margin-top:2rem}table{width:100%;border-collapse:collapse;margin:1rem 0;table-layout:fixed}th,td{border:1px solid #777;padding:.5rem;text-align:left;overflow-wrap:anywhere}th{background:#eee}.report-warning{border:1px solid #333;padding:1rem}@media print{@page{size:A4;margin:14mm}body{font-size:9pt}thead{display:table-header-group}tr{break-inside:avoid}}</style></head><body>'+render(data,date)+'</body></html>';
  }
  const api = {capture,render,renderDocument,subtractMoney,format};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (!root || !root.document) return;
  const doc = root.document;
  let prepared = null;
  function clear() { prepared = null; const p=doc.getElementById('comparison-report-print'); if(p) p.replaceChildren(); }
  function host() { return doc.getElementById('scenario-report-host'); }
  function current() { if (root.location.hash !== '#escenarios' || typeof root.getScenarioComparisonSnapshot !== 'function') throw Error('Abre Escenarios y calcula ambos escenarios.'); return capture(root.getScenarioComparisonSnapshot()); }
  function refresh() {
    clear(); const h=host(); if (!h) return;
    const button=h.querySelector('button'), download=h.querySelector('[data-download]'), status=h.querySelector('[role=status]');
    h.querySelector('[data-print-guard]').textContent=root.__hermesPrintGuard ? 'La impresión está desactivada en este panel. Descarga HTML y ábrelo en tu navegador para imprimir/guardar PDF.' : '';
    try { current(); button.disabled=!!root.__hermesPrintGuard; download.disabled=false; status.textContent='Ambos escenarios están actualizados. El informe se captura al imprimir o descargar.'; }
    catch(e) { button.disabled=true; download.disabled=true; status.textContent=e.message; }
  }
  function mount(h) {
    h.className='scenario-report-host'; h.innerHTML='<h2>Informe de comparación</h2><p data-print-guard></p><p role="status" aria-live="polite"></p><button type="button" class="button button-primary">Imprimir / guardar como PDF</button> <button type="button" class="button" data-download>Descargar informe (HTML)</button>';
    h.querySelector('[data-download]').addEventListener('click', () => {
      let data;
      try { data=current(); } catch(e) { refresh(); return; }
      let url;
      try {
        const html=renderDocument(data,new Date().toISOString());
        url=root.URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));
        const a=doc.createElement('a'); a.href=url; a.download='informe-comparacion.html'; doc.body.appendChild(a);
        try { a.click(); } finally { a.remove(); }
        h.querySelector('[role=status]').textContent='Descarga solicitada. El navegador decide dónde guardar el archivo.';
      } catch(e) { h.querySelector('[role=status]').textContent='No se pudo solicitar la descarga. Inténtalo de nuevo.'; }
      finally { if(url) root.setTimeout(()=>root.URL.revokeObjectURL(url),60000); }
    });
    h.querySelector('button').addEventListener('click', () => {
      clear();
      try {
        const data=current(), html=render(data,new Date().toISOString());
        let p=doc.getElementById('comparison-report-print'); if(!p) { p=doc.createElement('div'); p.id='comparison-report-print'; doc.body.appendChild(p); }
        p.innerHTML=html; prepared=JSON.stringify(data); root.print();
      } catch(e) { clear(); h.querySelector('[role=status]').textContent=e.message; h.querySelector('button').disabled=true; }
    });
    refresh();
  }
  root.mountScenarioReport=mount;
  root.addEventListener('scenario-comparison-change',refresh);
  root.addEventListener('hashchange',clear);
  root.addEventListener('afterprint',clear);
  root.addEventListener('beforeprint',()=>{ try { if (!prepared || JSON.stringify(current()) !== prepared) clear(); } catch (_) { clear(); } });
})(typeof window === 'undefined' ? null : window);
