'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const provenance = require('../static/scenario_provenance.js');
const report = require('../static/comparison_report.js');

test('la fuente de una tasa del snapshot llega al informe sin confundirla con la ficha', () => {
  const condition = {
    metric: 'annual_rate_percent', state: 'known', value: '2.61',
    retrieved_at: '2026-10-26', effective_to: '2026-11-18',
    source_refs: [{ url: 'https://fuente-ejemplo.invalid/condicion', title: 'Fuente de la condición', accessed: '2026-10-27' }]
  };
  const source = provenance.buildSource({
    product: { id: 'SYN-01', name: 'Producto ficticio', primary_url: 'https://ficha-ejemplo.invalid/producto' },
    conditionEntry: { source: null, rate_tiers: [] }, rateCondition: condition, rate: '2.61'
  });
  assert.equal(source.url, 'https://fuente-ejemplo.invalid/condicion');
  assert.equal(source.url_origin, 'condition_source');
  assert.equal(source.source_title, 'Fuente de la condición');
  assert.equal(source.source_accessed_at, '2026-10-27');
  assert.equal(source.retrieved_at, '2026-10-26');
  assert.equal(source.kind, '');
  const inputs = { principal:'1000',annual_rate_percent:'2.61',years:'1',monthly_contribution:'0',inflation_percent:'0',method:'compound' };
  const run = spawnSync('python', ['-c', 'import json,sys,domain; i=json.load(sys.stdin); i["years"]=int(i["years"]); print(json.dumps(domain.calculate_scenario(i)))'], {
    cwd: path.resolve(__dirname, '..'), input: JSON.stringify(inputs), encoding: 'utf8'
  });
  assert.equal(run.status, 0, run.stderr);
  const result = JSON.parse(run.stdout);
  const snapshot = {schema:'paideia.scenario-comparison',schema_version:1,scenarios:['A','B'].map(id=>({id,status:'current',version:1,inputs,result,source:id==='A'?source:null}))};
  const html = report.render(report.capture(snapshot), '2026-11-04T00:00:00.000Z');
  assert.match(html, /https:\/\/fuente-ejemplo\.invalid\/condicion/);
  assert.match(html, /Fuente de la condición/);
  assert.match(html, /2026-10-27/);
  assert.match(html, /clase de fuente desconocida/i);
  assert.doesNotMatch(html, /fuente oficial/i);
});
