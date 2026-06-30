#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime as dt,json
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
def split(v): return [x for x in (v or '').split(',') if x]
def main():
    ap=argparse.ArgumentParser(description='Record a plugin/skill execution receipt; does not run plugins')
    ap.add_argument('--case-id',default='NO-CASE'); ap.add_argument('--agent-name',default='codex_plugin_factory_agent'); ap.add_argument('--capability-name',default='manual'); ap.add_argument('--capability-path',default=''); ap.add_argument('--input-artifacts',default=''); ap.add_argument('--output-artifacts',default=''); ap.add_argument('--validation',default='help/dry-run'); ap.add_argument('--approval-boundary',default='internal_draft_only'); ap.add_argument('--sources-used',default=''); ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args(); now=dt.datetime.now().strftime('%Y%m%d%H%M%S'); rid=f'PLUG-{now}-{args.case_id}'
    receipt={'receipt_id':rid,'case_id':args.case_id,'agent_name':args.agent_name,'capability_name':args.capability_name,'capability_path':args.capability_path,'input_artifacts':split(args.input_artifacts),'output_artifacts':split(args.output_artifacts),'validation_performed':args.validation,'approval_boundary':args.approval_boundary,'created_at':dt.datetime.now().isoformat(timespec='seconds'),'sources_used':split(args.sources_used),'safety':'Receipt only. No external send/submission/payment/DSC/final claim.'}
    if args.dry_run: print(json.dumps(receipt,indent=2)); return 0
    out=PROJECT_ROOT/'receipts'/'plugin_runs'/f'{rid}.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(receipt,indent=2),encoding='utf-8'); print(f'Wrote {out.relative_to(PROJECT_ROOT)}'); return 0
if __name__=='__main__': raise SystemExit(main())
