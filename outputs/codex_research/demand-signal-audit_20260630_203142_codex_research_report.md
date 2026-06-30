# Demand Signal Audit - 2026-06-30 20:31 IST

Scope: repo-local audit of `data/master_cases.csv`, `data/rfq_master.csv`, `data/source_health.csv`, `data/agent_run_log.csv`, `config/sources.gov.yaml`, `config/sources.export.yaml`, `outputs/source_scans/*`, `outputs/demand_signals/*`, `outputs/buyer_verification/*`, and the 20:31 external-intake report. No live portal action, login, submission, outreach, payment, DSC use, or price/classification/origin commitment was performed.

## 1. Demand signals found / validated

| Bucket | Count | Cases | Evidence |
|---|---:|---|---|
| EXPORT - verified institutional RFQ demand | 2 | `EXP-20260630-005`, `EXP-20260630-006` | Public UNDP notice URLs in `data/master_cases.csv`, `data/rfq_master.csv`, `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`, and `outputs/buyer_verification/EXP-20260630-005.md` / `EXP-20260630-006.md`. |
| GOV - public starter rows needing Fast Kill | 5 | `GOV-20260630-003` to `GOV-20260630-007` | Public GeM/Maharashtra scan in `outputs/source_scans/gov_radar_batch_20260630131554.md` and register rows in `data/master_cases.csv`. |
| EXPORT - real but weak marketplace leads | 3 | `EXP-20260630-003`, `EXP-20260630-004`, `EXP-20260630-007` | TradeKey/go4WorldBusiness URLs in `data/master_cases.csv` and `data/rfq_master.csv`; buyer visibility gaps recorded in `outputs/buyer_verification/EXP-20260630-003.md`, `EXP-20260630-004.md`, and `outputs/supplier_shortlists/EXP-20260630-007_agarbatti_fiji_supplier_shortlist.md`. |

Demoted / excluded from the top actionable queue:

| Row | Reason | Evidence |
|---|---|---|
| `EXP-20260630-001` | Buyer-specific Alibaba RFQ evidence is missing; only the generic RFQ source is recorded. | `outputs/buyer_verification/EXP-20260630-001.md`, `outputs/case_reports/EXP-20260630-001/audit_EXP-20260630-001.md`, `data/rfq_master.csv`. |
| `EXP-20260630-002` | Internal-only recovered row; no original RFQ URL, buyer legal identity, or buyer-specific RFQ proof. | `outputs/case_reports/EXP-20260630-002/rfq_evidence_intake_EXP-20260630-002.md`, `outputs/buyer_verification/EXP-20260630-002.md`. |
| `GOV-20260630-001` | Existing case still has a source-evidence gap: exact GeM searches did not verify the registered opportunity/buyer. | `cases/GOV-20260630-001/evidence/source_intake_20260630T073856Z.md`. |
| `GOV-20260630-002` | Already rejected by Fast Kill. | `data/master_cases.csv`, `outputs/case_reports/GOV-20260630-002/no_go_reason_note.txt`. |
| Mock GOV / EXPORT rows | Fixture-only, not real opportunities. | `outputs/source_scans/daily_morning_autopilot_mock_20260630_130941.json`, `data/agent_run_log.csv` row `RUN-20260630131129-DAILY-RADAR`. |

## 2. Top actionable cases

| Priority | Case | Buyer / authority | Product | Deadline | Source URL | Recommended route | Evidence |
|---:|---|---|---|---|---|---|---|
| 1 | `EXP-20260630-006` | UNDP-PHL - Philippines | Hygiene Supplies | 2026-07-21 | https://procurement-notices.undp.org/view_negotiation.cfm?nego_id=47079 | Deep-read first; Fast Kill only if Quantum docs show eligibility/category blockers. | `data/master_cases.csv`; `data/rfq_master.csv`; `outputs/buyer_verification/EXP-20260630-006.md`. |
| 2 | `EXP-20260630-005` | UNDP-TJK - Tajikistan | Food Kits / Humanitarian Supplies | 2026-07-13 | https://procurement-notices.undp.org/view_negotiation.cfm?nego_id=46967 | Deep-read first; check Quantum documents, line items, eligibility, delivery, and supplier feasibility. | `data/master_cases.csv`; `data/rfq_master.csv`; `outputs/buyer_verification/EXP-20260630-005.md`. |
| 3 | `GOV-20260630-003` | Department of School Education and Literacy, Ministry of Education | Office Stationery and Supplies | 2026-07-10 | https://bidplus.gem.gov.in/showbidDocument/9535449 | Fast Kill, then deep-read if no OEM/past-experience/EMD traps. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |
| 4 | `GOV-20260630-004` | Department of Higher Education, Ministry of Education | Facility management / housekeeping | 2026-07-21 | https://bidplus.gem.gov.in/showbidDocument/9513041 | Fast Kill first because it appears manpower/service-heavy. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |
| 5 | `GOV-20260630-006` | Department of Military Affairs, Ministry of Defence | Furniture and Fixtures | 2026-07-10 | https://bidplus.gem.gov.in/showbidDocument/9284873 | Fast Kill for defence clauses, delivery, quantity, and past experience. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |
| 6 | `GOV-20260630-005` | Department of Military Affairs, Ministry of Defence | Safety Equipment and PPE | 2026-07-06 | https://bidplus.gem.gov.in/showbidDocument/9519946 | Urgent Fast Kill; short deadline plus defence/PPE compliance risk. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |
| 7 | `EXP-20260630-007` | Vasu Amin, Fiji buyer on go4WorldBusiness; company not visible | Agarbatti / incense sticks | Not stated | https://go4worldbusiness.com/inquiries/send/buyleads/1304702/wanted--agarbatti-incense-sticks | Keep WATCHLIST; run buyer KYC/spec capture before any quote. | `data/master_cases.csv`; `data/rfq_master.csv`; `outputs/supplier_shortlists/EXP-20260630-007_agarbatti_fiji_supplier_shortlist.md`. |
| 8 | `EXP-20260630-003` | TradeKey buyer, South Africa; contact hidden pending sign-in | Rice | Not stated | https://importer.tradekey.com/buyoffer/Supply-Inquiry-For-Rice-3849377.html | Buyer verification / Fast Kill only; do not deep-price. | `data/master_cases.csv`; `data/rfq_master.csv`; `outputs/buyer_verification/EXP-20260630-003.md`. |
| 9 | `EXP-20260630-004` | TradeKey buyer, Turkey; partially masked | Juniper Oil | Not stated | https://importer.tradekey.com/buyoffer/Purchase-Inquiry-For-Juniper-Oils-3849579.html | Buyer verification / Fast Kill only; product and buyer evidence are weak. | `data/master_cases.csv`; `data/rfq_master.csv`; `outputs/buyer_verification/EXP-20260630-004.md`. |
| 10 | `GOV-20260630-007` | Municipal Council, Pandharpur | Cleaning / housekeeping service | 2026-06-30 | https://mahatenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndListTendersbyDate&service=direct&session=T&sp=SLC1XLgA5d%2FpTAF%2Fdv235xg%3D%3D | Fast Kill / likely reject: deadline is today. | `data/master_cases.csv`; `outputs/source_scans/gov_radar_batch_20260630131554.md`. |

## 3. Evidence quality and missing information

- `EXP-20260630-005` and `EXP-20260630-006` are the strongest export demand signals: public institutional notices, buyer/country, product, deadline, source URL, and RFQ verification notes are present. Missing: Quantum documents, line items, eligibility, delivery terms, document checklist, and supplier feasibility.
- `GOV-20260630-003` to `GOV-20260630-006` are evidence-backed starter rows, not deep-read cases. Missing: full bid document extraction, BOQ, EMD, buyer clauses, delivery location, OEM/certification terms, turnover/past experience, and penalty terms.
- `GOV-20260630-007` is source-backed but practically deadline-killed unless the owner explicitly wants an emergency manual review.
- `EXP-20260630-003` and `EXP-20260630-004` are public marketplace pages but buyer identity, quantity, deadline, and direct contact path are masked or incomplete.
- `EXP-20260630-007` is better than the TradeKey leads on quantity/destination/payment/incoterms, but still lacks buyer company identity, buyer email/domain, exact fragrance/packing, target price, destination port, import requirements, and proof of funds/advance-payment willingness.
- `EXP-20260630-001`, `EXP-20260630-002`, and `GOV-20260630-001` should not be counted as clean demand signals until their source-evidence gaps are repaired, even though some downstream supplier/pricing artifacts exist.

## 4. Source blockers / credentials needed

- UNDP: public notices are visible, but full tender handling requires UNDP Quantum registration/subscription before any bid action. Evidence: `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`, `data/source_health.csv`.
- TradeKey: public pages are visible, but buyer identity/contact is hidden or partially masked. Evidence: `data/rfq_master.csv`, `outputs/buyer_verification/EXP-20260630-003.md`, `EXP-20260630-004.md`.
- go4WorldBusiness: RFQ facts are captured locally, but buyer company/KYC and commercial seriousness are not independently verified. Evidence: `data/rfq_master.csv`, `outputs/supplier_shortlists/EXP-20260630-007_agarbatti_fiji_supplier_shortlist.md`.
- Alibaba RFQ, FIEO, APEDA AgriXchange, Made-in-China, UNGM, and several blocked B2B/multilateral sources need legitimate research login/browser-session handling; this audit did not log in or bypass anything. Evidence: `outputs/source_scans/export_rfq_batch_scan_20260630_131453.md`, `data/source_health.csv`, `data/portal_access_register.csv`.
- GOV source blockers: Tender Tiger and Tenders Info are paywalled; IREPS needs manual/browser flow; 20:31 intake marked GeM and IREPS as blocked/login-like for that probe while CPPP, eProcure NIC, Punjab, and Maharashtra were reachable. Evidence: `outputs/source_scans/gov_radar_batch_20260630131554.md`, `outputs/external_intake/external_intake_report_20260630_203112.md`, `data/source_health.csv`.

## 5. What Hermes should ask the owner to approve next

1. Approve the internal priority queue: deep-read `EXP-20260630-006` and `EXP-20260630-005`; fast-kill `GOV-20260630-003`, `GOV-20260630-004`, `GOV-20260630-006`, `GOV-20260630-005`, and `GOV-20260630-007`; buyer-verify `EXP-20260630-007`, `EXP-20260630-003`, and `EXP-20260630-004`.
2. Confirm whether Hermes should use the standing-authorized research login/credential policy for UNDP Quantum, TradeKey, go4WorldBusiness, Alibaba, and APEDA evidence capture. Use only legitimate free/research access; pause on paid plans, OTP, CAPTCHA, or legal attestations.
3. Ask Changes on `APR-001` for `EXP-20260630-002` until original buyer/RFQ evidence, second quote proof, concrete risks, recovery path, and compliance notes are corrected.
4. Keep buyer quote, tender submission, portal upload, EMD/payment, DSC, final price, HSN/ITC-HS, origin, delivery, and payment-term commitments blocked behind explicit owner approval.
5. Treat the mock source adapter output as test data only; do not include fixture rows in owner-facing opportunity counts.

## 6. Safety

No external business action executed: no supplier/buyer messages, no tender/RFQ submissions or portal uploads, no payments/EMD/security deposit/advance, no DSC use, no login/captcha/paywall bypass, and no final HSN/ITC-HS classification, origin claim, price, delivery, or payment-term commitment.
