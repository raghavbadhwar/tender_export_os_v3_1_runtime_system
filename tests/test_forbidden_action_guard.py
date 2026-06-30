import pytest

from scripts.source_runtime.forbidden_action_guard import assert_no_forbidden_action, detect_forbidden_actions


def test_detect_forbidden_action_buttons() -> None:
    html = '<button>Final Submit Bid</button><a>Download NIT</a>'
    hits = detect_forbidden_actions(html)
    assert hits
    assert "Final Submit Bid" in hits[0]["label"]


def test_assert_no_forbidden_action_raises() -> None:
    with pytest.raises(ValueError):
        assert_no_forbidden_action("<a>Pay EMD</a>")
