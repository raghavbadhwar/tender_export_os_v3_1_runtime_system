from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import reconcile_execution_receipts as reconciler


def write_receipt(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def approval() -> dict[str, dict[str, str]]:
    return {"APR-TEST": {"approval_id": "APR-TEST", "case_id": "EXP-TEST-001"}}


def sent_receipt() -> dict[str, object]:
    return {
        "receipt_id": "EXE-TEST",
        "approval_id": "APR-TEST",
        "case_id": "EXP-TEST-001",
        "gmail_result": {"status": "sent"},
    }


def test_parse_receipt_rejects_path_outside_governed_stores(tmp_path: Path) -> None:
    receipt_path = tmp_path / "staged-receipt.json"
    write_receipt(receipt_path, sent_receipt())

    with pytest.raises(ValueError, match="approved execution-receipt store"):
        reconciler.parse_receipt(receipt_path, approval())


def test_parse_receipt_rejects_contradictory_sent_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt_path = tmp_path / "EXE-TEST.json"
    payload = sent_receipt()
    payload["external_action_sent"] = False
    write_receipt(receipt_path, payload)
    monkeypatch.setattr(reconciler, "relative_to_root", lambda _: "receipts/executions/EXE-TEST.json")

    with pytest.raises(ValueError, match="contradicts external_action_sent"):
        reconciler.parse_receipt(receipt_path, approval(), allowed_roots=(tmp_path,))
