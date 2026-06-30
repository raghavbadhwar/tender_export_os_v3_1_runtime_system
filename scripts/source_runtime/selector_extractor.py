"""Selector-first extraction helpers for public portal fixtures and pages."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SELECTOR_DIR = PROJECT_ROOT / "config" / "source_selectors"


def load_selector_config(slug: str) -> dict[str, Any]:
    path = SELECTOR_DIR / f"{slug}.yaml"
    if not path.exists() or yaml is None:
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def first_text(root: Any, selectors: list[str]) -> str:
    for selector in selectors:
        if not hasattr(root, "select_one"):
            return ""
        node = root.select_one(selector)
        if node:
            text = " ".join(node.get_text(" ", strip=True).split())
            if text:
                return text
    return ""


def first_attr(root: Any, selectors: list[str], attr: str, base_url: str = "") -> str:
    for selector in selectors:
        if not hasattr(root, "select_one"):
            return ""
        node = root.select_one(selector)
        if node and node.get(attr):
            value = str(node.get(attr)).strip()
            return urljoin(base_url, value) if base_url else value
    return ""


def field_selectors(config: dict[str, Any], field: str) -> list[str]:
    fields = config.get("fields", {}) if isinstance(config, dict) else {}
    value = fields.get(field, [])
    if isinstance(value, str):
        return [value]
    return list(value or [])


def extract_cards(html: str, base_url: str, config: dict[str, Any]) -> list[dict[str, str]]:
    if BeautifulSoup is None:
        text = " ".join(re.sub(r"<[^>]+>", " ", html or "").split())
        title = infer_title(text)
        return [{
            "title": title,
            "tender_id": infer_reference(text) or "LISTING-1",
            "buyer": "",
            "deadline": "",
            "value": "",
            "emd": "",
            "detail_link": base_url,
            "document_link": "",
            "corrigendum_link": "",
            "boq_link": "",
            "text": text,
        }] if text or base_url else []
    soup = BeautifulSoup(html, "html.parser")
    card_selectors = config.get("listing_card", [".tender-card", ".notice-card", "tr", "li"])
    if isinstance(card_selectors, str):
        card_selectors = [card_selectors]
    cards = []
    for selector in card_selectors:
        cards = soup.select(selector)
        if cards:
            break
    if not cards:
        cards = [soup]

    results: list[dict[str, str]] = []
    for index, card in enumerate(cards, start=1):
        title = first_text(card, field_selectors(config, "title"))
        tender_id = first_text(card, field_selectors(config, "tender_id"))
        buyer = first_text(card, field_selectors(config, "buyer"))
        deadline = first_text(card, field_selectors(config, "deadline"))
        value = first_text(card, field_selectors(config, "value"))
        emd = first_text(card, field_selectors(config, "emd"))
        detail_link = first_attr(card, field_selectors(config, "detail_link"), "href", base_url)
        document_link = first_attr(card, field_selectors(config, "document_link"), "href", base_url)
        corrigendum_link = first_attr(card, field_selectors(config, "corrigendum_link"), "href", base_url)
        boq_link = first_attr(card, field_selectors(config, "boq_link"), "href", base_url)
        text = " ".join(card.get_text(" ", strip=True).split())
        if not title:
            title = infer_title(text)
        if not tender_id:
            tender_id = infer_reference(text) or f"LISTING-{index}"
        if not any([title, buyer, deadline, detail_link, document_link]):
            continue
        results.append(
            {
                "title": title,
                "tender_id": tender_id,
                "buyer": buyer,
                "deadline": deadline,
                "value": value,
                "emd": emd,
                "detail_link": detail_link or base_url,
                "document_link": document_link,
                "corrigendum_link": corrigendum_link,
                "boq_link": boq_link,
                "text": text,
            }
        )
    return results


def infer_reference(text: str) -> str:
    patterns = [
        r"GEM/\d{4}/B/\d+",
        r"\b[A-Z]{2,10}/\d{4}[-/][A-Z0-9/-]+",
        r"\b(?:Tender|Notice|Bid)\s*(?:ID|No|Number)?[:\-\s]+([A-Z0-9/-]{4,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    return ""


def infer_title(text: str) -> str:
    for part in re.split(r"\s{2,}|\n", text):
        value = part.strip()
        if len(value) > 12 and not re.fullmatch(r"[A-Z0-9/ -]+", value):
            return value[:180]
    return text[:120]
