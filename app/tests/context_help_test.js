(() => {
  const results = [];
  function test(name, fn) { try { fn(); results.push('PASS ' + name); } catch (e) { results.push('FAIL ' + name + ': ' + e.message); } }
  function assert(value, message) { if (!value) throw new Error(message); }
  test('existe API pública y seis definiciones cerradas', () => {
    const api = window.ContextHelp;
    assert(api && typeof api.mount === 'function' && typeof api.createHelp === 'function', 'falta ContextHelp.mount/createHelp');
    const keys = ['tae', 'tin', 'liquidez', 'riesgo', 'inflacion', 'interes-compuesto'];
    assert(Object.isFrozen(api.definitions) && Object.keys(api.definitions).join(',') === keys.join(','), 'catálogo incorrecto o mutable');
    for (const key of keys) assert(Object.isFrozen(api.definitions[key]) && api.definitions[key].label && api.definitions[key].definition, key);
  });
  const fixture = document.getElementById('fixture');
  test('mount crea ayudas independientes con controles accesibles', () => {
    const items = ContextHelp.mount(fixture, {terms: ['tae', 'riesgo', 'interes-compuesto']});
    assert(items.length === 3 && fixture.children.length === 3, 'número incorrecto');
    const buttons = items.map(item => item.querySelector('button'));
    const ids = buttons.map(button => button.getAttribute('aria-controls'));
    assert(new Set(ids).size === 3, 'IDs duplicados');
    for (const b of buttons) assert(b.type === 'button' && b.getAttribute('aria-expanded') === 'false' && document.getElementById(b.getAttribute('aria-controls')).hidden, 'estado cerrado incorrecto');
  });
  test('abrir y cerrar restaura el foco', () => {
    const first = fixture.firstElementChild, b = first.querySelector('button');
    const panel = document.getElementById(b.getAttribute('aria-controls'));
    b.click(); assert(!panel.hidden && b.getAttribute('aria-expanded') === 'true', 'no abre');
    const close = panel.querySelector('button'); close.focus(); close.click();
    assert(panel.hidden && b.getAttribute('aria-expanded') === 'false' && document.activeElement === b, 'no cierra o no restaura foco');
  });
  test('Escape cierra y restaura el foco', () => {
    const first = fixture.firstElementChild, b = first.querySelector('button');
    b.click(); const panel = document.getElementById(b.getAttribute('aria-controls'));
    panel.querySelector('button').focus();
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
    assert(panel.hidden && document.activeElement === b && b.getAttribute('aria-expanded') === 'false', 'Escape no cierra');
  });
  test('las entradas desconocidas se rechazan sin inserción parcial', () => {
    const before = fixture.children.length;
    let rejected = false; try { ContextHelp.mount(fixture, {terms:['tae', '<img src=x onerror=alert(1)>']}); } catch(e) { rejected = e instanceof RangeError; }
    assert(rejected && fixture.children.length === before && !fixture.querySelector('img'), 'entrada no rechazada');
  });
  test('createHelp devuelve un elemento independiente', () => {
    const el = ContextHelp.createHelp('inflacion');
    assert(!el.isConnected && el.querySelector('button').getAttribute('aria-label').includes('Inflación'), 'elemento no válido');
  });
  document.getElementById('results').textContent = results.join('\n');
  document.body.dataset.testStatus = results.some(r => r.startsWith('FAIL')) ? 'fail' : 'pass';
})();
