#!/usr/bin/env python3
"""Refine GeM PDF parse into actual gate fields instead of boilerplate keyword hits."""
from __future__ import annotations
import csv, json, re, datetime as dt
from pathlib import Path

OUTDIR=Path('/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/outputs/ad_hoc_research/full_capability_hidden_radar_20260706_0300')
DOCDIR=OUTDIR/'gem_bid_docs'
MAP={
 'GEM_2026_B_7682183_9488137.txt': {'rank':1,'bid_no':'GEM/2026/B/7682183','title':'Stationery 1-5 / price Breakup','category':'stationery'},
 'GEM_2026_B_7746395_9560698.txt': {'rank':2,'bid_no':'GEM/2026/B/7746395','title':'Stationery items','category':'stationery'},
 'GEM_2026_B_7694766_9502339.txt': {'rank':3,'bid_no':'GEM/2026/B/7694766','title':'OFFICE stationery','category':'stationery'},
 'GEM_2026_B_7747358_9561765.txt': {'rank':4,'bid_no':'GEM/2026/B/7747358','title':'Exam Stationary Items','category':'exam stationery'},
 'GEM_2026_B_7739997_9553439.txt': {'rank':5,'bid_no':'GEM/2026/B/7739997','title':'TONERS','category':'toner'},
 'GEM_2026_B_7726732_9538562.txt': {'rank':6,'bid_no':'GEM/2026/B/7726732','title':'Toner Cartridge','category':'toner'},
 'GEM_2026_B_7746523_9560834.txt': {'rank':7,'bid_no':'GEM/2026/B/7746523','title':'garden tools','category':'garden/jute/rubber'},
 'GEM_2026_B_7722082_9533239.txt': {'rank':8,'bid_no':'GEM/2026/B/7722082','title':'jalpraday items','category':'utility consumables'},
}

def clean(s): return re.sub(r'\s+',' ',s or '').strip()
def find(pattern,s,default=''):
    m=re.search(pattern,s,re.I|re.S)
    return clean(m.group(1)) if m else default

def yesno_after(label,s):
    # Works for bilingual text where English field label and Required No/Yes appear nearby.
    m=re.search(label+r'.{0,180}?Required\s+(Yes|No)',s,re.I|re.S)
    return m.group(1) if m else ''

def snippet(pattern,s,window=220):
    m=re.search(pattern,s,re.I|re.S)
    if not m: return ''
    return clean(s[max(0,m.start()-window):min(len(s),m.end()+window)])

def atc_text(s):
    m=re.search(r'Buyer Added text based ATC clauses(.{0,1800})',s,re.I|re.S)
    return clean(m.group(1)) if m else ''

rows=[]
for p in sorted(DOCDIR.glob('*.txt')):
    meta=MAP.get(p.name)
    if not meta: continue
    s=p.read_text(errors='ignore')
    est=find(r'Estimated Bid Value\s+(\d[\d,]*)',s)
    emd=yesno_after(r'EMD Detail',s)
    epbg=yesno_after(r'ePBG Detail',s)
    exp=find(r'Years of Past Experience Required[^\n]{0,120}?(\d+)\s+Year',s)
    oem_turn=find(r'OEM Average Turnover[^\n]{0,120}?([\d.]+\s+Lakh)',s)
    mse_relax=find(r'MSE Relaxation for Years[^\n]{0,140}?(Yes|No)',s)
    startup_relax=find(r'Startup Relaxation for Years[^\n]{0,140}?(Yes|No)',s)
    doc_req=find(r'Document required from seller\s+(.{0,420}?)(?:\*In case|Bid Details|\n\d+\s*/)',s)
    atc=atc_text(s)
    local_office='local office' in atc.lower()
    gst_pan=bool(re.search(r'\bGST\b|\bPAN\b',atc,re.I))
    past_supply=bool(re.search(r'past supply|past performance|credentials',atc,re.I))
    hard_oem=bool(re.search(r'authorization|authorisation|MAF|manufacturer authorization',s,re.I))
    sample=bool(re.search(r'\bsample\b',s,re.I))
    score=50; reasons=[]; blockers=[]
    if emd=='No': score+=10; reasons.append('EMD not required')
    elif emd=='Yes': score-=18; blockers.append('EMD required')
    if epbg=='No': score+=8; reasons.append('ePBG not required')
    elif epbg=='Yes': score-=12; blockers.append('ePBG required')
    if exp:
        n=int(exp); score-=5*n; blockers.append(f'{n} years past experience field')
        if n<=2: reasons.append('experience requirement is not extreme')
    if mse_relax=='Yes': score+=7; reasons.append('MSE relaxation available')
    elif mse_relax=='No' and exp: score-=5; blockers.append('no MSE relaxation')
    if startup_relax=='Yes': score+=5; reasons.append('startup relaxation available')
    elif startup_relax=='No' and exp: score-=4; blockers.append('no startup relaxation')
    if hard_oem: score-=20; blockers.append('hard OEM/authorization language detected')
    if local_office: score-=18; blockers.append('local office requirement')
    if past_supply: score-=10; blockers.append('past supply/credentials required')
    if gst_pan: reasons.append('GST/PAN required (normal if business ready)')
    if sample: score-=3; blockers.append('sample mentioned')
    if meta['category'] in ['stationery','garden/jute/rubber','utility consumables']: score+=8; reasons.append('boring/simple category fit')
    if meta['category']=='toner': score-=6; blockers.append('toner often OEM/original-sensitive')
    verdict='PROMOTE_DOC_REVIEW' if score>=58 else 'WATCHLIST_WITH_BLOCKERS' if score>=42 else 'FAST_KILL_UNLESS_SPECIALIST'
    rows.append({**meta,'estimated_bid_value':est,'emd_required':emd,'epbg_required':epbg,'years_experience':exp,'oem_turnover':oem_turn,'mse_relaxation':mse_relax,'startup_relaxation':startup_relax,'documents_required':doc_req,'atc_excerpt':atc[:500],'local_office_required':local_office,'past_supply_required':past_supply,'hard_oem_auth_detected':hard_oem,'sample_mentioned':sample,'score':max(0,min(100,score)),'verdict':verdict,'reasons':'; '.join(reasons),'blockers':'; '.join(blockers),'text_path':str(p)})

csv_path=OUTDIR/'gem_field_aware_scorecard.csv'
fields=['rank','bid_no','title','category','estimated_bid_value','emd_required','epbg_required','years_experience','oem_turnover','mse_relaxation','startup_relaxation','local_office_required','past_supply_required','hard_oem_auth_detected','sample_mentioned','score','verdict','reasons','blockers','documents_required','atc_excerpt','text_path']
with csv_path.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
json_path=OUTDIR/'gem_field_aware_scorecard.json'
json_path.write_text(json.dumps({'created_at':dt.datetime.now().isoformat(timespec='seconds'),'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
md=['# Field-aware GeM Deep Read — Corrected','',f'**Created:** {dt.datetime.now().isoformat(timespec="seconds")}  ','','This corrects the earlier over-strict keyword scan by extracting actual fields such as EMD Required, ePBG Required, experience, MSE/startup relaxation, and buyer-added ATC.','','| Rank | Bid | Value | EMD | ePBG | Exp | MSE relax | Startup relax | Score | Verdict | Main blockers |','|---:|---|---:|---|---|---:|---|---|---:|---|---|']
for r in rows:
    md.append(f"| {r['rank']} | `{r['bid_no']}` | {r['estimated_bid_value']} | {r['emd_required']} | {r['epbg_required']} | {r['years_experience']} | {r['mse_relaxation']} | {r['startup_relaxation']} | {r['score']} | {r['verdict']} | {r['blockers'][:160]} |")
md += ['','## Corrected conclusion','','- The first keyword scanner over-penalized standard boilerplate.','- Several GeM bids have **EMD No** and **ePBG No**, making them more beginner-friendly than the earlier report implied.','- The real blockers are **past experience / past supply credentials / local office / OEM authorization**, not EMD for the top stationery rows.','- Promote `PROMOTE_DOC_REVIEW` rows to manual bid-doc review; do not bid or upload anything without approval.','','## Safety','','Read-only only. No bid, upload, payment, DSC use, buyer/supplier contact, or commitment executed.']
md_path=OUTDIR/'GEM_FIELD_AWARE_DEEP_READ.md'
md_path.write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps({'csv':str(csv_path),'json':str(json_path),'md':str(md_path),'rows':len(rows),'promote':sum(1 for r in rows if r['verdict']=='PROMOTE_DOC_REVIEW')},indent=2))
