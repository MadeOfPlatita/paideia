"""Independent corruption probe: temporary ledgers, no credentials/network."""
from pathlib import Path
import sys, json, tempfile, os
from datetime import timedelta
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'prototipos/paideia-local'))
import mission_budget as m

with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
    path=Path(directory)/'MISSION.json'
    path.write_text(json.dumps({'schema':'paideia-mission.v1','mission_id':'paideia-ia-20261029T220831Z','start_utc':'2026-10-29T22:08:31.985015+00:00','deadline_utc':'2026-10-29T23:08:31.985015+00:00','max_external_attempts':24}),encoding='utf-8')
    with patch.object(m,'NEW_MANIFEST',path):
        config=m.load_mission(path)
        with m.MissionBudget(config) as budget:
            budget.reserve(config.start+timedelta(seconds=1))
            budget.reserve(config.start+timedelta(seconds=2))
        journal=Path(directory)/'mission-ledger.json.lock'
        original=journal.read_bytes().splitlines()
        assert len(original)>=4,'Probe requires initial entry and two reservations'
        import re
        cases=[]
        for name in ('invalid_intermediate','valid_hex_intermediate','missing_last_entry'):
            lines=list(original)
            if name=='invalid_intermediate':
                lines[1]=b'CORRUPTED_INTERMEDIATE_ENTRY'
            elif name=='valid_hex_intermediate':
                match=re.search(rb'[0-9a-f]{64}',lines[1])
                assert match,'Probe could not locate a hex digest'
                start=match.start()
                replacement=b'0' if lines[1][start:start+1]!=b'0' else b'1'
                lines[1]=lines[1][:start]+replacement+lines[1][start+1:]
            else:
                lines.pop()
            journal.write_bytes(b'\n'.join(lines)+b'\n')
            accepted=False
            try:
                with m.MissionBudget(config) as budget:
                    budget.remaining()
                    accepted=True
            except (ValueError,RuntimeError,OSError):
                pass
            cases.append({'case':name,'corruption_rejected':not accepted})
        passed=all(case['corruption_rejected'] for case in cases)
        print(json.dumps({'test_only':True,'external_model_calls':0,'cases':cases,'passed':passed}))
        raise SystemExit(0 if passed else 1)
