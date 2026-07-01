#!/usr/bin/env python3
"""Run a safe Tender Export OS v4.1 health check."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "system_health"

VALID_STATUSES = {
    "NEW",
    "FAST_KILL",
    "REJECTED",
    "WATCHLIST",
    "DEEP_READ",
    "SUPPLIER_SEARCH",
    "PRICING_READY",
    "ARTIFACT_PRODUCTION",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "CHANGES_REQUESTED",
    "SENT_OR_SUBMITTED",
    "FOLLOW_UP",
    "WON",
    "LOST",
    "ARCHIVED",
}

REQUIRED_FILES = [
    "SOUL.md",
    "HERMES.md",
    "AGENTS.md",
    "README.md",
    "docs/FINAL_ARCHITECTURE.md",
    "docs/HERMES_NATIVE_CONTROL_PLANE.md",
    "docs/CODEX_APP_SERVER_RUNTIME.md",
    "docs/HERMES_KANBAN_BOARD.md",
    "docs/CODEX_PLUGIN_RUNTIME_POLICY.md",
    "docs/GOOGLE_DRIVE_KNOWLEDGE_BUS.md",
    "docs/CHATGPT_BOARDROOM.md",
    "docs/PAPERCLIP_DECISION.md",
    "docs/APPROVAL_BOUNDARIES.md",
    "docs/WEB_BROWSER_RESEARCH_ROUTING.md",
    "docs/ARCHITECTURE_CRITIQUE_AND_V4_1_PROPOSAL.md",
    "docs/CHATGPT_CODEX_HERMES_DRIVE_COMMUNICATION.md",
    "docs/FOUNDER_QUICK_COMMANDS.md",
    "docs/MAX_CAPABILITY_UPGRADE_ROADMAP.md",
    "docs/AGENT_EXCELLENCE_SYSTEM.md",
    "docs/ROLE_CAPABILITY_STANDARDS.md",
    "docs/MOBILE_DELIVERY_SETUP.md",
    "docs/MOBILE_APPROVAL_PROTOCOL.md",
    "docs/GOOGLE_DRIVE_SYNC_RUNBOOK.md",
    "docs/REGRESSION_CHECKLIST_90_PLUS.md",
    "config/hermes_cron.yaml",
    "config/codex_runtime_policy.yaml",
    "config/kanban_board.yaml",
    "config/memory_policy.yaml",
    "config/plugin_routing.yaml",
    "config/agent_capability_routing.yaml",
    "config/sync_policy.yaml",
    "config/source_strategy.yaml",
    "config/schemas/master_cases.schema.json",
    "config/schemas/approvals_receipts.schema.json",
    "config/schemas/quote_master.schema.json",
    "config/schemas/supplier_master.schema.json",
    "config/schemas/event.schema.json",
    "config/schemas/approval_card.schema.json",
    "config/schemas/drive_manifest.schema.json",
    "config/schemas/plugin_run_receipt.schema.json",
    "data/events.jsonl",
    "data/master_cases.csv",
    "data/approvals_receipts.csv",
    "data/drive_manifest.csv",
    "data/source_health.csv",
    "data/plugin_health.csv",
    "data/supplier_master.csv",
    "data/quote_master.csv",
    "templates/daily_brief.html",
    "templates/approval_card.html",
    "scripts/initialize_event_ledger.py",
    "scripts/rebuild_projections_from_events.py",
    "scripts/validate_register_schemas.py",
    "scripts/process_owner_decision.py",
    "scripts/validate_case_readiness.py",
    "scripts/generate_artifact_manifest.py",
    "scripts/create_case_workspace.py",
    "scripts/capture_case_evidence.py",
    "scripts/create_case_task_graph.py",
    "scripts/reconcile_hermes_kanban.py",
    "scripts/run_source_adapter.py",
    "scripts/prepare_chatgpt_drive_packet.py",
    "scripts/stage_chatgpt_return.py",
    "scripts/setup_drive_knowledge_bus.py",
    "scripts/render_mobile_approval_payload.py",
    "scripts/render_mobile_dashboard_summary.py",
    "scripts/sync_drive_manifest.py",
    "scripts/test_source_adapters.py",
    "scripts/generate_source_health_report.py",
    "scripts/record_plugin_run_receipt.py",
    "scripts/capture_browser_evidence.py",
    "scripts/generate_founder_dashboard.py",
    "scripts/audit_agent_prompts.py",
    "scripts/run_agent_regression_checks.py",
    "scripts/generate_90_plus_scorecard.py",
    "scripts/source_adapters/base.py",
    "scripts/source_adapters/mock_adapter.py",
    "tests/fixtures/sources/mock_opportunities.json",
    "tests/fixtures/chatgpt_returns/sample_return.md",
]

PUBLIC_TEMPLATE_REQUIRED_FILES = [
    "SOUL.md",
    "HERMES.md",
    "AGENTS.md",
    "README.md",
    "docs/FINAL_ARCHITECTURE.md",
    "docs/HERMES_NATIVE_CONTROL_PLANE.md",
    "docs/CODEX_APP_SERVER_RUNTIME.md",
    "docs/HERMES_KANBAN_BOARD.md",
    "docs/CODEX_PLUGIN_RUNTIME_POLICY.md",
    "docs/GOOGLE_DRIVE_KNOWLEDGE_BUS.md",
    "docs/CHATGPT_BOARDROOM.md",
    "docs/PAPERCLIP_DECISION.md",
    "docs/APPROVAL_BOUNDARIES.md",
    "docs/V4_1_2_PHASEWISE_IMPLEMENTATION_PLAN.md",
    "config/hermes_cron.yaml",
    "config/codex_runtime_policy.yaml",
    "config/kanban_board.yaml",
    "config/memory_policy.yaml",
    "config/plugin_routing.yaml",
    "config/agent_capability_routing.yaml",
    "config/sync_policy.yaml",
    "config/source_strategy.yaml",
    "config/public_scan_allowlist.yaml",
    "config/schemas/master_cases.schema.json",
    "config/schemas/approvals_receipts.schema.json",
    "config/schemas/quote_master.schema.json",
    "config/schemas/supplier_master.schema.json",
    "config/schemas/event.schema.json",
    "config/schemas/approval_card.schema.json",
    "config/schemas/drive_manifest.schema.json",
    "config/schemas/plugin_run_receipt.schema.json",
    "data/examples/master_cases.example.csv",
    "data/examples/approvals_receipts.example.csv",
    "data/examples/supplier_master.example.csv",
    "data/examples/buyer_master.example.csv",
    "data/examples/quote_master.example.csv",
    "data/examples/rfq_master.example.csv",
    "data/examples/demand_research.example.csv",
    "data/examples/drive_manifest.example.csv",
    "data/examples/source_health.example.csv",
    "data/examples/plugin_health.example.csv",
    "data/examples/events.example.jsonl",
    "outputs/examples/sample_deep_source_report.html",
    "receipts/examples/sample_approval_card.html",
    "templates/daily_brief.html",
    "templates/approval_card.html",
    "scripts/validate_register_schemas.py",
    "scripts/check_no_private_runtime_data.py",
    "scripts/system_health_check.py",
    "tests/fixtures/sources/mock_opportunities.json",
    "tests/fixtures/chatgpt_returns/sample_return.md",
]

PRIVATE_RUNTIME_REQUIRED_FILES = [
    "data/events.jsonl",
    "data/master_cases.csv",
    "data/approvals_receipts.csv",
    "data/drive_manifest.csv",
    "data/source_health.csv",
    "data/plugin_health.csv",
    "data/supplier_master.csv",
    "data/quote_master.csv",
    "data/buyer_master.csv",
    "data/rfq_master.csv",
    "data/demand_research.csv",
]


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


class Health:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.passes: list[str] = []

    def pass_(self, message: str) -> None:
        self.passes.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def fail(self, message: str) -> None:
        self.failures.append(message)


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run(command: list[str], timeout: int = 30) -> tuple[int, str, str]:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def check_required_files(health: Health, required_files: list[str] | None = None, label: str = "v4.1") -> None:
    files = required_files or REQUIRED_FILES
    missing = [path for path in files if not (PROJECT_ROOT / path).exists()]
    if missing:
        health.fail(f"Missing required files: {', '.join(missing)}")
    else:
        health.pass_(f"All required {label} files exist")


def check_json(health: Health) -> None:
    for path in ["manifest.json", "config/agent_loops.json", "config/loop_schedule.json"]:
        try:
            json.loads((PROJECT_ROOT / path).read_text(encoding="utf-8"))
        except Exception as exc:
            health.fail(f"{path} is not valid JSON: {exc}")
            return
    health.pass_("JSON files parse")


def check_yaml(health: Health) -> None:
    yaml_files = sorted((PROJECT_ROOT / "config").glob("*.yaml"))
    try:
        import yaml  # type: ignore

        for path in yaml_files:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        health.pass_(f"YAML files parse with PyYAML: {len(yaml_files)}")
        return
    except ModuleNotFoundError:
        ruby = shutil.which("ruby")
        if not ruby:
            health.warn("PyYAML and Ruby are unavailable; YAML parse check skipped")
            return
        code = 'require "yaml"; Dir["config/*.yaml"].sort.each { |p| YAML.load_file(p) }; puts "ok"'
        rc, stdout, stderr = run([ruby, "-e", code])
        if rc == 0:
            health.pass_(f"YAML files parse with Ruby: {len(yaml_files)}")
        else:
            health.fail(f"YAML parse failed: {stderr or stdout}")
    except Exception as exc:
        health.fail(f"YAML parse failed: {exc}")


def check_csv_contracts(health: Health) -> None:
    csv_paths = [
        PROJECT_ROOT / "data" / "master_cases.csv",
        PROJECT_ROOT / "data" / "approvals_receipts.csv",
        PROJECT_ROOT / "data" / "supplier_master.csv",
        PROJECT_ROOT / "data" / "quote_master.csv",
        PROJECT_ROOT / "data" / "source_health.csv",
        PROJECT_ROOT / "data" / "plugin_health.csv",
    ]
    malformed = []
    for path in csv_paths:
        for index, row in enumerate(load_csv(path), start=2):
            if None in row:
                malformed.append(f"{rel(path)}:{index} has extra cells {row[None]}")
    if malformed:
        health.fail("Malformed CSV rows: " + " | ".join(malformed))
    else:
        health.pass_("CSV rows match their headers")

    cases = load_csv(PROJECT_ROOT / "data" / "master_cases.csv")
    approvals = load_csv(PROJECT_ROOT / "data" / "approvals_receipts.csv")
    suppliers = load_csv(PROJECT_ROOT / "data" / "supplier_master.csv")
    quotes = load_csv(PROJECT_ROOT / "data" / "quote_master.csv")

    case_ids = {row.get("case_id") for row in cases}
    supplier_ids = {row.get("supplier_id") for row in suppliers}

    unknown_statuses = sorted({row.get("status", "") for row in cases} - VALID_STATUSES - {""})
    if unknown_statuses:
        health.fail(f"Unknown case statuses in master_cases.csv: {unknown_statuses}")
    else:
        health.pass_("All master case statuses are valid v4.1 statuses")

    missing_approval_cases = sorted({row.get("case_id") for row in approvals if row.get("case_id") not in case_ids})
    if missing_approval_cases:
        health.fail(f"Approval rows reference unknown case IDs: {missing_approval_cases}")
    else:
        health.pass_("Approval rows reference known cases")

    missing_quote_cases = sorted({row.get("case_id") for row in quotes if row.get("case_id") not in case_ids})
    if missing_quote_cases:
        health.fail(f"Quote rows reference unknown case IDs: {missing_quote_cases}")
    else:
        health.pass_("Quote rows reference known cases")

    missing_quote_suppliers = sorted({row.get("supplier_id") for row in quotes if row.get("supplier_id") not in supplier_ids})
    if missing_quote_suppliers:
        health.fail(f"Quote rows reference unknown supplier IDs: {missing_quote_suppliers}")
    else:
        health.pass_("Quote rows reference known suppliers")

    missing_cards = []
    pending_with_decision_fields = []
    for approval in approvals:
        if (approval.get("approval_status") or "").upper() == "PENDING":
            path = approval.get("approval_card_path") or f"receipts/approvals/{approval.get('case_id')}_approval_card.html"
            if not (PROJECT_ROOT / path).exists():
                missing_cards.append(path)
            if approval.get("approved_by") or approval.get("approved_at"):
                pending_with_decision_fields.append(approval.get("approval_id") or approval.get("case_id"))
    if missing_cards:
        health.fail(f"Pending approvals missing card files: {missing_cards}")
    else:
        health.pass_("Pending approval cards exist")

    if pending_with_decision_fields:
        health.fail(f"Pending approvals have approved_by/approved_at populated: {pending_with_decision_fields}")
    else:
        health.pass_("Pending approvals do not contain approval decision fields")


def check_v41_schemas(health: Health) -> None:
    rc, stdout, stderr = run(["python3", "scripts/validate_register_schemas.py"])
    if rc != 0:
        health.fail(f"v4.1 schema validation failed: {stderr or stdout}")
    else:
        health.pass_("v4.1 register schemas and event ledger validate")


def check_public_examples(health: Health) -> None:
    examples = [
        PROJECT_ROOT / "data" / "examples" / "master_cases.example.csv",
        PROJECT_ROOT / "data" / "examples" / "supplier_master.example.csv",
        PROJECT_ROOT / "data" / "examples" / "buyer_master.example.csv",
        PROJECT_ROOT / "data" / "examples" / "quote_master.example.csv",
        PROJECT_ROOT / "data" / "examples" / "source_health.example.csv",
        PROJECT_ROOT / "data" / "examples" / "plugin_health.example.csv",
    ]
    malformed = []
    for path in examples:
        rows = load_csv(path)
        for index, row in enumerate(rows, start=2):
            if None in row:
                malformed.append(f"{rel(path)}:{index} has extra cells {row[None]}")
    if malformed:
        health.fail("Malformed example CSV rows: " + " | ".join(malformed))
    else:
        health.pass_("Public example CSV rows match their headers")


def check_private_data_scan(health: Health) -> None:
    rc, stdout, stderr = run(["python3", "scripts/check_no_private_runtime_data.py", "--public-template"])
    if rc != 0:
        health.fail(f"Private runtime public-template scan failed: {stderr or stdout}")
    else:
        health.pass_("Private runtime public-template scan passes")


def check_templates(health: Health) -> None:
    daily = (PROJECT_ROOT / "templates" / "daily_brief.html").read_text(encoding="utf-8")
    legacy_sample_title = "Tender + Export OS v" + "3.1"
    forbidden = [
        legacy_sample_title,
        "Brass Handicraft Items — UK Buyer",
        "Artisan Bazaar Ltd",
        "Review and approve EXP-20260630-002 quote",
    ]
    scan_files = list((PROJECT_ROOT / "templates").glob("*")) + list((PROJECT_ROOT / "agents").glob("*.md"))
    hits = []
    for path in scan_files:
        if not path.is_file():
            continue
        if path.suffix.lower() not in {"", ".html", ".md", ".txt", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        hits.extend(f"{rel(path)}: {item}" for item in forbidden if item in text)
    if hits:
        health.fail(f"Templates contain stale/static sample text: {hits}")
    else:
        health.pass_("Templates and agent prompts do not contain known stale sample data")

    required_placeholders = ["{{BEST_OPPORTUNITIES}}", "{{APPROVAL_REQUIRED}}", "{{RISKS_BLOCKERS}}"]
    missing = [placeholder for placeholder in required_placeholders if placeholder not in daily]
    if missing:
        health.fail(f"Daily brief template missing placeholders: {missing}")
    else:
        health.pass_("Daily brief template has dynamic v4 placeholders")


def check_script_dry_runs(health: Health) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    commands = [
        ["python3", "scripts/case_id_generator.py", "--type", "GOV", "--date", "20260630"],
        ["python3", "scripts/supplier_score.py", "--top", "1"],
        ["python3", "scripts/validate_register_schemas.py"],
        ["python3", "scripts/rebuild_projections_from_events.py", "--output-dir", str(OUTPUT_DIR / "projections")],
        ["python3", "scripts/process_owner_decision.py", "--approval-id", "APR-001", "--decision", "ask-changes", "--owner", "health_check", "--changes", "dry run only", "--dry-run"],
        ["python3", "scripts/validate_case_readiness.py", "--all"],
        ["python3", "scripts/generate_artifact_manifest.py", "--all"],
        ["python3", "scripts/run_source_adapter.py", "--adapter", "mock", "--output", str(OUTPUT_DIR / "mock_source_opportunities.json")],
        ["python3", "scripts/reconcile_hermes_kanban.py", "--output", str(OUTPUT_DIR / "hermes_kanban_reconciliation_plan.json")],
        ["python3", "scripts/prepare_chatgpt_drive_packet.py", "--topic", "system_health", "--outbox", str(OUTPUT_DIR / "chatgpt_to_chatgpt")],
        ["python3", "scripts/stage_chatgpt_return.py", "--input", "tests/fixtures/chatgpt_returns/sample_return.md", "--inbox", str(OUTPUT_DIR / "chatgpt_from_chatgpt")],
        ["python3", "scripts/setup_drive_knowledge_bus.py", "--output", str(OUTPUT_DIR / "drive_knowledge_bus_setup_plan.json")],
        ["python3", "scripts/generate_chatgpt_snapshot.py", "--output", str(OUTPUT_DIR / "chatgpt_snapshot.md")],
        ["python3", "scripts/sync_to_drive.py", "--mode", "public-template", "--output", str(OUTPUT_DIR / "drive_sync_manifest.json")],
        ["python3", "scripts/import_from_drive.py", "--output", str(OUTPUT_DIR / "drive_import_plan.json")],
        ["python3", "scripts/generate_daily_brief.py", "--date", "20260630", "--no-log"],
        ["python3", "scripts/codex_task_runner.py"],
        ["python3", "scripts/render_mobile_approval_payload.py", "--all-pending", "--dry-run"],
        ["python3", "scripts/render_mobile_dashboard_summary.py", "--dry-run"],
        ["python3", "scripts/sync_drive_manifest.py", "--dry-run", "--case-id", "GOV-20260630-001"],
        ["python3", "scripts/test_source_adapters.py", "--safe", "--limit", "5"],
        ["python3", "scripts/generate_source_health_report.py"],
        ["python3", "scripts/record_plugin_run_receipt.py", "--case-id", "GOV-20260630-001", "--capability-name", "health-check", "--dry-run"],
        ["python3", "scripts/capture_browser_evidence.py", "--url", "https://example.com", "--case-id", "GOV-20260630-001", "--dry-run"],
        ["python3", "scripts/generate_founder_dashboard.py"],
        ["python3", "scripts/audit_agent_prompts.py"],
        ["python3", "scripts/run_agent_regression_checks.py", "--structural-only"],
        ["python3", "scripts/generate_90_plus_scorecard.py"],
    ]
    failures = []
    for command in commands:
        rc, stdout, stderr = run(command)
        if rc != 0:
            failures.append(f"{' '.join(command)} -> {rc}: {stderr or stdout}")
    if failures:
        health.fail("Dry-run command failures: " + " | ".join(failures))
    else:
        health.pass_("Safe dry-run commands pass")

    generated_outputs = [
        PROJECT_ROOT / "outputs" / "daily_briefs" / "brief_20260630.html",
        PROJECT_ROOT / "receipts" / "approvals" / "EXP-20260630-002_approval_card.html",
        PROJECT_ROOT / "receipts" / "approvals" / "GOV-20260630-001_approval_card.html",
        PROJECT_ROOT / "outputs" / "system_health" / "mock_source_opportunities.json",
        PROJECT_ROOT / "outputs" / "system_health" / "hermes_kanban_reconciliation_plan.json",
        PROJECT_ROOT / "outputs" / "dashboards" / "founder_dashboard.html",
        PROJECT_ROOT / "outputs" / "scorecards" / "90_plus_scorecard.html",
        PROJECT_ROOT / "outputs" / "source_health" / "source_health_report.html",
    ]
    unreplaced = []
    for path in generated_outputs:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if "{{" in text or "}}" in text:
                unreplaced.append(rel(path))
    if unreplaced:
        health.fail(f"Generated outputs contain unreplaced placeholders: {unreplaced}")
    else:
        health.pass_("Generated brief and approval cards have no unreplaced placeholders")


def check_existing_validators(health: Health) -> None:
    for command in [
        ["python3", "-m", "py_compile", *[str(p) for p in sorted((PROJECT_ROOT / "scripts").glob("*.py"))]],
        ["python3", "scripts/validate_agent_loops.py"],
        ["python3", "scripts/validate_loop_schedule.py"],
    ]:
        rc, stdout, stderr = run(command)
        if rc != 0:
            health.fail(f"{' '.join(command[:3])} failed: {stderr or stdout}")
            return
    health.pass_("Python compile and loop validators pass")


def check_runtime(health: Health) -> None:
    rc, stdout, stderr = run(["python3", "scripts/check_codex_runtime_readiness.py"], timeout=60)
    if rc != 0:
        health.fail(f"Runtime readiness failed: {stderr or stdout}")
    else:
        health.pass_("Hermes/Codex runtime readiness passes")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Tender Export OS v4.1 system health check")
    parser.add_argument("--runtime", action="store_true", help="Include slower Hermes/Codex runtime checks")
    parser.add_argument("--public-template", action="store_true", help="Validate public template files without live runtime data")
    parser.add_argument("--private-runtime", action="store_true", help="Validate private runtime live data and ledgers")
    args = parser.parse_args()

    health = Health()
    if args.public_template:
        check_required_files(health, PUBLIC_TEMPLATE_REQUIRED_FILES, "public-template")
        check_json(health)
        check_yaml(health)
        check_public_examples(health)
        check_private_data_scan(health)
        check_templates(health)
        check_existing_validators(health)
    elif args.private_runtime:
        check_required_files(health, PRIVATE_RUNTIME_REQUIRED_FILES, "private-runtime")
        check_csv_contracts(health)
        check_v41_schemas(health)
        check_existing_validators(health)
        if args.runtime:
            check_runtime(health)
    else:
        check_required_files(health)
        check_json(health)
        check_yaml(health)
        check_csv_contracts(health)
        check_v41_schemas(health)
        check_templates(health)
        check_existing_validators(health)
        check_script_dry_runs(health)
        if args.runtime:
            check_runtime(health)

    print("Tender Export OS v4.1 System Health")
    print(f"Passes: {len(health.passes)}")
    for item in health.passes:
        print(f"PASS: {item}")
    for item in health.warnings:
        print(f"WARN: {item}")
    for item in health.failures:
        print(f"FAIL: {item}")

    return 1 if health.failures else 0


if __name__ == "__main__":
    sys.exit(main())
