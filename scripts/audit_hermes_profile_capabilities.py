#!/usr/bin/env python3
"""Detect drift between the Tender Hermes desired state and the live profile."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "config" / "hermes_profile_capabilities.yaml"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "hermes_profile_audit"


def nested(config: dict[str, Any], *keys: str) -> Any:
    value: Any = config
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def resolve_path(value: Any) -> Path:
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def event_evidence_exists(path: Path, event_type: str, source: str) -> bool:
    if not path.is_file():
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event_type") == event_type and (not source or event.get("source") == source):
            return True
    return False


def evaluate_profile(
    manifest: dict[str, Any],
    config: dict[str, Any],
    profile_home: Path,
    *,
    cron_output: str,
    gateway_output: str,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    expected = {
        ("terminal", "cwd"): manifest.get("workspace"),
        ("memory", "write_approval"): nested(manifest, "governed_learning", "memory_write_approval"),
        ("memory", "memory_enabled"): nested(manifest, "governed_learning", "built_in_memory_enabled"),
        ("memory", "user_profile_enabled"): nested(manifest, "governed_learning", "built_in_memory_enabled"),
        ("skills", "write_approval"): nested(manifest, "governed_learning", "skill_write_approval"),
        ("skills", "guard_agent_created"): nested(manifest, "governed_learning", "guard_agent_created_skills"),
        ("agent", "reasoning_effort"): nested(manifest, "reasoning_and_context", "reasoning_effort"),
        ("agent", "max_turns"): nested(manifest, "reasoning_and_context", "max_turns"),
        ("agent", "verify_on_stop"): nested(manifest, "reasoning_and_context", "verify_on_stop"),
        ("web", "search_backend"): nested(manifest, "local_capabilities", "web_search", "backend"),
        ("checkpoints", "enabled"): nested(manifest, "local_capabilities", "filesystem_checkpoints", "enabled"),
    }
    for path, expected_value in expected.items():
        if expected_value is None:
            continue
        actual = nested(config, *path)
        if actual != expected_value:
            findings.append(
                {
                    "severity": "BLOCKER",
                    "code": "CONFIG_DRIFT",
                    "detail": f"{'.'.join(path)} expected {expected_value!r}, got {actual!r}",
                }
            )

    checkpoint_manifest = nested(manifest, "local_capabilities", "filesystem_checkpoints") or {}
    for key in (
        "max_snapshots",
        "max_total_size_mb",
        "max_file_size_mb",
        "auto_prune",
        "retention_days",
        "delete_orphans",
        "min_interval_hours",
    ):
        expected_value = checkpoint_manifest.get(key)
        if expected_value is not None and nested(config, "checkpoints", key) != expected_value:
            findings.append(
                {
                    "severity": "BLOCKER",
                    "code": "CHECKPOINT_CONFIG_DRIFT",
                    "detail": f"checkpoints.{key} expected {expected_value!r}, got {nested(config, 'checkpoints', key)!r}",
                }
            )

    expected_fallbacks = nested(manifest, "local_capabilities", "model_resilience", "fallback_chain") or []
    actual_fallbacks = config.get("fallback_providers") or []
    for expected_fallback in expected_fallbacks:
        if not any(
            isinstance(actual, dict)
            and all(actual.get(key) == value for key, value in expected_fallback.items())
            for actual in actual_fallbacks
        ):
            findings.append(
                {
                    "severity": "BLOCKER",
                    "code": "FALLBACK_MISSING",
                    "detail": f"missing fallback {expected_fallback!r}",
                }
            )

    security_manifest = nested(manifest, "local_capabilities", "deterministic_security") or {}
    if security_manifest.get("website_blocklist_enabled") is True and nested(
        config, "security", "website_blocklist", "enabled"
    ) is not True:
        findings.append(
            {
                "severity": "BLOCKER",
                "code": "WEBSITE_BLOCKLIST_DRIFT",
                "detail": "security.website_blocklist.enabled is not true",
            }
        )
    actual_domains = set(nested(config, "security", "website_blocklist", "domains") or [])
    missing_domains = sorted(set(security_manifest.get("website_blocklist_domains") or []) - actual_domains)
    if missing_domains:
        findings.append(
            {
                "severity": "BLOCKER",
                "code": "WEBSITE_BLOCKLIST_DRIFT",
                "detail": f"missing blocked domains: {missing_domains}",
            }
        )
    actual_deny = set(nested(config, "approvals", "deny") or [])
    missing_deny = sorted(set(security_manifest.get("terminal_deny_globs") or []) - actual_deny)
    if missing_deny:
        findings.append(
            {
                "severity": "BLOCKER",
                "code": "APPROVAL_DENY_MISSING",
                "detail": f"missing approvals.deny patterns: {missing_deny}",
            }
        )

    behavioral = nested(manifest, "local_capabilities", "behavioral_evaluation") or {}
    for code, value in (
        ("BEHAVIORAL_EVAL_SPEC_MISSING", behavioral.get("spec")),
        ("BEHAVIORAL_EVAL_RUNNER_MISSING", behavioral.get("runner")),
    ):
        if value and not resolve_path(value).is_file():
            findings.append({"severity": "BLOCKER", "code": code, "detail": str(value)})
    report_pattern = behavioral.get("latest_report_glob")
    if report_pattern:
        report_paths = [Path(value) for value in glob.glob(str(resolve_path(report_pattern)))]
        latest_report = max(report_paths, key=lambda path: path.stat().st_mtime) if report_paths else None
        if latest_report is None:
            findings.append(
                {
                    "severity": "BLOCKER",
                    "code": "BEHAVIORAL_EVAL_REPORT_MISSING",
                    "detail": str(report_pattern),
                }
            )
        else:
            try:
                latest_payload = json.loads(latest_report.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                latest_payload = {}
            required_status = str(behavioral.get("required_status") or "PASS")
            if latest_payload.get("status") != required_status:
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "code": "BEHAVIORAL_EVAL_NOT_PASSING",
                        "detail": f"{latest_report}: status={latest_payload.get('status')!r}",
                    }
                )
            max_age_hours = behavioral.get("max_age_hours")
            if isinstance(max_age_hours, (int, float)):
                age_hours = (dt.datetime.now(dt.timezone.utc).timestamp() - latest_report.stat().st_mtime) / 3600
                if age_hours > float(max_age_hours):
                    findings.append(
                        {
                            "severity": "BLOCKER",
                            "code": "BEHAVIORAL_EVAL_STALE",
                            "detail": f"{latest_report}: age_hours={age_hours:.1f}",
                        }
                    )

    for skill in nested(manifest, "local_skills", "members") or []:
        if not (profile_home / "skills" / str(skill) / "SKILL.md").is_file():
            findings.append({"severity": "BLOCKER", "code": "SKILL_MISSING", "detail": str(skill)})
    bundle = nested(manifest, "local_skills", "bundle")
    if bundle and not (profile_home / "skill-bundles" / f"{bundle}.yaml").is_file():
        findings.append({"severity": "BLOCKER", "code": "BUNDLE_MISSING", "detail": str(bundle)})

    if nested(manifest, "governed_learning", "built_in_memory_enabled"):
        for filename in ("MEMORY.md", "USER.md"):
            memory_path = profile_home / "memories" / filename
            if not memory_path.is_file() or not memory_path.read_text(encoding="utf-8").strip():
                findings.append(
                    {"severity": "BLOCKER", "code": "MEMORY_FILE_MISSING", "detail": str(memory_path)}
                )

    recovery_config = nested(manifest, "governed_learning", "recovered_context_config")
    recovery_search = nested(manifest, "governed_learning", "recovered_context_search")
    recovery_archive = nested(manifest, "governed_learning", "recovered_context_archive")
    for code, value in (
        ("RECOVERY_CONFIG_MISSING", recovery_config),
        ("RECOVERY_SEARCH_MISSING", recovery_search),
    ):
        if value and not resolve_path(value).is_file():
            findings.append({"severity": "BLOCKER", "code": code, "detail": str(value)})
    if recovery_archive and not Path(str(recovery_archive)).expanduser().is_file():
        findings.append(
            {"severity": "BLOCKER", "code": "RECOVERY_ARCHIVE_MISSING", "detail": str(recovery_archive)}
        )

    for code, value in (
        ("WEB_SCRAPING_CONFIG_MISSING", nested(manifest, "local_capabilities", "web_scraping", "config")),
        ("WEB_SCRAPER_MISSING", nested(manifest, "local_capabilities", "web_scraping", "static_batch")),
        ("JS_CAPTURE_MISSING", nested(manifest, "local_capabilities", "web_scraping", "javascript_rendered")),
    ):
        if value and not resolve_path(value).is_file():
            findings.append({"severity": "BLOCKER", "code": code, "detail": str(value)})

    governed_mcp = nested(manifest, "local_capabilities", "governed_mcp") or {}
    if governed_mcp:
        server_name = str(governed_mcp.get("server_name", ""))
        server = nested(config, "mcp_servers", server_name) or {}
        if not isinstance(server, dict) or not server:
            findings.append(
                {"severity": "BLOCKER", "code": "MCP_SERVER_MISSING", "detail": server_name}
            )
        else:
            expected_command = str(governed_mcp.get("command", ""))
            if server.get("command") != expected_command:
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "code": "MCP_COMMAND_DRIFT",
                        "detail": f"expected {expected_command!r}, got {server.get('command')!r}",
                    }
                )
            expected_script = str(resolve_path(governed_mcp.get("server_script")))
            actual_args = [str(value) for value in server.get("args", [])]
            if actual_args != [expected_script]:
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "code": "MCP_ARGS_DRIFT",
                        "detail": f"expected {[expected_script]!r}, got {actual_args!r}",
                    }
                )
            if server.get("enabled") is not True:
                findings.append(
                    {"severity": "BLOCKER", "code": "MCP_SERVER_DISABLED", "detail": server_name}
                )
            if server.get("supports_parallel_tool_calls") is not bool(
                governed_mcp.get("supports_parallel_tool_calls", False)
            ):
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "code": "MCP_PARALLEL_POLICY_DRIFT",
                        "detail": server_name,
                    }
                )
            if nested(server, "sampling", "enabled") is not bool(
                governed_mcp.get("sampling_enabled", False)
            ):
                findings.append(
                    {"severity": "BLOCKER", "code": "MCP_SAMPLING_POLICY_DRIFT", "detail": server_name}
                )
            if nested(server, "elicitation", "enabled") is not bool(
                governed_mcp.get("elicitation_enabled", False)
            ):
                findings.append(
                    {"severity": "BLOCKER", "code": "MCP_ELICITATION_POLICY_DRIFT", "detail": server_name}
                )
            expected_tools = {str(value) for value in governed_mcp.get("tools", [])}
            actual_tools = set(nested(server, "tools", "include") or [])
            if actual_tools != expected_tools:
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "code": "MCP_TOOL_ALLOWLIST_DRIFT",
                        "detail": f"expected {sorted(expected_tools)}, got {sorted(actual_tools)}",
                    }
                )
            if nested(server, "tools", "resources") is not bool(
                governed_mcp.get("resources_enabled", False)
            ):
                findings.append(
                    {"severity": "BLOCKER", "code": "MCP_RESOURCE_POLICY_DRIFT", "detail": server_name}
                )
            if nested(server, "tools", "prompts") is not bool(
                governed_mcp.get("prompts_enabled", False)
            ):
                findings.append(
                    {"severity": "BLOCKER", "code": "MCP_PROMPT_POLICY_DRIFT", "detail": server_name}
                )

        for code, key in (
            ("MCP_SERVER_SCRIPT_MISSING", "server_script"),
            ("MCP_RUNTIME_REQUIREMENTS_MISSING", "runtime_requirements"),
            ("MCP_POLICY_CONFIG_MISSING", "policy_config"),
            ("MCP_POLICY_FILE_MISSING", "policy_file"),
            ("MCP_RESULT_SCHEMA_MISSING", "result_schema"),
        ):
            value = governed_mcp.get(key)
            if value and not resolve_path(value).is_file():
                findings.append({"severity": "BLOCKER", "code": code, "detail": str(value)})
        expected_command = Path(str(governed_mcp.get("command", ""))).expanduser()
        if not expected_command.is_file() or not expected_command.stat().st_mode & 0o111:
            findings.append(
                {"severity": "BLOCKER", "code": "MCP_PYTHON_NOT_EXECUTABLE", "detail": str(expected_command)}
            )
        policy_binary_name = str(governed_mcp.get("policy_binary", "opa"))
        policy_binary = shutil.which(policy_binary_name)
        policy_file = resolve_path(governed_mcp.get("policy_file", ""))
        if not policy_binary:
            findings.append(
                {"severity": "BLOCKER", "code": "OPA_BINARY_MISSING", "detail": policy_binary_name}
            )
        elif policy_file.is_file():
            checked = subprocess.run(
                [policy_binary, "check", str(policy_file)],
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if checked.returncode != 0:
                findings.append(
                    {
                        "severity": "BLOCKER",
                        "code": "OPA_POLICY_INVALID",
                        "detail": (checked.stderr or checked.stdout).strip()[:1000],
                    }
                )
        evidence_type = str(governed_mcp.get("decision_event_type", ""))
        evidence_file = governed_mcp.get("decision_event_file")
        if evidence_type and evidence_file and not event_evidence_exists(
            resolve_path(evidence_file), evidence_type, str(governed_mcp.get("decision_event_source", ""))
        ):
            findings.append(
                {
                    "severity": "BLOCKER",
                    "code": "MCP_POLICY_EVIDENCE_MISSING",
                    "detail": f"no {evidence_type} evidence in {evidence_file}",
                }
            )

    enabled_plugins = set(nested(config, "plugins", "enabled") or [])
    for plugin in nested(manifest, "local_capabilities", "plugins", "enabled") or []:
        if str(plugin) not in enabled_plugins:
            findings.append({"severity": "BLOCKER", "code": "PLUGIN_NOT_ENABLED", "detail": str(plugin)})
    for hook in manifest.get("gateway_hooks", []) or []:
        name = str(hook.get("name", ""))
        if name and not (profile_home / "hooks" / name / "HOOK.yaml").is_file():
            findings.append({"severity": "BLOCKER", "code": "HOOK_MISSING", "detail": name})
        evidence_type = str(hook.get("evidence_event_type", ""))
        evidence_file = hook.get("evidence_event_file")
        if evidence_type and evidence_file and not event_evidence_exists(
            resolve_path(evidence_file), evidence_type, str(hook.get("evidence_event_source", ""))
        ):
            findings.append(
                {
                    "severity": "BLOCKER",
                    "code": "HOOK_EVIDENCE_MISSING",
                    "detail": f"{name}: no {evidence_type} evidence in {evidence_file}",
                }
            )
    for job in manifest.get("scheduled_jobs", []) or []:
        name = str(job.get("name", ""))
        if name and f"Name:      {name}" not in cron_output and f"Name: {name}" not in cron_output:
            findings.append({"severity": "BLOCKER", "code": "SCHEDULE_MISSING", "detail": name})
    if nested(manifest, "runtime", "gateway_supervision_required") == "launchd" and "supervised by launchd" not in gateway_output.lower():
        findings.append(
            {
                "severity": "BLOCKER",
                "code": "GATEWAY_NOT_SUPERVISED",
                "detail": "launchd supervision was not confirmed",
            }
        )
    return {
        "status": "BLOCKED" if any(item["severity"] == "BLOCKER" for item in findings) else "PASS",
        "profile": manifest.get("profile", ""),
        "profile_home": str(profile_home),
        "findings": findings,
        "safety_boundary": "Read-only drift audit; no profile, cron, gateway, credential, or external state was changed.",
    }


def run_hermes(profile: str, *args: str) -> str:
    completed = subprocess.run(
        ["hermes", "-p", profile, *args],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the live Tender Hermes profile")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    profile = str(manifest.get("profile") or "tender-export-os")
    profile_home = Path.home() / ".hermes" / "profiles" / profile
    config_path = profile_home / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
    report = evaluate_profile(
        manifest,
        config or {},
        profile_home,
        cron_output=run_hermes(profile, "cron", "list"),
        gateway_output=run_hermes(profile, "gateway", "status"),
    )
    report["generated_at"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    report["manifest"] = str(manifest_path)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"hermes_profile_capability_audit_{stamp}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {"status": report["status"], "findings": len(report["findings"]), "report": str(output_path)}
    print(json.dumps(summary, indent=2) if args.json else f"Hermes profile capability audit {report['status']}: {output_path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
