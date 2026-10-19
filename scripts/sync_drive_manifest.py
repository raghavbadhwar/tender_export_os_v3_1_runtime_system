#!/usr/bin/env python3
"""Build/update a local Google Drive sync manifest; upload requires explicit future approval."""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
FIELDS=['case_id','local_path','drive_file_id','drive_url','sha256','synced_at','sync_status','receipt_path']
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def candidate_files(case_id):
    roots=[PROJECT_ROOT/'cases'/case_id, PROJECT_ROOT/'receipts'/'approvals']
    out=[]
    for r in roots:
        if r.exists(): out += [p for p in r.rglob('*') if p.is_file() and p.name!='.DS_Store']
    return sorted(set(out))
def read_manifest(path):
    if not path.exists(): return []
    with path.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
def write_manifest(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--case-id',required=True); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--output',default='data/drive_manifest.csv'); args=ap.parse_args()
    status='DRY_RUN' if args.dry_run else 'APPROVAL_REQUIRED_NO_UPLOAD'
    now=dt.datetime.now().replace(microsecond=0).isoformat(); manifest=PROJECT_ROOT/args.output
    rows=read_manifest(manifest); by={(r['case_id'],r['local_path']):r for r in rows}
    receipt_dir=PROJECT_ROOT/'receipts'/'drive_sync'; receipt_dir.mkdir(parents=True,exist_ok=True)
    updates=[]
    for p in candidate_files(args.case_id):
        rel=str(p.relative_to(PROJECT_ROOT)); receipt=receipt_dir/f"{args.case_id}_{p.stem}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        row={'case_id':args.case_id,'local_path':rel,'drive_file_id':'','drive_url':'','sha256':sha(p),'synced_at':now,'sync_status':status,'receipt_path':str(receipt.relative_to(PROJECT_ROOT))}
        by[(args.case_id,rel)]=row; updates.append(row)
    write_manifest(manifest, list(by.values()))
    receipt={'case_id':args.case_id,'status':status,'dry_run':args.dry_run,'files_considered':len(updates),'manifest':str(manifest.relative_to(PROJECT_ROOT)),'safety':'No Drive upload performed; manifest only.'}
    rp=receipt_dir/f"{args.case_id}_manifest_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}.json"; rp.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(f'{status}: wrote {len(updates)} manifest rows to {manifest.relative_to(PROJECT_ROOT)}; receipt={rp.relative_to(PROJECT_ROOT)}'); return 0
if __name__=='__main__': raise SystemExit(main())
