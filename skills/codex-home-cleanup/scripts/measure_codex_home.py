#!/usr/bin/env python3
"""Measure the size of a Codex home directory."""

from __future__ import annotations

import argparse
from pathlib import Path


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def tree_size(path: Path) -> int:
    if path.is_file():
        return file_size(path)

    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += file_size(child)
    return total


def format_mb(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.2f} MB"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=str(Path.home() / ".codex"))
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Path does not exist: {root}")

    items = []
    total = 0
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        size = tree_size(child)
        total += size
        items.append((size, child))

    items.sort(key=lambda row: row[0], reverse=True)

    print(f"Root: {root}")
    print(f"Total: {format_mb(total)}")
    print("")
    print("Largest entries:")
    for size, child in items[: args.top]:
        kind = "Dir" if child.is_dir() else "File"
        print(f"  {format_mb(size):>10}  {kind:<4}  {child.name}")

    sessions = root / "sessions"
    archived = root / "archived_sessions"
    if sessions.exists():
        session_files = [p for p in sessions.rglob("*") if p.is_file()]
        print("")
        print(f"Session files: {len(session_files)}")
    if archived.exists():
        archived_files = [p for p in archived.rglob("*") if p.is_file()]
        print(f"Archived session files: {len(archived_files)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
