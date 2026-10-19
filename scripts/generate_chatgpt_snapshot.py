#!/usr/bin/env python3
"""Generate a bounded ChatGPT boardroom snapshot from local registers."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT = DATA_DIR / "chatgpt_snapshot.md"


ACTIVE_STATUSES = {
    "NEW",
    "FAST_KILL",
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
}


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def score(case: dict) -> float:
    value = case.get("score_gov") or case.get("score_export") or 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def case_line(case: dict) -> str:
    return (
        f"- `{case.get('case_id', '')}` | {case.get('workflow_type', '')} | "
        f"{case.get('status', '')} | score {score(case):.0f} | "
        f"{case.get('opportunity_title', '')} | buyer: {case.get('buyer_name', '')} | "
        f"deadline: {case.get('deadline_date', '')} | next note: {case.get('notes', '')}"
    )


def section(title: str, lines: list[str]) -> str:
    body = "\n".join(lines) if lines else "- None found in current local registers."
    return f"## {title}\n{body}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ChatGPT snapshot")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output markdown path")
    parser.add_argument("--limit", type=int, default=10, help="Max cases per section")
    args = parser.parse_args()

    cases = load_csv(DATA_DIR / "master_cases.csv")
    approvals = load_csv(DATA_DIR / "approvals_receipts.csv")
    suppliers = load_csv(DATA_DIR / "supplier_master.csv")
    sources = load_csv(DATA_DIR / "source_health.csv")
    plugins = load_csv(DATA_DIR / "plugin_health.csv")
    quotes = load_csv(DATA_DIR / "quote_master.csv")

    active = [c for c in cases if c.get("status") in ACTIVE_STATUSES]
    gov = [c for c in active if c.get("workflow_type") == "GOV"]
    export = [c for c in active if c.get("workflow_type") == "EXPORT"]
    top = sorted(active, key=score, reverse=True)[: args.limit]
    pending_approvals = [
        a for a in approvals
        if (a.get("approval_status") or a.get("status") or "").upper() == "PENDING"
    ]
    source_issues = [
        s for s in sources
        if s.get("health_status") not in {"Working", "Low Relevance", ""}
    ]
    plugin_issues = [
        p for p in plugins
        if p.get("health_status") not in {"Working", ""}
    ]
    supplier_issues = [
        s for s in suppliers
        if (s.get("blacklisted", "").upper() == "TRUE" or s.get("watchlisted", "").upper() == "TRUE")
    ]
    quote_gaps = []
    quote_counts = {}
    for quote in quotes:
        quote_counts[quote.get("case_id", "")] = quote_counts.get(quote.get("case_id", ""), 0) + 1
    for case in active:
        if case.get("status") in {"SUPPLIER_SEARCH", "PRICING_READY"} and quote_counts.get(case.get("case_id", ""), 0) < 2:
            quote_gaps.append(f"- `{case.get('case_id')}` has {quote_counts.get(case.get('case_id', ''), 0)} quote proof(s); final pricing requires 2.")

    risks = []
    risks.extend(quote_gaps[: args.limit])
    risks.extend(
        f"- Source `{s.get('source_name')}` is `{s.get('health_status')}`: {s.get('notes', '')}"
        for s in source_issues[: args.limit]
    )
    risks.extend(
        f"- Plugin/tool `{p.get('plugin_or_tool')}` is `{p.get('health_status')}`: {p.get('blocker', '')}"
        for p in plugin_issues[: args.limit]
    )

    if pending_approvals:
        recommended = f"Review pending approval for `{pending_approvals[0].get('case_id', 'unknown')}`."
    elif quote_gaps:
        recommended = "Resolve quote proof gaps before pricing or pack production."
    elif top:
        recommended = f"Review next action for top case `{top[0].get('case_id')}`."
    else:
        recommended = "Run radar scan and refresh source health."

    generated_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    content = [
        "# Tender Export OS - ChatGPT Boardroom Snapshot",
        "",
        f"Generated at: {generated_at}",
        "",
        "Boundary: This is a bounded strategy snapshot. It is not the raw operational database and is not final legal/compliance advice.",
        "",
        section("Active GOV Cases", [case_line(c) for c in gov[: args.limit]]),
        section("Active EXPORT Cases", [case_line(c) for c in export[: args.limit]]),
        section("Top Opportunities", [case_line(c) for c in top]),
        section("Pending Approvals", [
            f"- `{a.get('case_id', '')}` | {a.get('proposed_action', a.get('action', ''))} | status: {a.get('approval_status', a.get('status', ''))}"
            for a in pending_approvals[: args.limit]
        ]),
        section("Supplier Issues", [
            f"- `{s.get('supplier_id')}` | {s.get('supplier_name')} | blacklisted={s.get('blacklisted')} | watchlisted={s.get('watchlisted')} | {s.get('watchlist_reason') or s.get('blacklist_reason') or s.get('notes', '')}"
            for s in supplier_issues[: args.limit]
        ]),
        section("Source Health", [
            f"- {s.get('source_name')} | {s.get('health_status')} | {s.get('notes', '')}"
            for s in source_issues[: args.limit]
        ]),
        section("Plugin Health", [
            f"- {p.get('plugin_or_tool')} | {p.get('health_status')} | {p.get('notes', '')}"
            for p in plugin_issues[: args.limit]
        ]),
        section("Main Risks", risks[: args.limit]),
        "## Recommended Owner Action",
        f"- {recommended}",
        "",
        "## Sources Used",
        "- `data/master_cases.csv`",
        "- `data/approvals_receipts.csv`",
        "- `data/supplier_master.csv`",
        "- `data/source_health.csv`",
        "- `data/plugin_health.csv`",
        "- `data/quote_master.csv`",
    ]

    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(content) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
