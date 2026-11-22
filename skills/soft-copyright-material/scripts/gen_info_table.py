# -*- coding: utf-8 -*-
"""V1 软著信息表 — rebuilt to match the StreamEdge template layout:
2-column bordered table (6.44cm / 11.0cm), 10.5pt, same field labels,
followed by the 鉴别材料要求 notes.
"""
import os
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = os.environ.get('SC_BASE', r'C:\Users\admin\Documents\src\copyright\CMS')  # 新项目改此环境变量，并按新项目改 T1/T2/NOTES 文案
W1, W2 = 6.44, 11.0            # 3652 / 6237 twips

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(1.27)
sec.left_margin = sec.right_margin = Cm(1.27)

st = doc.styles['Normal']
st.font.name = 'Calibri'
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
st.paragraph_format.space_after = Pt(0)


def _ea(run, cjk='宋体', latin='Calibri'):
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = rPr.makeelement(qn('w:rFonts'), {})
        rPr.append(rf)
    rf.set(qn('w:eastAsia'), cjk)
    rf.set(qn('w:ascii'), latin)
    rf.set(qn('w:hAnsi'), latin)


def cell_text(cell, s, bold=False):
    cell.text = ''
    p = cell.paragraphs[0]
    r = p.add_run(s)
    r.font.size = Pt(10.5)
    r.font.bold = bold
    r.font.name = 'Calibri'
    _ea(r)


def build_table(pairs):
    t = doc.add_table(rows=len(pairs), cols=2)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, (k, v) in enumerate(pairs):
        cell_text(t.rows[i].cells[0], k)
        cell_text(t.rows[i].cells[1], v)
        for j, w in enumerate((W1, W2)):
            t.rows[i].cells[j].width = Cm(w)
    return t


# ---------------------------------------------------------- 表一（17 行）
T1 = [
    ('软件全称', '信息服务技术跨媒体数字内容智能生产与管理系统研发'),
    ('软件简称', 'FreshFlick CMS'),
    ('版本号', 'V1.0.0'),
    ('软件分类（4选1）', '应用软件'),
    ('开发完成日期', '2026年03月31日'),
    ('发表状态（2选1）', '【已发表】2026年04月15日发表于：广东省深圳市'),
    ('权利人名称（与“实名认证”时信息一致）', '深圳卓然软件有限公司'),
    ('证件号码（与“实名认证”时信息一致）', '91440300MA5HDP1N53'),
    ('开发的硬件环境（一般写研发软件的硬件配置）',
     'i7-12700H处理器，32GB内存，1024GB硬盘'),
    ('运行的硬件环境', '8核，16GB内存，100GB硬盘'),
    ('开发该软件的操作系统', 'Windows 11、Docker容器环境'),
    ('软件开发环境或开发工具', 'Vscode、GoLand、Git、Docker、Make等'),
    ('该软件的运行平台/操作系统', 'Linux系统（CentOS 7 / Ubuntu 20.04及以上）'),
    ('软件运行支撑环境或支持软件（一般写数据库、环境插件等）',
     'MySQL 8.0、Redis 6.0、Nginx 1.24等'),
    ('编程语言', 'Go、SQL'),
    ('源程序量', '5500行'),
    ('开发目的（包含不限于参考示例）',
     '①提供统一的内容录入与维护入口；②实现剧集、视频、字幕与图片的一体化管理；'
     '③实现内容与基础数据的关联引用；④提供基于角色的菜单与接口权限控制；'
     '⑤降低内容管理成本，提升内容发布效率'),
]
build_table(T1)

doc.add_paragraph()

# ------------------------------------------------------------ 表二（5 行）
T2 = [
    ('面向领域/行业（包含不限于参考示例）', '数字内容管理、媒体资讯运营等。'),
    ('软件的主要功能（概述软件实现的功能，200字以内）',
     '系统提供剧集内容管理、视频与字幕资料管理、类型与国家地区等基础数据维护，'
     '以及用户、角色、菜单权限等系统管理功能；支持内容分页检索、批量维护与操作日志记录。'),
    ('软件特点标签（可多选）', '【内容管理软件】【媒体行业软件】【信息安全软件】'),
    ('软件的技术特点（概述软件采用的技术，100字以内）',
     '采用分层架构与模块化设计；接口统一鉴权与令牌校验；基于角色的菜单与接口权限控制；'
     '数据模型规范化，支持内容与资料的关联引用。'),
    ('※注意事项※①除“软件简称”外，其他均为必填项；②带选项内容，请用其他颜色标注或进行删减保留；'
     '③认真核实填写内容，一经录入系统，无法修改。', ''),
]
t2 = build_table(T2)
# 末行合并
t2.rows[-1].cells[0].merge(t2.rows[-1].cells[1])

doc.add_paragraph()

# ---------------------------------------------------- 鉴别材料要求（同模板）
NOTES = [
    '提供鉴别材料要求：',
    '软件说明文档：提供Word格式文档(可以是用户手册、设计说明书、使用说明书等中的任意一种)。'
    '文档要针对软件展开说明,说明文档中要有软件界面截图,或者功能流程说明。',
    '源代码：提供Word格式文档，按前、尾各连续30页, 共60页提供(不足60页提供全部代码），'
    '源程序每页不少于50行(结束页除外)，源码中出现的编程语言种类不得超过4种。',
]
for n in NOTES:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(n)
    r.font.size = Pt(10.5)
    r.font.name = 'Calibri'
    _ea(r)

OUT = os.path.join(BASE, '软著信息表.docx')
doc.save(OUT)
print('saved', OUT)
