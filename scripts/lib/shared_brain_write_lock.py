"""Local lock helpers for Drive/Knowledge Bus projection writes."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK_PATH = PROJECT_ROOT / "outputs" / "locks" / "knowledge_bus.write.lock"


class LockHeldError(RuntimeError):
    """Raised when another writer holds the projection lock."""


def acquire_lock(path: Path = DEFAULT_LOCK_PATH, stale_after_seconds: int = 900) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    if path.exists():
        age = now - path.stat().st_mtime
        if age < stale_after_seconds:
            raise LockHeldError(f"Drive projection lock is held: {path}")
        path.unlink()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(str(now))


def release_lock(path: Path = DEFAULT_LOCK_PATH) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


@contextmanager
def write_lock(path: Path = DEFAULT_LOCK_PATH, stale_after_seconds: int = 900) -> Iterator[Path]:
    acquire_lock(path, stale_after_seconds)
    try:
        yield path
    finally:
        release_lock(path)
