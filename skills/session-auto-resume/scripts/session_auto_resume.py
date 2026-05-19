#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

RESUME_PROMPT = "\u7ee7\u7eed"
DEFAULT_COOLDOWN_SECONDS = 30.0
TAIL_RECORD_COUNT = 10
UNCHANGED_POLLS_BEFORE_RESUME = 6
STABLE_CHECK_INTERVAL_SECONDS = 30.0
POST_RESUME_GRACE_SECONDS = 180.0


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def future_iso(seconds: float) -> str:
    return (
        (datetime.now(timezone.utc) + timedelta(seconds=seconds))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def runtime_root() -> Path:
    return codex_home() / "tmp" / "session-auto-resume"


def state_path(session_id: str) -> Path:
    return runtime_root() / "state" / f"{session_id}.json"


def log_path(session_id: str) -> Path:
    return runtime_root() / "logs" / f"{session_id}.log"


def ensure_runtime_dirs() -> None:
    (runtime_root() / "state").mkdir(parents=True, exist_ok=True)
    (runtime_root() / "logs").mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temp_path.replace(path)


def append_log(log_file: Path, message: str) -> None:
    line = f"[{now_iso()}] {message}"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")
    print(line, flush=True)


def preview(text: str, limit: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            return False
        output = result.stdout.strip()
        if not output or output.startswith("INFO:"):
            return False
        return f'"{pid}"' in output
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def terminate_pid(pid: int) -> tuple[int, str]:
    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        output = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
        return result.returncode, output

    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        return 0, "process already exited"
    return 0, "signal sent"


def find_session_file(session_id: str) -> Path | None:
    search_roots = [
        (0, codex_home() / "sessions"),
        (1, codex_home() / "archived_sessions"),
    ]
    candidates: list[tuple[int, float, Path]] = []
    pattern = f"*{session_id}*.jsonl"
    for priority, root in search_roots:
        if not root.exists():
            continue
        for candidate in root.rglob(pattern):
            try:
                stat = candidate.stat()
            except OSError:
                continue
            candidates.append((priority, stat.st_mtime, candidate))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], -item[1], str(item[2])))
    return candidates[0][2]


def extract_assistant_candidate(record: dict[str, Any]) -> tuple[str, str] | None:
    timestamp = str(record.get("timestamp") or "")
    record_type = record.get("type")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None

    if record_type == "event_msg" and payload.get("type") == "agent_message":
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return timestamp, message

    if (
        record_type == "response_item"
        and payload.get("type") == "message"
        and payload.get("role") == "assistant"
    ):
        content = payload.get("content")
        if not isinstance(content, list):
            return None
        pieces: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text:
                pieces.append(text)
        message = "".join(pieces).strip()
        if message:
            return timestamp, message

    return None


def inspect_tail_window(session_file: Path, limit: int = TAIL_RECORD_COUNT) -> dict[str, Any]:
    tail_lines: deque[str] = deque(maxlen=limit)
    with session_file.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            tail_lines.append(line)

    latest_assistant: tuple[str, str, str] | None = None
    for line in tail_lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        candidate = extract_assistant_candidate(record)
        if candidate is None:
            continue
        timestamp, message = candidate
        digest = hashlib.sha1(message.encode("utf-8")).hexdigest()
        candidate_with_signature = (timestamp, message, f"{timestamp}:{digest}")
        latest_assistant = candidate_with_signature

    return {
        "tail_line_count": len(tail_lines),
        "latest_assistant": latest_assistant,
    }


def should_retry_same_trigger(state: dict[str, Any], interval: float) -> bool:
    last_attempt_at = parse_iso(state.get("last_attempt_at"))
    if last_attempt_at is None:
        return True
    elapsed = (datetime.now(timezone.utc) - last_attempt_at).total_seconds()
    return elapsed >= max(interval, DEFAULT_COOLDOWN_SECONDS)


def perform_resume_command(session_id: str) -> tuple[int, str]:
    resume_args = [
        "codex",
        "exec",
        "resume",
        "--skip-git-repo-check",
        "--dangerously-bypass-approvals-and-sandbox",
        session_id,
        RESUME_PROMPT,
    ]
    try:
        if os.name == "nt":
            resume_command = subprocess.list2cmdline(resume_args)
            result = subprocess.run(
                ["cmd.exe", "/c", resume_command],
                check=False,
            )
            return result.returncode, "interactive resume finished in terminal"

        result = subprocess.run(
            resume_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return 127, "codex executable was not found on PATH"
    except OSError as exc:
        return 1, f"failed to launch resume command: {exc!r}"

    output = "\n".join(
        part.strip() for part in [result.stdout, result.stderr] if part and part.strip()
    )
    return result.returncode, output


def launch_resume_command(
    session_id: str, trigger_reason: str, trigger_token: str
) -> tuple[int, str]:
    helper_args = [
        sys.executable,
        str(Path(__file__).resolve()),
        "__resume__",
        session_id,
        trigger_reason,
        trigger_token,
    ]
    try:
        if os.name == "nt":
            helper_command = subprocess.list2cmdline(helper_args)
            wt_path = shutil.which("wt.exe") or shutil.which("wt")
            if wt_path:
                subprocess.Popen(
                    [
                        wt_path,
                        "-w",
                        "0",
                        "new-tab",
                        "cmd.exe",
                        "/k",
                        helper_command,
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
                return 0, f"launched resume worker in Windows Terminal tab: {helper_command}"

            start_command = f'start "" cmd.exe /k {helper_command}'
            subprocess.Popen(
                ["cmd.exe", "/c", start_command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            return 0, f"launched resume worker in new cmd window: {helper_command}"

        subprocess.Popen(helper_args, start_new_session=True, close_fds=True)
        return 0, f"launched resume worker process: {helper_args!r}"
    except FileNotFoundError:
        return 127, "python executable or terminal launcher was not found on PATH"
    except OSError as exc:
        return 1, f"failed to launch resume worker: {exc!r}"


def run_resume_worker(session_id: str, trigger_reason: str, trigger_token: str) -> int:
    ensure_runtime_dirs()
    spath = state_path(session_id)
    log_file = log_path(session_id)
    state = read_json(spath)
    state["resume_worker_pid"] = os.getpid()
    state["resume_worker_reason"] = trigger_reason
    state["resume_worker_trigger_token"] = trigger_token
    state["resume_worker_started_at"] = now_iso()
    state["resume_launch_pending_token"] = None
    state["resume_launch_pending_at"] = None
    write_json(spath, state)
    append_log(
        log_file,
        "Resume worker started "
        f"pid={os.getpid()}, reason={trigger_reason}, token={trigger_token}.",
    )

    try:
        return_code, output = perform_resume_command(session_id)
        state = read_json(spath)
        state["resume_worker_pid"] = None
        state["resume_worker_finished_at"] = now_iso()
        state["resume_worker_exit_code"] = return_code
        state["resume_worker_output"] = preview(output, 400)
        write_json(spath, state)
        if return_code == 0:
            append_log(
                log_file,
                "Resume worker finished successfully "
                f"reason={trigger_reason}, output={preview(output, 240)}",
            )
        else:
            append_log(
                log_file,
                "Resume worker failed "
                f"reason={trigger_reason}, exit_code={return_code}, output={preview(output, 400)}",
            )
        return return_code
    except Exception as exc:  # noqa: BLE001
        state = read_json(spath)
        state["resume_worker_pid"] = None
        state["resume_worker_finished_at"] = now_iso()
        state["resume_worker_exit_code"] = 1
        state["resume_worker_output"] = repr(exc)
        write_json(spath, state)
        append_log(log_file, f"Resume worker crashed: {exc!r}")
        return 1


def build_base_state(interval: float, session_id: str) -> dict[str, Any]:
    log_file = log_path(session_id)
    current_state = read_json(state_path(session_id))
    for stale_key in (
        "stop_keyword",
        "last_keyword_timestamp",
        "last_keyword_signature",
        "last_keyword_preview",
    ):
        current_state.pop(stale_key, None)
    started_at = current_state.get("started_at") or now_iso()
    launcher_pid = current_state.get("launcher_pid")
    supervisor_pid = launcher_pid or current_state.get("pid") or os.getpid()
    return {
        **current_state,
        "session_id": session_id,
        "interval_seconds": interval,
        "pid": supervisor_pid,
        "launcher_pid": launcher_pid,
        "runner_pid": os.getpid(),
        "started_at": started_at,
        "status": current_state.get("status") or "running",
        "script_path": str(Path(__file__).resolve()),
        "state_file": str(state_path(session_id)),
        "log_file": str(log_file),
        "resume_prompt": RESUME_PROMPT,
    }


def start_monitor(interval: float, session_id: str) -> int:
    if interval <= 0:
        print("Interval must be greater than 0 seconds.", file=sys.stderr)
        return 1

    ensure_runtime_dirs()
    spath = state_path(session_id)
    log_file = log_path(session_id)
    append_log(
        log_file,
        f"Start requested: session={session_id}, interval={interval}s.",
    )
    existing_state = read_json(spath)
    existing_pid = int(existing_state.get("launcher_pid") or existing_state.get("pid") or 0)
    existing_runner_pid = int(existing_state.get("runner_pid") or 0)
    if (
        existing_pid
        and is_pid_running(existing_pid)
        or existing_runner_pid
        and is_pid_running(existing_runner_pid)
    ):
        append_log(
            log_file,
            f"Watcher already running; launcher_pid={existing_pid}, runner_pid={existing_runner_pid}.",
        )
        print(f"Watcher already running for {session_id} (PID {existing_pid}).")
        print(f"State: {spath}")
        print(f"Log:   {log_path(session_id)}")
        return 0

    python_command = subprocess.list2cmdline(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "__run__",
            str(interval),
            session_id,
        ]
    )
    child_args: list[str]
    creationflags = 0
    popen_kwargs: dict[str, Any] = {"env": {**os.environ, "PYTHONUNBUFFERED": "1"}}
    if os.name == "nt":
        child_args = ["cmd.exe", "/k", python_command]
        creationflags = (
            subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        child_args = [
            sys.executable,
            str(Path(__file__).resolve()),
            "__run__",
            str(interval),
            session_id,
        ]
        popen_kwargs["start_new_session"] = True
        log_handle = log_file.open("a", encoding="utf-8")
        popen_kwargs.update(
            {
                "stdin": subprocess.DEVNULL,
                "stdout": log_handle,
                "stderr": log_handle,
                "close_fds": True,
            }
        )

    append_log(
        log_file,
        f"Launching watcher process: {child_args!r}",
    )
    process = subprocess.Popen(
        child_args,
        creationflags=creationflags,
        **popen_kwargs,
    )
    if os.name != "nt":
        log_handle.close()

    initial_state = {
        "session_id": session_id,
        "interval_seconds": interval,
        "pid": process.pid,
        "launcher_pid": process.pid if os.name == "nt" else None,
        "runner_pid": None,
        "started_at": now_iso(),
        "status": "starting",
        "script_path": str(Path(__file__).resolve()),
        "state_file": str(spath),
        "log_file": str(log_file),
        "resume_prompt": RESUME_PROMPT,
    }
    write_json(spath, initial_state)
    print(f"Started watcher for {session_id}.")
    print(f"PID:   {process.pid}")
    if os.name == "nt":
        print("Mode:  cmd console")
    print(f"State: {spath}")
    print(f"Log:   {log_file}")
    return 0


def stop_monitor(session_id: str) -> int:
    spath = state_path(session_id)
    state = read_json(spath)
    log_file = Path(state.get("log_file") or log_path(session_id))
    append_log(log_file, f"Stop requested: session={session_id}.")
    if not state:
        print(f"No watcher state found for {session_id}.")
        return 0

    launcher_pid = int(state.get("launcher_pid") or 0)
    runner_pid = int(state.get("runner_pid") or state.get("pid") or 0)
    pid = launcher_pid if launcher_pid and is_pid_running(launcher_pid) else runner_pid
    append_log(
        log_file,
        f"Resolved stop target: launcher_pid={launcher_pid}, runner_pid={runner_pid}, selected_pid={pid}.",
    )
    if not pid or not is_pid_running(pid):
        if spath.exists():
            spath.unlink()
        append_log(log_file, "Removed stale watcher state.")
        print(f"Removed stale watcher state for {session_id}.")
        return 0

    append_log(log_file, f"Stopping watcher process tree for PID {pid}.")
    return_code, output = terminate_pid(pid)
    if spath.exists():
        spath.unlink()
    if return_code != 0:
        print(output or f"Failed to stop watcher PID {pid}.", file=sys.stderr)
        return 1

    print(f"Stopped watcher for {session_id} (PID {pid}).")
    print(f"Log: {log_file}")
    return 0


def monitor_loop(interval: float, session_id: str) -> int:
    ensure_runtime_dirs()
    log_file = log_path(session_id)
    spath = state_path(session_id)
    state = build_base_state(interval, session_id)
    write_json(spath, state)
    append_log(
        log_file,
        "Watcher booted for session "
        f"{session_id} with PID {os.getpid()} and interval {interval}s. "
        f"tail_records={TAIL_RECORD_COUNT}, stable_check_interval={STABLE_CHECK_INTERVAL_SECONDS}s, "
        f"unchanged_polls_before_resume={UNCHANGED_POLLS_BEFORE_RESUME}, "
        f"post_resume_grace={POST_RESUME_GRACE_SECONDS}s.",
    )

    while True:
        try:
            state = build_base_state(interval, session_id)
            state["heartbeat_at"] = now_iso()
            append_log(
                log_file,
                f"Polling tick: session={session_id}, interval={interval}s.",
            )

            pending_trigger_token = state.get("resume_launch_pending_token")
            pending_trigger_at = parse_iso(state.get("resume_launch_pending_at"))
            if pending_trigger_token and pending_trigger_at is not None:
                pending_age = (
                    datetime.now(timezone.utc) - pending_trigger_at
                ).total_seconds()
                if pending_age < max(15.0, interval * 3):
                    state["status"] = "resume-launch-pending"
                    state["last_checked_at"] = now_iso()
                    append_log(
                        log_file,
                        "Resume launch is pending; skipping trigger evaluation "
                        f"token={pending_trigger_token}, age={pending_age:.1f}s.",
                    )
                    write_json(spath, state)
                    time.sleep(interval)
                    continue
                state["resume_launch_pending_token"] = None
                state["resume_launch_pending_at"] = None
                append_log(
                    log_file,
                    f"Cleared stale pending resume launch token={pending_trigger_token}.",
                )

            resume_worker_pid = int(state.get("resume_worker_pid") or 0)
            if resume_worker_pid and is_pid_running(resume_worker_pid):
                state["status"] = "resume-in-flight"
                state["last_checked_at"] = now_iso()
                append_log(
                    log_file,
                    "Resume worker still running; skipping trigger evaluation "
                    f"pid={resume_worker_pid}, reason={state.get('resume_worker_reason')}.",
                )
                write_json(spath, state)
                time.sleep(interval)
                continue
            if resume_worker_pid:
                state["resume_worker_pid"] = None
                state["resume_worker_finished_at"] = state.get("resume_worker_finished_at") or now_iso()
                append_log(
                    log_file,
                    f"Cleared stale resume worker pid={resume_worker_pid}.",
                )

            resume_grace_until = parse_iso(state.get("resume_grace_until"))
            if resume_grace_until is not None:
                remaining_grace = (
                    resume_grace_until - datetime.now(timezone.utc)
                ).total_seconds()
                if remaining_grace > 0:
                    state["status"] = "post-resume-grace"
                    state["last_checked_at"] = now_iso()
                    append_log(
                        log_file,
                        "Post-resume grace active; skipping trigger evaluation "
                        f"remaining={remaining_grace:.1f}s.",
                    )
                    write_json(spath, state)
                    time.sleep(interval)
                    continue
                state["resume_grace_until"] = None
                append_log(log_file, "Post-resume grace expired; resuming normal checks.")

            session_file = state.get("session_file")
            resolved_session_file: Path | None = None
            if session_file:
                candidate = Path(str(session_file))
                if candidate.exists():
                    resolved_session_file = candidate
                    append_log(
                        log_file,
                        f"Using cached session file: {resolved_session_file}.",
                    )

            if resolved_session_file is None:
                resolved_session_file = find_session_file(session_id)
                if resolved_session_file is not None:
                    state["session_file"] = str(resolved_session_file)
                    append_log(
                        log_file,
                        f"Resolved session file to {resolved_session_file}.",
                    )

            if resolved_session_file is None:
                state["status"] = "waiting-for-session-file"
                state["last_checked_at"] = now_iso()
                append_log(
                    log_file,
                    f"Session file not found yet for session={session_id}; waiting.",
                )
                write_json(spath, state)
                time.sleep(interval)
                continue

            stat = resolved_session_file.stat()
            file_signature = f"{stat.st_mtime_ns}:{stat.st_size}"
            state["last_checked_at"] = now_iso()
            state["last_file_signature"] = file_signature
            state["session_file"] = str(resolved_session_file)
            previous_signature = state.get("last_processed_file_signature")
            trigger_reason: str | None = None
            trigger_token: str | None = None

            if file_signature != previous_signature:
                append_log(
                    log_file,
                    f"Detected session file change: previous={previous_signature}, current={file_signature}.",
                )
                is_initial_snapshot = previous_signature is None
                state["consecutive_unchanged_polls"] = 0
                state["last_stable_probe_at"] = None
                tail_window = inspect_tail_window(resolved_session_file, TAIL_RECORD_COUNT)
                state["last_processed_file_signature"] = file_signature
                state["last_tail_line_count"] = tail_window["tail_line_count"]
                latest_message = tail_window["latest_assistant"]
                if latest_message is not None:
                    message_timestamp, message_text, message_signature = latest_message
                    state["last_message_timestamp"] = message_timestamp
                    state["last_message_signature"] = message_signature
                    state["last_message_preview"] = preview(message_text)
                    append_log(
                        log_file,
                        "Tail window inspected "
                        f"(records={tail_window['tail_line_count']}). "
                        f"Latest assistant message timestamp={message_timestamp}, "
                        f"preview={preview(message_text, 180)}",
                    )
                    if is_initial_snapshot:
                        state["initial_snapshot_at"] = now_iso()
                        state["status"] = "idle"
                        append_log(
                            log_file,
                            "Initial session snapshot captured; suppressing trigger evaluation "
                            "for pre-existing tail content.",
                        )
                    else:
                        state["status"] = "idle"
                        append_log(
                            log_file,
                            "File changed; reset stable counters and continue waiting for the stable-file rule.",
                        )
                else:
                    state["status"] = "idle"
                    append_log(
                        log_file,
                        "No assistant message could be extracted from the session file.",
                    )
            else:
                last_stable_probe_at = parse_iso(state.get("last_stable_probe_at"))
                stable_probe_due = (
                    last_stable_probe_at is None
                    or (
                        datetime.now(timezone.utc) - last_stable_probe_at
                    ).total_seconds()
                    >= STABLE_CHECK_INTERVAL_SECONDS
                )
                if stable_probe_due:
                    consecutive_unchanged_polls = int(state.get("consecutive_unchanged_polls") or 0) + 1
                    state["consecutive_unchanged_polls"] = consecutive_unchanged_polls
                    state["last_stable_probe_at"] = now_iso()
                    append_log(
                        log_file,
                        "Session file unchanged and stable probe counted "
                        f"({file_signature}); consecutive_unchanged_polls={consecutive_unchanged_polls}/"
                        f"{UNCHANGED_POLLS_BEFORE_RESUME}, stable_interval={STABLE_CHECK_INTERVAL_SECONDS}s.",
                    )
                    if consecutive_unchanged_polls >= UNCHANGED_POLLS_BEFORE_RESUME:
                        trigger_reason = "stable-file"
                        stable_anchor = state.get("last_message_signature") or file_signature
                        trigger_token = f"{trigger_reason}:{stable_anchor}"
                        append_log(
                            log_file,
                            "Primary trigger candidate detected from stable file: "
                            f"reason={trigger_reason}, token={trigger_token}.",
                        )
                else:
                    remaining_probe = STABLE_CHECK_INTERVAL_SECONDS - (
                        datetime.now(timezone.utc) - last_stable_probe_at
                    ).total_seconds()
                    append_log(
                        log_file,
                        "Session file unchanged but stable probe not due yet "
                        f"({file_signature}); next_probe_in={max(remaining_probe, 0):.1f}s.",
                    )

            if trigger_reason is not None and trigger_token is not None:
                same_trigger = trigger_token == state.get("last_attempt_trigger_token")
                if same_trigger and not should_retry_same_trigger(state, interval):
                    state["status"] = "trigger-cooldown"
                    append_log(
                        log_file,
                        "Trigger cooldown active for current stable state; waiting before another launch.",
                    )
                else:
                    state["status"] = "resuming"
                    state["last_attempt_trigger_token"] = trigger_token
                    state["last_attempt_reason"] = trigger_reason
                    state["last_attempt_at"] = now_iso()
                    state["resume_launch_pending_token"] = trigger_token
                    state["resume_launch_pending_at"] = now_iso()
                    write_json(spath, state)
                    append_log(
                        log_file,
                        f"Trigger accepted; reason={trigger_reason}, token={trigger_token}.",
                    )
                    append_log(
                        log_file,
                        "Launching resume worker terminal for command: codex exec resume "
                        "--skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "
                        f"{session_id} {RESUME_PROMPT}",
                    )
                    return_code, output = launch_resume_command(
                        session_id, trigger_reason, trigger_token
                    )
                    state = build_base_state(interval, session_id)
                    state["session_file"] = str(resolved_session_file)
                    state["last_processed_file_signature"] = file_signature
                    state["last_file_signature"] = file_signature
                    state["last_checked_at"] = now_iso()
                    state["last_attempt_trigger_token"] = trigger_token
                    state["last_attempt_reason"] = trigger_reason
                    state["last_attempt_at"] = now_iso()
                    state["last_resume_exit_code"] = return_code
                    state["last_resume_output"] = preview(output, limit=800)
                    state["consecutive_unchanged_polls"] = 0
                    state["last_stable_probe_at"] = None
                    if return_code == 0:
                        state["status"] = "idle"
                        state["last_resume_trigger_token"] = trigger_token
                        state["last_resume_reason"] = trigger_reason
                        state["last_resume_at"] = now_iso()
                        state["resume_grace_until"] = future_iso(POST_RESUME_GRACE_SECONDS)
                        append_log(
                            log_file,
                            "Resume worker launched successfully. "
                            f"reason={trigger_reason}, output={preview(output, 240)}",
                        )
                    else:
                        state["status"] = "resume-failed"
                        state["resume_launch_pending_token"] = None
                        state["resume_launch_pending_at"] = None
                        state["resume_grace_until"] = None
                        append_log(
                            log_file,
                            "Resume worker launch failed "
                            f"reason={trigger_reason}, exit_code={return_code}: {preview(output, 800)}",
                        )

            write_json(spath, state)
        except Exception as exc:  # noqa: BLE001
            state = build_base_state(interval, session_id)
            state["status"] = "error"
            state["last_error"] = repr(exc)
            state["last_error_at"] = now_iso()
            write_json(spath, state)
            append_log(log_file, f"Monitor iteration failed: {exc!r}")

        time.sleep(interval)


def parse_user_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Start or stop a watcher that auto-resumes a paused Codex session after "
            "the session file stays unchanged across the configured stable-file checks. "
            "On Windows, start opens a new cmd console for the watcher."
        )
    )
    parser.add_argument(
        "interval",
        type=float,
        help="Polling interval in seconds. Keep passing the same positional layout for stop.",
    )
    parser.add_argument("action", choices=["start", "stop"])
    parser.add_argument("session_id", help="Codex session id to monitor.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    if len(argv) >= 4 and argv[1] == "__run__":
        interval = float(argv[2])
        session_id = argv[3]
        return monitor_loop(interval, session_id)
    if len(argv) >= 5 and argv[1] == "__resume__":
        session_id = argv[2]
        trigger_reason = argv[3]
        trigger_token = argv[4]
        return run_resume_worker(session_id, trigger_reason, trigger_token)

    args = parse_user_args(argv[1:])
    if args.action == "start":
        return start_monitor(args.interval, args.session_id)
    return stop_monitor(args.session_id)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
