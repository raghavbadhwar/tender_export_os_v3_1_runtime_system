# Hermes Governed FastMCP + OPA Integration — 2026-07-12

## Outcome

Hermes now has a real, typed Tender Export OS service boundary without receiving unrestricted browser, terminal, portal, email, payment, or submission authority.

The live `tender-export-os` profile starts one local stdio server. Hermes-side MCP sampling and elicitation are explicitly disabled, so the server cannot request extra model calls or mid-call user input outside the registered tool contract:

```text
Hermes planner
  -> tender_os FastMCP allowlist
  -> local OPA T0-T5 decision
  -> existing deterministic Tender OS module
  -> typed result + policy receipt
  -> data/events.jsonl policy.decision_recorded
```

`data/events.jsonl` remains canonical. FastMCP is an interface, and OPA is a permission decision point; neither becomes business state.

## Active tools

| Tool | Tier | Capability | External mutation |
|---|---:|---|---|
| `capability_status` | T0 | Live selected-stack health | No |
| `get_case` | T0 | Exact canonical case read | No |
| `search_cases` | T0 | Bounded case search | No |
| `get_source_health` | T0 | Source-health read | No |
| `get_approval_status` | T0 | Approval metadata read | No |
| `evaluate_business_action` | T0 | Read-only T0–T5 policy probe | No |
| `capture_public_web` | T1 | Robots-compliant public HTTPS evidence | No |
| `assess_opportunity` | T2 | Advisory score and Fast Kill review | No |
| `parse_local_documents` | T2 | Workspace-bounded parsing, hashing, and evidence bundle | No |

There is no MCP tool for send, login, signup, upload, submit, payment, DSC, final price, final delivery, HSN/ITC-HS confirmation, origin claim, invoice, PO, blacklist, plugin activation, or public service exposure.

## Approval verification

Hermes/model text cannot assert approval. For T3–T5, `scripts/tender_os_policy.py` checks:

1. exact action and case in `data/approvals_receipts.csv`;
2. `APPROVED` status and named owner;
3. unused `PENDING_APPROVED_EXECUTION` state;
4. readable owner-decision receipt with matching approval, case, action, and state;
5. structured approval card with matching scope hash;
6. a current, unexpired approval window;
7. explicit special controls for T5 actions such as fresh owner command, expert review, or owner-present DSC.

OPA then makes the final fail-closed decision. Missing OPA, invalid Rego, missing receipts, stale approvals, scope mismatch, consumed approvals, unknown actions, CAPTCHA/OTP bypass, credential exfiltration, ledger rewriting, and policy self-promotion all block.

## Typed result

Every tool returns `config/schemas/mcp_tool_result.schema.json`, including status, evidence IDs, source URLs/hashes, bounded confidence, missing information, recommended next action, approval requirement, OPA decision ID/receipt, and `external_side_effects: false`.

## Reproducible files

- `requirements-mcp.txt` and `requirements-mcp.lock.txt`
- `scripts/tender_os_mcp_server.py`
- `scripts/tender_os_mcp_tools.py`
- `scripts/tender_os_policy.py`
- `config/tender_tool_policy.yaml`
- `policies/tender_os_authorization.rego`
- `config/schemas/mcp_tool_result.schema.json`
- `tests/test_tender_os_policy.py`
- `tests/test_tender_os_mcp_tools.py`

The pre-change profile backup is:

`/Users/raghav/.hermes/profile-config-backups/tender-export-os-config-pre-governed-mcp-20260712T070523Z.yaml`

## Verification

```bash
opa check policies/tender_os_authorization.rego
.venv/bin/python scripts/tender_os_policy.py --self-test
.venv/bin/python -m pytest -q tests/test_tender_os_policy.py tests/test_tender_os_mcp_tools.py
hermes -p tender-export-os mcp list
hermes -p tender-export-os mcp test tender_os
.venv/bin/python scripts/audit_hermes_profile_capabilities.py --json
```

The first live MCP call produced a successful typed result, receipt `receipts/policy_decisions/POL-20260712T070603Z-2d8230bde3.json`, and canonical event `EVT-20260712070603-06a7272c02`.

The expanded live Hermes behavioral evaluation passed 27/27 attempts across three independent runs, including the new `opa_allow_is_not_execution` contract. Report: `outputs/hermes_behavioral_eval/HBEVAL-20260712T071405Z-8caae916/report.json`.

Final implementation receipt: `receipts/hermes_runtime/hermes_governed_mcp_opa_20260712T072054Z.json`.

## Why the other projects were not added

The current system already has Playwright/agent-browser capture, public scraping, hashes/screenshots, scheduled corrigenda checks, RapidFuzz, append-only events, job supervision, checkpoints, repeated behavioral evaluation, and small CSV ledgers. Adding Temporal, PostgreSQL/pgvector, Langfuse, Browsertrix, changedetection.io, Kingfisher, OpenSearch, AGE, Splink, or heavyweight OCR now would increase disk, maintenance, privacy, and failure surface without a measured capability gain.

Reconsider them only when a measured threshold appears: workflow recovery failures, query latency/volume, retrieval miss rate, source-proof insufficiency, OCR/layout failure rate, international OCDS feed demand, or dedicated infrastructure.

## Official references

- https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
- https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
- https://gofastmcp.com/v2/servers/tools
- https://www.openpolicyagent.org/docs/integration
