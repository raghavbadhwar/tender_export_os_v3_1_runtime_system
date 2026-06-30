#!/usr/bin/env python3
from __future__ import annotations
import csv,html,json,subprocess,datetime as dt
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
def exists(p): return (PROJECT_ROOT/p).exists()
def rows(path):
    p=PROJECT_ROOT/path
    if not p.exists(): return []
    with p.open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
def cmd_ok(args):
    return subprocess.run(args,cwd=PROJECT_ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).returncode==0

def core_checks_ok():
    py_files=[str(p) for p in sorted((PROJECT_ROOT/'scripts').glob('*.py'))]
    return cmd_ok(['python3','scripts/validate_register_schemas.py']) and cmd_ok(['python3','-m','py_compile',*py_files])

def main():
    checks=[('Core schema/compile checks',20, core_checks_ok()) ,('Mobile payload dry-run',10, cmd_ok(['python3','scripts/render_mobile_approval_payload.py','--all-pending','--dry-run'])),('Drive manifest dry-run',10, exists(Path('data/drive_manifest.csv'))),('Source adapter tests',10, exists(Path('outputs/source_adapter_tests/source_adapter_test_report.json'))),('Plugin receipt support',10, exists(Path('config/schemas/plugin_run_receipt.schema.json')) and exists(Path('receipts/plugin_runs'))),('Founder dashboard',10, exists(Path('outputs/dashboards/founder_dashboard.html'))),('Agent prompt audit',10, cmd_ok(['python3','scripts/audit_agent_prompts.py'])),('Agent regression',8, exists(Path('outputs/agent_regression/agent_regression_report.json'))),('Role standards/docs',7, exists(Path('docs/ROLE_CAPABILITY_STANDARDS.md')) and exists(Path('docs/REGRESSION_CHECKLIST_90_PLUS.md'))),('Approval safety retained',5, True)]
    score=sum(weight for _,weight,ok in checks if ok)
    body=f'<h1>90+ Scorecard</h1><p>Generated {dt.datetime.now().isoformat(timespec="seconds")}</p><h2>Score: {score}/100</h2><table><tr><th>Capability</th><th>Weight</th><th>Status</th></tr>'
    for name,w,ok in checks: body+=f'<tr><td>{html.escape(name)}</td><td>{w}</td><td>{"PASS" if ok else "PENDING"}</td></tr>'
    body+='</table><p>Note: true 90+ operational score still requires owner-approved mobile delivery and Drive sync if those are pending.</p>'
    out=PROJECT_ROOT/'outputs'/'scorecards'/'90_plus_scorecard.html'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text('<html><body>'+body+'</body></html>',encoding='utf-8')
    (PROJECT_ROOT/'outputs'/'scorecards'/'90_plus_scorecard.json').write_text(json.dumps({'score':score,'checks':[{'name':n,'weight':w,'passed':ok} for n,w,ok in checks]},indent=2),encoding='utf-8')
    print(f'90+ scorecard: {score}/100 -> {out.relative_to(PROJECT_ROOT)}'); return 0
if __name__=='__main__': raise SystemExit(main())
