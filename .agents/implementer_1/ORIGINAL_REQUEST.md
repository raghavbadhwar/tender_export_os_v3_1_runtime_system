## 2026-07-06T03:20:33Z
You are teamwork_preview_worker (Implementer 1). Your working directory is /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/implementer_1/.
Your task is to apply and verify the matured scripts, fallbacks, and test cases staged in /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please execute the following steps:
1. Apply the patch /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/stage_deep_research_leads.patch to scripts/stage_deep_research_leads.py.
2. Replace scripts/source_adapters/gem_adapter.py with /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_gem_adapter.py.
3. Replace scripts/source_adapters/cppp_adapter.py with /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_cppp_adapter.py.
4. Copy /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_india_business_portal_selectors.yaml to config/source_selectors/india_business_portal_selectors.yaml.
5. Copy /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_indian_trade_portal_selectors.yaml to config/source_selectors/indian_trade_portal_selectors.yaml.
6. Replace scripts/reconcile_hermes_kanban.py with /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_reconcile_hermes_kanban.py.
7. Copy /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_ingest_learning_loop.py to scripts/ingest_learning_loop.py. Make it executable if needed.
8. Copy the following test files to tests/:
   - /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_test_adapter_fallback.py -> tests/test_adapter_fallback.py
   - /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_test_reconcile_hermes_kanban.py -> tests/test_reconcile_hermes_kanban.py
   - /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_test_india_business_portal.py -> tests/test_india_business_portal.py
   - /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_test_mobile_approval_payload.py -> tests/test_mobile_approval_payload.py
   - /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/explorer_1/proposed_india_business_portal_listing.html -> tests/proposed_india_business_portal_listing.html
9. Run the pytest suite using run_command to verify all tests (including the new ones) pass.
10. Run scripts/system_health_check.py --runtime to verify all system checks pass.
11. Document all the actions taken, the commands executed, and the test results in /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/.agents/implementer_1/handoff.md. Send a message back with the path when done.
