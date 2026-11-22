# -*- coding: utf-8 -*-
"""交付前校验 docx 完整性、图片映射与文档属性。

用法：
  python verify_delivery.py --docx DOC.docx --shots MARK_DIR [--baseline OLD.docx]

检查项：zip CRC / media 数量 / 内嵌图与截图目录 md5 对应 / 
docProps/core.xml 敏感字段 / 段落与表格数（与基线对比）/ 图注数量。
"""
import argparse
import hashlib
import os
import re
import zipfile


def md5(b):
    return hashlib.md5(b).hexdigest()


def count(xml):
    return (xml.count("<w:p "), xml.count("<w:tbl>"),
            len(re.findall(r"图\s*\d+[-－]\d+", xml)))


def main():
    ap = argparse.ArgumentParser(description="软著 docx 交付校验")
    ap.add_argument("--docx", required=True)
    ap.add_argument("--shots", required=True)
    ap.add_argument("--baseline", help="改稿前备份 docx，用于对比段落/表格数")
    a = ap.parse_args()

    shots = {}
    for f in sorted(os.listdir(a.shots)):
        if f.lower().endswith(".png"):
            shots[md5(open(os.path.join(a.shots, f), "rb").read())] = f

    forbidden = ["dc:creator", "dc:description", "cp:lastModifiedBy",
                 "dc:title", "dc:subject", "cp:keywords", "cp:category", "cp:contentStatus"]
    with zipfile.ZipFile(a.docx) as z:
        print("zip CRC:", z.testzip())
        media = [(n, z.read(n)) for n in z.namelist()
                 if n.startswith("word/media/") and not n.endswith("/")]
        hit = {}
        for n, data in media:
            h = md5(data)
            if h in shots:
                hit[n] = shots[h]
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
        core = z.read("docProps/core.xml").decode("utf-8", "ignore")
        print("media:", len(media), " 匹配截图:", len(hit))
        print("未匹配截图:", sorted(set(shots.values()) - set(hit.values())))
        print("段落/表格/图注:", count(xml))
        print("属性残留字段:", [k for k in forbidden if k in core])

    if a.baseline:
        with zipfile.ZipFile(a.baseline) as z:
            bxml = z.read("word/document.xml").decode("utf-8", "ignore")
        print("基线段落/表格/图注:", count(bxml))
        print("结构一致:", count(xml) == count(bxml))


if __name__ == "__main__":
    main()
