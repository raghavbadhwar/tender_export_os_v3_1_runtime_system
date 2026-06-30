#!/usr/bin/env python3
"""Safe structural harness for source adapters."""
from __future__ import annotations
import argparse,datetime as dt,importlib,json,sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]; ADAPTER_DIR=PROJECT_ROOT/'scripts'/'source_adapters'; sys.path.insert(0,str(ADAPTER_DIR))
REQUIRED={'source_url','opportunity_title','buyer_name','deadline_date','citations'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--safe',action='store_true'); ap.add_argument('--limit',type=int,default=5); args=ap.parse_args()
    modules=[p.stem for p in ADAPTER_DIR.glob('*_adapter.py')]
    results=[]
    for name in sorted(modules):
        if name=='base': continue
        try:
            mod=importlib.import_module(name); cls=[v for v in vars(mod).values() if isinstance(v,type) and v.__name__.endswith('Adapter')][0]
            items=[x.to_dict() for x in cls().scan()][:args.limit]
            missing=[k for item in items for k in REQUIRED if k not in item]
            results.append({'adapter':name.replace('_adapter',''),'status':'PASS' if not missing else 'FAIL','items':len(items),'missing_fields':sorted(set(missing))})
        except Exception as e: results.append({'adapter':name,'status':'FAIL','error':str(e)})
    report={'generated_at':dt.datetime.now().isoformat(timespec='seconds'),'safe_mode':args.safe,'summary':{'adapters_checked':len(results),'passes':sum(r['status']=='PASS' for r in results),'failures':sum(r['status']!='PASS' for r in results)},'results':results}
    out=PROJECT_ROOT/'outputs'/'source_adapter_tests'/'source_adapter_test_report.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"Checked {len(results)} adapters; passes={report['summary']['passes']} failures={report['summary']['failures']}; report={out.relative_to(PROJECT_ROOT)}")
    return 0 if report['summary']['failures']==0 else 1
if __name__=='__main__': raise SystemExit(main())
