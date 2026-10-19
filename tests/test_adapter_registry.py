from scripts.source_adapters.adapter_registry import ADAPTERS, create_adapter


def test_registry_contains_required_adapters() -> None:
    for name in ["mock", "gem", "cppp", "epublish", "mahatenders", "punjab", "indian_trade_portal", "india_business_portal", "ungm", "supplier_directory"]:
        assert name in ADAPTERS


def test_real_adapter_can_return_structured_blocker_without_browser(monkeypatch) -> None:
    monkeypatch.setenv("DEEP_SOURCE_DISABLE_BROWSER", "1")
    adapter = create_adapter("gem", keyword="water purifier", limit=1, headless=True, run_id="TEST")
    result = adapter.scan()[0]
    assert result.blocker_status == "BROWSER_DISABLED_BY_ENV"
