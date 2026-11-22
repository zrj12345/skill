# -*- coding: utf-8 -*-
"""V1 设计原理.docx  —  structure mirrors StreamEdge/设计原理.docx exactly:

  [H1 22pt] 文档标题
  [H2 16pt 黑体] 一、总体架构概述
      正文段 + “核心目标：” + ● 项目符号
  [H2] 系统功能模块设计          -> 表(模块名称|功能说明)
  [H2] 系统架构图                -> 图
  [H2] 核心模块设计说明
      [H3 16pt] 模块名
          功能描述： + 正文 + ● 列表
          xx流程图： -> 图
          接口设计： -> 表(接口名称|请求方式|参数|返回示例)
          数据结构示例： -> JSON 段（仅首个模块）
  [H2] 运行设计                  -> 表(项目|描述)
  [H2] 附录：流程图汇总          -> 编号引导语 + 图 ×2
"""
import os
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE = os.environ.get('SC_BASE', r'C:\Users\admin\Documents\src\copyright\CMS')  # 新项目改此环境变量
IMG = os.path.join(BASE, 'images')
W_CM = 12.0                     # portrait figures, centred

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.54)
sec.left_margin = sec.right_margin = Cm(3.17)

# ---- Normal: 10.5pt, justified (matches template styleId=1) ----
st = doc.styles['Normal']
st.font.name = 'Times New Roman'
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
st.paragraph_format.space_after = Pt(3)
st.paragraph_format.line_spacing = 1.15
st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def _ea(run, name):
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = rPr.makeelement(qn('w:rFonts'), {})
        rPr.append(rf)
    rf.set(qn('w:eastAsia'), name)
    rf.set(qn('w:ascii'), 'Times New Roman')
    rf.set(qn('w:hAnsi'), 'Times New Roman')


def h1(s):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(20)
    r = p.add_run(s)
    r.font.size = Pt(22)
    r.font.bold = True
    r.font.name = 'Times New Roman'
    _ea(r, '黑体')
    return p


def h2(s):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(7)
    r = p.add_run(s)
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.name = 'Times New Roman'
    _ea(r, '黑体')
    return p


def h3(s):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(s)
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.name = 'Times New Roman'
    _ea(r, '黑体')
    return p


def para(s, indent=True, size=10.5, ea='宋体'):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(21)     # 420 twips = 2 chars
    r = p.add_run(s)
    r.font.size = Pt(size)
    r.font.name = 'Times New Roman'
    _ea(r, ea)
    return p


def label(s):
    """A lead-in line such as 功能描述： (no indent)."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    r = p.add_run(s)
    r.font.size = Pt(10.5)
    r.font.name = 'Times New Roman'
    _ea(r, '宋体')
    return p


def bullets(items):
    """Real Word-style bullet: ● + indent left 840tw / hanging 420tw."""
    for it in items:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Pt(42)
        pf.first_line_indent = Pt(-21)
        pf.space_after = Pt(2)
        r = p.add_run('●  ' + it)
        r.font.size = Pt(10.5)
        r.font.name = 'Times New Roman'
        _ea(r, '宋体')


def table(headers, rows, widths):
    t = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htxt in enumerate(headers):
        c = t.rows[0].cells[j]
        c.text = ''
        cp = c.paragraphs[0]
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cp.add_run(htxt)
        r.font.bold = True
        r.font.size = Pt(10.5)
        r.font.name = 'Times New Roman'
        _ea(r, '宋体')
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.rows[i + 1].cells[j]
            c.text = ''
            r = c.paragraphs[0].add_run(str(v))
            r.font.size = Pt(10.5)
            r.font.name = 'Times New Roman'
            _ea(r, '宋体')
    for j, w in enumerate(widths):
        for row in t.rows:
            row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(fname):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    p.add_run().add_picture(os.path.join(IMG, fname), width=Cm(W_CM))


def json_block(lines):
    for ln in lines:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Pt(21)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(ln)
        r.font.size = Pt(10)
        r.font.name = 'Consolas'
        rPr = r._element.get_or_add_rPr()
        rf = rPr.find(qn('w:rFonts'))
        if rf is None:
            rf = rPr.makeelement(qn('w:rFonts'), {})
            rPr.append(rf)
        rf.set(qn('w:eastAsia'), '宋体')
        rf.set(qn('w:ascii'), 'Consolas')
        rf.set(qn('w:hAnsi'), 'Consolas')


# ==================================================================
# 文档标题
h1('信息服务技术跨媒体数字内容智能生产与管理系统研发设计说明书')

# ---------------------------------------------------------- 一、总体架构概述
h2('一、总体架构概述')
para('本系统为“信息服务技术跨媒体数字内容智能生产与管理系统”，面向跨媒体数字内容的生产与'
     '运营场景，为内容编辑与系统管理人员提供内容录入、资料管理、基础数据维护与权限控制的'
     '统一后台。系统采用浏览器 / 服务器架构，服务端基于 Go 语言开发，前端通过 HTTPS 访问'
     'Nginx 反向代理，请求经统一鉴权后进入业务服务，业务服务完成数据读写并返回统一格式的响应。')
label('核心目标：')
bullets([
    '提供统一的内容录入与维护入口',
    '支持剧集、视频、字幕与图片的一体化管理',
    '实现内容与基础数据的关联引用',
    '提供基于角色的菜单与接口权限控制',
    '保证接口访问的安全与操作可追溯',
])

# ------------------------------------------------------ 系统功能模块设计
h2('系统功能模块设计')
table(['模块名称', '功能说明'], [
    ['剧集内容管理', '剧集信息录入、编辑、查询与上下架维护'],
    ['视频管理', '视频源与播放信息维护'],
    ['字幕与图片管理', '字幕与图片资料的上传、存储与关联'],
    ['基础数据维护', '类型、国家地区与字典项目维护'],
    ['用户管理', '运营账号的创建、编辑与状态控制'],
    ['角色与权限', '角色定义、菜单与接口授权配置'],
    ['登录认证', '账号登录、访问令牌签发与请求校验'],
    ['操作日志', '关键操作的记录与查询'],
], [4.0, 10.66])

# ------------------------------------------------------------ 系统架构图
h2('系统架构图')
figure('fig_arch.png')

# -------------------------------------------------------- 核心模块设计说明
h2('核心模块设计说明')

h3('剧集内容管理模块')
label('功能描述：')
para('实现剧集内容的新建、编辑、查询与上下架维护，支持一次录入多语言标题与简介，'
     '并可关联视频、字幕与图片资料。')
bullets([
    '支持剧集基础信息录入（标题、类型、国家、时长等）',
    '支持多语言标题与简介的录入',
    '支持关联视频、字幕与图片资料',
    '支持按类型、国家、状态等条件分页检索',
    '支持剧集的批量上下架',
])
label('剧集内容管理流程图：')
figure('fig_m1_content.png')
label('接口设计：')
table(['接口名称', '请求方式', '参数', '返回示例'], [
    ['/api/v1/episode/list', 'GET', '页码、每页条数、类型、国家', '列表与总记录数'],
    ['/api/v1/episode', 'POST', '剧集基础信息、多语言内容', '新增记录编号'],
    ['/api/v1/episode/{id}', 'PUT', '剧集编号、待更新字段', '更新结果'],
    ['/api/v1/episode/{id}', 'DELETE', '剧集编号', '删除结果'],
], [4.6, 2.4, 4.2, 3.46])
label('数据结构示例：')
json_block([
    '{',
    '  "episode_id": "10086",',
    '  "title": "示例剧集",',
    '  "genre_id": 12,',
    '  "country_id": 33,',
    '  "status": 1,',
    '  "video_ids": [201, 202],',
    '  "subtitle_ids": [301]',
    '}',
])

h3('视频与字幕资料管理模块')
label('功能描述：')
para('负责视频、字幕与图片资料的上传与存储。文件经格式与大小校验后写入对象存储，'
     '数据库仅记录资料标识与元信息，供内容模块关联引用。')
bullets([
    '支持视频、字幕与图片文件上传',
    '校验文件格式与大小限制',
    '文件写入对象存储并返回唯一标识',
    '支持按资料标识查询与批量删除',
])
label('资料上传与存储流程图：')
figure('fig_m3_upload.png')
label('接口设计：')
table(['接口名称', '请求方式', '参数', '返回示例'], [
    ['/api/v1/upload', 'POST', '文件流、资料类型', '文件标识与访问路径'],
    ['/api/v1/video/list', 'GET', '剧集编号', '视频列表'],
    ['/api/v1/video/{id}', 'DELETE', '视频编号', '删除结果'],
    ['/api/v1/subtitle/list', 'GET', '剧集编号', '字幕列表'],
], [4.6, 2.4, 4.2, 3.46])

h3('基础数据维护模块')
label('功能描述：')
para('维护类型、国家地区与字典项目等基础数据，为内容模块提供统一的取值来源。')
table(['数据类型', '维护方式', '引用位置'], [
    ['类型', '名称、排序与状态维护', '剧集类型字段'],
    ['国家地区', '名称与代码维护', '剧集国家字段'],
    ['字典项目', '键值对维护', '各业务枚举字段'],
], [3.2, 5.9, 5.56])
bullets([
    '支持基础数据的新增、编辑与排序',
    '名称与编码唯一性校验',
    '修改后即时生效，内容模块直接引用',
])
label('基础数据维护流程图：')
figure('fig_m2_basedata.png')
label('接口设计：')
table(['接口名称', '请求方式', '参数', '返回示例'], [
    ['/api/v1/genre/list', 'GET', '页码、每页条数', '类型列表'],
    ['/api/v1/genre', 'POST', '名称、排序', '新增结果'],
    ['/api/v1/country/list', 'GET', '页码、每页条数', '国家列表'],
    ['/api/v1/dict/list', 'GET', '字典分组', '字典项目列表'],
], [4.6, 2.4, 4.2, 3.46])

h3('用户与角色权限模块')
label('功能描述：')
para('管理运营账号与角色，通过为角色绑定菜单与接口权限，实现基于角色的访问控制。')
bullets([
    '支持账号的创建、编辑与状态控制',
    '支持角色定义与菜单、接口权限勾选',
    '支持用户与角色绑定关系维护',
    '权限策略保存后即时生效',
])
label('角色权限分配流程图：')
figure('fig_m4_role.png')

h3('登录认证模块')
label('功能描述：')
para('提供账号登录与访问令牌签发，后续请求携带令牌完成身份识别与校验。')
bullets([
    '账号密码登录，密码以不可逆摘要存储',
    '连续失败达阈值后限制登录',
    '登录成功签发带有效期的访问令牌',
    '请求校验令牌有效性并注入身份信息',
])
label('登录认证流程图：')
figure('fig_m5_auth.png')

# ---------------------------------------------------------------- 运行设计
h2('运行设计')
table(['项目', '描述'], [
    ['部署方式', 'Nginx 反向代理，业务服务以常驻进程运行'],
    ['运行环境', 'Linux（CentOS 7 / Ubuntu 20.04 及以上）'],
    ['数据库', 'MySQL 8.0，存储业务主数据与权限数据'],
    ['缓存', 'Redis 6.0，用于会话与热点数据缓存'],
    ['对象存储', 'S3 兼容存储，存放图片与字幕文件'],
], [3.6, 11.06])

# ------------------------------------------------------- 附录：流程图汇总
h2('附录：流程图汇总')
label('1.内容录入与发布流程图')
figure('fig_a1_content_flow.png')
label('2.权限校验流程图')
figure('fig_a2_auth_flow.png')

# ------------------------------------------------------------------ 保存
target = os.path.join(BASE, '设计原理.docx')
try:
    doc.save(target)
    print('saved', target)
except PermissionError:
    alt = os.path.join(BASE, '设计原理(V1).docx')
    doc.save(alt)
    print('locked -> saved', alt)
