# HERMES TENDER EXPORT OS — MAXIMUM CAPABILITY AUDIT AND VISION

Date: 12 July 2026
Profile: `tender-export-os`
Workspace: `/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system`

---

# PART I — HERMES TENDER EXPORT OS — MAXIMUM CAPABILITY AUDIT

## 1. Executive verdict

Verdict: **partially used, with strong safety/control foundations and a real but still early operational loop. It is not operating near its safe maximum.**

What is genuinely live:

- Hermes gateway is running under launchd supervision.
- The active model is `gpt-5.6-terra` via OpenAI Codex OAuth, with a same-provider fallback to `gpt-5.5`.
- Tender OS MCP is visible to the actual session and all 9 bounded tools were discovered and used successfully.
- The event ledger, OPA policy enforcement, receipts, cron scheduler, source-health register, case register, forecast ledgers, public evidence capture lane, browser lane, Gmail-plugin reply monitor, and Kanban board all exist and have current evidence.
- Core source scans for GeM, CPPP, and UNGM ran on 12 July, as did opportunity intelligence, the forecast shadow cycle, source canary, and buyer-reply monitor runs.

What prevents a “strongly used” or “near maximum” verdict:

1. All 9 live cron jobs are deterministic `no_agent` scripts. No scheduled Hermes reasoning job uses skills, a prompt, a model, delegated specialists, or a learning critique loop.
2. The planned weekly learning loop is not currently live in the scheduler: its first scheduled run is 17 July; the previous weekly review is from 30 June and its memory/skill proposals remain staged, not promoted.
3. Forecasting is explicitly uncalibrated: 79 forecasts in the latest run, 249 review records, but 0 mature observations. No calibration metric is valid.
4. External delivery is currently local only. The live Hermes status reports every messaging platform unconfigured, despite older plugin-health rows saying Telegram previously worked.
5. Government and export execution stops intentionally before submission, final quote, payment, DSC, and contractual/legal commitments. The MCP surface has no external-execution tools.
6. Several data/control inconsistencies remain: stale plugin-health claims, cron-config/runtime drift, a degraded 2/3 source canary, and contradictory legacy case narrative. The earlier safe-regression failure cited in this audit was stale and is superseded by the current PASS report at `outputs/regression/full_safe_regression_report.json`.

No utilization percentage was assigned because there is no verified denominator for “maximum business capability,” and a number would be promotional rather than measurable.

## 2. Capability matrix

| Capability | Installed | Configured | Demonstrated | Used operationally | Learning from outcomes | Blocker | Next action |
|---|---:|---:|---:|---:|---:|---|---|
| Hermes runtime / gateway | Yes | Yes | Yes | Yes | Limited | Repeated gateway starts; current service healthy | Monitor restarts and reconcile event-hook frequency |
| Model fallback | Yes | Yes | Config only | No observed failover | No | Same-provider only | Add cross-provider fallback only with approved budget |
| Checkpoints / rollback | Yes | Yes | Snapshot store exists | Unknown | No | Restore not safely tested | Controlled rollback drill |
| Terminal / files | Yes | Yes | Yes | Yes | N/A | `pytest` absent from shell PATH | Standardize runner and `.venv` path |
| Code execution | Yes | Yes | Tool invocation succeeded but returned no usable payload | Unclear | No | Not independently proven useful | Controlled deterministic test |
| Web search | Yes | DDGS | Yes | Available | No | Search only | Keep for discovery |
| Web extraction | Tool visible | No usable extractor | No | No | No | DDGS is search-only | Add extractor only if needed |
| Browser | Yes | Local / agent-browser | Yes | Yes via source radar | Source health only | No residential proxy | Preserve public read-only mode |
| Computer Use | Enabled | Readiness says ready | No | No | No | Recent requirement checks failed | Run doctor before use |
| Delegation / parallel work | Yes | Yes | Parallel tools used | No durable use found | No | Delegation non-durable | Pilot bounded specialists |
| Session recall | Yes | Yes | Yes | Limited | No automatic consolidation | Broad query initially failed | Make weekly review cite prior lessons |
| Kanban | Yes | Yes | Yes via CLI | Partly | No | Current board has 1 blocked card | Reconcile approval blocker |
| Cron | Yes | Yes | Yes | Yes | Deterministic only | No agentic jobs | Controlled agentic weekly review |
| Hooks / event bridge | Yes | Yes | Yes | Yes, metadata only | No learning trigger | Does not trigger case reasoning | Add event-to-Kanban proposals |
| Skills | 87 installed | Yes | Yes | Interactive only evidenced | No patches | Cron loads no skills | Bind to agentic review jobs |
| Built-in memory | Yes | Yes | `memories/MEMORY.md` and `memories/USER.md` exist | Yes, bounded | Weak | No external provider; no promotions | Promote approved durable lessons |
| Trajectory / RL | Hermes supports it | Not enabled | No | No | No | No labelled business outcome base | Keep off until data matures |
| Tender OS FastMCP + OPA | Yes | Yes | Yes | Yes | Audit receipts only | Transient reconnect warnings | Monitor startup/keepalive |
| Gmail-plugin handoff | Repo connector present | Yes | Historic receipts; connector status healthy | Reply monitor running | No replies yet | No direct model-visible execution tool | Keep monitor and route reply to owner |
| Google Drive knowledge bus | Historically verified | Configured | Historic upload receipt | Current manifest mostly dry-run | No | Current live sync not demonstrated | Re-run authorized non-sensitive sync |
| Codex App-Server routing | Historically checked | Yes | Historic health record only | No cron invocation | No | Not re-tested | Use for artifact work with receipts |
| ChatGPT Deep Research bridge | Local packet workflow | Yes | Packet artifacts exist | Manual only | Strategic only | No live Project connection tested | Use cited bounded packets |

## 3. Hermes runtime

- Hermes version: `0.18.2 (2026.7.7.2)`, install commit `4281151a`.
- Active profile: `tender-export-os`.
- Active model/provider: `gpt-5.6-terra` / `openai-codex`.
- Fallback: `openai-codex:gpt-5.5`.
- Reasoning effort: `high`; max turns: `80`; `verify_on_stop: true`.
- Compression: enabled at 70%, target 35%, protects first 3 and last 30 turns.
- Terminal: local backend, 600-second timeout.
- Checkpoints: enabled; 12 snapshots maximum, 300 MB maximum, 7-day retention; populated checkpoint store exists.
- Security: manual approvals; secret redaction enabled; Gmail domains blocked for website access; private URLs disabled; destructive terminal deny patterns include `gws` and `himalaya`.
- Tool-loop guardrails: warn after repeated failures/no progress and hard-stop after repeated failure thresholds.

Gateway:

- Running under launchd, PID `52077` during the audit.
- Service definition matched current Hermes installation.
- Gateway lifecycle events are recorded by `teos-event-bridge`; hook code allowlists only platform, session ID, iteration, and tool names (`scripts/hermes_event_bridge.py:17-78`).
- Multiple `hermes.gateway_started` events occurred in recent hours. This may be intentional restart/reload activity, but should be monitored.

Observed warnings/reliability concerns:

- Tender MCP logged a transient keepalive/reconnection failure around 13:12–13:13. Cold discovery normally needs roughly two to three seconds, so the profile now uses a 20-second bounded discovery timeout and the Hermes one-shot path waits before taking its tool snapshot. The current gate passes 3/3 cold starts and 10/10 warm agent canaries; see `outputs/upgrade_baseline/mcp_discovery_reliability.json`.
- Browser CDP and Computer Use requirement checks intermittently returned false in logs. Browser navigation worked during the audit; Computer Use was not tested.
- The web server reported a 9.4-second event-loop stall attributed to suspected GIL pressure.
- The audit-time safe-regression `FAIL` was a stale snapshot. The canonical report was regenerated through the repository virtual environment and is now `PASS` with all 16 safe checks green at `outputs/regression/full_safe_regression_report.json`.
- Repository tests and validation commands must use `.venv/bin/python`; bare shell `pytest` availability is not the verification contract.

## 4. Native Hermes capabilities

Working and demonstrated:

- File reads/searches, terminal inspection, task tracking, web search, browser navigation, session search, cron inspection, skill loading, memory status, and Tender MCP tools.
- Parallel tool work was used repeatedly.
- Session database: 23 sessions / 180 messages / 5.2 MB.
- Durable Kanban CLI: 4 completed cards and 1 blocked card.

Available but not sufficiently demonstrated:

- Computer Use.
- Filesystem rollback restore.
- Code-execution usefulness.
- Delegated specialist work.
- Agentic cron.
- Webhook/event-triggered case work.
- Cross-provider fallback.
- Codex App-Server invocation from Hermes.
- External messaging delivery.

Profile clarification: `hermes profile list` currently exposes `default`, `brained`, `freshos`, and `tender-export-os`. The legacy Tender specialist names are shell compatibility aliases that all execute `hermes -p tender-export-os`; they are not isolated Hermes profiles and do not provide separate tools, memory, authentication, cron, or gateway state.

Not available now:

- Functional `web_extract`: DDGS is configured as a search-only backend.
- An active external memory provider.
- Active RL / trajectory-learning tooling.
- Tender MCP external-execution action, by design.
- A configured live messaging platform.

## 5. Tender OS MCP, OPA, and event ledger

### Actual session visibility

The actual session exposed all nine MCP tools:

1. `capability_status`
2. `get_case`
3. `search_cases`
4. `assess_opportunity`
5. `get_source_health`
6. `parse_local_documents`
7. `capture_public_web`
8. `get_approval_status`
9. `evaluate_business_action`

`hermes mcp test tender_os` succeeded over stdio. It discovered all 9 selected tools.

A prior session had reported MCP unavailable. This was a real historical limitation, but it is not the current state. The exact root cause cannot be proven from the historical session alone; current evidence indicates a transient discovery/reconnect or pre-registration/restart issue, not missing tool registration.

### OPA and receipts

OPA enforcement is real, not prompt-only:

- FastMCP `3.4.4`, OPA `1.16.2`, Playwright `1.61.0`, and RapidFuzz `3.14.5` were reported active.
- `TenderPolicyEngine` resolves action tier, validates approval rows, owner-decision receipt, structured card, scope hash, expiry, unused external-effect state, and required controls before OPA evaluation.
- Every audited MCP invocation produced a policy receipt and `policy.decision_recorded` event.
- The MCP result contract hard-codes `external_side_effects: false`.
- MCP exposes no execution tool: `mcp_external_execution_tools_exposed: false`.

### Event ledger

`data/events.jsonl` is actively used. It contains current gateway lifecycle events, job started/completed pairs, forecast events, policy decisions, and staged skill/memory proposal events.

## 6. Current operational automations

All jobs are enabled, local-delivery, actual `no_agent` scripts. None has a prompt, skills, model, provider, context chain, or restricted toolset. Some repository YAML records intended Hermes/Codex/ChatGPT runtime labels, but actual scheduler state is deterministic no-agent execution.

| Job | Schedule IST | Mode | Last observed result | Receipt / learning reality |
|---|---|---|---|---|
| Core Source Agent-Browser Radar | 05:30 daily | no-agent | Success, 45 sec; GeM/CPPP/UNGM report PASS | Receipt exists; source-health evidence updated |
| Morning Opportunity Intelligence | 06:00 daily | no-agent | Success; 12 cases analyzed, 15 warnings | Internal reports only; no outcome learning |
| V5 Prediction Shadow and Calibration | 07:15 daily | no-agent | Success | Forecast/backtest updates; 0 mature outcomes |
| Morning Operator Brief | 08:30 daily | no-agent | Success | Deterministic operating desk, not Hermes reasoning |
| Midday Opportunity Radar | 13:00 daily | no-agent | Scheduler success but task `DEGRADED`; 2/3 healthy adapters | Needs adapter investigation |
| Supplier Follow-up Review | 17:00 daily | no-agent | Not yet run | No effectiveness claim possible |
| Buyer Reply Monitor | Every 30 min, 09:00–21:59 | no-agent | 13 successful runs; latest 0 replies, 0 owner actions | Connector works mechanically; no outcome data |
| Evening Execution Close | 20:30 daily | no-agent | Not yet run | No effectiveness claim possible |
| Weekly Learning Review | Friday 18:00 | no-agent | Not yet run | No live scheduled learning review yet |

Each inspected completed job had a `teos_job_supervisor` receipt and event pair.

## 7. Tender-specific skills

All six Tender skills are active. None has ever been patched. Their low use counts include audit-time loading and do not prove sustained operating use.

| Skill | Purpose | Use count | Scheduled use | Patch history | Decision |
|---|---|---:|---|---|---|
| `teos-chief-operator` | Event-ledger-first control plane, approvals, Kanban, owner brief | 2 | No | 0; pinned | Keep |
| `teos-evidence-verifier` | Evidence quality, provenance, dedupe, quote proof | 3 | No | 0; pinned | Keep |
| `teos-prediction-calibration` | Forecast/backtest/calibration discipline | 1 | No | 0; pinned | Keep; needs mature outcomes |
| `teos-buyer-acquisition` | Buyer discovery, staging, gated outreach/replies | 3 | No | 0 | Keep |
| `teos-public-web-scraping` | DDGS → static scraper → browser/adapters | 2 | No | 0 | Keep |
| `teos-recovered-context` | Safe historical Ares archive access | 2 | No | 0 | Keep |

The skills are aligned with v4.1 governance and are not obviously obsolete. Evidence verifier and public-web-scraping overlap at the boundary but have distinct functions: validation versus capture. Do not consolidate yet.

## 8. Memory and learning

### Verdict

**The profile is a governed memory-and-review system with early forecast instrumentation. It is not yet a closed-loop business learning system.**

| Learning type | State | Verdict |
|---|---|---|
| Working memory | Bounded runtime memory/user context | Working |
| Episodic memory | 23 sessions / event ledger | Working |
| Semantic business memory | Built-in memory plus profile-local `memories/MEMORY.md` and `memories/USER.md` | Partial |
| Procedural memory | Six Tender skills | Working but low use/no patches |
| Forecast/model learning | Candidate/backtest/calibration ledgers | Not useful yet |
| Strategic market learning | ChatGPT bridge packets and buyer research artifacts | Partial/manual |

Findings:

- Built-in memory is active; provider is `none — built-in only`.
- Profile-local `memories/MEMORY.md` and `memories/USER.md` exist and are loaded by the profile. Their presence does not make the system outcome-learning-complete; promotion remains governed and external memory remains disabled.
- External memory plugins are installed but no provider is configured or used.
- Exact session search recalled repeated behavioral-contract sessions; a broad query initially returned no result.
- A 30 June weekly review staged one memory proposal and several skill/process proposals. None was applied.
- No trajectory files were found; RL is not enabled.
- No demonstrated loop connects buyer replies, supplier performance, delivery, payment, wins/losses, or forecast errors into approved future rule/model changes.

## 9. Government-tender lifecycle

| Stage | Status | Current reality |
|---|---|---|
| Pre-tender / repeat-buyer intelligence | Partial | Historical scripts exist; no trained outcome model |
| GeM / CPPP monitoring | Working | Core browser radar captured both on 12 July |
| State portal / PSU monitoring | Partial | Maharashtra adapter/case exists; no broad live cadence |
| Corrigenda / retender / extension | Available but unscheduled | Script/prior dry run exist; no dedicated live job |
| Low-competition detection | Partial | Scoring exists; no validated outcome loop |
| Tender / BOQ extraction | Partial | MCP parser available; live cases still have incomplete documents/terms |
| Eligibility / Fast Kill | Working | Live assessment returned WATCHLIST and missing evidence |
| Supplier 5-3-2 sourcing | Partial | Candidate counts exist; strict quote proof gaps remain |
| Quote-proof validation | Working as a gate | Public marketplace prices do not count as strict proof |
| Pricing / working-capital | Available, incomplete operationally | Current case example has `pricing_done=FALSE` |
| Compliance matrix / bid pack | Available but not shown ready | Templates/routing exist |
| Approval-card preparation | Working | Cards, receipts, scope validation, OPA |
| Submission readiness | Partial | Can prepare; cannot submit |
| Submission / DSC / upload | Not available by design | No execution tool |
| Post-submission evaluation | Missing / not evidenced | No live loop found |
| Award, delivery, payment tracking | Data model only | No demonstrated outcome |
| Win/loss / renewal learning | Missing in practice | No mature outcomes |

## 10. Export lifecycle

| Stage | Status | Current reality |
|---|---|---|
| Product-country demand research | Partial | Research and forecast lanes exist; no validated demand model |
| Retailer/importer/distributor discovery | Working for hypotheses | Four public retailer target accounts staged |
| Verified target accounts | Partial | Catalogue fit is not treated as confirmed demand |
| Contact-path verification | Partial | Public paths and Gmail connector exist; no broad verified procurement-contact dataset |
| Outreach drafts | Working | Drafts and approvals exist |
| Gmail-plugin handoff | Working, controlled | Connector reports connected/read-and-report only; historic receipts exist |
| Buyer-reply monitor | Working mechanically | 13 successful monitor runs; 0 replies |
| Reply classification | Available, unproven on real reply | No real substantive classification observed |
| RFQ qualification | Partial | UNDP notices have public evidence but missing full terms |
| Supplier sourcing | Partial | Candidate evidence exists; strict proof incomplete |
| EXW/FOB/CIF pricing | Available, not ready | No proof-supported final price |
| Compliance/classification | Draft only | Stops before final claims |
| Quote-pack preparation | Available but not demonstrated ready | No fully ready pack evidenced |
| Negotiation assistance | Draft-only | Cannot accept commercial terms |
| Order/shipment/invoice/payment | Missing / not evidenced | No live order-to-cash evidence |
| Repeat-buyer prediction | Not useful | No mature repeat outcomes |

## 11. Forecasting and decision intelligence

- Current model: `teos-expert-prior-v1`.
- Latest forecast-generated event: 79 forecasts.
- Latest calibration status: `INSUFFICIENT_MATURE_SAMPLE`.
- Minimum mature sample: 30.
- Mature sample: 0.
- Excluded unmatured/unscored backtest records: 249.
- Brier score: null.
- Observed success rate: null.
- Calibration bins: none.
- Probability label: `PRIOR_UNCALIBRATED`.

Government and export rows are separated by workflow field but share the same expert-prior model; they are not separate trained models.

## 12. Underutilised capabilities

1. Agentic Weekly Learning Review.
2. Outcome-to-learning promotion.
3. Kanban-driven case routing.
4. Event-triggered exception proposals.
5. Session-search-based operational recall.
6. Champion/challenger skill tests.
7. Delegated internal specialists.
8. Cross-provider fallback.
9. Computer Use after readiness validation.
10. External memory/vector DB only after a measured retrieval bottleneck.
11. RL only after sufficient labelled mature outcomes.

## 13. Safe demonstrations

| Demonstration | Result | External action |
|---|---|---|
| `capability_status()` | FastMCP, OPA, Playwright, event ledger, document intelligence, and public-web evidence active; no MCP execution tools | None |
| `get_case(GOV-20260630-001)` | Retrieved live GOV case in `SUPPLIER_SEARCH` | None |
| `search_cases(limit=20)` | Returned 18 GOV/EXPORT cases | None |
| `get_source_health(limit=20)` | Returned 20 sources with Working/login/paywall/block states | None |
| `assess_opportunity(GOV-20260630-001)` | Score 78, but advisory WATCHLIST due to proof gaps | None |
| `evaluate_business_action(submit_tender, GOV-20260630-001)` | Blocked as prohibited; `execution_tool_exposed=false` | None |
| Tender skill loading | Loaded chief-operator and peer Tender skills | None |
| Session search | Recalled prior behavior evaluations | None |
| Cron inspection | Found 9 active jobs, all no-agent | None |
| Browser navigation | Loaded `https://example.com` | Read-only request only |
| Web search | DDGS returned results | Read-only request only |

Audit-time internal writes were only OPA policy receipts and ledger records deliberately generated by read/probe MCP calls.

## 14. Immediate fixes

1. Reconcile cron configuration language with actual all-no-agent scheduler state.
2. Preserve the regenerated safe-regression PASS and treat older FAIL artifacts as historical only.
3. Diagnose the degraded 2/3 source canary.
4. Reconcile stale Telegram/plugin-health claims with actual gateway state: all live messaging platforms report unconfigured and all current cron delivery is local.
5. Reconcile case narrative, approval `external_effect`, connector receipts, and case status where notes say both “not sent” and “sent.”
6. Keep repository verification standardized on `.venv/bin/python` and the recorded validation receipts.
7. Revalidate 30 June staged learning proposals before promotion.

## 15. 30/60/90-day roadmap

### Days 0–30

- Correct cron documentation/runtime labels.
- Reconcile plugin health with gateway truth.
- Make project test command reproducible.
- Add source-canary degradation escalation.
- Repair public-template scanner scope.
- Add consistency validation across case notes, approval status, external effects, and receipts.
- Define structured GOV and EXPORT outcome schemas.
- Obtain owner decision on a local-only agentic weekly review pilot.

### Days 31–60

- Turn Weekly Learning Review into constrained local-only Hermes agentic cron, with Tender skills and no external tools.
- Add outcome ingestion/maturity checks separately for GOV and EXPORT.
- Add event-ledger/Kanban/approval/receipt reconciliation.
- Add source-yield metrics distinguishing public leads from document-backed cases.
- Pilot champion/challenger skill evaluations.

### Days 61–90

- Require structured closure for every case.
- Collect 30 mature, time-separated outcomes before probability claims.
- Separate GOV and EXPORT forecast specifications.
- Build supplier reliability, buyer repeat, source-yield, and payment-delay models only from verified outcomes.
- Add release gates for model/skill changes: fixtures, behavioral repeats, time-separated backtest, owner approval.

## 16. Owner summary

### Five strongest capabilities now

1. Governed Tender MCP with real OPA enforcement.
2. Public evidence monitoring for GeM, CPPP, and UNGM.
3. Strong approval boundaries with receipts and scope validation.
4. Deterministic operational rhythm with supervised receipts.
5. Evidence-aware buyer acquisition and Gmail-plugin reply-monitor infrastructure.

### Five largest underutilised capabilities

1. Agentic weekly learning review.
2. Outcome-driven memory/skill promotion.
3. Kanban-driven execution.
4. Event-triggered escalation.
5. Session search and behavioral evaluation as recurring operating inputs.

### Five concrete next actions

1. Fix scheduler/config mismatch and choose which jobs become agentic.
2. Repair safe-regression public-runtime scan.
3. Investigate degraded source canary.
4. Reconcile messaging/plugin health with live gateway.
5. Approve a constrained, local-only Weekly Learning Review pilot.

### Single most important action

**Approve a narrowly scoped local-only agentic Weekly Learning Review pilot, after correcting the cron/config truth gap.**

---

# PART II — WHAT I WOULD DO TO TAKE HERMES TO ITS SAFE MAXIMUM CAPABILITY

“Absolute capability” should not mean unrestricted authority to send, submit, pay, use credentials, or make legal/commercial commitments. For Tender Export OS, the strongest form is maximum capability in sensing, proving, prioritising, drafting, remembering, criticising, and improving—while retaining human authority for irreversible business decisions.

The target loop is:

**Sense → Verify → Remember → Reason → Draft → Gate → Act through approved connectors → Observe → Learn → Propose → Test → Approve → Promote**

## 1. Make Hermes the actual operating brain

Keep deterministic jobs for capture, parsing, dedupe, validation, projections, and receipts. Add three strictly governed agentic Hermes jobs.

### Morning Chief Operator

- Reads only fresh source receipts, case changes, deadlines, Kanban, approvals, source health, forecast deltas, and reply-monitor results.
- Produces one owner brief: best opportunities, urgent evidence gaps, and one smallest owner decision.
- Creates/updates Kanban cards only.
- No external action.

### Intraday Exception Officer

Wakes only on meaningful events:

- deadline threshold;
- source degradation;
- substantive buyer reply;
- new approval request;
- quote-proof contradiction;
- forecast maturity;
- failed job.

It diagnoses the exception, prepares a remedy, and creates typed `needs_input` cards where needed. It never sends messages or changes commercial state.

### Weekly Learning Council

- Uses Tender skills, session recall, event ledger, source yield, case outcomes, supplier performance, buyer replies, forecast error, and failed-run receipts.
- Proposes memory updates, skill patches, source-adapter repairs, score/model changes, test additions, and process retirements.
- Never applies them without owner approval.

Every agentic job should be local-delivery first, skill-scoped, tool-restricted, and receipt-backed.

## 2. Make the event ledger a business nervous system

Add typed events for economically meaningful observations:

- `source.record_captured`
- `source.adapter_degraded`
- `tender.corrigendum_detected`
- `tender.deadline_changed`
- `case.fast_kill_completed`
- `supplier.candidate_verified`
- `supplier.quote_received`
- `supplier.quote_rejected`
- `buyer.target_staged`
- `buyer.reply_received`
- `buyer.opted_out`
- `buyer.rfq_verified`
- `approval.requested`
- `approval.expired`
- `execution.receipt_ingested`
- `case.outcome_recorded`
- `payment.received`
- `forecast.matured`
- `learning.proposal_staged`
- `learning.promoted`

Use event-triggered rules to create safe work automatically:

- deadline extension → reopen Fast Kill / Deep Read;
- corrigendum → create document-diff task;
- substantive buyer reply → halt automatic flow and create owner action;
- source failure streak → create source-adapter repair task;
- forecast maturity → schedule backtest/calibration;
- payment delay → update evidence, not a model directly.

## 3. Create a proper case graph

Every case should be a durable graph:

Case → source evidence → documents/BOQs/corrigenda → extracted requirements → eligibility evidence → supplier candidates → strict quote proofs → draft pricing assumptions → compliance draft → approval cards → approved external-action packets → connector receipts → outcome → post-mortem / learning attribution.

This enables machine-detectable contradictions:

- no `SENT_OR_SUBMITTED` without receipt;
- no pricing-ready state without two strict quote proofs;
- no public marketplace listing treated as a quote;
- no approval left pending after verified external receipt;
- no conflicting “sent” and “not sent” statement without reconciliation exception.

## 4. Use specialist agents without giving them authority

Create constrained durable roles:

- Source Intelligence Auditor: adapters, yield, access boundaries, evidence quality.
- Tender Requirements Critic: Deep Read completeness and clause gaps.
- Supplier Proof Auditor: 5-3-2, provenance, validity, MOQ, lead time, readiness.
- Pricing Red Team: freight, payment delay, working capital, margin, L1 sensitivity; draft only.
- Export Compliance Draft Critic: preserve draft-only HSN/ITC-HS, origin, SCOMET, certificate, and Incoterm output.
- Buyer Response Triage Officer: classify Gmail-plugin replies and turn substantive replies into owner actions; stop opt-outs/bounces automatically.
- Learning Auditor: compare forecast, evidence, recommendation, approval, and outcome; propose corrections.

Use delegation for bounded analysis, Kanban for durable work, and MCP/file evidence for grounding.

## 5. Collect outcomes before building advanced models

The first serious ML investment should be outcome hygiene, not model complexity.

For every GOV case record:

- bid/not bid;
- reason not bid;
- technical qualification;
- bidder/competition information where known;
- L1 / award / loss;
- timing;
- delivery performance;
- payment date/delay;
- renewal/repeat signal.

For every EXPORT case record:

- target-account stage;
- reply class;
- RFQ verified or not;
- supplier response;
- quote sent or not;
- quote accepted/rejected/no response;
- PO value;
- shipment milestones;
- payment terms and receipt;
- repeat inquiry/order;
- loss reason.

Then build separately versioned models:

1. GOV bid-worthiness / justified-kill model.
2. GOV buyer-repeat / retender model.
3. GOV competition / L1-risk model.
4. Export target-account reply model.
5. Export RFQ-conversion model.
6. Supplier reliability and quote-response model.
7. Payment-delay / working-capital-risk model.
8. Source-yield model.

Every output must name target, horizon, workflow, model version, feature snapshot, maturity rule, sample size, calibration state, evidence level, and proof gaps. No model authorizes an external action.

## 6. Make skills self-improving through promotion gates

Use this lifecycle:

1. A recurring failure, contradiction, owner correction, or repeated success appears.
2. Hermes records `learning.proposal_staged`.
3. It drafts a skill patch with evidence, affected workflows, fixtures/tests, and rollback plan.
4. Champion/challenger evaluation runs: current skill versus proposed skill, same fixtures, three repeats, no external tools.
5. Owner approves promotion.
6. The patch is applied, versioned, and cited in future runs.
7. A later review measures whether the original error declined.

This lets Hermes improve without silently rewriting the business.

## 7. Turn session history into controlled recall

- Daily operations recall only unresolved decisions and prior owner corrections.
- Weekly review searches repeated source failures, approval rejections, proof disputes, buyer-reply handling, price/compliance corrections, missed deadlines, and failed tests.
- Recovered Ares context remains separate, read-only, and must be reverified.
- No raw tenders, emails, credentials, supplier dumps, or private buyer data enter durable memory.

## 8. Route work to the right runtime

| Need | Best runtime |
|---|---|
| Broad market/category/country thesis | ChatGPT Deep Research |
| Exact public source capture | Python / Playwright / agent-browser |
| Structured parsing, documents, spreadsheets, packs | Codex App-Server |
| Operating brief, approvals, routing, critique | Hermes |
| Durable case work / handoffs | Hermes Kanban |
| High-volume deterministic validation | Supervisor-controlled no-agent cron |
| Email send/reply receipts | Gmail plugin only |
| Shared long-lived context | Google Drive Knowledge Bus |
| Canonical state / audit truth | Event ledger |

The goal is orchestration, not forcing one tool to do everything.

## 9. Build an exception-first control tower

The operator view should surface only:

- deadline threshold;
- source degradation;
- evidence gap;
- insufficient quote proof;
- unresolved price assumption;
- expiring approval;
- substantive buyer reply;
- mature forecast;
- stale Kanban task;
- missing receipt;
- projection contradiction;
- overdue payment.

Owner view:

1. What changed?
2. What is proved?
3. What is blocked?
4. What is the smallest safe next action?
5. What decision is required?

## 10. Preserve hard boundaries even at maximum capability

Never automate without explicit owner control and dedicated execution tooling:

- tender submission;
- DSC use;
- payment, EMD, BG, advance, or bank action;
- final bid price;
- delivery commitment;
- payment-term acceptance;
- purchase orders;
- final HSN/ITC-HS;
- origin claim;
- legal/compliance declaration;
- unsupervised buyer or supplier messaging;
- CAPTCHA/login bypass;
- private portal scraping;
- permanent supplier blacklisting.

## End state

Every day, the system should:

- capture source evidence;
- kill weak leads quickly;
- convert strong leads into evidence-backed cases;
- check requirements, supplier proof, pricing proof, and compliance drafts continuously;
- turn replies and operational changes into safe owner actions;
- require scoped approval and receipt for every external effect;
- learn from outcomes into source selection, supplier ranking, case scoring, and skills;
- test every proposed learning change before promotion;
- give the owner one concise decision surface instead of an operational data dump.

That is the cutting-edge safe deployment: a continuously learning, evidence-grounded, self-auditing commercial operating system—not an uncontrolled tender-submission bot.
