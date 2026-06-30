from scripts.check_corrigenda import corrigendum_hash, detect_corrigenda


def test_corrigenda_detection_flags_changed_hash() -> None:
    items = [{"title": "Corrigendum 1", "url": "https://example.com/c1", "deadline": "2099-01-31"}]
    old_hash = corrigendum_hash([{"title": "Old"}])
    result = detect_corrigenda("GOV-1", old_hash, items)
    assert result["changed"] is True
    assert result["corrigenda_status"] == "CHANGED_REVIEW_REQUIRED"


def test_corrigenda_detection_no_change() -> None:
    items = [{"title": "Corrigendum 1", "url": "https://example.com/c1"}]
    current_hash = corrigendum_hash(items)
    result = detect_corrigenda("GOV-1", current_hash, items)
    assert result["changed"] is False
    assert result["corrigenda_count"] == 1
