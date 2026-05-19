#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


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
SEPARATOR_RE = re.compile(r"^\s*//\s*[-=]{3,}\s*$")
DECL_RE = re.compile(r"^\s*(service|message|enum)\s+([A-Za-z0-9_]+)\s*\{")
RPC_RE = re.compile(r"^\s*rpc\s+([A-Za-z0-9_]+)\s*\(")
FIELD_RE = re.compile(
    r"^(\s*)(?:repeated\s+|optional\s+)?(?:map<[^>]+>\s+|[.\w<>]+(?:\s+[.\w<>]+)?)\s+([A-Za-z0-9_]+)\s*=\s*[-\d]+"
)
ENUM_VALUE_RE = re.compile(r"^(\s*)([A-Za-z0-9_]+)\s*=\s*[-\d]+")


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


def contains_private_use(text: str) -> bool:
    return any(0xE000 <= ord(ch) <= 0xF8FF for ch in text) or "\ufffd" in text or "\u20ac" in text


def looks_suspicious_comment(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if any(pattern in stripped for pattern in WEIRD_COMMENT_PATTERNS):
        return True
    if contains_private_use(stripped):
        return True
    if try_recover(stripped):
        return True
    suspicious = sum(1 for ch in stripped if ch in SUSPICIOUS_CHARS)
    common = sum(1 for ch in stripped if ch in COMMON_CHINESE)
    non_ascii = any(ord(ch) > 127 for ch in stripped)
    return non_ascii and suspicious >= 2 and common == 0


def split_identifier(name: str) -> list[str]:
    parts: list[str] = []
    for chunk in name.split("_"):
        if not chunk:
            continue
        parts.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+", chunk))
    return parts


def humanize(name: str) -> str:
    words = split_identifier(name)
    if not words:
        return name
    normalized: list[str] = []
    acronyms = {"ID", "URL", "URI", "HTTP", "HTTPS", "MQTT", "ACL", "RPC", "DTO", "JSON", "XML", "API", "IP", "TCP", "UDP"}
    for word in words:
        upper = word.upper()
        if upper in acronyms:
            normalized.append(upper)
        elif word.isupper() and len(word) <= 4:
            normalized.append(word)
        else:
            normalized.append(word.lower())
    phrase = " ".join(normalized)
    return phrase[:1].upper() + phrase[1:]


def declaration_comment(kind: str, name: str) -> str:
    if kind == "service":
        return f"{name} service."
    if kind == "enum":
        return f"{name} enum."
    if name.endswith("Request"):
        return f"{name} request message."
    if name.endswith("Response"):
        return f"{name} response message."
    if name.endswith("DTO"):
        return f"{name} DTO."
    return f"{name} message."


def rpc_comment(name: str) -> str:
    return f"{name} RPC."


def inline_comment(name: str, is_enum_value: bool = False) -> str:
    if is_enum_value and "_" in name:
        _, suffix = name.split("_", 1)
        return f"{humanize(suffix)}."
    return f"{humanize(name)}."


def format_comment(indent: str, text: str) -> str:
    return f"{indent}// {text}"


def replace_declaration_comment_blocks(lines: list[str]) -> list[str]:
    result = lines[:]
    replacements: list[tuple[int, int, list[str]]] = []
    for idx, line in enumerate(lines):
        decl_match = DECL_RE.match(line)
        rpc_match = RPC_RE.match(line)
        if not decl_match and not rpc_match:
            continue
        kind = decl_match.group(1) if decl_match else "rpc"
        name = decl_match.group(2) if decl_match else rpc_match.group(1)
        start = idx - 1
        while start >= 0:
            stripped = lines[start].strip()
            if not stripped.startswith("//") or SEPARATOR_RE.match(lines[start]):
                break
            start -= 1
        block_start = start + 1
        if block_start >= idx:
            continue
        block = lines[block_start:idx]
        if not any(looks_suspicious_comment(item.split("//", 1)[1].strip()) for item in block):
            continue
        indent = re.match(r"^(\s*)", block[0]).group(1)
        comment = rpc_comment(name) if kind == "rpc" else declaration_comment(kind, name)
        replacements.append((block_start, idx, [format_comment(indent, comment)]))
    for start, end, new_lines in reversed(replacements):
        result[start:end] = new_lines
    return result


def repair_inline_and_standalone_comments(lines: list[str]) -> list[str]:
    result: list[str] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if SEPARATOR_RE.match(line):
            result.append(line)
            continue

        if stripped.startswith("//"):
            comment = stripped[2:].strip()
            if looks_suspicious_comment(comment):
                next_line = ""
                for j in range(idx + 1, len(lines)):
                    probe = lines[j].strip()
                    if not probe:
                        continue
                    next_line = lines[j]
                    break
                if next_line:
                    field_match = FIELD_RE.match(next_line)
                    enum_match = ENUM_VALUE_RE.match(next_line)
                    if field_match:
                        continue
                    if enum_match and not next_line.lstrip().startswith(("message ", "enum ", "service ", "rpc ")):
                        continue
                continue
            result.append(line)
            continue

        if "//" in line:
            code, comment = line.split("//", 1)
            comment = comment.strip()
            if looks_suspicious_comment(comment):
                field_match = FIELD_RE.match(code.rstrip())
                enum_match = ENUM_VALUE_RE.match(code.rstrip())
                if field_match:
                    name = field_match.group(2)
                    result.append(f"{code.rstrip()} // {inline_comment(name)}")
                    continue
                if enum_match:
                    name = enum_match.group(2)
                    result.append(f"{code.rstrip()} // {inline_comment(name, is_enum_value=True)}")
                    continue
            recovered = try_recover(line)
            if recovered:
                result.append(recovered)
                continue

        recovered = try_recover(line)
        if recovered:
            result.append(recovered)
            continue
        result.append(line)
    return result


def repair_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    lines = original.splitlines()
    repaired = replace_declaration_comment_blocks(lines)
    repaired = repair_inline_and_standalone_comments(repaired)
    output = "\n".join(repaired) + ("\n" if original.endswith("\n") else "")
    if output == original:
        return False
    path.write_text(output, encoding="utf-8", newline="\n")
    return True


def main(argv: list[str]) -> int:
    paths = [Path(arg).resolve() for arg in argv]
    changed = 0
    for path in paths:
        if repair_file(path):
            changed += 1
            print(f"repaired: {path}")
    print(f"files changed: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
