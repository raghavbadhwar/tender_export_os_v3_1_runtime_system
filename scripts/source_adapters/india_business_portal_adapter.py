"""India Business Portal export buyer adapter."""

from __future__ import annotations

from scripts.source_adapters.gem_adapter import GeMAdapter


class IndiaBusinessPortalAdapter(GeMAdapter):
    name = "india_business_portal"
    source_name = "India Business Portal"
    source_type = "indian_government"
    workflow_type = "EXPORT"
    base_url = "https://www.indiabusinessportal.gov.in"
