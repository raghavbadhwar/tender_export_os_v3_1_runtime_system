#!/usr/bin/env python3
"""Render pending approval cards into safe mobile-readable payloads (no send)."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]

def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))

def load_card(row):
    candidates=[]
    if row.get('approval_card_json_path'): candidates.append(PROJECT_ROOT/row['approval_card_json_path'])
    if row.get('approval_card_path'):
        p=Path(row['approval_card_path']); candidates.append((PROJECT_ROOT/p).with_suffix('.json'))
    candidates.append(PROJECT_ROOT/'receipts'/'approvals'/f"{row.get('case_id')}_approval_card.json")
    for p in candidates:
        if p.exists():
            try: return json.loads(p.read_text(encoding='utf-8')), str(p.relative_to(PROJECT_ROOT))
            except Exception: pass
    return {}, ''

def pick(d,*keys,default=''):
    for k in keys:
        v=d.get(k)
        if v not in (None,'',[]): return v
    return default

def render(row):
    card,path=load_card(row)
    approval_id=row.get('approval_id') or pick(card,'approval_id')
    lines=[
        f"APPROVAL REQUIRED — {approval_id}",
        f"Case: {row.get('case_id') or pick(card,'case_id')}",
        f"Workflow: {row.get('workflow_type') or pick(card,'workflow_type')}",
        f"Action: {row.get('action_approved') or pick(card,'proposed_action','action_approved')}",
        f"Business object: {pick(card,'business_object', default=row.get('business_object',''))}",
    ]
    amount=pick(card,'amount','amount_inr','price','quote_amount', default=row.get('amount',''))
    if amount: lines.append(f"Amount/price: {amount}")
    deadline=pick(card,'deadline','deadline_date', default=row.get('deadline_date',''))
    if deadline: lines.append(f"Deadline: {deadline}")
    for label, keys in [('Benefit',('expected_benefit','benefit')),('Risk',('concrete_risk','risk')),('Recovery',('recovery_path','rollback_path')),('Missing info',('missing_information','missing_info'))]:
        val=pick(card,*keys, default=row.get(keys[0],''))
        if isinstance(val,list): val='; '.join(map(str,val))
        if val: lines.append(f"{label}: {val}")
    sources=pick(card,'sources','documents_sources_used','source_links', default=path)
    if isinstance(sources,list): sources='; '.join(map(str,sources[:5]))
    if sources: lines.append(f"Sources: {sources}")
    lines += ["", f"Reply options: APPROVE {approval_id} | REJECT {approval_id} <reason> | CHANGES {approval_id} <request>", "Safety: rendering only; no send/submit/pay/DSC/price/classification/origin action is executed."]
    return '\n'.join(lines)

def main():
    ap=argparse.ArgumentParser(description='Render mobile approval payloads without sending')
    ap.add_argument('--all-pending', action='store_true'); ap.add_argument('--approval-id'); ap.add_argument('--dry-run', action='store_true')
    args=ap.parse_args(); rows=read_csv(PROJECT_ROOT/'data'/'approvals_receipts.csv')
    rows=[r for r in rows if (r.get('approval_status') or '').upper()=='PENDING'] if args.all_pending else rows
    if args.approval_id: rows=[r for r in rows if r.get('approval_id')==args.approval_id]
    if not rows: print('No matching pending approvals.'); return 0
    print('\n\n---\n\n'.join(render(r) for r in rows)); return 0
if __name__=='__main__': raise SystemExit(main())
