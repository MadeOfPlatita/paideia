(async () => {
  const assert = (v, m) => { if (!v) throw Error(m); };
  const press = t => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t); assert(b && !b.disabled, 'button ' + t); b.click(); };
  const model = PaideiaProfileModel;
  const current = localStorage.getItem(model.STORAGE_KEY);
  assert(current, 'reload lost current snapshot');
  const answer = model.getAnswer(JSON.parse(current).profile, 'detalle_economico.importe_objetivo');
  assert(answer.estado === 'declarado' && answer.valor.min_eur === '0', 'reload lost declared zero');
  assert(!document.querySelector('#profile-persist-toggle').checked, 'reload restored opt-in');
  assert(/incompleto|desconocido/i.test(document.querySelector('#profile-storage-state').innerText), 'residue not reported after reload');
  assert(document.querySelector('main').innerText.includes('copias'), 'no warning');
  const origRemove = Storage.prototype.removeItem, origConfirm = window.confirm;
  Storage.prototype.removeItem = function(key) { if (key === model.STORAGE_KEY) throw Error('synthetic delete failure'); return origRemove.call(this, key); };
  window.confirm = () => true;
  try {
    press('Revocar y borrar copia');
    const text = document.querySelector('#profile-storage-state').innerText + ' ' + document.querySelector('#profile-storage-feedback').innerText;
    assert(!/solo memoria|solo en memoria|copia local borrada/i.test(text), 'false delete claim: ' + text);
    assert(/no se pudo borrar/i.test(text), 'delete failure missing');
    assert(localStorage.getItem(model.STORAGE_KEY) === current, 'fixture did not retain current');
    assert(!document.querySelector('#profile-persist-toggle').checked, 'consent not revoked');
    return {partial:text, answer};
  } finally { Storage.prototype.removeItem = origRemove; window.confirm = origConfirm; }
})()