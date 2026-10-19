from __future__ import annotations

from scripts.compliance_source_policy import load_policy, validate_citation, validate_policy


def test_compliance_source_policy_is_valid() -> None:
    assert validate_policy(load_policy()) == []


def test_export_scomet_requires_current_primary_official_source() -> None:
    policy = load_policy()
    good = {
        "source_kind": "scomet_list",
        "source_date": "2026-07-01",
        "primary_source": True,
        "source_url": "https://www.dgft.gov.in/",
    }
    stale = dict(good, source_date="2025-01-01")
    wrong_kind = dict(good, source_kind="public_blog")

    assert validate_citation(good, workflow_type="EXPORT", requirement_type="scomet", generated_at="2026-07-13T00:00:00+00:00", policy=policy) == []
    assert any("stale by policy" in error for error in validate_citation(stale, workflow_type="EXPORT", requirement_type="scomet", generated_at="2026-07-13T00:00:00+00:00", policy=policy))
    assert any("source_kind public_blog is not allowed" in error for error in validate_citation(wrong_kind, workflow_type="EXPORT", requirement_type="scomet", generated_at="2026-07-13T00:00:00+00:00", policy=policy))
