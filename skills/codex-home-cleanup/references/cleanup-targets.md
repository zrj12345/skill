# Cleanup Targets

Use this file when you need a quick safety map before pruning `.codex`.

## Keep By Default

- `config.toml`
- `auth.json`
- `skills/`
- `plugins/`
- `prompts/`
- `agents/`
- `rules/`
- `memories/`

## Usually Safe To Delete

- `archived_sessions/`
- `.tmp/`
- `tmp/`
- `cache/`
- `log/`
- `.sandbox-bin/`
- `config.toml.bak.*`
- `sandbox.log`

## Usually Better To Prune

- `sessions/`
  Keep the newest few files unless the user explicitly says full deletion is acceptable.
- `logs_2.sqlite`
  Keep a recent tail of rows, then checkpoint and vacuum.

## Preset Profiles

- `light`
  Keep a generous tail for people who want history but still want obvious junk removed.
- `standard`
  Good default for routine cleanup.
- `aggressive`
  Keep only a tiny tail.
- `purge`
  Delete all sessions and logs that the cleanup script manages.

## Report After Cleanup

- Total size before and after
- Biggest remaining entries
- Session files kept
- Log rows kept
- Any files that could not be compacted or removed because of live locks
