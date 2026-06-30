#!/usr/bin/env python3
"""Create a category-country buyer research horizon from public-source strategy files."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "buyer_research"
FIELDS = [
    "research_id", "category_code", "category_name", "country", "buyer_type",
    "source_tier", "source_name", "source_url", "market_fit_score",
    "source_reliability_score", "evidence_density_score", "recommended_next_action",
    "approval_required", "notes", "created_at", "updated_at",
]


def today() -> str:
    return dt.date.today().isoformat()


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def try_load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except Exception:
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fallback_categories(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    block_match = re.search(r"export_categories:\n(?P<body>.*?)(?:\n[a-zA-Z_]+:|\Z)", text, re.S)
    if not block_match:
        return []
    categories = []
    current: dict[str, str] | None = None
    for raw_line in block_match.group("body").splitlines():
        line = raw_line.strip()
        if line.startswith("- name:"):
            if current:
                categories.append(current)
            current = {"name": line.split(":", 1)[1].strip().strip('"'), "markets": []}
        elif current and line.startswith("code:"):
            current["code"] = line.split(":", 1)[1].strip().strip('"')
        elif current and line.startswith("priority:"):
            current["priority"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("active:"):
            current["active"] = line.split(":", 1)[1].strip().lower()
        elif current and line.startswith("destination_markets:"):
            market_values = []
            for quoted, bare in re.findall(r'"([^"]+)"|([^,\[\]]+)', line.split(":", 1)[1]):
                value = (quoted or bare).strip().strip('"')
                if value:
                    market_values.append(value)
            current["markets"] = market_values
    if current:
        categories.append(current)
    return categories


def load_categories() -> list[dict]:
    path = CONFIG_DIR / "categories.yaml"
    data = try_load_yaml(path)
    if data and isinstance(data.get("export_categories"), list):
        out = []
        for item in data["export_categories"]:
            if item.get("active") is False:
                continue
            out.append({
                "name": item.get("name", ""),
                "code": item.get("code", ""),
                "priority": item.get("priority", "medium"),
                "markets": item.get("destination_markets") or [],
            })
        return out
    return [cat for cat in fallback_categories(path) if cat.get("active", "true") != "false"]


def fallback_sources(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    sources = []
    current: dict[str, str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("- name:"):
            if current:
                sources.append(current)
            current = {"name": line.split(":", 1)[1].strip().strip('"')}
        elif current and line.startswith("url:"):
            current["url"] = line.split(":", 1)[1].strip().strip('"')
        elif current and line.startswith("login_required:"):
            current["login_required"] = line.split(":", 1)[1].strip().lower()
    if current:
        sources.append(current)
    return sources


def load_sources() -> list[dict]:
    path = CONFIG_DIR / "sources.export.yaml"
    data = try_load_yaml(path)
    if data:
        found = []
        for value in data.values() if isinstance(data, dict) else []:
            if isinstance(value, list):
                found.extend(item for item in value if isinstance(item, dict))
        if found:
            return found
    return fallback_sources(path)


def tier_for_source(source: dict) -> tuple[str, str, int, int]:
    name = (source.get("name") or source.get("source_name") or "").lower()
    if any(token in name for token in ["undp", "world bank", "adb", "ungm", "government", "embassy"]):
        return ("TIER_1_INSTITUTIONAL", "Institutional procurement desk", 88, 70)
    if any(token in name for token in ["apeda", "spices", "fieo", "epc", "council", "board"]):
        return ("TIER_2_SECTOR", "Sector board or export promotion desk", 72, 55)
    if any(token in name for token in ["directory", "association", "importer", "distributor"]):
        return ("TIER_3_IMPORTER_DISTRIBUTOR", "Importer/distributor research", 58, 42)
    if any(token in name for token in ["alibaba", "tradekey", "indiamart", "global sources", "ec21"]):
        return ("TIER_4_MARKETPLACE_RFQ", "Marketplace lead triage", 38, 30)
    return ("TIER_5_STRATEGIC_ACCOUNT", "Named account research", 52, 35)


def market_score(priority: str, tier: str) -> int:
    base = {"high": 75, "medium": 62, "low": 48}.get((priority or "").lower(), 55)
    if tier == "TIER_1_INSTITUTIONAL":
        return min(95, base + 10)
    if tier == "TIER_4_MARKETPLACE_RFQ":
        return max(25, base - 12)
    return base


def make_rows(categories: list[dict], sources: list[dict]) -> list[dict]:
    rows = []
    used_keys = set()
    for category in categories:
        markets = category.get("markets") or ["Global"]
        for country in markets[:5]:
            for source in sources:
                tier, buyer_type, source_score, density = tier_for_source(source)
                key = (category.get("code"), country, tier)
                if key in used_keys:
                    continue
                used_keys.add(key)
                login_required = str(source.get("login_required", "")).lower() == "true"
                if tier == "TIER_1_INSTITUTIONAL":
                    action = "Scan public notices for buyer-specific RFQs with reference, product, country, deadline, and portal/contact path."
                elif tier == "TIER_2_SECTOR":
                    action = "Use sector board evidence to identify country demand lanes; do not count as RFQ until buyer proof exists."
                elif tier == "TIER_3_IMPORTER_DISTRIBUTOR":
                    action = "Map public importer/distributor candidates and verify legal identity before outreach approval."
                elif tier == "TIER_4_MARKETPLACE_RFQ":
                    action = "Treat as weak lead; require unmasked buyer identity and RFQ proof before promotion."
                else:
                    action = "Create named target-account research packet for owner-approved outreach drafting."
                research_id = "DEM-" + "-".join([
                    str(category.get("code", "CAT")).upper(),
                    re.sub(r"[^A-Z0-9]+", "", country.upper())[:12] or "GLOBAL",
                    tier.split("_")[1],
                ])
                rows.append({
                    "research_id": research_id,
                    "category_code": category.get("code", ""),
                    "category_name": category.get("name", ""),
                    "country": country,
                    "buyer_type": buyer_type,
                    "source_tier": tier,
                    "source_name": source.get("name") or source.get("source_name") or "",
                    "source_url": source.get("url") or source.get("source_url") or "",
                    "market_fit_score": market_score(category.get("priority", "medium"), tier),
                    "source_reliability_score": source_score,
                    "evidence_density_score": density,
                    "recommended_next_action": action,
                    "approval_required": "TRUE" if tier == "TIER_5_STRATEGIC_ACCOUNT" else "FALSE",
                    "notes": "Public-source/portal-lane V1; owner standing authorization covers research login/signup, but operational demand still requires RFQ verification and all buyer/bid/payment/final commitments remain gated.",
                    "created_at": today(),
                    "updated_at": today(),
                })
    return sorted(rows, key=lambda row: (-int(row["market_fit_score"]), row["category_code"], row["country"], row["source_tier"]))


def write_report(rows: list[dict]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"buyer_horizon_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    lines = [
        "# Buyer Demand Research Horizon",
        "",
        "Public-source-only research map. These rows are research lanes, not verified RFQ demand.",
        "",
        "| Category | Country | Tier | Source | Market | Source | Next action |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in rows[:40]:
        lines.append(
            f"| {row['category_name']} | {row['country']} | {row['source_tier']} | {row['source_name']} | "
            f"{row['market_fit_score']} | {row['source_reliability_score']} | {row['recommended_next_action']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def append_run_log(row_count: int, dry_run: bool) -> None:
    path = DATA_DIR / "agent_run_log.csv"
    file_exists = path.exists()
    row = {
        "run_id": f"RUN-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-BUYER-HORIZON",
        "run_date": today(),
        "run_time": dt.datetime.now().strftime("%H:%M:%S"),
        "agent_name": "buyer_research_agent",
        "trigger_type": "manual",
        "cases_processed": 0,
        "cases_created": 0,
        "cases_rejected": 0,
        "cases_updated": 0,
        "sources_checked": row_count,
        "sources_failed": 0,
        "actions_taken": "research_buyer_horizon_dry_run" if dry_run else "research_buyer_horizon",
        "approval_cards_created": 0,
        "receipts_created": 1 if not dry_run else 0,
        "errors": 0,
        "warnings": 0,
        "runtime_seconds": 0,
        "status": "SUCCESS",
        "notes": "Generated public-source buyer research horizon; no external actions.",
    }
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate buyer research horizon")
    parser.add_argument("--dry-run", action="store_true", help="Do not write registers/events")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = parser.parse_args()

    rows = make_rows(load_categories(), load_sources())
    if not args.dry_run:
        write_csv(DATA_DIR / "demand_research.csv", rows)
        report = write_report(rows)
        for row in rows:
            append_event(
                "demand_research.created",
                "research_buyer_horizon",
                object_type="demand_research",
                object_id=row["research_id"],
                payload={"updates": row},
                citations=[str(report.relative_to(PROJECT_ROOT)), row.get("source_url", "")],
            )
        append_run_log(len(rows), args.dry_run)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(f"Generated {len(rows)} buyer research lanes.")
        if not args.dry_run:
            print(f"Report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
