# -*- coding: utf-8 -*-
"""Generalised page-count simulator.

Reads real layout parameters from each docx (page size, margins, run fonts,
sizes, spacing, image heights, table geometry) and simulates Word's page
filling.  Calibrated on two anchors whose page counts are known:
  - StreamEdge/设计原理.docx      -> 9 pages  (WPS-measured)
  - CMS-全量版/源代码.docx        -> 60 pages (Word-measured)
"""
import os, zipfile, re
from xml.etree import ElementTree as ET
from PIL import ImageFont

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
EMS_PER_CM = 360000.0
PT_PER_CM = 28.3465

FONT_FILES = {
    'consolas': r'C:\Windows\Fonts\consola.ttf',
    'times new roman': r'C:\Windows\Fonts\times.ttf',
    'calibri': r'C:\Windows\Fonts\calibri.ttf',
    'arial': r'C:\Windows\Fonts\arial.ttf',
    '宋体': r'C:\Windows\Fonts\simsun.ttc',
    'simsun': r'C:\Windows\Fonts\simsun.ttc',
    '黑体': r'C:\Windows\Fonts\simhei.ttf',
    'simhei': r'C:\Windows\Fonts\simhei.ttf',
    '微软雅黑': r'C:\Windows\Fonts\msyh.ttc',
}

_fc = {}
def _f(path, pt):
    k = (path, round(pt, 2))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, max(1, int(round(pt * 8))))
    return _fc[k]

def _resolve(name, default):
    if not name:
        return default
    return FONT_FILES.get(name.strip().lower(), default)

def width_pt(s, latin_path, cjk_path, pt):
    fl, fc_ = _f(latin_path, pt), _f(cjk_path, pt)
    tot = 0.0
    for ch in s:
        f = fc_ if ord(ch) > 0x2E80 else fl
        tot += f.getlength(ch) / 8.0
    return tot

def wrap_count(s, avail_pt, latin_path, cjk_path, pt):
    if not s:
        return 1
    fl, fc_ = _f(latin_path, pt), _f(cjk_path, pt)
    lines, cur = 1, 0.0
    for ch in s:
        f = fc_ if ord(ch) > 0x2E80 else fl
        a = f.getlength(ch) / 8.0
        if cur + a > avail_pt + 0.01:
            lines += 1
            cur = a
        else:
            cur += a
    return lines


def simulate(path, label, verbose=True):
    z = zipfile.ZipFile(path)
    xml = z.read('word/document.xml')
    doc = ET.fromstring(xml)

    # --- page geometry ---
    sect = doc.find('.//' + W + 'sectPr')
    pgsz = sect.find(W + 'pgSz') if sect is not None else None
    pgmar = sect.find(W + 'pgMar') if sect is not None else None
    PW = float(pgsz.get(W + 'w')) / 20.0
    PH = float(pgsz.get(W + 'h')) / 20.0
    mt = float(pgmar.get(W + 'top')) / 20.0
    mb = float(pgmar.get(W + 'bottom')) / 20.0
    ml = float(pgmar.get(W + 'left')) / 20.0
    mr = float(pgmar.get(W + 'right')) / 20.0
    COL = PW - ml - mr
    PGH = PH - mt - mb

    # --- Normal style defaults ---
    styles = z.read('word/styles.xml').decode('utf-8')
    m = re.search(r'<w:style [^>]*w:default="1"[^>]*>(.*?)</w:style>', styles, re.S)
    base = m.group(1) if m else ''
    ms = re.search(r'<w:sz w:val="(\d+)"', base)
    BASE_SZ = float(ms.group(1)) / 2.0 if ms else 10.5
    mf = re.search(r'w:ascii="([^"]+)"', base)
    BASE_LATIN = _resolve(mf.group(1) if mf else None, FONT_FILES['times new roman'])
    mf2 = re.search(r'w:eastAsia="([^"]+)"', base)
    BASE_CJK = _resolve(mf2.group(1) if mf2 else None, FONT_FILES['宋体'])

    body = doc.find(W + 'body')
    tw = lambda v: float(v) / 20.0

    y, page = 0.0, 1
    def newpage():
        nonlocal y, page
        page += 1
        y = 0.0

    for el in body:
        if el.tag == W + 'p':
            pPr = el.find(W + 'pPr')
            before = after = None
            line = None
            ind_f = ind_l = ind_h = None
            if pPr is not None:
                sp = pPr.find(W + 'spacing')
                if sp is not None:
                    if sp.get(W + 'before'): before = tw(sp.get(W + 'before'))
                    if sp.get(W + 'after'):  after = tw(sp.get(W + 'after'))
                    if sp.get(W + 'line'):   line = float(sp.get(W + 'line')) / 240.0
                ind = pPr.find(W + 'ind')
                if ind is not None:
                    if ind.get(W + 'firstLine'): ind_f = tw(ind.get(W + 'firstLine'))
                    if ind.get(W + 'left'):      ind_l = tw(ind.get(W + 'left'))
                    if ind.get(W + 'hanging'):   ind_h = tw(ind.get(W + 'hanging'))
            # run properties: size + fonts
            size, latin, cjk = None, None, None
            rpr = el.find('.//' + W + 'rPr')
            if rpr is not None:
                sz = rpr.find(W + 'sz')
                if sz is not None:
                    size = float(sz.get(W + 'val')) / 2.0
                rf = rpr.find(W + 'rFonts')
                if rf is not None:
                    latin = _resolve(rf.get(W + 'ascii'), BASE_LATIN)
                    cjk = _resolve(rf.get(W + 'eastAsia'), BASE_CJK)
            size = size or BASE_SZ
            latin = latin or BASE_LATIN
            cjk = cjk or BASE_CJK
            txt = ''.join(t.text or '' for t in el.iter(W + 't'))
            imgs = [int(e.get('cy')) / EMS_PER_CM * PT_PER_CM
                    for e in el.iter(WP + 'extent')]

            lh = size * 1.28 * (line if line else 1.0)
            if before:
                if y + before > PGH:
                    newpage()
                y += before
            if txt:
                lstart = ind_l or 0.0
                if ind_h:
                    first_avail = COL - lstart + ind_h
                    rest_avail = COL - lstart
                else:
                    first_avail = COL - lstart - (ind_f or 0.0)
                    rest_avail = COL - lstart
                n_first = wrap_count(txt, max(20.0, first_avail), latin, cjk, size)
                if n_first == 1:
                    n = 1
                else:
                    # re-wrap accounting for the shorter first line
                    n = 1 + wrap_count(txt, max(20.0, rest_avail), latin, cjk, size)
                    n = min(n, max(1, int(width_pt(txt, latin, cjk, size) /
                                          max(20.0, rest_avail)) + 1))
                    # safer: explicit greedy with two widths
                    def greedy(s, wa, wb):
                        fl, fc_ = _f(latin, size), _f(cjk, size)
                        lines, cur, w = 1, 0.0, wa
                        for ch in s:
                            f = fc_ if ord(ch) > 0x2E80 else fl
                            a = f.getlength(ch) / 8.0
                            if cur + a > w + 0.01:
                                lines += 1
                                cur = a
                                w = wb
                            else:
                                cur += a
                        return lines
                    n = greedy(txt, max(20.0, first_avail), max(20.0, rest_avail))
                for _ in range(n):
                    if y + lh > PGH:
                        newpage()
                    y += lh
            else:
                if y + lh > PGH:
                    newpage()
                y += lh
            y += (after if after is not None else 0.0)
            for ih in imgs:
                if y + ih > PGH:
                    newpage()
                y += ih
        elif el.tag == W + 'tbl':
            for tr in el.findall(W + 'tr'):
                rh = 0.0
                cells = tr.findall(W + 'tc')
                for tc in cells:
                    t = ''.join(x.text or '' for x in tc.iter(W + 't'))
                    tcw = tc.find(W + 'tcPr/' + W + 'tcW')
                    wpt = tw(tcw.get(W + 'w')) if (tcw is not None and tcw.get(W + 'w')) else COL / max(1, len(cells))
                    n = wrap_count(t, max(20.0, wpt - 11.0), BASE_LATIN, BASE_CJK, BASE_SZ)
                    rh = max(rh, n * BASE_SZ * 1.28)
                rh += 2.0
                if y + rh > PGH:
                    newpage()
                y += rh
            y += 4.0

    if verbose:
        print(f'   {label:38s} pages≈{page:3d}')
    return page


A = os.environ.get('SC_ROOT', r'C:\Users\admin\Documents\src\copyright')  # 新项目改：三件套所在根目录
print('--- anchors (known true values) ---')
a1 = simulate(A + r'\StreamEdge\设计原理.docx', 'StreamEdge 设计原理  (true 9)')
a2 = simulate(A + r'\CMS-全量版\源代码.docx', 'CMS-全量版 源代码  (true 60)')
print()
print('--- new documents ---')
n1 = simulate(A + r'\CMS\设计原理(V1).docx', 'CMS 设计原理(V1)')
n2 = simulate(A + r'\CMS\源代码.docx', 'CMS 源代码 (V1)')
n3 = simulate(A + r'\CMS\软著信息表.docx', 'CMS 软著信息表')
print()
print(f'anchor error: 设计原理 {a1} vs 9 ; 源代码 {a2} vs 60')
