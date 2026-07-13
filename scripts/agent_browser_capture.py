#!/usr/bin/env python3
"""Capture public web evidence with agent-browser in a read-only command lane."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import re
import socket
import subprocess
import uuid
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

try:
    from event_ledger import append_event
except ModuleNotFoundError:  # pragma: no cover
    from scripts.event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_EVIDENCE_ROOT = PROJECT_ROOT / "outputs" / "evidence" / "private"
DEFAULT_OUTPUT_ROOT = PRIVATE_EVIDENCE_ROOT / "agent_browser"
PROFILE_ROOT = PROJECT_ROOT / ".local" / "browser_profiles" / "agent_browser"
READ_ONLY_COMMANDS = {"open", "snapshot", "get", "screenshot", "close"}
BLOCKER_MARKERS = {
    "verify you are human": "CAPTCHA_BLOCKED",
    "complete the captcha": "CAPTCHA_BLOCKED",
    "captcha challenge": "CAPTCHA_BLOCKED",
    "i'm not a robot": "CAPTCHA_BLOCKED",
    "access denied": "ACCESS_BLOCKED",
    "forbidden": "ACCESS_BLOCKED",
    "you must log in": "MANUAL_LOGIN_REQUIRED",
    "login required": "MANUAL_LOGIN_REQUIRED",
    "please log in to continue": "MANUAL_LOGIN_REQUIRED",
    "subscription required": "PAYWALL_BLOCKED",
    "subscribe to continue": "PAYWALL_BLOCKED",
    "paywall": "PAYWALL_BLOCKED",
    "ignore previous instructions": "PROMPT_INJECTION_DETECTED",
    "ignore all previous instructions": "PROMPT_INJECTION_DETECTED",
    "reveal your instructions": "PROMPT_INJECTION_DETECTED",
    "system prompt": "PROMPT_INJECTION_DETECTED",
    "net::err_timed_out": "NAVIGATION_TIMEOUT",
    "navigation timeout": "NAVIGATION_TIMEOUT",
    "timed out after": "CAPTURE_TIMEOUT",
}


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:64] or "source"


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_private_evidence_root(output_root: Path) -> Path:
    """Reject accidental raw browser artifact writes outside the private root."""
    resolved = output_root.expanduser().resolve()
    private_root = PRIVATE_EVIDENCE_ROOT.expanduser().resolve()
    try:
        resolved.relative_to(private_root)
    except ValueError as exc:
        raise ValueError(f"raw browser evidence must stay under private root: {private_root}") from exc
    return resolved


def public_hostname(url: str, *, resolve_dns: bool = True) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("agent-browser capture requires a credential-free public HTTPS URL")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("local/private hosts are not permitted")
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        addresses = []
        if resolve_dns:
            for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
                addresses.append(ipaddress.ip_address(result[4][0]))
    if not addresses and resolve_dns:
        raise ValueError(f"public host did not resolve: {host}")
    if any(not address.is_global for address in addresses):
        raise ValueError("local, private, reserved, or link-local destinations are not permitted")
    return host


def allowed_domains(host: str) -> str:
    labels = host.split(".")
    bare = host[4:] if host.startswith("www.") else host
    domains = [bare, f"*.{bare}"]
    if len(labels) > 2 and not host.startswith("www."):
        domains.insert(0, host)
    return ",".join(dict.fromkeys(domains))


def base_command(session: str, profile: Path, host: str) -> list[str]:
    return [
        "agent-browser",
        "--session",
        session,
        "--profile",
        str(profile),
        "--allowed-domains",
        allowed_domains(host),
        "--content-boundaries",
        "--max-output",
        "50000",
        "--json",
    ]


def command(base: list[str], action: str, *arguments: str) -> list[str]:
    if action not in READ_ONLY_COMMANDS:
        raise ValueError(f"agent-browser action is not read-only: {action}")
    return [*base, action, *arguments]


def run_process(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def process_output(value: object) -> str:
    """Return subprocess output safely when a command times out mid-stream."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value or "")


def blocker_status(*values: str) -> list[str]:
    text = "\n".join(values).lower()
    return sorted({status for marker, status in BLOCKER_MARKERS.items() if marker in text})


def capture(
    *,
    url: str,
    source_name: str,
    case_id: str = "",
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    timeout: int = 90,
    resolve_dns: bool = True,
    record_event: bool = False,
    runner: Callable[[list[str], int], subprocess.CompletedProcess[str]] = run_process,
) -> tuple[dict, Path]:
    host = public_hostname(url, resolve_dns=resolve_dns)
    output_root = require_private_evidence_root(output_root)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    capture_id = f"ABCAP-{timestamp}-{uuid.uuid4().hex[:8]}"
    source_slug = safe_slug(source_name)
    output_dir = output_root / capture_id
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = PROFILE_ROOT / source_slug
    profile.mkdir(parents=True, exist_ok=True)
    session = f"teos-{source_slug}-{uuid.uuid4().hex[:8]}"
    base = base_command(session, profile, host)
    artifacts: dict[str, str] = {}
    steps: list[dict] = []

    def execute(action: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        args = command(base, action, *arguments)
        try:
            result = runner(args, timeout)
        except subprocess.TimeoutExpired as exc:
            message = f"agent-browser {action} timed out after {timeout} seconds"
            result = subprocess.CompletedProcess(
                args=args,
                returncode=-1,
                stdout=process_output(exc.stdout),
                stderr="\n".join(part for part in (process_output(exc.stderr), message) if part),
            )
            steps.append(
                {
                    "action": action,
                    "returncode": -1,
                    "stderr": result.stderr[-2000:],
                    "timed_out": True,
                }
            )
            return result
        except OSError as exc:
            result = subprocess.CompletedProcess(args=args, returncode=-1, stdout="", stderr=str(exc))
        steps.append(
            {
                "action": action,
                "returncode": result.returncode,
                "stderr": result.stderr[-2000:],
            }
        )
        return result

    try:
        opened = execute("open", url)
        snapshot = execute("snapshot", "-i", "-c") if opened.returncode == 0 else None
        page_text = execute("get", "text", "body") if opened.returncode == 0 else None

        for name, result in (("open", opened), ("snapshot", snapshot), ("page_text", page_text)):
            if result is None:
                continue
            path = output_dir / f"{name}.json"
            path.write_text(result.stdout, encoding="utf-8")
            artifacts[name] = relative(path)

        screenshot_path = output_dir / "page.png"
        screenshot = execute("screenshot", str(screenshot_path), "--full") if opened.returncode == 0 else None
        if screenshot is not None and screenshot.returncode == 0 and screenshot_path.exists():
            artifacts["screenshot"] = relative(screenshot_path)

        texts = [
            value
            for result in (opened, snapshot, page_text)
            if result is not None
            for value in (result.stdout, result.stderr)
        ]
        blockers = blocker_status(*texts)
        status = "COMPLETED" if opened.returncode == 0 else "FAILED"
        if blockers and status == "COMPLETED":
            status = "COMPLETED_WITH_BLOCKERS"
    finally:
        try:
            execute("close")
        except Exception as exc:  # pragma: no cover - cleanup best effort
            steps.append({"action": "close", "returncode": -1, "stderr": str(exc)})

    hashes = {}
    for name, value in artifacts.items():
        path = PROJECT_ROOT / value if not Path(value).is_absolute() else Path(value)
        if path.is_file():
            hashes[name] = sha256(path)

    receipt = {
        "capture_id": capture_id,
        "captured_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "case_id": case_id,
        "source_name": source_name,
        "url": url,
        "host": host,
        "status": status,
        "blockers": blockers,
        "artifacts": artifacts,
        "sha256": hashes,
        "steps": steps,
        "browser": "agent-browser",
        "mode": "READ_ONLY_EVIDENCE",
        "permitted_commands": sorted(READ_ONLY_COMMANDS),
        "external_business_actions": False,
        "safety": "No click, fill, type, submit, upload, download, message, payment, DSC, or commercial commitment command is available in this capture lane.",
    }
    receipt_path = output_dir / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    citations = [url, relative(receipt_path), *artifacts.values()]
    if record_event:
        event_type = "browser.capture_completed" if status != "FAILED" else "browser.capture_failed"
        append_event(
            event_type,
            "agent_browser_capture",
            case_id=case_id,
            object_type="browser_capture",
            object_id=capture_id,
            source="agent_browser",
            payload={
                "capture_id": capture_id,
                "status": status,
                "receipt_path": relative(receipt_path),
                "source_name": source_name,
                "blockers": blockers,
                "external_business_actions": False,
            },
            citations=citations,
            idempotency_key=f"agent-browser-capture:{capture_id}",
        )
    return receipt, receipt_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only agent-browser evidence capture")
    parser.add_argument("--url", required=True)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()

    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root
    receipt, path = capture(
        url=args.url,
        source_name=args.source_name,
        case_id=args.case_id,
        output_root=output_root,
        timeout=args.timeout,
        record_event=args.record_event,
    )
    print(json.dumps({"status": receipt["status"], "capture_id": receipt["capture_id"], "receipt": relative(path)}, indent=2))
    return 0 if receipt["status"] != "FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
