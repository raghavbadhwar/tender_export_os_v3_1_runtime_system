from scripts.source_runtime.blocker_assessment import assess_blockers


def test_login_link_is_soft_blocker_only() -> None:
    html = '<html><a href="/login">Login</a><main>Public tender listing</main></html>'
    result = assess_blockers(html)
    assert result["hard_blockers"] == []
    assert "LOGIN_LINK_VISIBLE" in result["soft_blockers"]
    assert result["can_continue_read_only"] is True


def test_captcha_is_hard_blocker() -> None:
    html = "<html><body>Please solve CAPTCHA to continue</body></html>"
    result = assess_blockers(html)
    assert "CAPTCHA" in result["hard_blockers"]
    assert result["manual_action_required"] is True
