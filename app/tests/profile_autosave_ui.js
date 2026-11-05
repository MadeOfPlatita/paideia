(async () => {
  const assert = (v, m) => { if (!v) throw Error(m); };
  const press = t => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t); assert(b && !b.disabled, 'button ' + t); b.click(); };
  const wait = () => new Promise(r => setTimeout(r, 100));
  if (sessionStorage.getItem('autosave-test')) {
    const before = sessionStorage.getItem('autosave-before');
    const after = sessionStorage.getItem('autosave-after');
    location.hash = '#perfil'; await wait();
    const summary = document.querySelector('main').innerText;
    assert(summary.includes('123,00'), 'changed answer absent after reload: ' + summary);
    assert(/automáticamente/i.test(before) && /cambios posteriores/i.test(before) && /navegador/i.test(before), 'missing pre-opt-in autosave notice: ' + before);
    assert(/automáticamente/i.test(after) && /cambios posteriores/i.test(after) && /navegador/i.test(after), 'missing save confirmation autosave notice: ' + after);
    assert(!/se escribe solo al pulsar Guardar/i.test(before), 'misleading single-write claim');
    sessionStorage.clear(); localStorage.clear();
    return {pass: true, before, after, persisted: '123,00'};
  }
  assert(!localStorage.length && !sessionStorage.length, 'isolated origin required');
  location.hash = '#perfil'; await wait();
  press('No lo sé'); press('Omitir'); press('Omitir'); press('Omitir');
  const input = document.querySelector('main input[type=text]'); assert(input, 'amount'); input.value = '0'; input.form.requestSubmit(); press('Pausar y ver el resumen');
  assert(!localStorage.length, 'saved before opt-in');
  location.hash = '#privacidad'; await wait();
  const before = document.querySelector('main').innerText;
  document.querySelector('#profile-persist-toggle').click(); assert(!localStorage.length, 'toggle wrote data');
  press('Guardar perfil local');
  const after = document.querySelector('#profile-storage-feedback').innerText;
  assert(localStorage.getItem(PaideiaProfileModel.STORAGE_KEY), 'save missing');
  location.hash = '#perfil'; await wait();
  const row = [...document.querySelectorAll('.profile-summary-row')].find(x => x.innerText.includes('0,00')); assert(row, 'amount summary');
  const edit = row.querySelector('button'); assert(edit, 'edit amount'); edit.click();
  const changed = document.querySelector('main input[type=text]'); assert(changed, 'edit input'); changed.value = '123'; changed.form.requestSubmit();
  assert(document.querySelector('main').innerText.includes('123,00'), 'answer not changed');
  sessionStorage.setItem('autosave-before', before); sessionStorage.setItem('autosave-after', after); sessionStorage.setItem('autosave-test', '1');
  return {reloadRequired: true};
})()