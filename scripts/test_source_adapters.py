#!/usr/bin/env python3
"""Safe structural harness for source adapters."""
from __future__ import annotations
import argparse,datetime as dt,json,os,sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT_ROOT)); sys.path.insert(0,str(PROJECT_ROOT/'scripts'))
from scripts.source_adapters.adapter_registry import ADAPTERS, create_adapter
REQUIRED={'source_url','opportunity_title','buyer_name','deadline_date','citations'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--safe',action='store_true'); ap.add_argument('--limit',type=int,default=5); args=ap.parse_args()
    if args.safe:
        os.environ['DEEP_SOURCE_DISABLE_BROWSER']='1'
    results=[]
    for name in sorted(ADAPTERS):
        try:
            adapter=create_adapter(name, limit=args.limit, headless=True, run_id='HARNESS')
            items=[x.to_dict() for x in adapter.scan()][:args.limit]
            missing=[k for item in items for k in REQUIRED if k not in item]
            structured_blocker=bool(items) and all(item.get('blocker_status') for item in items)
            status='PASS' if not missing or structured_blocker else 'FAIL'
            results.append({'adapter':name,'status':status,'items':len(items),'structured_blocker':structured_blocker,'missing_fields':sorted(set(missing))})
        except Exception as e: results.append({'adapter':name,'status':'FAIL','error':str(e)})
    report={'generated_at':dt.datetime.now().isoformat(timespec='seconds'),'safe_mode':args.safe,'summary':{'adapters_checked':len(results),'passes':sum(r['status']=='PASS' for r in results),'failures':sum(r['status']!='PASS' for r in results)},'results':results}
    out=PROJECT_ROOT/'outputs'/'source_adapter_tests'/'source_adapter_test_report.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"Checked {len(results)} adapters; passes={report['summary']['passes']} failures={report['summary']['failures']}; report={out.relative_to(PROJECT_ROOT)}")
    return 0 if report['summary']['failures']==0 else 1
if __name__=='__main__': raise SystemExit(main())
