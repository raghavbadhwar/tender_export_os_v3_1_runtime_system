#!/usr/bin/env python3
from __future__ import annotations
import csv,html,datetime as dt
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
def main():
    p=PROJECT_ROOT/'data'/'source_health.csv'
    with p.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        headers=reader.fieldnames or []
        rows=list(reader)
    def status_score(r):
        s=' '.join(r.values()).lower();
        return 100 if 'working' in s or 'active' in s else 60 if 'paywall' in s or 'login' in s else 40 if 'broken' in s or 'fail' in s else 75
    body='<h1>Source Health Report</h1><p>Generated '+dt.datetime.now().isoformat(timespec='seconds')+'</p><table><tr>'+''.join(f'<th>{html.escape(h)}</th>' for h in headers+['reliability_score'])+'</tr>'
    for r in rows: body+='<tr>'+''.join(f'<td>{html.escape(r.get(h,""))}</td>' for h in headers)+f'<td>{status_score(r)}</td></tr>'
    body+='</table><p>Scores are heuristic and used for routing attention, not source truth.</p>'
    out=PROJECT_ROOT/'outputs'/'source_health'/'source_health_report.html'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text('<html><body>'+body+'</body></html>',encoding='utf-8'); print(f'Wrote {out.relative_to(PROJECT_ROOT)}'); return 0
if __name__=='__main__': raise SystemExit(main())
