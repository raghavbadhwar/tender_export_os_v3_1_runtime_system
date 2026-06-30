# Final Daily Operating Loop

## v4 Daily Loop
1. Hermes wakes up.
2. Hermes checks memory, Kanban, approvals, and Google Drive snapshot.
3. Hermes runs Morning Operator Brief.
4. Hermes triggers Midday Opportunity Radar through cron or owner command.
5. Hermes uses Codex App-Server Runtime for plugin-heavy tasks.
6. Codex scans, parses, edits files, and produces artifacts.
7. Hermes/Kanban tracks tasks and blockers.
8. Codex/Drive sync stores artifacts and records.
9. Hermes shows owner brief and approval cards.
10. Owner approves, rejects, or asks changes.
11. Approved actions execute only through approval-gated flows.
12. Receipts are written.
13. Hermes stages memory and skill updates from corrections.
14. ChatGPT snapshot is generated for boardroom review.
15. Weekly, ChatGPT reviews strategy and Hermes turns approved insights into rules/skills.

## Daily Owner Action Principle
Every daily loop should end with one smallest useful owner action.

## Approval Rule
The loop stops at every external, financial, legal, DSC, classification, origin, final quote, supplier commitment, delivery commitment, or payment terms gate.

## Sources
- `config/hermes_cron.yaml`
- `config/approval_policy.yaml`
- `docs/FINAL_ARCHITECTURE.md`
