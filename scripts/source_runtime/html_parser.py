"""HTML text and link parsing helpers."""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.parts.append(text)


def html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return "\n".join(line for line in soup.get_text("\n", strip=True).splitlines() if line.strip())
    except Exception:
        parser = _TextParser()
        parser.feed(html)
        return "\n".join(parser.parts)


def extract_document_links(html: str, base_url: str) -> list[str]:
    suffixes = (".pdf", ".xlsx", ".xls", ".csv", ".docx", ".zip")
    links: list[str] = []
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"]).strip()
            text = anchor.get_text(" ", strip=True).lower()
            if href.lower().split("?")[0].endswith(suffixes) or any(word in text for word in ["download", "document", "boq", "nit", "corrigendum"]):
                links.append(urljoin(base_url, href))
    except Exception:
        pass
    seen: set[str] = set()
    unique: list[str] = []
    for link in links:
        if link not in seen:
            unique.append(link)
            seen.add(link)
    return unique
