import datetime as dt

from scripts.approval_lifecycle import classify_approval
from scripts.buyer_verification_engine import verify_buyer_stage
from scripts.export_compliance_policy_check import draft_policy_check
from scripts.score_opportunity import evaluate_trader_specific_kills
from scripts.source_runtime.blocker_assessment import assess_blockers
from scripts.supplier_matcher_from_tender import is_quote_proof
from scripts.validate_case_readiness import evaluate_case


def test_browser_edge_cases_become_blockers_or_soft_read_only_states() -> None:
    cases = {
        "captcha": "<html>captcha verification required</html>",
        "otp": "<html>enter OTP to continue</html>",
        "session": "<html>session expired, please login to view</html>",
        "payment": "<button>Pay now</button>",
        "dsc": "<html>Digital Signature Certificate prompt</html>",
    }
    for html in cases.values():
        result = assess_blockers(html)
        assert result["manual_action_required"] is True
        assert result["can_continue_read_only"] is False

    login_link = assess_blockers("<a>Login</a><div>public listing summary</div>")
    assert "LOGIN_LINK_VISIBLE" in login_link["soft_blockers"]
    assert login_link["can_continue_read_only"] is True


def test_incomplete_tender_cases_do_not_advance() -> None:
    result = evaluate_case({"case_id": "GOV-X", "workflow_type": "GOV", "status": "PRICING_READY", "opportunity_title": "X"}, [], [], [])
    assert result["next_allowed"] is False
    assert any("quote proofs" in blocker for blocker in result["blockers"])


def test_quote_listing_only_is_not_quote_proof() -> None:
    assert not is_quote_proof({"quote_proof_path": "listing.html", "quote_proof_type": "marketplace_listing", "indicative_price_only": True})


def test_export_buyer_and_compliance_edge_cases_stop() -> None:
    buyer = verify_buyer_stage({"buyer_name": "", "marketplace_only": True})
    assert buyer["ready"] is False
    assert buyer["stage"] == "RAW_LEAD"

    risky = verify_buyer_stage({"buyer_name": "Example", "destination_risk": "high"})
    assert risky["ready"] is False
    assert risky["stage"] == "RISKY"

    scomet = draft_policy_check("dual-use electronics", scomet_suspected=True)
    assert scomet["hard_stop"] is True
    assert scomet["draft_only"] is True

    prohibited = draft_policy_check("restricted item", policy="prohibited")
    assert prohibited["hard_stop"] is True


def test_trader_kill_and_approval_expiry_edge_cases() -> None:
    kill = evaluate_trader_specific_kills({"manufacturer_only_tender": "TRUE"})
    assert kill["status"] == "REJECTED"

    expired = classify_approval(
        {"approval_status": "PENDING", "created_at": "2026-06-30T00:00:00+00:00"},
        now=dt.datetime.fromisoformat("2026-07-03T00:00:00+00:00"),
        policy={"approval_timeout_policy": {"default_timeout_hours": 48}},
    )
    assert expired["expired"] is True
