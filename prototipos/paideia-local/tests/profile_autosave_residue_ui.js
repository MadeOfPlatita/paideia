(async () => {
  const assert = (v, m) => { if (!v) throw Error(m); };
  const press = t => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t); assert(b && !b.disabled, 'button ' + t); b.click(); };
  const wait = () => new Promise(r => setTimeout(r, 120));
  const model = PaideiaProfileModel, key = model.STORAGE_KEY, legacy = model.LEGACY_STORAGE_KEYS[0];
  const warning = () => { const w = document.querySelector('#profile-autosave-warning'); assert(w && w.getBoundingClientRect().height > 0 && w.getBoundingClientRect().bottom > 0 && w.getBoundingClientRect().top < innerHeight && getComputedStyle(w).visibility === 'visible', 'global warning not visible in viewport'); return w.innerText; };
  if (sessionStorage.getItem('residue-reload')) {
    assert(localStorage.getItem(legacy) === 'synthetic legacy', 'legacy residue not retained');
    const snapshot = JSON.parse(localStorage.getItem(key));
    assert(JSON.stringify(snapshot).includes('123'), 'current snapshot missing edited value after reload');
    assert(/copias|anteriores|antigu/i.test(warning()), 'reload warning missing residue');
    location.hash = '#perfil'; await wait();
    assert(document.querySelector('main').innerText.includes('123,00'), 'reload did not show new value');
    assert(/copias|anteriores|antigu/i.test(warning()), 'warning lost after navigation');
    // Reload no longer carries permission: retry requires a fresh deliberate save.
    location.hash = '#privacidad'; await wait();
    const toggle = document.querySelector('#profile-persist-toggle');
    assert(!toggle.checked, 'reload restored permission');
    toggle.click(); press('Guardar perfil local');
    assert(!localStorage.getItem(legacy), 'successful retry retained legacy');
    assert(!document.querySelector('#profile-autosave-warning'), 'warning remains after successful retry');
    sessionStorage.clear(); localStorage.clear();
    return {pass: true, reloadShowsNewValue: true, retryRemovedResidue: true};
  }
  assert(!localStorage.length && !sessionStorage.length, 'isolated empty origin required');
  location.hash = '#perfil'; await wait();
  press('No lo sé'); press('Omitir'); press('Omitir'); press('Omitir');
  const initial = document.querySelector('main input[type=text]'); initial.value = '0'; initial.form.requestSubmit(); press('Pausar y ver el resumen');
  location.hash = '#privacidad'; await wait(); document.querySelector('#profile-persist-toggle').click(); press('Guardar perfil local');
  const old = localStorage.getItem(key); assert(old, 'initial snapshot absent');
  location.hash = '#perfil'; await wait();
  const row = [...document.querySelectorAll('.profile-summary-row')].find(x => x.innerText.includes('0,00')); assert(row, 'initial value absent'); row.querySelector('button').click();
  localStorage.setItem(legacy, 'synthetic legacy');
  const original = Storage.prototype.removeItem;
  Storage.prototype.removeItem = function(k) { if (k === legacy) throw Error('synthetic removal failure'); return original.call(this, k); };
  try {
    const input = document.querySelector('main input[type=text]'); input.value = '123'; input.form.requestSubmit();
    const snapshot = localStorage.getItem(key); assert(snapshot && snapshot !== old && snapshot.includes('123'), 'new snapshot not written');
    assert(localStorage.getItem(legacy) === 'synthetic legacy', 'residue missing');
    const text = warning();
    assert(/guardad/i.test(text) && /copias|anteriores|antigu/i.test(text), 'warning must disclose written snapshot and legacy residue: ' + text);
    assert(!/perder esos cambios|versión anterior/i.test(text), 'incorrect stale snapshot warning: ' + text);
    location.hash = '#biblioteca'; await wait(); assert(/copias|anteriores|antigu/i.test(warning()), 'warning lost on other screen');
    press('Reintentar guardado local'); assert(/copias|anteriores|antigu/i.test(warning()), 'failed retry hid warning');
    sessionStorage.setItem('residue-reload', '1');
    return {reloadRequired: true, immediateWarning: text, snapshotUpdated: true};
  } finally { Storage.prototype.removeItem = original; }
})()