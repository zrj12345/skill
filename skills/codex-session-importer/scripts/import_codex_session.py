#!/usr/bin/env python3
"""Import a copied Codex JSONL session into the local Codex Desktop state."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register a copied Codex rollout JSONL in local Codex Desktop state."
    )
    parser.add_argument("session_jsonl", help="Path to rollout-*.jsonl copied from another machine.")
    parser.add_argument(
        "--project-cwd",
        default=os.getcwd(),
        help="Local workspace/project root for the Codex App sidebar. Defaults to current directory.",
    )
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"),
        help="Local Codex home directory. Defaults to CODEX_HOME or ~/.codex.",
    )
    parser.add_argument("--title", help="Override the thread title shown in the sidebar.")
    parser.add_argument(
        "--rewrite-turn-context-cwd",
        action="store_true",
        help="Also rewrite historical turn_context payload.cwd values from old cwd to project cwd.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect and print planned changes without modifying files.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at line {line_no}: {exc}") from exc
    if not rows:
        raise SystemExit("Session JSONL is empty.")
    first = rows[0]
    if first.get("type") != "session_meta" or not isinstance(first.get("payload"), dict):
        raise SystemExit("First JSONL record must be a session_meta payload.")
    if not first["payload"].get("id"):
        raise SystemExit("session_meta.payload.id is missing.")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def format_rollout_name(created: datetime, session_id: str) -> str:
    local = created.astimezone()
    stamp = local.strftime("%Y-%m-%dT%H-%M-%S")
    return f"rollout-{stamp}-{session_id}.jsonl"


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(1, 1000):
        candidate = path.with_name(f"{stem}-imported-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise SystemExit(f"Cannot find a free import path near {path}")


def target_rollout_path(source: Path, sessions_root: Path, rows: list[dict[str, Any]]) -> Path:
    if is_relative_to(source, sessions_root):
        return source

    meta = rows[0]["payload"]
    session_id = meta["id"]
    created = parse_time(meta.get("timestamp")) or parse_time(rows[0].get("timestamp")) or datetime.now(timezone.utc)
    local = created.astimezone()
    folder = sessions_root / local.strftime("%Y") / local.strftime("%m") / local.strftime("%d")
    name = source.name if source.suffix.lower() == ".jsonl" else format_rollout_name(created, session_id)
    return unique_path(folder / name)


def extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            text = item.get("text") or item.get("content")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts).strip()


def collect_metadata(rows: list[dict[str, Any]], title_override: str | None) -> dict[str, Any]:
    meta = rows[0]["payload"]
    session_id = meta["id"]
    title = title_override
    first_user_message = ""
    updated_dt = parse_time(rows[0].get("timestamp")) or datetime.now(timezone.utc)
    tokens_used = 0
    turn_context: dict[str, Any] = {}

    for row in rows:
        row_dt = parse_time(row.get("timestamp"))
        if row_dt and row_dt > updated_dt:
            updated_dt = row_dt

        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        payload_type = payload.get("type")
        if payload_type == "thread_name_updated" and payload.get("thread_id") == session_id:
            if not title_override and payload.get("thread_name"):
                title = payload["thread_name"]
        elif row.get("type") == "turn_context":
            turn_context = payload
        elif row.get("type") == "response_item" and payload_type == "message":
            if payload.get("role") == "user" and not first_user_message:
                first_user_message = extract_text_from_content(payload.get("content"))
        elif row.get("type") == "event_msg" and payload_type == "token_count":
            info = payload.get("info")
            usage = info.get("total_token_usage", {}) if isinstance(info, dict) else {}
            try:
                total = int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
                tokens_used = max(tokens_used, total)
            except (TypeError, ValueError):
                pass

    if not title:
        title = first_user_message[:80] if first_user_message else "Imported Codex session"

    created_dt = parse_time(meta.get("timestamp")) or parse_time(rows[0].get("timestamp")) or updated_dt
    sandbox_policy = turn_context.get("sandbox_policy") or {"type": "danger-full-access"}
    approval_mode = turn_context.get("approval_policy") or "never"

    return {
        "id": session_id,
        "title": title,
        "first_user_message": first_user_message,
        "created_dt": created_dt,
        "updated_dt": updated_dt,
        "source": meta.get("source") or "vscode",
        "model_provider": meta.get("model_provider") or "",
        "cli_version": meta.get("cli_version") or "",
        "model": turn_context.get("model"),
        "reasoning_effort": turn_context.get("effort"),
        "sandbox_policy": json.dumps(sandbox_policy, separators=(",", ":")),
        "approval_mode": approval_mode,
        "tokens_used": tokens_used,
        "git_sha": (meta.get("git") or {}).get("commit_hash"),
        "git_branch": (meta.get("git") or {}).get("branch"),
        "old_cwd": meta.get("cwd"),
    }


def backup_file(path: Path, backup_dir: Path) -> None:
    if path.exists():
        shutil.copy2(path, backup_dir / path.name)


def backup_sqlite(db_path: Path, backup_dir: Path) -> None:
    if not db_path.exists():
        return
    backup_path = backup_dir / db_path.name
    src = sqlite3.connect(str(db_path), timeout=30)
    dst = sqlite3.connect(str(backup_path))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def make_backup(codex_home: Path, source: Path, target: Path) -> Path:
    backup_dir = codex_home / "tmp" / ("session-import-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file(source, backup_dir)
    if target != source:
        backup_file(target, backup_dir)
    backup_file(codex_home / "session_index.jsonl", backup_dir)
    backup_file(codex_home / ".codex-global-state.json", backup_dir)
    backup_sqlite(codex_home / "state_5.sqlite", backup_dir)
    return backup_dir


def update_session_rows(
    rows: list[dict[str, Any]],
    project_cwd: str,
    rewrite_turn_context: bool,
) -> tuple[list[dict[str, Any]], int]:
    changed = 0
    old_cwd = rows[0]["payload"].get("cwd")
    if rows[0]["payload"].get("cwd") != project_cwd:
        rows[0]["payload"]["cwd"] = project_cwd
        changed += 1
    if rewrite_turn_context:
        for row in rows:
            if row.get("type") == "turn_context":
                payload = row.get("payload")
                if isinstance(payload, dict) and payload.get("cwd") == old_cwd:
                    payload["cwd"] = project_cwd
                    changed += 1
    return rows, changed


def update_threads_db(db_path: Path, rollout_path: Path, project_cwd: str, info: dict[str, Any]) -> None:
    if not db_path.exists():
        raise SystemExit(f"Missing Codex state database: {db_path}")

    con = sqlite3.connect(str(db_path), timeout=30)
    con.row_factory = sqlite3.Row
    try:
        tables = {row[0] for row in con.execute("select name from sqlite_master where type='table'")}
        if "threads" not in tables:
            raise SystemExit(f"Database has no threads table: {db_path}")

        columns = [dict(row) for row in con.execute("pragma table_info(threads)")]
        column_names = {row["name"] for row in columns}
        created_ms = int(info["created_dt"].timestamp() * 1000)
        updated_ms = int(info["updated_dt"].timestamp() * 1000)
        values = {
            "id": info["id"],
            "rollout_path": str(rollout_path),
            "created_at": created_ms // 1000,
            "updated_at": updated_ms // 1000,
            "source": info["source"],
            "model_provider": info["model_provider"],
            "cwd": project_cwd,
            "title": info["title"],
            "sandbox_policy": info["sandbox_policy"],
            "approval_mode": info["approval_mode"],
            "tokens_used": info["tokens_used"],
            "has_user_event": 1 if info["first_user_message"] else 0,
            "archived": 0,
            "archived_at": None,
            "git_sha": info["git_sha"],
            "git_branch": info["git_branch"],
            "git_origin_url": None,
            "cli_version": info["cli_version"],
            "first_user_message": info["first_user_message"],
            "agent_nickname": None,
            "agent_role": None,
            "memory_mode": "enabled",
            "model": info["model"],
            "reasoning_effort": info["reasoning_effort"],
            "agent_path": None,
            "created_at_ms": created_ms,
            "updated_at_ms": updated_ms,
        }
        values = {key: value for key, value in values.items() if key in column_names}

        exists = con.execute("select count(*) from threads where id=?", (info["id"],)).fetchone()[0] > 0
        if exists:
            updates = {k: v for k, v in values.items() if k != "id"}
            assignments = ", ".join(f"{name}=?" for name in updates)
            con.execute(
                f"update threads set {assignments} where id=?",
                [*updates.values(), info["id"]],
            )
        else:
            names = list(values.keys())
            placeholders = ", ".join("?" for _ in names)
            con.execute(
                f"insert into threads ({', '.join(names)}) values ({placeholders})",
                [values[name] for name in names],
            )
        con.commit()
    finally:
        con.close()


def update_session_index(index_path: Path, info: dict[str, Any]) -> None:
    entries: list[Any] = []
    if index_path.exists():
        for raw in index_path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                entries.append(raw)
                continue
            if obj.get("id") != info["id"]:
                entries.append(obj)

    updated_at = info["updated_dt"].astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    entries.append({"id": info["id"], "thread_name": info["title"], "updated_at": updated_at})

    with index_path.open("w", encoding="utf-8", newline="\n") as f:
        for entry in entries:
            if isinstance(entry, str):
                f.write(entry + "\n")
            else:
                f.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")


def update_workspace_state(global_state_path: Path, info: dict[str, Any], project_cwd: str) -> bool:
    if not global_state_path.exists():
        return False
    try:
        state = json.loads(global_state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    def update_obj(obj: dict[str, Any]) -> None:
        obj.setdefault("thread-workspace-root-hints", {})[info["id"]] = project_cwd
        if isinstance(obj.get("projectless-thread-ids"), list):
            obj["projectless-thread-ids"] = [x for x in obj["projectless-thread-ids"] if x != info["id"]]
        for key in ("electron-saved-workspace-roots", "active-workspace-roots", "project-order"):
            if isinstance(obj.get(key), list) and project_cwd not in obj[key]:
                obj[key].insert(0, project_cwd)

    if isinstance(state, dict):
        update_obj(state)
        nested = state.get("electron-persisted-atom-state")
        if isinstance(nested, dict):
            update_obj(nested)

    global_state_path.write_text(
        json.dumps(state, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return True


def main() -> int:
    args = parse_args()
    source = Path(args.session_jsonl).expanduser().resolve()
    codex_home = Path(args.codex_home).expanduser().resolve()
    sessions_root = codex_home / "sessions"
    project_cwd = str(Path(args.project_cwd).expanduser().resolve())

    if not source.exists():
        raise SystemExit(f"Session JSONL not found: {source}")
    if not codex_home.exists():
        raise SystemExit(f"Codex home not found: {codex_home}")

    rows = read_jsonl(source)
    info = collect_metadata(rows, args.title)
    target = target_rollout_path(source, sessions_root, rows)
    target_same_as_source = source == target.resolve() if target.exists() else source == target

    summary = {
        "dry_run": args.dry_run,
        "session_id": info["id"],
        "title": info["title"],
        "old_cwd": info["old_cwd"],
        "project_cwd": project_cwd,
        "source_jsonl": str(source),
        "target_jsonl": str(target),
        "will_copy": not target_same_as_source,
        "rewrite_turn_context_cwd": args.rewrite_turn_context_cwd,
    }

    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    backup_dir = make_backup(codex_home, source, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target_same_as_source:
        shutil.copy2(source, target)

    target_rows = read_jsonl(target)
    target_rows, jsonl_changes = update_session_rows(
        target_rows,
        project_cwd,
        args.rewrite_turn_context_cwd,
    )
    if args.title:
        info["title"] = args.title
    write_jsonl(target, target_rows)

    # Recollect after metadata rewrite so timestamps and title remain grounded in the final file.
    info = collect_metadata(target_rows, args.title)
    update_threads_db(codex_home / "state_5.sqlite", target, project_cwd, info)
    update_session_index(codex_home / "session_index.jsonl", info)
    global_state_updated = update_workspace_state(codex_home / ".codex-global-state.json", info, project_cwd)

    summary.update(
        {
            "backup_dir": str(backup_dir),
            "jsonl_metadata_changes": jsonl_changes,
            "global_state_updated": global_state_updated,
            "restart_codex_desktop": True,
        }
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
