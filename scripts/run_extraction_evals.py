#!/usr/bin/env python3
"""Run TenderOS source-grounded extraction evals."""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.extract_case_evidence import extract_quote_evidence, extract_tender_evidence

def load_cases(paths):
    cases=[]
    for path in paths:
        cases.extend(json.loads(Path(path).read_text(encoding="utf-8")))
    return cases

def run_case(case):
    if case["kind"] == "tender":
        result = extract_tender_evidence(case["text"], case_id=case["case_id"], source_name="eval")
    else:
        result = extract_quote_evidence(case["text"], case_id=case["case_id"], source_name="eval")
    failures=[]
    for field, expected in case.get("expect_fields", {}).items():
        actual = result.get("fields", {}).get(field, {}).get("value")
        span = result.get("fields", {}).get(field, {}).get("source_span", {})
        if actual != expected:
            failures.append(f"field {field}: expected {expected!r}, got {actual!r}")
        if not isinstance(span.get("start"), int) or span.get("start", -1) < 0:
            failures.append(f"field {field}: missing source span")
    if case.get("expect_evidence_level") and result.get("evidence_level") != case["expect_evidence_level"]:
        failures.append(f"evidence_level expected {case['expect_evidence_level']}, got {result.get('evidence_level')}")
    if case.get("expect_quote_proof_classification") and result.get("quote_proof_classification") != case["expect_quote_proof_classification"]:
        failures.append(f"quote classification expected {case['expect_quote_proof_classification']}, got {result.get('quote_proof_classification')}")
    if case.get("expect_approval_gate") and result.get("approval_gate") != case["expect_approval_gate"]:
        failures.append(f"approval gate expected {case['expect_approval_gate']}, got {result.get('approval_gate')}")
    return {"name": case["name"], "ok": not failures, "failures": failures, "result_summary": {"evidence_level": result.get("evidence_level"), "approval_gate": result.get("approval_gate"), "quote_proof_classification": result.get("quote_proof_classification")}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cases", nargs="*", default=["tests/evals/tender_extraction_cases.json", "tests/evals/quote_proof_cases.json"])
    p.add_argument("--output", default="outputs/evals/source_grounded_extraction_eval_report.json")
    args=p.parse_args()
    paths=[str(PROJECT_ROOT/path) if not str(path).startswith("/") else str(path) for path in args.cases]
    results=[run_case(case) for case in load_cases(paths)]
    report={"created_at": datetime.now(timezone.utc).isoformat(), "status": "PASS" if all(r["ok"] for r in results) else "FAIL", "results": results}
    out=PROJECT_ROOT/args.output if not str(args.output).startswith("/") else Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"TenderOS extraction eval {report['status']}: {out}")
    for r in results: print(("PASS" if r["ok"] else "FAIL"), r["name"], "; ".join(r["failures"]))
    return 0 if report["status"]=="PASS" else 1
if __name__ == "__main__": raise SystemExit(main())
