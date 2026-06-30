# Plugin Health Review

Use this skill for Codex/Hermes plugin and tool capability checks.

## Inputs
- `codex plugin list --available --json`
- `codex --help`
- `hermes --help`
- `hermes tools --help`
- `data/plugin_health.csv`
- `data/capability_registry.csv`

## Procedure
1. Run local readiness checks where available.
2. Summarize plugin/tool status without dumping huge raw JSON.
3. Update `data/plugin_health.csv`.
4. Update capability notes when routing changes.
5. Flag auth, missing plugin, or runtime blockers.

## Must Not
- enable network/credential-heavy plugins without approval
- expose services publicly
- claim a plugin is usable without local or connector evidence
