from pathlib import Path

import pytest

from scripts.lib.shared_brain_write_lock import LockHeldError, acquire_lock, release_lock, write_lock


def test_drive_write_lock_blocks_concurrent_writer(tmp_path: Path) -> None:
    lock_path = tmp_path / "drive.lock"
    with write_lock(lock_path):
        with pytest.raises(LockHeldError):
            acquire_lock(lock_path)
    assert not lock_path.exists()


def test_release_lock_is_idempotent(tmp_path: Path) -> None:
    lock_path = tmp_path / "missing.lock"
    release_lock(lock_path)
    assert not lock_path.exists()
