'use strict';
const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
test('simulation describes reference without claiming synthetic fixtures are real products',()=>{
 const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
 const start=source.indexOf('function renderSimulation()');const stop=source.indexOf('page.appendChild(callout',start);
 const heading=source.slice(start,stop);
 assert.match(heading,/candidato del catálogo/);
 assert.doesNotMatch(heading,/candidato real del catálogo/);
});
