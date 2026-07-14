#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  printf '%s\n' "Missing project interpreter: $PYTHON" >&2
  exit 2
fi

# Keep Hermes's own Python environment out of the project test process.
unset PYTHONPATH
export PYTHONNOUSERSITE=1
exec "$PYTHON" -m pytest "$@"
