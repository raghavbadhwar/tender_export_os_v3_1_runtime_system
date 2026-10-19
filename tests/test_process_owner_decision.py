from __future__ import annotations

import datetime as dt

from scripts.process_owner_decision import verify_decision_identity
from scripts.owner_identity import DEFAULT_AUDIENCE, DEFAULT_ISSUER, decision_scope

NOW = dt.datetime(2026, 7, 12, 6, 0, tzinfo=dt.timezone.utc)
APPROVAL = {"approval_id": "APR-1", "case_id": "CASE-1", "action_approved": "send_buyer_rfq_reply"}
SCOPE = decision_scope(approval_id="APR-1", case_id="CASE-1", action="send_buyer_rfq_reply")


def principal():
    return {"verified":True,"source":"authenticated_verifier","subject":"owner-123","issuer":DEFAULT_ISSUER,"audience":[DEFAULT_AUDIENCE],"expires_at":(NOW + dt.timedelta(hours=1)).isoformat(),"decision_scope":[SCOPE],"verifier":"test-verifier"}


def test_owner_text_alone_cannot_authorize():
    result = verify_decision_identity(APPROVAL, owner="owner-123", principal_evidence={}, now=NOW)
    assert result["valid"] is False


def test_exact_approval_case_and_action_scope_is_required():
    result = verify_decision_identity(APPROVAL, owner="owner-123", principal_evidence=principal(), now=NOW)
    assert result["valid"] is True
    changed = dict(APPROVAL, action_approved="commit_final_price")
    result = verify_decision_identity(changed, owner="owner-123", principal_evidence=principal(), now=NOW)
    assert result["valid"] is False
    assert "scope" in result["reason"]
