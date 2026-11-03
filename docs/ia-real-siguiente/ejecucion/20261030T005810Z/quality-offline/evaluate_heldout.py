"""Evaluate a small human-authored regression set. NEVER a model benchmark."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[5]/'prototipos/paideia-local'))
from financial_quality import assess_financial_text
path=Path(__file__).with_name('heldout-corpus.json')
corpus=json.loads(path.read_text(encoding='utf-8'))
rows=[]
for case in corpus['rows']:
    flags=assess_financial_text(case['text'])
    rows.append({'id':case['id'],'gating':case['gating'],'expected_flag':case['expected_flag'],'flags':list(flags),'matched':bool(flags)==case['expected_flag']})
report={'test_only':True,'project_provider_calls':0,'type':'hand-authored regression corpus, not model generation','cases':rows,'gating_cases':sum(c['gating'] for c in rows),'gating_failures':sum(c['gating'] and not c['matched'] for c in rows),'exploratory_misses':[c['id'] for c in rows if not c['gating'] and not c['matched']],'model_quality_proven':False}
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(1 if report['gating_failures'] else 0)
