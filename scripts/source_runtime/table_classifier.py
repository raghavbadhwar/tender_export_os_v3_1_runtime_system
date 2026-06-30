"""Classify extracted tender tables by likely business purpose."""

from __future__ import annotations

from typing import Any


def flatten_cells(rows: list[Any]) -> str:
    values: list[str] = []
    for row in rows[:5]:
        if isinstance(row, dict):
            values.extend(str(value) for value in row.values())
        elif isinstance(row, (list, tuple)):
            values.extend(str(value) for value in row)
        else:
            values.append(str(row))
    return " ".join(values).lower()


def classify_table(rows: list[Any]) -> str:
    text = flatten_cells(rows)
    if any(word in text for word in ["boq", "bill of quantity", "quantity", "qty", "item description", "unit rate"]):
        return "BOQ"
    if any(word in text for word in ["eligibility", "turnover", "similar work", "past experience"]):
        return "eligibility"
    if any(word in text for word in ["payment schedule", "payment terms", "milestone"]):
        return "payment schedule"
    if any(word in text for word in ["technical specification", "specification", "standards"]):
        return "technical specification"
    if any(word in text for word in ["document checklist", "documents required", "certificate", "declaration"]):
        return "document checklist"
    if any(word in text for word in ["price schedule", "financial bid", "price bid"]):
        return "price schedule"
    if any(word in text for word in ["penalty", "liquidated damages", "sla"]):
        return "penalty/SLA"
    return "unknown"
