#!/usr/bin/env python3
"""Refresh a case evidence bundle and SHA-256 manifest."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from event_ledger import append_event

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = PROJECT_ROOT / "cases"


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_evidence_files(evidence_dir: Path) -> list[Path]:
    excluded = {"metadata.json", "sha256sums.txt"}
    files = []
    for path in evidence_dir.rglob("*"):
        if path.is_file() and path.name not in excluded:
            files.append(path)
    return sorted(files)


def refresh(case_id: str, *, record_event: bool = False) -> Path:
    evidence_dir = CASES_DIR / case_id / "evidence"
    if not evidence_dir.exists():
        raise SystemExit(f"Evidence folder missing for {case_id}. Run create_case_workspace.py first.")
    files = iter_evidence_files(evidence_dir)
    hashes = []
    for path in files:
        hashes.append({"path": rel(path), "sha256": sha256_file(path)})
    hash_path = evidence_dir / "hashes" / "sha256sums.txt"
    hash_path.parent.mkdir(parents=True, exist_ok=True)
    hash_path.write_text("".join(f"{item['sha256']}  {item['path']}\n" for item in hashes), encoding="utf-8")
    metadata_path = evidence_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    else:
        metadata = {"case_id": case_id, "evidence_items": []}
    metadata.update({
        "case_id": case_id,
        "refreshed_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "evidence_item_count": len(hashes),
        "evidence_items": hashes,
        "hash_manifest": rel(hash_path),
    })
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if record_event:
        append_event(
            "evidence.file_hashed",
            "capture_case_evidence",
            case_id=case_id,
            object_type="evidence",
            object_id=rel(evidence_dir),
            payload={"file_count": len(hashes), "hash_manifest": rel(hash_path)},
            citations=[rel(metadata_path), rel(hash_path)],
        )
    return metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh case evidence metadata and hashes")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()
    path = refresh(args.case_id, record_event=args.record_event)
    print(f"Refreshed {rel(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
