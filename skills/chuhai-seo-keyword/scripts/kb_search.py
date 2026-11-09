# -*- coding: utf-8 -*-
"""Search the local Web.Cafe / 哥飞 SEO knowledge base (1104 docs).

Usage:
  python kb_search.py --query "KD 判断 搜索量" --limit 8
  python kb_search.py --title "找词" --cat 哥飞小课堂
  python kb_search.py --id 1037
  python kb_search.py --list-cats
  python kb_search.py --query "SERP 内页" --json

The knowledge base is addressed by its folder name only: 出海seo资源分享V1.0
(no absolute paths). The script searches the current directory and its parents,
plus the script's own parent directories. Override with --kb <dir> or the
SEO_KB_ROOT environment variable. The folder must contain search-index.json.
"""
import argparse, json, os, re, sys

KB_DIRNAME = "出海seo资源分享V1.0"
DEFAULT_KB = os.environ.get("SEO_KB_ROOT") or KB_DIRNAME
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def resolve_kb(kb):
    """Locate the knowledge-base folder by name, without hardcoded paths."""
    def has_index(p):
        return os.path.isfile(os.path.join(p, "search-index.json"))

    if has_index(kb):
        return kb
    if kb != KB_DIRNAME:
        candidate = os.path.join(os.getcwd(), kb)
        return candidate if has_index(candidate) else kb

    seen = set()
    for base in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        cur = os.path.abspath(base)
        for _ in range(7):
            if cur in seen:
                break
            seen.add(cur)
            candidate = os.path.join(cur, KB_DIRNAME)
            if has_index(candidate):
                return candidate
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    return kb


def load(kb):
    kb = resolve_kb(kb)
    path = os.path.join(kb, "search-index.json")
    if not os.path.exists(path):
        sys.exit("Knowledge base not found. Place the folder 出海seo资源分享V1.0 in the "
                 "workspace (or any parent), or pass --kb <dir> / set SEO_KB_ROOT.")
    with open(path, encoding="utf-8") as f:
        docs = json.load(f)
    for i, d in enumerate(docs):
        d["id"] = i
        d["text"] = d.get("t", "") or ""
    return docs


def doc_paths(d):
    """Return (md, html) paths relative to the workspace root."""
    name = os.path.splitext(d.get("h", ""))[0]
    folder = d.get("f", "")
    cat = d.get("d", "")
    parts = [KB_DIRNAME] + ([cat] if cat else []) + [folder]
    return (os.path.join(*parts, name + ".md"),
            os.path.join(*parts, name + ".html"))


def snippets(text, terms, width=150, maxn=3):
    low = text.lower()
    out, seen = [], []
    for t in terms:
        start = 0
        while len(out) < maxn:
            i = low.find(t.lower(), start)
            if i < 0:
                break
            if any(abs(i - p) < width for p in seen):
                start = i + len(t)
                continue
            seen.append(i)
            a, b = max(0, i - width), min(len(text), i + width + len(t))
            out.append(text[a:b].replace("\n", " ").strip())
            start = i + len(t)
        if len(out) >= maxn:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default=DEFAULT_KB, help="folder containing search-index.json")
    ap.add_argument("--query", help="full-text query; space separated terms")
    ap.add_argument("--title", help="title-only query")
    ap.add_argument("--cat", help="filter by category")
    ap.add_argument("--id", type=int, help="print full text of one document id")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--list-cats", action="store_true")
    ap.add_argument("--all", action="store_true", help="with --id, do not truncate")
    ap.add_argument("--path", action="store_true", help="with --id, print local md/html paths and the original URL instead of the full text")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    docs = load(a.kb)

    if a.list_cats:
        from collections import Counter
        for c, n in Counter(d.get("d", "") for d in docs).most_common():
            print("%5d  %s" % (n, c or "(根目录)"))
        return

    if a.id is not None:
        if not (0 <= a.id < len(docs)):
            sys.exit("id out of range 0..%d" % (len(docs) - 1))
        d = docs[a.id]
        if a.path:
            md, html = doc_paths(d)
            print("id=%d | %s | %s" % (d["id"], d.get("d", ""), d["n"]))
            print("md   : %s" % md)
            print("html : %s" % html)
            print("paths are relative to the workspace root; open them directly, or run:")
            print("  python kb_search.py --id %d --all   (read full text)" % d["id"])
            m = re.search(r"原文链接[：:]\s*(\S+)", d["text"])
            if m:
                print("原文 : %s" % m.group(1))
            return
        print("id=%d | %s | %s\n%s\n" % (d["id"], d.get("d", ""), d["n"], "-" * 60))
        print(d["text"] if a.all else d["text"][:30000])
        return

    terms = [t for t in re.split(r"\s+", (a.query or a.title or "").strip()) if t]
    if not terms:
        ap.error("provide --query, --title, --id or --list-cats")

    rows = []
    for d in docs:
        if a.cat and a.cat not in (d.get("d") or ""):
            continue
        title, body = d["n"].lower(), d["text"].lower()
        hits = [t for t in terms if t.lower() in title or t.lower() in body]
        if not hits:
            continue
        if a.title and not any(t.lower() in title for t in terms):
            continue
        s = 0.0
        for t in terms:
            s += 8 * title.count(t.lower())
            s += min(body.count(t.lower()), 20) * 0.5
        s += 2 * len(hits)
        s += min(len(d["text"]), 9000) / 5000.0
        if len(d["text"]) > 40000:
            s *= 0.5
        rows.append((s, d, hits))
    rows.sort(key=lambda x: -x[0])

    if a.json:
        print(json.dumps([{"id": d["id"], "category": d.get("d"), "title": d["n"],
                           "score": round(s, 1), "snippets": snippets(d["text"], terms)}
                          for s, d, h in rows[:a.limit]], ensure_ascii=False, indent=2))
        return
    print("Found %d docs, showing top %d for: %s\n" % (len(rows), min(a.limit, len(rows)), " ".join(terms)))
    for s, d, h in rows[:a.limit]:
        print("=" * 78)
        print("[id=%d] %s | %s | score=%.1f | %d chars" % (d["id"], d.get("d", ""), d["n"], s, len(d["text"])))
        for sn in snippets(d["text"], terms):
            print("   ... %s ..." % sn)
        print("   read full: python kb_search.py --id %d --all" % d["id"])
    print()


if __name__ == "__main__":
    main()
