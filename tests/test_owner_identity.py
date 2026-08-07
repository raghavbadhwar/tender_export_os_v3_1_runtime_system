from __future__ import annotations

import datetime as dt

from scripts.owner_identity import DEFAULT_AUDIENCE, DEFAULT_ISSUER, decision_scope, verify_owner_principal

NOW = dt.datetime(2026, 7, 12, 6, 0, tzinfo=dt.timezone.utc)
SCOPE = decision_scope(approval_id="APR-1", case_id="CASE-1", action="send_buyer_rfq_reply")


def evidence(**overrides):
    value = {
        "verified": True,
        "source": "authenticated_verifier",
        "subject": "owner-123",
        "issuer": DEFAULT_ISSUER,
        "audience": [DEFAULT_AUDIENCE],
        "expires_at": (NOW + dt.timedelta(hours=1)).isoformat(),
        "decision_scope": [SCOPE],
        "verifier": "local-test-verifier",
    }
    value.update(overrides)
    return value


def test_verified_principal_binds_exact_scope() -> None:
    result = verify_owner_principal(evidence(), expected_subject="owner-123", expected_scope=SCOPE, now=NOW)
    assert result["valid"] is True
    assert result["scope"] == SCOPE


def test_missing_or_caller_supplied_identity_fails_closed() -> None:
    missing = evidence(); missing.pop("subject")
    assert verify_owner_principal(missing, expected_subject="owner-123", expected_scope=SCOPE, now=NOW)["valid"] is False
    caller = evidence(source="caller")
    result = verify_owner_principal(caller, expected_subject="owner-123", expected_scope=SCOPE, now=NOW)
    assert result["valid"] is False
    assert "verifier" in result["reason"]


def test_expiry_issuer_audience_subject_and_scope_mismatch_fail() -> None:
    cases = [
        ("expires_at", (NOW - dt.timedelta(seconds=1)).isoformat(), "expired"),
        ("issuer", "wrong-issuer", "issuer"),
        ("audience", ["wrong-audience"], "audience"),
        ("subject", "other-owner", "subject"),
        ("decision_scope", ["other-scope"], "scope"),
    ]
    for field, value, fragment in cases:
        result = verify_owner_principal(evidence(**{field: value}), expected_subject="owner-123", expected_scope=SCOPE, now=NOW)
        assert result["valid"] is False
        assert fragment in result["reason"]


def test_verifier_is_injectable_for_deterministic_tests() -> None:
    def fake_verifier(_evidence):
        from scripts.owner_identity import AuthenticatedPrincipal
        return AuthenticatedPrincipal("owner-123", DEFAULT_ISSUER, (DEFAULT_AUDIENCE,), NOW + dt.timedelta(hours=1), (SCOPE,), "fake")

    result = verify_owner_principal({}, expected_subject="owner-123", expected_scope=SCOPE, now=NOW, verifier=fake_verifier)
    assert result["valid"] is True
