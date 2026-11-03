(async () => {
  const checks = [];
  const check = (condition, name) => { checks.push({name, pass: !!condition}); if (!condition) throw new Error(name); };
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const wait = async predicate => { for (let i=0; i<150; i++) { if (predicate()) return; await sleep(20); } throw new Error('timeout esperando resultado'); };
  const realFetch = window.fetch.bind(window);
  const byId = id => document.getElementById(id);
  const snap = () => window.getScenarioComparisonSnapshot();
  const edit = (id, value) => { const element = byId(id); element.value = value; element.dispatchEvent(new Event('input', {bubbles:true})); };
  const submit = index => document.querySelectorAll('.scenario-form')[index].requestSubmit();
  const output = index => document.querySelectorAll('.scenario-output')[index];
  const inputs = (suffix, values) => Object.entries(values).forEach(([field,value]) => edit('scenario-'+field+suffix,value));
  const post = async payload => (await realFetch('/api/calculate', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})).json();
  const currency = value => { const neg=value.startsWith('-'); const [whole,cents]=(neg?value.slice(1):value).split('.'); return (neg?'-':'')+new Intl.NumberFormat('es-ES').format(BigInt(whole))+','+cents+'\u00a0€'; };
  const verifyOutput = (index, result) => {
    const panel=output(index), rows=[...panel.querySelectorAll('tbody tr')];
    check(rows.length === result.series.length, `tabla ${index} tiene serie completa`);
    result.series.forEach((point,i)=>{
      const cells=[...rows[i].children].map(e=>e.textContent);
      check(cells[0]===`${point.month} meses` && cells[1]===currency(point.contributions) && cells[2]===currency(point.balance) && cells[3]===currency(point.real_balance), `tabla ${index} mes ${point.month}`);
    });
    const values=result.series.flatMap(p=>[Number(p.contributions),Number(p.balance),Number(p.real_balance)]);
    let min=Math.min(0,...values),max=Math.max(0,...values); if(min===max){min-=1;max+=1;} const pad=(max-min)*.08;min-=pad;max+=pad;
    const xmax=Math.max(1,...result.series.map(p=>p.month));
    for(const [field,klass] of [['contributions','series-contributions'],['balance','series-balance'],['real_balance','series-real']]){
      const expected=result.series.map((p,i)=>`${i?'L':'M'}${(74+p.month/xmax*(735-74)).toFixed(2)} ${(280-(Number(p[field])-min)/(max-min)*(280-24)).toFixed(2)}`).join(' ');
      check(panel.querySelector('path.'+klass)?.getAttribute('d')===expected,`gráfico ${index} ${field}`);
    }
    for(const value of Object.values(result.summary)) check(panel.innerText.includes(currency(value)),`resumen ${index} ${value}`);
  };
  try {
    check(document.querySelectorAll('.scenario-form').length===2,'dos formularios');
    check(!!document.querySelector('#scenario-comparison-summary table'),'tabla comparativa');
    inputs('',{principal:'1000',rate:'-5',years:'2',contribution:'20',inflation:'2'});
    inputs('-b',{principal:'0',rate:'0',years:'1',contribution:'0',inflation:'0'});
    submit(0); submit(1); await wait(()=>snap().scenarios.every(s=>s.status==='current'));
    let [a,b]=snap().scenarios;
    check(a.result.summary.interest.startsWith('-') && output(0).innerText.includes('pérdida'),'pérdida y aviso visibles');
    check(b.result.summary.final_balance==='0.00' && output(1).innerText.includes('0,00') && output(1).innerText.includes('Tasa supuesta cero'),'cero y aviso visibles');
    check(JSON.stringify(a.result)===JSON.stringify(await post({...a.inputs,years:Number(a.inputs.years)})),'A coincide con motor HTTP');
    check(JSON.stringify(b.result)===JSON.stringify(await post({...b.inputs,years:Number(b.inputs.years)})),'B coincide con motor HTTP');
    verifyOutput(0,a.result); verifyOutput(1,b.result);
    const bBefore=JSON.stringify(b);
    let release; const held=new Promise(resolve=>release=resolve); let intercepted=false;
    window.fetch=async (...args)=>{ const response=await realFetch(...args); if(String(args[0])==='/api/calculate' && !intercepted){intercepted=true; await held;} return response; };
    edit('scenario-rate','-8'); submit(0); await wait(()=>intercepted);
    check(snap().scenarios[0].status==='pending' && snap().scenarios[0].result===null && !output(0).querySelector('svg'),'pendiente oculta resultado anterior');
    edit('scenario-rate','-10'); check(snap().scenarios[0].status==='dirty' && snap().scenarios[0].result===null,'edición invalida respuesta pendiente');
    release(); await sleep(150);
    check(snap().scenarios[0].status==='dirty' && snap().scenarios[0].result===null,'respuesta tardía descartada');
    check(JSON.stringify(snap().scenarios[1])===bBefore,'edición A conserva B');
    window.fetch=realFetch; submit(0); await wait(()=>snap().scenarios[0].status==='current');
    a=snap().scenarios[0]; check(a.result.assumptions.annual_rate_percent==='-10','resultado usa edición actual'); verifyOutput(0,a.result);
    window.fetch=async (...args)=>{if(String(args[0])==='/api/calculate') throw new Error('synthetic transport failure'); return realFetch(...args);};
    edit('scenario-rate','-11'); submit(0); await wait(()=>snap().scenarios[0].status==='error');
    check(snap().scenarios[0].result===null && !output(0).querySelector('svg'),'error no muestra resultado viejo');
    check(JSON.stringify(snap().scenarios[1])===bBefore && output(1).querySelector('svg'),'error A conserva B');
    window.fetch=realFetch;
    edit('scenario-method','simple'); edit('scenario-principal','1000'); edit('scenario-years','3'); edit('scenario-rate','-99'); submit(0); await wait(()=>snap().scenarios[0].status==='current');
    a=snap().scenarios[0]; check(a.result.assumptions.method==='simple' && a.result.summary.final_balance.startsWith('-') && output(0).innerText.includes('pérdida'),'simple con saldo negativo y aviso');
    check(JSON.stringify(a.result)===JSON.stringify(await post({...a.inputs,years:Number(a.inputs.years)})),'simple coincide con motor HTTP'); verifyOutput(0,a.result);
    edit('scenario-method','compound');
    edit('scenario-rate','0.1234'); edit('scenario-principal','1000000000'); edit('scenario-years','40'); edit('scenario-inflation','0.1234');
    edit('scenario-rate','1000'); submit(0); await wait(()=>snap().scenarios[0].status==='current');
    a=snap().scenarios[0]; check(output(0).innerText.includes('0,1234 %'),'supuestos conservan cuatro decimales');
    check(output(0).innerText.includes(currency(a.result.summary.final_balance)),'importe grande exacto en resumen'); verifyOutput(0,a.result);
    const detached=snap(); detached.scenarios[0].result.summary.final_balance='alterado'; check(snap().scenarios[0].result.summary.final_balance!=='alterado','snapshot aislado');
    check(document.documentElement.scrollWidth <= document.documentElement.clientWidth, 'sin desbordamiento horizontal de página');
    let calls=0; window.fetch=async (...args)=>{if(String(args[0])==='/api/calculate') calls++;return realFetch(...args);};
    edit('scenario-principal','1e3'); submit(0); await sleep(100);
    check(calls===0 && byId('scenario-form-error').innerText.includes('sin exponentes') && snap().scenarios[0].status==='dirty','validación comprensible sin solicitud inválida');
    check(JSON.stringify(snap().scenarios[1])===bBefore,'validación A conserva B');
    window.fetch=realFetch; edit('scenario-principal','1000'); edit('scenario-rate','-5'); edit('scenario-years','2'); edit('scenario-inflation','2'); submit(0); await wait(()=>snap().scenarios[0].status==='current');
    return {ok:true,checks, viewport:{width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth}, snapshot:snap()};
  } catch(error) { return {ok:false,checks,error:String(error),snapshot:window.getScenarioComparisonSnapshot?.()}; }
  finally { window.fetch=realFetch; }
})()