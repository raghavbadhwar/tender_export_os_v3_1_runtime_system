#!/usr/bin/env python3
"""
case_id_generator.py
Generate IDs for Tender Export OS records.

Usage:
    python scripts/case_id_generator.py --type GOV
    python scripts/case_id_generator.py --type EXP --date 20260630
    python scripts/case_id_generator.py --type SUP
    python scripts/case_id_generator.py --type TASK --count 3

Legacy:
    python scripts/case_id_generator.py --workflow GOV
    python scripts/case_id_generator.py --workflow EXPORT
"""

import argparse
import csv
import datetime
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MASTER_CASES_FILE = os.path.join(DATA_DIR, 'master_cases.csv')
SUPPLIER_MASTER_FILE = os.path.join(DATA_DIR, 'supplier_master.csv')
RUN_LOG_FILE = os.path.join(DATA_DIR, 'agent_run_log.csv')
APPROVALS_FILE = os.path.join(DATA_DIR, 'approvals_receipts.csv')

DATE_PREFIX_TYPES = {'GOV', 'EXP', 'TASK', 'REC'}
SIMPLE_SEQUENCE_TYPES = {'SUP'}


def get_next_case_sequence(prefix: str, date_str: str) -> int:
    """
    Read master_cases.csv and find the next available sequence number
    for the given workflow and date.
    """
    pattern = f"{prefix}-{date_str}-"
    max_seq = 0

    try:
        with open(MASTER_CASES_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                case_id = row.get('case_id', '')
                if case_id.startswith(pattern):
                    seq = int(case_id.split('-')[-1])
                    max_seq = max(max_seq, seq)
    except FileNotFoundError:
        pass  # First run — no existing cases

    return max_seq + 1


def get_next_simple_sequence(filepath: str, column_name: str, prefix: str) -> int:
    pattern = f"{prefix}-"
    max_seq = 0

    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                value = row.get(column_name, '')
                if value.startswith(pattern):
                    try:
                        seq = int(value.split('-')[-1])
                    except ValueError:
                        continue
                    max_seq = max(max_seq, seq)
    except FileNotFoundError:
        pass

    return max_seq + 1


def get_next_date_sequence(prefix: str, date_str: str) -> int:
    if prefix in {'GOV', 'EXP'}:
        return get_next_case_sequence(prefix, date_str)

    files_and_columns = [
        (RUN_LOG_FILE, 'run_id'),
        (APPROVALS_FILE, 'approval_id'),
        (APPROVALS_FILE, 'receipt_id'),
    ]
    pattern = f"{prefix}-{date_str}-"
    max_seq = 0
    for filepath, column_name in files_and_columns:
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    value = row.get(column_name, '')
                    if value.startswith(pattern):
                        try:
                            seq = int(value.split('-')[-1])
                        except ValueError:
                            continue
                        max_seq = max(max_seq, seq)
        except FileNotFoundError:
            continue
    return max_seq + 1


def normalize_id_type(id_type: str = None, workflow: str = None) -> str:
    if workflow:
        workflow = workflow.upper()
        if workflow == 'EXPORT':
            return 'EXP'
        if workflow == 'GOV':
            return 'GOV'
        raise ValueError(f"Invalid workflow: {workflow}. Must be GOV or EXPORT.")

    if not id_type:
        raise ValueError("Missing --type or legacy --workflow.")

    id_type = id_type.upper()
    if id_type == 'EXPORT':
        return 'EXP'
    if id_type in DATE_PREFIX_TYPES or id_type in SIMPLE_SEQUENCE_TYPES:
        return id_type
    raise ValueError(f"Invalid type: {id_type}. Must be GOV, EXP, EXPORT, SUP, TASK, or REC.")


def generate_id(id_type: str, date_str: str = None) -> str:
    """Generate a new v4 ID."""
    if date_str is None:
        date_str = datetime.date.today().strftime('%Y%m%d')

    id_type = normalize_id_type(id_type=id_type)

    if id_type in DATE_PREFIX_TYPES:
        sequence = get_next_date_sequence(id_type, date_str)
        return f"{id_type}-{date_str}-{str(sequence).zfill(3)}"

    if id_type == 'SUP':
        sequence = get_next_simple_sequence(SUPPLIER_MASTER_FILE, 'supplier_id', 'SUP')
        return f"SUP-{str(sequence).zfill(4)}"

    raise ValueError(f"Unsupported ID type: {id_type}")


def generate_case_id(workflow: str, date_str: str = None) -> str:
    """Backward-compatible GOV/EXPORT case ID generator."""
    return generate_id(normalize_id_type(workflow=workflow), date_str)


def main():
    parser = argparse.ArgumentParser(description='Generate a new case ID')
    parser.add_argument('--type', dest='id_type', default=None,
                        choices=['GOV', 'EXP', 'EXPORT', 'SUP', 'TASK', 'REC'],
                        help='ID type: GOV, EXP/EXPORT, SUP, TASK, or REC')
    parser.add_argument('--workflow', default=None,
                        choices=['GOV', 'EXPORT'],
                        help='Legacy workflow type: GOV or EXPORT')
    parser.add_argument('--date', default=None,
                        help='Date in YYYYMMDD format. Defaults to today.')
    parser.add_argument('--count', type=int, default=1,
                        help='Number of IDs to generate')

    args = parser.parse_args()

    date_str = args.date or datetime.date.today().strftime('%Y%m%d')

    try:
        id_type = normalize_id_type(id_type=args.id_type, workflow=args.workflow)
    except ValueError as exc:
        parser.error(str(exc))

    print(f"\nGenerating {args.count} {id_type} ID(s) for {date_str}:")
    print("-" * 40)

    for i in range(args.count):
        if i == 0:
            new_id = generate_id(id_type, date_str)
        else:
            if id_type in DATE_PREFIX_TYPES:
                seq = get_next_date_sequence(id_type, date_str) + i
                new_id = f"{id_type}-{date_str}-{str(seq).zfill(3)}"
            else:
                seq = get_next_simple_sequence(SUPPLIER_MASTER_FILE, 'supplier_id', id_type) + i
                new_id = f"{id_type}-{str(seq).zfill(4)}"
        print(f"  {new_id}")

    print("-" * 40)
    print("Note: Register the ID in the relevant master file before using it.")


if __name__ == '__main__':
    main()
