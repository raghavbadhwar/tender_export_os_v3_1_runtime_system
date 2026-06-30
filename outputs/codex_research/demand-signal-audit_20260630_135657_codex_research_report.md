# Demand Signal Audit - 2026-06-30 13:56:57 IST

Scope: repo-local audit of `data/master_cases.csv`, `data/source_health.csv`, `data/agent_run_log.csv`, `config/sources.gov.yaml`, `config/sources.export.yaml`, `outputs/source_scans/*`, and `outputs/demand_signals/*`. No live portal action, login, submission, or outreach was performed.

## 1. Demand signals found / validated

Validated as real public-source signals from today's scans:

| Bucket | Count | Cases | Evidence |
|---|---:|---|---|
| EXPORT - strong | 2 | `EXP-20260630-005`, `EXP-20260630-006` | UNDP public notice URLs and scan captures in `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`, `outputs/source_scans/export_scan_probe_20260630_130537.json`, `outputs/source_scans/export_candidate_details_20260630_130726.json`; register rows in `data/master_cases.csv`. |
| EXPORT - medium/weak buyer visibility | 2 | `EXP-20260630-003`, `EXP-20260630-004` | TradeKey public RFQ URLs and scan captures in `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`, `outputs/source_scans/export_candidate_details_20260630_130726.json`; register rows in `data/master_cases.csv`. |
| GOV - public starter rows | 5 | `GOV-20260630-003`, `GOV-20260630-004`, `GOV-20260630-005`, `GOV-20260630-006`, `GOV-20260630-007` | GeM/Maharashtra radar report in `outputs/source_scans/gov_radar_batch_20260630131554.md` and `outputs/source_scans/gov_radar_batch_20260630131554.json`; register rows in `data/master_cases.csv`. |

Demoted / excluded from actionable demand-signal count:

| Row | Reason | Evidence |
|---|---|---|
| `EXP-20260630-001` | Weak evidence for the buyer-specific RFQ: only a generic Alibaba RFQ landing page was captured; buyer-specific RFQ URL/attachment/screenshot is missing. | `cases/EXP-20260630-001/evidence/extracted_text/rfq_evidence_intake_EXP-20260630-001.md`; `outputs/case_reports/EXP-20260630-001/audit_EXP-20260630-001.md`; `data/master_cases.csv`. |
| `EXP-20260630-002` | Internal-only recovered case: no original buyer/RFQ source URL, buyer legal identity, buyer message, or screenshot; one quote proof only despite earlier pricing note. | `outputs/case_reports/EXP-20260630-002/rfq_evidence_intake_EXP-20260630-002.md`; `outputs/pricing_compliance/pricing_gate_check_RUN-20260630131218.md`; `data/master_cases.csv`. |
| `GOV-20260630-001` | Existing case has a source-evidence gap: exact GeM searches did not verify the registered buyer/opportunity; needs bid number/document URL/PDF or owner screenshot. | `cases/GOV-20260630-001/evidence/source_intake_20260630T073856Z.md`; `data/master_cases.csv`. |
| `GOV-20260630-002` | Already rejected by Fast Kill for deadline and experience gaps. | `data/master_cases.csv`; `data/agent_run_log.csv`; `outputs/case_reports/GOV-20260630-002/no_go_reason_note.txt`. |
| Mock GOV / mock EXPORT rows | Fixture-only output from the mock source adapter; not real tenders/RFQs. | `outputs/source_scans/daily_morning_autopilot_mock_20260630_130941.json`; `data/agent_run_log.csv` row `RUN-20260630131129-DAILY-RADAR`. |

## 2. Top actionable cases

| Priority | Case | Buyer / authority | Product | Deadline | Source URL | Hermes route | Evidence |
|---:|---|---|---|---|---|---|---|
| 1 | `EXP-20260630-005` | UNDP-TJK - Tajikistan | Food Kits / Humanitarian Supplies | 2026-07-13 | https://procurement-notices.undp.org/view_negotiation.cfm?nego_id=46967 | Deep-read first, then Fast Kill if Quantum docs show eligibility/supplier-registration blockers. | `data/master_cases.csv`; `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`; `outputs/source_scans/export_candidate_details_20260630_130726.json`. |
| 2 | `EXP-20260630-006` | UNDP-PHL - Philippines | Hygiene Supplies | 2026-07-21 | https://procurement-notices.undp.org/view_negotiation.cfm?nego_id=47079 | Deep-read category fit and UNDP Quantum requirements; likely viable if product sourcing is practical. | `data/master_cases.csv`; `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`; `outputs/source_scans/export_candidate_details_20260630_130726.json`. |
| 3 | `GOV-20260630-003` | Department of School Education and Literacy, Ministry of Education | Office Stationery and Supplies | 2026-07-10 | https://bidplus.gem.gov.in/showbidDocument/9535449 | Fast Kill for eligibility/EMD/delivery first; deep-read if no OEM/past-experience traps. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |
| 4 | `GOV-20260630-004` | Department of Higher Education, Ministry of Education | Facility management / housekeeping service | 2026-07-21 | https://bidplus.gem.gov.in/showbidDocument/9513041 | Fast Kill before deep-read because title appears manpower/service-heavy, not simple supply. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |
| 5 | `GOV-20260630-006` | Department of Military Affairs, Ministry of Defence | Furniture and Fixtures | 2026-07-10 | https://bidplus.gem.gov.in/showbidDocument/9284873 | Fast Kill for defence compliance, quantity, delivery location, and past-experience clauses. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |
| 6 | `GOV-20260630-005` | Department of Military Affairs, Ministry of Defence | Safety Equipment and PPE | 2026-07-06 | https://bidplus.gem.gov.in/showbidDocument/9519946 | Fast Kill urgently; six-day deadline and defence/PPE compliance make it high-risk. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |
| 7 | `EXP-20260630-003` | TradeKey buyer - contact hidden pending sign-in; South Africa market | Rice | Not stated; page time-left observed in scan | https://importer.tradekey.com/buyoffer/Supply-Inquiry-For-Rice-3849377.html | Fast Kill / buyer verification only; do not treat as strong until legal identity and specs are visible. | `data/master_cases.csv`; `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`; `outputs/source_scans/export_candidate_details_20260630_130726.json`. |
| 8 | `EXP-20260630-004` | TradeKey buyer - partially masked, Turkey | Juniper Oil | Not stated; page time-left observed in scan | https://importer.tradekey.com/buyoffer/Purchase-Inquiry-For-Juniper-Oils-3849579.html | Fast Kill / buyer verification only; product compliance and buyer identity are not yet strong. | `data/master_cases.csv`; `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`; `outputs/source_scans/export_candidate_details_20260630_130726.json`. |
| 9 | `GOV-20260630-007` | Municipal Council, Pandharpur | Cleaning and housekeeping services | 2026-06-30 | https://mahatenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndListTendersbyDate&service=direct&session=T&sp=SLC1XLgA5d%2FpTAF%2Fdv235xg%3D%3D | Fast Kill / likely reject: deadline is today. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |

## 3. Evidence quality and missing information

- Best evidence: `EXP-20260630-005` and `EXP-20260630-006`. The UNDP rows have formal notice URLs, public notice text, deadlines, references, and Quantum-registration warnings captured in the export scan outputs. Missing: solicitation documents from Quantum/linked document folders, detailed line items, eligibility, delivery terms, document checklist, and whether Tender Export OS can source the goods.
- Medium evidence: `GOV-20260630-003` through `GOV-20260630-006`. The GeM radar found public bid document URLs and HTTP-200 scan evidence, but the cases are starter rows only. Missing: full bid document extraction, BOQ, EMD, buyer terms, delivery location, eligibility, OEM/certification requirements, and past-experience clauses.
- Medium-low evidence: `EXP-20260630-003` and `EXP-20260630-004`. The TradeKey pages were public and product-specific, but buyer contacts are hidden/partially masked and no legal buyer verification is present. Missing: buyer legal identity, direct RFQ ID validation after sign-in, exact deadline, quantity, specs, packing, payment terms, and credibility checks.
- Deadline-kill evidence: `GOV-20260630-007` is a public Maharashtra tender row, but the deadline is 2026-06-30. Missing data should not be filled in; route to Fast Kill unless the owner explicitly approves an emergency review.
- Weak/internal-only rows should not be promoted: `EXP-20260630-001`, `EXP-20260630-002`, and `GOV-20260630-001` need source-evidence repair before buyer/supplier/pricing work. The evidence-gap files cited above are stronger than the optimistic status fields in `data/master_cases.csv`.

## 4. Source blockers / credentials needed

- UNDP: public notices are visible, but bidding and full tender management require UNDP Quantum supplier portal registration/subscription. Cite: `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`; source URLs above.
- TradeKey: public RFQ pages are visible, but buyer contact/legal identity is hidden or partially masked behind sign-in. Cite: `outputs/source_scans/export_candidate_details_20260630_130726.json`.
- Alibaba RFQ: configured as login/manual; current evidence for `EXP-20260630-001` is only the generic RFQ landing page. Cite: `cases/EXP-20260630-001/evidence/extracted_text/rfq_evidence_intake_EXP-20260630-001.md`; `data/source_health.csv`.
- APEDA AgriXchange: home page reachable, but buy leads redirected to exporter login. Cite: `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`; `data/source_health.csv`.
- India Business Portal failed DNS; Indian Trade Portal, EC21, African Development Bank, and Global Sources were blocked/403/interstitial; IndiaMart buyer-leads URL changed/404; FIEO, Made-in-China, and UNGM are login/manual sources. Cite: `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`; `data/source_health.csv`.
- GOV sources: Tender Tiger and Tenders Info are paywalled/login-required; IREPS tender search is manual/JavaScript-routed; BHEL configured URL returned 404 but alternate `/tenders` was reachable. Cite: `outputs/source_scans/gov_radar_batch_20260630131554.md`; `data/source_health.csv`.

## 5. What Hermes should ask the owner to approve next

1. Approve the internal priority queue: deep-read `EXP-20260630-005` and `EXP-20260630-006`; fast-kill/deep-read `GOV-20260630-003`, `GOV-20260630-004`, `GOV-20260630-006`, and urgent fast-kill `GOV-20260630-005` / `GOV-20260630-007`.
2. Approve read-only credential use only where needed: UNDP Quantum registration/subscription review, TradeKey buyer-identity reveal, and Alibaba buyer-specific RFQ evidence capture. This is for evidence capture only, not bidding or outreach.
3. Ask changes on `APR-001` for `EXP-20260630-002` until original buyer/RFQ evidence and second quote proof are captured.
4. Keep `APR-002` and `APR-003` pending unless the owner explicitly approves supplier quote requests; this audit did not send or prepare any new supplier/buyer messages.
5. Tell the owner that mock fixture rows from `outputs/source_scans/daily_morning_autopilot_mock_20260630_130941.json` are test data only and must not appear in owner-facing opportunity counts.

## 6. Safety

No external business action executed: no supplier/buyer messages, no tender/RFQ submissions or portal uploads, no payments/EMD/security deposit/advance, no DSC use, no login/captcha/paywall bypass, and no final HSN/ITC-HS classification, origin claim, price, delivery, or payment-term commitment.
