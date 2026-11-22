# -*- coding: utf-8 -*-
"""对系统界面截图批量打像素化马赛克（必须在叠加手写标注之前执行）。

用法：
  python desensitize.py --src RAW_DIR --dst DES_DIR
  python desensitize.py --src RAW_DIR --dst DES_DIR \
      --extra extra_boxes.json --boost 2.2 --block 10

extra_boxes.json 格式（坐标 0~1 为相对值，>1 视为绝对像素）：
  {"10_transcoding.png": [[632,186,806,212]],
   "09_config.png": [[0.43,0.19,0.58,0.22]]}

默认内置 CMS 项目的四类敏感信息规则（顶栏账号、用户列表账号/姓名、
日志页账号/IP、登录页验证码）。新项目可用 --no-defaults 只用 --extra。

经验要点：
- 顺序必须是「原图 → 马赛克 → 手写标注」，否则批注会被盖住。
- 弹窗遮罩使整片背景变暗，深色像素行扫描会失效，这类页必须用固定框。
- 框元组顺序恒为 (x0, y0, x1, y1)。
- URL / IP 这类细笔画文字像素化后对比很淡（像涂抹不像马赛克），
  用 --boost 2.2 放大灰度差异，才会呈现与头像打码一致的灰白方格。
"""
import argparse
import json
import os

from PIL import Image

TOP_USER_X = 0.905
TOP_USER_H = 48
FIXED = {"00_login.png": [(0.678, 0.445, 0.792, 0.530)]}
FIXED_ROWS = {
    "21_user_add.png": [
        (0.205, 0.204 + i * 0.051 - 0.017, 0.295, 0.204 + i * 0.051 + 0.017)
        for i in range(6)
    ],
}
SCAN_COLS = {
    "13_user.png": [(0.170, 0.320, 0.185, 0.480), (0.330, 0.470, 0.185, 0.480)],
    "14_log.png": [(0.150, 0.300, 0.215, 0.930), (0.575, 0.710, 0.215, 0.930)],
}
NO_TOP_USER = {"00_login.png"}


def find_text_boxes(im, xr, yr, threshold=150):
    """在指定列内扫描深色文字行，返回每个文字块的像素矩形。"""
    W, H = im.size
    px = im.convert("L").load()
    x0, x1 = int(xr[0] * W), int(xr[1] * W)
    y0, y1 = int(yr[0] * H), int(yr[1] * H)
    flags = []
    for y in range(y0, y1):
        dark = sum(1 for x in range(x0, x1, 2) if px[x, y] < threshold)
        flags.append(dark >= 2)
    segs, start = [], None
    for i, v in enumerate(flags):
        if v and start is None:
            start = i
        elif not v and start is not None:
            segs.append([start, i])
            start = None
    if start is not None:
        segs.append([start, len(flags)])
    merged = []
    for a, b in segs:
        if merged and a - merged[-1][1] <= 3:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    boxes = []
    for a, b in merged:
        if b - a < 5 or b - a > 46:      # 过滤表格线与大段正文
            continue
        ya, yb = y0 + a, y0 + b
        xs = [x for y in range(ya, yb, 2) for x in range(x0, x1) if px[x, y] < threshold]
        if not xs:
            continue
        xa, xb = min(xs), max(xs)
        if xb - xa < 7:
            continue
        boxes.append((max(0, xa - 6), max(0, ya - 3),
                      min(W, xb + 7), min(H, yb + 3)))
    return boxes


def apply_mosaic(im, box, block=9, boost=1.0):
    """缩小再最近邻放大生成像素化方块；boost 用于低对比文字（URL/IP）。"""
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.width, x1), min(im.height, y1)
    if x1 <= x0 or y1 <= y0:
        return
    crop = im.crop((x0, y0, x1, y1)).convert("RGB")
    w, h = crop.size
    small = crop.resize((max(1, w // block), max(1, h // block)), Image.BILINEAR)
    pix = small.resize((w, h), Image.NEAREST)
    if boost != 1.0:
        px = pix.load()
        for yy in range(h):
            for xx in range(w):
                r, g, b = px[xx, yy]
                px[xx, yy] = tuple(max(0, min(255, int(255 - (255 - v) * boost)))
                                   for v in (r, g, b))
    im.paste(pix, (x0, y0))


def desensitize(src, fname, extra=None, use_defaults=True,
                block=9, boost=1.0, top_user=True):
    """src 可为路径或 PIL Image；返回 (RGB Image, 打码处数)。"""
    im = Image.open(src).convert("RGB") if isinstance(src, str) else src.convert("RGB")
    W, H = im.size
    boxes = []
    if use_defaults:
        if top_user and fname not in NO_TOP_USER:
            boxes.append((int(TOP_USER_X * W), 0, W, min(H, TOP_USER_H)))
        for b in FIXED.get(fname, []) + FIXED_ROWS.get(fname, []):
            boxes.append(tuple((b[i] * W if i % 2 == 0 else b[i] * H) for i in range(4)))
        for col in SCAN_COLS.get(fname, []):
            boxes.extend(find_text_boxes(im, (col[0], col[1]), (col[2], col[3])))
    if extra:
        for b in extra.get(fname, []):
            boxes.append(tuple(v if v > 1 else (v * W if i % 2 == 0 else v * H)
                               for i, v in enumerate(b)))
    uniq = []
    for b in boxes:
        if not any(abs(b[0] - u[0]) < 8 and abs(b[1] - u[1]) < 8 for u in uniq):
            uniq.append(b)
    for b in uniq:
        apply_mosaic(im, b, block=block, boost=boost)
    return im, len(uniq)


def main():
    ap = argparse.ArgumentParser(description="截图敏感信息批量打马赛克")
    ap.add_argument("--src", required=True, help="原始截图目录")
    ap.add_argument("--dst", required=True, help="脱敏结果目录")
    ap.add_argument("--extra", help="附加固定框 JSON 文件")
    ap.add_argument("--no-defaults", action="store_true", help="不使用内置 CMS 规则")
    ap.add_argument("--no-top-user", default="", help="不打顶栏账号的文件名，逗号分隔")
    ap.add_argument("--block", type=int, default=9)
    ap.add_argument("--boost", type=float, default=1.0)
    a = ap.parse_args()
    extra = json.load(open(a.extra, encoding="utf-8")) if a.extra else None
    no_top = set(a.no_top_user.split(",")) if a.no_top_user else set()
    os.makedirs(a.dst, exist_ok=True)
    for f in sorted(os.listdir(a.src)):
        if not f.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        im, n = desensitize(os.path.join(a.src, f), f, extra=extra,
                            use_defaults=not a.no_defaults, block=a.block,
                            boost=a.boost, top_user=f not in no_top)
        im.save(os.path.join(a.dst, f))
        print("%-28s 打码 %2d 处" % (f, n))
    print("脱敏原图 ->", a.dst)


if __name__ == "__main__":
    main()
