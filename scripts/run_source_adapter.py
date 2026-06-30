#!/usr/bin/env python3
"""Run a source adapter in safe output-only mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from event_ledger import append_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_DIR = PROJECT_ROOT / "scripts" / "source_adapters"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "system_health" / "mock_source_opportunities.json"
sys.path.insert(0, str(ADAPTER_DIR))


def load_adapter(name: str):
    if name != "mock":
        raise ValueError("Only the fixture-backed mock adapter is implemented. Add real adapters behind this contract.")
    from mock_adapter import MockSourceAdapter

    return MockSourceAdapter()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run source adapter in safe output-only mode")
    parser.add_argument("--adapter", default="mock", help="Adapter name")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path")
    parser.add_argument("--record-event", action="store_true", help="Append source_adapter.mock_ran event")
    args = parser.parse_args()

    adapter = load_adapter(args.adapter)
    opportunities = [item.to_dict() for item in adapter.scan()]
    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"adapter": args.adapter, "opportunities": opportunities}, indent=2), encoding="utf-8")
    print(f"Wrote {len(opportunities)} opportunities to {output}")
    print("Output-only mode: no cases created and no external actions taken.")

    if args.record_event:
        append_event(
            "source_adapter.mock_ran",
            "run_source_adapter",
            object_type="source_adapter",
            object_id=args.adapter,
            payload={"opportunities": len(opportunities), "output": str(output.relative_to(PROJECT_ROOT))},
            citations=[str(output.relative_to(PROJECT_ROOT))],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
