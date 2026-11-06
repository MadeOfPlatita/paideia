(async () => {
  const assert = (v, m) => { if (!v) throw Error(m); };
  const press = t => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t); assert(b && !b.disabled, 'button ' + t); b.click(); };
  localStorage.clear(); sessionStorage.clear();
  location.hash = '#perfil'; await new Promise(r => setTimeout(r, 100));
  press('No lo sé'); press('Continuar'); press('Omitir'); press('Continuar'); press('Omitir'); press('Continuar'); press('Omitir'); press('Continuar');
  const input = document.querySelector('main input[type=text]'); assert(input, 'amount'); input.value = '0'; input.form.requestSubmit(); press('Continuar y revisar');
  location.hash = '#privacidad'; await new Promise(r => setTimeout(r, 100));
  const legacy = PaideiaProfileModel.LEGACY_STORAGE_KEYS[0];
  localStorage.setItem(legacy, 'synthetic legacy');
  const original = Storage.prototype.removeItem;
  Storage.prototype.removeItem = function(key) { if (key === legacy) throw Error('synthetic failure'); return original.call(this, key); };
  document.querySelector('#profile-persist-toggle').click(); press('Guardar perfil local');
  const feedback = document.querySelector('#profile-storage-feedback').innerText;
  const status = document.querySelector('#profile-storage-state').innerText;
  assert(localStorage.getItem(PaideiaProfileModel.STORAGE_KEY), 'current snapshot missing');
  assert(localStorage.getItem(legacy), 'legacy fixture missing');
  assert(!/solo en memoria/i.test(feedback + status), 'false memory-only claim: ' + feedback + ' / ' + status);
  assert(/guardad/i.test(feedback) && /anterior|antigu|copias/i.test(feedback), 'missing partial save warning: ' + feedback);
  Storage.prototype.removeItem = original;
  return {feedback, status};
})()