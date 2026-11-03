(() => {
  const assert = (v, m) => { if (!v) throw Error(m); };
  const model = PaideiaProfileModel;
  assert(localStorage.getItem(model.STORAGE_KEY), 'partial delete did not survive reload');
  assert(/copia guardada/i.test(document.querySelector('#profile-storage-feedback').innerText), 'reload must disclose surviving copy');
  assert(!document.querySelector('#profile-persist-toggle').checked, 'reload restored consent');
  const original = window.confirm; window.confirm = () => true;
  try {
    const button = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Revocar y borrar copia');
    assert(button, 'delete button missing'); button.click();
    assert(!localStorage.getItem(model.STORAGE_KEY), 'current remains');
    for (const key of model.LEGACY_STORAGE_KEYS) assert(!localStorage.getItem(key), 'legacy remains');
    const feedback = document.querySelector('#profile-storage-feedback').innerText;
    assert(/copia local borrada/i.test(feedback), 'success missing');
    return {feedback, keys: localStorage.length};
  } finally { window.confirm = original; }
})()