from pathlib import Path

import yaml

from scripts.source_runtime.evidence_store import DEFAULT_EVIDENCE_ROOT

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_evidence_defaults_to_private_root() -> None:
    assert DEFAULT_EVIDENCE_ROOT.as_posix().endswith("outputs/evidence/private")


def test_deep_source_runtime_privacy_config() -> None:
    config = yaml.safe_load((PROJECT_ROOT / "config" / "deep_source_runtime.yaml").read_text(encoding="utf-8"))
    evidence = config["evidence"]
    assert evidence["mode"] == "private"
    assert evidence["allow_raw_html_commit"] is False
    assert evidence["allow_screenshot_commit"] is False
