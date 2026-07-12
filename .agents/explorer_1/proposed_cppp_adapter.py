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
            if self.keyword and self.keyword.lower() not in chunk.lower() and idx > 0:
                continue
            tender_id_match = re.search(r"CPP/\d{4}/[A-Z0-9_/]+", chunk, flags=re.I)
            if not tender_id_match and "CPP/" not in chunk:
                continue
                
            lines = [line.strip() for line in chunk.splitlines() if line.strip()]
            tender_id = tender_id_match.group(0) if tender_id_match else f"CPP-LISTING-{idx + 1}"
            
            # Find date, estimated value, title, and buyer
            deadline = ""
            val = ""
            title = ""
            buyer = ""
            
            for line in lines:
                if re.search(r"\d{4}-\d{2}-\d{2}", line) or re.search(r"\d{2}-\d{2}-\d{4}", line):
                    deadline = line
                elif "INR" in line or re.search(r"\b\d{5,}\b", line):
                    val = line
                    
            other_lines = []
            for line in lines:
                if line == tender_id:
                    continue
                if line == deadline:
                    continue
                if line == val:
                    continue
                if line.isdigit() and len(line) < 4:  # row index
                    continue
                if any(word in line.lower() for word in ["download", "document", "nit", "corrigendum"]):
                    continue
                other_lines.append(line)
                
            if len(other_lines) >= 1:
                title = other_lines[0]
            if len(other_lines) >= 2:
                buyer = other_lines[1]
                
            source_url = unique_links[min(len(fallback_opportunities), len(unique_links) - 1)] if unique_links else current_url
            fallback_opportunities.append(
                SourceOpportunity(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    workflow_type=self.workflow_type,
                    source_url=source_url,
                    external_reference=tender_id,
                    opportunity_title=title or f"CPPP listing match {idx + 1}",
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
                
        return fallback_opportunities[: self.limit]
