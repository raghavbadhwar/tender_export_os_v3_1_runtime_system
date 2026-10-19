#!/usr/bin/env python3
"""Capture a redacted, reproducible Tender Export OS upgrade baseline.

The script is read-only with respect to Hermes and business registers. Its only
write is the requested local JSON report. Profile archives are created
separately with ``hermes profile export`` so this script never reads or embeds
archive contents, credentials, cookies, or tokens.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - the repo venv includes PyYAML
    yaml = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = "tender-export-os"
DEFAULT_PROFILES_ROOT = Path.home() / ".hermes" / "profiles"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "upgrade_baseline" / "baseline.json"
DEFAULT_ARCHIVE = (
    PROJECT_ROOT
    / "outputs"
    / "upgrade_baseline"
    / "tender-export-os-before-specialists.tar.gz"
)

SECRET_KEY_RE = re.compile(
    r"(?:password|passwd|secret|token|cookie|authorization|api[_-]?key|private[_-]?key|credential)",
    re.I,
)
SECRET_VALUE_RE = re.compile(
    r"(?:authorization\s*:|bearer\s+[A-Za-z0-9._-]+|sk-[A-Za-z0-9_-]{12,}|api[_-]?key\s*[:=]|cookie\s*[:=])",
    re.I,
)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def redact(value: Any, key_hint: str = "") -> Any:
    """Remove secret-bearing fields and obvious credential strings."""

    if key_hint and SECRET_KEY_RE.search(key_hint):
        if isinstance(value, bool) or value is None:
            return value
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(key): redact(item, str(key)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item, key_hint) for item in value]
    if isinstance(value, tuple):
        return [redact(item, key_hint) for item in value]
    if isinstance(value, str) and SECRET_VALUE_RE.search(value):
        return "[REDACTED_STRING]"
    return value


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def is_true(value: Any) -> bool:
    return str(value or "").strip().upper() in {"TRUE", "1", "YES", "Y"}


def capture_data_counts(project_root: Path = PROJECT_ROOT) -> dict[str, int]:
    data = project_root / "data"
    cases = load_csv(data / "master_cases.csv")
    forecasts = load_csv(data / "forecast_candidates.csv")
    backtests = load_csv(data / "forecast_backtests.csv")
    quotes = load_csv(data / "quote_master.csv")
    communications = load_csv(data / "communication_log.csv")
    outreach = load_csv(data / "outreach_queue.csv")

    strict_candidates = sum(
        1
        for row in quotes
        if is_true(row.get("supplier_specific_quote"))
        and not is_true(row.get("indicative_price_only"))
        and bool(str(row.get("quote_proof_path") or "").strip())
    )
    return {
        "master_cases": len(cases),
        "forecast_candidates": len(forecasts),
        "forecast_backtests": len(backtests),
        "mature_forecast_outcomes": sum(is_true(row.get("is_mature")) for row in backtests),
        "quote_rows": len(quotes),
        "strict_quote_proof_candidates": strict_candidates,
        "communication_rows": len(communications),
        "inbound_communications": sum(
            str(row.get("direction") or "").strip().upper() == "INBOUND"
            for row in communications
        ),
        "outreach_rows": len(outreach),
        "sent_outreach": sum(
            str(row.get("send_status") or "").strip().upper() == "SENT"
            for row in outreach
        ),
    }


def run_command(
    command: list[str],
    *,
    cwd: Path = PROJECT_ROOT,
    timeout: int = 30,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return redact(
            {
                "command": command,
                "returncode": completed.returncode,
                "ok": completed.returncode == 0,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {
            "command": command,
            "returncode": None,
            "ok": False,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def read_profile_description(profile_dir: Path) -> str:
    profile_yaml = profile_dir / "profile.yaml"
    if not profile_yaml.is_file():
        return ""
    if yaml is None:
        for line in profile_yaml.read_text(encoding="utf-8").splitlines():
            if line.startswith("description:"):
                return line.split(":", 1)[1].strip().strip("'\"")
        return ""
    payload = yaml.safe_load(profile_yaml.read_text(encoding="utf-8")) or {}
    return str(payload.get("description") or "") if isinstance(payload, dict) else ""


def capture_profiles(profiles_root: Path = DEFAULT_PROFILES_ROOT) -> dict[str, Any]:
    names = sorted(
        path.name
        for path in profiles_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ) if profiles_root.is_dir() else []
    return {
        "profiles_root": str(profiles_root),
        "on_disk": [
            {
                "name": name,
                "description": read_profile_description(profiles_root / name),
                "has_config": (profiles_root / name / "config.yaml").is_file(),
                "has_soul": (profiles_root / name / "SOUL.md").is_file(),
                "has_memory": (profiles_root / name / "memories" / "MEMORY.md").is_file(),
                "has_user_memory": (profiles_root / name / "memories" / "USER.md").is_file(),
                "has_cron": (profiles_root / name / "cron" / "jobs.json").is_file(),
                "gateway_pid": (
                    (profiles_root / name / "gateway.pid").read_text(encoding="utf-8").strip()
                    if (profiles_root / name / "gateway.pid").is_file()
                    else ""
                ),
            }
            for name in names
        ],
        "cli": run_command(["hermes", "profile", "list"]),
    }


def parse_json_stdout(result: dict[str, Any]) -> Any:
    if not result.get("ok"):
        return None
    try:
        return json.loads(str(result.get("stdout") or ""))
    except json.JSONDecodeError:
        return None


def capture_kanban(board: str = "tender-export-os") -> dict[str, Any]:
    boards = run_command(["hermes", "kanban", "boards", "list", "--json"])
    assignees = run_command(
        ["hermes", "kanban", "--board", board, "assignees", "--json"]
    )
    stats = run_command(["hermes", "kanban", "--board", board, "stats", "--json"])
    tasks = run_command(["hermes", "kanban", "--board", board, "list", "--json"])
    return {
        "board": board,
        "boards": parse_json_stdout(boards),
        "assignees": parse_json_stdout(assignees),
        "stats": parse_json_stdout(stats),
        "tasks": parse_json_stdout(tasks),
        "command_status": {
            "boards": boards.get("ok", False),
            "assignees": assignees.get("ok", False),
            "stats": stats.get("ok", False),
            "tasks": tasks.get("ok", False),
        },
    }


def capture_cron(profile: str, profile_home: Path) -> dict[str, Any]:
    jobs_path = profile_home / "cron" / "jobs.json"
    jobs: Any = None
    if jobs_path.is_file():
        try:
            jobs = redact(json.loads(jobs_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            jobs = {"error": "invalid JSON"}
    return {
        "profile": profile,
        "jobs_path": str(jobs_path),
        "jobs_sha256": sha256_file(jobs_path) if jobs_path.is_file() else "",
        "jobs": jobs,
        "cli": run_command(["hermes", "-p", profile, "cron", "list", "--all"]),
    }


def capture_runtime(profile: str, profile_home: Path) -> dict[str, Any]:
    memory_files = {}
    for name in ("MEMORY.md", "USER.md"):
        path = profile_home / "memories" / name
        memory_files[name] = {
            "exists": path.is_file(),
            "bytes": path.stat().st_size if path.is_file() else 0,
            "sha256": sha256_file(path) if path.is_file() else "",
        }
    return {
        "status": run_command(["hermes", "status", "--all"], timeout=60),
        "profile_show": run_command(["hermes", "profile", "show", profile]),
        "config_check": run_command(["hermes", "-p", profile, "config", "check"]),
        "mcp_list": run_command(["hermes", "-p", profile, "mcp", "list"]),
        "skills": run_command(
            ["hermes", "-p", profile, "skills", "list", "--enabled-only"],
            timeout=60,
        ),
        "memory_status": run_command(["hermes", "-p", profile, "memory", "status"]),
        "memory_files": memory_files,
    }


def build_report(
    *,
    project_root: Path = PROJECT_ROOT,
    profile: str = DEFAULT_PROFILE,
    profiles_root: Path = DEFAULT_PROFILES_ROOT,
) -> dict[str, Any]:
    profile_home = profiles_root / profile
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "project_root": str(project_root),
        "profile": profile,
        "safety": {
            "external_actions_executed": False,
            "business_registers_mutated": False,
            "credentials_included": False,
            "note": (
                "Read-only baseline inspection. The report contains hashes and redacted metadata, "
                "not credentials, cookies, tokens, or profile archive contents."
            ),
        },
        "repository": {
            "head": run_command(["git", "rev-parse", "HEAD"], cwd=project_root),
            "branch": run_command(["git", "branch", "--show-current"], cwd=project_root),
            "status": run_command(["git", "status", "--short"], cwd=project_root),
        },
        "profiles": capture_profiles(profiles_root),
        "runtime": capture_runtime(profile, profile_home),
        "cron": capture_cron(profile, profile_home),
        "kanban": capture_kanban(),
        "data_counts": capture_data_counts(project_root),
    }


def write_report(
    output: Path,
    report: dict[str, Any],
    *,
    archive_path: Path | None = None,
) -> dict[str, Any]:
    stored = redact(report)
    if archive_path is not None:
        stored["profile_export"] = {
            "path": str(archive_path),
            "exists": archive_path.is_file(),
            "bytes": archive_path.stat().st_size if archive_path.is_file() else 0,
            "sha256": sha256_file(archive_path) if archive_path.is_file() else "",
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(stored, indent=2, ensure_ascii=False), encoding="utf-8")
    os.chmod(output, 0o600)
    return stored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--profiles-root", default=str(DEFAULT_PROFILES_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    args = parser.parse_args()

    profiles_root = Path(args.profiles_root).expanduser().resolve()
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    archive = Path(args.archive).expanduser()
    if not archive.is_absolute():
        archive = PROJECT_ROOT / archive

    report = build_report(
        project_root=PROJECT_ROOT,
        profile=args.profile,
        profiles_root=profiles_root,
    )
    stored = write_report(output, report, archive_path=archive)
    failed_commands = []
    for section in ("repository",):
        for name, result in stored.get(section, {}).items():
            if isinstance(result, dict) and result.get("ok") is False:
                failed_commands.append(f"{section}.{name}")
    print(
        json.dumps(
            {
                "status": "PASS" if not failed_commands else "PARTIAL",
                "output": str(output),
                "profile_export_sha256": stored.get("profile_export", {}).get("sha256", ""),
                "data_counts": stored.get("data_counts", {}),
                "failed_commands": failed_commands,
                "external_actions_executed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed_commands else 1


if __name__ == "__main__":
    raise SystemExit(main())
