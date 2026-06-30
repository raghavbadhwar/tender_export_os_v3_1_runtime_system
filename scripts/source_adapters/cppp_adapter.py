"""CPPP/eProcure source-specific adapter."""

from __future__ import annotations

from scripts.source_runtime.portal_adapter_base import SelectorPortalAdapter


class CPPPAdapter(SelectorPortalAdapter):
    name = "cppp"
    source_name = "CPPP/eProcure"
    source_type = "primary"
    workflow_type = "GOV"
    base_url = "https://eprocure.gov.in/cppp/latestactivetendersnew/cpppdata"
    search_path = base_url

    def build_search_url(self) -> str:
        return self.search_path

    def detect_source_specific_blockers(self, page) -> None:
        # CPPP public pages can show login links while still allowing read-only
        # listing/detail access. Hard blockers are handled by BrowserManager.
        return None
