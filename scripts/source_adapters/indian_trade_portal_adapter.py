"""Indian Trade Portal export intelligence adapter."""

from __future__ import annotations

from scripts.source_adapters.gem_adapter import GeMAdapter


class IndianTradePortalAdapter(GeMAdapter):
    name = "indian_trade_portal"
    source_name = "Indian Trade Portal"
    source_type = "indian_government"
    workflow_type = "EXPORT"
    base_url = "https://www.indiantradeportal.in"
