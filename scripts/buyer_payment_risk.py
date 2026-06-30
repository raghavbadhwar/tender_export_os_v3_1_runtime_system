"""Draft buyer payment-risk scoring."""

from __future__ import annotations


def payment_risk(payment_terms: str, destination_risk: str = "") -> dict:
    text = (payment_terms or "").lower()
    score = 50
    flags = []
    if "lc" in text or "letter of credit" in text or "advance" in text:
        score += 25
    if "open account" in text or "da" in text or "dp" in text:
        score -= 25
        flags.append("risky_payment_terms")
    if destination_risk == "high":
        score -= 30
        flags.append("high_destination_risk")
    return {"payment_risk_score": max(0, min(100, score)), "flags": flags}
