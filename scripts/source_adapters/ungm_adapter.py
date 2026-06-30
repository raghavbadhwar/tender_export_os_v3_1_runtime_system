"""UNGM export/multilateral procurement adapter."""

from __future__ import annotations

from urllib.parse import quote_plus

from scripts.source_runtime.portal_adapter_base import SelectorPortalAdapter


class UNGMAdapter(SelectorPortalAdapter):
    name = "ungm"
    source_name = "UNGM"
    source_type = "multilateral"
    workflow_type = "EXPORT"
    base_url = "https://www.ungm.org/Public/Notice"
    search_path = base_url

    def build_search_url(self) -> str:
        if self.keyword:
            return f"{self.base_url}?searchText={quote_plus(self.keyword)}"
        return self.base_url

    def detect_source_specific_blockers(self, page) -> None:
        # UNGM may show registration prompts on public notices; these are not
        # submission permission. Generic hard blockers remain centralized.
        return None
