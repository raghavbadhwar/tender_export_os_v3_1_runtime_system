#!/usr/bin/env python3
"""Capture bounded GOV history from pre-captured official/public evidence packets.

This job intentionally does not browse, authenticate, or fetch a portal.  A
separate read-only capture lane must first place a small JSON packet beneath
the private evidence root.  Each imported row keeps the source URL, packet
path, and packet SHA-256 so historical intelligence never becomes an
untraceable or inferred award dataset.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - surfaced by the CLI
    yaml = None  # type: ignore[assignment]

from scripts.event_ledger import append_event


CONFIG_PATH = PROJECT_ROOT / "config" / "historical_capture.yaml"
NOTICE_PATH = PROJECT_ROOT / "data" / "historical_tender_notices.csv"
AWARD_PATH = PROJECT_ROOT / "data" / "historical_awards.csv"
EVENTS_PATH = PROJECT_ROOT / "data" / "events.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "historical_intelligence"

NOTICE_COLUMNS = [
    "notice_id",
    "source_record_id",
    "buyer_name",
    "buyer_normalized",
    "buyer_type",
    "workflow_type",
    "country_or_state",
    "source_name",
    "source_url",
    "category_code",
    "category_name",
    "category_normalized",
    "product_or_service",
    "notice_date",
    "deadline_date",
    "estimated_value_inr",
    "emd_amount_inr",
    "competition_signal",
    "evidence_level",
    "evidence_path",
    "evidence_sha256",
    "source_confidence",
    "created_at",
]
AWARD_COLUMNS = [
    "award_id",
    "source_record_id",
    "notice_id",
    "buyer_name",
    "buyer_normalized",
    "winner_name",
    "award_date",
    "award_value_inr",
    "bidder_count",
    "l1_price_inr",
    "l2_price_inr",
    "competition_signal",
    "category_code",
    "category_name",
    "category_normalized",
    "source_name",
    "source_url",
    "evidence_level",
    "evidence_path",
    "evidence_sha256",
    "source_confidence",
    "created_at",
]
DEFAULT_CONFIDENCE = {
    "PUBLIC_LISTING_ONLY": 60,
    "DETAIL_PAGE_READ": 80,
    "DOCUMENTS_DISCOVERED": 85,
    "DOCUMENTS_DOWNLOADED": 90,
    "STRUCTURED_EVIDENCE_BUNDLE": 95,
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load config/historical_capture.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Historical capture configuration must be a mapping: {path}")
    return value


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalized_text(value: Any) -> str:
    return clean_text(value).casefold()


def clean_number(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    try:
        number = float(text.replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"numeric field is invalid: {text!r}") from exc
    return str(int(number)) if number.is_integer() else str(number)


def clean_date(value: Any, field: str, *, required: bool) -> str:
    text = clean_text(value)
    if not text:
        if required:
            raise ValueError(f"{field} is required")
        return ""
    try:
        return dt.date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 date") from exc


def canonical_id(prefix: str, source_name: str, source_record_id: str) -> str:
    identity = f"{normalized_text(source_name)}|{clean_text(source_record_id)}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16].upper()
    return f"{prefix}-{digest}"


def official_public_url(source_url: str, official_domains: set[str]) -> bool:
    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").casefold().rstrip(".")
    allowed = {domain.casefold().rstrip(".") for domain in official_domains}
    return (
        parsed.scheme == "https"
        and bool(hostname)
        and not parsed.username
        and not parsed.password
        and any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed)
    )


def require_official_public_url(source_url: str, official_domains: set[str]) -> None:
    if not official_public_url(source_url, official_domains):
        raise ValueError("source_url must be an HTTPS official public source on the configured allowlist")


def source_confidence(
    row: dict[str, Any],
    *,
    evidence_level: str,
    confidence_by_level: dict[str, Any] | None = None,
    source_confidence_overrides: dict[str, Any] | None = None,
) -> str:
    levels = confidence_by_level or DEFAULT_CONFIDENCE
    if evidence_level not in levels:
        raise ValueError(f"unsupported evidence_level: {evidence_level!r}")
    confidence = int(levels[evidence_level])
    source_name = clean_text(row.get("source_name"))
    overrides = source_confidence_overrides or {}
    for name, value in overrides.items():
        if normalized_text(name) == normalized_text(source_name):
            confidence = min(confidence, int(value))
            break
    supplied = clean_text(row.get("source_confidence"))
    if supplied:
        try:
            confidence = min(confidence, int(float(supplied)))
        except ValueError as exc:
            raise ValueError("source_confidence must be numeric") from exc
    if not 0 <= confidence <= 100:
        raise ValueError("source_confidence must be within 0..100")
    return str(confidence)


def _required(value: Any, field: str) -> str:
    text = clean_text(value)
    if not text:
        raise ValueError(f"{field} is required")
    return text


def normalize_record(
    record: dict[str, Any],
    *,
    kind: str,
    packet_path: Path,
    official_domains: set[str],
    as_of: str,
    confidence_by_level: dict[str, Any] | None = None,
    source_confidence_overrides: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Normalize one record and attach immutable evidence provenance.

    ``kind`` is deliberately explicit so an award cannot be derived from a
    notice merely because it appears in the same packet.
    """
    if kind not in {"notice", "award"}:
        raise ValueError(f"unsupported historical record kind: {kind}")
    if not packet_path.is_file():
        raise ValueError(f"evidence packet does not exist: {packet_path}")

    source_name = _required(record.get("source_name"), "source_name")
    source_url = _required(record.get("source_url"), "source_url")
    require_official_public_url(source_url, official_domains)
    source_record_id = _required(record.get("source_record_id"), "source_record_id")
    buyer_name = _required(record.get("buyer_name"), "buyer_name")
    category_name = _required(record.get("category_name") or record.get("category"), "category_name")
    evidence_level = _required(record.get("evidence_level"), "evidence_level").upper()
    evidence_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    confidence = source_confidence(
        record,
        evidence_level=evidence_level,
        confidence_by_level=confidence_by_level,
        source_confidence_overrides=source_confidence_overrides,
    )
    common = {
        "source_record_id": source_record_id,
        "buyer_name": buyer_name,
        "buyer_normalized": normalized_text(buyer_name),
        "category_code": clean_text(record.get("category_code")),
        "category_name": category_name,
        "category_normalized": normalized_text(category_name),
        "source_name": source_name,
        "source_url": source_url,
        "evidence_level": evidence_level,
        "evidence_path": str(packet_path),
        "evidence_sha256": evidence_sha256,
        "source_confidence": confidence,
        "created_at": clean_date(as_of, "as_of", required=True),
    }
    if kind == "notice":
        return {
            "notice_id": clean_text(record.get("notice_id")) or canonical_id("HTN", source_name, source_record_id),
            **common,
            "buyer_type": clean_text(record.get("buyer_type")) or "Government",
            "workflow_type": "GOV",
            "country_or_state": clean_text(record.get("country_or_state") or record.get("state")),
            "product_or_service": clean_text(record.get("product_or_service") or record.get("title")),
            "notice_date": clean_date(record.get("notice_date"), "notice_date", required=True),
            "deadline_date": clean_date(record.get("deadline_date"), "deadline_date", required=False),
            "estimated_value_inr": clean_number(record.get("estimated_value_inr")),
            "emd_amount_inr": clean_number(record.get("emd_amount_inr")),
            "competition_signal": clean_text(record.get("competition_signal")),
        }
    return {
        "award_id": clean_text(record.get("award_id")) or canonical_id("HAW", source_name, source_record_id),
        **common,
        "notice_id": clean_text(record.get("notice_id")),
        "winner_name": _required(record.get("winner_name"), "winner_name"),
        "award_date": clean_date(record.get("award_date"), "award_date", required=True),
        "award_value_inr": clean_number(record.get("award_value_inr")),
        "bidder_count": clean_number(record.get("bidder_count")),
        "l1_price_inr": clean_number(record.get("l1_price_inr")),
        "l2_price_inr": clean_number(record.get("l2_price_inr")),
        "competition_signal": clean_text(record.get("competition_signal")),
    }


def _unique_paths(packet_paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    values: list[Path] = []
    for path in packet_paths:
        resolved = path.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            values.append(resolved)
    return sorted(values, key=str)


def capture_packets(
    packet_paths: Iterable[Path],
    *,
    official_domains: set[str],
    max_packets: int,
    max_records: int,
    as_of: str,
    confidence_by_level: dict[str, Any] | None = None,
    source_confidence_overrides: dict[str, Any] | None = None,
    max_packet_bytes: int = 5_000_000,
) -> dict[str, Any]:
    """Read a bounded set of evidence packets without making network calls."""
    if max_packets < 1 or max_records < 1 or max_packet_bytes < 1:
        raise ValueError("max_packets, max_records, and max_packet_bytes must be positive")
    paths = _unique_paths(packet_paths)
    selected = paths[:max_packets]
    notices: list[dict[str, str]] = []
    awards: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    seen_records: set[tuple[str, str]] = set()
    records_seen = 0
    record_limit_reached = False
    for packet_path in selected:
        if not packet_path.is_file():
            rejected.append({"packet_path": str(packet_path), "reason": "packet_not_found"})
            continue
        if packet_path.stat().st_size > max_packet_bytes:
            rejected.append({"packet_path": str(packet_path), "reason": "packet_exceeds_max_packet_bytes"})
            continue
        try:
            payload = json.loads(packet_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            rejected.append({"packet_path": str(packet_path), "reason": f"invalid_json:{exc}"})
            continue
        if not isinstance(payload, dict):
            rejected.append({"packet_path": str(packet_path), "reason": "packet_must_be_object"})
            continue
        packet_source_name = clean_text(payload.get("source_name"))
        packet_source_url = clean_text(payload.get("source_url"))
        for kind, collection in (("notice", payload.get("notices", [])), ("award", payload.get("awards", []))):
            if not isinstance(collection, list):
                rejected.append({"packet_path": str(packet_path), "reason": f"{kind}s_must_be_list"})
                continue
            for raw in collection:
                if records_seen >= max_records:
                    record_limit_reached = True
                    break
                if not isinstance(raw, dict):
                    rejected.append({"packet_path": str(packet_path), "reason": f"{kind}_record_must_be_object"})
                    continue
                prepared = dict(raw)
                prepared.setdefault("source_name", packet_source_name)
                prepared.setdefault("source_url", packet_source_url)
                try:
                    row = normalize_record(
                        prepared,
                        kind=kind,
                        packet_path=packet_path,
                        official_domains=official_domains,
                        as_of=as_of,
                        confidence_by_level=confidence_by_level,
                        source_confidence_overrides=source_confidence_overrides,
                    )
                except ValueError as exc:
                    rejected.append({"packet_path": str(packet_path), "reason": f"{kind}:{exc}"})
                    continue
                key = (kind, row["notice_id"] if kind == "notice" else row["award_id"])
                if key in seen_records:
                    continue
                seen_records.add(key)
                records_seen += 1
                (notices if kind == "notice" else awards).append(row)
            if record_limit_reached:
                break
        if record_limit_reached:
            break
    return {
        "status": "PASS",
        "mode": "official_public_evidence_only",
        "as_of": clean_date(as_of, "as_of", required=True),
        "packets_discovered": len(paths),
        "packets_processed": len(selected),
        "records_captured": len(notices) + len(awards),
        "notice_count": len(notices),
        "award_count": len(awards),
        "bounded": True,
        "packet_limit_reached": len(paths) > len(selected),
        "record_limit_reached": record_limit_reached,
        "notices": notices,
        "awards": awards,
        "rejected_records": rejected,
        "external_actions_executed": False,
    }


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def upsert_rows(path: Path, columns: list[str], key: str, rows: list[dict[str, str]]) -> bool:
    current = load_csv(path)
    index = {str(row.get(key) or ""): position for position, row in enumerate(current)}
    changed = False
    for row in rows:
        normalized = {column: str(row.get(column) or "") for column in columns}
        row_id = normalized[key]
        if not row_id:
            raise ValueError(f"{key} is required for projection upsert")
        if row_id in index:
            if current[index[row_id]] != normalized:
                current[index[row_id]] = normalized
                changed = True
        else:
            index[row_id] = len(current)
            current.append(normalized)
            changed = True
    if not changed:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(current)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return True


def write_capture(
    capture: dict[str, Any],
    *,
    notices_path: Path = NOTICE_PATH,
    awards_path: Path = AWARD_PATH,
    events_path: Path = EVENTS_PATH,
    actor: str = "historical_gov_capture",
) -> dict[str, Any]:
    """Append canonical events first, then refresh the two CSV projections."""
    event_ids: list[str] = []
    for kind, rows, object_type, key in (
        ("notice", capture.get("notices", []), "historical_notice", "notice_id"),
        ("award", capture.get("awards", []), "historical_award", "award_id"),
    ):
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"captured {kind} row must be an object")
            row_id = str(row.get(key) or "")
            evidence_sha256 = str(row.get("evidence_sha256") or "")
            event = append_event(
                f"{object_type}.captured",
                actor,
                object_type=object_type,
                object_id=row_id,
                source="official_public_historical_capture",
                payload={"row": row},
                citations=[str(row.get("evidence_path") or ""), str(row.get("source_url") or "")],
                idempotency_key=f"{object_type}:{row_id}:{evidence_sha256}",
                events_file=events_path,
            )
            event_ids.append(str(event["event_id"]))
    notices_changed = upsert_rows(notices_path, NOTICE_COLUMNS, "notice_id", list(capture.get("notices", [])))
    awards_changed = upsert_rows(awards_path, AWARD_COLUMNS, "award_id", list(capture.get("awards", [])))
    return {
        "canonical_event_appended": bool(event_ids),
        "event_ids": event_ids,
        "notice_projection_updated": notices_changed,
        "award_projection_updated": awards_changed,
        "external_actions_executed": False,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"historical_gov_capture_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--input-root", default="")
    parser.add_argument("--packet", action="append", default=[], help="Explicit packet path; may be repeated")
    parser.add_argument("--max-packets", type=int)
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Append evidence-backed events and refresh projections")
    mode.add_argument("--dry-run", action="store_true", help="Explicitly keep the default no-write mode")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    config = load_config(config_path)
    limits = config.get("limits", {}) if isinstance(config.get("limits"), dict) else {}
    root = Path(args.input_root or config.get("input_root") or "outputs/evidence/private").expanduser()
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    packet_glob = str(config.get("packet_glob") or "**/historical_gov_packet*.json")
    packet_paths = [Path(value).expanduser() for value in args.packet] or list(root.glob(packet_glob))
    report = capture_packets(
        packet_paths,
        official_domains={str(value) for value in config.get("official_domains", [])},
        max_packets=args.max_packets or int(limits.get("max_packets_per_run", 20)),
        max_records=args.max_records or int(limits.get("max_records_per_run", 200)),
        max_packet_bytes=int(limits.get("max_packet_bytes", 5_000_000)),
        as_of=args.as_of,
        confidence_by_level=config.get("evidence_confidence") if isinstance(config.get("evidence_confidence"), dict) else None,
        source_confidence_overrides=config.get("source_confidence_overrides") if isinstance(config.get("source_confidence_overrides"), dict) else None,
    )
    report["mode"] = "write" if args.write else "dry_run"
    report["input_root"] = str(root)
    report["network_capture_in_this_job"] = False
    report["raw_evidence_root"] = str(root)
    if args.write:
        report["write_result"] = write_capture(report)
    else:
        report["write_result"] = {
            "canonical_event_appended": False,
            "notice_projection_updated": False,
            "award_projection_updated": False,
            "external_actions_executed": False,
        }
    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    report_path = write_report(report, output_dir)
    report["report_path"] = str(report_path)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else f"Historical GOV capture: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
