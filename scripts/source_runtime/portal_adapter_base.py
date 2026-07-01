"""Selector-first source adapter base for read-only procurement portals."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus, urljoin

from scripts.source_adapters.base import DeepExtractedFields, DeepSourceOpportunity, SourceBlocked, SourceDocument, SourceOpportunity
from scripts.source_runtime.browser_manager import BrowserManager
from scripts.source_runtime.document_downloader import DocumentDownloader
from scripts.source_runtime.document_parser import parse_document
from scripts.source_runtime.evidence_store import EvidenceStore, relative, safe_name
from scripts.source_runtime.html_parser import extract_document_links
from scripts.source_runtime.selector_extractor import extract_cards, load_selector_config
from scripts.source_runtime.source_session import load_runtime_config
from scripts.source_runtime.tender_field_extractor import extract_fields

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SelectorPortalAdapter:
    name = "portal"
    source_name = "Portal"
    source_type = "primary"
    workflow_type = "GOV"
    base_url = ""
    search_path = ""

    def __init__(
        self,
        keyword: str = "",
        limit: int | None = None,
        headless: bool | None = None,
        run_id: str = "",
        evidence_only: bool = False,
    ) -> None:
        config = load_runtime_config()
        self.keyword = keyword
        self.limit = limit or config.max_results_per_source
        self.headless = config.headless_default if headless is None else headless
        self.run_id = run_id or "manual"
        self.evidence_only = evidence_only
        self.selector_config = load_selector_config(self.name)

    def build_search_url(self) -> str:
        url = self.search_path or self.base_url
        if self.keyword:
            separator = "&" if "?" in url else "?"
            return f"{url}{separator}search={quote_plus(self.keyword)}"
        return url

    def apply_filters(self, page) -> None:
        return None

    def extract_listing_cards(self, html: str, current_url: str) -> list[SourceOpportunity]:
        opportunities: list[SourceOpportunity] = []
        for card in extract_cards(html, current_url, self.selector_config)[: self.limit]:
            title = card.get("title") or f"{self.source_name} listing"
            if self.keyword and self.keyword.lower() not in (title + " " + card.get("text", "")).lower():
                continue
            opportunities.append(
                SourceOpportunity(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    workflow_type=self.workflow_type,
                    source_url=card.get("detail_link") or current_url,
                    external_reference=card.get("tender_id") or safe_name(title),
                    opportunity_title=title,
                    buyer_name=card.get("buyer", ""),
                    product_or_service=self.keyword,
                    deadline_date=card.get("deadline", ""),
                    estimated_value_inr=card.get("value", ""),
                    blocker_status="",
                    citations=[card.get("detail_link") or current_url],
                    notes="Selector-first public listing extraction; verify documents before action.",
                )
            )
        return opportunities[: self.limit]

    def open_detail(self, page, opportunity: SourceOpportunity) -> None:
        page.goto(opportunity.source_url, wait_until="domcontentloaded", timeout=60000)

    def extract_detail_fields(self, opportunity: SourceOpportunity, parsed_results: list[dict]) -> DeepExtractedFields:
        return extract_fields(opportunity, parsed_results, self.source_name)

    def extract_document_links(self, html: str, current_url: str) -> list[str]:
        selector_links = []
        for card in extract_cards(html, current_url, self.selector_config):
            for key in ["document_link", "boq_link", "corrigendum_link"]:
                if card.get(key):
                    selector_links.append(card[key])
        return list(dict.fromkeys(selector_links + extract_document_links(html, current_url)))

    def normalize_dates(self, value: str) -> str:
        return value

    def detect_source_specific_blockers(self, page) -> None:
        return None

    def _blocked_opportunity(self, reason: str, details: str = "") -> SourceOpportunity:
        return SourceOpportunity(
            source_name=self.source_name,
            source_type=self.source_type,
            workflow_type=self.workflow_type,
            source_url=self.base_url,
            external_reference=f"{self.name.upper()}-BLOCKED",
            opportunity_title=f"{self.source_name} source blocked: {reason}",
            blocker_status=reason,
            citations=[self.base_url],
            notes=details,
        )

    def scan(self) -> list[SourceOpportunity]:
        if os.environ.get("DEEP_SOURCE_DISABLE_BROWSER") == "1":
            return [self._blocked_opportunity("BROWSER_DISABLED_BY_ENV")]
        browser = BrowserManager(self.name)
        try:
            context = browser.open_context(self.name, headless=self.headless)
            page = context.new_page()
            page.goto(self.build_search_url(), wait_until="domcontentloaded", timeout=60000)
            self.apply_filters(page)
            self.detect_source_specific_blockers(page)
            browser.detect_blockers(page, self.source_name)
            html = page.content()
            return self.extract_listing_cards(html, page.url) or [self._blocked_opportunity("NO_PUBLIC_LISTINGS_DETECTED")]
        except SourceBlocked as exc:
            return [self._blocked_opportunity(exc.reason, exc.details)]
        except Exception as exc:
            return [self._blocked_opportunity("SOURCE_SCAN_ERROR", str(exc))]
        finally:
            browser.close_context()

    def deep_read(self, opportunity: SourceOpportunity) -> DeepSourceOpportunity:
        temp_id = safe_name(opportunity.external_reference or f"{self.name.upper()}-CANDIDATE")
        evidence = EvidenceStore(self.workflow_type, temp_id, self.source_name, opportunity.source_url, self.run_id)
        documents: list[SourceDocument] = []
        parsed_results: list[dict] = []
        screenshots: list[str] = []
        raw_html_paths: list[str] = []
        if os.environ.get("DEEP_SOURCE_DISABLE_BROWSER") == "1":
            evidence.add_blocker("BROWSER_DISABLED_BY_ENV", opportunity.source_url)
            fields = self.extract_detail_fields(opportunity, [])
            evidence.write_extracted_json("deep_extracted_fields.json", fields.to_dict())
            return DeepSourceOpportunity(opportunity, fields, documents, screenshots, raw_html_paths, relative(evidence.base_dir), "BLOCKED", "BROWSER_DISABLED_BY_ENV", evidence.manifest["citations"])
        browser = BrowserManager(self.name, evidence=evidence)
        try:
            context = browser.open_context(self.name, headless=self.headless)
            page = context.new_page()
            self.open_detail(page, opportunity)
            self.detect_source_specific_blockers(page)
            browser.detect_blockers(page, self.source_name)
            screenshots.append(browser.save_screenshot(page, temp_id, "detail_page", evidence))
            raw_html_paths.append(browser.save_raw_html(page, temp_id, "detail_page", evidence))
            html_path = PROJECT_ROOT / raw_html_paths[-1]
            parsed_results.append(parse_document(html_path, evidence).to_dict())
            downloader = DocumentDownloader(evidence)
            for link in self.extract_document_links(page.content(), page.url)[:20]:
                document_url = urljoin(page.url, link)
                document = downloader.download_from_browser_context(page, document_url)
                if not document:
                    document = downloader.download_url(document_url)
                if not document:
                    continue
                result = parse_document(PROJECT_ROOT / document.local_path, evidence)
                document.parse_status = result.parse_status
                document.page_count = result.page_count
                document.extracted_text_path = result.extracted_text_path
                document.extraction_notes = result.notes
                documents.append(document)
                parsed_results.append(result.to_dict())
            fields = self.extract_detail_fields(opportunity, parsed_results)
            evidence.write_extracted_json("deep_extracted_fields.json", fields.to_dict())
            return DeepSourceOpportunity(opportunity, fields, documents, screenshots, raw_html_paths, relative(evidence.base_dir), "COMPLETED", "", evidence.manifest["citations"])
        except SourceBlocked as exc:
            evidence.add_blocker(exc.reason, opportunity.source_url, exc.details)
            fields = self.extract_detail_fields(opportunity, parsed_results)
            evidence.write_extracted_json("deep_extracted_fields.json", fields.to_dict())
            return DeepSourceOpportunity(opportunity, fields, documents, screenshots, raw_html_paths, relative(evidence.base_dir), "BLOCKED", exc.reason, evidence.manifest["citations"])
        except Exception as exc:
            evidence.add_blocker("DEEP_READ_ERROR", opportunity.source_url, str(exc))
            fields = self.extract_detail_fields(opportunity, parsed_results)
            evidence.write_extracted_json("deep_extracted_fields.json", fields.to_dict())
            return DeepSourceOpportunity(opportunity, fields, documents, screenshots, raw_html_paths, relative(evidence.base_dir), "ERROR", "DEEP_READ_ERROR", evidence.manifest["citations"])
        finally:
            browser.close_context()
