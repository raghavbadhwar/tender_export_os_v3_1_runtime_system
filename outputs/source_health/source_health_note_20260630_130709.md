# Source Health Note — 2026-06-30 13:07:09 IST

Kanban task: t_3e0fdb1f — Daily System Health Check

## Registers read
- data/source_health.csv
- data/plugin_health.csv
- data/agent_run_log.csv

## Source status
- Sources in register: 13
- Source issues flagged for owner brief: 3
- Sources marked Broken: 0
- Tender Tiger (GOV): Paywalled — last_checked=2026-06-15, consecutive_failures=3, url=https://www.tendertiger.com. Note: Paywalled — skip until subscription confirmed.
- Alibaba RFQ (EXPORT): Needs Login — last_checked=2026-06-30, consecutive_failures=0, url=https://rfq.alibaba.com. Note: High volume RFQs. Login needed. Verify buyers carefully.
- FIEO Connect (EXPORT): Needs Login — last_checked=2026-06-20, consecutive_failures=0, url=https://connect.fieo.org. Note: Good quality leads when accessible. Registration needed.

## Plugin/runtime status
- Plugins/tools in register: 11
- Plugin issues flagged for owner brief: 1
- google_drive_external_sync (Google Drive): Working — blocker/warning: gws emitted token-cache decrypt warning but command succeeded. Note: One non-sensitive Drive sync probe succeeded; receipt=receipts/drive_sync/SYSTEM-90PLUS-DELIVERY-TEST_20260630124313_google_drive_sync.json.

## Agent run log signal
- Recent run rows with warnings/errors/non-success status: 7
- RUN-20260630083416 (hermes-chief-operator): status=SUCCESS, errors=0, warnings=5 — Morning operator brief cron: schemas passed; readiness found GOV-20260630-001 and EXP-20260630-001 blocked on one quote proof each; pending approvals APR-001/APR-002; projection dry-run plugin health differs from data register; no external sends/submissions/payments/DSC/classification/origin/price commitments.
- RUN-20260630124511 (90_plus_external_integration_tester): status=SUCCESS, errors=0, warnings=1 — Owner approved harmless external tests. Telegram receipt=receipts/mobile_delivery/SYSTEM-90PLUS-DELIVERY-TEST_20260630124345_final_retry.json; Drive receipt=receipts/drive_sync/SYSTEM-90PLUS-DELIVERY-TEST_20260630124313_google_drive_sync.json; no supplier/buyer/submission/payment/DSC/price/classification/origin action.
- RUN-20260630125936 (codex_audit_operator): status=SUCCESS, errors=0, warnings=5 — EXP-20260630-001 audit complete. RUN-004 quote count unsupported by quote_master; proof count is 1. Supplier search marked incomplete. Six approval-gated supplier drafts prepared but not sent. Compliance draft flags 0902.30 mismatch and 95% curcumin ambiguity.
- RUN-20260630130318 (midday_opportunity_radar): status=SUCCESS_WITH_WARNINGS, errors=0, warnings=2 — Midday opportunity radar cron: mock source adapter recorded 2 fixture opportunities (1 GOV/1 EXPORT) in output-only mode; projection rebuild dry-run completed; schemas passed; active case workspaces refreshed; Kanban reconciliation plan-only produced 4 actions. No external communications, submissions, payments, DSC, final classifications/origin claims, or price commitments. Warnings: dry-run projections differ from live registers (master_cases blank projection row; plugin_health missing mobile/Drive rows) and initial combined shell returned exit_code=1 despite successful component rechecks.
- RUN-20260630130617 (owner_briefing_agent): status=SUCCESS, errors=0, warnings=4 — Generated /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/scripts/../outputs/daily_briefs/brief_20260630.html; pending_approvals=3; risk_items=4

## Reported outputs
- Morning brief regenerated: outputs/daily_briefs/brief_20260630.html
- Source health HTML report refreshed: outputs/source_health/source_health_report.html

## Safety
No supplier/buyer messages, submissions, payments, DSC use, final HSN/ITC-HS, origin claim, or price commitment occurred.

## Recommended owner action
Prioritize owner decisions on pending approval cards, and treat Tender Tiger/FIEO Connect/Alibaba RFQ as access-gated until login/subscription is confirmed. Monitor the Google Drive token-cache warning, but Drive sync remains usable because the last harmless sync succeeded.
