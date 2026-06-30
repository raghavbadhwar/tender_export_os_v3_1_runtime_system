#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime as dt,json,urllib.request
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--url',default='https://example.com'); ap.add_argument('--case-id',default='NO-CASE'); ap.add_argument('--dry-run',action='store_true'); args=ap.parse_args()
    text=''
    try:
        with urllib.request.urlopen(args.url,timeout=15) as r: text=r.read(4000).decode('utf-8','replace')
    except Exception as e: text=f'FETCH_FAILED: {e}'
    receipt={'case_id':args.case_id,'url':args.url,'captured_at':dt.datetime.now().isoformat(timespec='seconds'),'snippet':text[:1000],'dry_run':args.dry_run,'safety':'browser/source evidence only; no form submit/login/CAPTCHA bypass.'}
    out=PROJECT_ROOT/'receipts'/'browser_research'/f"{args.case_id}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(f'Wrote {out.relative_to(PROJECT_ROOT)}'); return 0
if __name__=='__main__': raise SystemExit(main())
