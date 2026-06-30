"""Document download helper with evidence and hash tracking."""

from __future__ import annotations

import datetime as dt
import hashlib
import mimetypes
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    from scripts.source_adapters.base import SourceDocument
except ModuleNotFoundError:  # pragma: no cover
    from source_adapters.base import SourceDocument  # type: ignore

from .evidence_store import EvidenceStore, relative, safe_name


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def filename_from_url(url: str, fallback: str = "download") -> str:
    parsed = urlparse(url)
    name = unquote(Path(parsed.path).name)
    if not Path(name).suffix:
        guessed = mimetypes.guess_extension(mimetypes.guess_type(url)[0] or "") or ""
        name = f"{fallback}{guessed}"
    return safe_name(name or fallback)


class DocumentDownloader:
    def __init__(self, evidence: EvidenceStore, timeout_seconds: int = 120, max_file_size_mb: int = 100) -> None:
        self.evidence = evidence
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_file_size_mb * 1024 * 1024

    def _already_downloaded(self, digest: str) -> SourceDocument | None:
        for item in self.evidence.manifest.get("downloads", []):
            if item.get("sha256") == digest and item.get("local_path"):
                return SourceDocument(
                    document_id=digest[:16],
                    document_type=Path(item["local_path"]).suffix.lower().lstrip("."),
                    document_name=Path(item["local_path"]).name,
                    source_url=item.get("source_url", ""),
                    local_path=item["local_path"],
                    sha256=digest,
                    downloaded_at=item.get("downloaded_at", ""),
                )
        return None

    def download_url(self, url: str, filename: str = "") -> SourceDocument | None:
        target_name = safe_name(filename) if filename else filename_from_url(url)
        target = self.evidence.path_for("downloads", target_name)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "TenderExportOS/4.1 evidence downloader"})
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310 - configured source URLs only
                content = response.read(self.max_bytes + 1)
                if len(content) > self.max_bytes:
                    raise ValueError(f"file exceeds configured size limit: {self.max_bytes} bytes")
            target.write_bytes(content)
            digest = sha256_file(target)
            duplicate = self._already_downloaded(digest)
            if duplicate:
                target.unlink(missing_ok=True)
                return duplicate
            document = SourceDocument(
                document_id=digest[:16],
                document_type=target.suffix.lower().lstrip(".") or "unknown",
                document_name=target.name,
                source_url=url,
                local_path=relative(target),
                sha256=digest,
                downloaded_at=now_iso(),
            )
            self.evidence.record_download(document.to_dict())
            return document
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            self.evidence.record_download(
                {
                    "source_url": url,
                    "local_path": "",
                    "sha256": "",
                    "downloaded_at": now_iso(),
                    "status": "FAILED_OR_BLOCKED",
                    "error": str(exc),
                }
            )
            self.evidence.add_blocker("DOCUMENT_DOWNLOAD_FAILED_OR_BLOCKED", source_url=url, details=str(exc))
            return None
