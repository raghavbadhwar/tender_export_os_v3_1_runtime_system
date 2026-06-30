#!/usr/bin/env python3
"""
update_master_case.py
Update a specific field or set of fields for a case in master_cases.csv.

Usage:
    python scripts/update_master_case.py --case_id GOV-20260630-001 --status DEEP_READ
    python scripts/update_master_case.py --case_id EXP-20260630-001 --status APPROVED --approved_by Owner
"""

import argparse
import csv
import datetime
import os
import shutil
import subprocess

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MASTER_CASES_FILE = os.path.join(DATA_DIR, 'master_cases.csv')
LOG_FILE = os.path.join(DATA_DIR, 'agent_run_log.csv')

# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    'NEW': ['FAST_KILL', 'REJECTED'],
    'FAST_KILL': ['REJECTED', 'WATCHLIST', 'DEEP_READ'],
    'WATCHLIST': ['DEEP_READ', 'REJECTED', 'ARCHIVED'],
    'DEEP_READ': ['SUPPLIER_SEARCH', 'REJECTED'],
    'SUPPLIER_SEARCH': ['PRICING_READY', 'WATCHLIST'],
    'PRICING_READY': ['ARTIFACT_PRODUCTION', 'APPROVAL_REQUIRED'],
    'ARTIFACT_PRODUCTION': ['APPROVAL_REQUIRED', 'CHANGES_REQUESTED', 'REJECTED'],
    'APPROVAL_REQUIRED': ['APPROVED', 'REJECTED', 'CHANGES_REQUESTED'],
    'CHANGES_REQUESTED': ['ARTIFACT_PRODUCTION', 'APPROVAL_REQUIRED', 'REJECTED'],
    'APPROVED': ['SENT_OR_SUBMITTED'],
    'SENT_OR_SUBMITTED': ['FOLLOW_UP', 'WON', 'LOST'],
    'FOLLOW_UP': ['WON', 'LOST', 'ARCHIVED'],
    'WON': ['ARCHIVED'],
    'LOST': ['ARCHIVED'],
    'REJECTED': ['ARCHIVED'],
}

VALID_STATUSES = set(VALID_STATUS_TRANSITIONS.keys())


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Check if status transition is valid."""
    allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
    return new_status in allowed or new_status == 'ARCHIVED'


def update_case(case_id: str, updates: dict, force: bool = False) -> bool:
    """
    Update a case in master_cases.csv.

    Args:
        case_id: The case ID to update
        updates: Dict of field -> new_value
        force: Skip status transition validation

    Returns:
        True if updated, False if not found
    """
    # Read all rows
    rows = []
    case_found = False
    fieldnames = []

    with open(MASTER_CASES_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            if row.get('case_id') == case_id:
                case_found = True
                current_status = row.get('status', '')

                # Validate status transition if status is being updated
                if 'status' in updates:
                    new_status = updates['status']
                    if not force and not validate_status_transition(current_status, new_status):
                        print(f"  ⚠️  Invalid status transition: {current_status} → {new_status}")
                        print(f"  Allowed from {current_status}: {VALID_STATUS_TRANSITIONS.get(current_status, [])}")
                        print("  Use --force to override.")
                        return False

                # Apply updates
                for field, value in updates.items():
                    if field in row or field in fieldnames:
                        old_value = row.get(field, '')
                        row[field] = value
                        print(f"  {field}: '{old_value}' → '{value}'")
                    else:
                        print(f"  ⚠️  Field '{field}' not in master_cases.csv — skipping")

                # Always update updated_at
                row['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d')

            rows.append(row)

    if not case_found:
        print(f"  ❌ Case not found: {case_id}")
        return False

    # Write backup
    backup_file = f"{MASTER_CASES_FILE}.bak"
    shutil.copy2(MASTER_CASES_FILE, backup_file)

    # Write updated CSV
    with open(MASTER_CASES_FILE, 'w', newline='', encoding='utf-8') as f:
        # Clean None keys from rows to prevent DictWriter errors from trailing commas
        for r in rows:
            r.pop(None, None)
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✅ Case {case_id} updated. Backup: {backup_file}")
    return True


def log_update(case_id: str, updates: dict, actor: str = 'update_master_case'):
    """Log the update to agent_run_log.csv."""
    run_id = f"RUN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    row = {
        'run_id': run_id,
        'run_date': datetime.date.today().isoformat(),
        'run_time': datetime.datetime.now().strftime('%H:%M:%S'),
        'agent_name': actor,
        'trigger_type': 'manual',
        'cases_processed': 1,
        'cases_created': 0,
        'cases_rejected': 1 if updates.get('status') == 'REJECTED' else 0,
        'cases_updated': 1,
        'sources_checked': 0,
        'sources_failed': 0,
        'actions_taken': f"update_case:{case_id}:{updates}",
        'approval_cards_created': 0,
        'receipts_created': 0,
        'errors': 0,
        'warnings': 0,
        'runtime_seconds': 0,
        'status': 'SUCCESS',
        'notes': f"Manual update to case {case_id}: {updates}"
    }

    fieldnames = list(row.keys())
    file_exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description='Update a case in master_cases.csv')
    parser.add_argument('--case_id', required=True, help='Case ID to update')
    parser.add_argument('--status', help='New status')
    parser.add_argument('--kill_reason', help='Kill reason code')
    parser.add_argument('--score', type=int, help='Updated score')
    parser.add_argument('--notes', help='Notes to add')
    parser.add_argument('--approved_by', help='Set approved_by field')
    parser.add_argument('--force', action='store_true', help='Skip transition validation')
    parser.add_argument('--notify', action='store_true', help='Send owner gateway notification for status changes')
    parser.add_argument('--field', nargs=2, action='append', metavar=('FIELD', 'VALUE'),
                        help='Update any field: --field fieldname value')

    args = parser.parse_args()

    updates = {}
    if args.status:
        updates['status'] = args.status
        if args.status == 'APPROVED':
            updates['approved_at'] = datetime.datetime.now().isoformat()
    if args.kill_reason:
        updates['kill_reason'] = args.kill_reason
    if args.notes:
        updates['notes'] = args.notes
    if args.approved_by:
        updates['approved_by'] = args.approved_by
    if args.field:
        for field, value in args.field:
            updates[field] = value

    if not updates:
        print("Error: No updates specified. Use --status, --notes, or --field FIELD VALUE")
        return

    print(f"\nUpdating case: {args.case_id}")
    print(f"Updates: {updates}")
    print("-" * 40)

    success = update_case(args.case_id, updates, force=args.force)

    if success:
        log_update(args.case_id, updates)
        print(f"\n  Run logged to agent_run_log.csv")
        
        # Send Telegram notification via Hermes if status changed
        if args.notify and 'status' in updates:
            notify_status_update(args.case_id, updates['status'])


def notify_status_update(case_id: str, status: str):
    """Notify the owner via Telegram of a case status change."""
    emoji = "✅"
    if status == "REJECTED":
        emoji = "❌"
    elif status == "CHANGES_REQUESTED":
        emoji = "🔄"
    elif status == "APPROVAL_REQUIRED":
        emoji = "⚠️"
        
    msg = f"{emoji} Case {case_id} status updated to {status}."
    try:
        subprocess.run(
            ["/Users/raghav/.ares/bin/ares-hermes", "send", "--to", "telegram", msg],
            check=True,
            capture_output=True
        )
        print(f"  ✓ Telegram status update notification sent.")
    except Exception as e:
        print(f"  ⚠️  Failed to send Telegram update: {e}")


if __name__ == '__main__':
    main()
