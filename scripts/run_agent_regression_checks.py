#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,datetime as dt
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--structural-only',action='store_true'); args=ap.parse_args()
    results=[]
    for p in sorted((PROJECT_ROOT/'agents').glob('*.md')):
        text=p.read_text(encoding='utf-8').lower(); checks={'case_id_or_case':('case_id' in text or 'case' in text),'approval':('approval' in text),'sources':('source' in text),'best_in_class':('best-in-class tuning' in text)}
        results.append({'agent':p.stem,'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks})
    report={'generated_at':dt.datetime.now().isoformat(timespec='seconds'),'structural_only':args.structural_only,'results':results,'summary':{'passes':sum(r['status']=='PASS' for r in results),'failures':sum(r['status']!='PASS' for r in results)}}
    out=PROJECT_ROOT/'outputs'/'agent_regression'/'agent_regression_report.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"Agent regression structural checks: passes={report['summary']['passes']} failures={report['summary']['failures']} report={out.relative_to(PROJECT_ROOT)}")
    return 0 if report['summary']['failures']==0 else 1
if __name__=='__main__': raise SystemExit(main())
