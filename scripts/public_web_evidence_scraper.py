#!/usr/bin/env python3
"""Governed, read-only scraper for public HTML evidence.

This lane is intentionally conservative: HTTPS only, public DNS only, robots.txt
enforced, same-host crawl by default, bounded pages/bytes/depth, no cookies or
credentials, and no form/click/upload/message actions. Dynamic pages should be
captured with ``scripts/agent_browser_capture.py`` instead.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

try:
    from agent_browser_capture import blocker_status, public_hostname, relative, safe_slug, sha256
except ModuleNotFoundError:  # pragma: no cover
    from scripts.agent_browser_capture import (
        blocker_status,
        public_hostname,
        relative,
        safe_slug,
        sha256,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "web_scraping"
DEFAULT_USER_AGENT = "TenderExportOS-EvidenceBot/1.0 (read-only public research)"
NON_HTML_SUFFIXES = {
    ".7z",
    ".avi",
    ".csv",
    ".doc",
    ".docx",
    ".dmg",
    ".exe",
    ".gif",
    ".gz",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".rar",
    ".svg",
    ".tar",
    ".webp",
    ".xls",
    ".xlsx",
    ".zip",
}


def normalize_url(url: str, *, resolve_dns: bool = True) -> str:
    public_hostname(url, resolve_dns=resolve_dns)
    clean, _fragment = urldefrag(url.strip())
    parsed = urlparse(clean)
    path = parsed.path or "/"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", parsed.query, ""))


def same_public_host(url: str, expected_host: str, *, resolve_dns: bool = True) -> bool:
    try:
        host = public_hostname(url, resolve_dns=resolve_dns)
    except ValueError:
        return False
    left = host[4:] if host.startswith("www.") else host
    right = expected_host[4:] if expected_host.startswith("www.") else expected_host
    return left == right


def extract_html(html: str, base_url: str, *, max_text_chars: int = 200_000) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "template", "svg", "iframe"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description = ""
    description_node = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if description_node:
        description = str(description_node.get("content") or "").strip()

    canonical = ""
    canonical_node = soup.find("link", attrs={"rel": lambda value: value and "canonical" in value})
    if canonical_node and canonical_node.get("href"):
        canonical = urljoin(base_url, str(canonical_node.get("href")))

    headings = []
    for node in soup.find_all(re.compile(r"^h[1-6]$")):
        value = node.get_text(" ", strip=True)
        if value:
            headings.append({"level": int(node.name[1]), "text": value[:1000]})

    links: list[dict[str, str]] = []
    public_contacts: list[str] = []
    seen_links: set[str] = set()
    for node in soup.find_all("a", href=True):
        raw_href = str(node.get("href") or "").strip()
        if raw_href.lower().startswith("mailto:"):
            address = raw_href[7:].split("?", 1)[0].strip()
            if address and address not in public_contacts:
                public_contacts.append(address)
            continue
        absolute = urljoin(base_url, raw_href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        normalized, _ = urldefrag(absolute)
        if normalized in seen_links:
            continue
        seen_links.add(normalized)
        links.append(
            {
                "url": normalized,
                "text": node.get_text(" ", strip=True)[:1000],
                "rel": " ".join(node.get("rel") or []),
            }
        )
        if len(links) >= 1000:
            break

    text = soup.get_text("\n", strip=True)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    truncated = len(text) > max_text_chars
    if truncated:
        text = text[:max_text_chars]

    return {
        "title": title[:2000],
        "description": description[:4000],
        "canonical_url": canonical,
        "headings": headings[:500],
        "links": links,
        "public_mailto_contacts": public_contacts[:200],
        "text": text,
        "text_truncated": truncated,
    }


def crawlable_links(
    extracted: dict[str, Any],
    *,
    host: str,
    resolve_dns: bool = True,
) -> list[str]:
    urls: list[str] = []
    for link in extracted.get("links", []):
        url = str(link.get("url") or "")
        if Path(urlparse(url).path.lower()).suffix in NON_HTML_SUFFIXES:
            continue
        if not same_public_host(url, host, resolve_dns=resolve_dns):
            continue
        try:
            normalized = normalize_url(url, resolve_dns=resolve_dns)
        except ValueError:
            continue
        if normalized not in urls:
            urls.append(normalized)
    return urls


def _robots_allowed(
    session: requests.Session,
    url: str,
    *,
    user_agent: str,
    timeout: int,
    resolve_dns: bool,
) -> tuple[bool, str]:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = session.get(robots_url, timeout=timeout, allow_redirects=True)
        for hop in [*response.history, response]:
            if not same_public_host(hop.url, parsed.hostname or "", resolve_dns=resolve_dns):
                raise ValueError("cross-host robots redirect is not permitted")
        if response.status_code == 404:
            return True, "ROBOTS_NOT_FOUND"
        if response.status_code != 200:
            return False, f"ROBOTS_UNAVAILABLE_HTTP_{response.status_code}"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(response.text.splitlines())
        return parser.can_fetch(user_agent, url), "ROBOTS_ALLOWED" if parser.can_fetch(user_agent, url) else "ROBOTS_DISALLOWED"
    except (requests.RequestException, ValueError) as exc:
        return False, f"ROBOTS_CHECK_FAILED:{type(exc).__name__}"


def _bounded_get(
    session: requests.Session,
    url: str,
    *,
    timeout: int,
    max_bytes: int,
    resolve_dns: bool,
) -> tuple[requests.Response, bytes]:
    expected_host = public_hostname(url, resolve_dns=resolve_dns)
    response = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
    for hop in [*response.history, response]:
        if not same_public_host(hop.url, expected_host, resolve_dns=resolve_dns):
            raise ValueError("cross-host redirect is not permitted")
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise ValueError(f"unsupported content type: {content_type or 'missing'}")
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        size += len(chunk)
        if size > max_bytes:
            response.close()
            raise ValueError(f"response exceeded max_bytes={max_bytes}")
        chunks.append(chunk)
    body = b"".join(chunks)
    response.close()
    return response, body


def _page_dir(run_dir: Path, index: int, url: str) -> Path:
    parsed = urlparse(url)
    hint = safe_slug(Path(parsed.path).name or parsed.hostname or "page")
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return run_dir / "pages" / f"{index:03d}-{hint}-{digest}"


def scrape(
    urls: Iterable[str],
    *,
    source_name: str,
    case_id: str = "",
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    follow_links: bool = False,
    max_pages: int = 10,
    max_depth: int = 1,
    delay_seconds: float = 1.5,
    timeout: int = 30,
    max_bytes: int = 5_000_000,
    resolve_dns: bool = True,
    session: requests.Session | None = None,
) -> tuple[dict[str, Any], Path]:
    seeds = [normalize_url(url, resolve_dns=resolve_dns) for url in urls]
    if not seeds:
        raise ValueError("at least one public HTTPS URL is required")
    max_pages = max(1, min(max_pages, 50))
    max_depth = max(0, min(max_depth, 3))
    delay_seconds = max(1.0, delay_seconds)
    timeout = max(5, min(timeout, 120))
    max_bytes = max(100_000, min(max_bytes, 10_000_000))

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"WEB-{timestamp}-{uuid.uuid4().hex[:8]}"
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    client = session or requests.Session()
    client.headers.update({"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    queue = deque((seed, 0) for seed in seeds)
    visited: set[str] = set()
    robots_cache: dict[tuple[str, str], tuple[bool, str]] = {}
    pages: list[dict[str, Any]] = []
    last_request_at = 0.0

    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        host = public_hostname(url, resolve_dns=resolve_dns)
        robots_key = (urlparse(url).scheme, host)
        if robots_key not in robots_cache:
            robots_cache[robots_key] = _robots_allowed(
                client,
                url,
                user_agent=DEFAULT_USER_AGENT,
                timeout=timeout,
                resolve_dns=resolve_dns,
            )
        allowed, robots_status = robots_cache[robots_key]
        page: dict[str, Any] = {
            "url": url,
            "depth": depth,
            "host": host,
            "robots_status": robots_status,
            "status": "ROBOTS_BLOCKED" if not allowed else "PENDING",
            "artifacts": {},
            "sha256": {},
            "blockers": [],
        }
        if not allowed:
            pages.append(page)
            continue

        elapsed = time.monotonic() - last_request_at
        if last_request_at and elapsed < delay_seconds:
            time.sleep(delay_seconds - elapsed)
        last_request_at = time.monotonic()
        page_dir = _page_dir(run_dir, len(pages) + 1, url)
        page_dir.mkdir(parents=True, exist_ok=True)
        try:
            response, body = _bounded_get(
                client,
                url,
                timeout=timeout,
                max_bytes=max_bytes,
                resolve_dns=resolve_dns,
            )
            encoding = response.encoding or response.apparent_encoding or "utf-8"
            html = body.decode(encoding, errors="replace")
            extracted = extract_html(html, response.url)
            html_path = page_dir / "page.html"
            extracted_path = page_dir / "extracted.json"
            text_path = page_dir / "text.txt"
            html_path.write_bytes(body)
            extracted_path.write_text(
                json.dumps(extracted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            text_path.write_text(extracted["text"] + "\n", encoding="utf-8")
            artifacts = {
                "html": relative(html_path),
                "extracted": relative(extracted_path),
                "text": relative(text_path),
            }
            page.update(
                {
                    "status": "CAPTURED",
                    "final_url": response.url,
                    "http_status": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "bytes": len(body),
                    "title": extracted["title"],
                    "description": extracted["description"],
                    "heading_count": len(extracted["headings"]),
                    "link_count": len(extracted["links"]),
                    "public_mailto_contacts": extracted["public_mailto_contacts"],
                    "blockers": blocker_status(extracted["text"]),
                    "artifacts": artifacts,
                    "sha256": {
                        name: sha256(PROJECT_ROOT / path) for name, path in artifacts.items()
                    },
                }
            )
            if follow_links and depth < max_depth:
                for link in crawlable_links(extracted, host=host, resolve_dns=resolve_dns):
                    if link not in visited:
                        queue.append((link, depth + 1))
        except (requests.RequestException, ValueError, OSError) as exc:
            page.update({"status": "FAILED", "error": f"{type(exc).__name__}: {exc}"})
        pages.append(page)

    captured = sum(page["status"] == "CAPTURED" for page in pages)
    blocked = sum(page["status"] == "ROBOTS_BLOCKED" for page in pages)
    failed = sum(page["status"] == "FAILED" for page in pages)
    status = "COMPLETED"
    if captured == 0:
        status = "FAILED"
    elif blocked or failed:
        status = "PARTIAL"
    receipt = {
        "schema_version": 1,
        "run_id": run_id,
        "captured_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_name": source_name,
        "case_id": case_id,
        "status": status,
        "seed_urls": seeds,
        "policy": {
            "mode": "READ_ONLY_PUBLIC_HTML",
            "robots_enforced": True,
            "https_only": True,
            "public_network_only": True,
            "same_host_link_following": True,
            "cookies_or_auth": False,
            "form_or_click_actions": False,
            "max_pages": max_pages,
            "max_depth": max_depth,
            "min_delay_seconds": delay_seconds,
            "max_response_bytes": max_bytes,
        },
        "summary": {"captured": captured, "robots_blocked": blocked, "failed": failed},
        "pages": pages,
        "safety": "No login, CAPTCHA/paywall bypass, form fill, click, upload, download, message, payment, DSC, or commercial commitment is available in this lane.",
    }
    receipt_path = run_dir / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt, receipt_path


def _load_urls(explicit: list[str], urls_file: str) -> list[str]:
    urls = [value.strip() for value in explicit if value.strip()]
    if urls_file:
        for line in Path(urls_file).expanduser().read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                urls.append(value)
    return list(dict.fromkeys(urls))


def main() -> int:
    parser = argparse.ArgumentParser(description="Governed public HTML evidence scraper")
    parser.add_argument("--url", action="append", default=[], help="Public HTTPS seed URL; repeatable")
    parser.add_argument("--urls-file", default="", help="Text file with one public HTTPS URL per line")
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--follow-links", action="store_true")
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--max-depth", type=int, default=1)
    parser.add_argument("--delay-seconds", type=float, default=1.5)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    args = parser.parse_args()

    output_root = Path(args.output_root).expanduser()
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root
    try:
        receipt, path = scrape(
            _load_urls(args.url, args.urls_file),
            source_name=args.source_name,
            case_id=args.case_id,
            output_root=output_root,
            follow_links=args.follow_links,
            max_pages=args.max_pages,
            max_depth=args.max_depth,
            delay_seconds=args.delay_seconds,
            timeout=args.timeout,
            max_bytes=args.max_bytes,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(
        json.dumps(
            {"status": receipt["status"], "run_id": receipt["run_id"], "receipt": relative(path)},
            indent=2,
        )
    )
    return 0 if receipt["status"] != "FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
