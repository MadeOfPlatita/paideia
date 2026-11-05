(async () => {
 const assert = (x,m) => {if(!x) throw Error(m)};
 const press = t => {const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()===t); assert(b&&!b.disabled,'button unavailable '+t); b.click()};
 const route = async hash => {location.hash=hash; await new Promise(r=>setTimeout(r,80))};
 const advance = id => {const s=document.querySelector('#simulation-product'); s.value=id;s.dispatchEvent(new Event('change',{bubbles:true}));press('Elegir referencia');press('Continuar con el importe ficticio');let a=document.querySelector('#simulation-amount');a.value='100';a.form.requestSubmit()};
 await route('#simulacion'); await new Promise(r=>setTimeout(r,150));
 advance('fixture-d'); document.querySelector('#simulation-understood').click(); press('Volver');press('Volver');press('Volver');
 const s=document.querySelector('#simulation-product'); const opt=document.createElement('option');opt.value='fixture-two';opt.textContent='SEGUNDO SINTÉTICO';s.appendChild(opt);
 // Add a second synthetic product through the same in-memory catalogue used by the UI.
 state.simulation.products.push({id:'fixture-two',name:'SEGUNDO SINTÉTICO',family:'deposito',issuer:'Ficticia',unknown_fields:[],conflicts:[]});
 advance('fixture-two'); let check=document.querySelector('#simulation-understood');
 assert(!check.checked,'acknowledgement persisted after changing product');
 check.click(); await route('#privacidad'); await route('#simulacion');
 check=document.querySelector('#simulation-understood');
 assert(check && !check.checked && [...document.querySelectorAll('button')].find(x=>x.textContent.trim()==='Terminar ensayo y crear justificante').disabled,'acknowledgement persisted after leaving and reentering');
 return {pass:true,product:'fixture-two',unchecked:!check.checked};
})()