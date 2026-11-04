"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Execute the actual chat section and request helper with a small targeted element shim.
// La puerta de envío aceptada en B8 exige un estado de IA concluyente: sin
// `ai.status` reconocible la app no envía nada. El valor por defecto refleja un
// proveedor configurado con mapa e historial disponibles.
const DEFAULT_STATUS = {ai: {status: 'configured_not_verified', capabilities: {context: true, history: true, structured_education: false}}};

function setup(fetch, status = DEFAULT_STATUS, hooks = {}) {
  const code = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
  const byId = {};
  class Node {
    constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this.text = ''; this.checked = false; this.value = ''; }
    setAttribute(k, v) { this[k] = v; if (k === 'id') byId[v] = this; }
    appendChild(n) { this.children.push(n); return n; }
    append(...nodes) { nodes.forEach(n => this.appendChild(n)); }
    replaceChildren(...nodes) { this.children = nodes; this.text = ''; }
    addEventListener(event, fn) { this.listeners[event] = fn; }
    querySelector(selector) { return selector === '.field-help' ? this.children.find(x => x.className === 'field-help') : null; }
    focus() {}
    set textContent(s) { this.text = String(s); this.children = []; }
    get textContent() { return this.text + this.children.map(n => n.textContent).join(''); }
  }
  const document = {createElement: tag => new Node(tag), createTextNode: text => { const n = new Node('#text'); n.textContent = text; return n; }, getElementById: id => byId[id]};
  const ctx = { document, fetch, URL, console, PaideiaChatContext: require('../static/chat_context_model.js'), PaideiaStructuredEducation: require('../static/structured_education_ui.js'), PROFILE_MODEL: require('../static/profile_model.js'), state: {chatMessage:'', chatTicket:null, chatTicketQuery:null, chatBusy:false, chatUncertain:false, chatUncertainQuery:null, chatUncertainTicket:false, status, profile: require('../static/profile_model.js').createEmptyProfile()}, API: {chat:'/api/chat'}, ...hooks };
  vm.createContext(ctx);
  const common = code.slice(code.indexOf('function isSafePrimaryUrl'), code.indexOf('const state =')) + code.slice(code.indexOf('function el('), code.indexOf('function setStatusChip')) + code.slice(code.indexOf('function displayProfileValue'), code.indexOf('function formatCurrency', code.indexOf('function displayProfileValue'))) + code.slice(code.indexOf('function apiErrorText'), code.indexOf('function errorBox'));
  const start = code.indexOf('  const chat = section("Pregunta a Pai"');
  const chat = code.slice(start, code.indexOf('  if (state.storageNotice)', start));
  vm.runInContext(common + '\nfunction section(){ return el("section"); }\nfunction callout(s){ return el("div",{},s); }\nconst page = el("main");\n' + chat + '\nglobalThis.form = form; globalThis.submit = submit; globalThis.message = message; globalThis.feedback = feedback;', ctx);
  return {...ctx, byId, consent: byId['chat-consent'], async send() { return ctx.form.listeners.submit({preventDefault(){}}); }, input(value) {ctx.message.value = value; ctx.message.listeners.input();}};
}
function response(status, body) { return {ok:status >= 200 && status < 300, status, async json(){return body;}}; }

test('synthetic context and history require independent opt ins', async () => {
  const calls=[]; const ui=setup(async(_url,options)=>{calls.push(JSON.parse(options.body)); return response(200,{provider_mode:'test_only',answer:'respuesta sintética'});});
  ui.PaideiaChatContext.clear(); ui.input('pregunta ficticia'); ui.consent.checked=true;
  assert.equal(ui.byId['chat-context-consent'].checked,false); assert.equal(ui.byId['chat-history-consent'].checked,false);
  ui.byId['chat-context-field-0'].checked=true; ui.byId['chat-context-consent'].checked=true; ui.byId['chat-history-consent'].checked=true;
  await ui.send(); assert.equal(calls[0].context.version,'chat-context-map-v1'); assert.equal(calls[0].history.length,0);
  ui.input('segunda pregunta ficticia'); await ui.send(); assert.equal(calls[1].history.length,2); assert.equal(calls[1].context_consent.history,true);
  ui.byId['chat-history-clear'].listeners.click(); assert.equal(ui.PaideiaChatContext.history().length,0);
});

test('consent gates request and the body contains no profile', async () => {
  const calls = []; const ui = setup(async (...args) => { calls.push(args); return response(200,{provider_mode:'external', answer:'Respuesta real simulada en fixture'}); });
  ui.input('  Pregunta  '); await ui.send(); assert.equal(calls.length,0);
  ui.consent.checked = true; await ui.send(); assert.equal(calls.length,1);
  assert.deepEqual(JSON.parse(calls[0][1].body), {message:'Pregunta', consent:{notice_version:'paideia-chat-remote-v1',accepted_chat_processing:true,purpose:'free_chat',approved_fields:[]}});
  assert.match(ui.feedback.textContent,/Respuesta real simulada/); assert.doesNotMatch(ui.feedback.textContent,/PRUEBA SINTÉTICA/);
});

test('queued ticket is never attached to an edited question while request is pending', async () => {
  let resolve; const calls=[]; const ui = setup((...args) => { calls.push(args); return new Promise(r => {resolve=r;}); });
  ui.consent.checked=true; ui.input('Primera'); const pending=ui.send(); ui.input('Segunda');
  resolve(response(202,{status:'queued', queue:{ticket:'a'.repeat(32),position:1,code:'queued'},provider_mode:'external'})); await pending;
  assert.equal(ui.state.chatTicket, null, 'an old queue ticket must not bind to a changed question');
});

test('duplicate submission while busy must not send a second request', async () => {
  const resolves=[]; let calls=0; const ui=setup(() => {calls++; return new Promise(r=>resolves.push(r));});
  ui.consent.checked=true; ui.input('Pregunta'); const pending=ui.send(); const duplicate=ui.send();
  resolves.forEach(resolve => resolve(response(200,{provider_mode:'test_only',answer:'fixture'})));
  await Promise.all([pending, duplicate]); assert.equal(calls,1);
});

test('flags, safe sources and tool events are visible; unsafe links are suppressed', async () => {
  const ui=setup(async()=>response(200,{provider_mode:'test_only',answer:'fixture',refused:true,truncated:true,tool_events:[{name:'search_products',state:'executed'}],sources:[{source:{url:'https://example.org',label:'Oficial'}},{source:{url:'javascript:alert(1)',label:'Mala'}}]}));
  ui.input('Pregunta'); ui.consent.checked=true; await ui.send();
  for (const text of ['PRUEBA SINTÉTICA','fixture','rechazado','incompleta','search_products','Oficial']) assert.ok(ui.feedback.textContent.includes(text),text);
  assert.doesNotMatch(ui.feedback.textContent,/Mala/);
});

test('synthetic calculation is opt-in, bound to explicit form inputs and sent once', async () => {
 const calls=[]; const ui=setup(async(_u,o)=>{calls.push(JSON.parse(o.body)); return response(200,{provider_mode:'test_only',external_sent:false,answer:'',structured_education:{version:'paideia-education-v1',kind:'editorial',items:[{id:'risk',text:'Los riesgos dependen del producto, de la entidad y de la custodia; conviene revisar sus condiciones antes de decidir.'}],calculation:null}});},{ai:{status:'test_only',capabilities:{structured_education:true}}});
 ui.input('Calcula'); ui.consent.checked=true; ui.byId['chat-scenario-enabled'].checked=true;
 for(const [key,value] of Object.entries({principal:'1000',annual_rate_percent:'3',years:'2',monthly_contribution:'10',method:'simple',inflation_percent:'1'})) ui.byId['chat-scenario-'+key].value=value;
 await ui.send(); assert.equal(calls.length,1); assert.deepEqual(calls[0].scenario,{principal:'1000.00',annual_rate_percent:'3',years:2,monthly_contribution:'10.00',method:'simple',inflation_percent:'1'});
});

test('structured capability is frozen before fetch even when status changes in flight', async () => {
  let resolve; let calls=0; const ui=setup(()=>{calls++; return new Promise(r=>resolve=r);});
  ui.state.status={ai:{status:'test_only',capabilities:{structured_education:true}}};
  ui.input('Pregunta'); ui.consent.checked=true;
  const pending=ui.send(); ui.state.status={ai:{status:'test_only',capabilities:{structured_education:false}}};
  resolve(response(200,{provider_mode:'test_only',answer:'INJECTED LEGACY'})); await pending;
  assert.equal(calls,1); assert.doesNotMatch(ui.feedback.textContent,/INJECTED LEGACY/);
  assert.match(ui.feedback.textContent,/estructurada no válida/);
});

test('202 requires manual resend and 429 is visible without automatic calls', async () => {
  let calls=0; const ui=setup(async()=>{calls++; return calls===1 ? response(202,{status:'queued',queue:{ticket:'b'.repeat(32),position:2,code:'quota_exhausted'},provider_mode:'external'}) : response(429,{error:{code:'CHAT_RATE_LIMITED',message:'Límite alcanzado; no hay reintento automático.'}});});
  ui.input('Pregunta'); ui.consent.checked=true; await ui.send(); assert.equal(calls,1); assert.match(ui.feedback.textContent,/Posición: 2/); assert.match(ui.feedback.textContent,/cupo está agotado/);
  await ui.send(); assert.equal(calls,2); assert.match(ui.feedback.textContent,/límite de uso \(429\)/i); assert.doesNotMatch(ui.feedback.textContent,/tiempo de espera/i);
});

test('an uncertain queued resend drops the ticket and warns that it may be consumed', async () => {
  let calls=0; const posts=[];
  const ui=setup(async(_url, options)=>{
    calls+=1; posts.push(JSON.parse(options.body));
    if (calls===1) return response(202,{status:'queued',queue:{ticket:'c'.repeat(32),position:1,code:'queued'},provider_mode:'external'});
    if (calls===2) return new Promise((_resolve, reject)=>{
      options.signal.addEventListener('abort', ()=>{ const error=new Error('aborted'); error.name='AbortError'; reject(error); });
    });
    return response(200,{provider_mode:'test_only',answer:'respuesta sintética'});
  }, DEFAULT_STATUS, {
    AbortController,
    setTimeout: (fn, ms)=>setTimeout(fn, Math.min(ms, 25)),
    clearTimeout: (id)=>clearTimeout(id),
  });
  ui.input('Pregunta retenida sin confirmar'); ui.consent.checked=true;
  await ui.send(); assert.equal(ui.state.chatTicket,'c'.repeat(32));
  await ui.send();
  assert.equal(calls,2,'solo hay un POST por envío manual, sin reintentos');
  assert.equal(posts[1].ticket,'c'.repeat(32),'el intento manual usa el ticket que estaba en cola');
  assert.equal(ui.state.chatTicket,null,'un ticket tras un intento sin confirmar no se conserva como si siguiera en cola');
  assert.match(ui.feedback.textContent,/no se reutiliza/i);
  assert.match(ui.feedback.textContent,/podría duplicar|podrías duplicar/i);
  assert.match(ui.feedback.textContent,/rechazad/i);
  assert.doesNotMatch(ui.feedback.textContent,/Se mantiene el turno en cola|mismo ticket/i);
  assert.equal(ui.message.value,'Pregunta retenida sin confirmar','la pregunta sigue en el campo');
  assert.equal(ui.feedback.role,'alert');
  assert.equal(ui.feedback['aria-live'],'assertive');
  assert.equal(ui.submit.textContent,'Reenviar pregunta');
  await ui.send();
  assert.equal(calls,3,'el siguiente envío manual no reintenta solo');
  assert.equal('ticket' in posts[2],false,'el ticket posiblemente consumido no se adjunta a un envío nuevo');
  await new Promise(resolve=>setTimeout(resolve,60));
  assert.equal(calls,3,'no aparece un POST automático tras el timeout');
});

test('editing after an uncertain timeout does not label the new draft as a resend', async () => {
  let calls=0;
  const ui=setup(async(_url, options)=>{
    calls+=1;
    return new Promise((_resolve, reject)=>{
      options.signal.addEventListener('abort', ()=>{ const error=new Error('aborted'); error.name='AbortError'; reject(error); });
    });
  }, DEFAULT_STATUS, {
    AbortController,
    setTimeout: (fn, ms)=>setTimeout(fn, Math.min(ms, 25)),
    clearTimeout: (id)=>clearTimeout(id),
  });
  ui.input('Pregunta anterior sin confirmar'); ui.consent.checked=true;
  await ui.send();
  assert.equal(ui.submit.textContent,'Reenviar pregunta');
  ui.input('Pregunta nueva todavía sin enviar');
  assert.equal(ui.state.chatTicket,null);
  assert.equal(ui.submit.textContent,'Enviar pregunta','la pregunta nueva no se presenta como reenvío');
  assert.doesNotMatch(ui.feedback.textContent,/La pregunta se conserva|Se mantiene el turno en cola|mismo ticket/i);
  assert.match(ui.feedback.textContent,/envío anterior|pregunta anterior/i);
  assert.match(ui.feedback.textContent,/no se ha enviado|todavía no se ha enviado/i);
  assert.equal(calls,1,'editar no dispara otro POST');
});

test('editing while a request is in flight does not claim the sent question was kept', async () => {
  let calls=0;
  const ui=setup(async(_url, options)=>{
    calls+=1;
    return new Promise((_resolve, reject)=>{
      options.signal.addEventListener('abort', ()=>{ const error=new Error('aborted'); error.name='AbortError'; reject(error); });
    });
  }, DEFAULT_STATUS, {
    AbortController,
    setTimeout: (fn, ms)=>setTimeout(fn, Math.min(ms, 25)),
    clearTimeout: (id)=>clearTimeout(id),
  });
  ui.input('Pregunta A en vuelo'); ui.consent.checked=true;
  const pending=ui.send();
  ui.input('Pregunta B escrita mientras tanto');
  await pending;
  assert.equal(calls,1);
  assert.equal(ui.message.value,'Pregunta B escrita mientras tanto');
  assert.equal(ui.submit.textContent,'Enviar pregunta','la pregunta nueva no se etiqueta como reenvío');
  assert.doesNotMatch(ui.feedback.textContent,/La pregunta se conserva/i);
  assert.match(ui.feedback.textContent,/envío anterior|pregunta enviada/i);
  assert.match(ui.feedback.textContent,/no se ha enviado|todavía no se ha enviado/i);
});

test('send_state never proves the whole turn was or was not processed', async () => {
  for (const sendState of ['not_started','completed']) {
    const ui=setup(async()=>response(504,{error:{code:'CHAT_TIMEOUT',message:'genérico',send_state:sendState}}));
    ui.input('Pregunta con timeout'); ui.consent.checked=true; await ui.send();
    assert.equal(ui.state.chatUncertain,true,`${sendState} deja el turno sin confirmar`);
    assert.doesNotMatch(ui.feedback.textContent,/no llegó a recibir|no se envió|no se ha enviado/i);
    assert.doesNotMatch(ui.feedback.textContent,/llegó completa|procesó|procesad[oa]/i);
    assert.match(ui.feedback.textContent,/no demuestra|no confirma/i);
  }
});

test('429 and 504 produce different, explicit messages and never retry by themselves', async () => {
  let calls429=0;
  const ui429=setup(async()=>{calls429+=1; return response(429,{error:{code:'CHAT_RATE_LIMITED',message:'No se pudo completar la llamada al proveedor; no hay reintento automático.'}});});
  ui429.input('Pregunta con límite'); ui429.consent.checked=true; await ui429.send();
  assert.equal(calls429,1);
  assert.match(ui429.feedback.textContent,/límite de uso \(429\)/i);
  assert.match(ui429.feedback.textContent,/no es un timeout/i);
  assert.doesNotMatch(ui429.feedback.textContent,/tiempo de espera|pudo llegar/i);
  assert.equal(ui429.message.value,'Pregunta con límite');
  await new Promise(resolve=>setTimeout(resolve,40));
  assert.equal(calls429,1,'el 429 no dispara otro POST');

  let calls504=0;
  const ui504=setup(async()=>{calls504+=1; return response(504,{error:{code:'CHAT_TIMEOUT',message:'No se pudo completar la llamada al proveedor; no hay reintento automático.'}});});
  ui504.input('Pregunta con timeout'); ui504.consent.checked=true; await ui504.send();
  assert.equal(calls504,1);
  assert.match(ui504.feedback.textContent,/tiempo de espera \(504\)/i);
  assert.match(ui504.feedback.textContent,/pudo llegar al proveedor/i);
  assert.match(ui504.feedback.textContent,/no está confirmado/i);
  assert.doesNotMatch(ui504.feedback.textContent,/límite de uso/i);
  assert.equal(ui504.message.value,'Pregunta con timeout');
  assert.notEqual(ui429.feedback.textContent,ui504.feedback.textContent,'429 y 504 no comparten mensaje');
  await new Promise(resolve=>setTimeout(resolve,40));
  assert.equal(calls504,1,'el 504 no dispara otro POST');
});

test('a mission stop is explicit: nothing was sent and there is no retry', async () => {
  let calls=0;
  const ui=setup(async()=>{calls+=1; return response(429,{error:{code:'CHAT_MISSION_EXHAUSTED',message:'Se agotó el cupo de intentos reales de esta misión.',send_state:'not_started'}});});
  ui.input('Pregunta con cupo agotado'); ui.consent.checked=true; await ui.send();
  assert.equal(calls,1);
  assert.match(ui.feedback.textContent,/No se envió la pregunta al proveedor/i);
  assert.match(ui.feedback.textContent,/cupo de intentos reales/i);
  assert.doesNotMatch(ui.feedback.textContent,/pudo llegar|no está confirmado/i);
  assert.equal(ui.message.value,'Pregunta con cupo agotado');
  await new Promise(resolve=>setTimeout(resolve,40));
  assert.equal(calls,1,'el bloqueo por cupo no dispara otro POST');
});

test('a mission stop with a closed window is not shown as a provider limit', async () => {
  const ui=setup(async()=>response(503,{error:{code:'CHAT_MISSION_CLOSED',message:'La ventana de la misión ya está cerrada.',send_state:'not_started'}}));
  ui.input('Pregunta fuera de ventana'); ui.consent.checked=true; await ui.send();
  assert.match(ui.feedback.textContent,/ventana de esta prueba ya está cerrada/i);
  assert.doesNotMatch(ui.feedback.textContent,/límite de uso|tiempo de espera/i);
});

test('a 504 with not_started transport state keeps the turn uncertain', async () => {
  let calls=0;
  const ui=setup(async()=>{calls+=1; return response(504,{error:{code:'CHAT_TIMEOUT',message:'genérico',send_state:'not_started'}});});
  ui.input('Pregunta con timeout parcial'); ui.consent.checked=true; await ui.send();
  assert.equal(calls,1);
  assert.match(ui.feedback.textContent,/no iniciado/i);
  assert.doesNotMatch(ui.feedback.textContent,/no llegó a recibir|no se envió|no se ha enviado|pudo llegar|no está confirmado/i);
  assert.match(ui.feedback.textContent,/no demuestra/i);
  assert.equal(ui.state.chatUncertain,true,'un intento de transporte no demuestra que el turno entero no se enviara');
});

test('unknown server errors keep the backend message and do not invent send state', async () => {
  let calls=0;
  const ui=setup(async()=>{calls+=1; return response(500,{error:{code:'CHAT_PROVIDER_UNAVAILABLE',message:'Fallo sintético del proveedor; no hay reintento automático.'}});});
  ui.input('Pregunta con fallo'); ui.consent.checked=true; await ui.send();
  assert.equal(calls,1);
  assert.match(ui.feedback.textContent,/Fallo sintético del proveedor/i);
  assert.doesNotMatch(ui.feedback.textContent,/pudo llegar|no está confirmado/i);
});
