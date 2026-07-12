"""Proposed CPPP/eProcure source-specific adapter with page-text extraction fallback."""

from __future__ import annotations

import re
from urllib.parse import urljoin
from scripts.source_adapters.base import SourceOpportunity
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

    def extract_listing_cards(self, html: str, current_url: str) -> list[SourceOpportunity]:
        # Try selector-based extraction first
        opportunities = super().extract_listing_cards(html, current_url)
        for opportunity in opportunities:
            value = opportunity.estimated_value_inr.strip()
            if value and not re.search(r"(?:₹|INR|RS\.?|RUPEES?)\s*[\d,]+|\b\d{5,}(?:\.\d+)?\b", value, flags=re.I):
                opportunity.estimated_value_inr = ""

        # Check if all opportunities have required fields populated (not default/fallbacks)
        is_valid = len(opportunities) > 0 and all(
            opt.external_reference and opt.buyer_name and opt.deadline_date
            for opt in opportunities
            if "CPP-LISTING-" not in opt.external_reference
        )
        if is_valid:
            return opportunities[: self.limit]

        # Fallback to page-text keyword extraction and regex parsing
        from scripts.source_runtime.html_parser import html_to_text

        text = html_to_text(html)
        # Find all detail links
        links = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
        detail_links = []
        for href in links:
            if "TenderDetails" in href or "cppp" in href.lower() or "showbid" in href.lower():
                detail_links.append(urljoin(current_url, href))
        seen: set[str] = set()
        unique_links = []
        for link in detail_links:
            if link not in seen:
                unique_links.append(link)
                seen.add(link)

        fallback_opportunities = []
        # Split text into chunks representing potential cards
        chunks = [chunk for chunk in re.split(r"\n{2,}|(?=CPP/\d{4}/)", text) if chunk.strip()]
        for idx, chunk in enumerate(chunks):
            if self.keyword and self.keyword.lower() not in chunk.lower():
                continue
            tender_id_match = re.search(r"CPP/\d{4}/[A-Z0-9_/]+", chunk, flags=re.I)
            if not tender_id_match:
                continue

            lines = [line.strip() for line in chunk.splitlines() if line.strip()]
            tender_id = tender_id_match.group(0)

            # Find date, estimated value, title, and buyer
            deadline = ""
            val = ""
            buyer = ""

            for line in lines:
                if re.search(r"\d{4}-\d{2}-\d{2}", line) or re.search(r"\d{2}-\d{2}-\d{4}", line):
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
                if line.isdigit() and len(line) < 4:  # row index
                    continue
                if any(word in line.lower() for word in ["download", "document", "nit", "corrigendum"]):
                    continue
                other_lines.append(line)

            title = ""
            if len(other_lines) >= 1:
                title = other_lines[0]
            else:
                title = f"CPPP Bid {tender_id}"

            source_url = unique_links[min(len(fallback_opportunities), len(unique_links) - 1)] if unique_links else current_url
            fallback_opportunities.append(
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
                    notes="Listing extracted from CPPP page text; verify detail evidence before action.",
                )
            )
            if len(fallback_opportunities) >= self.limit:
                break

        if not fallback_opportunities and text:
            fallback_opportunities.append(
                SourceOpportunity(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    workflow_type=self.workflow_type,
                    source_url=current_url,
                    external_reference="CPP-LISTING-UNSTRUCTURED",
                    opportunity_title=(self.keyword or "CPPP listing page reached"),
                    product_or_service=self.keyword,
                    citations=[current_url],
                    notes="Page reached but no structured bid cards were detected by rules.",
                )
            )
        return fallback_opportunities[: self.limit]
