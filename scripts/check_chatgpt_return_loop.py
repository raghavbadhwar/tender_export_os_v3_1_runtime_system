#!/usr/bin/env python3
"""Dry-run check for the ChatGPT -> Hermes/Codex return loop."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from validate_chatgpt_return import validate_file  # noqa: E402

REQUIRED_FOLDERS = [
    "outputs/chatgpt_bridge/to_chatgpt",
    "outputs/chatgpt_bridge/from_chatgpt",
    "outputs/chatgpt_bridge/reviewed",
]
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "chatgpt_bridge" / "return_loop_check.json"
DEFAULT_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "chatgpt_returns" / "good_return.md"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def resolve_fixture(project_root: Path, fixture_return: Path) -> Path:
    if fixture_return.is_absolute() and fixture_return.exists():
        return fixture_return
    candidate = project_root / fixture_return
    if candidate.exists():
        return candidate
    candidate = PROJECT_ROOT / fixture_return
    if candidate.exists():
        return candidate
    raise FileNotFoundError(fixture_return)


def build_chatgpt_return_loop_report(project_root: Path, fixture_return: Path = DEFAULT_FIXTURE) -> dict[str, Any]:
    project_root = Path(project_root)
    folder_results = []
    for rel in REQUIRED_FOLDERS:
        folder = project_root / rel
        folder.mkdir(parents=True, exist_ok=True)
        folder_results.append({"path": rel, "exists": folder.exists()})

    fixture = resolve_fixture(project_root, Path(fixture_return))
    valid, errors = validate_file(fixture)
    staging_probe_ok = False
    staging_probe_dir = project_root / "outputs" / "chatgpt_bridge" / "from_chatgpt" / "DRYRUN_STAGING_PROBE"
    if valid:
        staging_probe_dir.mkdir(parents=True, exist_ok=True)
        staged = staging_probe_dir / fixture.name
        shutil.copy2(fixture, staged)
        review_plan = {
            "return_id": "DRYRUN-STAGING-PROBE",
            "direction": "chatgpt_to_codex_hermes",
            "review_required": True,
            "state_mutation_allowed": False,
            "source_fixture": str(fixture),
            "required_review_steps": [
                "Validate schema and citations.",
                "Translate accepted recommendations into reviewed tasks only.",
                "Never mutate registers or execute external actions directly from ChatGPT output.",
            ],
        }
        (staging_probe_dir / "review_plan.json").write_text(json.dumps(review_plan, indent=2), encoding="utf-8")
        staging_probe_ok = staged.exists() and (staging_probe_dir / "review_plan.json").exists()

    return {
        "generated_at": now_iso(),
        "mode": "dry_run_only",
        "external_actions_executed": False,
        "repo_registers_mutated": False,
        "drive_uploaded_or_downloaded": False,
        "required_folders": folder_results,
        "required_folders_ok": all(item["exists"] for item in folder_results),
        "fixture_return": str(fixture),
        "fixture_validation_ok": valid,
        "fixture_validation_errors": errors,
        "staging_probe_dir": str(staging_probe_dir),
        "staging_probe_ok": staging_probe_ok,
        "safety_note": "Dry-run only. No Drive import/export, register mutation, external send, submission, upload, payment, DSC, final price, final classification, or origin claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ChatGPT return loop in dry-run mode")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--fixture-return", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    report = build_chatgpt_return_loop_report(Path(args.project_root), Path(args.fixture_return))
    output = Path(args.output)
    if not output.is_absolute():
        output = Path(args.project_root) / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"ChatGPT return loop dry-run check: {output}")
    print(f"folders_ok={report['required_folders_ok']} fixture_ok={report['fixture_validation_ok']} staging_probe_ok={report['staging_probe_ok']}")
    print("No Drive transfer, repo register mutation, or external action executed.")
    return 0 if report["required_folders_ok"] and report["fixture_validation_ok"] and report["staging_probe_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
