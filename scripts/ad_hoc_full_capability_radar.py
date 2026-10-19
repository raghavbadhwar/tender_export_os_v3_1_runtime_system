#!/usr/bin/env python3
"""Ad-hoc full capability hidden tender/export radar.

Read-only: downloads public GeM bid PDFs, extracts blocker signals,
adds export RFQ/supplier-readiness notes captured from previous Kimi pass,
and writes structured JSON/CSV/MD artifacts.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
from pathlib import Path

import requests
import fitz  # PyMuPDF

ROOT = Path('/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system')
OUTDIR = ROOT / 'outputs' / 'ad_hoc_research' / 'full_capability_hidden_radar_20260706_0300'
DOCDIR = OUTDIR / 'gem_bid_docs'
OUTDIR.mkdir(parents=True, exist_ok=True)
DOCDIR.mkdir(parents=True, exist_ok=True)

GEM_LEADS = [
    {'rank': 1, 'bid_no': 'GEM/2026/B/7682183', 'bid_id': 9488137, 'buyer': 'Uttar Pradesh Cooperative Sugar Factories Federation Ltd', 'title': 'Stationery 1-5 / price Breakup', 'category': 'stationery', 'qty': 47, 'deadline': '2026-08-01 17:00 UTC'},
    {'rank': 2, 'bid_no': 'GEM/2026/B/7746395', 'bid_id': 9560698, 'buyer': 'Ministry of AYUSH / CCRAS', 'title': 'Stationery items', 'category': 'stationery', 'qty': 52, 'deadline': '2026-07-25 16:00 UTC'},
    {'rank': 3, 'bid_no': 'GEM/2026/B/7694766', 'bid_id': 9502339, 'buyer': 'Department of Heavy Industry', 'title': 'OFFICE stationery', 'category': 'stationery', 'qty': 1764, 'deadline': '2026-07-23 11:00 UTC'},
    {'rank': 4, 'bid_no': 'GEM/2026/B/7747358', 'bid_id': 9561765, 'buyer': 'Ministry of Education', 'title': 'Exam Stationary Items', 'category': 'exam stationery/printing', 'qty': 33324, 'deadline': '2026-07-25 20:00 UTC'},
    {'rank': 5, 'bid_no': 'GEM/2026/B/7739997', 'bid_id': 9553439, 'buyer': 'Ministry of Skill Development / DGT', 'title': 'TONERS', 'category': 'toner', 'qty': 19, 'deadline': '2026-07-25 11:00 UTC'},
    {'rank': 6, 'bid_no': 'GEM/2026/B/7726732', 'bid_id': 9538562, 'buyer': 'MoEFCC', 'title': 'Toner Cartridge', 'category': 'toner cartridge basket', 'qty': 691, 'deadline': '2026-07-23 18:00 UTC'},
    {'rank': 7, 'bid_no': 'GEM/2026/B/7746523', 'bid_id': 9560834, 'buyer': 'Ministry of AYUSH / CCRAS', 'title': 'garden tools', 'category': 'garden/jute/rubber mixed BOQ', 'qty': 64, 'deadline': '2026-07-25 16:00 UTC'},
    {'rank': 8, 'bid_no': 'GEM/2026/B/7722082', 'bid_id': 9533239, 'buyer': 'Urban Development and Environment Department', 'title': 'jalpraday items', 'category': 'utility consumables', 'qty': 6102, 'deadline': '2026-07-30 16:00 UTC'},
]

EXPORT_LEADS = [
    {'rank': 1, 'rfq': 'Cocoa and Coffee USED GUNNY BAGS JUTE BAGS', 'country': 'Vanuatu', 'qty': '5000 pcs', 'quotes_left': 1, 'posted': '3 days ago', 'category': 'used jute/gunny bags', 'supplier_readiness': 'medium-high if fumigated used gunny bag exporter found', 'blockers': 'fumigation, used-bag cleanliness, freight to Vanuatu, photos/spec match', 'next_action': 'source 5 used jute/gunny bag exporters with fumigation/export docs'},
    {'rank': 2, 'rfq': 'custom biodegradable 12 oz coffee bags / kraft flat bottom pouch', 'country': 'Saudi Arabia', 'qty': '1000 pcs', 'quotes_left': 1, 'posted': '13 days ago', 'category': 'flexible packaging', 'supplier_readiness': 'high; India has many pouch converters', 'blockers': 'MOQ, print plates, food-grade cert, shipping estimate', 'next_action': 'source 5 kraft/coffee pouch vendors; confirm food-grade and MOQ'},
    {'rank': 3, 'rfq': 'custom printed eco-friendly disposable kraft food bags', 'country': 'United States', 'qty': '1000 pcs', 'quotes_left': 1, 'posted': '1 day ago', 'category': 'paper food packaging', 'supplier_readiness': 'high if food-contact paper cert available', 'blockers': 'FDA/food-contact cert, custom size/color, landed freight', 'next_action': 'source 5 kraft paper bag vendors with food-grade capability'},
    {'rank': 4, 'rfq': 'custom printed lined roast chicken / greaseproof paper bag', 'country': 'United States', 'qty': '100000 pcs', 'quotes_left': 3, 'posted': '1 day ago', 'category': 'greaseproof food packaging', 'supplier_readiness': 'medium-high, but certification and large-run pricing needed', 'blockers': 'greaseproof coating spec, food cert, production capacity', 'next_action': 'identify greaseproof bag manufacturers and request internal indicative MOQ only'},
    {'rank': 5, 'rfq': 'custom drawer incense stick paper box', 'country': 'United States', 'qty': '1000 pcs', 'quotes_left': 3, 'posted': '3 days ago', 'category': 'incense packaging', 'supplier_readiness': 'high; India has incense + carton ecosystem', 'blockers': 'die-line, drawer box fit, print finish, sample lead time', 'next_action': 'source incense box/carton vendors with die-line support'},
    {'rank': 6, 'rfq': 'coconut coir disc mat / private label inquiry', 'country': 'United States', 'qty': '500 pcs', 'quotes_left': 0, 'posted': '13 days ago', 'category': 'coir garden product', 'supplier_readiness': 'medium-high in Kerala/TN coir cluster', 'blockers': 'private label, phytosanitary/plant-fiber import treatment, RFQ freshness', 'next_action': 'verify still open, then source coir mat exporters'},
]

NEGATIVE_PATTERNS = {
    'oem_or_authorized': r'\b(OEM|Original Equipment Manufacturer|authorized dealer|authorised dealer|authorization|authorisation|MAF)\b',
    'experience': r'\b(experience|past performance|past experience|similar work|years? of experience)\b',
    'turnover': r'\b(turnover|annual average turnover)\b',
    'emd': r'\bEMD\b|Earnest Money',
    'pbg': r'\bPBG\b|Performance Bank Guarantee|performance security',
    'sample': r'\bsample\b|prototype',
    'local_delivery': r'\bdelivery\b|consignee|location|days from',
    'bid_specific_atc': r'Bid Specific ATC|Additional Terms and Conditions',
}

POSITIVE_PATTERNS = {
    'mse_exemption': r'\bMSE\b|Micro and Small Enterprise|Startup',
    'boq': r'BOQ|Bill of Quantity',
    'low_value_hint': r'Stationery|Toner|Cartridge|Garden|Jute|Rubber|PVC|GI FITTING|Pen|File|Envelope',
}

def get_text(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    parts = []
    for page in doc:
        parts.append(page.get_text())
    return '\n'.join(parts)

def snippets(text: str, pattern: str, window: int = 160):
    out = []
    for m in re.finditer(pattern, text, flags=re.I):
        start = max(0, m.start() - window)
        end = min(len(text), m.end() + window)
        snip = re.sub(r'\s+', ' ', text[start:end]).strip()
        if snip not in out:
            out.append(snip)
        if len(out) >= 3:
            break
    return out

def classify(lead, text):
    neg = {k: snippets(text, p) for k, p in NEGATIVE_PATTERNS.items()}
    pos = {k: snippets(text, p) for k, p in POSITIVE_PATTERNS.items()}
    neg_hits = {k:v for k,v in neg.items() if v}
    pos_hits = {k:v for k,v in pos.items() if v}
    score = 50
    reasons=[]
    if pos_hits.get('boq'):
        score += 8; reasons.append('BOQ/custom item visible')
    if pos_hits.get('low_value_hint'):
        score += 10; reasons.append('beginner-friendly/boring category terms visible')
    if pos_hits.get('mse_exemption'):
        score += 4; reasons.append('MSE/startup language visible')
    if neg_hits.get('emd'):
        score -= 8; reasons.append('EMD language must be checked')
    if neg_hits.get('pbg'):
        score -= 6; reasons.append('PBG/performance security language must be checked')
    if neg_hits.get('oem_or_authorized'):
        score -= 14; reasons.append('OEM/authorization terms may block non-authorized seller')
    if neg_hits.get('experience'):
        score -= 10; reasons.append('experience/past-performance terms may block beginner')
    if neg_hits.get('turnover'):
        score -= 8; reasons.append('turnover terms may block beginner')
    if neg_hits.get('sample'):
        score -= 4; reasons.append('sample/prototype may be required')
    if 'toner' in lead['category'].lower() and neg_hits.get('oem_or_authorized'):
        score -= 10; reasons.append('toner with OEM clause is high risk')
    if 'stationery' in lead['category'].lower() and not neg_hits.get('oem_or_authorized'):
        score += 5; reasons.append('stationery without obvious OEM hit is promising')
    verdict = 'PROMOTE_TO_DEEP_READ' if score >= 55 else 'WATCHLIST_FAST_KILL_CHECK' if score >= 42 else 'LIKELY_KILL_OR_SPECIALIST_ONLY'
    return {
        'score': max(0,min(100,score)),
        'verdict': verdict,
        'positive_hits': pos_hits,
        'risk_hits': neg_hits,
        'reason_summary': '; '.join(reasons[:6]) or 'No strong parse signals; manual review needed',
    }

def main():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0', 'Referer': 'https://bidplus.gem.gov.in/all-bids'})
    session.get('https://bidplus.gem.gov.in/all-bids', timeout=30)
    gem_rows=[]
    for lead in GEM_LEADS:
        pdf_path = DOCDIR / f"{lead['bid_no'].replace('/','_')}_{lead['bid_id']}.pdf"
        url = f"https://bidplus.gem.gov.in/showbidDocument/{lead['bid_id']}"
        if not pdf_path.exists():
            r = session.get(url, timeout=60)
            r.raise_for_status()
            pdf_path.write_bytes(r.content)
        text = get_text(pdf_path)
        txt_path = pdf_path.with_suffix('.txt')
        txt_path.write_text(text[:60000], encoding='utf-8')
        cls = classify(lead, text)
        row = {**lead, 'source_url': url, 'pdf_path': str(pdf_path), 'text_path': str(txt_path), 'text_chars': len(text), **cls}
        gem_rows.append(row)

    # Export scoring (read-only supplier readiness heuristic; no supplier contact)
    export_rows=[]
    for l in EXPORT_LEADS:
        score=50
        if l['quotes_left'] <= 1: score += 18
        elif l['quotes_left'] <= 3: score += 10
        if any(k in l['category'] for k in ['jute','kraft','paper','coir','incense','packaging']): score += 12
        if l['country'] in {'Saudi Arabia','United States','Vanuatu'}: score += 5
        if any(b in l['blockers'].lower() for b in ['cert','fumigation','phytosanitary']): score -= 8
        verdict = 'SUPPLIER_SPRINT_FIRST' if score >= 65 else 'WATCHLIST_SOURCE_CHECK'
        export_rows.append({**l, 'score': max(0,min(100,score)), 'verdict': verdict})

    payload = {
        'created_at': dt.datetime.now().isoformat(timespec='seconds'),
        'mode': 'read-only; no external contact or commitments',
        'gem_deep_reads': gem_rows,
        'export_supplier_readiness': export_rows,
        'safety': 'No buyer/supplier contact, quote, bid, upload, payment, DSC, or commitment executed.',
    }
    json_path = OUTDIR / 'full_capability_hidden_radar_scorecard.json'
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    csv_path = OUTDIR / 'gem_deep_read_scorecard.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        fields=['rank','bid_no','bid_id','buyer','title','category','qty','deadline','score','verdict','reason_summary','source_url','pdf_path','text_path','text_chars']
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in gem_rows:
            w.writerow({k:r.get(k,'') for k in fields})

    csv2_path = OUTDIR / 'export_readiness_scorecard.csv'
    with csv2_path.open('w', newline='', encoding='utf-8') as f:
        fields=['rank','rfq','country','qty','quotes_left','posted','category','supplier_readiness','blockers','next_action','score','verdict']
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in export_rows:
            w.writerow({k:r.get(k,'') for k in fields})

    md=[]
    md.append('# Full Capability Upgrade — Hidden Tender + Export Radar')
    md.append('')
    md.append(f"**Created:** {payload['created_at']}  ")
    md.append('**Mode:** read-only; public bid documents downloaded; no external commercial action.  ')
    md.append('')
    md.append('## What changed vs first pass')
    md.append('')
    md.append('- Downloaded and text-extracted public GeM bid PDFs for the top 8 hidden leads.')
    md.append('- Added blocker parsing for EMD/PBG/OEM/experience/turnover/sample/ATC terms.')
    md.append('- Created structured JSON + CSV scorecards, not only a narrative report.')
    md.append('- Added export supplier-readiness scoring without contacting any supplier/buyer.')
    md.append('')
    md.append('## GeM deep-read scorecard')
    md.append('')
    md.append('| Rank | Bid | Category | Score | Verdict | Why |')
    md.append('|---:|---|---|---:|---|---|')
    for r in gem_rows:
        md.append(f"| {r['rank']} | `{r['bid_no']}` | {r['category']} | {r['score']} | {r['verdict']} | {r['reason_summary'][:180]} |")
    md.append('')
    md.append('## Export supplier-readiness scorecard')
    md.append('')
    md.append('| Rank | RFQ | Country | Quotes left | Score | Verdict | Next internal action |')
    md.append('|---:|---|---|---:|---:|---|---|')
    for r in export_rows:
        md.append(f"| {r['rank']} | {r['rfq'][:70]} | {r['country']} | {r['quotes_left']} | {r['score']} | {r['verdict']} | {r['next_action']} |")
    md.append('')
    md.append('## Recommended operating upgrade')
    md.append('')
    md.append('1. Promote only `PROMOTE_TO_DEEP_READ` GeM rows into case cards after manual PDF review of exact EMD/OEM/experience clauses.')
    md.append('2. Run supplier-sourcing sprint for export rows scored >=65, starting with jute/gunny + kraft packaging.')
    md.append('3. Convert this script into a daily TEOS radar job after owner approval of automation schedule/delivery target.')
    md.append('')
    md.append('## Safety')
    md.append('')
    md.append(payload['safety'])
    md_path = OUTDIR / 'FULL_CAPABILITY_HIDDEN_RADAR_REPORT.md'
    md_path.write_text('\n'.join(md)+'\n', encoding='utf-8')

    print(json.dumps({
        'outdir': str(OUTDIR),
        'json': str(json_path),
        'gem_csv': str(csv_path),
        'export_csv': str(csv2_path),
        'report': str(md_path),
        'gem_count': len(gem_rows),
        'export_count': len(export_rows),
        'gem_promoted': sum(1 for r in gem_rows if r['verdict']=='PROMOTE_TO_DEEP_READ'),
        'pdfs': len(list(DOCDIR.glob('*.pdf'))),
    }, indent=2))

if __name__ == '__main__':
    main()
