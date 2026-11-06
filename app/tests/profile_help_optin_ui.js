(async () => {
  const assert = (v, m) => { if (!v) throw Error(m); };
  const press = t => { const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === t); assert(b && !b.disabled, 'button ' + t); b.click(); };
  const wait = () => new Promise(r => setTimeout(r, 100));
  localStorage.clear(); location.hash = '#perfil'; await wait();
  press('No lo sé'); press('Continuar'); press('Omitir'); press('Continuar'); press('Omitir'); press('Continuar'); press('Omitir'); press('Continuar');
  const input = document.querySelector('main input[type=text]'); input.value = '0'; input.form.requestSubmit(); press('Continuar y revisar');
  location.hash = '#privacidad'; await wait(); document.querySelector('#profile-persist-toggle').click(); press('Guardar perfil local');
  location.hash = '#perfil'; await wait(); press('Continuar donde lo dejé');
  const help = document.querySelector('.why-question').textContent;
  assert(/automáticamente/i.test(help) && /navegador|dispositivo/i.test(help), 'help must disclose opt-in autosave: ' + help);
  assert(!/solo queda en memoria/i.test(help), 'help falsely says memory-only: ' + help);
  assert(/no autoriza.*remot|no se envía|no.*envío remoto/i.test(help), 'help must distinguish remote processing: ' + help);
  return {pass:true, help};
})()