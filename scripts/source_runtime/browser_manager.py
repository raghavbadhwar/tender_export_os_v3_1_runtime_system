"""Playwright persistent browser manager with blocker detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from scripts.source_adapters.base import SourceBlocked
except ModuleNotFoundError:  # pragma: no cover
    from source_adapters.base import SourceBlocked  # type: ignore

from .evidence_store import EvidenceStore, DEFAULT_EVIDENCE_ROOT, relative, safe_name
from .blocker_assessment import assess_blockers

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_ROOT = PROJECT_ROOT / ".local" / "browser_profiles"


class BrowserManager:
    def __init__(self, source_slug: str = "", evidence: EvidenceStore | None = None) -> None:
        self.source_slug = safe_name(source_slug or "source")
        self.evidence = evidence
        self._playwright: Any = None
        self._context: Any = None

    def open_context(self, source_slug: str | None = None, headless: bool = False):
        slug = safe_name(source_slug or self.source_slug)
        PROFILE_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # pragma: no cover - depends on local optional install
            raise SourceBlocked(slug, "CODEX_RUNTIME_OR_PLAYWRIGHT_UNAVAILABLE", True, str(exc)) from exc
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            str(PROFILE_ROOT / slug),
            headless=headless,
            accept_downloads=True,
            viewport={"width": 1440, "height": 1000},
        )
        return self._context

    def close_context(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def new_page(self):
        if self._context is None:
            self.open_context(headless=False)
        return self._context.new_page()

    def save_screenshot(self, page, case_id: str, name: str, evidence: EvidenceStore | None = None) -> str:
        store = evidence or self.evidence
        if store:
            path = store.path_for("screenshots", f"{name}.png")
        else:
            path = DEFAULT_EVIDENCE_ROOT / "UNKNOWN" / safe_name(case_id) / "screenshots" / f"{safe_name(name)}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=True)
        if store:
            return store.record_screenshot(path, getattr(page, "url", ""))
        return relative(path)

    def save_raw_html(self, page, case_id: str, name: str, evidence: EvidenceStore | None = None) -> str:
        store = evidence or self.evidence
        html = page.content()
        if store:
            path = store.path_for("raw_html", f"{name}.html")
        else:
            path = DEFAULT_EVIDENCE_ROOT / "UNKNOWN" / safe_name(case_id) / "raw_html" / f"{safe_name(name)}.html"
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        if store:
            return store.record_raw_html(path, getattr(page, "url", ""))
        return relative(path)

    def detect_blockers(self, page, source: str | None = None) -> None:
        assessment = assess_blockers(page)
        if self.evidence:
            for label in assessment.get("forbidden_action_elements", []):
                self.evidence.add_blocker("FORBIDDEN_ACTION_ELEMENT_PRESENT", source_url=getattr(page, "url", ""), details=label)
        hard = assessment.get("hard_blockers", [])
        if hard:
            reason = "_".join(str(hard[0]).upper().split())
            if self.evidence:
                self.evidence.add_blocker(reason, source_url=getattr(page, "url", ""))
            raise SourceBlocked(source or self.source_slug, reason, True)

    def __enter__(self) -> "BrowserManager":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        self.close_context()
