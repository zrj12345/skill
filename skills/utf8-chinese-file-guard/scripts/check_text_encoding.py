#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


TEXT_EXTENSIONS = {
    ".go",
    ".proto",
    ".md",
    ".ps1",
    ".json",
    ".yaml",
    ".yml",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".vue",
    ".hook",
    ".sh",
    ".bat",
    ".txt",
    ".xml",
}
SKIP_PATH_MARKERS = (".pb.go", "/pb/", "\\pb\\", "package-lock.json", ".specify/")
WEIRD_COMMENT_PATTERNS = (
    "I don't know.",
    "I'm sorry.",
    "It's all right.",
    "What's wrong?",
    "What?",
    "Kuanjiang",
    "Zenium",
    "We're in the middle of nowhere.",
    "I've got two of them.",
    "It's a piece of paper.",
    "It's just a little bit too much.",
    "It's a hard-on paper chain.",
    "I'm not sure I'm going to be able to do that.",
    "I've got a record.",
    "I'm afraid.",
    "It's just a little bit of a platinum.",
    "It's been a long time.",
    "It's a long line of paper.",
    "We've got to get out of here.",
    "It's a big deal.",
    "It's not like I'm going to have to do this.",
    "It's not like we're going to have to do this.",
    "What's up?",
    "Wearing.",
)
SUSPICIOUS_CHARS = set("鍒鏈璁鏇鑾闄鏃褰绫璇鎸瀛娓锟閸鐗鍙妫鍖鍝浠诲幓鎴闂閿榛樺畾鍖呯洰彔")
COMMON_CHINESE = set(
    "的一是在不了有和设置信请求响应更新创建列表设备产品名称编码分页信息描述原因操作消息版本通知分类标签实体配置主题连接租户组织插件来源核心导入验证时间成功失败"
)
UNSAFE_PS_READ = re.compile(r"Get-Content\b[^\r\n]*-Raw", re.IGNORECASE)
UNSAFE_PS_WRITE = re.compile(r"Set-Content\b[^\r\n]*-Encoding\s+UTF8\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check UTF-8 Chinese text files for mojibake, suspicious comments, and unsafe PowerShell write patterns."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional file or directory paths to check. Defaults to tracked text files under --repo-root or the current working directory.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository or workspace root to scan when no explicit paths are provided. Defaults to the current working directory.",
    )
    return parser.parse_args()


def is_text_candidate(path: Path) -> bool:
    if any(marker in path.as_posix() for marker in SKIP_PATH_MARKERS):
        return False
    return path.suffix.lower() in TEXT_EXTENSIONS


def iter_git_files(repo_root: Path) -> list[Path]:
    output = subprocess.check_output(
        ["git", "-C", str(repo_root), "ls-files"],
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    result: list[Path] = []
    for rel in output.splitlines():
        path = repo_root / rel
        if not path.exists() or not path.is_file():
            continue
        if not is_text_candidate(path):
            continue
        result.append(path)
    return result


def iter_paths(args: argparse.Namespace) -> list[Path]:
    repo_root = Path(args.repo_root).resolve()
    if args.paths:
        result: list[Path] = []
        for raw in args.paths:
            path = Path(raw).resolve()
            if not path.exists():
                continue
            if path.is_file() and is_text_candidate(path):
                result.append(path)
                continue
            if path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file() and is_text_candidate(child):
                        result.append(child)
        return sorted(set(result))
    try:
        return iter_git_files(repo_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return sorted(
            child
            for child in repo_root.rglob("*")
            if child.is_file() and is_text_candidate(child)
        )


def score_text(text: str) -> int:
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    common = sum(1 for ch in text if ch in COMMON_CHINESE)
    punct = sum(1 for ch in text if ch in "，。；：？！【】（）《》、“”‘’—")
    private = sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)
    replacement = text.count("\ufffd")
    suspicious = sum(1 for ch in text if ch in SUSPICIOUS_CHARS)
    return common * 5 + punct * 2 + cjk - private * 6 - replacement * 8 - suspicious * 2


def try_recover(text: str) -> str | None:
    best = text
    best_score = score_text(text)
    current = text
    improved = False
    for _ in range(3):
        try:
            candidate = current.encode("gbk").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        candidate_score = score_text(candidate)
        if candidate_score > best_score + 2:
            best = candidate
            best_score = candidate_score
            current = candidate
            improved = True
        else:
            break
    return best if improved else None


def comment_has_private_use(text: str) -> bool:
    return any(0xE000 <= ord(ch) <= 0xF8FF for ch in text) or "\ufffd" in text


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    content = path.read_text(encoding="utf-8", errors="replace")
    rel = path.as_posix()
    if path.suffix.lower() == ".ps1":
        if UNSAFE_PS_READ.search(content) and UNSAFE_PS_WRITE.search(content):
            problems.append(
                f"{rel}: uses Get-Content -Raw together with Set-Content -Encoding UTF8; switch to UTF-8-safe .NET file I/O."
            )
    for line_no, line in enumerate(content.splitlines(), 1):
        recovered = try_recover(line)
        if recovered:
            problems.append(f"{rel}:{line_no}: recoverable mojibake detected.")
        stripped = line.strip()
        if stripped.startswith("//"):
            comment = stripped[2:].strip()
            if comment_has_private_use(comment):
                problems.append(f"{rel}:{line_no}: suspicious private-use characters in comment.")
            elif any(pattern in comment for pattern in WEIRD_COMMENT_PATTERNS):
                problems.append(f"{rel}:{line_no}: suspicious machine-translated comment detected.")
    return problems


def main() -> int:
    args = parse_args()
    problems: list[str] = []
    for path in iter_paths(args):
        problems.extend(check_file(path))
    if problems:
        print("Text encoding check failed:")
        for item in problems:
            print(f"- {item}")
        return 1
    print("Text encoding check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
