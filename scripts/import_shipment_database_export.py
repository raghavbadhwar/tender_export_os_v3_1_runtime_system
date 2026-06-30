#!/usr/bin/env python3
"""Import licensed/manual shipment database exports into buyer intelligence."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.event_ledger import append_event  # noqa: E402
from scripts.source_runtime.credential_policy import sanitize_payload  # noqa: E402

BUYER_MASTER = PROJECT_ROOT / "data" / "buyer_master.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "shipment_imports"


def read_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    if suffix in {".xlsx", ".xls"}:
        import pandas as pd

        return pd.read_excel(path, dtype=str).fillna("").to_dict(orient="records")
    raise ValueError("Supported inputs: .csv, .xlsx, .xls")


def first(row: dict[str, Any], names: list[str]) -> str:
    normalized = {key.lower().strip().replace(" ", "_"): str(value or "") for key, value in row.items()}
    for name in names:
        value = normalized.get(name)
        if value:
            return value
    return ""


def normalize_buyer_rows(rows: list[dict[str, Any]], source_name: str) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for idx, row in enumerate(rows, start=1):
        buyer_name = first(row, ["buyer", "buyer_name", "importer", "importer_name", "consignee", "company_name"])
        product = first(row, ["product", "product_description", "description", "commodity"])
        country = first(row, ["country", "buyer_country", "destination_country"])
        if not buyer_name and not product:
            continue
        output.append(
            {
                "buyer_id": f"BUY-SHIP-{dt.datetime.now().strftime('%Y%m%d')}-{idx:04d}",
                "buyer_name": buyer_name or "Unknown buyer",
                "buyer_type": "Company",
                "country": country,
                "source_name": source_name,
                "source_url": "manual_shipment_database_export",
                "contact_path": "",
                "identity_status": "UNVERIFIED",
                "verification_status": "SHIPMENT_EXPORT_IMPORTED",
                "buyer_stage": "WARM" if buyer_name and product else "COLD",
                "buyer_score": "45",
                "source_reliability_score": "50",
                "fraud_flags": "",
                "evidence_links": "",
                "notes": f"Imported manually from licensed/exported shipment database row. Product: {product}. HS: {first(row, ['hs_code', 'hscode', 'hs'])}. Quantity: {first(row, ['quantity', 'qty'])}.",
                "created_at": dt.date.today().isoformat(),
                "updated_at": dt.date.today().isoformat(),
            }
        )
    return output


def append_to_buyer_master(rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    if not BUYER_MASTER.exists():
        raise FileNotFoundError(BUYER_MASTER)
    with BUYER_MASTER.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        existing = list(reader)
    with BUYER_MASTER.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(existing)
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a manual shipment database export")
    parser.add_argument("--input", required=True, help="CSV/XLSX export from a licensed/manual shipment database")
    parser.add_argument("--source-name", default="Manual shipment database export")
    parser.add_argument("--write", action="store_true", help="Append rows to data/buyer_master.csv")
    parser.add_argument("--record-event", action="store_true")
    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    rows = normalize_buyer_rows(read_rows(input_path), args.source_name)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = OUTPUT_DIR / f"shipment_import_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report.write_text(json.dumps(sanitize_payload({"input": str(input_path), "rows": rows}), indent=2, ensure_ascii=False), encoding="utf-8")
    if args.write:
        append_to_buyer_master(rows)
    if args.record_event:
        append_event(
            "buyer.shipment_export_imported",
            "import_shipment_database_export",
            object_type="buyer",
            object_id=report.name,
            source=args.source_name,
            payload={"rows": len(rows), "wrote_buyer_master": bool(args.write), "report": str(report.relative_to(PROJECT_ROOT))},
            citations=[str(report.relative_to(PROJECT_ROOT)), str(input_path.relative_to(PROJECT_ROOT)) if input_path.is_relative_to(PROJECT_ROOT) else str(input_path)],
        )
    print(f"Parsed {len(rows)} buyer row(s). Report: {report}")
    print("buyer_master.csv updated." if args.write else "Dry run only; pass --write to append buyer_master.csv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
