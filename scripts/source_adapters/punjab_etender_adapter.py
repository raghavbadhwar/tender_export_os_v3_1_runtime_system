"""Punjab eTender safe adapter placeholder."""

from __future__ import annotations

from scripts.source_adapters.gem_adapter import GeMAdapter


class PunjabETenderAdapter(GeMAdapter):
    name = "punjab"
    source_name = "Punjab eTender"
    source_type = "state"
    workflow_type = "GOV"
    base_url = "https://eproc.punjab.gov.in/nicgep/app"
