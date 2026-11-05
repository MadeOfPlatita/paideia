(async () => {
  // Synthetic-only: run after profile_autosave_failure_ui.js and a real reload.
  const assert = (v,m) => { if (!v) throw Error(m); };
  const press = t => { const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim()===t); assert(b && !b.disabled,'button '+t); b.click(); };
  const wait=()=>new Promise(r=>setTimeout(r,100));
  const key=PaideiaProfileModel.STORAGE_KEY;
  if (sessionStorage.getItem('retry-test-reload')) {
    location.hash='#perfil'; await wait();
    assert(document.querySelector('main').innerText.includes('123,00'), 'retried value absent after reload');
    location.hash='#privacidad'; await wait();
    assert(!document.querySelector('#profile-persist-toggle').checked, 'permission survived second reload');
    sessionStorage.removeItem('retry-test-reload');
    return {pass:true, retriedValuePersisted:true, permissionReset:true};
  }
  const old=localStorage.getItem(key); assert(old, 'old snapshot missing');
  location.hash='#perfil'; await wait();
  const row=[...document.querySelectorAll('.profile-summary-row')].find(x=>x.innerText.includes('0,00'));
  assert(row && !document.querySelector('main').innerText.includes('123,00'),'reload must show old zero snapshot');
  location.hash='#privacidad'; await wait();
  const toggle=document.querySelector('#profile-persist-toggle');
  assert(toggle && !toggle.checked, 'reload restored permission');
  const original=Storage.prototype.setItem; let writes=0;
  Storage.prototype.setItem=function(k,v){if(k===key) writes++; return original.call(this,k,v)};
  try {
    toggle.click();
    assert(writes===0 && localStorage.getItem(key)===old, 'checkbox alone wrote');
    press('Guardar perfil local');
    assert(writes===1 && localStorage.getItem(key)===old, 'explicit save did not enable persistence of old snapshot');
  } finally { Storage.prototype.setItem=original; }
  location.hash='#perfil'; await wait();
  const editRow=[...document.querySelectorAll('.profile-summary-row')].find(x=>x.innerText.includes('0,00'));
  assert(editRow, 'zero row missing'); editRow.querySelector('button').click();
  Storage.prototype.setItem=function(k,v){if(k===key) throw Error('synthetic failure'); return original.call(this,k,v)};
  try {
    const input=document.querySelector('main input[type=text]'); input.value='123'; input.form.requestSubmit();
    assert(localStorage.getItem(key)===old, 'failed autosave changed snapshot');
    assert(document.querySelector('main').innerText.includes('123,00'), 'edited value missing in memory');
    assert(document.querySelector('#profile-autosave-warning'),'warning absent');
    location.hash='#inicio'; await wait();
    press('Reintentar guardado local'); assert(document.querySelector('#profile-autosave-warning'),'retry failure hidden');
    assert(localStorage.getItem(key)===old, 'failed retry changed snapshot');
  } finally { Storage.prototype.setItem=original; }
  press('Reintentar guardado local'); assert(!document.querySelector('#profile-autosave-warning'),'warning remains after success');
  assert(localStorage.getItem(key).includes('123'), 'successful retry did not persist edited value');
  sessionStorage.setItem('retry-test-reload','1');
  return {reloadRequired:true, reloadedOldZero:true, checkboxNoWrite:true, explicitSaveEnabled:true, retrySucceeded:true};
})()