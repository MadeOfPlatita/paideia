// Las enumeraciones del chat tienen que ser listas de verdad, no números sueltos.
//
// Medido EN PANTALLA con captura real, pregunta por el colchón de emergencia: la
// respuesta llegaba así,
//
//     Cómo lo montaría yo, en 5 pasos. 1. Mide tus esenciales reales durante 2-3
//     meses… 2. Fija el objetivo en 3-6 meses… 3. Separa físicamente el dinero…
//
// y los cinco pasos salían PEGADOS dentro del párrafo, con los «2.» y «3.» a mitad
// de línea. La lista perdía por completo su estructura: no se podía seguir una
// secuencia de pasos.
//
// La causa: la numeración llega escrita en prosa, dentro de un párrafo de texto
// plano, y el render lo metía entero en un <p> sin reconocerla.
//
// Este test carga las funciones REALES de app.js (chatPlain, chatSteps y
// renderChatProse) sobre un DOM mínimo y exige <ol>/<li> donde hay enumeración, y
// prosa donde solo hay cifras. Cubre los DOS formatos que se ven en producción: la
// enumeración toda en un párrafo y un paso por párrafo.

'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const APP = path.join(__dirname, '..', 'static', 'app.js');

// DOM mínimo: acumula hijos y suma texto, como el que ya usan otros tests del chat.
function nodo(tag, attrs = {}, children = []) {
  const item = {
    tag,
    className: attrs.className || '',
    attrs,
    children: [],
    text: '',
    appendChild(child) { item.children.push(child); return child; },
  };
  Object.defineProperty(item, 'textContent', {
    get() { return item.text + item.children.map((c) => c.textContent).join(''); },
  });
  const lista = Array.isArray(children) ? children : [children];
  for (const child of lista) {
    if (typeof child === 'string' || typeof child === 'number') item.text += String(child);
    else if (child) item.children.push(child);
  }
  return item;
}

// Carga el bloque real del chat: chatPlain, chatSteps y renderChatProse viven
// seguidos, justo antes de chatMoney.
function cargar() {
  const src = fs.readFileSync(APP, 'utf8');
  const i = src.indexOf('function chatPlain');
  const j = src.indexOf('function chatMoney', i);
  assert.ok(i > 0 && j > i, 'no se encontró el bloque de prosa del chat en app.js');
  const ctx = { console, Number, String, Math };
  vm.createContext(ctx);
  ctx.el = (tag, attrs, children) => nodo(tag, attrs || {}, children === undefined ? [] : children);
  ctx.textElement = (tag, text, className) => nodo(tag, className ? { className } : {}, String(text));
  vm.runInContext(src.slice(i, j), ctx);
  assert.strictEqual(typeof ctx.chatSteps, 'function', 'debe existir chatSteps');
  assert.strictEqual(typeof ctx.renderChatProse, 'function', 'debe existir renderChatProse');
  return ctx;
}

// El mismo recorrido que hace el render: limpia el markdown, parte por línea en
// blanco y pinta los trozos. Así el test ejercita el camino real, no una copia.
function pintar(ctx, answer) {
  const contenedor = nodo('div', { id: 'chat-feedback' });
  ctx.renderChatProse(contenedor, ctx.chatPlain(answer).split(/\n\s*\n/));
  return contenedor;
}

const hijos = (contenedor, tag) => contenedor.children.filter((c) => c.tag === tag);
const items = (lista) => lista.children.filter((c) => c.tag === 'li').map((li) => li.textContent);

// La respuesta medida en pantalla, tal cual: los cinco pasos en un solo párrafo.
const COLCHON = [
  'Cómo lo montaría yo, en 5 pasos.',
  '1. Mide tus esenciales reales durante 2-3 meses (alquiler, comida, suministros, transporte, seguros, cuotas).',
  '2. Fija el objetivo en 3-6 meses de esos gastos, no en un número redondo que suene bien.',
  '3. Separa físicamente el dinero en una cuenta remunerada distinta de la del día a día.',
  '4. Automatiza una transferencia mensual el día que cobras, aunque sean 50 euros.',
  '5. Define qué es emergencia y qué no lo es antes de que llegue la primera.',
].join(' ');

test('la lista de 5 pasos del colchón se pinta como lista real de 5 items', () => {
  const ctx = cargar();
  const contenedor = pintar(ctx, COLCHON);
  const listas = hijos(contenedor, 'ol');
  assert.strictEqual(listas.length, 1, `debe haber una sola lista: ${JSON.stringify(contenedor.children.map((c) => c.tag))}`);
  const pasos = items(listas[0]);
  assert.strictEqual(pasos.length, 5, `deben ser 5 pasos, no ${pasos.length}: ${JSON.stringify(pasos)}`);
  // Y cada paso conserva su texto completo: no se pierde contenido al trocear.
  assert.match(pasos[0], /^Mide tus esenciales reales durante 2-3 meses/, pasos[0]);
  assert.match(pasos[0], /transporte, seguros, cuotas\)\.$/, pasos[0]);
  assert.match(pasos[1], /^Fija el objetivo en 3-6 meses de esos gastos/, pasos[1]);
  assert.match(pasos[2], /^Separa físicamente el dinero en una cuenta remunerada/, pasos[2]);
  assert.match(pasos[3], /^Automatiza una transferencia mensual el día que cobras/, pasos[3]);
  assert.match(pasos[4], /^Define qué es emergencia y qué no lo es/, pasos[4]);
  // El «N. » del marcador lo pinta el <ol>: no se duplica en el texto del item.
  for (const paso of pasos) assert.ok(!/^\d+\.\s/.test(paso), `queda el número en el texto: ${paso}`);
});

test('el texto anterior al «1.» va como párrafo propio, y el posterior a la lista también', () => {
  const ctx = cargar();
  const contenedor = pintar(ctx, COLCHON);
  const parrafos = hijos(contenedor, 'p').map((p) => p.textContent);
  assert.strictEqual(parrafos.length, 1, `un párrafo de entrada: ${JSON.stringify(parrafos)}`);
  assert.strictEqual(parrafos[0], 'Cómo lo montaría yo, en 5 pasos.');
  // Y el orden se respeta: párrafo primero, lista después.
  assert.strictEqual(contenedor.children[0].tag, 'p');
  assert.strictEqual(contenedor.children[1].tag, 'ol');

  // Con el cierre en su propio párrafo, el cierre queda como párrafo y no se come
  // un paso.
  const conCierre = pintar(ctx, `${COLCHON}\n\nY no hace falta más.`);
  const cierre = hijos(conCierre, 'p').map((p) => p.textContent);
  assert.strictEqual(cierre.length, 2, `debe quedar el cierre como párrafo: ${JSON.stringify(cierre)}`);
  assert.strictEqual(cierre[1], 'Y no hace falta más.');
  assert.strictEqual(items(hijos(conCierre, 'ol')[0]).length, 5, 'el cierre no se come un paso');

  // Y sin separación de párrafo no se pierde: sigue dentro del último paso, que es
  // donde el modelo lo escribió.
  const pegado = pintar(ctx, `${COLCHON} Y no hace falta más.`);
  assert.match(items(hijos(pegado, 'ol')[0])[4], /Y no hace falta más\.$/, 'no se pierde el texto');
});

test('los importes y las horas NO se confunden con numeración', () => {
  const ctx = cargar();
  const casos = [
    'Si dejas 2.000 € al 2 % acabas con 2.040 €.',
    'La cuota es un 3 % TAE y el cargo entra a las 12.30.',
    'Tienes 1.500 euros y el banco abre a las 9.00.',
    'Un 2,5 % de comisión sobre 3.000 euros son 75 euros.',
    'La TAE del depósito es 2.000 puntos básicos mayor que la del 1.500 €.',
  ];
  for (const texto of casos) {
    const contenedor = pintar(ctx, texto);
    assert.strictEqual(hijos(contenedor, 'ol').length, 0,
      `«${texto}» no es una lista: ${JSON.stringify(hijos(contenedor, 'ol'))}`);
    assert.deepStrictEqual(hijos(contenedor, 'p').map((p) => p.textContent), [texto],
      'el texto se conserva tal cual en un párrafo');
  }
});

test('una respuesta con dos listas da dos listas separadas', () => {
  const ctx = cargar();
  const answer = [
    'Primero, el orden de los pasos:',
    '1. Mide tus esenciales reales.',
    '2. Fija el objetivo en meses de gasto.',
    '',
    'Y después, el día a día:',
    '1. Separa el dinero en otra cuenta.',
    '2. Automatiza la transferencia el día de cobro.',
  ].join('\n');
  const contenedor = pintar(ctx, answer);
  const listas = hijos(contenedor, 'ol');
  assert.strictEqual(listas.length, 2, `deben ser dos listas: ${listas.length}`);
  assert.deepStrictEqual(items(listas[0]), ['Mide tus esenciales reales.', 'Fija el objetivo en meses de gasto.']);
  assert.deepStrictEqual(items(listas[1]), ['Separa el dinero en otra cuenta.', 'Automatiza la transferencia el día de cobro.']);
  // Y los dos encabezados quedan como párrafos, no dentro de la lista.
  const parrafos = hijos(contenedor, 'p').map((p) => p.textContent);
  assert.deepStrictEqual(parrafos, ['Primero, el orden de los pasos:', 'Y después, el día a día:']);
});

test('un solo «1.» no es una lista: se queda como párrafo', () => {
  const ctx = cargar();
  const contenedor = pintar(ctx, 'Solo hay un consejo. 1. Mide tus esenciales reales antes de invertir.');
  assert.strictEqual(hijos(contenedor, 'ol').length, 0,
    'un paso suelto no puede convertirse en lista');
  assert.strictEqual(hijos(contenedor, 'p').length, 1);
  assert.match(contenedor.textContent, /1\. Mide tus esenciales reales/, 'el texto no se pierde');
  // Tampoco si el «1.» va en su propio párrafo, que es como lo deja el backend.
  const aparte = pintar(ctx, 'Solo hay un consejo.\n\n1. Mide tus esenciales reales antes de invertir.');
  assert.strictEqual(hijos(aparte, 'ol').length, 0, 'un «1.» en su propio párrafo no es lista');
  assert.match(aparte.textContent, /1\. Mide tus esenciales reales/, 'y su número se conserva');
});

test('un paso por párrafo (formato del backend actual) también da una lista', () => {
  const ctx = cargar();
  // El backend abre un párrafo por paso numerado. Aislado, «1. Mide…» se leería
  // como prosa; con el «2.» detrás, es una lista.
  const answer = [
    'Cómo lo montaría yo, en 5 pasos.',
    '1. Mide tus esenciales reales durante 2-3 meses.',
    '2. Fija el objetivo en 3-6 meses de esos gastos.',
    '3. Separa físicamente el dinero en una cuenta remunerada.',
    '4. Automatiza una transferencia mensual el día que cobras.',
    '5. Define qué es emergencia y qué no lo es.',
  ].join('\n\n');
  const contenedor = pintar(ctx, answer);
  const listas = hijos(contenedor, 'ol');
  assert.strictEqual(listas.length, 1, `una sola lista: ${listas.length}`);
  assert.strictEqual(items(listas[0]).length, 5, JSON.stringify(items(listas[0])));
  assert.deepStrictEqual(hijos(contenedor, 'p').map((p) => p.textContent),
    ['Cómo lo montaría yo, en 5 pasos.']);
});

test('una frase de continuación entre dos pasos no parte la lista', () => {
  const ctx = cargar();
  // El backend admite hasta dos frases de continuación por paso, así que entre dos
  // pasos puede llegar una frase sin numeración. No puede romper la lista.
  const answer = [
    '1. Mide tus esenciales reales.',
    'Esa cifra es la base de todo lo demás.',
    '2. Fija el objetivo en meses de gasto.',
    '3. Separa el dinero en otra cuenta.',
  ].join('\n\n');
  const contenedor = pintar(ctx, answer);
  const listas = hijos(contenedor, 'ol');
  assert.strictEqual(listas.length, 1, `una sola lista: ${listas.length}`);
  const pasos = items(listas[0]);
  assert.strictEqual(pasos.length, 3, JSON.stringify(pasos));
  // La continuación se une a SU paso, no se convierte en un párrafo en medio.
  assert.match(pasos[0], /Esa cifra es la base de todo lo demás\.$/, pasos[0]);
});

test('una lista que el backend partió en dos párrafos sigue siendo una sola lista', () => {
  const ctx = cargar();
  const answer = [
    'Cómo lo montaría yo, en 4 pasos.',
    '1. Mide tus esenciales reales.',
    '2. Fija el objetivo en meses de gasto.',
    '',
    '3. Separa el dinero en otra cuenta.',
    '4. Automatiza la transferencia mensual.',
  ].join('\n');
  const contenedor = pintar(ctx, answer);
  const listas = hijos(contenedor, 'ol');
  assert.strictEqual(listas.length, 1, `la lista no se parte en dos: ${listas.length}`);
  assert.deepStrictEqual(items(listas[0]), [
    'Mide tus esenciales reales.',
    'Fija el objetivo en meses de gasto.',
    'Separa el dinero en otra cuenta.',
    'Automatiza la transferencia mensual.',
  ]);
});

test('la regresión se caza: pintar los pasos como texto plano ya no pasa el test', () => {
  const ctx = cargar();
  // El render antiguo: cada trozo, un <p> y nada más. Es lo que hacía que la lista
  // se viera pegada. Se reproduce aquí para demostrar que el caso de arriba lo
  // habría rechazado: si alguien vuelve al texto plano, este test se pone rojo.
  const contenedorViejo = nodo('div', { id: 'chat-feedback' });
  for (const trozo of ctx.chatPlain(COLCHON).split(/\n\s*\n/)) {
    const texto = trozo.trim();
    if (texto) contenedorViejo.appendChild(nodo('p', {}, texto));
  }
  assert.strictEqual(hijos(contenedorViejo, 'ol').length, 0, 'el render viejo no generaba listas');
  assert.match(hijos(contenedorViejo, 'p')[0].textContent, /pasos\. 1\. Mide .* 2\. Fija/,
    'y los números quedaban a mitad del párrafo, que es lo medido en pantalla');

  // Y el código de app.js ya no usa ese camino: los dos sitios que pintan
  // `result.answer` llaman a renderChatProse.
  const src = fs.readFileSync(APP, 'utf8');
  const planos = src.split('feedback.appendChild(textElement("p", texto))').length - 1;
  assert.strictEqual(planos, 0,
    'el render de la respuesta no puede volver a pintar cada trozo como párrafo plano');
  const llamadas = src.split('renderChatProse(feedback, chatPlain(result.answer)').length - 1;
  assert.strictEqual(llamadas, 2, `los dos caminos de la respuesta deben pintar la prosa: ${llamadas}`);
  // Y los bloques se cuelgan del contenedor del chat directamente, sin <div> de por
  // medio: el CSS usa selectores de hijo directo (#chat-feedback > p).
  const contenedor = pintar(ctx, COLCHON);
  for (const hijo of contenedor.children) {
    assert.ok(['p', 'ol'].indexOf(hijo.tag) !== -1, `hijo inesperado en el chat: ${hijo.tag}`);
  }
});

test('chatSteps no inventa pasos en texto vacío ni con valores raros', () => {
  const ctx = cargar();
  for (const valor of [null, undefined, 42, '', '   ']) {
    assert.strictEqual(ctx.chatSteps(valor).length, 0, `no debe haber pasos en ${valor}`);
  }
  for (const valor of [null, undefined, 42, '', '   ']) {
    const contenedor = nodo('div', {});
    ctx.renderChatProse(contenedor, [valor]);
    assert.strictEqual(contenedor.children.length, 0, `no debe pintar nada para ${valor}`);
  }
  // Un párrafo normal sale como un único <p>.
  const contenedor = pintar(ctx, 'La TAE incluye comisiones.');
  assert.deepStrictEqual(contenedor.children.map((c) => c.tag), ['p']);
});
