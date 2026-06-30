#!/usr/bin/env python3
from __future__ import annotations

from html import escape
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "outputs" / "diagrams" / "detailed"


CSS = """
  .bg { fill: #050607; }
  .title { fill: #f4f6f1; font: 800 40px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .subtitle { fill: #c4c9c2; font: 600 20px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .section { fill: #eff5ed; font: 800 27px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .h1 { fill: #f2f8ef; font: 800 24px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .body { fill: #c7d6c8; font: 600 17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .small { fill: #b9c2b8; font: 600 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .tiny { fill: #a8aea6; font: 600 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .card { stroke-width: 2.1; rx: 16; ry: 16; filter: url(#shadow); }
  .mini { stroke-width: 1.7; rx: 11; ry: 11; filter: url(#shadow); }
  .hermes { fill: #0a5a49; stroke: #31d0a3; }
  .agent { fill: #0a4d40; stroke: #28bd96; }
  .ledger { fill: #4d390d; stroke: #e0ad34; }
  .projection { fill: #464844; stroke: #aeb0a6; }
  .codex { fill: #0a4d68; stroke: #42c8f0; }
  .chatgpt { fill: #443692; stroke: #8e82ff; }
  .drive { fill: #3f4542; stroke: #b9bbb2; }
  .owner { fill: #6e4309; stroke: #f1a22c; }
  .approval { fill: #5c1f28; stroke: #f16e7f; }
  .source { fill: #233b45; stroke: #69b8d0; }
  .validate { fill: #28324f; stroke: #7c9cf6; }
  .line { fill: none; stroke-width: 3; marker-end: url(#arrow); }
  .thin { stroke-width: 2; }
  .dash { stroke-dasharray: 10 8; }
"""


def text_lines(lines: list[str], x: int, y: int, cls: str = "body", gap: int = 26, anchor: str = "middle") -> str:
    return "\n".join(
        f'<text class="{cls}" x="{x}" y="{y + i * gap}" text-anchor="{anchor}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )


def box(x: int, y: int, w: int, h: int, title: str, lines: list[str], kind: str, title_y: int = 40) -> str:
    cx = x + w // 2
    body_y = y + title_y + 36
    return "\n".join(
        [
            f'<rect class="card {kind}" x="{x}" y="{y}" width="{w}" height="{h}"/>',
            f'<text class="h1" x="{cx}" y="{y + title_y}" text-anchor="middle">{escape(title)}</text>',
            text_lines(lines, cx, body_y, "body", 26),
        ]
    )


def mini(x: int, y: int, w: int, h: int, title: str, lines: list[str], kind: str) -> str:
    cx = x + w // 2
    return "\n".join(
        [
            f'<rect class="mini {kind}" x="{x}" y="{y}" width="{w}" height="{h}"/>',
            f'<text class="h1" x="{cx}" y="{y + 34}" text-anchor="middle">{escape(title)}</text>',
            text_lines(lines, cx, y + 62, "small", 21),
        ]
    )


def arrow(x1: int, y1: int, x2: int, y2: int, color: str, dash: bool = False) -> str:
    d = " dash" if dash else ""
    return f'<path class="line{d}" stroke="{color}" d="M{x1} {y1} L{x2} {y2}"/>'


def shell(title: str, subtitle: str, body: str, width: int = 1800, height: int = 1200) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <style>{CSS}</style>
    <filter id="shadow" x="-8%" y="-8%" width="116%" height="125%">
      <feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#000" flood-opacity="0.36"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#d2d8cf"/>
    </marker>
  </defs>
  <rect class="bg" width="{width}" height="{height}"/>
  <text class="title" x="{width // 2}" y="58" text-anchor="middle">{escape(title)}</text>
  <text class="subtitle" x="{width // 2}" y="94" text-anchor="middle">{escape(subtitle)}</text>
  {body}
</svg>
"""


def footer() -> str:
    return "\n".join(
        [
            '<rect class="mini projection" x="70" y="1110" width="1660" height="58"/>',
            '<text class="tiny" x="900" y="1134" text-anchor="middle">Current live registers: 13 cases, 671 events, 3 approvals, 14 suppliers, 5 quotes, 6 RFQs, 6 buyers. Safe health check: 16/16 passed.</text>',
            '<text class="tiny" x="900" y="1158" text-anchor="middle">Generated from Tender Export OS v4.1 repo state: manifest.json, AGENTS.md, HERMES.md, config/*, data/*, scripts/*.</text>',
        ]
    )


def diagram_control_plane() -> str:
    body = "\n".join(
        [
            box(70, 150, 330, 170, "Owner Interface", ["Telegram / CLI / Hermes commands", "Approves, rejects, asks changes", "Receives brief + approval cards"], "owner"),
            box(510, 130, 420, 210, "Hermes Chief Operator", ["Control plane and daily rhythm", "Routes agents, Kanban, approvals", "Reads HERMES.md, SOUL.md, AGENTS.md", "Writes run log + owner brief"], "hermes"),
            box(1040, 130, 320, 210, "Scheduler", ["config/hermes_cron.yaml", "config/agent_loops.json", "config/loop_schedule.json", "Timeouts and stop conditions"], "validate"),
            box(1460, 130, 270, 210, "Hermes Kanban", ["Durable workboard", "Tasks and blockers", "Approval cards", "Projected, not canonical"], "projection"),
            arrow(400, 235, 510, 235, "#f1a22c"),
            arrow(930, 235, 1040, 235, "#31d0a3"),
            arrow(1360, 235, 1460, 235, "#31d0a3"),
            mini(95, 450, 280, 112, "Owner Commands", ["status, approve, reject", "ask changes, steer priority"], "owner"),
            mini(450, 430, 330, 152, "Hermes Inputs", ["SOUL.md", "docs/FINAL_ARCHITECTURE.md", "config/approval_policy.yaml", "data/master_cases.csv"], "hermes"),
            mini(830, 430, 330, 152, "Daily Outputs", ["outputs/daily_briefs/*.html", "receipts/approvals/*", "data/agent_run_log.csv", "Kanban route notes"], "projection"),
            mini(1210, 430, 300, 152, "Cron Jobs", ["06:00 morning intelligence", "08:30 operator brief", "13:00 opportunity radar", "17:00 supplier review"], "validate"),
            mini(95, 680, 340, 155, "Evening / Weekly Jobs", ["20:30 execution close", "Friday 18:00 learning review", "Monthly strategy research", "All stop at approval gates"], "validate"),
            mini(500, 680, 390, 155, "Runtime Routing", ["Hermes: orchestration and owner interaction", "Codex: artifacts, plugins, files", "ChatGPT: bounded research", "Drive/Kanban: projections"], "hermes"),
            mini(955, 680, 355, 155, "Control-Plane Guardrails", ["No public service exposure", "No final legal/compliance claims", "No irreversible action without approval", "No secrets in repo/logs"], "approval"),
            mini(1375, 680, 300, 155, "State Rule", ["data/events.jsonl is canonical", "CSVs/Kanban/Drive are views", "Every run logs a row", "Every output cites sources"], "ledger"),
            footer(),
        ]
    )
    return shell("Detail 01 - Control Plane, Owner Interface, Scheduler, Kanban", "How Hermes runs the working system and routes owner-supervised automation.", body)


def diagram_agent_pipeline() -> str:
    items = [
        (90, 170, "1 Radar", ["Find GOV and EXPORT leads", "Assign case IDs", "Update source health"], "agent"),
        (395, 170, "2 Fast Kill", ["Apply kill rules", "Score 0-100", "Reject or watchlist"], "agent"),
        (700, 170, "3 Deep Read", ["Extract PDF/BOQ/RFQ fields", "Eligibility, terms, deadlines", "Unreadable docs become blockers"], "agent"),
        (1005, 170, "4 Supplier Engine", ["5 candidate suppliers", "3 source types", "2 quote proofs before pricing"], "agent"),
        (1310, 170, "5 Pricing", ["Cost waterfall", "Draft bid/quote price", "No final commitment"], "agent"),
        (90, 430, "6 Compliance", ["Draft HSN/ITC-HS only", "DGFT/SCOMET flags", "Origin never final"], "agent"),
        (395, 430, "7 Pack Builder", ["Bid packs", "Export quote packs", "Risk and missing items"], "agent"),
        (700, 430, "8 Approval Desk", ["Decision card", "Benefit, risk, recovery", "Approve / Reject / Ask"], "approval"),
        (1005, 430, "9 Execution Tracker", ["Post-approval tracking", "Receipts", "No resend without command"], "agent"),
        (1310, 430, "10 Owner Briefing", ["Daily concise brief", "Top approvals and blockers", "One smallest useful action"], "agent"),
        (505, 700, "11 Codex Plugin Factory", ["Artifacts and parser tooling", "Plugin receipts", "No external sends"], "codex"),
    ]
    parts = []
    for x, y, title, lines, kind in items:
        width = 330 if title == "11 Codex Plugin Factory" else 245
        parts.append(mini(x, y, width, 145, title, lines, kind))
    arrows = [
        arrow(335, 242, 395, 242, "#28bd96"),
        arrow(640, 242, 700, 242, "#28bd96"),
        arrow(945, 242, 1005, 242, "#28bd96"),
        arrow(1250, 242, 1310, 242, "#28bd96"),
        arrow(1432, 315, 1432, 382, "#28bd96"),
        arrow(1432, 382, 212, 382, "#28bd96"),
        arrow(212, 382, 212, 430, "#28bd96"),
        arrow(335, 502, 395, 502, "#28bd96"),
        arrow(640, 502, 700, 502, "#f16e7f"),
        arrow(945, 502, 1005, 502, "#f16e7f"),
        arrow(1250, 502, 1310, 502, "#28bd96"),
        arrow(832, 575, 832, 700, "#42c8f0", True),
    ]
    body = "\n".join(
        parts
        + arrows
        + [
            box(75, 880, 500, 185, "Shared Agent Contract", ["Read/write by case_id", "Append data/agent_run_log.csv after each run", "Cite source files and links", "Stop at configured approval gates"], "projection"),
            box(650, 880, 480, 185, "Status Contract", ["NEW -> FAST_KILL -> WATCHLIST / REJECTED", "DEEP_READ -> SUPPLIER_SEARCH -> PRICING_READY", "ARTIFACT_PRODUCTION -> APPROVAL_REQUIRED", "APPROVED -> SENT_OR_SUBMITTED -> FOLLOW_UP"], "validate"),
            box(1205, 880, 520, 185, "Forbidden Across Agents", ["No fabricated documents, buyer verification, supplier claims", "No final HSN/ITC-HS, origin, price, or delivery claim", "No DSC, payment, bid upload, buyer quote without approval"], "approval"),
            footer(),
        ]
    )
    return shell("Detail 02 - Operating Agent Pipeline", "The actual 11-agent roster and the state-machine contract each agent must obey.", body)


def diagram_state_registers() -> str:
    body = "\n".join(
        [
            box(640, 150, 520, 230, "Canonical State", ["data/events.jsonl", "Append-only event ledger", "671 current events", "Every durable state change cites sources"], "ledger"),
            mini(90, 180, 360, 130, "Event Schema", ["config/schemas/event.schema.json", "allowed event/object types", "validated by script"], "validate"),
            mini(1350, 180, 360, 155, "Event Writers", ["case updates", "approval cards", "Drive sync receipts", "evidence captures"], "agent"),
            arrow(450, 245, 640, 245, "#7c9cf6"),
            arrow(1350, 245, 1160, 245, "#28bd96"),
            box(90, 490, 430, 260, "Projection Rebuild", ["scripts/rebuild_projections_from_events.py", "data/events.jsonl -> CSV projections", "CSV files are working views", "Never treat views as competing truth"], "validate"),
            box(685, 490, 430, 260, "Core Registers", ["data/master_cases.csv", "data/rfq_master.csv", "data/buyer_master.csv", "data/supplier_master.csv", "data/quote_master.csv"], "projection"),
            box(1280, 490, 430, 260, "Health / Control Registers", ["data/approvals_receipts.csv", "data/source_health.csv", "data/plugin_health.csv", "data/drive_manifest.csv", "data/agent_run_log.csv"], "projection"),
            arrow(900, 380, 900, 490, "#e0ad34"),
            arrow(520, 620, 685, 620, "#aeb0a6"),
            arrow(1115, 620, 1280, 620, "#aeb0a6"),
            box(90, 850, 430, 170, "Current Register Counts", ["13 cases: 7 GOV + 6 EXPORT", "9 NEW, 2 SUPPLIER_SEARCH", "1 APPROVAL_REQUIRED, 1 REJECTED", "3 approvals, 14 suppliers, 5 quotes"], "ledger"),
            box(685, 850, 430, 170, "Schema Validation", ["scripts/validate_register_schemas.py", "10 CSV schemas + event ledger", "Current result: PASS", "CSV row/header integrity checked"], "validate"),
            box(1280, 850, 430, 170, "Output Consumers", ["Hermes Kanban", "Google Drive sync", "Daily briefs", "Dashboards and approval cards"], "drive"),
            footer(),
        ]
    )
    return shell("Detail 03 - Canonical State, Registers, and Projections", "The working model around data/events.jsonl and the register/projection layer.", body)


def diagram_approval_safety() -> str:
    body = "\n".join(
        [
            box(70, 150, 470, 215, "Mode A - Allowed Internal Work", ["scan sources, extract fields, score opportunities", "create case IDs, fast-kill, deep-read", "draft pricing/compliance, case reports, briefs", "standing-authorized supplier outreach with receipts"], "agent"),
            box(665, 150, 470, 215, "Mode B - Per-Case Approval Gates", ["buyer RFQ reply, export quotation, tender bid", "document upload, DSC use, payments", "final price, HSN/ITC-HS, origin, delivery", "purchase order or payment-term acceptance"], "approval"),
            box(1260, 150, 470, 215, "Mode C - Execution Tracking", ["track supplier/buyer replies after approval", "track quote validity and deadlines", "record receipts and case status", "internal reminders only"], "hermes"),
            arrow(540, 258, 665, 258, "#f16e7f"),
            arrow(1135, 258, 1260, 258, "#f16e7f"),
            box(90, 485, 440, 235, "Approval Card Required Fields", ["case_id, workflow, proposed action", "business object and amount", "benefit, concrete risk, recovery path", "sources, confidence, missing info, options"], "projection"),
            box(680, 485, 440, 235, "Standing Authorization Limits", ["supplier quote/availability requests allowed", "portal login/signup for research allowed", "secrets only in Keychain/approved store", "OTP/CAPTCHA pauses for owner help"], "owner"),
            box(1270, 485, 440, 235, "Hard Stop Conditions", ["required evidence missing", "SCOMET/prohibited suspicion", "Codex/plugin/auth unavailable", "Drive connector unavailable for sync"], "approval"),
            box(90, 835, 440, 190, "Receipts", ["receipts/approvals", "receipts/supplier_quotes", "receipts/submissions", "receipts/owner_decisions"], "projection"),
            box(680, 835, 440, 190, "Memory Discipline", ["memory writes require approval", "raw tenders/RFQs and supplier tables excluded", "credentials, DSC, bank details never saved"], "validate"),
            box(1270, 835, 440, 190, "Audit Trail", ["data/events.jsonl", "data/agent_run_log.csv", "source citations in every output", "approval status remains explicit"], "ledger"),
            footer(),
        ]
    )
    return shell("Detail 04 - Approval, Safety, and Execution Boundaries", "The current approval policy and safety model, including standing authorizations and hard gates.", body)


def diagram_codex_runtime() -> str:
    body = "\n".join(
        [
            box(70, 150, 430, 200, "Codex Runtime Policy", ["config/codex_runtime_policy.yaml", "default_runtime: codex_app_server", "fallback_runtime: auto", "verify before use"], "codex"),
            box(685, 150, 430, 200, "Artifact Jobs", ["case reports, bid packs, quote packs", "pricing workbooks and scorecards", "approval cards and dashboards", "parser/source-adapter tooling"], "codex"),
            box(1300, 150, 430, 200, "Plugin Routing", ["config/plugin_routing.yaml", "documents, pdf, spreadsheets, presentations", "finance, sales, legal draft tools", "browser/chrome/testing/data plugins"], "validate"),
            arrow(500, 250, 685, 250, "#42c8f0"),
            arrow(1115, 250, 1300, 250, "#42c8f0"),
            box(70, 480, 430, 235, "Codex Inputs", ["config/plugin_routing.yaml", "data/capability_registry.csv", "data/plugin_health.csv", "case reports and pricing drafts", "approved templates"], "projection"),
            box(685, 480, 430, 235, "Codex Outputs", ["outputs/case_reports", "outputs/bid_packs", "outputs/export_quote_packs", "outputs/dashboards", "receipts/plugin_runs"], "projection"),
            box(1300, 480, 430, 245, "Codex Stop Conditions", ["runtime unavailable", "plugin unavailable/unauthenticated", "unapproved legal/price/origin claim", "credential-heavy plugin needs approval"], "approval"),
            box(70, 845, 510, 170, "Readiness Checks", ["hermes doctor/help/tools/skills/mcp/kanban/cron", "codex --version/help/doctor", "codex plugin list --available --json", "codex app-server --help"], "validate"),
            box(645, 845, 510, 170, "Safety Notes", ["No external send from artifact runtime", "No public service exposure", "No final compliance/legal advice", "Plugin choice and run receipt recorded"], "approval"),
            box(1220, 845, 510, 170, "Current Supporting Scripts", ["scripts/check_codex_runtime_readiness.py", "scripts/generate_artifact_manifest.py", "scripts/record_plugin_run_receipt.py", "scripts/run_agent_regression_checks.py"], "codex"),
            footer(),
        ]
    )
    return shell("Detail 05 - Codex App-Server Runtime and Plugin Factory", "How artifact/file/plugin-heavy work is routed and constrained in the current model.", body)


def diagram_chatgpt_drive() -> str:
    body = "\n".join(
        [
            box(70, 150, 430, 215, "Stable Context Folder", ["Drive: Tender Export OS - Knowledge Bus", "00_Project_Context/01_Instructions", "00_Project_Context/02_State_Snapshots", "00_Project_Context/03_Context_Receipts"], "drive"),
            box(685, 150, 430, 215, "Outbound to ChatGPT", ["08_ChatGPT_Bridge/01_To_ChatGPT", "chatgpt_snapshot.md", "CHATGPT_BOARDROOM.md", "project_instructions.md", "packet_manifest.json"], "chatgpt"),
            box(1300, 150, 430, 215, "Inbound from ChatGPT", ["08_ChatGPT_Bridge/02_From_ChatGPT", "Research or strategy returns", "stage before use", "no direct register mutation"], "chatgpt"),
            arrow(500, 258, 685, 258, "#8e82ff"),
            arrow(1115, 258, 1300, 258, "#8e82ff"),
            box(70, 500, 430, 215, "Packet Preparation", ["scripts/prepare_chatgpt_drive_packet.py", "bounded case summary", "approval and quote-proof gaps", "source/plugin health"], "validate"),
            box(685, 500, 430, 215, "Drive Sync / Import", ["scripts/sync_to_drive.py", "scripts/import_from_drive.py", "dry-run default", "connector/auth required for execute"], "drive"),
            box(1300, 500, 430, 215, "Return Review", ["scripts/stage_chatgpt_return.py", "review plan created", "accepted findings become task/event/artifact/card", "ChatGPT output remains advisory"], "hermes"),
            box(70, 850, 500, 165, "Never Send to Drive/ChatGPT", ["credentials, cookies, DSC files, bank details", "raw operational databases unless explicitly bounded", "unreviewed private supplier claims as final facts"], "approval"),
            box(650, 850, 500, 165, "Drive is a Projection", ["data/events.jsonl remains canonical", "Drive stores packets, artifacts, receipts, snapshots", "ChatGPT must not overwrite registers"], "ledger"),
            box(1230, 835, 500, 190, "Current Sync Policy", ["config/sync_policy.yaml", "dry_run_default: true", "explicit execute flag required", "owner approval required for public share"], "drive"),
            footer(),
        ]
    )
    return shell("Detail 06 - ChatGPT Project and Google Drive Knowledge Bus", "The current bounded boardroom/research handoff and Drive projection contract.", body)


def diagram_sources_intake() -> str:
    body = "\n".join(
        [
            box(70, 150, 430, 225, "Source Configs", ["config/sources.gov.yaml", "config/sources.export.yaml", "config/sources.supplier.yaml", "config/source_strategy.yaml", "config/credential_policy.yaml"], "source"),
            box(685, 150, 430, 225, "Safe Intake Scripts", ["scripts/run_external_task_intake.py", "scripts/run_source_adapter.py", "scripts/capture_browser_evidence.py", "scripts/capture_case_evidence.py"], "validate"),
            box(1300, 150, 430, 225, "Source Outputs", ["data/external_task_inbox.csv", "data/source_health.csv", "outputs/external_intake", "receipts/browser_research"], "projection"),
            arrow(500, 262, 685, 262, "#69b8d0"),
            arrow(1115, 262, 1300, 262, "#69b8d0"),
            box(70, 510, 430, 220, "Radar Intake", ["Find opportunities", "Create GOV/EXP case IDs", "Avoid duplicates by case/source", "Do not deep-read every lead"], "agent"),
            box(685, 510, 430, 220, "Evidence Bundle", ["source URL capture", "metadata and hashes", "case workspace files", "unreadable docs become blockers"], "source"),
            box(1300, 510, 430, 220, "Health Tracking", ["paywall/login/CAPTCHA logged", "source reliability tracked", "failed sources skipped", "owner brief includes blockers"], "projection"),
            box(70, 835, 500, 190, "Portal Rules", ["Public read-only unless authorized", "No CAPTCHA bypass", "Portal login only under authorization", "Secrets never written to repo"], "approval"),
            box(650, 835, 500, 190, "Case Creation Results", ["NEW cases enter Fast Kill", "weak or missing evidence stays incomplete", "source citations required in reports"], "hermes"),
            box(1230, 835, 500, 190, "Current Source State", ["13 total cases", "7 GOV and 6 EXPORT", "9 currently NEW", "2 in supplier search"], "ledger"),
            footer(),
        ]
    )
    return shell("Detail 07 - Sources, External Intake, and Research Capture", "How opportunities and evidence enter the system safely.", body)


def diagram_validation_learning() -> str:
    body = "\n".join(
        [
            box(70, 150, 430, 230, "System Health", ["scripts/system_health_check.py", "required files, JSON/YAML/CSV checks", "status and cross-reference checks", "current safe result: 16/16 PASS"], "validate"),
            box(685, 150, 430, 230, "Schema and Readiness", ["scripts/validate_register_schemas.py", "scripts/validate_case_readiness.py", "schemas under config/schemas", "approval and quote-proof blockers explicit"], "validate"),
            box(1300, 150, 430, 230, "Loop Validators", ["scripts/validate_agent_loops.py", "scripts/validate_loop_schedule.py", "scripts/audit_agent_prompts.py", "agent capability routing checked"], "validate"),
            box(70, 510, 430, 220, "Regression / Scorecards", ["scripts/run_agent_regression_checks.py", "scripts/generate_90_plus_scorecard.py", "scripts/test_source_adapters.py", "outputs/scorecards", "outputs/agent_regression"], "codex"),
            box(685, 510, 430, 220, "Learning Review", ["weekly_learning_review cron", "wins, losses, source quality", "supplier quality, pricing errors", "owner corrections"], "hermes"),
            box(1300, 510, 430, 220, "Memory and Skill Policy", ["config/memory_policy.yaml", "memory writes require approval", "skill updates staged first", "pricing/compliance skills need owner approval"], "approval"),
            arrow(500, 620, 685, 620, "#31d0a3"),
            arrow(1115, 620, 1300, 620, "#f16e7f"),
            box(70, 835, 500, 190, "What Gets Learned", ["durable founder preferences", "repeated corrections", "source quirks and parser fixes", "compact supplier lessons"], "ledger"),
            box(650, 835, 500, 190, "What Does Not Get Learned", ["raw tenders/RFQs", "long supplier tables", "credentials, DSC, bank details", "unverified claims as facts"], "approval"),
            box(1230, 835, 500, 190, "Closure Loop", ["proposal -> owner review -> accepted change", "then event/log/skill/config update", "next day runs with better rules"], "hermes"),
            footer(),
        ]
    )
    return shell("Detail 08 - Validation, Health, and Learning Loop", "How the system proves it is safe, catches drift, and improves without silent memory/skill writes.", body)


DIAGRAMS = {
    "01_control_plane_owner_scheduler_kanban.svg": diagram_control_plane,
    "02_operating_agent_pipeline.svg": diagram_agent_pipeline,
    "03_canonical_state_registers_projections.svg": diagram_state_registers,
    "04_approval_safety_execution.svg": diagram_approval_safety,
    "05_codex_runtime_plugin_factory.svg": diagram_codex_runtime,
    "06_chatgpt_drive_knowledge_bus.svg": diagram_chatgpt_drive,
    "07_sources_intake_research_capture.svg": diagram_sources_intake,
    "08_validation_health_learning_loop.svg": diagram_validation_learning,
}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, build in DIAGRAMS.items():
        path = OUT_DIR / filename
        path.write_text(build(), encoding="utf-8")
        print(path.relative_to(PROJECT_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
