"""ePublish safe adapter placeholder."""

from __future__ import annotations

from scripts.source_adapters.gem_adapter import GeMAdapter


class EPublishAdapter(GeMAdapter):
    name = "epublish"
    source_name = "ePublishing"
    source_type = "primary"
    workflow_type = "GOV"
    base_url = "https://eprocure.gov.in/epublish/app"
