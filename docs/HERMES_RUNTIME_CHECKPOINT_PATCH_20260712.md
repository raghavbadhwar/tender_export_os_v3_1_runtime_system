# Hermes Runtime Checkpoint Patch — 2026-07-12

## Problem

Hermes checkpoints were enabled, but a live activation canary returned `False`. The runtime logged that the workspace exceeded the 50,000-file guard even though it contained roughly 46,000 actual files.

`tools/checkpoint_manager.py::_dir_file_count()` used `Path.rglob("*")` and incremented the count for every path entry, including directories. The function and guard are explicitly defined in terms of files, so deeply nested virtual environments caused a false rejection.

## Local fix

The guard now increments only when `entry.is_file()` is true and skips unreadable entries. A regression test creates 40 nested directories plus one file and confirms the result is exactly one.

Changed in the local Hermes checkout:

- `tools/checkpoint_manager.py`
- `tests/tools/test_checkpoint_manager.py`

## Verification

- Focused regression: 78 checkpoint-manager tests passed.
- Live Tender workspace canary: checkpoint created successfully in 3.526 seconds.
- Checkpoint store: 1,190,525 bytes, one project, one commit.
- Workspace files were not modified by the canary; only the profile's shadow checkpoint store changed.

This is a local runtime fix, not an upstream release claim. The original version remains available from the checkout's upstream commit `4281151ae859241351ba14d8c7682dc67ff4c126`. After a future Hermes update, rerun the live checkpoint canary and retain the patch only if the upstream implementation still counts directories.
