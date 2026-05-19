---
name: codex-session-importer
description: Import copied Codex JSONL session rollouts from another computer into the local Codex Desktop sidebar/project list. Use when a user has a ~/.codex/sessions/.../rollout-*.jsonl file and wants the full historical chat to appear under a local workspace in Codex App, or when a copied session resumes in CLI but is missing from the App left sidebar.
---

# Codex Session Importer

Use this skill to make an existing Codex session JSONL visible to Codex Desktop on the current machine.

## Core Workflow

1. Identify the source JSONL file and target project root.
   - Source must be a Codex rollout JSONL whose first line is `type: session_meta`.
   - Target project root should be the local workspace path where the App should group the chat.
   - If the user does not specify a target root, use the current working directory.

2. Run the bundled importer script.

```powershell
python "$HOME\.codex\skills\codex-session-importer\scripts\import_codex_session.py" `
  "C:\path\to\rollout-....jsonl" `
  --project-cwd "C:\path\to\local\workspace"
```

3. Read the script summary and report:
   - session id
   - thread title
   - target project root
   - rollout path now registered locally
   - backup directory

4. Tell the user to restart Codex Desktop or refresh the window if the sidebar does not update immediately. The App can cache sidebar state while running.

## Script Behavior

`scripts/import_codex_session.py` performs the fragile parts deterministically:

- Backs up touched local Codex state files under `$CODEX_HOME/tmp/session-import-backup-*`.
- Copies the source JSONL into `$CODEX_HOME/sessions/YYYY/MM/DD/` when it is outside the local session store.
- Updates the JSONL `session_meta.payload.cwd` to the local project root.
- Inserts or updates the row in `$CODEX_HOME/state_5.sqlite` table `threads`.
- Inserts or updates the lightweight `$CODEX_HOME/session_index.jsonl` entry.
- Updates available workspace hints in `$CODEX_HOME/.codex-global-state.json`.
- Prints a JSON summary suitable for final reporting.

## Useful Options

Dry run without changing files:

```powershell
python "$HOME\.codex\skills\codex-session-importer\scripts\import_codex_session.py" `
  "C:\path\to\rollout-....jsonl" `
  --project-cwd "C:\path\to\local\workspace" `
  --dry-run
```

Rewrite historical `turn_context.payload.cwd` records too:

```powershell
python "$HOME\.codex\skills\codex-session-importer\scripts\import_codex_session.py" `
  "C:\path\to\rollout-....jsonl" `
  --project-cwd "C:\path\to\local\workspace" `
  --rewrite-turn-context-cwd
```

Override the inferred title:

```powershell
python "$HOME\.codex\skills\codex-session-importer\scripts\import_codex_session.py" `
  "C:\path\to\rollout-....jsonl" `
  --project-cwd "C:\path\to\local\workspace" `
  --title "My restored chat"
```

## Recovery

If a bad import needs to be reverted, restore files from the backup directory printed by the script. For SQLite, restore `state_5.sqlite` only after closing Codex Desktop.
