---
name: session-auto-resume
description: Automatically resume paused Codex CLI sessions by watching `~/.codex/sessions/**/*.jsonl` or `~/.codex/archived_sessions/*.jsonl` for stable inactivity and then running `codex exec resume ...`. Use when the user wants hands-free continuation across staged tasks, wants to start or stop a watcher for a known session id, or needs a reusable Python tool that can also be run manually outside Codex.
---

# Session Auto Resume

## Overview

Use the bundled Python watcher instead of rebuilding the polling logic in shell each time. Start it when a staged Codex workflow pauses between phases and needs to continue without manual clicks; stop it when the automation is no longer needed.

## Quick Start

Run the bundled script from this skill directory:

```bash
python scripts/session_auto_resume.py <interval-seconds> start <session-id>
python scripts/session_auto_resume.py <interval-seconds> stop <session-id>
```

Prefer numeric intervals such as `5` or `10`.

## Workflow

1. Confirm the user has a concrete session id.
2. Run the bundled script with `start` or `stop`.
3. Report the emitted PID, state file, and log file.
4. If the watcher cannot find the session file, inspect the Codex home `sessions/` and `archived_sessions/` directories instead of rewriting the tool.

## Behavior

- `start` opens a new `cmd` console on Windows and runs the watcher there.
- The watcher locates the matching session JSONL file under the Codex home directory.
- The watcher establishes an initial snapshot on startup and does not trigger from pre-existing history.
- The watcher only uses the stable-file rule: every 30 seconds it counts one unchanged sample, and after 6 unchanged samples it launches `codex exec resume`.
- The watcher applies a post-resume grace period so it does not immediately trigger again.
- `stop` kills the watcher for that session id by reading its state file and terminating the console process tree.

## Outputs

The script writes runtime artifacts under `CODEX_HOME/tmp/session-auto-resume/` or `~/.codex/tmp/session-auto-resume/` when `CODEX_HOME` is unset.

- `state/<session-id>.json`
- `logs/<session-id>.log`

## Notes

- Keep using the bundled script; do not inline an ad-hoc polling loop in shell.
- Edit `scripts/session_auto_resume.py` if the user wants different stable-file timing or a different resume prompt.
- Fix the environment first if `codex` is not on `PATH`.

## Resources (optional)

### scripts/
- `scripts/session_auto_resume.py`: detached watcher and `start`/`stop` entrypoint.
