#!/usr/bin/env python3
from __future__ import annotations
import csv,html,datetime as dt
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
def rows(name):
    with (PROJECT_ROOT/'data'/name).open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
def table(rows_, cols):
    head=''.join(f'<th>{html.escape(c)}</th>' for c in cols); body=''.join('<tr>'+''.join(f'<td>{html.escape(str(r.get(c,"")))}</td>' for c in cols)+'</tr>' for r in rows_[:50]); return f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
def main():
    cases=rows('master_cases.csv'); approvals=rows('approvals_receipts.csv'); source=rows('source_health.csv'); plugins=rows('plugin_health.csv'); runs=rows('agent_run_log.csv')
    active=[c for c in cases if c.get('status') not in {'REJECTED','WON','LOST','ARCHIVED'}]; pending=[a for a in approvals if (a.get('approval_status') or '').upper()=='PENDING']
    css='body{font-family:-apple-system,Arial;margin:24px;background:#0f172a;color:#e5e7eb} table{border-collapse:collapse;width:100%;margin:16px 0}td,th{border:1px solid #334155;padding:6px} .card{display:inline-block;background:#1e293b;padding:14px;margin:8px;border-radius:10px} a{color:#93c5fd}'
    body=f"<h1>Tender Export OS Founder Dashboard</h1><p>Generated {dt.datetime.now().isoformat(timespec='seconds')}</p>"+''.join([f"<div class='card'><b>{k}</b><br>{v}</div>" for k,v in {'Active cases':len(active),'Pending approvals':len(pending),'Sources':len(source),'Plugins':len(plugins),'Agent runs':len(runs)}.items()])
    body+='<h2>Pending Approvals</h2>'+table(pending,['approval_id','case_id','workflow_type','action_approved','approval_status','approval_card_path'])
    body+='<h2>Active Cases</h2>'+table(active,['case_id','workflow_type','opportunity_title','buyer_name','deadline_date','status','approval_status'])
    body+='<h2>Source Health</h2>'+table(source, list(source[0].keys())[:8] if source else [])
    body+='<h2>Plugin Health</h2>'+table(plugins, list(plugins[0].keys())[:8] if plugins else [])
    body+='<h2>Recommended action</h2><p>Review pending approvals and keep all external actions gated until receipts are recorded.</p>'
    out=PROJECT_ROOT/'outputs'/'dashboards'/'founder_dashboard.html'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>',encoding='utf-8')
    print(f'Wrote {out.relative_to(PROJECT_ROOT)}'); return 0
if __name__=='__main__': raise SystemExit(main())
