from scripts.create_cases_from_deep_source_results import should_skip


def test_case_creation_uses_configurable_confidence_threshold() -> None:
    result = {"extracted": {"confidence_score": 60}}
    skip, reason = should_skip(result, respect_deadline=False, min_confidence_score=70)
    assert skip is True
    assert "low confidence" in reason


def test_case_creation_accepts_threshold_match() -> None:
    result = {"extracted": {"confidence_score": 70}}
    skip, reason = should_skip(result, respect_deadline=False, min_confidence_score=70)
    assert skip is False
    assert reason == ""
