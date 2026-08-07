#!/usr/bin/env python3
"""Persist Hermes Insights as privacy-minimized aggregate metrics."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "hermes_insights"


def integer(value: str) -> int:
    return int(value.replace(",", ""))


def parse_overview(text: str) -> dict[str, int]:
    patterns = {
        "sessions": r"Sessions:\s*([\d,]+)",
        "messages": r"Messages:\s*([\d,]+)",
        "tool_calls": r"Tool calls:\s*([\d,]+)",
        "user_messages": r"User messages:\s*([\d,]+)",
        "input_tokens": r"Input tokens:\s*([\d,]+)",
        "output_tokens": r"Output tokens:\s*([\d,]+)",
        "total_tokens": r"Total tokens:\s*([\d,]+)",
    }
    return {name: integer(match.group(1)) for name, pattern in patterns.items() if (match := re.search(pattern, text))}


def section(text: str, heading: str, next_headings: list[str]) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    tail = text[start + len(heading):]
    end_positions = [tail.find(candidate) for candidate in next_headings if tail.find(candidate) >= 0]
    return tail[: min(end_positions)] if end_positions else tail


def parse_models(text: str) -> list[dict[str, Any]]:
    body = section(text, "🤖 Models Used", ["🔧 Top Tools", "🧠 Top Skills"])
    rows = []
    for match in re.finditer(r"^\s{2,}([^\s]+)\s+([\d,]+)\s+([\d,]+)\s*$", body, re.MULTILINE):
        if match.group(1) == "Model":
            continue
        rows.append({"name": match.group(1), "count": integer(match.group(2)), "tokens": integer(match.group(3))})
    return rows


def parse_tools(text: str) -> list[dict[str, Any]]:
    body = section(text, "🔧 Top Tools", ["🧠 Top Skills", "📅 Activity Patterns"])
    rows = []
    for match in re.finditer(r"^\s{2,}([^\n]+?)\s{2,}([\d,]+)\s+([\d.]+)%\s*$", body, re.MULTILINE):
        name = match.group(1).strip()
        if name == "Tool":
            continue
        rows.append({"name": name, "count": integer(match.group(2)), "percentage": float(match.group(3))})
    return rows


def parse_skills(text: str) -> list[dict[str, Any]]:
    body = section(text, "🧠 Top Skills", ["📅 Activity Patterns"])
    rows = []
    for match in re.finditer(r"^\s{2,}([^\n]+?)\s{2,}([\d,]+)\s+([\d,]+)\s{2,}([^\n]+?)\s*$", body, re.MULTILINE):
        name = match.group(1).strip()
        if name in {"Skill", "Distinct skills:"} or name.startswith("Distinct skills:"):
            continue
        rows.append({"name": name, "count": integer(match.group(2)), "edits": integer(match.group(3)), "last_used": match.group(4).strip()})
    return rows


def parse_insights(text: str, *, profile: str, generated_at: str | None = None) -> dict[str, Any]:
    period_match = re.search(r"^\s*Period:\s*(.+?)\s*$", text, re.MULTILINE)
    metrics = parse_overview(text)
    metrics.update({"models": parse_models(text), "tools": parse_tools(text), "skills": parse_skills(text)})
    required = ["sessions", "messages", "tool_calls", "input_tokens", "output_tokens", "total_tokens"]
    missing = [key for key in required if key not in metrics]
    if missing:
        raise ValueError(f"Insights output missing overview metrics: {', '.join(missing)}")
    return {
        "schema_version": "hermes_insights_summary.v1",
        "profile": profile,
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "period": period_match.group(1).strip() if period_match else "unknown",
        "metrics": metrics,
        "source_output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "raw_output_persisted": False,
    }


def write_summary(summary: dict[str, Any], output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"{summary['profile']}_insights_{stamp}.json"
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="tender-export-os")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--input", help="Use a fixture file instead of invoking Hermes")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        completed = subprocess.run(
            ["hermes", "--profile", args.profile, "insights", "--days", str(args.days)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            print(json.dumps({"status": "FAIL", "stderr_tail": completed.stderr[-1000:]}, indent=2))
            return completed.returncode or 1
        text = completed.stdout
    summary = parse_insights(text, profile=args.profile)
    path = write_summary(summary, Path(args.output_dir).expanduser())
    payload = {"status": "PASS", "summary": str(path), "raw_output_persisted": False, "tool_calls": summary["metrics"]["tool_calls"]}
    print(json.dumps(payload, indent=2) if args.json else f"Insights summary: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
