"""Proposed GeM BidPlus deep source adapter with regex and text-based fallback."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote_plus, urljoin

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover - optional parser fallback
    BeautifulSoup = None  # type: ignore

try:
    from scripts.source_adapters.base import DeepSourceOpportunity, SourceBlocked, SourceDocument, SourceOpportunity
except ModuleNotFoundError:
    from base import DeepSourceOpportunity, SourceBlocked, SourceDocument, SourceOpportunity  # type: ignore

from scripts.source_runtime.browser_manager import BrowserManager
from scripts.source_runtime.document_downloader import DocumentDownloader
from scripts.source_runtime.document_parser import parse_document
from scripts.source_runtime.evidence_store import EvidenceStore, relative, safe_name
from scripts.source_runtime.html_parser import extract_document_links, html_to_text
from scripts.source_runtime.selector_extractor import extract_cards, load_selector_config
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
        self.selector_config = load_selector_config(self.name)

    def build_search_url(self) -> str:
        if self.keyword:
            return f"{self.base_url}?search={quote_plus(self.keyword)}"
        return self.base_url

    def apply_filters(self, page) -> None:
        return None

    def open_detail(self, page, opportunity: SourceOpportunity) -> None:
        page.goto(opportunity.source_url, wait_until="domcontentloaded", timeout=60000)

    def extract_detail_fields(self, opportunity: SourceOpportunity, parsed_results: list[dict]) -> object:
        return extract_fields(opportunity, parsed_results, self.source_name)

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

    @staticmethod
    def _plausible_title(value: str) -> bool:
        normalized = " ".join(value.split()).strip(" :.-").lower()
        labels = {"ra no", "bid no", "bid number", "items", "quantity", "start date", "end date"}
        return normalized not in labels and len(normalized) >= 8 and sum(character.isalpha() for character in normalized) >= 6

    def _extract_live_gem_cards(self, html: str, current_url: str) -> list[SourceOpportunity] | None:
        """Extract the live BidPlus card layout without confusing RA labels or static links for bids.

        The generic selector fallback is retained for fixtures and future layout variants.  The
        current public page has a stable ``#bidCard .card`` structure where the true item title
        is carried in a ``data-content`` attribute and the actionable record link is specifically
        ``showbidDocument``.  Parsing this structure directly prevents false tender leads.
        """
        if BeautifulSoup is None:
            return None
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("#bidCard .card")
        if not cards:
            return None

        opportunities: list[SourceOpportunity] = []
        saw_bid_card = False
        for card in cards:
            bid_link = next(
                (
                    anchor
                    for anchor in card.select("a[href*='showbidDocument']")
                    if re.search(r"GEM/\d{4}/B/\d+", anchor.get_text(" ", strip=True), flags=re.I)
                ),
                None,
            )
            if bid_link is None:
                continue
            saw_bid_card = True
            tender_id_match = re.search(r"GEM/\d{4}/B/\d+", bid_link.get_text(" ", strip=True), flags=re.I)
            if tender_id_match is None:  # defensive, kept close to the selector above
                continue
            title_node = card.select_one(".card-body .col-md-4 a[data-content]") or card.select_one(".card-body .col-md-4 a")
            title = ""
            if title_node is not None:
                title = str(title_node.get("data-content") or title_node.get_text(" ", strip=True)).strip()
            if self.keyword and self.keyword.lower() not in title.lower():
                continue
            if not self._plausible_title(title):
                continue
            buyer_column = card.select_one(".card-body .col-md-5")
            buyer = " ".join(buyer_column.stripped_strings) if buyer_column is not None else ""
            buyer = re.sub(r"^Department Name And Address:\s*", "", buyer, flags=re.I).strip()
            deadline_node = card.select_one(".end_date")
            deadline = deadline_node.get_text(" ", strip=True) if deadline_node is not None else ""
            source_url = urljoin(current_url, str(bid_link.get("href") or ""))
            opportunities.append(
                SourceOpportunity(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    workflow_type=self.workflow_type,
                    source_url=source_url,
                    external_reference=tender_id_match.group(0).upper(),
                    opportunity_title=title,
                    buyer_name=buyer,
                    product_or_service=self.keyword,
                    deadline_date=deadline,
                    citations=[source_url],
                    notes="Public GeM BidPlus card extraction; detail document evidence is still required before case movement.",
                )
            )
            if len(opportunities) >= self.limit:
                break

        if opportunities or saw_bid_card:
            return opportunities
        return [
            SourceOpportunity(
                source_name=self.source_name,
                source_type=self.source_type,
                workflow_type=self.workflow_type,
                source_url=current_url,
                external_reference="GEM-LISTING-UNSTRUCTURED",
                opportunity_title="GeM listing page reached but no valid bid cards were extracted",
                citations=[current_url],
                notes="The live card layout was present but required bid fields were incomplete; do not create a case from this record.",
            )
        ]

    def _extract_listing_opportunities(self, html: str, current_url: str) -> list[SourceOpportunity]:
        live_card_opportunities = self._extract_live_gem_cards(html, current_url) if self.name == "gem" else None
        if live_card_opportunities is not None:
            return live_card_opportunities[: self.limit]
        selector_cards = extract_cards(html, current_url, self.selector_config)
        selector_opportunities: list[SourceOpportunity] = []
        for card in selector_cards[: self.limit]:
            title = card.get("title", "")
            if self.keyword and self.keyword.lower() not in (title + " " + card.get("text", "")).lower():
                continue
            selector_opportunities.append(
                SourceOpportunity(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    workflow_type=self.workflow_type,
                    source_url=card.get("detail_link") or current_url,
                    external_reference=card.get("tender_id") or f"GEM-LISTING-{len(selector_opportunities) + 1}",
                    opportunity_title=title or f"GeM listing match {len(selector_opportunities) + 1}",
                    buyer_name=card.get("buyer", ""),
                    product_or_service=self.keyword,
                    deadline_date=card.get("deadline", ""),
                    estimated_value_inr=card.get("value", ""),
                    citations=[card.get("detail_link") or current_url],
                    notes="Selector-first GeM public listing extraction; verify detail evidence before action.",
                )
            )
        if selector_opportunities:
            # Check if all opportunities have required fields populated (not default/fallbacks)
            is_valid = all(
                opt.external_reference
                and opt.buyer_name
                and opt.deadline_date
                for opt in selector_opportunities
                if "GEM-LISTING-" not in opt.external_reference
            )
            if self.name == "gem":
                is_valid = is_valid and all(
                    self._plausible_title(opt.opportunity_title) and "showbiddocument" in opt.source_url.lower()
                    for opt in selector_opportunities
                    if "GEM-LISTING-" not in opt.external_reference
                )
            if is_valid:
                return selector_opportunities[: self.limit]

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
            if self.keyword and self.keyword.lower() not in chunk.lower():
                continue
            bid = re.search(r"GEM/\d{4}/B/\d+", chunk, flags=re.I)
            if not bid:
                continue

            lines = [line.strip() for line in chunk.splitlines() if line.strip()]
            tender_id = bid.group(0)
            deadline = ""
            buyer = ""
            val = ""

            for line in lines:
                if re.search(r"\d{2}-\d{2}-\d{4}", line) or re.search(r"\d{4}-\d{2}-\d{2}", line):
                    if ":" in line:
                        deadline = line.split(":", 1)[1].strip()
                    else:
                        deadline = line
                elif ("INR" in line or re.search(r"\b\d{5,}\b", line)) and tender_id not in line:
                    if ":" in line:
                        val = line.split(":", 1)[1].strip()
                    else:
                        val = line
                elif any(word in line.lower() for word in ["organisation", "buyer", "authority", "ministry", "department", "exporter"]):
                    if ":" in line:
                        buyer = line.split(":", 1)[1].strip()
                    else:
                        buyer = line

            other_lines = []
            for line in lines:
                if tender_id in line:
                    continue
                if deadline and deadline in line:
                    continue
                if val and val in line:
                    continue
                if buyer and buyer in line:
                    continue
                if any(word in line.lower() for word in ["download", "document", "nit", "corrigendum"]):
                    continue
                other_lines.append(line)

            title = ""
            if len(other_lines) >= 1:
                title = other_lines[0]
            else:
                title = f"GeM Bid {tender_id}"

            source_url = unique_links[min(len(opportunities), len(unique_links) - 1)] if unique_links else current_url
            opportunities.append(
                SourceOpportunity(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    workflow_type=self.workflow_type,
                    source_url=source_url,
                    external_reference=tender_id,
                    opportunity_title=title,
                    buyer_name=buyer,
                    product_or_service=self.keyword,
                    deadline_date=deadline,
                    estimated_value_inr=val,
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
        url = self.build_search_url()
        browser = BrowserManager(self.name)
        try:
            context = browser.open_context(self.name, headless=self.headless)
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            self.apply_filters(page)
            self.detect_source_specific_blockers(page)
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
            self.open_detail(page, opportunity)
            self.detect_source_specific_blockers(page)
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
            fields = self.extract_detail_fields(opportunity, parsed_results)
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
