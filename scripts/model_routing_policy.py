#!/usr/bin/env python3
"""Select and validate safe internal model routes without invoking a model."""

from __future__ import annotations

from typing import Any


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    routes = policy.get("routes") if isinstance(policy.get("routes"), dict) else {}
    default_route = str(policy.get("default_route") or "")
    if default_route not in routes:
        errors.append("default_route must reference a configured route")
    for name, route in routes.items():
        if not isinstance(route, dict):
            errors.append(f"route {name} must be a mapping")
            continue
        if not route.get("provider") or not route.get("model"):
            errors.append(f"route {name} requires provider and model")
        if route.get("external_actions_executed") is not False:
            errors.append(f"route {name} must not execute external actions")
        if not isinstance(route.get("allowed_work_types"), list) or not route.get("allowed_work_types"):
            errors.append(f"route {name} requires allowed_work_types")
        if route.get("risk_tier") not in {"low", "high"}:
            errors.append(f"route {name} risk_tier must be low or high")
    fallback = policy.get("fallback") if isinstance(policy.get("fallback"), dict) else {}
    same = fallback.get("same_provider") if isinstance(fallback.get("same_provider"), dict) else {}
    if same.get("enabled") is not True or same.get("provider") != "openai-codex" or same.get("model") != "gpt-5.5":
        errors.append("same-provider fallback must preserve openai-codex gpt-5.5")
    if same.get("external_actions_executed") is not False:
        errors.append("same-provider fallback must not execute external actions")
    cross = fallback.get("cross_provider") if isinstance(fallback.get("cross_provider"), dict) else {}
    if cross.get("enabled") is True:
        errors.append("cross-provider fallback requires a separate owner-approved policy and is disabled")
    safety = policy.get("safety") if isinstance(policy.get("safety"), dict) else {}
    if safety.get("external_actions_executed") is not False or safety.get("no_route_grants_external_authority") is not True:
        errors.append("model routes must not grant external authority")
    return errors


def choose_route(
    policy: dict[str, Any],
    *,
    work_type: str,
    risk_tier: str,
    requested_route: str | None = None,
) -> dict[str, Any]:
    errors = validate_policy(policy)
    if errors:
        raise ValueError("invalid model routing policy: " + "; ".join(errors))
    routes = policy["routes"]
    route_name = requested_route
    if route_name is None:
        candidates = [
            (name, route) for name, route in routes.items()
            if work_type in route.get("allowed_work_types", []) and route.get("risk_tier") == risk_tier
        ]
        route_name = candidates[0][0] if candidates else str(policy["default_route"])
    if route_name not in routes:
        raise ValueError(f"unknown model route: {route_name}")
    route = routes[route_name]
    if work_type not in route.get("allowed_work_types", []):
        raise ValueError(f"work type {work_type} is not allowed on route {route_name}")
    if risk_tier == "high" and route.get("risk_tier") != "high":
        raise ValueError("high-risk work cannot use a low-risk route")
    if route.get("external_actions_executed") is not False:
        raise ValueError("selected route cannot execute external actions")
    return {"route": route_name, **route}
