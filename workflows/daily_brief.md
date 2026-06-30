# Daily Brief — Workflow Reference

## What Is the Daily Brief?
The daily brief is the owner's morning intelligence report. It is a single HTML file generated every morning that summarises everything happening in the system.

The owner should spend 5–10 minutes on it and know:
1. What was found yesterday/overnight
2. What was automatically rejected and why
3. The 3 best active opportunities and their status
4. What supplier proof is pending
5. What needs their approval decision
6. Any risks or blockers
7. One recommended action for today

## Who Generates It
The Owner Briefing Agent generates it as the final step of the daily autopilot.

**Output file:** `outputs/daily_briefs/brief_YYYYMMDD.html`

## How to Access It
- **Gateway Push (If Configured):** Delivered through the configured Hermes gateway. If no gateway is configured, save the local HTML brief and surface the file path.
- Open directly in browser: `outputs/daily_briefs/brief_20260630.html`
- Via Hermes command: `show today brief`
- Via script: `python3 scripts/generate_daily_brief.py --open`

---

## Structure (7 Sections)
1. New Opportunities Scanned (GOV + EXPORT count)
2. Auto-Rejected Today (count + top reasons)
3. Best Opportunities (top 3 by score)
4. Pending Supplier Proof (cases waiting on quotes)
5. Approval Required (all pending cards)
6. Risks and Blockers (source, supplier, compliance, deadline issues)
7. Recommended Owner Action (ONE thing to do today)

## Template
`templates/daily_brief.html` is the base HTML template.
The Owner Briefing Agent fills in the data and saves the populated version to `outputs/daily_briefs/`.

## Viewing on Mobile
- **Telegram Push**: The formatted text version is pushed directly to your phone via Telegram.
- **HTML responsive view**: Open the HTML file in Safari or Chrome on your phone.
- **On-demand**: Ask Hermes: `show today brief` for a text version.

## Brief Quality Check
A good brief:
- Has the recommended action as ONE clear sentence (not a list)
- Shows all pending approvals with decision deadline
- Never includes raw tender text
- Always shows case IDs with every item
- Flags source health issues if any source is broken
