#!/usr/bin/env python3
"""
generate_daily_brief.py
Reads all data files and generates the HTML daily brief.

Usage:
    python scripts/generate_daily_brief.py
    python scripts/generate_daily_brief.py --date 20260630
    python scripts/generate_daily_brief.py --open  # Opens in browser after generating
"""

import argparse
import csv
import datetime
import html
import os
import subprocess
import sys
import webbrowser

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.abspath(PROJECT_ROOT))

from scripts.approval_lifecycle import classify_approval

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'templates')
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, 'outputs', 'daily_briefs')

MASTER_CASES_FILE = os.path.join(DATA_DIR, 'master_cases.csv')
APPROVALS_FILE = os.path.join(DATA_DIR, 'approvals_receipts.csv')
SOURCE_HEALTH_FILE = os.path.join(DATA_DIR, 'source_health.csv')
RUN_LOG_FILE = os.path.join(DATA_DIR, 'agent_run_log.csv')
PLUGIN_HEALTH_FILE = os.path.join(DATA_DIR, 'plugin_health.csv')
RFQ_MASTER_FILE = os.path.join(DATA_DIR, 'rfq_master.csv')
TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, 'daily_brief.html')

ACTIVE_STATUSES = [
    'DEEP_READ',
    'SUPPLIER_SEARCH',
    'PRICING_READY',
    'ARTIFACT_PRODUCTION',
    'APPROVAL_REQUIRED',
    'APPROVED',
    'SENT_OR_SUBMITTED',
    'FOLLOW_UP',
]

SOURCE_ISSUE_STATUSES = {
    'Needs Login',
    'Paywalled',
    'Broken',
    'Manual Check Required',
    'Blocked by CAPTCHA',
    'Restricted / Do Not Scrape',
}


def load_csv(filepath):
    """Load a CSV file and return list of dicts."""
    rows = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        pass
    return rows


def compact_date_to_iso(date_str):
    """Convert YYYYMMDD to YYYY-MM-DD; pass through ISO dates."""
    if not date_str:
        return datetime.date.today().isoformat()
    if len(date_str) == 8 and date_str.isdigit():
        return datetime.datetime.strptime(date_str, '%Y%m%d').date().isoformat()
    return date_str


def esc(value):
    return html.escape(str(value if value is not None else ''), quote=True)


def get_action(approval):
    return approval.get('proposed_action') or approval.get('action_approved') or approval.get('action') or 'Approval required'


def get_amount(approval, case=None):
    workflow = (approval.get('workflow_type') if approval else '') or (case.get('workflow_type') if case else '')
    if approval.get('amount_or_price'):
        return approval['amount_or_price']
    if workflow == 'EXPORT' and approval.get('amount_usd'):
        return f"${approval['amount_usd']}"
    if approval.get('amount_inr'):
        return f"₹{approval['amount_inr']}"
    if approval.get('amount_usd'):
        return f"${approval['amount_usd']}"
    if case:
        if workflow == 'EXPORT' and case.get('estimated_value_usd'):
            return f"${case['estimated_value_usd']}"
        if case.get('estimated_value_inr'):
            return f"₹{case['estimated_value_inr']}"
        if case.get('estimated_value_usd'):
            return f"${case['estimated_value_usd']}"
    return 'N/A'


def get_todays_stats(cases, run_log, today_str):
    """Compute stats for today's brief."""
    today_iso = compact_date_to_iso(today_str)
    today_cases = [c for c in cases if c.get('created_at', '').startswith(today_iso)]
    gov_new = sum(1 for c in today_cases if c.get('workflow_type') == 'GOV')
    export_new = sum(1 for c in today_cases if c.get('workflow_type') == 'EXPORT')
    rejected = sum(1 for c in today_cases if c.get('status') in ['REJECTED', 'FAST_KILL'])

    return {
        'gov_new': gov_new,
        'export_new': export_new,
        'rejected_count': rejected
    }


def _date_value(value):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value[:10])
    except ValueError:
        return None


def _score_value(case):
    score = case.get('score_gov', '') or case.get('score_export', '')
    try:
        return float(score)
    except (TypeError, ValueError):
        return None


def get_trailing_30_day_metrics(cases, approvals, source_health, today_str):
    """Compute compact trailing metrics for owner context."""
    today = datetime.datetime.strptime(today_str, '%Y%m%d').date() if today_str and len(today_str) == 8 else datetime.date.today()
    start = today - datetime.timedelta(days=30)

    def in_window(value):
        parsed = _date_value(value)
        return bool(parsed and start <= parsed <= today)

    recent_cases = [case for case in cases if in_window(case.get('created_at') or case.get('updated_at'))]
    scores = [score for score in (_score_value(case) for case in recent_cases) if score is not None]
    now = datetime.datetime.combine(today, datetime.time(23, 59), tzinfo=datetime.timezone.utc)
    expired = sum(1 for approval in approvals if classify_approval(approval, now=now).get('expired'))
    return {
        'created': len(recent_cases),
        'rejected': sum(1 for case in recent_cases if case.get('status') in {'REJECTED', 'FAST_KILL'}),
        'won': sum(1 for case in recent_cases if case.get('status') == 'WON'),
        'lost': sum(1 for case in recent_cases if case.get('status') == 'LOST'),
        'pending_approvals': sum(1 for approval in approvals if approval.get('approval_status') == 'PENDING'),
        'expired_approvals': expired,
        'source_issues': len(get_source_issues(source_health)),
        'average_score': round(sum(scores) / len(scores), 1) if scores else 'N/A',
    }


def render_trailing_metrics(metrics):
    labels = [
        ('Created', 'created'),
        ('Rejected', 'rejected'),
        ('Pending approvals', 'pending_approvals'),
        ('Expired approvals', 'expired_approvals'),
        ('Won/Lost', 'won_lost'),
        ('Source issues', 'source_issues'),
        ('Avg score', 'average_score'),
    ]
    enriched = dict(metrics)
    enriched['won_lost'] = f"{metrics['won']}/{metrics['lost']}"
    return ''.join(
        f'<div class="metric-pill"><span>{esc(label)}</span><strong>{esc(enriched[key])}</strong></div>'
        for label, key in labels
    )


def get_best_opportunities(cases, top_n=3):
    """Get top N cases by score."""
    active_cases = [c for c in cases if c.get('status') in ACTIVE_STATUSES]

    def get_score(case):
        score = case.get('score_gov', '') or case.get('score_export', '') or '0'
        try:
            return float(score)
        except (ValueError, TypeError):
            return 0

    sorted_cases = sorted(active_cases, key=get_score, reverse=True)
    return sorted_cases[:top_n]


def get_pending_approvals(approvals):
    """Get all pending approval items."""
    return [a for a in approvals if a.get('approval_status', '').upper() == 'PENDING']


def get_source_issues(source_health):
    """Get sources with issues."""
    return [s for s in source_health if s.get('health_status', '') in SOURCE_ISSUE_STATUSES]


def get_plugin_issues(plugin_health):
    """Get plugins/tools with blockers or non-working health.

    A tool can still be marked Working while carrying a non-empty blocker/warning
    field, e.g. a Drive command that succeeded but emitted an auth-cache warning.
    Surface those in the owner brief so operational risks are not hidden.
    """
    return [
        p for p in plugin_health
        if p.get('health_status', '') not in {'Working', ''} or (p.get('blocker') or '').strip()
    ]


def get_upcoming_deadlines(cases, days_threshold=14):
    """Get cases with deadlines within threshold days."""
    urgent = []
    today = datetime.date.today()
    for case in cases:
        deadline_str = case.get('deadline_date', '')
        if deadline_str:
            try:
                deadline = datetime.date.fromisoformat(deadline_str)
                days_left = (deadline - today).days
                if 0 < days_left <= days_threshold:
                    case['_days_left'] = days_left
                    urgent.append(case)
            except ValueError:
                pass
    return sorted(urgent, key=lambda x: x.get('_days_left', 999))


def render_case_card_html(case):
    """Render an HTML case card."""
    workflow = case.get('workflow_type', 'GOV')
    score = case.get('score_gov', '') or case.get('score_export', '') or '—'
    deadline = case.get('deadline_date', '—')
    days = case.get('days_to_deadline', '?')
    status = case.get('status', '')

    badge_class = 'badge-gov' if workflow == 'GOV' else 'badge-exp'
    if workflow == 'GOV':
        value = case.get('estimated_value_inr', '') or '—'
        value_prefix = '₹' if value != '—' else ''
    else:
        value = case.get('estimated_value_usd', '') or '—'
        value_prefix = '$' if value != '—' else ''
    deadline_display = deadline if deadline else 'N/A'
    days_display = f" [{days} days]" if days else ''

    return f"""
    <div class="case-card">
      <div class="case-id">{esc(case['case_id'])} · <span class="score-badge">{esc(score)}/100</span>
        <span class="{badge_class}">{workflow}</span></div>
      <div class="case-title">{esc(case.get('opportunity_title', 'Unknown'))}</div>
      <div class="case-meta">
        <span>Buyer: {esc(case.get('buyer_name', '—'))}</span>
        <span>Value: {value_prefix}{esc(value)}</span>
        <span>Deadline: {esc(deadline_display)}{esc(days_display)}</span>
        <span>Status: {esc(status)}</span>
      </div>
      <div class="next-step">Next: {esc(next_step_for_case(case))}</div>
    </div>"""


def next_step_for_case(case):
    status = case.get('status', '')
    if status == 'DEEP_READ':
        return 'Complete extraction, then move to supplier search if evidence supports it.'
    if status == 'SUPPLIER_SEARCH':
        return 'Finish 5-3-2 supplier proof and create approval card before quote requests.'
    if status == 'PRICING_READY':
        return 'Produce draft artifacts through Codex runtime.'
    if status == 'ARTIFACT_PRODUCTION':
        return 'Validate pack artifacts and create approval card for any external action.'
    if status == 'APPROVAL_REQUIRED':
        return 'Owner decision required: Approve, Reject, or Ask Changes.'
    if status == 'APPROVED':
        return 'Execution tracker may proceed only within the approved action scope.'
    if status == 'FOLLOW_UP':
        return 'Track reply, validity, deadline, payment, or document receipt.'
    return 'Review status and route to the next valid internal step.'


def render_pending_supplier_proof(cases):
    rows = [c for c in cases if c.get('status') == 'SUPPLIER_SEARCH']
    if not rows:
        return '<p style="color:#94a3b8">No cases currently waiting at supplier proof stage.</p>'
    return ''.join(
        f'<div class="risk-item"><span class="risk-label">{esc(c.get("case_id"))}</span>: '
        f'{esc(c.get("product_or_service", "Supplier proof"))} — 5-3-2 proof pending.</div>'
        for c in rows
    )


def get_verified_buyer_demand(rfqs):
    return [
        rfq for rfq in rfqs
        if rfq.get('rfq_stage') in {'RFQ_VERIFIED', 'READY_FOR_SUPPLIER_PROOF'}
        and rfq.get('evidence_status') == 'RFQ_VERIFIED'
    ]


def get_weak_buyer_leads(rfqs):
    return [
        rfq for rfq in rfqs
        if rfq.get('rfq_stage') in {'RAW_LEAD', 'BUYER_VISIBLE', 'BLOCKED'}
        or rfq.get('evidence_status') in {'MISSING', 'MARKETPLACE_MASKED', 'PARTIAL'}
    ]


def render_verified_buyer_demand(rfqs):
    rows = get_verified_buyer_demand(rfqs)
    if not rows:
        return '<p style="color:#94a3b8">No RFQ-verified buyer demand. Weak marketplace leads are not counted as demand.</p>'
    cards = []
    for rfq in sorted(rows, key=lambda row: float(row.get('rfq_score') or 0), reverse=True)[:5]:
        cards.append(f"""
    <div class="case-card">
      <div class="case-id">{esc(rfq.get('case_id'))} · <span class="score-badge">{esc(rfq.get('rfq_score'))}/100</span>
        <span class="badge-exp">RFQ VERIFIED</span></div>
      <div class="case-title">{esc(rfq.get('product_or_service', 'Verified RFQ'))}</div>
      <div class="case-meta">
        <span>Country: {esc(rfq.get('buyer_country', '—'))}</span>
        <span>Deadline: {esc(rfq.get('deadline_date', '—'))}</span>
        <span>Source: {esc(rfq.get('source_name', '—'))}</span>
      </div>
      <div class="next-step">Next: supplier proof may begin only inside approval-gated workflow discipline.</div>
    </div>""")
    return '\n'.join(cards)


def render_approval_cards(approvals, cases_by_id):
    if not approvals:
        return '<p style="color:#94a3b8">No pending approvals.</p>'
    cards = []
    for approval in approvals:
        case_id = approval.get('case_id', '')
        case = cases_by_id.get(case_id, {})
        action = get_action(approval)
        amount = get_amount(approval, case)
        benefit = approval.get('expected_benefit') or approval.get('notes') or 'Benefit not fully quantified in approval register.'
        risk = approval.get('concrete_risk') or 'Risk note missing; owner should ask changes before approving if this matters.'
        recovery = approval.get('recovery_rollback_path') or 'Recovery path missing; owner should ask changes before approving if this matters.'
        cards.append(f"""
    <div class="approval-card">
      <div class="action-label">Action Required</div>
      <div class="case-title" style="margin: 6px 0">{esc(case_id)} — {esc(action)}</div>
      <div style="font-size:13px; color:#94a3b8; margin-bottom:12px">
        <strong>Amount:</strong> {esc(amount)} ·
        <strong>Benefit:</strong> {esc(benefit)} ·
        <strong>Risk:</strong> {esc(risk)} ·
        <strong>Recovery:</strong> {esc(recovery)}
      </div>
      <span class="approve-btn">Approve</span>
      <span class="approve-btn reject-btn">Reject</span>
      <span class="approve-btn changes-btn">Ask Changes</span>
      <div style="font-size:11px; color:#64748b; margin-top:8px">Say: "approve case {esc(case_id)}" in Hermes</div>
    </div>""")
    return '\n'.join(cards)


def render_risks(source_issues, plugin_issues, urgent_deadlines, cases, rfqs=None):
    items = []
    rfqs = rfqs or []
    for source in source_issues:
        items.append(('Source', f"{source.get('source_name', 'Unknown source')} — {source.get('health_status', '')}. {source.get('notes', '')}"))
    for plugin in plugin_issues:
        items.append(('Plugin', f"{plugin.get('plugin_or_tool', 'Unknown tool')} — {plugin.get('health_status', '')}. {plugin.get('blocker') or plugin.get('notes', '')}"))
    for case in urgent_deadlines:
        items.append(('Deadline', f"{case.get('case_id')} — {case.get('opportunity_title', '')}: {case.get('_days_left')} days left."))
    for case in cases:
        if case.get('source_name') == 'Recovered local registers' or (case.get('status') in ACTIVE_STATUSES and not case.get('source_url')):
            items.append(('Evidence', f"{case.get('case_id')} — source URL or buyer evidence is incomplete; ask changes before external action."))
        if case.get('status') == 'SUPPLIER_SEARCH':
            items.append(('Supplier', f"{case.get('case_id')} — Supplier proof pending before pricing."))
        if case.get('scomet_flag', '').upper() == 'TRUE':
            items.append(('Compliance', f"{case.get('case_id')} — SCOMET flag suspected. Stop for specialist review."))
    for rfq in get_weak_buyer_leads(rfqs):
        items.append((
            'Buyer demand',
            f"{rfq.get('case_id')} — {rfq.get('rfq_stage')} / {rfq.get('evidence_status')}; missing: {rfq.get('missing_evidence')}"
        ))
    if not items:
        return '<p style="color:#94a3b8">No active risks found in local registers.</p>'
    return '\n'.join(
        f'<div class="risk-item"><div class="risk-label">{esc(label)}</div>{esc(text)}</div>'
        for label, text in items[:12]
    )


def generate_brief(date_str=None, send_gateway=False, gateway='telegram', log_run=True):
    """Generate the full HTML brief for the given date."""
    if date_str is None:
        date_str = datetime.date.today().strftime('%Y%m%d')

    today_display = datetime.datetime.strptime(date_str, '%Y%m%d').strftime('%B %d, %Y')
    now_display = datetime.datetime.now().strftime('%H:%M IST')

    # Load data
    cases = load_csv(MASTER_CASES_FILE)
    approvals = load_csv(APPROVALS_FILE)
    source_health = load_csv(SOURCE_HEALTH_FILE)
    run_log = load_csv(RUN_LOG_FILE)
    plugin_health = load_csv(PLUGIN_HEALTH_FILE)
    rfqs = load_csv(RFQ_MASTER_FILE)

    # Compute data
    stats = get_todays_stats(cases, run_log, date_str)
    best_opps = get_best_opportunities(cases)
    pending_approvals = get_pending_approvals(approvals)
    source_issues = get_source_issues(source_health)
    plugin_issues = get_plugin_issues(plugin_health)
    urgent_deadlines = get_upcoming_deadlines(cases)
    cases_by_id = {case.get('case_id'): case for case in cases}
    trailing_metrics = get_trailing_30_day_metrics(cases, approvals, source_health, date_str)

    # Load template
    try:
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            html = f.read()
    except FileNotFoundError:
        print(f"Warning: Template not found at {TEMPLATE_FILE}. Using minimal template.")
        html = "<html><body>{{DATE}} — Brief data loaded successfully.</body></html>"

    # Build case cards HTML
    case_cards_html = '\n'.join(render_case_card_html(c) for c in best_opps) if best_opps else \
        '<p style="color:#64748b">No active cases meeting threshold. Run Radar scan to find new opportunities.</p>'

    # Build rejection reasons HTML
    rejection_reasons_html = ''
    reason_counts = {}
    for case in cases:
        if case.get('status') == 'REJECTED' and case.get('created_at', '').startswith(compact_date_to_iso(date_str)):
            reason = case.get('kill_reason', 'UNKNOWN')
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        rejection_reasons_html += f'<div class="risk-item"><span class="risk-label">{reason}</span>: {count} case(s)</div>\n'

    # Recommended action
    if pending_approvals:
        rec = f"Review and decide on approval card for {pending_approvals[0].get('case_id', '?')} — action required."
    elif urgent_deadlines:
        d = urgent_deadlines[0]
        rec = f"Check status of {d.get('case_id','?')} — deadline in {d.get('_days_left','?')} days."
    else:
        rec = "No urgent actions today. Consider running a manual source scan to discover new opportunities."

    # Replace template placeholders
    replacements = {
        '{{DATE}}': today_display,
        '{{TIME}}': now_display,
        '{{GOV_NEW}}': str(stats['gov_new']),
        '{{EXPORT_NEW}}': str(stats['export_new']),
        '{{REJECTED_COUNT}}': str(stats['rejected_count']),
        '{{REJECTION_REASONS}}': rejection_reasons_html,
        '{{BEST_OPPORTUNITIES}}': case_cards_html,
        '{{VERIFIED_BUYER_DEMAND}}': render_verified_buyer_demand(rfqs),
        '{{PENDING_SUPPLIER_PROOF}}': render_pending_supplier_proof(cases),
        '{{APPROVAL_REQUIRED}}': render_approval_cards(pending_approvals, cases_by_id),
        '{{RISKS_BLOCKERS}}': render_risks(source_issues, plugin_issues, urgent_deadlines, cases, rfqs),
        '{{RECOMMENDED_ACTION}}': rec,
        '{{TRAILING_30_METRICS}}': render_trailing_metrics(trailing_metrics),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # Save
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUTS_DIR, f'brief_{date_str}.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    if log_run:
        log_brief_generation(date_str, output_path, len(pending_approvals), len(source_issues) + len(plugin_issues))

    if send_gateway:
        send_gateway_brief(
            cases,
            approvals,
            source_health,
            run_log,
            stats,
            best_opps,
            source_issues,
            urgent_deadlines,
            pending_approvals,
            today_display,
            gateway,
        )

    return output_path


def send_gateway_brief(cases, approvals, source_health, run_log, stats, best_opps, source_issues, urgent_deadlines, pending_approvals, date_display, gateway):
    """Compile and send a text version of the daily brief through an explicitly requested Hermes gateway."""
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f" TODAY'S OWNER BRIEF — {date_display}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("1. NEW OPPORTUNITIES SCANNED")
    lines.append(f"   GOV: {stats['gov_new']} new tenders")
    lines.append(f"   EXPORT: {stats['export_new']} new RFQs")
    
    total_sources = len(source_health)
    failed_sources = len(source_issues)
    lines.append(f"   Sources checked: {total_sources} | Failed: {failed_sources}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("2. AUTO-REJECTED TODAY")
    lines.append(f"   Count: {stats['rejected_count']}")
    
    reason_counts = {}
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    for case in cases:
        if case.get('status') == 'REJECTED' and case.get('created_at', '').startswith(today_str):
            reason = case.get('kill_reason', 'UNKNOWN')
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
    if reason_counts:
        lines.append("   Reasons:")
        for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
            lines.append(f"   • {reason}: {count} case(s)")
    else:
        lines.append("   Nothing to report")
        
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("3. BEST OPPORTUNITIES")
    lines.append("")
    
    for case in best_opps:
        workflow = case.get('workflow_type', 'GOV')
        score = case.get('score_gov', '') or case.get('score_export', '') or '—'
        deadline = case.get('deadline_date', '—')
        days = case.get('days_to_deadline', '?')
        value = case.get('estimated_value_inr', '') or case.get('estimated_value_usd', '') or '—'
        value_prefix = '₹' if workflow == 'GOV' else '$'
        
        lines.append(f"   {case['case_id']} — {case.get('opportunity_title', 'Unknown')}")
        lines.append(f"   Workflow: {workflow} | Score: {score}/100")
        lines.append(f"   Value: {value_prefix}{value} | Deadline: {deadline} [{days} days]")
        lines.append(f"   ↳ Next: {case.get('status', 'NEW')} stage")
        lines.append("")
        
    if not best_opps:
        lines.append("   Nothing to report\n")
        
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("4. PENDING SUPPLIER PROOF")
    pending_quotes_lines = []
    for case in cases:
        if case.get('status') == 'SUPPLIER_SEARCH':
            pending_quotes_lines.append(f"   {case['case_id']}: supplier proof pending")
    if pending_quotes_lines:
        lines.extend(pending_quotes_lines)
    else:
        lines.append("   Nothing to report")
        
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("5. APPROVAL REQUIRED")
    lines.append("")
    
    if pending_approvals:
        for app in pending_approvals:
            lines.append(f"   {app.get('case_id')} — {get_action(app)}")
            lines.append(f"   Amount: {get_amount(app)}")
            lines.append(f"   Benefit: {app.get('expected_benefit') or app.get('notes') or 'N/A'}")
            lines.append(f"   Risk: {app.get('concrete_risk', 'N/A')}")
            lines.append(f"   Recovery: {app.get('recovery_rollback_path', 'N/A')}")
            lines.append(f"   Decide by: {app.get('deadline_date', 'N/A')}")
            lines.append(f"   → Say: approve case {app.get('case_id')}")
            lines.append("")
    else:
        lines.append("   Nothing to report\n")
        
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("6. RISKS & BLOCKERS")
    has_risks = False
    if failed_sources:
        lines.append(f"   Sources: {failed_sources} source(s) failing")
        has_risks = True
    if urgent_deadlines:
        lines.append(f"   Deadlines: {len(urgent_deadlines)} cases near deadline")
        has_risks = True
    if not has_risks:
        lines.append("   Nothing to report")
        
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")
    
    # Recommended Action
    if pending_approvals:
        rec = f"Review and decide on approval card for {pending_approvals[0].get('case_id', '?')} — action required."
    elif urgent_deadlines:
        d = urgent_deadlines[0]
        rec = f"Check status of {d.get('case_id','?')} — deadline in {d.get('_days_left','?')} days."
    else:
        rec = "No urgent actions today. Consider running a manual source scan."
        
    lines.append("7. RECOMMENDED ACTION TODAY")
    lines.append(f"   ⭐ {rec}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    text_brief = "\n".join(lines)
    
    try:
        subprocess.run(
            ["/Users/raghav/.ares/bin/ares-hermes", "send", "--to", gateway],
            input=text_brief,
            text=True,
            check=True,
            capture_output=True
        )
        print(f"  Daily brief pushed to {gateway}.")
    except Exception as e:
        print(f"  Failed to push brief to {gateway}: {e}")


def log_brief_generation(date_str, output_path, approvals_count, risk_count):
    """Append an owner-briefing run row."""
    file_exists = os.path.exists(RUN_LOG_FILE)
    run_id = f"RUN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    row = {
        'run_id': run_id,
        'run_date': compact_date_to_iso(date_str),
        'run_time': datetime.datetime.now().strftime('%H:%M:%S'),
        'agent_name': 'owner_briefing_agent',
        'trigger_type': 'manual_or_cron',
        'cases_processed': 0,
        'cases_created': 0,
        'cases_rejected': 0,
        'cases_updated': 0,
        'sources_checked': 0,
        'sources_failed': 0,
        'actions_taken': 'generate_daily_brief',
        'approval_cards_created': 0,
        'receipts_created': 0,
        'errors': 0,
        'warnings': risk_count,
        'runtime_seconds': 0,
        'status': 'SUCCESS',
        'notes': f"Generated {output_path}; pending_approvals={approvals_count}; risk_items={risk_count}",
    }
    with open(RUN_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description='Generate daily owner brief')
    parser.add_argument('--date', default=None, help='Date in YYYYMMDD format')
    parser.add_argument('--open', action='store_true', help='Open in browser after generating')
    parser.add_argument('--send-gateway', action='store_true',
                        help='Send the brief through Hermes gateway. Default is local file only.')
    parser.add_argument('--gateway', default='telegram', help='Hermes gateway target when --send-gateway is set')
    parser.add_argument('--no-log', action='store_true', help='Do not append agent_run_log row')
    parser.add_argument('--dry-run', action='store_true', help='Generate local file only and do not log or send externally')
    args = parser.parse_args()

    print("\nGenerating daily brief...")
    output_path = generate_brief(
        date_str=args.date,
        send_gateway=False if args.dry_run else args.send_gateway,
        gateway=args.gateway,
        log_run=False if args.dry_run else not args.no_log,
    )

    abs_path = os.path.abspath(output_path)
    print(f"✅ Brief saved: {abs_path}")

    if args.open:
        print("Opening in browser...")
        webbrowser.open(f"file://{abs_path}")


if __name__ == '__main__':
    main()
