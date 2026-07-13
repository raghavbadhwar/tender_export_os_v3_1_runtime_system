from __future__ import annotations

from pathlib import Path

from scripts.evaluate_learning_proposal import evaluate_payload


def _payload(root: Path) -> dict:
    rollback = root / "rollback.json"
    rollback.write_text("{}", encoding="utf-8")
    return {
        "proposal_id": "LP-1",
        "profile": "radar-agent",
        "scenario_id": "SCN-1",
        "scenario_type": "INTEGRATION",
        "rollback_artifact_path": str(rollback),
        "policy_checks": [{"name": "approval_gate", "status": "PASS"}],
        "current_metrics": {"latency_ms": 1000, "cost_usd": 0.1},
        "candidate_metrics": {"latency_ms": 1100, "cost_usd": 0.12},
        "repeated_runs": [
            {"run_id": "RUN-1", "expected_result": "PASS", "actual_result": "PASS", "evidence_completeness_pct": 95, "score": 90},
            {"run_id": "RUN-2", "expected_result": "PASS", "actual_result": "PASS", "evidence_completeness_pct": 95, "score": 91},
            {"run_id": "RUN-3", "expected_result": "PASS", "actual_result": "PASS", "evidence_completeness_pct": 95, "score": 92},
        ],
    }


def test_learning_proposal_evaluation_passes_three_repeated_runs(tmp_path: Path) -> None:
    report = evaluate_payload(_payload(tmp_path), root=tmp_path)

    assert report["evaluation_status"] == "PASS"
    assert len(report["rows"]) == 3
    assert all(row["status"] == "PASS" for row in report["rows"])


def test_learning_proposal_evaluation_fails_policy_or_cost_latency(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    payload["policy_checks"] = [{"name": "approval_gate", "status": "FAIL"}]
    payload["candidate_metrics"] = {"latency_ms": 3000, "cost_usd": 0.5}

    report = evaluate_payload(payload, root=tmp_path)

    assert report["evaluation_status"] == "FAIL"
    assert any("policy checks" in error for error in report["errors"])
    assert any("latency" in error for error in report["errors"])
    assert any("cost" in error for error in report["errors"])
