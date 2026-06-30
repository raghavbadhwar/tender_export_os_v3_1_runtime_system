"""CPPP/eProcure deep source adapter MVP."""

from __future__ import annotations

from scripts.source_adapters.gem_adapter import GeMAdapter


class CPPPAdapter(GeMAdapter):
    name = "cppp"
    source_name = "CPPP/eProcure"
    source_type = "primary"
    workflow_type = "GOV"
    base_url = "https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata"
