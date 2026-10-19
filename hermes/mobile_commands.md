# Hermes Mobile Commands

## All Available Commands

Use these commands when talking to Hermes on the go. Hermes will read the relevant data files and respond in mobile-friendly format.

---

## Daily Briefing Commands

| Command | What it does |
|---|---|
| `show today brief` | Shows today's full owner brief |
| `show yesterday brief` | Shows yesterday's brief |
| `show source health` | Lists all sources with health status |
| `show plugin health` | Lists Hermes/Codex plugin and runtime health |
| `show kanban` | Shows Hermes Kanban board summary |
| `show pipeline` | Shows all active cases by status |

---

## Opportunity Commands

| Command | What it does |
|---|---|
| `show case <case_id>` | Full case summary and current status |
| `show top cases` | Top 5 cases by score |
| `show gov cases` | All active government tender cases |
| `show export cases` | All active export RFQ cases |
| `show approvals` | All pending approval cards |
| `show rejected today` | Cases rejected today with reasons |
| `show watchlist` | All cases in WATCHLIST status |

---

## Case Action Commands

> ⚠️ These commands prepare actions — they do NOT execute externally. External execution requires your explicit "approve" command.

| Command | What it does |
|---|---|
| `deep read <case_id>` | Trigger deep read agent for this case |
| `find suppliers <case_id>` | Trigger supplier engine for this case |
| `prepare pricing <case_id>` | Trigger pricing agent for this case |
| `produce artifacts <case_id>` | Route artifact production to Codex runtime |
| `create export quote pack <case_id>` | Build export quote pack draft |
| `create bid pack <case_id>` | Build GOV bid pack draft |
| `build pack <case_id>` | Trigger pack builder for this case |
| `archive <case_id>` | Move case to ARCHIVED status |

---

## Approval Commands

| Command | What it does |
|---|---|
| `show approvals` | List all pending approval cards |
| `show approval <case_id>` | Show approval card for specific case |
| `approve case <case_id>` | ✅ Record owner approval — triggers execution |
| `reject case <case_id>` | ❌ Record owner rejection — closes case |
| `ask changes <case_id>` | 🔄 Send back for revisions — agent reworks |

---

## Supplier Commands

| Command | What it does |
|---|---|
| `show supplier history <supplier_id>` | Full supplier scorecard and history |
| `show supplier quotes <case_id>` | All quotes received for a case |
| `blacklist supplier <supplier_id>` | Flag supplier as blacklisted (with reason prompt) |
| `show blacklist` | List all blacklisted suppliers |

---

## Tracker Commands

| Command | What it does |
|---|---|
| `show pending actions` | All execution tracking items needing attention |
| `show deadlines` | Cases sorted by deadline (closest first) |
| `mark payment received <case_id>` | Log payment receipt (requires amount confirmation) |
| `mark delivery done <case_id>` | Log delivery completion |
| `mark won <case_id>` | Mark case as won |
| `mark lost <case_id>` | Mark case as lost with reason prompt |

---

## System Commands

| Command | What it does |
|---|---|
| `run daily scan` | Trigger Radar + Fast Kill agents |
| `run full pipeline` | Trigger full daily autopilot |
| `show agent log` | Show today's agent run log summary |
| `stage memory update` | Prepare a memory update for owner approval |
| `show memory pending` | Show staged memory updates |
| `show skills pending` | Show staged skill updates |
| `run weekly review` | Run weekly learning review |
| `send to ChatGPT research <topic>` | Create bounded ChatGPT research handoff |
| `switch codex runtime on` | Try Codex App-Server Runtime |
| `switch codex runtime auto` | Fall back to automatic runtime selection |
| `help` | Show this command list |

---

## Usage Examples

```
You: show today brief
Hermes: [Today's owner brief — 5 sections]

You: show approvals
Hermes: [Lists all pending approval cards]

You: approve case EXP-20260630-002
Hermes: ✅ Approved. Execution Tracker will monitor quote send and buyer response.
        Receipt: APR-001 | Timestamp: 2026-07-01T10:15:00

You: show supplier history SUP-003
Hermes: [Supplier scorecard for Spice Valley Exports]

You: ask changes GOV-20260630-001
Hermes: What changes do you want? [Hermes prompts for change notes]
You: Reduce EMD budget. Check NSIC exemption option.
Hermes: ✅ Sent to Approval Desk agent with your notes. Will update in next brief.

You: show deadlines
Hermes: 
  [1] GOV-20260630-001 — Stationery Tender — 12 days
  [2] EXP-20260630-001 — Turmeric RFQ — 10 days
  [3] EXP-20260630-002 — Brass Handicraft — 20 days
```

---

## Emergency Commands

| Command | What it does |
|---|---|
| `emergency reject all pending` | Rejects all pending approvals — prompts for confirmation |
| `pause autopilot` | Stops all scheduled agent runs until unpaused |
| `resume autopilot` | Resumes scheduled agent runs |

---

## Notes
- All commands are logged in `data/agent_run_log.csv`
- All approval decisions create receipts in `receipts/owner_decisions/`
- Hermes never executes external actions — it records your decision and the next scheduled agent run picks it up
