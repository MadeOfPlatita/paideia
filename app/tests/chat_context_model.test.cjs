'use strict';
const test=require('node:test'); const assert=require('node:assert/strict');
const model=require('../static/chat_context_model.js');
test('projection preserves v2 answer states and decimal strings and includes only selected fields',()=>{
 const profile={respuestas:{objetivo:{estado:'no_se'},horizonte:{estado:'sin_preguntar'}},detalle_economico:{importe_objetivo:{estado:'declarado',valor:{min_eur:'0',max_eur:'0.00',moneda:'EUR'}},colchon_liquido:{estado:'omitido'}}};
 const p=model.project(profile,['respuestas.objetivo','detalle_economico.importe_objetivo','detalle_economico.colchon_liquido']);
 assert.deepEqual(p.fields['respuestas.objetivo'],{estado:'no_se'}); assert.equal(p.fields['detalle_economico.importe_objetivo'].valor.max_eur,'0.00'); assert.equal(p.fields['detalle_economico.colchon_liquido'].estado,'omitido'); assert.equal(p.fields['respuestas.horizonte'],undefined);
 assert.throws(()=>model.project(profile,['url']));
});
test('history keeps only two previous turns in tab memory and can be cleared',()=>{
 model.clear(); for(let i=0;i<3;i++) model.add('p'+i,'r'+i);
 assert.equal(model.history().length,4);
 assert.deepEqual(model.history().map(x=>x.content),['p1','r1','p2','r2']);
 assert.throws(()=>model.add('p'.repeat(1001),'r4'),/límite/i);
 assert.equal(model.history().length,4); model.clear(); assert.deepEqual(model.history(),[]);
});
