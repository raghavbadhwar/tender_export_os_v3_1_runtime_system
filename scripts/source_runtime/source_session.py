"""Source session configuration helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "deep_source_runtime.yaml"


@dataclass
class SourceSessionConfig:
    headless_default: bool = False
    max_results_per_source: int = 25
    max_deep_reads_per_source: int = 10
    timeout_seconds: int = 60
    download_timeout_seconds: int = 120
    external_side_effects_allowed: bool = False


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else {}


def load_runtime_config(path: Path = DEFAULT_CONFIG) -> SourceSessionConfig:
    data = _load_yaml(path)
    runtime = data.get("runtime", {}) if isinstance(data, dict) else {}
    return SourceSessionConfig(
        headless_default=bool(runtime.get("headless_default", False)),
        max_results_per_source=int(runtime.get("max_results_per_source", 25)),
        max_deep_reads_per_source=int(runtime.get("max_deep_reads_per_source", 10)),
        timeout_seconds=int(runtime.get("timeout_seconds", 60)),
        download_timeout_seconds=int(runtime.get("download_timeout_seconds", 120)),
        external_side_effects_allowed=bool(runtime.get("external_side_effects_allowed", False)),
    )
