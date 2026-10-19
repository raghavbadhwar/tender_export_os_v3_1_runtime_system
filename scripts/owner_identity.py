#!/usr/bin/env python3
"""Injectable authenticated-principal contract for owner decisions.

This module verifies a local evidence envelope produced by an authenticated
verifier.  It does not contact an identity provider and never treats a caller's
owner string as proof of identity.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

DEFAULT_ISSUER = "tender-export-owner-verifier-v1"
DEFAULT_AUDIENCE = "tender-export-owner-decision"


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    issuer: str
    audience: tuple[str, ...]
    expires_at: dt.datetime
    scopes: tuple[str, ...]
    verifier: str


class PrincipalVerifier(Protocol):
    def __call__(self, evidence: Mapping[str, Any]) -> AuthenticatedPrincipal: ...


def parse_expiry(value: object) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def decision_scope(*, approval_id: str, case_id: str, action: str) -> str:
    values = (approval_id.strip(), case_id.strip(), action.strip())
    if not all(values):
        raise ValueError("approval_id, case_id, and action are required for decision scope")
    return f"approval:{values[0]}:case:{values[1]}:action:{values[2]}"


def _default_verifier(evidence: Mapping[str, Any]) -> AuthenticatedPrincipal:
    if evidence.get("verified") is not True:
        raise ValueError("principal evidence is not marked verified")
    if evidence.get("source") != "authenticated_verifier":
        raise ValueError("principal evidence must come from the authenticated verifier")
    subject = evidence.get("subject")
    issuer = evidence.get("issuer")
    raw_audience = evidence.get("audience")
    raw_scopes = evidence.get("decision_scope")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("verified principal subject is missing")
    if not isinstance(issuer, str) or not issuer.strip():
        raise ValueError("verified principal issuer is missing")
    audience = (raw_audience,) if isinstance(raw_audience, str) else tuple(raw_audience or ())
    scopes = (raw_scopes,) if isinstance(raw_scopes, str) else tuple(raw_scopes or ())
    if not audience or not all(isinstance(value, str) and value.strip() for value in audience):
        raise ValueError("verified principal audience is missing")
    if not scopes or not all(isinstance(value, str) and value.strip() for value in scopes):
        raise ValueError("verified decision scope is missing")
    expires_at = parse_expiry(evidence.get("expires_at"))
    if expires_at is None:
        raise ValueError("verified principal expiry is missing or invalid")
    verifier = evidence.get("verifier")
    if not isinstance(verifier, str) or not verifier.strip():
        raise ValueError("principal verifier identity is missing")
    return AuthenticatedPrincipal(subject.strip(), issuer.strip(), tuple(audience), expires_at, tuple(scopes), verifier.strip())


def verify_owner_principal(
    evidence: Mapping[str, Any],
    *,
    expected_subject: str,
    expected_scope: str,
    now: dt.datetime,
    expected_issuer: str = DEFAULT_ISSUER,
    expected_audience: str = DEFAULT_AUDIENCE,
    verifier: PrincipalVerifier | None = None,
) -> dict[str, Any]:
    """Verify a principal against issuer, audience, expiry, subject, and scope."""
    failures: list[str] = []
    try:
        principal = (verifier or _default_verifier)(evidence)
    except (TypeError, ValueError, KeyError) as exc:
        return {"valid": False, "reason": str(exc), "subject": "", "issuer": "", "audience": [], "scope": expected_scope}
    current = now.astimezone(dt.timezone.utc) if now.tzinfo else now.replace(tzinfo=dt.timezone.utc)
    if principal.subject != expected_subject.strip(): failures.append("authenticated subject mismatch")
    if principal.issuer != expected_issuer: failures.append("authenticated issuer mismatch")
    if expected_audience not in principal.audience: failures.append("authenticated audience mismatch")
    if expected_scope not in principal.scopes: failures.append("decision scope mismatch")
    if current >= principal.expires_at: failures.append("authenticated principal is expired")
    return {"valid": not failures, "reason": "; ".join(failures) if failures else "authenticated principal verified", "subject": principal.subject, "issuer": principal.issuer, "audience": list(principal.audience), "scope": expected_scope, "expires_at": principal.expires_at.isoformat(), "verifier": principal.verifier}


def load_principal_evidence(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("principal evidence must be a JSON object")
    return value
