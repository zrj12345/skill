#!/usr/bin/env python3
"""Prune a Codex home directory while preserving a small recent tail."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import time
from pathlib import Path


SAFE_DELETE_DIRS = [
    "archived_sessions",
    ".tmp",
    "tmp",
    "cache",
    "log",
    ".sandbox-bin",
]

SAFE_DELETE_FILES = [
    "sandbox.log",
]

SAFE_DELETE_GLOBS = [
    "config.toml.bak.*",
]

PROFILES = {
    "light": {
        "keep_sessions": 20,
        "keep_logs": 20000,
        "keep_session_days": 14.0,
        "keep_log_days": 7.0,
    },
    "standard": {
        "keep_sessions": 5,
        "keep_logs": 1000,
        "keep_session_days": 3.0,
        "keep_log_days": 1.0,
    },
    "aggressive": {
        "keep_sessions": 2,
        "keep_logs": 200,
        "keep_session_days": 0.0,
        "keep_log_days": 0.0,
    },
    "purge": {
        "keep_sessions": 0,
        "keep_logs": 0,
        "keep_session_days": 0.0,
        "keep_log_days": 0.0,
    },
}


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def tree_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return file_size(path)

    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += file_size(child)
    return total


def format_mb(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def ensure_codex_root(path: Path) -> None:
    if path.name.lower() != ".codex":
        raise SystemExit(f"Refusing to clean a non-.codex path: {path}")


def newest_files(root: Path) -> list[Path]:
    files = [p for p in root.rglob("*") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def cutoff_epoch(days: float | None) -> float | None:
    if days is None or days <= 0:
        return None
    return time.time() - (days * 86400.0)


def remove_empty_dirs(root: Path) -> None:
    if not root.exists():
        return
    for child in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            next(child.iterdir())
        except StopIteration:
            child.rmdir()


def prune_sessions(path: Path, keep: int, keep_days: float | None, execute: bool) -> tuple[int, int, int]:
    if not path.exists():
        return 0, 0, 0

    files = newest_files(path)
    keep_set: set[Path] = set()

    if keep > 0:
        keep_set.update(files[:keep])

    session_cutoff = cutoff_epoch(keep_days)
    if session_cutoff is not None:
        for item in files:
            if item.stat().st_mtime >= session_cutoff:
                keep_set.add(item)

    to_remove = [item for item in files if item not in keep_set]
    reclaimed = sum(file_size(item) for item in to_remove)

    if execute:
        for item in to_remove:
            item.unlink(missing_ok=True)
        remove_empty_dirs(path)

    return len(to_remove), reclaimed, len(keep_set)


def retained_log_count(cursor: sqlite3.Cursor, keep: int, keep_days: float | None) -> int:
    selects = []
    params: list[int] = []

    log_cutoff = cutoff_epoch(keep_days)
    if log_cutoff is not None:
        selects.append("select id from logs where ts >= ?")
        params.append(int(log_cutoff))

    if keep > 0:
        selects.append("select id from (select id from logs order by id desc limit ?)")
        params.append(keep)

    if not selects:
        return 0

    sql = "select count(*) from logs where id in (" + " union ".join(selects) + ")"
    return cursor.execute(sql, params).fetchone()[0]


def prune_logs(db_path: Path, keep: int, keep_days: float | None, execute: bool) -> tuple[int, int, int, list[str]]:
    if not db_path.exists():
        return 0, 0, 0, []

    notes: list[str] = []
    before_size = file_size(db_path)
    deleted_rows = 0

    connection = sqlite3.connect(db_path, timeout=30)
    cursor = connection.cursor()

    try:
        before_rows = cursor.execute("select count(*) from logs").fetchone()[0]
    except sqlite3.Error as exc:
        connection.close()
        raise SystemExit(f"Could not inspect logs table: {exc}") from exc

    kept_rows = retained_log_count(cursor, keep, keep_days)
    deleted_rows = max(before_rows - kept_rows, 0)

    if execute and deleted_rows > 0:
        log_cutoff = cutoff_epoch(keep_days)
        selects = []
        params: list[int] = []

        if log_cutoff is not None:
            selects.append("select id from logs where ts >= ?")
            params.append(int(log_cutoff))

        if keep > 0:
            selects.append("select id from (select id from logs order by id desc limit ?)")
            params.append(keep)

        if selects:
            cursor.execute(
                "delete from logs where id not in (" + " union ".join(selects) + ")",
                params,
            )
        else:
            cursor.execute("delete from logs")

        deleted_rows = cursor.rowcount
        connection.commit()

        for statement in ("PRAGMA wal_checkpoint(TRUNCATE)", "VACUUM"):
            try:
                cursor.execute(statement)
                connection.commit()
            except sqlite3.Error as exc:
                notes.append(f"{statement} failed: {exc}")

    connection.close()

    after_size = file_size(db_path)
    if execute:
        reclaimed = max(before_size - after_size, 0)
    elif before_rows > 0:
        reclaimed = int(before_size * (deleted_rows / before_rows))
    else:
        reclaimed = 0
    return kept_rows, deleted_rows, reclaimed, notes


def resolve_retention(
    profile_name: str,
    keep_sessions: int | None,
    keep_logs: int | None,
    keep_session_days: float | None,
    keep_log_days: float | None,
) -> dict[str, float | int]:
    profile = PROFILES[profile_name]
    return {
        "keep_sessions": profile["keep_sessions"] if keep_sessions is None else keep_sessions,
        "keep_logs": profile["keep_logs"] if keep_logs is None else keep_logs,
        "keep_session_days": profile["keep_session_days"] if keep_session_days is None else keep_session_days,
        "keep_log_days": profile["keep_log_days"] if keep_log_days is None else keep_log_days,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=str(Path.home() / ".codex"))
    parser.add_argument("--profile", choices=sorted(PROFILES), default="standard")
    parser.add_argument("--keep-sessions", type=int)
    parser.add_argument("--keep-logs", type=int)
    parser.add_argument("--keep-session-days", type=float)
    parser.add_argument("--keep-log-days", type=float)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    ensure_codex_root(root)
    if not root.exists():
        raise SystemExit(f"Path does not exist: {root}")

    retention = resolve_retention(
        profile_name=args.profile,
        keep_sessions=args.keep_sessions,
        keep_logs=args.keep_logs,
        keep_session_days=args.keep_session_days,
        keep_log_days=args.keep_log_days,
    )

    total_before = tree_size(root)
    reclaimed = 0
    notes: list[str] = []

    print(f"Root: {root}")
    print(f"Mode: {'execute' if args.execute else 'dry-run'}")
    print(
        "Retention: "
        f"profile={args.profile}, "
        f"keep_sessions={retention['keep_sessions']}, "
        f"keep_session_days={retention['keep_session_days']}, "
        f"keep_logs={retention['keep_logs']}, "
        f"keep_log_days={retention['keep_log_days']}"
    )

    for name in SAFE_DELETE_DIRS:
        path = root / name
        size = tree_size(path)
        if size == 0:
            continue
        print(f"Delete dir: {name} ({format_mb(size)})")
        reclaimed += size
        if args.execute:
            shutil.rmtree(path, ignore_errors=False)

    for name in SAFE_DELETE_FILES:
        path = root / name
        size = tree_size(path)
        if size == 0:
            continue
        print(f"Delete file: {name} ({format_mb(size)})")
        reclaimed += size
        if args.execute:
            path.unlink(missing_ok=True)

    for pattern in SAFE_DELETE_GLOBS:
        for path in root.glob(pattern):
            size = tree_size(path)
            print(f"Delete file: {path.name} ({format_mb(size)})")
            reclaimed += size
            if args.execute:
                path.unlink(missing_ok=True)

    removed_sessions, session_bytes, kept_sessions = prune_sessions(
        root / "sessions",
        int(retention["keep_sessions"]),
        float(retention["keep_session_days"]),
        args.execute,
    )
    reclaimed += session_bytes
    print(
        "Prune sessions: "
        f"remove {removed_sessions} file(s), "
        f"keep {kept_sessions} file(s), "
        f"reclaim {format_mb(session_bytes)}"
    )

    kept_logs, removed_logs, log_bytes, log_notes = prune_logs(
        root / "logs_2.sqlite",
        int(retention["keep_logs"]),
        float(retention["keep_log_days"]),
        args.execute,
    )
    reclaimed += log_bytes
    notes.extend(log_notes)
    print(
        "Prune logs_2.sqlite: "
        f"remove about {removed_logs} row(s), "
        f"keep {kept_logs} row(s), "
        f"reclaim about {format_mb(log_bytes)}"
    )

    total_after = tree_size(root) if args.execute else total_before - reclaimed
    print("")
    print(f"Before: {format_mb(total_before)}")
    print(f"After:  {format_mb(total_after)}")
    print(f"Freed:  {format_mb(max(total_before - total_after, 0))}")

    if notes:
        print("")
        print("Notes:")
        for note in notes:
            print(f"  - {note}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
