(async () => {
  // Synthetic-only: run after profile_partial_delete_ui.js and a real reload.
  const assert = (v, m) => { if (!v) throw Error(m); };
  const press = t => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t); assert(b && !b.disabled, 'button ' + t); b.click(); };
  const wait = () => new Promise(r => setTimeout(r, 100));
  const key = PaideiaProfileModel.STORAGE_KEY, old = localStorage.getItem(key);
  assert(old && JSON.parse(old).profile, 'retained copy missing');
  assert(!document.querySelector('#profile-persist-toggle').checked, 'reload restored permission');
  const notice = document.querySelector('main').innerText;
  assert(/copia guardada/i.test(notice) && /desactivado tras recargar/i.test(notice), 'retained copy warning missing');
  assert(/independiente del procesamiento local/i.test(notice) && /ningún envío remoto/i.test(notice), 'privacy separation missing');
  const original = Storage.prototype.setItem; let writes = 0;
  Storage.prototype.setItem = function(k, v) { if (k === key) writes++; return original.call(this, k, v); };
  try {
    location.hash = '#perfil'; await wait();
    const row = [...document.querySelectorAll('.profile-summary-row')].find(x => x.innerText.includes('0,00'));
    assert(row, 'retained zero not visible'); row.querySelector('button').click();
    const input = document.querySelector('main input[type=text]'); assert(input, 'amount editor'); input.value = '456'; input.form.requestSubmit();
    assert(document.querySelector('main').innerText.includes('456,00'), 'edit not shown');
    assert(writes === 0 && localStorage.getItem(key) === old, 'edit automatically wrote without permission');
    location.hash = '#privacidad'; await wait();
    const toggle = document.querySelector('#profile-persist-toggle'); assert(!toggle.checked, 'permission restored'); toggle.click();
    assert(writes === 0 && localStorage.getItem(key) === old, 'checkbox alone wrote');
    press('Guardar perfil local');
    assert(writes === 1 && localStorage.getItem(key).includes('456'), 'explicit save failed');
    return {retainedZero:true, edit456NoWrite:true, checkboxNoWrite:true, explicitSaveWrites:writes, notice};
  } finally { Storage.prototype.setItem = original; }
})()