#!/usr/bin/env python3
"""Run the Tender Export OS Document Intelligence + Evidence Archive lane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.source_runtime.document_intelligence import DEFAULT_OUTPUT_ROOT, run_document_intelligence_bundle  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", help="Local document paths to parse/archive")
    parser.add_argument("--output-dir", default="", help="Output directory. Defaults to outputs/document_intelligence/<run_id>")
    parser.add_argument("--run-id", default="", help="Optional deterministic run id")
    parser.add_argument("--workflow", default="GENERAL", help="Workflow label, e.g. GOV, EXPORT, SUPPLIER")
    parser.add_argument("--case-id", default="", help="Optional TEOS case id for traceability")
    parser.add_argument("--no-archive", action="store_true", help="Do not copy source files into evidence_archive")
    parser.add_argument("--enable-ocr", action="store_true", help="Use ocrmypdf fallback for unreadable PDFs when installed")
    parser.add_argument("--json", action="store_true", help="Print full manifest JSON instead of compact summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else None
    bundle = run_document_intelligence_bundle(
        args.sources,
        output_dir=output_dir,
        run_id=args.run_id or None,
        workflow=args.workflow,
        case_id=args.case_id,
        archive_inputs=not args.no_archive,
        enable_ocr=args.enable_ocr,
    )
    if args.json:
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
    else:
        print(
            json.dumps(
                {
                    "run_id": bundle["run_id"],
                    "output_dir": bundle["output_dir"],
                    "manifest_path": bundle["manifest_path"],
                    "report_path": bundle["report_path"],
                    "summary": bundle["summary"],
                    "external_side_effects": bundle["external_side_effects"],
                    "cases_created": bundle["cases_created"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
