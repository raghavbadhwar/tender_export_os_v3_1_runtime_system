# Hermes Runtime Security Patch - 2026-07-12

The installed Hermes 0.18.2 checkout was current at upstream commit `4281151a`, but `hermes security audit` detected newly published dependency advisories after installation.

The local runtime was patched to the advisory-fixed versions:

- `cryptography` 46.0.7 -> 48.0.1
- `starlette` 1.0.1 -> 1.3.1
- `python-multipart` 0.0.27 -> 0.0.31
- `pydantic-settings` 2.13.1 -> 2.14.2
- `Pygments` 2.19.2 -> 2.20.0
- `pytest` 9.0.2 -> 9.0.3
- `certifi` 2026.5.20 -> 2026.6.17

DDGS 9.14.4 is pinned in the local Hermes project so the selected no-key search backend survives future `uv sync` and desktop rebuilds. The Starlette/python-multipart lazy-install pins and regression expectation were updated in lockstep.

Verification:

- `uv pip check`: all installed packages compatible.
- `hermes security audit`: no known vulnerabilities across 117 components in the final last-pass re-audit.
- Hermes packaging metadata regression: passed.
- Hermes packaging, Computer Use, and MCP regression selection: 272 passed after the version expectation was updated.
- Gateway remains loopback/local and launchd-supervised; no public service was enabled.

Rollback copies of the pre-patch `pyproject.toml` and `uv.lock` are stored at:

`/Users/raghav/.hermes/security-patch-backups/20260712-pre-advisory-fixes/`

The previous Hermes Desktop app bundle is stored at:

`/Users/raghav/.hermes/desktop-backups/Hermes-0.17.0-5ecc0798-20260711.app`

These are local runtime changes, not an upstream release claim. A future Hermes update may supersede them; rerun the security audit after updating.
