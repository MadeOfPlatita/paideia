'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const ui=require('../static/structured_education_ui.js');
test('structured fixture exposes server-owned editorial without using free answer',()=>{
 const value={provider_mode:'test_only',external_sent:false,answer:'UNTRUSTED FREE TEXT',structured_education:{version:'paideia-education-v1',kind:'editorial',items:[{id:'risk',text:'Los riesgos dependen del producto, de la entidad y de la custodia; conviene revisar sus condiciones antes de decidir.'}],calculation:null}};
 const result=ui.project(value);
 assert.equal(result.items[0].id,'risk');
 assert.equal(JSON.stringify(result).includes('UNTRUSTED FREE TEXT'),false);
});
test('structured mode never falls back to an unstructured answer',()=>{
 assert.throws(()=>ui.select({provider_mode:'test_only',external_sent:false,answer:'arbitrary prose'},true));
 assert.equal(ui.select({provider_mode:'test_only',answer:'legacy'},false),null);
});
test('structured response refuses external provenance or malformed editorial data',()=>{
 const dto={version:'paideia-education-v1',kind:'editorial',items:[{id:'x',text:'Texto.'}],calculation:null};
 assert.throws(()=>ui.project({provider_mode:'external',external_sent:true,structured_education:dto}));
 assert.throws(()=>ui.project({provider_mode:'test_only',external_sent:false,structured_education:{...dto,items:[{id:'x',text:'ok',extra:'forged'}]}}));
});
