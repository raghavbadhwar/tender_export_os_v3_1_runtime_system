"""GeM BidPlus deep source adapter MVP."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote_plus, urljoin

try:
    from scripts.source_adapters.base import DeepSourceOpportunity, SourceBlocked, SourceDocument, SourceOpportunity
except ModuleNotFoundError:  # pragma: no cover
    from base import DeepSourceOpportunity, SourceBlocked, SourceDocument, SourceOpportunity  # type: ignore

from scripts.source_runtime.browser_manager import BrowserManager
from scripts.source_runtime.document_downloader import DocumentDownloader
from scripts.source_runtime.document_parser import parse_document
from scripts.source_runtime.evidence_store import EvidenceStore, relative, safe_name
from scripts.source_runtime.html_parser import extract_document_links, html_to_text
from scripts.source_runtime.source_session import load_runtime_config
from scripts.source_runtime.tender_field_extractor import extract_fields

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class GeMAdapter:
    name = "gem"
    source_name = "GeM"
    source_type = "primary"
    workflow_type = "GOV"
    base_url = "https://bidplus.gem.gov.in/all-bids"

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

    def _extract_listing_opportunities(self, html: str, current_url: str) -> list[SourceOpportunity]:
        text = html_to_text(html)
        links = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
        bid_links = []
        for href in links:
            if "showbidDocument" in href or "bid" in href.lower():
                bid_links.append(urljoin(current_url, href))
        seen: set[str] = set()
        unique_links: list[str] = []
        for link in bid_links:
            if link not in seen:
                unique_links.append(link)
                seen.add(link)

        opportunities: list[SourceOpportunity] = []
        chunks = [chunk for chunk in re.split(r"\n{2,}|(?=GEM/\d{4}/B/)", text) if chunk.strip()]
        for idx, chunk in enumerate(chunks):
            if self.keyword and self.keyword.lower() not in chunk.lower() and idx > 0:
                continue
            bid = re.search(r"GEM/\d{4}/B/\d+", chunk, flags=re.I)
            title = ""
            for line in chunk.splitlines():
                if len(line.strip()) > 20 and "GEM/" not in line:
                    title = line.strip()
                    break
            source_url = unique_links[min(len(opportunities), len(unique_links) - 1)] if unique_links else current_url
            opportunities.append(
                SourceOpportunity(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    workflow_type=self.workflow_type,
                    source_url=source_url,
                    external_reference=bid.group(0) if bid else f"GEM-LISTING-{idx + 1}",
                    opportunity_title=title or f"GeM listing match {idx + 1}",
                    product_or_service=self.keyword,
                    blocker_status="",
                    citations=[source_url],
                    notes="Listing extracted from GeM page text; verify detail evidence before action.",
                )
            )
            if len(opportunities) >= self.limit:
                break
        if not opportunities and text:
            opportunities.append(
                SourceOpportunity(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    workflow_type=self.workflow_type,
                    source_url=current_url,
                    external_reference="GEM-LISTING-UNSTRUCTURED",
                    opportunity_title=(self.keyword or "GeM listing page reached"),
                    product_or_service=self.keyword,
                    citations=[current_url],
                    notes="Page reached but no structured bid cards were detected by rules.",
                )
            )
        return opportunities[: self.limit]

    def scan(self) -> list[SourceOpportunity]:
        if os.environ.get("DEEP_SOURCE_DISABLE_BROWSER") == "1":
            return [self._blocked_opportunity("BROWSER_DISABLED_BY_ENV")]
        url = self.base_url
        if self.keyword:
            url = f"{url}?search={quote_plus(self.keyword)}"
        browser = BrowserManager(self.name)
        try:
            context = browser.open_context(self.name, headless=self.headless)
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            browser.detect_blockers(page, self.source_name)
            try:
                page.wait_for_timeout(1500)
            except Exception:
                pass
            html = page.content()
            return self._extract_listing_opportunities(html, page.url)
        except SourceBlocked as exc:
            return [self._blocked_opportunity(exc.reason, exc.details)]
        except Exception as exc:
            return [self._blocked_opportunity("SOURCE_SCAN_ERROR", str(exc))]
        finally:
            browser.close_context()

    def deep_read(self, opportunity: SourceOpportunity) -> DeepSourceOpportunity:
        temp_id = safe_name(opportunity.external_reference or "GOV-CANDIDATE")
        evidence = EvidenceStore(self.workflow_type, temp_id, self.source_name, opportunity.source_url, self.run_id)
        documents: list[SourceDocument] = []
        parsed_results: list[dict] = []
        screenshots: list[str] = []
        raw_html_paths: list[str] = []

        if os.environ.get("DEEP_SOURCE_DISABLE_BROWSER") == "1":
            evidence.add_blocker("BROWSER_DISABLED_BY_ENV", opportunity.source_url)
            fields = extract_fields(opportunity, [], self.source_name)
            evidence.write_extracted_json("deep_extracted_fields.json", fields.to_dict())
            return DeepSourceOpportunity(opportunity, fields, documents, screenshots, raw_html_paths, relative(evidence.base_dir), "BLOCKED", "BROWSER_DISABLED_BY_ENV", evidence.manifest["citations"])

        browser = BrowserManager(self.name, evidence=evidence)
        try:
            context = browser.open_context(self.name, headless=self.headless)
            page = context.new_page()
            page.goto(opportunity.source_url, wait_until="domcontentloaded", timeout=60000)
            browser.detect_blockers(page, self.source_name)
            screenshots.append(browser.save_screenshot(page, temp_id, "detail_page", evidence))
            raw_html_paths.append(browser.save_raw_html(page, temp_id, "detail_page", evidence))
            html = page.content()
            html_path = PROJECT_ROOT / raw_html_paths[-1]
            parsed_results.append(parse_document(html_path, evidence).to_dict())

            links = extract_document_links(html, page.url)[:20]
            downloader = DocumentDownloader(evidence)
            if not links:
                evidence.record_download({"source_url": page.url, "local_path": "", "sha256": "", "status": "NO_ACCESSIBLE_DOCUMENT_LINKS"})
            for link in links:
                document = downloader.download_url(link)
                if not document:
                    continue
                result = parse_document(PROJECT_ROOT / document.local_path, evidence)
                document.parse_status = result.parse_status
                document.page_count = result.page_count
                document.extracted_text_path = result.extracted_text_path
                document.extraction_notes = result.notes
                documents.append(document)
                parsed_results.append(result.to_dict())
            fields = extract_fields(opportunity, parsed_results, self.source_name)
            evidence.write_extracted_json("deep_extracted_fields.json", fields.to_dict())
            return DeepSourceOpportunity(
                shallow=opportunity,
                extracted=fields,
                documents=documents,
                screenshots=screenshots,
                raw_html_paths=raw_html_paths,
                evidence_dir=relative(evidence.base_dir),
                extraction_status="COMPLETED",
                blocker_status="",
                citations=evidence.manifest["citations"],
            )
        except SourceBlocked as exc:
            evidence.add_blocker(exc.reason, opportunity.source_url, exc.details)
            fields = extract_fields(opportunity, parsed_results, self.source_name)
            evidence.write_extracted_json("deep_extracted_fields.json", fields.to_dict())
            return DeepSourceOpportunity(opportunity, fields, documents, screenshots, raw_html_paths, relative(evidence.base_dir), "BLOCKED", exc.reason, evidence.manifest["citations"])
        except Exception as exc:
            evidence.add_blocker("DEEP_READ_ERROR", opportunity.source_url, str(exc))
            fields = extract_fields(opportunity, parsed_results, self.source_name)
            evidence.write_extracted_json("deep_extracted_fields.json", fields.to_dict())
            return DeepSourceOpportunity(opportunity, fields, documents, screenshots, raw_html_paths, relative(evidence.base_dir), "ERROR", "DEEP_READ_ERROR", evidence.manifest["citations"])
        finally:
            browser.close_context()
