#!/usr/bin/env python3
"""Render a compact founder dashboard summary for mobile delivery (no send)."""
from __future__ import annotations
import argparse,csv
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
def rows(name):
    p=PROJECT_ROOT/'data'/name
    with p.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dry-run',action='store_true'); args=ap.parse_args()
    cases=rows('master_cases.csv'); approvals=rows('approvals_receipts.csv'); source=rows('source_health.csv'); plugins=rows('plugin_health.csv')
    active=[c for c in cases if c.get('status') not in {'REJECTED','WON','LOST','ARCHIVED'}]
    pending=[a for a in approvals if (a.get('approval_status') or '').upper()=='PENDING']
    blockers=[c for c in active if c.get('blocker_status') or c.get('approval_status')=='PENDING']
    lines=['TENDER EXPORT OS — MOBILE DASHBOARD',f'Active cases: {len(active)}',f'Pending approvals: {len(pending)}',f'Blocked/attention cases: {len(blockers)}',f'Sources tracked: {len(source)}',f'Plugins tracked: {len(plugins)}']
    if pending: lines.append('Top approval: '+pending[0].get('case_id','')+' / '+pending[0].get('action_approved',''))
    if active: lines.append('Next case: '+active[0].get('case_id','')+' status='+active[0].get('status',''))
    lines.append('Recommended action: Review pending approvals before enabling any external execution.')
    lines.append('Safety: summary only; no external action sent.')
    print('\n'.join(lines)); return 0
if __name__=='__main__': raise SystemExit(main())
