(function(root){
  'use strict';
  const editorial={
    saving_investing:'Ahorrar e invertir son decisiones distintas; una inversión puede perder valor y sus resultados son inciertos.',
    risk:'Los riesgos dependen del producto, de la entidad y de la custodia; conviene revisar sus condiciones antes de decidir.',
    inflation:'La inflación puede reducir el poder adquisitivo del dinero aunque su importe nominal no cambie.',
    guarantees:'La existencia y el alcance de una garantía dependen de las condiciones aplicables; no deben suponerse sin verificarlas.',
    simulation:'Una simulación es hipotética y depende de sus supuestos; no predice resultados futuros ni incluye necesariamente costes o impuestos.'
  };
  const obj=x=>x!==null && typeof x==='object' && !Array.isArray(x);
  const keys=(x,k)=>obj(x) && Object.keys(x).sort().join('|')===k.slice().sort().join('|');
  const fields=['principal','annual_rate_percent','years','monthly_contribution','method','inflation_percent'];
  function canonical(value,money){
    const negative=value.startsWith('-'); const s=negative?value.slice(1):value;
    let [integer,decimal='']=s.split('.');
    if(money) return integer+'.'+decimal.padEnd(2,'0');
    decimal=decimal.replace(/0+$/,'');
    return (negative && (integer!=='0' || decimal) ? '-':'')+integer+(decimal?'.'+decimal:'');
  }
  function scenario(input){
    if(!keys(input,fields)) throw new Error('Escenario no válido');
    for(const k of ['principal','monthly_contribution']) if(typeof input[k]!=='string' || !/^(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,2})?$/.test(input[k]) || Number(input[k])>1000000000) throw new Error('Importe no válido');
    for(const k of ['annual_rate_percent','inflation_percent']) if(typeof input[k]!=='string' || !/^-?(?:0|[1-9][0-9]{0,3})(?:\.[0-9]{1,4})?$/.test(input[k]) || Number(input[k])<=-100 || Number(input[k])>1000) throw new Error('Tasa no válida');
    if(!Number.isInteger(input.years) || input.years<1 || input.years>40 || !['simple','compound'].includes(input.method)) throw new Error('Escenario no válido');
    return {principal:canonical(input.principal,true),annual_rate_percent:canonical(input.annual_rate_percent,false),years:input.years,monthly_contribution:canonical(input.monthly_contribution,true),method:input.method,inflation_percent:canonical(input.inflation_percent,false)};
  }
  function calculation(c,submitted){
    if(!keys(c,['source','data']) || c.source!=='deterministic_local' || !submitted) throw new Error('Cálculo no válido');
    const s=scenario(submitted),d=c.data;
    if(!keys(d,['hypothetical','not_prediction','currency','assumptions','summary','series']) || d.hypothetical!==true || d.not_prediction!==true || d.currency!=='EUR') throw new Error('Cálculo no válido');
    const a=d.assumptions;
    if(!keys(a,[...fields,'annual_rate_convention','monthly_contribution_timing','monthly_rate_conversion','working_precision','rounding','taxes_included','fees_included']) || fields.some(k=>a[k]!==s[k]) || a.annual_rate_convention!==(s.method==='compound'?'effective_annual_rate':'simple_annual_rate') || a.monthly_rate_conversion!==(s.method==='compound'?'effective_monthly_rate':'annual_simple_rate_divided_by_12') || a.monthly_contribution_timing!=='end_of_month' || a.working_precision!=='80_significant_decimal_digits' || a.rounding!=='half_up_to_cents_in_serialized_output; no_cent_rounding_per_month' || a.taxes_included!==false || a.fees_included!==false) throw new Error('Supuestos no válidos');
    const money=x=>typeof x==='string' && /^-?(?:0|[1-9][0-9]*)\.[0-9]{2}$/.test(x) && x.length<=100;
    if(!keys(d.summary,['contributions','final_balance','interest','inflation_adjusted']) || Object.values(d.summary).some(x=>!money(x)) || !Array.isArray(d.series) || d.series.length!==s.years+1 || d.series.some((p,i)=>!keys(p,['month','contributions','balance','real_balance']) || p.month!==i*12 || !money(p.contributions) || !money(p.balance) || !money(p.real_balance))) throw new Error('Resultado no válido');
    return c;
  }
  function project(value,submitted){
    if(!obj(value) || value.provider_mode!=='test_only' || value.external_sent!==false) throw new Error('Origen estructurado no válido');
    const d=value.structured_education;
    if(obj(d) && d.version==='paideia-education-v2'){
      // v2: el catálogo lo posee el servidor (39 afirmaciones). El cliente comprueba
      // forma y las invariantes del catálogo, no la igualdad con una copia local.
      if(!keys(d,['version','kind','items','calculation']) || d.kind!=='claims' || !Array.isArray(d.items) || d.items.length>6) throw new Error('Contenido estructurado no válido');
      const vistos=new Set();
      for(const item of d.items){
        if(!keys(item,['id','text']) || typeof item.id!=='string' || !/^[a-z0-9_]{3,64}$/.test(item.id) || vistos.has(item.id)) throw new Error('Afirmación no válida');
        if(typeof item.text!=='string' || item.text.length<20 || item.text.length>600 || /[0-9%€]/.test(item.text)) throw new Error('Texto de afirmación no válido');
        vistos.add(item.id);
      }
      if(d.calculation!==null) calculation(d.calculation,submitted);
      else if(submitted) throw new Error('Falta el cálculo solicitado');
      return {items:d.items.map(({id,text})=>({id,text})),calculation:d.calculation};
    }
    if(!keys(d,['version','kind','items','calculation']) || d.version!=='paideia-education-v1' || d.kind!=='editorial' || !Array.isArray(d.items) || d.items.length<1 || d.items.length>5) throw new Error('Contenido estructurado no válido');
    const ids=new Set();
    for(const item of d.items) { if(!keys(item,['id','text']) || typeof item.id!=='string' || !Object.hasOwn(editorial,item.id) || editorial[item.id]!==item.text || ids.has(item.id)) throw new Error('Contenido editorial no válido'); ids.add(item.id); }
    if(d.calculation!==null) calculation(d.calculation,submitted);
    else if(submitted) throw new Error('Falta el cálculo solicitado');
    return {items:d.items.map(({id,text})=>({id,text})),calculation:d.calculation};
  }
  function select(value, expected, submitted){
    if(expected===true || (value && Object.prototype.hasOwnProperty.call(value,'structured_education'))) return project(value,submitted);
    return null;
  }
  const api={project,select,scenario};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  else root.PaideiaStructuredEducation=api;
})(typeof globalThis!=='undefined'?globalThis:this);
