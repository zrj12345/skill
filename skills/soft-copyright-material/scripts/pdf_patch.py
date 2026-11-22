# -*- coding: utf-8 -*-
"""替换 PDF 内嵌的某张截图，避免为了改一张图而重转整份 PDF。

用法：
  python pdf_patch.py --pdf PREVIEW.pdf --old OLD.png --new NEW.png

使用场景：WPS 重新导出 PDF 不可用时（PowerShell COM 被安全策略拦截、
pywin32/comtypes 未安装），直接用 PyMuPDF 替换 PDF 内嵌图像对象。
定位方式：遍历全部内嵌图，按尺寸 + 缩略图 MAE 找到与 --old 最相似的 xref。
替换后可用 page.get_image_info(xrefs=True) 确认页面实际引用的是新对象。
"""
import argparse
import io
import os
import shutil

import pymupdf
from PIL import Image, ImageChops, ImageStat


def thumb(im):
    return im.convert("RGB").resize((80, 50))


def mae(a, b):
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3


def main():
    ap = argparse.ArgumentParser(description="替换 PDF 内嵌截图")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--old", required=True, help="替换前的截图文件")
    ap.add_argument("--new", required=True, help="替换后的截图文件")
    ap.add_argument("--no-backup", action="store_true")
    a = ap.parse_args()

    old_im = Image.open(a.old)
    new_im = Image.open(a.new)
    if old_im.size != new_im.size:
        raise SystemExit("新旧图尺寸不一致，PDF 中的显示框可能错位")
    W, H = old_im.size
    r_old, r_new = thumb(old_im), thumb(new_im)
    doc = pymupdf.open(a.pdf)
    cands = []
    for xref in range(1, doc.xref_length()):
        try:
            info = doc.extract_image(xref)
        except Exception:
            continue
        if info.get("width") != W or info.get("height") != H:
            continue
        im = thumb(Image.open(io.BytesIO(info["image"])))
        cands.append((mae(im, r_old), mae(im, r_new), xref))
    cands.sort()
    if not cands or cands[0][0] > 12:
        raise SystemExit("未找到匹配图像对象，停止")
    xref = cands[0][2]
    print("target xref", xref, "diff_old", round(cands[0][0], 2),
          "diff_new", round(cands[0][1], 2))

    done = False
    new_xref = xref
    for page in doc:
        for img in page.get_images(full=True):
            if img[0] == xref:
                ret = page.replace_image(xref, filename=a.new)
                if ret:
                    new_xref = ret
                done = True
                break
        if done:
            break
    if not done:
        raise SystemExit("图像对象未被任何页面引用")
    tmp = a.pdf + ".new"
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    if not a.no_backup:
        shutil.copyfile(a.pdf, a.pdf + ".bak")
    os.replace(tmp, a.pdf)

    chk = pymupdf.open(a.pdf)
    print("PDF pages:", chk.page_count)
    for page in chk:
        for it in page.get_image_info(xrefs=True):
            if it.get("xref") in (xref, new_xref):
                print("page", page.number + 1, "displays xref", it.get("xref"))
                break
    chk.close()
    print("PDF size:", os.path.getsize(a.pdf))


if __name__ == "__main__":
    main()
