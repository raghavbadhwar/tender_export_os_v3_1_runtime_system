from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.codex_task_runner import validate_task_packet
from scripts.hermes_create_codex_task import build_artifact_request


def artifact(tmp_path: Path, name: str = "source.json") -> tuple[str, str]:
    path = tmp_path / name
    path.write_text('{"verified":true}\n', encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return str(path), digest


def test_build_artifact_request_binds_hashes_paths_schema_and_claim_boundaries(tmp_path: Path, monkeypatch) -> None:
    import scripts.hermes_create_codex_task as task_module

    monkeypatch.setattr(task_module, "PROJECT_ROOT", tmp_path)
    source_path, source_hash = artifact(tmp_path)

    packet = build_artifact_request(
        case_id="GOV-CODEX-001",
        artifact_kind="spreadsheet",
        input_artifacts=[{"path": source_path, "sha256": source_hash}],
        expected_outputs=["outputs/case_reports/GOV-CODEX-001/workbook.xlsx"],
        allowed_paths=["outputs/case_reports/GOV-CODEX-001"],
        required_output_schema="config/schemas/artifact_manifest.schema.json",
        prohibited_claims=["final price", "origin", "bid submission"],
    )

    assert packet["schema_version"] == "codex_artifact_task.v1"
    assert packet["artifact_kind"] == "spreadsheet"
    assert packet["source_artifact_hashes"] == [{"path": "source.json", "sha256": source_hash}]
    assert packet["allowed_paths"] == ["outputs/case_reports/GOV-CODEX-001"]
    assert packet["external_actions_executed"] is False
    assert packet["prohibited_claims"] == ["final price", "origin", "bid submission"]
    assert len(packet["input_fingerprint"]) == 64


def test_build_artifact_request_rejects_missing_hash_and_path_escape(tmp_path: Path, monkeypatch) -> None:
    import scripts.hermes_create_codex_task as task_module

    monkeypatch.setattr(task_module, "PROJECT_ROOT", tmp_path)
    source_path, _ = artifact(tmp_path)

    with pytest.raises(ValueError, match="sha256"):
        build_artifact_request(
            "GOV-CODEX-002", "pdf", [{"path": source_path}], ["outputs/a.pdf"], ["outputs"], "schema.json", ["origin"]
        )

    with pytest.raises(ValueError, match="project root"):
        build_artifact_request(
            "GOV-CODEX-003", "pdf", [{"path": "/tmp/outside.pdf", "sha256": "a" * 64}], ["outputs/a.pdf"], ["outputs"], "schema.json", ["origin"]
        )


def test_validate_task_packet_rejects_external_execution_and_unbounded_paths() -> None:
    packet = {
        "schema_version": "codex_artifact_task.v1",
        "case_id": "EXP-CODEX-001",
        "artifact_kind": "docx",
        "workflow_type": "EXPORT",
        "source_artifact_hashes": [{"path": "inputs/source.json", "sha256": "a" * 64}],
        "expected_outputs": ["outputs/EXP-CODEX-001/draft.docx"],
        "allowed_paths": ["outputs/EXP-CODEX-001"],
        "required_output_schema": "config/schemas/artifact_manifest.schema.json",
        "prohibited_claims": ["final classification"],
        "external_actions_executed": True,
    }

    report = validate_task_packet(packet)

    assert report["status"] == "FAIL"
    assert "external_actions_executed must be false" in report["errors"]

    packet["external_actions_executed"] = False
    packet["expected_outputs"] = ["/tmp/unbounded.docx"]
    report = validate_task_packet(packet)
    assert report["status"] == "FAIL"
    assert any("project root" in error or "allowed_paths" in error for error in report["errors"])
