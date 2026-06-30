"""UNGM export/multilateral procurement adapter."""

from __future__ import annotations

from scripts.source_adapters.gem_adapter import GeMAdapter


class UNGMAdapter(GeMAdapter):
    name = "ungm"
    source_name = "UNGM"
    source_type = "multilateral"
    workflow_type = "EXPORT"
    base_url = "https://www.ungm.org/Public/Notice"
