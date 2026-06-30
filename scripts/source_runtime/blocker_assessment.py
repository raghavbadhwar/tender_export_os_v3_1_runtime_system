"""Hard/soft blocker assessment for read-only browser workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

HARD_BLOCKERS = {
    "CAPTCHA": r"captcha|recaptcha|hcaptcha|verify\s+you\s+are\s+human",
    "OTP": r"\botp\b|one[-\s]?time\s+password|phone\s+verification",
    "MFA": r"\bmfa\b|multi[-\s]?factor|two[-\s]?factor|2fa",
    "LOGIN_WALL": r"login\s+required|session\s+expired|please\s+login\s+to\s+(?:continue|view|download)",
    "DSC_PROMPT": r"\bDSC\b|digital\s*signature|certificate\s*prompt|signature\s*prompt",
    "PAYMENT_PAGE": r"payment\s+required|pay\s+now|make\s+payment",
    "ACCESS_DENIED": r"access denied|forbidden|unauthorized|not authorized|blocked",
}

SOFT_BLOCKERS = {
    "LOGIN_LINK_VISIBLE": r"\b(?:login|log in|sign in)\b",
    "SUBSCRIPTION_TEXT": r"subscription|subscribe|member login",
    "NEWSLETTER_POPUP": r"newsletter|subscribe to updates",
    "COOKIE_BANNER": r"cookie consent|accept cookies|we use cookies",
}


@dataclass
class BlockerAssessment:
    hard_blockers: list[str]
    soft_blockers: list[str]
    forbidden_action_elements: list[str]
    can_continue_read_only: bool
    manual_action_required: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def page_text(page_or_html: Any) -> str:
    if isinstance(page_or_html, str):
        return page_or_html
    parts = []
    for attr in ["title", "url", "content"]:
        try:
            value = getattr(page_or_html, attr)
            parts.append(value() if callable(value) else str(value))
        except Exception:
            continue
    return "\n".join(parts)


def detect_forbidden_action_elements(html: str) -> list[str]:
    from scripts.source_runtime.forbidden_action_guard import detect_forbidden_actions

    return [item["label"] for item in detect_forbidden_actions(html)]


def assess_blockers(page_or_html: Any) -> dict[str, Any]:
    text = page_text(page_or_html)
    if BeautifulSoup is not None and "<" in text:
        soup = BeautifulSoup(text, "html.parser")
        visible_text = " ".join(soup.get_text(" ", strip=True).split())
    else:
        visible_text = " ".join(re.sub(r"<[^>]+>", " ", text).split()) if "<" in text else text
    hard = [label for label, pattern in HARD_BLOCKERS.items() if re.search(pattern, visible_text, flags=re.I)]
    soft = [label for label, pattern in SOFT_BLOCKERS.items() if re.search(pattern, visible_text, flags=re.I)]
    forbidden = detect_forbidden_action_elements(text)
    assessment = BlockerAssessment(
        hard_blockers=hard,
        soft_blockers=soft,
        forbidden_action_elements=forbidden,
        can_continue_read_only=not hard,
        manual_action_required=bool(hard),
    )
    return assessment.to_dict()
