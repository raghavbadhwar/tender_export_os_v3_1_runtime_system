#!/usr/bin/env python3
"""
score_opportunity.py
Score an opportunity from master_cases.csv using scoring_weights.yaml.

Usage:
    python scripts/score_opportunity.py --case_id GOV-20260630-001
    python scripts/score_opportunity.py --case_id EXP-20260630-001 --verbose
"""

import argparse
import csv
import datetime
import os

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Note: PyYAML not installed. Using hardcoded weights. Install: pip install pyyaml")

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'config')
MASTER_CASES_FILE = os.path.join(DATA_DIR, 'master_cases.csv')
SCORING_FILE = os.path.join(CONFIG_DIR, 'scoring_weights.yaml')
KILL_RULES_FILE = os.path.join(CONFIG_DIR, 'kill_rules.yaml')


# Hardcoded fallback weights (GOV)
GOV_WEIGHTS = {
    'eligibility_fit': 25,
    'capital_requirement': 15,
    'supplier_availability': 15,
    'pricing_clarity': 15,
    'execution_difficulty': 10,
    'competition_intensity': 10,
    'payment_risk': 5,
    'learning_value': 5,
}

# Hardcoded fallback weights (EXPORT)
EXPORT_WEIGHTS = {
    'buyer_credibility': 25,
    'supplier_availability': 20,
    'product_simplicity': 15,
    'pricing_clarity': 15,
    'compliance_difficulty': 10,
    'order_size_vs_risk': 10,
    'payment_safety': 5,
}


def truthy(value) -> bool:
    return str(value or '').strip().upper() in {'TRUE', 'YES', '1', 'Y'}


def number(value) -> float:
    try:
        return float(str(value or '0').replace(',', ''))
    except ValueError:
        return 0.0


def evaluate_trader_specific_kills(case: dict) -> dict:
    """Return trader-specific reject/watchlist decision without guessing missing evidence."""
    missing_evidence = []
    flags = []
    status = 'PASS'

    if truthy(case.get('manufacturer_only_tender')):
        flags.append('manufacturer_only_tender')
        status = 'REJECTED'
    if truthy(case.get('oem_required')) and not truthy(case.get('oem_authorization_available')):
        flags.append('authorized_dealer_or_oem_letter_missing')
        status = 'WATCHLIST' if not case.get('oem_authorization_available') else status
    if truthy(case.get('msme_reserved')) and not truthy(case.get('msme_eligible')):
        flags.append('mse_only_reservation_mismatch')
        status = 'WATCHLIST'
    if case.get('make_in_india_requirement') and not case.get('local_content_evidence'):
        flags.append('make_in_india_local_content_gap')
        status = 'WATCHLIST'
    if truthy(case.get('past_experience_required')) and not case.get('experience_details'):
        flags.append('past_same_or_similar_government_experience_missing')
        status = 'WATCHLIST'
    tender_value = number(case.get('estimated_value_inr'))
    turnover = number(case.get('turnover_required_inr'))
    if tender_value and turnover and turnover > tender_value * 5:
        flags.append('turnover_threshold_vs_tender_value_too_high')
        status = 'WATCHLIST'
    capital_exposure = sum(number(case.get(field)) for field in ['emd_amount_inr', 'portal_fee_inr', 'document_fee_inr', 'pbg_amount_inr'])
    max_capital = number(case.get('max_capital_exposure_inr') or 500000)
    if capital_exposure > max_capital:
        flags.append('emd_fee_pbg_exceeds_capital_limit')
        status = 'WATCHLIST'
    if 'l1' in (case.get('notes', '') + case.get('l1_sensitivity_summary', '')).lower() and 'commodity' in (case.get('category', '') + case.get('product_or_service', '')).lower():
        flags.append('l1_only_commodity_price_war')
        status = 'WATCHLIST'
    if number(case.get('delivery_days')) and number(case.get('delivery_days')) <= 3:
        flags.append('remote_delivery_short_timeline')
        status = 'WATCHLIST'
    if case.get('mandatory_certs') and not case.get('certificate_evidence'):
        flags.append('mandatory_iso_bis_unavailable')
        status = 'WATCHLIST'

    for field in ['oem_required', 'past_experience_required', 'turnover_required_inr', 'emd_amount_inr']:
        if case.get(field, '') == '':
            missing_evidence.append(field)
    if missing_evidence and status == 'PASS':
        status = 'WATCHLIST'
        flags.append('incomplete_evidence')

    return {
        'status': status,
        'flags': flags,
        'missing_evidence': missing_evidence,
        'reason': ', '.join(flags),
    }


def load_case(case_id: str) -> dict:
    """Load a case record from master_cases.csv."""
    with open(MASTER_CASES_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('case_id') == case_id:
                return row
    raise ValueError(f"Case ID not found: {case_id}")


def score_gov_opportunity(case: dict, verbose: bool = False) -> dict:
    """
    Score a government tender opportunity.
    Returns dict with factor scores and total.
    """
    scores = {}

    # 1. Eligibility Fit (0, 10, 18, 25)
    emd = float(case.get('emd_amount_inr', 0) or 0)
    past_exp_required = str(case.get('past_experience_required', 'FALSE')).upper() == 'TRUE'
    turnover_required = float(case.get('turnover_required_inr', 0) or 0)

    if not past_exp_required and turnover_required < 2500000:
        scores['eligibility_fit'] = 25
    elif not past_exp_required:
        scores['eligibility_fit'] = 18
    elif past_exp_required:
        scores['eligibility_fit'] = 10  # Gap exists
    else:
        scores['eligibility_fit'] = 0

    # 2. Capital Requirement (0, 5, 10, 15)
    if emd < 50000:
        scores['capital_requirement'] = 15
    elif emd < 500000:
        scores['capital_requirement'] = 10
    elif emd < 1000000:
        scores['capital_requirement'] = 5
    else:
        scores['capital_requirement'] = 0

    # 3. Supplier Availability — check if supplier search was done
    supplier_done = str(case.get('supplier_search_done', 'FALSE')).upper() == 'TRUE'
    scores['supplier_availability'] = 10 if supplier_done else 7

    # 4. Pricing Clarity
    pricing_done = str(case.get('pricing_done', 'FALSE')).upper() == 'TRUE'
    scores['pricing_clarity'] = 15 if pricing_done else 8

    # 5. Execution Difficulty (default medium)
    scores['execution_difficulty'] = 7

    # 6. Competition Intensity (default moderate)
    scores['competition_intensity'] = 7

    # 7. Payment Risk — check payment terms
    payment_terms = (case.get('payment_terms', '') or '').lower()
    if 'advance' in payment_terms:
        scores['payment_risk'] = 5
    elif '30 days' in payment_terms:
        scores['payment_risk'] = 3
    else:
        scores['payment_risk'] = 1

    # 8. Learning Value
    scores['learning_value'] = 3  # Default

    total = sum(scores.values())

    if verbose:
        print(f"\nGOV Scoring — {case['case_id']}")
        print("-" * 40)
        for factor, score in scores.items():
            max_score = GOV_WEIGHTS.get(factor, 0)
            bar = '█' * int((score / max_score) * 10) if max_score > 0 else ''
            print(f"  {factor:<25} {score:>3}/{max_score} {bar}")
        print("-" * 40)
        print(f"  {'TOTAL':<25} {total:>3}/100")

    return {'factor_scores': scores, 'total': total}


def score_export_opportunity(case: dict, verbose: bool = False) -> dict:
    """Score an export RFQ opportunity."""
    scores = {}

    buyer_score = float(case.get('buyer_credibility_score', 50) or 50)
    if buyer_score >= 80:
        scores['buyer_credibility'] = 25
    elif buyer_score >= 60:
        scores['buyer_credibility'] = 18
    elif buyer_score >= 40:
        scores['buyer_credibility'] = 10
    else:
        scores['buyer_credibility'] = 0

    supplier_done = str(case.get('supplier_search_done', 'FALSE')).upper() == 'TRUE'
    scores['supplier_availability'] = 14 if supplier_done else 10

    scomet = str(case.get('scomet_flag', 'FALSE')).upper()
    export_policy = case.get('export_policy', 'Free')
    if scomet == 'TRUE':
        scores['compliance_difficulty'] = 0
    elif export_policy == 'Free':
        scores['compliance_difficulty'] = 10
    else:
        scores['compliance_difficulty'] = 5

    scores['product_simplicity'] = 10  # Default medium
    scores['pricing_clarity'] = 10     # Default
    scores['order_size_vs_risk'] = 7   # Default

    payment_terms = (case.get('payment_terms', '') or '').lower()
    if 'lc' in payment_terms or '100%' in payment_terms.replace(' ', ''):
        scores['payment_safety'] = 5
    elif 'advance' in payment_terms:
        scores['payment_safety'] = 3
    else:
        scores['payment_safety'] = 1

    total = sum(scores.values())

    if verbose:
        print(f"\nEXPORT Scoring — {case['case_id']}")
        print("-" * 40)
        for factor, score in scores.items():
            max_score = EXPORT_WEIGHTS.get(factor, 0)
            bar = '█' * int((score / max_score) * 10) if max_score > 0 else ''
            print(f"  {factor:<25} {score:>3}/{max_score} {bar}")
        print("-" * 40)
        print(f"  {'TOTAL':<25} {total:>3}/100")

    return {'factor_scores': scores, 'total': total}


def main():
    parser = argparse.ArgumentParser(description='Score an opportunity')
    parser.add_argument('--case_id', required=True, help='Case ID to score')
    parser.add_argument('--verbose', action='store_true', help='Show factor breakdown')
    args = parser.parse_args()

    try:
        case = load_case(args.case_id)
    except ValueError as e:
        print(f"Error: {e}")
        return

    workflow = case.get('workflow_type', 'GOV').upper()

    print(f"\nScoring {args.case_id} ({workflow})")
    print(f"Opportunity: {case.get('opportunity_title', 'Unknown')}")
    print(f"Buyer: {case.get('buyer_name', 'Unknown')}")
    print(f"Deadline: {case.get('deadline_date', 'Unknown')} [{case.get('days_to_deadline', '?')} days]")

    if workflow == 'GOV':
        result = score_gov_opportunity(case, verbose=args.verbose)
    else:
        result = score_export_opportunity(case, verbose=args.verbose)
    trader_decision = evaluate_trader_specific_kills(case)

    total = result['total']
    print(f"\n{'='*40}")
    print(f"  SCORE: {total}/100", end=" ")

    if trader_decision['status'] == 'REJECTED':
        print(f"❌ REJECT — {trader_decision['reason']}")
    elif trader_decision['status'] == 'WATCHLIST':
        print(f"⚠️  WATCHLIST — {trader_decision['reason']}")
    elif total >= 60:
        print("✅ PROCEED — Deep Read")
    elif total >= 45:
        print("⚠️  WATCHLIST — Owner review")
    else:
        print("❌ REJECT")

    print(f"{'='*40}\n")


if __name__ == '__main__':
    main()
