from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_compliance_categories_have_required_fields() -> None:
    data = yaml.safe_load((PROJECT_ROOT / "config" / "compliance_by_category.yaml").read_text(encoding="utf-8"))
    required = {
        "certificates_required",
        "issuing_authority",
        "lead_time_days",
        "cost_band_inr",
        "validity",
        "destination_specific_checks",
        "supplier_documents_needed",
        "buyer_documents_needed",
        "quote_impact",
        "hard_stop_conditions",
        "draft_only_warning",
    }
    categories = data["categories"]
    assert "Spices and condiments" in categories
    assert "Data entry / MIS dashboard / call centre" in categories
    for category, spec in categories.items():
        assert required.issubset(spec), category
        assert "draft" in spec["draft_only_warning"].lower() or "approval" in spec["draft_only_warning"].lower()
