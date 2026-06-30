"""Evidence bundle management for source runtime runs."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from .credential_policy import sanitize_payload

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVIDENCE_ROOT = PROJECT_ROOT / "outputs" / "evidence"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def safe_name(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())[:140].strip("._-")
    return cleaned or fallback


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


class EvidenceStore:
    """Creates and updates per-opportunity evidence manifests."""

    subdirs = ("raw_html", "screenshots", "downloads", "parsed_text", "extracted_json")

    def __init__(
        self,
        workflow_type: str,
        case_id: str,
        source_name: str,
        source_url: str,
        run_id: str,
        root: Path = DEFAULT_EVIDENCE_ROOT,
    ) -> None:
        self.workflow_type = safe_name(workflow_type or "UNKNOWN")
        self.case_id = safe_name(case_id or "TEMP")
        self.source_name = source_name
        self.source_url = source_url
        self.run_id = run_id
        self.base_dir = root / self.workflow_type / self.case_id
        for subdir in self.subdirs:
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.base_dir / "evidence_manifest.json"
        if self.manifest_path.exists():
            self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        else:
            self.manifest = {
                "case_id": case_id,
                "source_name": source_name,
                "source_url": source_url,
                "run_id": run_id,
                "created_at": now_iso(),
                "screenshots": [],
                "raw_html": [],
                "downloads": [],
                "parsed_text": [],
                "extracted_json": [],
                "blockers": [],
                "citations": [],
            }
            self.save()

    def path_for(self, subdir: str, filename: str) -> Path:
        if subdir not in self.subdirs:
            raise ValueError(f"Unsupported evidence subdir: {subdir}")
        return self.base_dir / subdir / safe_name(filename)

    def save(self) -> None:
        self.manifest_path.write_text(
            json.dumps(sanitize_payload(self.manifest), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _append_unique(self, key: str, value: Any) -> None:
        if value not in self.manifest[key]:
            self.manifest[key].append(value)
            self.save()

    def record_screenshot(self, path: Path, source_url: str = "") -> str:
        item = {"path": relative(path), "source_url": source_url or self.source_url, "captured_at": now_iso()}
        self._append_unique("screenshots", item)
        self.add_citation(relative(path))
        return relative(path)

    def record_raw_html(self, path: Path, source_url: str = "") -> str:
        item = {"path": relative(path), "source_url": source_url or self.source_url, "captured_at": now_iso()}
        self._append_unique("raw_html", item)
        self.add_citation(relative(path))
        return relative(path)

    def record_download(self, item: dict[str, Any]) -> None:
        self._append_unique("downloads", sanitize_payload(item))
        if item.get("local_path"):
            self.add_citation(str(item["local_path"]))

    def record_parsed_text(self, path: Path, source_path: str = "", confidence: str = "") -> str:
        item = {
            "path": relative(path),
            "source_path": source_path,
            "confidence": confidence,
            "created_at": now_iso(),
        }
        self._append_unique("parsed_text", item)
        self.add_citation(relative(path))
        return relative(path)

    def write_extracted_json(self, filename: str, payload: dict[str, Any]) -> str:
        path = self.path_for("extracted_json", filename)
        path.write_text(json.dumps(sanitize_payload(payload), indent=2, ensure_ascii=False), encoding="utf-8")
        item = {"path": relative(path), "created_at": now_iso()}
        self._append_unique("extracted_json", item)
        self.add_citation(relative(path))
        return relative(path)

    def add_blocker(self, reason: str, source_url: str = "", details: str = "") -> None:
        self._append_unique(
            "blockers",
            {
                "reason": reason,
                "source_url": source_url or self.source_url,
                "details": details,
                "human_action_required": True,
                "created_at": now_iso(),
            },
        )

    def add_citation(self, citation: str) -> None:
        if citation:
            self._append_unique("citations", citation)
