"""Maharashtra eTender safe adapter placeholder."""

from __future__ import annotations

from scripts.source_adapters.gem_adapter import GeMAdapter


class MahaTendersAdapter(GeMAdapter):
    name = "mahatenders"
    source_name = "MahaTenders"
    source_type = "state"
    workflow_type = "GOV"
    base_url = "https://mahatenders.gov.in/nicgep/app"
