---
name: codex-home-cleanup
description: Audit and reclaim disk space in the Codex home directory (`$CODEX_HOME` or `~/.codex`). Use when `.codex` becomes unusually large, session history piles up, `logs_2.sqlite` grows too much, sandbox artifacts accumulate, or the user asks to clean Codex state while keeping only a small number of recent sessions or log entries.
---

# Codex Home Cleanup

## Overview

Measure where `.codex` space is going, apply a retention policy, and verify the result.
Use the bundled scripts to keep only recent sessions and logs while removing temporary and rebuildable artifacts.

## Workflow

1. Measure first with `scripts/measure_codex_home.py`.
2. Decide retention before deleting anything.
3. Run `scripts/cleanup_codex_home.py` in dry-run mode.
4. Re-run with `--execute` once the plan looks right.
5. Measure again and report reclaimed space plus the largest remaining directories.

## Default Retention

Keep these unless the user explicitly asks to remove them:
- `config.toml`
- `auth.json`
- `skills/`
- `plugins/`
- `prompts/`
- `agents/`
- `rules/`
- `memories/`

Usually safe to prune:
- `archived_sessions/`
- `.tmp/`
- `tmp/`
- `cache/`
- `log/`
- `.sandbox-bin/`
- `config.toml.bak.*`
- `sandbox.log`

Prune instead of deleting outright when the user wants to keep a tail:
- `sessions/`: keep the newest few files
- `logs_2.sqlite`: keep the newest N rows, then checkpoint and vacuum

Read [cleanup-targets.md](C:\Users\admin\.codex\skills\codex-home-cleanup\references\cleanup-targets.md) if you need a quick reminder of the risk tiers.

## Presets

Use one of these profiles unless the user asks for custom retention:
- `light`: keep a generous recent tail
- `standard`: keep a few recent sessions and a small log tail
- `aggressive`: keep almost nothing, but avoid a totally empty tail
- `purge`: remove all session history and all retained log rows

The cleanup script also supports day-based protection:
- `--keep-session-days N`: keep session files modified within the last `N` days
- `--keep-log-days N`: keep log rows newer than the last `N` days

If both count-based and day-based retention are present, keep the union of both sets.

## Commands

Use the bundled runtime Python when available, or any compatible local Python 3.

```powershell
python scripts/measure_codex_home.py --path "$env:USERPROFILE\.codex"
python scripts/cleanup_codex_home.py --path "$env:USERPROFILE\.codex" --profile standard
python scripts/cleanup_codex_home.py --path "$env:USERPROFILE\.codex" --profile aggressive --keep-session-days 1 --keep-log-days 0.5
python scripts/cleanup_codex_home.py --path "$env:USERPROFILE\.codex" --profile purge --execute
```

## Verification

After cleanup:
- Re-run `scripts/measure_codex_home.py`.
- Confirm the largest remaining directories match the user's intent.
- If the cleanup followed a shell-startup incident, spot-check that `powershell` and `cmd` still launch.
- If SQLite compaction is partially blocked by a live lock, report that clearly instead of pretending the file is fully compacted.
