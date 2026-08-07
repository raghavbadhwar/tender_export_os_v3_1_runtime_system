from __future__ import annotations

import pytest

from scripts.public_web_evidence_scraper import (
    body_sha256,
    crawlable_links,
    extract_html,
    normalize_url,
    same_public_host,
)


HTML = """
<!doctype html>
<html>
  <head>
    <title>Buyer Catalogue</title>
    <meta name="description" content="Handmade products for wholesale buyers">
    <link rel="canonical" href="/catalogue">
    <style>.hidden { display:none }</style>
    <script>window.secret = 'do not extract';</script>
  </head>
  <body>
    <h1>Handmade Homeware</h1>
    <h2>New collection</h2>
    <p>Public catalogue evidence.</p>
    <a href="/products/basket">Basket</a>
    <a href="https://shop.example.com/about#team">About</a>
    <a href="https://other.example.org/item">External</a>
    <a href="/catalog.pdf">PDF</a>
    <a href="mailto:trade@example.com">Trade contact</a>
  </body>
</html>
"""


def test_extract_html_returns_structured_public_evidence() -> None:
    result = extract_html(HTML, "https://shop.example.com/catalogue")

    assert result["title"] == "Buyer Catalogue"
    assert result["description"] == "Handmade products for wholesale buyers"
    assert result["canonical_url"] == "https://shop.example.com/catalogue"
    assert [item["text"] for item in result["headings"]] == [
        "Handmade Homeware",
        "New collection",
    ]
    assert "window.secret" not in result["text"]
    assert result["public_mailto_contacts"] == ["trade@example.com"]


def test_crawlable_links_stay_on_host_and_skip_documents() -> None:
    result = extract_html(HTML, "https://shop.example.com/catalogue")

    links = crawlable_links(result, host="shop.example.com", resolve_dns=False)

    assert links == [
        "https://shop.example.com/products/basket",
        "https://shop.example.com/about",
    ]


def test_normalize_url_rejects_non_https_and_private_hosts() -> None:
    with pytest.raises(ValueError):
        normalize_url("http://example.com", resolve_dns=False)
    with pytest.raises(ValueError):
        normalize_url("https://localhost/internal", resolve_dns=False)


def test_same_public_host_accepts_www_equivalent_only() -> None:
    assert same_public_host("https://www.example.com/a", "example.com", resolve_dns=False)
    assert not same_public_host("https://other.example.com/a", "example.com", resolve_dns=False)


def test_body_sha256_allows_duplicate_public_content_to_be_detected() -> None:
    assert body_sha256(b"same public evidence") == body_sha256(b"same public evidence")
    assert body_sha256(b"same public evidence") != body_sha256(b"different public evidence")
