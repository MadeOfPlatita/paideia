(async () => {
  const results = [];
  const check = (name, ok, detail) => results.push({name, pass: !!ok, detail});
  const ack = document.querySelector('#preview-acknowledged');
  const confirm = document.querySelector('#preview-confirm');
  ack.click(); confirm.click();
  const confirmed = document.querySelector('#preview-result').textContent;
  ack.click();
  const cleared = document.querySelector('#preview-result').textContent;
  check('preview withdrawal updates visible status immediately', !ack.checked && confirm.disabled && /Sin confirmación/.test(cleared) && !/recordad/.test(cleared), {confirmed, cleared});
  const originalFetch = window.fetch;
  let release;
  window.fetch = (...args) => String(args[0]).includes('/api/catalogue') ? new Promise(resolve => { release = () => resolve(new Response(JSON.stringify({items:[]}), {status:200,headers:{'Content-Type':'application/json'}})); }) : originalFetch(...args);
  location.hash = '#simulacion';
  await new Promise(resolve => setTimeout(resolve, 150));
  const holder = document.querySelector('#simulation-candidates');
  const loading = holder?.innerText;
  check('catalogue loading is visibly neutral', holder?.getAttribute('aria-busy') === 'true' && /candidatos del catálogo/.test(loading) && !/reales/i.test(loading), {loading});
  if (release) release();
  window.fetch = originalFetch;
  return results;
})()