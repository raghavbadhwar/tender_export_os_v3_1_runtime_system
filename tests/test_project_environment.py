from __future__ import annotations

import sys
from pathlib import Path


def test_project_test_runtime_is_isolated_from_hermes() -> None:
    prefix = Path(sys.prefix).resolve()
    assert prefix.name == ".venv"
    assert "hermes-agent" not in str(prefix)
    assert "hermes-agent" not in "\n".join(str(path) for path in sys.path)


def test_project_mcp_dependencies_load_from_project_runtime() -> None:
    import fastmcp
    import jsonschema
    import pydantic_core
    import rpds

    for module in (fastmcp, jsonschema, pydantic_core, rpds):
        assert module.__file__ is not None
        assert ".venv" in str(Path(module.__file__).resolve())
