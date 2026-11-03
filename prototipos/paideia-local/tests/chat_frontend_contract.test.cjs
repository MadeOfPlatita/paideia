"use strict";
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Execute the actual chat section and request helper with a small targeted element shim.
function setup(fetch, status) {
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
  const ctx = { document, fetch, URL, console, PaideiaChatContext: require('../static/chat_context_model.js'), PaideiaStructuredEducation: require('../static/structured_education_ui.js'), PROFILE_MODEL: require('../static/profile_model.js'), state: {chatMessage:'', chatTicket:null, chatBusy:false, status, profile: require('../static/profile_model.js').createEmptyProfile()}, API: {chat:'/api/chat'} };
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
  ui.state.status={ai:{capabilities:{structured_education:true}}};
  ui.input('Pregunta'); ui.consent.checked=true;
  const pending=ui.send(); ui.state.status={ai:{capabilities:{structured_education:false}}};
  resolve(response(200,{provider_mode:'test_only',answer:'INJECTED LEGACY'})); await pending;
  assert.equal(calls,1); assert.doesNotMatch(ui.feedback.textContent,/INJECTED LEGACY/);
  assert.match(ui.feedback.textContent,/estructurada no válida/);
});

test('202 requires manual resend and 429 is visible without automatic calls', async () => {
  let calls=0; const ui=setup(async()=>{calls++; return calls===1 ? response(202,{status:'queued',queue:{ticket:'b'.repeat(32),position:2,code:'quota_exhausted'},provider_mode:'external'}) : response(429,{error:{code:'CHAT_RATE_LIMITED',message:'Límite alcanzado; no hay reintento automático.'}});});
  ui.input('Pregunta'); ui.consent.checked=true; await ui.send(); assert.equal(calls,1); assert.match(ui.feedback.textContent,/Posición: 2/); assert.match(ui.feedback.textContent,/cupo está agotado/);
  await ui.send(); assert.equal(calls,2); assert.match(ui.feedback.textContent,/Límite alcanzado/);
});
