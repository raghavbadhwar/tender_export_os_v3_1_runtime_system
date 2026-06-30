#!/usr/bin/env python3
"""Generate source-weight recommendations without mutating source configs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_HEALTH = PROJECT_ROOT / "data" / "source_health.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "source_strategy"


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(str(value or "").replace(",", ""))
    except ValueError:
        return default


def recommendation_for(row: dict[str, str]) -> dict[str, object]:
    health = (row.get("health_status") or "").lower()
    relevance = to_float(row.get("relevance_score"), 50)
    leads = to_float(row.get("avg_leads_per_week"), 0)
    failures = to_float(row.get("consecutive_failures"), 0)
    login_required = (row.get("login_required") or "").upper() == "TRUE"
    paywalled = (row.get("paywalled") or "").upper() == "TRUE"
    score = relevance + min(20, leads * 3) - failures * 10
    reasons: list[str] = []
    if "working" in health:
        reasons.append("source currently marked working")
    if login_required:
        score -= 15
        reasons.append("login required; cap autonomous evidence level")
    if paywalled:
        score -= 25
        reasons.append("paywalled; do not depend on autonomous scan")
    if "captcha" in health or "manual" in health:
        score -= 20
        reasons.append("manual/CAPTCHA blocker present")
    if not reasons:
        reasons.append("limited health history")
    if score >= 70:
        recommended_weight = "high"
    elif score >= 40:
        recommended_weight = "medium"
    else:
        recommended_weight = "low"
    return {
        "source_name": row.get("source_name", ""),
        "workflow": row.get("workflow", ""),
        "recommended_source_weight": recommended_weight,
        "score": round(score, 2),
        "manual_check_required": bool(login_required or paywalled or "manual" in health or "captcha" in health),
        "evidence_level_expected": "PUBLIC_LISTING_ONLY" if login_required or paywalled else "DETAIL_PAGE_READ",
        "reasons": reasons,
    }


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def render_yaml(payload: dict[str, object]) -> str:
    try:
        import yaml  # type: ignore

        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    except Exception:
        return json.dumps(payload, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend source weights without mutating config")
    parser.add_argument("--dry-run", action="store_true", help="Print recommendations and do not require source config writes")
    parser.add_argument("--output", default="", help="Optional recommendation output path")
    args = parser.parse_args()

    rows = load_rows(SOURCE_HEALTH)
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y%m%d")
    payload = {
        "generated_at": dt.datetime.now(ZoneInfo("Asia/Kolkata")).replace(microsecond=0).isoformat(),
        "source": str(SOURCE_HEALTH.relative_to(PROJECT_ROOT)),
        "dry_run": bool(args.dry_run),
        "mutation_allowed": False,
        "recommendations": [recommendation_for(row) for row in rows],
    }
    output = Path(args.output) if args.output else OUTPUT_DIR / f"source_weight_recommendations_{today}.yaml"
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_yaml(payload), encoding="utf-8")
    print(f"Wrote source-weight recommendations to {output}")
    print("No source config was edited.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
