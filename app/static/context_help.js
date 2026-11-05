/* Ayuda contextual local, sin datos ni servicios externos.
 * API global ContextHelp:
 * definitions: objeto congelado {clave: {label, definition}} compartido con el glosario.
 * createHelp(clave): devuelve un <span> independiente listo para insertar; clave desconocida lanza RangeError.
 * mount(root, {terms}): añade una ayuda por clave y devuelve los elementos creados.
 * Las claves son tae, tin, liquidez, riesgo, inflacion e interes-compuesto.
 * Cada ayuda es un desplegable en línea no modal; Escape o Cerrar devuelven el foco al botón.
 */
(function (global) {
  'use strict';
  const definitions = Object.freeze({
    tae: Object.freeze({label: 'TAE', definition: 'La tasa anual equivalente expresa el coste o rendimiento anual según unos supuestos, incluyendo la frecuencia de los pagos y ciertos gastos. No describe por sí sola todas las condiciones.'}),
    tin: Object.freeze({label: 'TIN', definition: 'El tipo de interés nominal es el porcentaje de interés pactado, sin incorporar por sí mismo todos los gastos ni el efecto de la frecuencia de los pagos.'}),
    liquidez: Object.freeze({label: 'Liquidez', definition: 'Es la facilidad para disponer del dinero o convertir un activo en dinero, teniendo en cuenta el tiempo y los posibles costes o pérdidas.'}),
    riesgo: Object.freeze({label: 'Riesgo', definition: 'Es la posibilidad de que el resultado sea distinto del esperado, incluida la posibilidad de perder parte o todo el dinero invertido.'}),
    inflacion: Object.freeze({label: 'Inflación', definition: 'Es la subida general y sostenida de los precios. Si los ingresos o ahorros crecen menos que los precios, pueden perder poder de compra.'}),
    'interes-compuesto': Object.freeze({label: 'Interés compuesto', definition: 'Se produce cuando los intereses acumulados también generan intereses en periodos posteriores. El resultado depende del tipo, el tiempo y las condiciones.'})
  });
  let sequence = 0;
  function createHelp(key) {
    if (!Object.hasOwn(definitions, key)) throw new RangeError('Término de ayuda desconocido');
    const item = definitions[key];
    const wrapper = document.createElement('span');
    wrapper.className = 'context-help';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'context-help__trigger';
    button.textContent = '?';
    button.setAttribute('aria-label', 'Ayuda: ' + item.label);
    button.setAttribute('aria-expanded', 'false');
    const panel = document.createElement('span');
    panel.className = 'context-help__panel';
    panel.id = 'context-help-' + (++sequence);
    panel.hidden = true;
    button.setAttribute('aria-controls', panel.id);
    const text = document.createElement('span');
    text.textContent = item.label + ': ' + item.definition;
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'context-help__close';
    close.textContent = 'Cerrar';
    close.setAttribute('aria-label', 'Cerrar ayuda: ' + item.label);
    function setOpen(open, restore) {
      panel.hidden = !open;
      button.setAttribute('aria-expanded', String(open));
      if (restore) button.focus();
    }
    button.addEventListener('click', () => setOpen(panel.hidden, false));
    close.addEventListener('click', () => setOpen(false, true));
    wrapper.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !panel.hidden) { event.preventDefault(); event.stopPropagation(); setOpen(false, true); }
    });
    panel.append(text, document.createTextNode(' '), close);
    wrapper.append(button, panel);
    return wrapper;
  }
  function mount(root, options) {
    const terms = options && options.terms;
    if (!root || typeof root.append !== 'function' || !Array.isArray(terms)) throw new TypeError('Se necesitan un nodo raíz y una lista de términos');
    const elements = terms.map(createHelp);
    root.append(...elements);
    return elements;
  }
  global.ContextHelp = Object.freeze({definitions, createHelp, mount});
})(window);
