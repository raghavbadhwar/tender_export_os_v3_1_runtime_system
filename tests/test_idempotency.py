from scripts.lib.idempotency import (
    approval_card_key,
    case_create_key,
    chatgpt_return_key,
    corrigendum_key,
    source_adapter_key,
    supplier_request_key,
)


def test_idempotency_keys_are_stable_and_normalized() -> None:
    assert source_adapter_key(" GeM ", " GEM/2026/B/1 ", "2026-07-01") == "source_adapter:gem:gem/2026/b/1:2026-07-01"
    assert case_create_key("CPPP", "https://example.com/tender/1") == "case_create:cppp:https://example.com/tender/1"
    assert approval_card_key("GOV-1", "Submit Bid") == "approval_card:gov-1:submit bid"
    assert supplier_request_key("GOV-1", "SUP-1", "quote") == "supplier_request:gov-1:sup-1:quote"
    assert chatgpt_return_key("abc123") == "chatgpt_return:abc123"
    assert corrigendum_key("GOV-1", "def456") == "corrigendum:gov-1:def456"
