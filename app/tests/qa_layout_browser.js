(async () => {
 const checks=[]; const check=(name,pass,detail)=>checks.push({name,pass:!!pass,detail});
 const sleep=ms=>new Promise(r=>setTimeout(r,ms)); const wait=async f=>{for(let i=0;i<200;i++){if(f())return;await sleep(25)}throw Error('timeout')};
 try {
  location.hash='#inicio'; await wait(()=>document.querySelector('#chat-context-field-0'));
  const spans=[...document.querySelectorAll('#chat-panel .choice span')].filter(x=>/^(respuestas\.objetivo|detalle_economico\.importe_objetivo):/.test(x.textContent));
  const bounds=spans.map(x=>({text:x.textContent,right:x.getBoundingClientRect().right}));
  check('home bounds',document.documentElement.scrollWidth<=document.documentElement.clientWidth && bounds.length===2 && bounds.every(x=>x.right<=document.documentElement.clientWidth),{client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,bounds});
  location.hash='#biblioteca'; await wait(()=>document.querySelector('#catalogue-family')&&document.querySelectorAll('.product-card').length);
  check('temporal notice',/recarg/i.test(document.querySelector('.selection-tray').textContent)&&/filtros?/i.test(document.querySelector('.selection-tray').textContent),document.querySelector('.selection-tray').textContent);
  location.hash='#escenarios'; await wait(()=>document.querySelectorAll('.scenario-form').length===2);
  const edit=(id,value)=>{const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('input',{bubbles:true}))};
  for(const [s,values] of [['',['100','2','10','50','1']],['-b',['200','3','5','100','1']]]) ['principal','rate','years','contribution','inflation'].forEach((k,i)=>edit('scenario-'+k+s,values[i]));
  document.querySelectorAll('.scenario-form').forEach(f=>f.requestSubmit()); await wait(()=>window.getScenarioComparisonSnapshot().scenarios.every(s=>s.status==='current'));
  let summary=document.querySelector('#scenario-comparison-summary'); let rows=[...summary.querySelectorAll('tbody tr')];
  check('different horizons',/10\s*años/i.test(rows[0].textContent)&&/5\s*años/i.test(rows[1].textContent)&&/plazos.*distint|horizontes.*distint/i.test(summary.textContent),summary.textContent);
  const b=JSON.stringify(window.getScenarioComparisonSnapshot().scenarios[1]); edit('scenario-years','5'); rows=[...summary.querySelectorAll('tbody tr')];
  check('edit retains B and hides stale A',JSON.stringify(window.getScenarioComparisonSnapshot().scenarios[1])===b && window.getScenarioComparisonSnapshot().scenarios[0].result===null && /Pendiente/.test(rows[0].textContent)&& /5\s*años/i.test(rows[0].textContent)&& /—/.test(rows[0].textContent),summary.textContent);
  document.querySelector('.scenario-form').requestSubmit(); await wait(()=>window.getScenarioComparisonSnapshot().scenarios[0].status==='current');
  check('equal horizons no warning',!/plazos.*distint|horizontes.*distint/i.test(summary.textContent)&&[...summary.querySelectorAll('tbody tr')].every(r=>/5\s*años/i.test(r.textContent)),summary.textContent);
  return {ok:checks.every(x=>x.pass),checks};
 }catch(e){return {ok:false,error:String(e),checks}}
})()