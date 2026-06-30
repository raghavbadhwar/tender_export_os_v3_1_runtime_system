from scripts.approval_lifecycle import validate_execution_transition


def test_execution_lifecycle_allows_forward_tracking_steps() -> None:
    result = validate_execution_transition("AWAITING_EXECUTION", "SUPPLIER_RESPONSE_PENDING")
    assert result["allowed"] is True


def test_execution_lifecycle_blocks_reopening_completed_state() -> None:
    result = validate_execution_transition("COMPLETED", "SUPPLIER_RESPONSE_PENDING")
    assert result["allowed"] is False
