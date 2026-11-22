# -*- coding: utf-8 -*-
"""Regenerate V1 源代码.docx — 前 30 页 + 后 30 页 of the V1-scope source.

Calibration: the anchor document (identical layout profile) measured
55.2 rendered lines per page in Word (3312 lines -> exactly 60 pages).
The coarse line model reproduces that within 0.3%, so we target the same
rendered-line budget here, plus a small buffer, and place an elision
marker between the two chunks.
"""
import os, math
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn

SRC = os.environ.get('SC_CODE_DIR', r'C:\Users\admin\Documents\src\shortcms-freshflick')  # 新项目改：源码根目录
BASE = os.environ.get('SC_BASE', r'C:\Users\admin\Documents\src\copyright\CMS')  # 新项目改：输出目录

V1_FILES = [
    'main.go',
    'cmd/cobra.go',
    'api/router.go',
    'internal/middleware/jwt.go',
    'internal/middleware/signature.go',
    'api/v1/user.go',
    'api/v1/episode.go',
    'api/v1/video.go',
    'api/v1/upload.go',
    'internal/models/init.go',
    'internal/models/migration.go',
    'internal/models/program.go',
    'internal/models/streaming.go',
    'internal/models/user.go',
    'internal/models/menu.go',
    'internal/models/dict.go',
    'internal/models/genre.go',
    'internal/models/country.go',
    'pkg/utils/captcha.go',
    'pkg/utils/net.go',
]

lines = []
for rel in V1_FILES:
    with open(os.path.join(SRC, rel), 'r', encoding='utf-8', errors='replace') as f:
        for ln in f:
            lines.append(ln.rstrip())
print('total V1 source lines available:', len(lines))


def units(s):
    return sum(1.819 if ord(ch) > 0x2E80 else 1.0 for ch in s)


def dlines(s):
    return max(1, math.ceil(units(s) / 79))


PAGE_LINES = 55.2
TARGET_PER_SIDE = 1674          # rendered lines per side (~30.3 pages)

acc, hi = 0, 0
while hi < len(lines) and acc < TARGET_PER_SIDE:
    acc += dlines(lines[hi])
    hi += 1
head = lines[:hi]

acc, ti = 0, len(lines)
while ti > hi and acc < TARGET_PER_SIDE:
    ti -= 1
    acc += dlines(lines[ti])
tail = lines[ti:]

MARKER = '// ……（中间部分源代码省略）……'
body = head + [MARKER] + tail
total = sum(dlines(x) for x in body)
print(f'head={len(head)} tail={len(tail)} paras={len(body)}')
print(f'rendered lines≈{total} -> est pages {total / PAGE_LINES:.2f}')

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(1.5)
sec.left_margin = sec.right_margin = Cm(1.6)

st = doc.styles['Normal']
st.font.name = 'Consolas'
st.font.size = Pt(11.5)
st.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
st.paragraph_format.space_after = Pt(0)
st.paragraph_format.space_before = Pt(0)
st.paragraph_format.line_spacing = 1.0

for ln in body:
    p = doc.add_paragraph()
    r = p.add_run(ln)
    r.font.name = 'Consolas'
    r.font.size = Pt(11.5)
    rPr = r._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = rPr.makeelement(qn('w:rFonts'), {})
        rPr.append(rf)
    rf.set(qn('w:eastAsia'), '宋体')
    rf.set(qn('w:ascii'), 'Consolas')
    rf.set(qn('w:hAnsi'), 'Consolas')

OUT = os.path.join(BASE, '源代码.docx')
doc.save(OUT)
print('saved', OUT)
