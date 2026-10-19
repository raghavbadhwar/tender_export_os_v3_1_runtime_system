#!/usr/bin/env python3
"""Draft export EXW/FOB/CIF landed-cost calculator."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


@dataclass
class ExportPricingResult:
    exw_usd: float
    fob_usd: float
    cif_usd: float
    bank_charges_usd: float
    inspection_certification_usd: float
    sample_cost_usd: float
    currency_buffer_usd: float
    payment_risk_usd: float
    minimum_viable_order_size_usd: float
    quote_warning: str


def calculate_export_landed_cost(
    supplier_base_usd: float,
    packaging_usd: float = 0,
    inland_freight_usd: float = 0,
    cha_docs_usd: float = 0,
    port_handling_usd: float = 0,
    international_freight_usd: float = 0,
    insurance_usd: float = 0,
    bank_charges_pct: float = 1,
    inspection_certification_usd: float = 0,
    sample_cost_usd: float = 0,
    currency_buffer_pct: float = 3,
    payment_risk_pct: float = 2,
    minimum_viable_order_size_usd: float = 1000,
) -> ExportPricingResult:
    exw = supplier_base_usd + packaging_usd
    fob_base = exw + inland_freight_usd + cha_docs_usd + port_handling_usd
    bank = fob_base * bank_charges_pct / 100
    currency_buffer = fob_base * currency_buffer_pct / 100
    payment_risk = fob_base * payment_risk_pct / 100
    fob = fob_base + bank + inspection_certification_usd + sample_cost_usd + currency_buffer + payment_risk
    cif = fob + international_freight_usd + insurance_usd
    warning = "below_minimum_viable_order" if cif < minimum_viable_order_size_usd else "draft_internal_price_only"
    return ExportPricingResult(
        exw_usd=round(exw, 2),
        fob_usd=round(fob, 2),
        cif_usd=round(cif, 2),
        bank_charges_usd=round(bank, 2),
        inspection_certification_usd=round(inspection_certification_usd, 2),
        sample_cost_usd=round(sample_cost_usd, 2),
        currency_buffer_usd=round(currency_buffer, 2),
        payment_risk_usd=round(payment_risk, 2),
        minimum_viable_order_size_usd=round(minimum_viable_order_size_usd, 2),
        quote_warning=warning,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft export landed-cost pricing")
    parser.add_argument("--supplier-base-usd", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(asdict(calculate_export_landed_cost(args.supplier_base_usd)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
