from scripts.export_landed_cost_calculator import calculate_export_landed_cost


def test_export_landed_cost_calculates_exw_fob_cif() -> None:
    result = calculate_export_landed_cost(
        supplier_base_usd=1000,
        packaging_usd=50,
        inland_freight_usd=100,
        cha_docs_usd=75,
        port_handling_usd=50,
        international_freight_usd=300,
        insurance_usd=25,
    )
    assert result.exw_usd == 1050
    assert result.fob_usd > result.exw_usd
    assert result.cif_usd > result.fob_usd
    assert result.quote_warning == "draft_internal_price_only"
