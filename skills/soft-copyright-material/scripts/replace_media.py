# -*- coding: utf-8 -*-
"""用 md5 精确映射，把 docx 内嵌截图替换为脱敏/标注后的版本。

用法：
  python replace_media.py --doc DOC.docx --orig RAW_DIR --marked MARK_DIR [--apply]

要点：
- 以「替换前备份.docx」（内含原始截图）为映射基准，可重复执行、可回退。
- 只换 ZIP 里 word/media/* 的字节，其余 part 原样保留 → 章节/表格/图注/版式不变。
- 新图尺寸必须与原图一致，否则要同步改 <wp:extent> 与 <a:ext>。
- ⚠️ WPS 占用文档时 os.replace / shutil.move 会 WinError 5；
  直接 open(path, 'wb') 覆写通常仍可行，本脚本已采用该方式。
"""
import argparse
import hashlib
import io
import os
import shutil
import zipfile

from PIL import Image


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description="md5 映射替换 docx 内嵌图片")
    ap.add_argument("--doc", required=True, help="提交版 docx")
    ap.add_argument("--orig", required=True, help="原始截图目录（映射基准来源）")
    ap.add_argument("--marked", required=True, help="脱敏/标注后截图目录")
    ap.add_argument("--baseline", help="替换前备份 docx；不传则用 --doc")
    ap.add_argument("--apply", action="store_true", help="实际写入；默认 dry-run")
    ap.add_argument("--expected", type=int, default=0, help="期望匹配张数，0 不校验")
    a = ap.parse_args()

    origs = {}
    for f in sorted(os.listdir(a.orig)):
        if f.lower().endswith(".png"):
            origs[md5(open(os.path.join(a.orig, f), "rb").read())] = f
    with zipfile.ZipFile(a.doc) as z:
        items = [(i, z.read(i.filename)) for i in z.infolist()]
    media = [(i, d) for i, d in items if i.filename.startswith("word/media/")]
    base = a.baseline if a.baseline and os.path.exists(a.baseline) else a.doc
    with zipfile.ZipFile(base) as z:
        basemedia = [(i.filename, z.read(i.filename)) for i in z.infolist()
                     if i.filename.startswith("word/media/")]

    pairs, used = [], set()
    for mname, data in basemedia:
        h = md5(data)
        if h in origs and origs[h] not in used:
            name = origs[h]
            used.add(name)
            pairs.append((mname, name, os.path.join(a.marked, name), data))
    print("原始 PNG:", len(origs), " media:", len(media), " 精确匹配:", len(pairs))
    if a.expected and len(pairs) != a.expected:
        raise SystemExit("匹配数 %d != 期望 %d，停止（防止误改）" % (len(pairs), a.expected))
    miss = set(origs.values()) - used
    if miss:
        print("未匹配:", sorted(miss))

    cur = {i.filename: d for i, d in media}
    bad = []
    for mname, name, marked, old in pairs:
        if not os.path.exists(marked):
            bad.append((name, "文件缺失"))
            continue
        a_size = Image.open(io.BytesIO(cur.get(mname, old))).size
        b_size = Image.open(marked).size
        if a_size != b_size:
            bad.append((name, a_size, b_size))
    if bad:
        raise SystemExit("尺寸/文件校验失败: " + str(bad))
    print("尺寸校验通过（原图与新图一致，无需改 extent）")

    if not a.apply:
        print("[dry-run] 未写入；确认后加 --apply")
        return

    bak = a.baseline or os.path.join(a.orig, "设计原理_替换前备份.docx")
    if not os.path.exists(bak):
        shutil.copyfile(a.doc, bak)
        print("备份 ->", bak)
    lookup = {m: p for m, _, p, _ in pairs}
    out = []
    for i, data in items:
        if i.filename in lookup:
            data = open(lookup[i.filename], "rb").read()
        out.append((i, data))
    tmp = a.doc + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for i, data in out:
            zi = zipfile.ZipInfo(i.filename, date_time=i.date_time)
            zi.compress_type = i.compress_type
            zi.external_attr = i.external_attr
            zi.internal_attr = i.internal_attr
            zi.create_system = i.create_system
            zo.writestr(zi, data)
    blob = open(tmp, "rb").read()
    with open(a.doc, "wb") as f:          # WPS 占用时用覆写代替 os.replace
        f.write(blob)
    os.remove(tmp)
    print("已替换 %d 张 -> %s (%d B)" % (len(pairs), a.doc, len(blob)))
    with zipfile.ZipFile(a.doc) as z:
        print("zip CRC:", z.testzip())


if __name__ == "__main__":
    main()
