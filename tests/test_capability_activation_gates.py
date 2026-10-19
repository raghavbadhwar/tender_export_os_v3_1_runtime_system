from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_high_risk_optional_capabilities_stay_disabled_until_all_measured_gates_pass() -> None:
    manifest = yaml.safe_load((ROOT / "config/hermes_profile_capabilities.yaml").read_text(encoding="utf-8"))
    policy = manifest["restricted_capability_activation"]

    assert policy["default_status"] == "DISABLED"
    assert set(policy["capabilities"]) == {
        "paid_extraction_services",
        "cloud_browser_services",
        "residential_proxy_services",
        "general_third_party_mcp_services",
    }
    required = {
        "measured_capture_failure_rate",
        "operator_hours_lost",
        "monthly_volume",
        "privacy_review",
        "owner_approved_budget",
    }
    for name, capability in policy["capabilities"].items():
        assert capability["status"] == "DISABLED", name
        assert required <= set(capability["activation_requires"])
        assert capability["activation_requires"]["owner_approved_budget"]["required"] is True
        assert capability["activation_requires"]["privacy_review"]["required"] is True
