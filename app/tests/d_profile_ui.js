(async () => {
  const assert=(x,m)=>{if(!x) throw Error(m)};
  const press=t=>{let b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()===t); assert(b&&!b.disabled,'button '+t); b.click()};
  assert(!localStorage.length && !sessionStorage.length,'start clean');
  location.hash='#perfil'; await new Promise(r=>setTimeout(r,100));
  press('No lo sé'); press('Continuar'); press('Omitir'); press('Continuar'); press('Omitir'); press('Continuar'); press('Omitir'); press('Continuar');
  const i=document.querySelector('main input[type=text]'); assert(i,'amount field'); i.value='0'; i.form.requestSubmit(); press('Continuar y revisar');
  const summary=document.querySelector('main').innerText;
  for(const v of ['No lo sé','Omitido','0,00','Aún no preguntado']) assert(summary.includes(v),'summary missing '+v);
  assert(!localStorage.length && !sessionStorage.length,'automatic storage');
  location.hash='#privacidad'; await new Promise(r=>setTimeout(r,100));
  press('Guardar perfil local'); assert(!localStorage.length,'save without opt-in');
  document.querySelector('#profile-persist-toggle').click(); assert(!localStorage.length,'toggle alone writes');
  press('Guardar perfil local'); assert(localStorage.length===1,'save after opt-in');
  const confirm=window.confirm; window.confirm=()=>true; press('Revocar y borrar copia'); window.confirm=confirm;
  assert(!localStorage.length,'revocation does not erase');
  const requests=[]; const original=window.fetch; window.fetch=(u,o={})=>{requests.push({url:String(u),method:o.method||'GET',body:o.body||null});return original(u,o)};
  location.hash='#inicio'; await new Promise(r=>setTimeout(r,100));
  let m=document.querySelector('#chat-message'); m.value='Pregunta ficticia'; m.dispatchEvent(new Event('input',{bubbles:true})); m.form.requestSubmit();
  assert(!requests.length,'chat sent without consent'); document.querySelector('#chat-consent').click(); m.form.requestSubmit();
  assert(requests.length===1 && requests[0].url==='/api/chat','unexpected chat requests');
  const payload=JSON.parse(requests[0].body); assert(Object.keys(payload).sort().join(',')==='consent,message','profile included');
  window.fetch=original;
  return {pass:true,summary,requests,storage:localStorage.length};
})()