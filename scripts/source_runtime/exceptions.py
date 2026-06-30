"""Structured exceptions for deep source access."""

from __future__ import annotations

try:
    from scripts.source_adapters.base import SourceBlocked
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from source_adapters.base import SourceBlocked  # type: ignore


class SourceRuntimeError(RuntimeError):
    """Base runtime exception for source access failures."""


class UnsafePortalAction(SourceRuntimeError):
    """Raised when an adapter tries to cross an approval or portal-safety boundary."""
