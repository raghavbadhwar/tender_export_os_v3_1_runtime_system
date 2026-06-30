from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_shipment_import_profiles_are_manual_or_licensed_only() -> None:
    paths = sorted((PROJECT_ROOT / "config" / "shipment_import_profiles").glob("*.yaml"))
    assert {path.stem for path in paths} == {"volza", "panjiva", "importgenius", "tradeimex"}
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["access_model"] == "licensed_or_manual_export_only"
        assert "paywall_bypass" in data["forbidden"]
        assert "buyer_name" in data["required_fields"]
