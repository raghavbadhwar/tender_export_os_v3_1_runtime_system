#!/usr/bin/env python3
"""Record final owner signoff only after evidence-driven readiness blockers are gone."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.generate_final_readiness_receipt import OWNER_SIGNOFF, generate_receipt


def record_signoff(*, approved_by: str, note: str = "") -> dict:
    readiness = generate_receipt()
    if readiness["blocking_tasks"]:
        return {
            "status": "BLOCKED",
            "signed": False,
            "blocking_tasks": [row["task_id"] for row in readiness["blocking_tasks"]],
            "message": "Owner signoff cannot be recorded while readiness blockers remain.",
        }

    OWNER_SIGNOFF.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "production_readiness_owner_signoff.v1",
        "approved": True,
        "approved_by": approved_by,
        "approved_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "note": note,
        "readiness_evidence_status": readiness["status"],
        "external_authority_expanded": False,
        "safety_note": "This signoff records production readiness only. It does not authorize external sends, bids, uploads, payments, DSC, final pricing, final compliance, or public exposure.",
    }
    OWNER_SIGNOFF.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"status": "SIGNED", "signed": True, "signoff_path": str(OWNER_SIGNOFF)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = record_signoff(approved_by=args.approved_by, note=args.note)
    print(json.dumps(result, indent=2) if args.json else result["status"])
    return 0 if result["status"] in {"SIGNED", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
