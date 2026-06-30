#!/usr/bin/env python3
"""Draft government tender pricing model with cash-risk realism."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


@dataclass
class GovPricingResult:
    base_cost_inr: float
    gst_inr: float
    direct_costs_inr: float
    emd_opportunity_cost_inr: float
    pbg_cost_inr: float
    working_capital_gap_days: int
    cash_gap_inr: float
    financing_cost_inr: float
    risk_buffers_inr: float
    margin_inr: float
    final_bid_price_inr: float
    l1_sensitivity: list[dict]


def pct(value: float, rate: float) -> float:
    return value * rate / 100


def l1_sensitivity_table(base_bid_price: float, total_cost: float) -> list[dict]:
    rows = []
    for undercut in [0, 5, 10, 15, 20]:
        competitor_price = base_bid_price * (1 - undercut / 100)
        margin = competitor_price - total_cost
        rows.append(
            {
                "scenario": f"competitor -{undercut}%" if undercut else "base bid price",
                "bid_price_inr": round(competitor_price, 2),
                "gross_margin_inr": round(margin, 2),
                "gross_margin_pct": round((margin / competitor_price * 100) if competitor_price else 0, 2),
                "cash_risk": "high" if margin <= 0 else "medium" if margin / competitor_price < 0.08 else "normal",
                "decision_warning": "loss_or_too_thin" if margin <= 0 or (competitor_price and margin / competitor_price < 0.08) else "acceptable",
            }
        )
    return rows


def calculate_gov_pricing(
    supplier_base_cost: float,
    gst_rate_pct: float = 18,
    freight: float = 0,
    packaging: float = 0,
    installation: float = 0,
    warranty_reserve: float = 0,
    documentation: float = 0,
    portal_fee: float = 0,
    document_fee: float = 0,
    bid_submission_fee: float = 0,
    emd_amount: float = 0,
    emd_lock_days: int = 0,
    pbg_amount: float = 0,
    pbg_charge_pct: float = 2,
    supplier_payment_day: int = 0,
    buyer_payment_day: int = 30,
    annual_financing_rate_pct: float = 18,
    payment_delay_buffer_pct: float = 3,
    penalty_risk_buffer_pct: float = 2,
    margin_pct: float = 15,
) -> GovPricingResult:
    gst = pct(supplier_base_cost, gst_rate_pct)
    direct = supplier_base_cost + gst + freight + packaging + installation + warranty_reserve + documentation + portal_fee + document_fee + bid_submission_fee
    emd_cost = emd_amount * (annual_financing_rate_pct / 100) * max(0, emd_lock_days) / 365
    pbg_cost = pct(pbg_amount, pbg_charge_pct)
    gap_days = max(0, buyer_payment_day - supplier_payment_day)
    cash_gap = direct
    financing = cash_gap * (annual_financing_rate_pct / 100) * gap_days / 365
    buffers = pct(direct, payment_delay_buffer_pct) + pct(direct, penalty_risk_buffer_pct)
    subtotal = direct + emd_cost + pbg_cost + financing + buffers
    margin = pct(subtotal, margin_pct)
    final = subtotal + margin
    return GovPricingResult(
        base_cost_inr=round(supplier_base_cost, 2),
        gst_inr=round(gst, 2),
        direct_costs_inr=round(direct, 2),
        emd_opportunity_cost_inr=round(emd_cost, 2),
        pbg_cost_inr=round(pbg_cost, 2),
        working_capital_gap_days=gap_days,
        cash_gap_inr=round(cash_gap, 2),
        financing_cost_inr=round(financing, 2),
        risk_buffers_inr=round(buffers, 2),
        margin_inr=round(margin, 2),
        final_bid_price_inr=round(final, 2),
        l1_sensitivity=l1_sensitivity_table(final, subtotal),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft GOV tender pricing")
    parser.add_argument("--supplier-base-cost", type=float, required=True)
    parser.add_argument("--emd-amount", type=float, default=0)
    parser.add_argument("--emd-lock-days", type=int, default=0)
    args = parser.parse_args()
    result = calculate_gov_pricing(args.supplier_base_cost, emd_amount=args.emd_amount, emd_lock_days=args.emd_lock_days)
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
