"""Open-source web-search and evidence-bundle wrapper for Tender Export OS.

This module keeps broad discovery deterministic and proof-friendly:
SearXNG/DDGS discover, Katana expands URLs, Trafilatura/Crawl4AI capture detail
pages, and the caller writes an evidence-only bundle.  It never creates cases or
performs external business actions.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import os
import pwd
import re
import shutil
import subprocess
import time
import urllib.parse
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "source_discovery"
USER_AGENT = "TenderExportOS/1.0 evidence-only research bot (+local operator)"


def actual_user_home() -> Path:
    """Return the macOS account home, not Hermes' profile-local HOME override."""
    try:
        return Path(pwd.getpwuid(os.getuid()).pw_dir)
    except Exception:  # pragma: no cover
        return Path(os.environ.get("REAL_HOME") or os.environ.get("USER_HOME") or os.path.expanduser("~"))


def ensure_playwright_cache_env() -> None:
    """Point Playwright/Crawl4AI at the user-level browser cache when Hermes HOME is profile-local."""
    cache = actual_user_home() / "Library" / "Caches" / "ms-playwright"
    if cache.exists():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(cache))


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    snippet: str = ""
    engine: str = "unknown"
    rank: int = 0


@dataclass(frozen=True)
class PageCapture:
    url: str
    status: str
    title: str = ""
    text: str = ""
    raw_html_path: str = ""
    parsed_text_path: str = ""
    markdown_path: str = ""
    screenshot_path: str = ""
    tool: str = ""
    blocker: str = ""
    error: str = ""


@dataclass
class Candidate:
    url: str
    title: str = ""
    snippet: str = ""
    engines: set[str] = field(default_factory=set)
    discovery_sources: set[str] = field(default_factory=set)
    ranks: dict[str, int] = field(default_factory=dict)
    capture: PageCapture | None = None

    def evidence_level(self) -> str:
        if self.capture and self.capture.status == "captured" and (self.capture.text or self.capture.parsed_text_path):
            return "DETAIL_PAGE_CAPTURED"
        if "katana" in self.discovery_sources and not self.engines:
            return "URL_DISCOVERED_ONLY"
        return "PUBLIC_SEARCH_RESULT"

    def to_dict(self) -> dict[str, Any]:
        capture = asdict(self.capture) if self.capture else None
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "engines": sorted(self.engines),
            "discovery_sources": sorted(self.discovery_sources),
            "ranks": dict(sorted(self.ranks.items())),
            "evidence_level": self.evidence_level(),
            "capture": capture,
            "citations": [p for p in [self.url, *(capture or {}).get("raw_html_path", "").splitlines(), *(capture or {}).get("parsed_text_path", "").splitlines(), *(capture or {}).get("markdown_path", "").splitlines()] if p],
        }


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def make_run_id(prefix: str = "osdisc") -> str:
    return f"{prefix}_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def safe_name(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())[:120].strip("._-")
    return cleaned or fallback


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def canonical_url(url: str) -> str:
    parsed = urllib.parse.urlsplit((url or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return (url or "").strip()
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    query = urllib.parse.urlencode(sorted(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)))
    return urllib.parse.urlunsplit((scheme, netloc, path.rstrip("/") or "/", query, ""))


def html_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html or "", re.I | re.S)
    if not match:
        match = re.search(r"<h1[^>]*>(.*?)</h1>", html or "", re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()


def text_preview(text: str, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    return compact[:limit]


def build_discovery_bundle(
    *,
    query: str,
    workflow: str,
    run_id: str,
    search_hits: Iterable[SearchHit],
    katana_urls: Iterable[str],
    captures: dict[str, PageCapture],
    tool_receipts: dict[str, Any],
) -> dict[str, Any]:
    candidates: dict[str, Candidate] = {}

    def ensure(url: str) -> Candidate | None:
        key = canonical_url(url)
        if not key:
            return None
        if key not in candidates:
            candidates[key] = Candidate(url=key)
        return candidates[key]

    for hit in search_hits:
        candidate = ensure(hit.url)
        if not candidate:
            continue
        candidate.title = candidate.title or hit.title
        candidate.snippet = candidate.snippet or hit.snippet
        candidate.engines.add(hit.engine)
        candidate.discovery_sources.add(hit.engine)
        if hit.rank:
            candidate.ranks[hit.engine] = min(hit.rank, candidate.ranks.get(hit.engine, hit.rank))

    for url in katana_urls:
        candidate = ensure(url)
        if not candidate:
            continue
        candidate.discovery_sources.add("katana")

    for url, capture in captures.items():
        candidate = ensure(url)
        if not candidate:
            continue
        candidate.capture = capture
        candidate.title = candidate.title or capture.title
        if capture.text and not candidate.snippet:
            candidate.snippet = text_preview(capture.text)

    candidate_rows = [candidate.to_dict() for candidate in sorted(candidates.values(), key=lambda item: item.url)]
    captured = [row for row in candidate_rows if row["evidence_level"] == "DETAIL_PAGE_CAPTURED"]
    blockers = []
    for name, receipt in tool_receipts.items():
        if isinstance(receipt, dict) and receipt.get("status") not in {"ok", "skipped"}:
            blockers.append({"tool": name, **receipt})
    return {
        "run_id": run_id,
        "created_at": utc_now(),
        "query": query,
        "workflow": workflow.upper(),
        "external_side_effects": False,
        "cases_created": 0,
        "approval_required_before_external_action": True,
        "summary": {
            "unique_candidate_count": len(candidate_rows),
            "captured_page_count": len(captured),
            "blocker_count": len(blockers),
            "tools_used": sorted(tool_receipts),
        },
        "tool_receipts": tool_receipts,
        "blockers": blockers,
        "candidates": candidate_rows,
    }


def render_markdown_bundle(bundle: dict[str, Any]) -> str:
    lines = [
        f"# Open-source source-discovery bundle — {bundle['query']}",
        "",
        f"- Run ID: `{bundle['run_id']}`",
        f"- Workflow: `{bundle['workflow']}`",
        f"- Created: `{bundle['created_at']}`",
        f"- External side effects: `{bundle['external_side_effects']}`",
        f"- Cases created: `{bundle['cases_created']}`",
        f"- Unique candidates: `{bundle['summary']['unique_candidate_count']}`",
        f"- Captured pages: `{bundle['summary']['captured_page_count']}`",
        "",
        "## Tool receipts",
    ]
    for name, receipt in bundle.get("tool_receipts", {}).items():
        status = receipt.get("status") if isinstance(receipt, dict) else receipt
        lines.append(f"- **{name}**: `{status}`")
    if bundle.get("blockers"):
        lines.extend(["", "## Blockers"])
        for blocker in bundle["blockers"]:
            lines.append(f"- `{blocker.get('tool')}`: {blocker.get('status')} {blocker.get('error', '')}")
    lines.extend(["", "## Candidates"])
    for idx, candidate in enumerate(bundle.get("candidates", []), 1):
        lines.extend(
            [
                f"### {idx}. {candidate.get('title') or candidate['url']}",
                "",
                f"- URL: {candidate['url']}",
                f"- Evidence level: `{candidate['evidence_level']}`",
                f"- Engines: `{', '.join(candidate.get('engines', [])) or 'none'}`",
                f"- Discovery sources: `{', '.join(candidate.get('discovery_sources', [])) or 'none'}`",
            ]
        )
        if candidate.get("snippet"):
            lines.append(f"- Snippet: {candidate['snippet']}")
        capture = candidate.get("capture") or {}
        for key in ("raw_html_path", "parsed_text_path", "markdown_path", "screenshot_path"):
            if capture.get(key):
                lines.append(f"- {key}: `{capture[key]}`")
        lines.append("")
    lines.append("No cases created. Treat these as leads/evidence only until staged through proof gates.")
    return "\n".join(lines).rstrip() + "\n"


def write_discovery_bundle(bundle: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_json = output_dir / "bundle.json"
    bundle_md = output_dir / "bundle.md"
    manifest_json = output_dir / "manifest.json"
    bundle_json.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    bundle_md.write_text(render_markdown_bundle(bundle), encoding="utf-8")
    manifest = {
        "run_id": bundle["run_id"],
        "query": bundle["query"],
        "created_at": utc_now(),
        "bundle_json": bundle_json.name,
        "bundle_md": bundle_md.name,
        "candidate_count": bundle["summary"]["unique_candidate_count"],
        "captured_page_count": bundle["summary"]["captured_page_count"],
        "external_side_effects": False,
    }
    manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "bundle_json": str(bundle_json),
        "bundle_md": str(bundle_md),
        "manifest_json": str(manifest_json),
    }


def load_fixture(path: Path, limit: int) -> tuple[list[SearchHit], list[SearchHit], list[str], dict[str, str], dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    searxng = [
        SearchHit(
            title=str(item.get("title", "")),
            url=str(item.get("url", "")),
            snippet=str(item.get("content") or item.get("snippet") or ""),
            engine="searxng",
            rank=index + 1,
        )
        for index, item in enumerate(data.get("searxng", [])[:limit])
    ]
    ddgs = [
        SearchHit(
            title=str(item.get("title", "")),
            url=str(item.get("href") or item.get("url") or ""),
            snippet=str(item.get("body") or item.get("snippet") or ""),
            engine="ddgs",
            rank=index + 1,
        )
        for index, item in enumerate(data.get("ddgs", [])[:limit])
    ]
    return searxng, ddgs, list(data.get("katana", []))[:limit], dict(data.get("pages", {})), {"fixture": {"status": "ok", "path": str(path)}}


def query_searxng(base_url: str, query: str, limit: int, timeout: float = 20.0) -> tuple[list[SearchHit], dict[str, Any]]:
    try:
        import httpx

        url = urllib.parse.urljoin(base_url.rstrip("/") + "/", "search")
        with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
            response = client.get(url, params={"q": query, "format": "json"})
            response.raise_for_status()
            payload = response.json()
        hits = [
            SearchHit(
                title=str(item.get("title", "")),
                url=str(item.get("url", "")),
                snippet=str(item.get("content") or item.get("snippet") or ""),
                engine="searxng",
                rank=index + 1,
            )
            for index, item in enumerate(payload.get("results", [])[:limit])
            if item.get("url")
        ]
        return hits, {"status": "ok", "base_url": base_url, "result_count": len(hits)}
    except Exception as exc:  # pragma: no cover - exercised by live environment, not unit tests
        return [], {"status": "blocked_or_error", "base_url": base_url, "error": str(exc)}


def query_ddgs(query: str, limit: int) -> tuple[list[SearchHit], dict[str, Any]]:
    try:
        from ddgs import DDGS

        rows = list(DDGS().text(query, max_results=limit))
        hits = [
            SearchHit(
                title=str(item.get("title", "")),
                url=str(item.get("href") or item.get("url") or ""),
                snippet=str(item.get("body") or item.get("snippet") or ""),
                engine="ddgs",
                rank=index + 1,
            )
            for index, item in enumerate(rows)
            if item.get("href") or item.get("url")
        ]
        return hits, {"status": "ok", "result_count": len(hits)}
    except Exception as exc:  # pragma: no cover
        return [], {"status": "blocked_or_error", "error": str(exc)}


def run_katana(seed_urls: Iterable[str], *, depth: int, limit: int, timeout_seconds: int) -> tuple[list[str], dict[str, Any]]:
    binary = shutil.which("katana")
    if not binary:
        return [], {"status": "missing", "error": "katana not found on PATH"}
    urls: list[str] = []
    errors: list[str] = []
    start = time.time()
    for seed in list(seed_urls)[: max(1, limit)]:
        if len(urls) >= limit:
            break
        try:
            proc = subprocess.run(
                [binary, "-u", seed, "-silent", "-d", str(depth), "-timeout", str(timeout_seconds), "-retry", "0"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=max(timeout_seconds + 5, 10),
            )
            if proc.returncode != 0 and proc.stderr.strip():
                errors.append(proc.stderr.strip()[:300])
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line and line not in urls:
                    urls.append(line)
                    if len(urls) >= limit:
                        break
        except Exception as exc:  # pragma: no cover
            errors.append(str(exc))
    status = "ok" if urls or not errors else "blocked_or_error"
    return urls, {"status": status, "seed_count": len(list(seed_urls)), "url_count": len(urls), "duration_seconds": round(time.time() - start, 2), "errors": errors[:3]}


def write_text_capture(output_dir: Path, url: str, html: str, text: str, tool: str) -> PageCapture:
    raw_dir = output_dir / "raw_html"
    parsed_dir = output_dir / "parsed_text"
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    stem = safe_name(f"{urllib.parse.urlsplit(url).netloc}_{digest}")
    raw_path = raw_dir / f"{stem}.html"
    text_path = parsed_dir / f"{stem}.txt"
    raw_path.write_text(html, encoding="utf-8")
    text_path.write_text(text, encoding="utf-8")
    return PageCapture(
        url=canonical_url(url),
        status="captured" if text else "empty_text",
        title=html_title(html),
        text=text_preview(text, 800),
        raw_html_path=relative(raw_path),
        parsed_text_path=relative(text_path),
        tool=tool,
    )


def capture_fixture_pages(pages: dict[str, str], output_dir: Path, max_pages: int) -> tuple[dict[str, PageCapture], dict[str, Any]]:
    try:
        import trafilatura
    except Exception:  # pragma: no cover - optional dependency fallback
        trafilatura = None

    captures = {}
    for url, html in list(pages.items())[:max_pages]:
        if trafilatura is not None:
            text = trafilatura.extract(html) or ""
            tool = "fixture+trafilatura"
        else:
            text = ""
            tool = "fixture+html_regex"
        text = text or re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
        captures[canonical_url(url)] = write_text_capture(output_dir, url, html, text, tool)
    return captures, {"status": "ok", "captured": len(captures)}


def capture_http_pages(urls: Iterable[str], output_dir: Path, max_pages: int, timeout: float = 20.0) -> tuple[dict[str, PageCapture], dict[str, Any]]:
    try:
        import httpx
        import trafilatura
    except Exception as exc:  # pragma: no cover
        return {}, {"status": "missing", "error": str(exc)}

    captures: dict[str, PageCapture] = {}
    errors: list[str] = []
    with httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        for url in list(urls)[:max_pages]:
            try:
                response = client.get(url)
                response.raise_for_status()
                html = response.text
                text = trafilatura.extract(html, url=str(response.url)) or ""
                captures[canonical_url(url)] = write_text_capture(output_dir, url, html, text, "httpx+trafilatura")
            except Exception as exc:  # pragma: no cover
                errors.append(f"{url}: {exc}")
    status = "ok" if captures else ("blocked_or_error" if errors else "skipped")
    return captures, {"status": status, "captured": len(captures), "errors": errors[:5]}


async def _crawl4ai_one(url: str) -> tuple[str, str]:  # pragma: no cover - live integration only
    ensure_playwright_cache_env()
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(only_text=False, page_timeout=30000, word_count_threshold=1, verbose=False)
    async with AsyncWebCrawler(config=browser_config, base_directory=str(PROJECT_ROOT / ".crawl4ai")) as crawler:
        result = await crawler.arun(url=url, config=run_config)
    markdown = getattr(result, "markdown", "") or ""
    html = getattr(result, "html", "") or ""
    return html, str(markdown)


def capture_crawl4ai_pages(urls: Iterable[str], output_dir: Path, max_pages: int) -> tuple[dict[str, PageCapture], dict[str, Any]]:
    captures: dict[str, PageCapture] = {}
    errors: list[str] = []
    markdown_dir = output_dir / "crawl4ai_markdown"
    raw_dir = output_dir / "raw_html"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    for url in list(urls)[:max_pages]:
        try:
            html, markdown = asyncio.run(_crawl4ai_one(url))
            digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
            stem = safe_name(f"{urllib.parse.urlsplit(url).netloc}_{digest}")
            raw_path = raw_dir / f"{stem}_crawl4ai.html"
            md_path = markdown_dir / f"{stem}.md"
            raw_path.write_text(html, encoding="utf-8")
            md_path.write_text(markdown, encoding="utf-8")
            captures[canonical_url(url)] = PageCapture(
                url=canonical_url(url),
                status="captured" if markdown or html else "empty_text",
                title=html_title(html) or text_preview(markdown, 80),
                text=text_preview(markdown, 800),
                raw_html_path=relative(raw_path),
                markdown_path=relative(md_path),
                tool="crawl4ai",
            )
        except Exception as exc:  # pragma: no cover
            errors.append(f"{url}: {exc}")
    status = "ok" if captures else ("blocked_or_error" if errors else "skipped")
    return captures, {"status": status, "captured": len(captures), "errors": errors[:5]}


def merge_captures(primary: dict[str, PageCapture], secondary: dict[str, PageCapture]) -> dict[str, PageCapture]:
    merged = dict(primary)
    for url, capture in secondary.items():
        existing = merged.get(url)
        if not existing:
            merged[url] = capture
        elif capture.status == "captured" and (capture.markdown_path or len(capture.text) > len(existing.text)):
            merged[url] = capture
    return merged
