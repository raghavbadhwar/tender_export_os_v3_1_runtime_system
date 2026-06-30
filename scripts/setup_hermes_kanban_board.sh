#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RECEIPT_DIR="$PROJECT_ROOT/receipts/plugin_runs"
RECEIPT="$RECEIPT_DIR/hermes_kanban_setup_plan.txt"
EXECUTE="false"

if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="true"
fi

mkdir -p "$RECEIPT_DIR"

cat > "$RECEIPT" <<'PLAN'
Tender Export OS v4.1 - Hermes Kanban Setup Plan

Board:
  slug: tender-export-os
  name: Tender Export OS

Required statuses:
  triage, todo, ready, running, blocked, done, archived

Profiles:
  hermes-chief-operator
  gov-tender-radar
  export-rfq-radar
  supplier-sourcing
  pricing-compliance
  codex-artifact-factory
  sales-followup
  source-health
  learning-review
  chatgpt-boardroom-handoff

Run local help first:
  hermes kanban --help

Do not claim board creation succeeded unless Hermes confirms it.
PLAN

echo "Wrote setup plan: $RECEIPT"

if [[ "$EXECUTE" != "true" ]]; then
  echo "Dry run only. Re-run with --execute after inspecting 'hermes kanban --help'."
  exit 0
fi

if ! command -v hermes >/dev/null 2>&1; then
  echo "hermes not found on PATH" >&2
  exit 1
fi

echo "Hermes kanban help:"
hermes kanban --help
echo "Review the help output above and create the board with the exact supported local syntax."
