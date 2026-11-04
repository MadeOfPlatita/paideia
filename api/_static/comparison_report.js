/* Informe local: solo consume el contrato público; no calcula escenarios. */
(function (root) {
  'use strict';
  const money = /^-?(?:0|[1-9]\d*)\.\d{2}$/;
  const decimal = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;
  const keys = ['final_balance', 'inflation_adjusted', 'contributions', 'interest'];
  const labels = ['Saldo nominal', 'Saldo real', 'Aportaciones totales', 'Interés'];
  function cents(s) { if (typeof s !== 'string' || !money.test(s) || s.length > 200) throw Error('Importe inválido'); return BigInt(s.replace('.', '')); }
  const cleanText = (value, max) => typeof value === 'string' ? value.trim().slice(0, max) : '';
  function cleanDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return '';
    const [year, month, day] = value.split('-').map(Number);
    if (year < 1900 || year > 2100 || month < 1 || month > 12 || day < 1) return '';
    return day <= new Date(Date.UTC(year, month, 0)).getUTCDate() ? value : '';
  }
  function generationDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value)) throw Error('Informe inválido');
    const day = cleanDate(value.slice(0, 10));
    const parsed = new Date(value);
    if (!day || Number.isNaN(parsed.getTime()) || parsed.toISOString() !== value) throw Error('Informe inválido');
    return day;
  }
  function rateText(value) {
    if (typeof value === 'number') return Number.isFinite(value) ? String(value) : '';
    if (typeof value !== 'string') return '';
    const trimmed = value.trim();
    return /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/.test(trimmed) ? trimmed : '';
  }
  function cleanCondition(condition) {
    if (!condition || typeof condition !== 'object') return null;
    const value = rateText(condition.value);
    return {
      metric: cleanText(condition.metric, 40),
      value: value === '' ? null : value,
      state: cleanText(condition.state, 20),
      reason: cleanText(condition.reason, 80),
      effective_from: cleanDate(condition.effective_from),
      effective_to: cleanDate(condition.effective_to),
      retrieved_at: cleanDate(condition.retrieved_at)
    };
  }
  function cleanTier(tier) {
    if (typeof tier === 'string') return { label: cleanText(tier, 180), condition: '', tae: '', tin: '', selected: false };
    if (!tier || typeof tier !== 'object') return null;
    return {
      label: cleanText(tier.label || tier.condition_label || tier.condition, 180),
      condition: cleanText(tier.condition, 60),
      tae: rateText(tier.tae),
      tin: rateText(tier.tin),
      selected: tier.selected === true
    };
  }
  function sanitizeSource(s) {
    const raw = (s && typeof s === 'object' && Object.prototype.hasOwnProperty.call(s, 'source')) ? s.source : s;
    if (!raw || typeof raw !== 'object') return null;
    const product = cleanText(raw.product || raw.name || raw.product_name || raw.product_id || raw.id, 160);
    const productId = cleanText(raw.product_id || raw.id, 80);
    const urlCandidate = typeof raw.url === 'string' ? raw.url : (typeof raw.primary_url === 'string' ? raw.primary_url : '');
    const url = /^https:\/\/[^\s<>"']+$/.test(urlCandidate) && urlCandidate.length <= 2048 ? urlCandidate.slice(0, 500) : '';
    const retrieved_at = cleanDate(raw.retrieved_at) || cleanDate(raw.as_of);
    const kind = cleanText(raw.kind, 40);
    const condition = cleanCondition(raw.condition);
    const tiers = Array.isArray(raw.tiers) ? raw.tiers.slice(0, 8).map(cleanTier).filter(tier => tier && (tier.label || tier.tae)) : [];
    const term = Number.isInteger(raw.term_months) && raw.term_months >= 1 && raw.term_months <= 120 ? raw.term_months : null;
    const urlOrigin = ['condition_source', 'catalogue_record'].includes(raw.url_origin) ? raw.url_origin : '';
    const clean = {
      product, product_id: productId, url, url_origin: urlOrigin, retrieved_at,
      source_title: cleanText(raw.source_title, 160), source_accessed_at: cleanDate(raw.source_accessed_at),
      kind, secondary: raw.secondary === true || (kind !== '' && kind !== 'official'),
      document_date: cleanDate(raw.document_date),
      condition, selected_tier: cleanText(raw.selected_tier, 180), selected_condition: cleanText(raw.selected_condition, 60),
      tiers, term_months: term
    };
    if (!clean.product && !clean.url && !clean.retrieved_at) return null;
    return clean;
  }
  function sourceLabel(src) {
    if (!src) return 'Supuesto manual: sin fuente de producto ni fecha.';
    const parts = [];
    if (src.product) parts.push(src.product);
    if (src.source_title) parts.push(src.source_title);
    if (src.url) parts.push(src.url);
    if (src.source_accessed_at) parts.push('fuente consultada ' + src.source_accessed_at);
    if (src.retrieved_at) parts.push('consultada ' + src.retrieved_at);
    if (src.secondary) parts.push('fuente secundaria, pendiente de confirmar');
    else if (src.url_origin === 'condition_source' && !src.kind) parts.push('clase de fuente desconocida');
    return parts.length ? parts.join(' · ') : 'Supuesto manual: sin fuente de producto ni fecha.';
  }
  function rateDisplay(value) {
    const text = rateText(value);
    if (!text) return '';
    const number = Number(text);
    if (!Number.isFinite(number)) return '';
    return number.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) + ' %';
  }
  function conditionStateLabel(condition, generated) {
    if (condition.state === 'known') {
      if (condition.effective_to && condition.effective_to < generated) return 'documentada; vigencia terminada el ' + condition.effective_to;
      if (condition.effective_from && condition.effective_from > generated) return 'documentada; aún no vigente (desde ' + condition.effective_from + ')';
      if (condition.effective_to) return 'documentada; vigencia declarada hasta ' + condition.effective_to;
      if (condition.effective_from) return 'documentada; vigencia declarada desde ' + condition.effective_from + ', sin fecha de fin';
      return 'documentada; sin fechas de vigencia (no verificada)';
    }
    return { stale: 'vencida', conflict: 'en conflicto', unknown: 'sin dato' }[condition.state] || condition.state;
  }
  function conditionLabel(condition, generated) {
    if (!condition) return '';
    const rate = rateDisplay(condition.value);
    const value = rate ? 'TAE ' + rate : 'TAE sin cifra utilizable';
    return value + ' · ' + conditionStateLabel(condition, generated) + (condition.reason ? ' · motivo ' + condition.reason : '');
  }
  function tierLabel(source) {
    if (!source) return '';
    const selected = source.tiers.find(tier => tier.selected) || (source.selected_tier ? { label: source.selected_tier, tae: '', tin: '' } : null);
    const parts = [];
    if (selected) parts.push(selected.label + (selected.tae ? ' (' + rateDisplay(selected.tae) + ' TAE' + (selected.tin ? ' / ' + rateDisplay(selected.tin) + ' TIN' : '') + ')' : ''));
    const others = source.tiers.filter(tier => !tier.selected && tier.tae);
    if (others.length) parts.push('Otros tramos de la misma fuente: ' + others.map(tier => rateDisplay(tier.tae) + ' TAE' + (tier.label ? ' — ' + tier.label : '')).join('; '));
    return parts.join(' · ');
  }
  function validityLabel(condition) {
    if (!condition) return 'no consta';
    if (condition.effective_from && condition.effective_to) return 'del ' + condition.effective_from + ' al ' + condition.effective_to;
    if (condition.effective_to) return 'hasta ' + condition.effective_to;
    if (condition.effective_from) return 'desde ' + condition.effective_from + ', sin fecha de fin documentada';
    return 'sin fecha de fin documentada';
  }
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
      return { id:s.id, version:s.version, assumptions:{principal:a.principal,annual_rate_percent:a.annual_rate_percent,years:a.years,monthly_contribution:a.monthly_contribution,inflation_percent:a.inflation_percent,method:a.method}, summary, series, source: sanitizeSource(s) };
    });
  }
  function format(s) { const n = cents(s); const abs = n < 0n ? -n : n; return (n < 0n ? '−' : '') + String(abs / 100n).replace(/\B(?=(\d{3})+(?!\d))/g,'.') + ',' + String(abs % 100n).padStart(2,'0') + ' €'; }
  const esc = s => String(s).replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
  function render(data, date) {
    if (!Array.isArray(data) || data.length !== 2) throw Error('Informe inválido');
    const generated = generationDate(date);
    const row = cells => '<tr>' + cells.map((c,i) => i ? '<td>'+esc(c)+'</td>' : '<th scope="row">'+esc(c)+'</th>').join('') + '</tr>';
    const table = (heads, rows) => '<table><thead><tr>'+heads.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table>';
    const assumptions = data.map(s => {
      const a = s.assumptions, src = s.source;
      const rows = [
        row(['Capital inicial', format(a.principal)]),
        row(['Tasa anual supuesta', a.annual_rate_percent + ' %']),
        row(['Fuente de la tasa', sourceLabel(src)]),
        row(['Horizonte', a.years === 1 ? '1 año' : a.years + ' años']),
        row(['Aportación mensual', format(a.monthly_contribution)]),
        row(['Inflación anual supuesta', a.inflation_percent + ' %']),
        row(['Método', a.method === 'compound' ? 'Compuesto: tasa anual efectiva convertida a mensual efectiva' : 'Simple: tasa anual dividida entre 12'])
      ];
      let notes = '';
      if (!src) {
        notes += '<p>Sin vínculo a una condición documentada: la tasa es un supuesto manual.</p>';
      } else {
        if (src.condition) {
          rows.push(row(['Condición de la tasa', conditionLabel(src.condition, generated)]));
          if (tierLabel(src)) rows.push(row(['Tramo de la tasa', tierLabel(src)]));
          rows.push(row(['Vigencia de la tasa', validityLabel(src.condition)]));
          rows.push(row(['Consulta de la condición', src.retrieved_at ? 'consultada ' + src.retrieved_at : 'no consta fecha de consulta']));
          rows.push(row(['Fecha del documento', src.document_date ? 'fechado ' + src.document_date : 'no indicada en la fuente']));
          rows.push(row(['Plazo documentado del producto', src.term_months ? src.term_months + ' meses' : 'no consta']));
          const horizon = a.years === 1 ? '1 año' : a.years + ' años';
          const comparison = src.term_months ? (a.years * 12 === src.term_months ? ' · coincide con el plazo documentado' : ' · no coincide con el plazo documentado') : ' · sin plazo documentado con el que compararlo';
          rows.push(row(['Horizonte del escenario', horizon + comparison]));
          const expired = Boolean(src.condition.effective_to && src.condition.effective_to < generated);
          const notYet = Boolean(src.condition.effective_from && src.condition.effective_from > generated);
          if (src.secondary) notes += '<p class="report-warning"><strong>Fuente secundaria.</strong> Pendiente de confirmar en la página oficial del producto.</p>';
          if (src.term_months && a.years * 12 !== src.term_months) notes += '<p class="report-warning"><strong>Horizonte distinto del plazo documentado.</strong> El escenario usa ' + esc(horizon) + ' y el producto documenta ' + esc(src.term_months + ' meses') + '; el horizonte es un supuesto editable y no se presenta como plazo del producto.</p>';
          if (src.condition.state === 'known' && expired) notes += '<p class="report-warning"><strong>Vigencia terminada en la copia conservada.</strong> La condición terminó el ' + esc(src.condition.effective_to) + '; no se presenta como oferta vigente.</p>';
          else if (src.condition.state === 'known' && notYet) notes += '<p class="report-warning"><strong>Condición no vigente a fecha de generación.</strong> Su vigencia empieza el ' + esc(src.condition.effective_from) + '; no se presenta como oferta actual.</p>';
          else if (src.condition.state !== 'known') notes += '<p class="report-warning"><strong>La condición de la tasa no está vigente.</strong> Se conserva como referencia documentada, no como oferta actual.</p>';
          if (src.condition.state === 'known' && !expired && !notYet && !src.condition.effective_to) notes += '<p>La condición no tiene fecha de fin documentada; no se afirma que siga vigente.</p>';
          if (!src.condition.retrieved_at) notes += '<p>La condición no tiene fecha de consulta registrada.</p>';
          if (src.url_origin === 'catalogue_record') notes += '<p>La URL procede del registro del catálogo; la condición no incluye una URL propia.</p>';
        } else {
          notes += '<p>Procedencia sin detalle de condición: solo consta el producto y la fecha.</p>';
        }
      }
      return '<section><h2>Escenario ' + s.id + ' · supuestos</h2>' + table(['Supuesto', 'Valor'], rows) + notes + '</section>';
    }).join('');
    const summary = table(['Concepto','A','B','Diferencia B − A'],keys.map((k,n)=>row([labels[n],format(data[0].summary[k]),format(data[1].summary[k]),format(subtractMoney(data[1].summary[k],data[0].summary[k]))])));
    const series = data.map(s => '<section><h2>Escenario '+s.id+' · evolución anual</h2>'+table(['Mes','Aportaciones','Saldo nominal','Saldo real'],s.series.map(p=>row([p.month,format(p.contributions),format(p.balance),format(p.real_balance)])))+'</section>').join('');
    const sources = '<section><h2>Fuentes y fechas</h2><ul>'+data.map(s => '<li>Escenario '+esc(s.id)+': '+esc(sourceLabel(s.source))+'</li>').join('')+'<li>Motor de cálculo: local y determinista; las tasas son supuestos manuales y no provienen de ofertas, fuentes ni fechas de producto salvo que se indique arriba.</li></ul></section>';
    return '<article class="comparison-report"><h1>Informe de comparación de escenarios</h1><p>Generado: '+esc(date)+' (UTC)</p><p class="report-privacy">Este informe se genera en tu navegador a partir de los datos de esta pestaña. No incluye tu mapa de perfil y no se envía a ningún servidor.</p><p class="report-warning"><strong>Hipótesis, no predicción.</strong> Importes brutos; impuestos y costes de producto excluidos. No es asesoramiento financiero.</p><p>Aportaciones al final de cada mes. Inflación anual efectiva convertida a mensual efectiva. Cálculo con 80 dígitos significativos; redondeo half-up a céntimos solo al publicar, no cada mes.</p>'+assumptions+'<section><h2>Resumen y diferencias B − A</h2><p>Las diferencias restan las cifras publicadas en céntimos; si los horizontes difieren, comparan los finales de cada escenario, no un mismo instante.</p>'+summary+'</section>'+sources+series+'</article>';
  }
  function renderDocument(data, date) {
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Informe de comparación de escenarios</title><style>body{max-width:70rem;margin:2rem auto;padding:0 1rem;color:#111;font:16px/1.45 Arial,sans-serif}h2{margin-top:2rem}table{width:100%;border-collapse:collapse;margin:1rem 0;table-layout:fixed}th,td{border:1px solid #777;padding:.5rem;text-align:left;overflow-wrap:anywhere}th{background:#eee}.report-privacy{font-size:.9rem;color:#333}.report-warning{border:1px solid #333;padding:1rem}@media print{@page{size:A4;margin:14mm}body{font-size:9pt}thead{display:table-header-group}tr{break-inside:avoid}}</style></head><body>'+render(data,date)+'</body></html>';
  }
  const api = {capture,render,renderDocument,subtractMoney,format};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (!root || !root.document) return;
  const doc = root.document;
  let prepared = null;
  function setText(node, text) { if (node && node.textContent !== text) node.textContent = text; }
  function clear() { prepared = null; const p=doc.getElementById('comparison-report-print'); if(p) p.replaceChildren(); }
  function host() { return doc.getElementById('scenario-report-host'); }
  function current() { if (root.location.hash !== '#escenarios' || typeof root.getScenarioComparisonSnapshot !== 'function') throw Error('Abre Escenarios y calcula ambos escenarios.'); return capture(root.getScenarioComparisonSnapshot()); }
  function refresh() {
    clear(); const h=host(); if (!h) return;
    const button=h.querySelector('button'), download=h.querySelector('[data-download]'), status=h.querySelector('[role=status]');
    setText(h.querySelector('[data-print-guard]'), root.__hermesPrintGuard ? 'La impresión está desactivada en este panel. Descarga HTML y ábrelo en tu navegador para imprimir/guardar PDF.' : '');
    try { current(); button.disabled=!!root.__hermesPrintGuard; download.disabled=false; setText(status, 'Ambos escenarios están actualizados. El informe se captura al imprimir o descargar.'); }
    catch(e) { button.disabled=true; download.disabled=true; setText(status, e.message); }
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
