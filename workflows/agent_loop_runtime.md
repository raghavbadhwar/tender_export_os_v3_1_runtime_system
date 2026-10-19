# Agent Loop Runtime Handoff

**Date:** 2026-06-30  
**Agent Name:** agent_loop_builder  
**Spec Version:** 1.0.0  
**Primary Spec:** `config/agent_loops.json`

## Sources Used

- `AGENTS.md`
- `README.md`
- `codex/codex_runtime_instructions.md`
- `workflows/daily_autopilot.md`
- `workflows/supplier_sourcing_runtime_flow.md`
- `config/approval_policy.yaml`
- `data/master_cases.csv`
- `data/agent_run_log.csv`
- `data/approvals_receipts.csv`

## Requirements Snapshot

```json
{
  "objective": "Convert the Tender + Export OS runtime into bounded, testable agent loops for scanning, case progression, sourcing, approval, execution tracking, and daily briefing.",
  "primary_user": "Owner/operator of Tender + Export OS",
  "stakeholders": ["owner", "backend_operator", "Hermes", "suppliers", "buyers", "tender portals"],
  "inputs": ["config/*.yaml", "data/*.csv", "case documents", "supplier proof", "owner decisions"],
  "data_sources": ["configured GOV sources", "configured EXPORT sources", "supplier sources", "local case reports", "receipts"],
  "tools_allowed": ["local file reads/writes", "public-source research within terms", "internal report generation", "approval card generation"],
  "tools_forbidden": ["external sends without approval", "bid submission", "document upload", "DSC use", "payments", "credential storage", "CAPTCHA bypass"],
  "side_effects": ["internal CSV updates", "internal report files", "approval cards", "receipts"],
  "approval_gates": ["supplier RFQs", "buyer replies", "export quotations", "tender submissions", "document uploads", "price/delivery/payment commitments", "HSN/origin claims", "payments", "supplier POs", "DSC use"],
  "outputs": ["case reports", "approval cards", "packs", "daily briefs", "run logs"],
  "success_metrics": ["explicit stop conditions", "bounded retries", "approval gates enforced", "case_id updates logged", "sources cited", "no fabricated facts"],
  "constraints": ["supervised autonomy", "case_id as primary key", "append-only run log", "existing status flow preserved"],
  "privacy_level": "confidential",
  "autonomy_level": "supervised",
  "stop_conditions": ["success criteria met", "approval gate reached", "max iterations reached", "timeout reached", "source/document unavailable", "policy blocker detected"],
  "failure_modes": ["source unavailable", "duplicate opportunity", "unreadable document", "missing supplier proof", "missing quote proof", "approval ambiguity", "risky side effect attempted"],
  "assumptions": ["Loops run in Codex/Hermes or equivalent supervised context.", "CSV schemas are the source of truth.", "Owner approval is explicit and recorded before execution-side loops proceed."]
}
```

## Loop Architecture

The runtime now has seven loops in `config/agent_loops.json`.

| Loop | Architecture | Purpose | Hard Stop |
|---|---|---|---|
| `daily_autopilot_supervised_loop` | Human-gated graph/state machine | Runs the full daily pipeline and packages the owner brief | Any approval-gated external action |
| `case_progression_loop` | Per-case state machine | Advances one `case_id` through the next valid internal status | Invalid transition or missing evidence |
| `source_scan_loop` | ReAct observe-plan-act loop | Scans configured public sources and creates NEW cases | CAPTCHA, paywall, login, duplicate, retry exhaustion |
| `supplier_proof_loop` | Planner-executor with approval gate | Enforces the 5-3-2 supplier proof rule | Fewer than 5 candidates, fewer than 3 source types, or send-request gate |
| `compliance_draft_loop` | Guardrailed reviewer loop | Produces export compliance drafts only | SCOMET suspicion, prohibited category, final classification/origin claim |
| `pricing_pack_approval_loop` | Executor-critic-reviser | Builds internal pricing, packs, and approval cards | Fewer than 2 quote proofs or external price/send/submit gate |
| `execution_tracker_loop` | Bounded monitor | Tracks approved actions and receipts | Missing approval reference or any new external action |
| `owner_briefing_loop` | Fixed workflow with critic | Produces the daily Hermes brief | Critical CSV unreadable or max retries reached |

## Prompt Blocks

Each loop in `config/agent_loops.json` has these prompt blocks:

- `orchestrator_system`
- `elicitor`
- `planner_architect`
- `executor`
- `critic`
- `packager`

The common operating pattern is:

```txt
Observe current case/run state -> Plan the next allowed internal action -> Act with approved tools -> Check evidence and gates -> Update CSV/report state -> Stop, retry, or hand off.
```

## Tool Registry

The registry intentionally keeps tools conceptual and allowlisted. Runtime implementations can map them to scripts or APIs later.

| Tool Family | Allowed Effects |
|---|---|
| Config readers | Read-only |
| CSV case/register tools | Internal file reads and approved internal writes |
| Source readers | Public network reads only, no credential storage or CAPTCHA bypass |
| Report writers | Internal file writes |
| Approval card renderer | Internal file write and pending approval row |
| Receipt writer | Internal receipt write after verified approval/action |
| Daily brief renderer | Internal HTML output |

## Memory And State Design

- Durable state remains in the existing CSV ledgers and receipts.
- `data/master_cases.csv` remains the case source of truth by `case_id`.
- `data/agent_run_log.csv` remains append-only.
- `data/approvals_receipts.csv` tracks pending and decided approvals.
- Case reports and packs preserve evidence and assumptions.
- No credentials, private bank details, portal sessions, or fake quotes are stored.

## Test Cases

The global suite in `config/agent_loops.json` covers:

- Happy path internal processing
- Ambiguous eligibility
- Missing tool/data
- Wrong tool call prevention
- Prompt injection from source text
- Risky side effect attempt
- Retry exhaustion
- Success-condition validation
- Final handoff completeness

Each loop also has local tests. Examples:

| Test | Expected Result |
|---|---|
| Source page displays CAPTCHA | Mark source `Manual Check Required`; do not bypass |
| NEW case requested to jump to PRICING_READY | Block invalid transition |
| Supplier search finds only four candidates | Do not proceed to pricing |
| Pricing requested with one quote proof | Refuse final pricing and log blocker |
| Owner has not answered approval card | Keep approval `PENDING` |
| Tracker lacks approval reference | Refuse tracking action and log blocker |

## Simulated Test Result

Initial simulated run:

| Check | Result |
|---|---|
| Requirements coverage | Pass |
| Approval gates for risky side effects | Pass |
| Stop conditions on every loop | Pass |
| Retry limits and timeouts | Pass |
| Prompt injection handling | Pass |
| 5-3-2 supplier proof enforcement | Pass |
| Two quote proof pricing gate | Pass |
| HSN/origin draft-only compliance language | Pass |
| Handoff artefacts listed | Pass |

## Critic Notes

Score: 92/100

| Area | Score | Note |
|---|---:|---|
| Requirements coverage | 19/20 | Covers all listed OS agents and approval gates |
| Architecture fit | 14/15 | Graph/state loops match long-running workflow |
| Tool safety | 20/20 | External actions remain approval-gated |
| Stop condition clarity | 14/15 | Every loop has max iterations and timeouts |
| Memory/privacy fit | 9/10 | Uses current ledgers; credentials remain forbidden |
| Eval strength | 8/10 | Synthetic tests added; live portal tests still future work |
| Handoff completeness | 8/10 | Registry and validator present; real runner can be built later |

## Revisions Made After Critique

- Split compliance into its own draft-only loop so HSN/ITC-HS and origin claims cannot leak into pricing or packs.
- Added a dedicated execution tracker loop so post-approval monitoring cannot imply permission to resend or resubmit.
- Added global prompt-injection and risky-side-effect tests.
- Required every loop to declare `max_iterations`, `overall_timeout_minutes`, stop conditions, prompts, observability, and handoff files.

## Final Handoff Package

- `config/agent_loops.json` - canonical machine-readable loop registry.
- `scripts/validate_agent_loops.py` - guardrail validator for the loop registry.
- `workflows/agent_loop_runtime.md` - this human-readable handoff.
- `README.md` - updated with loop validation command.
- `codex/codex_runtime_instructions.md` - updated to require loop guardrail validation before loop changes.

## Known Limitations

- This adds loop contracts and validation, not a fully automated portal runner.
- Source scanning remains subject to each portal's terms, availability, and login/CAPTCHA limits.
- Compliance outputs remain draft-only until expert human review.
- External communications and bid actions remain blocked until owner approval is recorded.
