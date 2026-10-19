from __future__ import annotations

from scripts.run_specialist_profile_canaries import (
    build_canary_specs,
    extract_json_object,
    validate_canary_task,
)


def test_build_canary_specs_covers_each_new_profile_with_safe_idempotency() -> None:
    registry = {
        "workspace": "/workspace/teos",
        "specialist_profiles": ["worker-one", "worker-two"],
        "profiles": {
            "worker-one": {"task_timeout_seconds": 120},
            "worker-two": {"task_timeout_seconds": 300},
        },
    }

    specs = build_canary_specs(registry)

    assert [spec["profile"] for spec in specs] == ["worker-one", "worker-two"]
    assert [spec["idempotency_key"] for spec in specs] == [
        "teos:profile-canary:worker-one:v1",
        "teos:profile-canary:worker-two:v1",
    ]
    assert all(spec["workspace"] == "dir:/workspace/teos" for spec in specs)
    assert all("external_actions_executed" in spec["body"] for spec in specs)
    assert all("Do not modify" in spec["body"] for spec in specs)


def test_extract_json_object_accepts_fenced_worker_result() -> None:
    payload = extract_json_object('result\n```json\n{"status":"PASS","external_actions_executed":false}\n```')

    assert payload == {"status": "PASS", "external_actions_executed": False}


def test_validate_canary_task_requires_structured_evidence_and_zero_external_actions() -> None:
    spec = {"profile": "worker-one", "evidence_path": "config/example.yaml"}
    task = {
        "status": "done",
        "result": (
            '{"status":"PASS","profile":"worker-one","task_id":"canary",'
            '"case_id":"PROFILE_CANARY","summary":"ok",'
            '"evidence":["config/example.yaml"],"artifacts":[],"unknowns":[],'
            '"approval_required":false,"external_actions_executed":false,'
            '"stop_reason":"","next_profile":"tender-export-os"}'
        ),
    }

    valid = validate_canary_task(spec, task)
    invalid = validate_canary_task(spec, task | {"result": task["result"].replace("false", "true", 1)})

    assert valid["ok"] is True
    assert invalid["ok"] is False


def test_validate_canary_task_accepts_canonical_kanban_run_metadata() -> None:
    spec = {"profile": "worker-one", "evidence_path": "config/example.yaml"}
    show_payload = {
        "task": {"id": "t_123", "status": "done", "result": None},
        "latest_summary": "Verified one local fact.",
        "runs": [
            {
                "profile": "worker-one",
                "status": "done",
                "outcome": "completed",
                "summary": "Verified one local fact.",
                "metadata": {
                    "evidence": ["config/example.yaml:4-9"],
                    "external_actions_executed": False,
                    "changed_files": [],
                },
            }
        ],
    }

    validation = validate_canary_task(spec, show_payload)

    assert validation["ok"] is True
    assert validation["payload"]["status"] == "PASS"
    assert validation["payload"]["profile"] == "worker-one"
    assert validation["payload"]["evidence"] == ["config/example.yaml:4-9"]
