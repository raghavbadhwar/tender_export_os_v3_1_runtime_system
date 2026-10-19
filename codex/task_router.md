# Task Router — Codex

## How to Route Any Request to the Right Agent

When a new task arrives (from Hermes command, owner request, or scheduled trigger), use this router to determine which agent and which task type applies.

---

## Routing Decision Tree

```
Incoming task
│
├─ "Find new opportunities / run scan"
│   └─ → Radar Agent (Task Type 1 or 2)
│
├─ "Read tender document / deep read <case_id>"
│   └─ → Deep Read Agent (Task Type 3)
│
├─ "Find suppliers / source suppliers for <case_id>"
│   └─ → Supplier Engine Agent (Task Type 4)
│
├─ "Build pricing / prepare pricing for <case_id>"
│   └─ → Pricing Agent (Task Type 5)
│       └─ Check: 2+ quotes received? If not → back to Supplier Engine
│
├─ "Run compliance / export compliance for <case_id>"
│   └─ → Compliance Agent
│
├─ "Build pack / prepare bid / prepare quote for <case_id>"
│   └─ → Pack Builder Agent
│       └─ Check: Pricing done? Compliance done? If not → run those first
│
├─ "Create approval card for <case_id>"
│   └─ → Approval Desk Agent (Task Type 7)
│
├─ "Generate daily brief"
│   └─ → Owner Briefing Agent (Task Type 6)
│
├─ "Run daily autopilot"
│   └─ → Full pipeline (Task Type 1)
│
└─ "Track / follow up / mark as done"
    └─ → Execution Tracker Agent
```

---

## Pipeline Gate Checks

Before running each agent, check these gates:

| Agent | Gate: What Must Be True |
|---|---|
| Fast Kill | `status = NEW` |
| Deep Read | `status = FAST_KILL` and kill score passes |
| Supplier Engine | `status = DEEP_READ` |
| Compliance Agent | `workflow = EXPORT` and `status = SUPPLIER_SEARCH` |
| Pricing Agent | `status = SUPPLIER_SEARCH` and quotes ≥ 2 in quote_master |
| Pack Builder | `status = PRICING_READY` |
| Approval Desk | Pack is complete |
| Execution Tracker | `status = APPROVED` |

If a gate fails → log reason, stop, flag in next brief.

---

## Priority Queue (When Multiple Cases Need Work)

Order of priority:
1. Approval-required cases with imminent deadlines (< 5 days)
2. Deep-read cases where deadline < 10 days
3. Pricing-ready cases (already have supplier quotes)
4. Supplier-search cases (already in pipeline)
5. New cases from today's scan
6. Watchlist cases flagged for review

---

## Daily Autopilot Run Sequence

```
08:30 — Hermes Chief Operator (morning owner brief)
13:00 — Radar Agent (scan sources)
06:30 — Fast Kill Agent (filter new cases)
07:00 — Deep Read Agent (extract surviving cases)
07:30 — Supplier Engine (source suppliers)
08:00 — Compliance Agent (EXPORT cases)
08:00 — Pricing Agent (cases with quotes ready)
08:20 — Pack Builder (pricing-ready cases)
08:40 — Approval Desk (create cards for packed cases)
20:30 — Owner Briefing Agent / Hermes Chief Operator (evening close)
```

Each agent logs to agent_run_log.csv. If any agent fails, subsequent agents still run for other cases.
