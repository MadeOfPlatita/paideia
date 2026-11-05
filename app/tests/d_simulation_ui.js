(async () => {
  const assert = (ok, message) => { if (!ok) throw Error(message); };
  const button = text => [...document.querySelectorAll('button')].find(b => b.textContent.trim() === text);
  const press = text => { const b=button(text); assert(b && !b.disabled, 'button unavailable: '+text); b.click(); };
  const select=document.querySelector('#simulation-product');
  assert(select && [...select.options].some(o=>o.value==='fixture-d'), 'synthetic catalogue missing');
  select.value='fixture-d'; select.dispatchEvent(new Event('change',{bubbles:true})); press('Elegir referencia');
  assert(document.body.innerText.includes('Tipo desconocido'), 'unknown conditions missing');
  press('Continuar con el importe ficticio');
  let input=document.querySelector('#simulation-amount'); input.value='100'; input.form.requestSubmit();
  let check=document.querySelector('#simulation-understood');
  assert(check && !check.checked && button('Terminar ensayo y crear justificante').disabled, 'confirmation must start unchecked');
  check.click(); press('Volver');
  input=document.querySelector('#simulation-amount'); input.value='200'; input.form.requestSubmit();
  check=document.querySelector('#simulation-understood');
  assert(!check.checked && button('Terminar ensayo y crear justificante').disabled, 'RED: previous acknowledgement survives changed amount');
  check.click(); press('Terminar ensayo y crear justificante');
  const receipt=document.querySelector('[data-printable="receipt"]');
  assert(receipt && receipt.innerText.includes('ENSAYO FICTICIO') && receipt.innerText.includes('200'), 'receipt missing fictitious amount');
  assert(receipt.innerText.includes('no es un contrato'), 'receipt lacks non-contract warning');
  assert(localStorage.length===0 && sessionStorage.length===0, 'automatic browser storage');
  return {pass:true, receipt:receipt.innerText, storage:localStorage.length, url:location.href};
})()