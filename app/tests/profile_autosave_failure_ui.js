(async () => {
  const assert = (v, m) => { if (!v) throw Error(m); };
  const press = t => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t); assert(b && !b.disabled, 'button ' + t); b.click(); };
  const wait = () => new Promise(r => setTimeout(r, 100));
  localStorage.clear(); sessionStorage.clear(); location.hash = '#perfil'; await wait();
  press('No lo sé'); press('Continuar'); press('Omitir'); press('Continuar'); press('Omitir'); press('Continuar'); press('Omitir'); press('Continuar');
  const amount = document.querySelector('main input[type=text]'); amount.value = '0'; amount.form.requestSubmit(); press('Continuar y revisar');
  location.hash = '#privacidad'; await wait(); document.querySelector('#profile-persist-toggle').click(); press('Guardar perfil local');
  const key = PaideiaProfileModel.STORAGE_KEY; const old = localStorage.getItem(key); assert(old, 'initial snapshot missing');
  location.hash = '#perfil'; await wait();
  const row = [...document.querySelectorAll('.profile-summary-row')].find(x => x.innerText.includes('0,00')); assert(row, 'zero missing'); row.querySelector('button').click();
  const original = Storage.prototype.setItem;
  Storage.prototype.setItem = function(k,v) { if (k === key) throw Error('synthetic quota failure'); return original.call(this,k,v); };
  try {
    const input = document.querySelector('main input[type=text]'); input.value = '123'; input.form.requestSubmit();
    assert(localStorage.getItem(key) === old, 'snapshot unexpectedly changed');
    assert(document.querySelector('main').innerText.includes('123,00'), 'memory value missing');
    const warning = document.querySelector('#profile-autosave-warning');
    assert(warning && /no se pudo/i.test(warning.innerText) && /antigu|anterior/i.test(warning.innerText) && /recarg/i.test(warning.innerText), 'immediate stale snapshot warning missing');
    location.hash = '#biblioteca'; await wait(); assert(document.querySelector('#profile-autosave-warning'), 'warning missing on another screen');
    press('Reintentar guardado local'); assert(document.querySelector('#profile-autosave-warning'), 'failed retry hid warning');
    return {pass:true,warning:document.querySelector('#profile-autosave-warning').innerText,oldSnapshotUnchanged:true};
  } finally { Storage.prototype.setItem = original; }
})()