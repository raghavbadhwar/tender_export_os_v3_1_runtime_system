from scripts.check_codex_runtime_readiness import evaluate_readiness


def healthy_check(stdout: str = "") -> dict:
    return {"available": True, "returncode": 0, "timed_out": False, "stdout": stdout, "stderr": ""}


def test_preferred_runtime_requires_functional_doctor_checks() -> None:
    checks = {
        "hermes_path": healthy_check("cron kanban skills memory tools mcp gateway sessions"),
        "hermes_doctor": {"available": True, "returncode": None, "timed_out": True, "stdout": "", "stderr": ""},
        "hermes_kanban_help": healthy_check("kanban"),
        "hermes_cron_help": healthy_check("cron"),
        "codex_help": healthy_check("app-server plugin doctor mcp exec"),
        "codex_doctor": healthy_check("ok"),
        "codex_app_server_help": healthy_check("app-server"),
        "codex_plugin_inventory": {**healthy_check(), "summary": {"valid_json": True}},
    }

    ready = evaluate_readiness(checks)

    assert ready["hermes_available"] is True
    assert ready["hermes_doctor_healthy"] is False
    assert ready["preferred_runtime_ready"] is False


def test_preferred_runtime_is_true_only_when_critical_probes_are_healthy() -> None:
    checks = {
        "hermes_path": healthy_check("cron kanban skills memory tools mcp gateway sessions"),
        "hermes_doctor": healthy_check("ok"),
        "hermes_kanban_help": healthy_check("kanban"),
        "hermes_cron_help": healthy_check("cron"),
        "codex_help": healthy_check("app-server plugin doctor mcp exec"),
        "codex_doctor": healthy_check("ok"),
        "codex_app_server_help": healthy_check("app-server"),
        "codex_plugin_inventory": {**healthy_check(), "summary": {"valid_json": True}},
    }

    assert evaluate_readiness(checks)["preferred_runtime_ready"] is True
