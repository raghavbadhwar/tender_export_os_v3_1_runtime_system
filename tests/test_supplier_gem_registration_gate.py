from scripts.supplier_matcher_from_tender import gem_registration_gate


def test_gem_registration_required_for_gov() -> None:
    result = gem_registration_gate({"gem_registered": "UNKNOWN"}, workflow="GOV")
    assert result["passed"] is False


def test_gem_registration_passes_when_verified() -> None:
    result = gem_registration_gate({"gem_registered": "TRUE"}, workflow="GOV")
    assert result["passed"] is True
