'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const ui=require('../static/structured_education_ui.js');
const {execFileSync}=require('node:child_process');
test('real local calculation schema matches scenario; tampered assumptions and extras fail',()=>{
 const input={principal:'1000.00',annual_rate_percent:'3',years:2,monthly_contribution:'10.00',method:'simple',inflation_percent:'1'};
 const script='import json,sys,structured_education as e; print(json.dumps(e.render_selection({"version":e.VERSION,"intent":"calculate","claim_ids":["simulation"]},json.loads(sys.argv[1]),scenario_present=True)))';
 const value=JSON.parse(execFileSync('python',['-c',script,JSON.stringify(input)],{cwd:require('node:path').join(__dirname,'..'),encoding:'utf8'}));
 assert.equal(ui.project(value,input).calculation.data.assumptions.principal,'1000.00');
 assert.throws(()=>ui.project(value));
 const altered=structuredClone(value); altered.structured_education.calculation.data.assumptions.principal='999999.00'; assert.throws(()=>ui.project(altered,input));
 const extra=structuredClone(value); extra.structured_education.calculation.data.summary.injected='x'; assert.throws(()=>ui.project(extra,input));
});
const text='Los riesgos dependen del producto, de la entidad y de la custodia; conviene revisar sus condiciones antes de decidir.';
const response=()=>({provider_mode:'test_only',external_sent:false,answer:'UNTRUSTED',structured_education:{version:'paideia-education-v1',kind:'editorial',items:[{id:'risk',text}],calculation:null}});
test('closed editorial catalogue rejects unknown, changed and duplicated claims',()=>{
 assert.equal(ui.project(response()).items[0].text,text);
 for(const items of [[{id:'x',text}], [{id:'risk',text:'forged'}], [{id:'risk',text},{id:'risk',text}]]) {const r=response();r.structured_education.items=items;assert.throws(()=>ui.project(r));}
});
test('structured mode refuses legacy answer and arbitrary calculation without submitted scenario',()=>{
 assert.throws(()=>ui.select({provider_mode:'test_only',answer:'legacy'},true));
 assert.equal(ui.select({provider_mode:'test_only',answer:'legacy'},false),null);
 const r=response();r.structured_education.calculation={source:'deterministic_local',data:{summary:{final_balance:'999999'}}};assert.throws(()=>ui.project(r));
});
