"""Draft-only export policy checks."""

from __future__ import annotations


def draft_policy_check(product: str, scomet_suspected: bool = False, policy: str = "Free") -> dict:
    if scomet_suspected:
        return {"policy": "SCOMET_REVIEW", "hard_stop": True, "draft_only": True}
    if policy.lower() in {"restricted", "prohibited"}:
        return {"policy": policy.title(), "hard_stop": policy.lower() == "prohibited", "draft_only": True}
    return {"policy": "Free", "hard_stop": False, "draft_only": True, "product": product}
