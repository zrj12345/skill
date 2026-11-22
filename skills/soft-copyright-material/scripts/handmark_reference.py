# -*- coding: utf-8 -*-
"""在真实系统截图上做「真人手写」风格的红色画笔标注。

风格要点（对照用户给的示例）：
  - 红色实心圆里写白色数字 1 / 2 / 3 / 4（文字数字，非圈码字符）
  - 略带抖动、粗细不均的红色手绘箭头指向要操作的控件
  - 操作说明直接写在步骤（数字圆）旁边，楷体红字、轻微倾斜，像手写批注
  - 不扩展画布、不加边框、不统一模板：图片尺寸与原截图完全一致

复用指引：
  1) 把 ROOT / SRC / DST 改成新项目路径（或用 SC_ROOT / SC_SRC / SC_DST 环境变量）；
  2) MARKS 是「每张图 → [(序号, 控件坐标, 原说明, 落点), ...]」，坐标均为相对值 0~1；
  3) SHORT 是图上短句（6~10 字，不要【】方括号），完整说明写在文档正文；
  4) 本脚本会先调用 desensitize.py 打码再叠加批注，顺序不可颠倒；
  5) 随机种子按「文件名+序号」固定，重绘效果一致，便于反复微调。
"""
import os, math, random, hashlib
from PIL import Image, ImageDraw, ImageFont
from desensitize import desensitize

ROOT = os.environ.get('SC_ROOT', r'C:\Users\admin\Documents\src\copyright')
SRC = os.environ.get('SC_SRC', os.path.join(ROOT, r'软著202609\CMS_补正材料'))
DST = os.environ.get('SC_DST', os.path.join(ROOT, r'软著202609\CMS_补正材料_标注版'))
os.makedirs(DST, exist_ok=True)

KAI = r'C:\Windows\Fonts\simkai.ttf'          # 楷体：手写批注感
BOLD = r'C:\Windows\Fonts\msyhbd.ttc'         # 圆内数字
RED_BASE = (216, 46, 46)


# ---------------------------------------------------------------- 标注配置
# 每项 = (序号, 控件坐标, 操作说明文字, 标注落点)；坐标均为相对值 0~1
MARKS = {
    '00_login.png': [
        (1, (0.660, 0.340), '输入登录账号与密码', (0.735, 0.300)),
        (2, (0.660, 0.480), '按右侧图片填写 4 位验证码', (0.735, 0.420)),
        (3, (0.655, 0.558), '点【登录】，校验通过后进入系统', (0.735, 0.550)),
    ],
    '01_dashboard.png': [
        (1, (0.320, 0.330), '柱状图：各栏目内容数量', (0.690, 0.240)),
        (2, (0.515, 0.270), '环形图：题材分布占比', (0.690, 0.400)),
        (3, (0.420, 0.640), '折线图：近期发布与访问趋势', (0.690, 0.600)),
    ],
    '02_column.png': [
        (1, (0.145, 0.230), '在左侧栏目树选中父栏目', (0.620, 0.180)),
        (2, (0.172, 0.180), '点【新增】建子栏目、填名称排序', (0.620, 0.310)),
        (3, (0.700, 0.360), '右侧勾选栏目下归属的内容', (0.620, 0.450)),
        (4, (0.657, 0.506), '点【保存】提交栏目与内容关联', (0.620, 0.620)),
    ],
    '03_episode.png': [
        (1, (0.520, 0.104), '按名称、题材、国家、语言设置条件', (0.560, 0.430)),
        (2, (0.791, 0.104), '点【搜索】过滤剧集', (0.560, 0.530)),
        (3, (0.890, 0.104), '点【手动创建】进入剧集录入', (0.560, 0.630)),
        (4, (0.860, 0.333), '行内点【添加视频】维护分集字幕', (0.560, 0.730)),
    ],
    '04_notice.png': [
        (1, (0.630, 0.104), '输入标题或时间范围后点【搜索】', (0.560, 0.430)),
        (2, (0.720, 0.104), '点【新增】打开通知编辑弹窗', (0.560, 0.530)),
        (3, (0.869, 0.254), '行内编辑内容或调整推送状态', (0.560, 0.630)),
        (4, (0.500, 0.300), '保存后按目标用户范围下发', (0.560, 0.730)),
    ],
    '05_theme.png': [
        (1, (0.424, 0.104), '点【新增】创建主题', (0.600, 0.560)),
        (2, (0.450, 0.280), '填写主题名称、封面与排序值', (0.600, 0.650)),
        (3, (0.869, 0.494), '行内可编辑或删除主题', (0.600, 0.740)),
        (4, (0.500, 0.420), '主题被剧集引用时不允许直接删除', (0.600, 0.830)),
    ],
    '06_country.png': [
        (1, (0.566, 0.104), '点【新增】录入国家 / 地区', (0.600, 0.680)),
        (2, (0.500, 0.280), '填写名称、编码与所属区域', (0.600, 0.760)),
        (3, (0.794, 0.614), '行内修改或停用', (0.600, 0.840)),
        (4, (0.500, 0.480), '剧集表单的国家下拉引用此字典', (0.600, 0.920)),
    ],
    '07_heading.png': [
        (1, (0.601, 0.104), '点【新增】维护题材字典', (0.600, 0.480)),
        (2, (0.550, 0.250), '填写题材名称与排序', (0.600, 0.570)),
        (3, (0.869, 0.274), '行内编辑、删除', (0.600, 0.660)),
        (4, (0.500, 0.380), '剧集创建页的题材下拉从此处读取', (0.600, 0.750)),
    ],
    '08_apply.png': [
        (1, (0.584, 0.104), '点【新增】登记客户端应用', (0.600, 0.500)),
        (2, (0.520, 0.250), '填写应用名称、包名与平台', (0.600, 0.590)),
        (3, (0.869, 0.294), '配置启用状态与接口权限', (0.600, 0.680)),
        (4, (0.500, 0.400), '保存后应用方可请求开放接口', (0.600, 0.770)),
    ],
    '09_config.png': [
        (1, (0.584, 0.104), '点【新增】添加系统参数', (0.600, 0.620)),
        (2, (0.520, 0.250), '填写配置键、配置值与说明', (0.600, 0.710)),
        (3, (0.500, 0.440), '按业务模块分组维护参数', (0.600, 0.800)),
        (4, (0.500, 0.560), '服务端读取配置后即时生效', (0.600, 0.890)),
    ],
    '10_transcoding.png': [
        (1, (0.593, 0.104), '点【新增】创建转码模板', (0.600, 0.580)),
        (2, (0.550, 0.250), '设置分辨率、码率与封装格式', (0.600, 0.670)),
        (3, (0.869, 0.254), '行内启停或编辑模板', (0.600, 0.760)),
        (4, (0.500, 0.400), '上传视频后按模板生成多码率流文件', (0.600, 0.850)),
    ],
    '11_menu.png': [
        (1, (0.601, 0.104), '点【新增】登记菜单与路由', (0.600, 0.420)),
        (2, (0.550, 0.220), '选择上级菜单、图标与排序', (0.600, 0.510)),
        (3, (0.550, 0.300), '填写对应的接口权限标识', (0.600, 0.600)),
        (4, (0.500, 0.400), '保存后在角色授权树中可见', (0.600, 0.690)),
    ],
    '12_role.png': [
        (1, (0.584, 0.104), '点【新增】创建角色', (0.600, 0.440)),
        (2, (0.531, 0.252), '在列表行点击【授权】', (0.600, 0.530)),
        (3, (0.869, 0.312), '勾选菜单与接口级权限', (0.600, 0.620)),
        (4, (0.500, 0.420), '用户绑定角色后继承权限', (0.600, 0.710)),
    ],
    '13_user.png': [
        (1, (0.584, 0.104), '点【新增】创建系统用户', (0.600, 0.580)),
        (2, (0.530, 0.300), '列表行切换启用 / 停用状态', (0.600, 0.670)),
        (3, (0.869, 0.508), '行内重置密码或重新分配角色', (0.600, 0.760)),
        (4, (0.500, 0.560), '停用后令牌校验即时拒绝访问', (0.600, 0.850)),
    ],
    '14_log.png': [
        (1, (0.916, 0.096), '按请求路径或时间范围检索', (0.600, 0.180)),
        (2, (0.450, 0.330), '查看方法、IP、耗时与操作时间', (0.600, 0.280)),
        (3, (0.500, 0.560), '每条记录对应一次受控接口调用', (0.600, 0.380)),
        (4, (0.816, 0.956), '底部分页翻阅全部审计记录', (0.600, 0.480)),
    ],
    '15_episode_create.png': [
        (1, (0.280, 0.220), '选择剧集类型并填写名称', (0.680, 0.220)),
        (2, (0.280, 0.380), '关联题材、国家与语言字典', (0.680, 0.360)),
        (3, (0.280, 0.560), '设置付费方式、金币值与上架状态', (0.680, 0.500)),
        (4, (0.280, 0.790), '上传海报封面后点【保存】', (0.680, 0.650)),
    ],
    '16_episode_edit.png': [
        (1, (0.280, 0.210), '进入已有剧集，回显基础信息', (0.680, 0.220)),
        (2, (0.280, 0.380), '修改简介、演员与多语言名称', (0.680, 0.360)),
        (3, (0.280, 0.570), '调整付费与上架设置', (0.680, 0.500)),
        (4, (0.280, 0.790), '保存后列表与前台同步更新', (0.680, 0.650)),
    ],
    '17_episode_video.png': [
        (1, (0.370, 0.104), '点【创建视频】录入分集', (0.620, 0.200)),
        (2, (0.495, 0.104), '点【批量上传字幕】一次导入多集', (0.620, 0.300)),
        (3, (0.600, 0.350), '查看排序、时长、金币与音轨', (0.620, 0.420)),
        (4, (0.869, 0.754), '行内修改字幕、流文件与状态', (0.620, 0.540)),
    ],
    '18_notice_add.png': [
        (1, (0.450, 0.320), '填写通知标题与正文', (0.660, 0.280)),
        (2, (0.450, 0.420), '选择推送目标与生效时间', (0.660, 0.400)),
        (3, (0.450, 0.490), '设置展示位置与跳转链接', (0.660, 0.520)),
        (4, (0.333, 0.576), '点【确定】保存并发布', (0.660, 0.640)),
    ],
    '19_config_add.png': [
        (1, (0.450, 0.300), '填写参数名称', (0.660, 0.280)),
        (2, (0.450, 0.380), '填写配置键（唯一）', (0.660, 0.400)),
        (3, (0.450, 0.440), '填写配置值与备注', (0.660, 0.520)),
        (4, (0.420, 0.490), '点【确定】写入配置表', (0.660, 0.640)),
    ],
    '20_role_perm.png': [
        (1, (0.420, 0.320), '展开菜单树查看功能模块', (0.610, 0.280)),
        (2, (0.420, 0.450), '勾选允许访问的菜单节点', (0.610, 0.400)),
        (3, (0.420, 0.570), '再勾选新增 / 编辑 / 删除接口权限', (0.610, 0.520)),
        (4, (0.440, 0.690), '点【确定】保存角色权限', (0.610, 0.640)),
    ],
    '21_user_add.png': [
        (1, (0.450, 0.300), '填写登录账号与用户名', (0.610, 0.280)),
        (2, (0.450, 0.420), '设置初始密码', (0.610, 0.400)),
        (3, (0.450, 0.550), '选择所属角色与部门', (0.610, 0.520)),
        (4, (0.453, 0.690), '点【确定】创建用户', (0.610, 0.640)),
    ],
}

# 图上批注用短句：字大、好认，像真人随手写在控件旁；完整操作说明仍在正文里
SHORT = {
    '00_login.png':          ['填账号与密码', '填 4 位验证码', '点登录进入系统'],
    '01_dashboard.png':      ['栏目内容数量', '题材分布占比', '近期访问趋势'],
    '02_column.png':         ['选中父栏目', '点新增建子栏目', '勾选归属内容', '点保存提交关联'],
    '03_episode.png':        ['设置组合筛选', '点搜索', '点手动创建', '行内点添加视频'],
    '04_notice.png':         ['按标题 / 时间检索', '点新增建通知', '行内编辑或停用', '保存后按范围下发'],
    '05_theme.png':          ['点新增建主题', '填名称 / 封面 / 排序', '行内编辑或删除', '被引用时禁止删除'],
    '06_country.png':        ['点新增录国家', '填名称与编码', '行内修改或停用', '剧集下拉引用此表'],
    '07_heading.png':        ['点新增维护题材', '填名称与排序', '行内编辑 / 删除', '剧集表单引用此表'],
    '08_apply.png':          ['点新增登记应用', '填名称 / 包名 / 平台', '配置状态与权限', '保存后可调接口'],
    '09_config.png':         ['点新增加参数', '填配置键与值', '按模块分组维护', '服务端读取生效'],
    '10_transcoding.png':    ['点新增建转码模板', '设分辨率与码率', '行内启停或编辑', '生成多码率流文件'],
    '11_menu.png':           ['点新增登记菜单', '选上级 / 图标 / 排序', '填接口权限标识', '角色授权树可见'],
    '12_role.png':           ['点新增建角色', '行内点授权', '勾选菜单与接口权限', '绑定用户继承权限'],
    '13_user.png':           ['点新增建用户', '切换启用 / 停用', '重置密码 / 分角色', '停用即拒绝访问'],
    '14_log.png':            ['按路径 / 时间检索', '看方法 / IP / 耗时', '每次接口调用留痕', '分页翻阅审计记录'],
    '15_episode_create.png': ['选类型、填名称', '关联题材 / 国家 / 语言', '设付费与上架', '传海报后点保存'],
    '16_episode_edit.png':   ['回显基础信息', '改简介与多语言名', '调整付费与上架', '保存后同步更新'],
    '17_episode_video.png':  ['点创建视频录分集', '点批量上传字幕', '看时长 / 金币 / 音轨', '行内改字幕与流文件'],
    '18_notice_add.png':     ['填标题与正文', '选推送目标与时间', '设位置与跳转', '点确定保存发布'],
    '19_config_add.png':     ['填参数名称', '填配置键（唯一）', '填配置值与备注', '点确定写入配置'],
    '20_role_perm.png':      ['展开菜单树', '勾选菜单节点', '勾选接口级权限', '点确定保存权限'],
    '21_user_add.png':       ['填账号与用户名', '设置初始密码', '选角色与部门', '点确定创建用户'],
}

# 登录页构图特殊（表单居中、四周留白），固定把批注放在卡片右侧空白
FORCE_SPOT = {
    '00_login.png': [(0.805, 0.340), (0.805, 0.480), (0.805, 0.645)],
}


# ---------------------------------------------------------------- 绘制原语
def rng(fname, n):
    s = int(hashlib.md5((fname + str(n)).encode()).hexdigest()[:8], 16)
    return random.Random(s)


def text_sticker(text, size, color, angle, k):
    """手写楷体红字：红色描边加粗笔画 + 极细白底衬托 + 轻微倾斜。"""
    f = ImageFont.truetype(KAI, max(14, int(size * k)))
    bb = f.getbbox(text, stroke_width=1)
    tw, th = bb[2] - bb[0] + 20, bb[3] - bb[1] + 20
    layer = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = 10 - bb[0], 10 - bb[1]
    ow = max(1, int(1.0 * k))
    for dx, dy in ((-ow, 0), (ow, 0), (0, -ow), (0, ow)):
        d.text((ox + dx, oy + dy), text, font=f,
               fill=(255, 255, 255, 215), stroke_width=1,
               stroke_fill=(255, 255, 255, 215))
    d.text((ox, oy), text, font=f, fill=color,
           stroke_width=1, stroke_fill=color)
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    return layer


def hand_circle(d, cx, cy, r, color, k, rr):
    pts = []
    for i in range(18):
        a = 2 * math.pi * i / 18
        rad = r * (1 + rr.uniform(-0.07, 0.07))
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a) * 0.96))
    d.polygon(pts, fill=color)
    d.line(pts + [pts[0]], fill=color, width=max(2, int(2.5 * k)), joint='curve')
    return pts


def hand_arrow(d, a, b, color, k, rr):
    x1, y1 = a; x2, y2 = b
    dx, dy = x2 - x1, y2 - y1
    L = max(1.0, math.hypot(dx, dy))
    nx, ny = -dy / L, dx / L
    bow = L * rr.uniform(0.02, 0.07) * rr.choice((-1, 1))
    n = max(5, min(14, int(L / (34 * k))))
    pts = []
    for i in range(n + 1):
        t = i / n
        off = math.sin(math.pi * t) * bow + rr.uniform(-1.6, 1.6) * k
        pts.append((x1 + dx * t + nx * off, y1 + dy * t + ny * off))
    for i in range(len(pts) - 1):
        w = max(2, int(rr.uniform(2.8, 4.4) * k))
        d.line([pts[i], pts[i + 1]], fill=color, width=w)
    ang = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
    Lh = 17 * k
    d.polygon([(x2, y2),
               (x2 - Lh * math.cos(ang - 0.42), y2 - Lh * math.sin(ang - 0.42)),
               (x2 - Lh * math.cos(ang + 0.42), y2 - Lh * math.sin(ang + 0.42))],
              fill=color)
    # 偶尔在箭头边上补一笔画，像真人随手描的
    if rr.random() < 0.35:
        d.line([(x2 - 6 * k, y2 - 5 * k), (x2 - 13 * k, y2 - 12 * k)],
               fill=color, width=max(1, int(1.6 * k)))


POPUPS = {'18_notice_add.png', '19_config_add.png',
          '20_role_perm.png', '21_user_add.png'}


def clean_ratio(im, box, step=6):
    """区域「背景干净度」：排除黑色文字与蓝色/红色控件；
    纯白留白与弹窗外的灰色遮罩都算干净，适合落手写红字。"""
    W, H = im.size
    px = im.load()
    x0, y0, x1, y1 = [int(v) for v in box]
    tot = clean = 0
    for y in range(max(0, y0), min(H, y1), step):
        for x in range(max(0, x0), min(W, x1), step):
            r, g, b = px[x, y][:3]
            bright = (r + g + b) / 3
            mx, mn = max(r, g, b), min(r, g, b)
            ink = (bright < 95) or (mx - mn > 62 and bright < 225)
            tot += 1
            if not ink:
                clean += 1
    return clean / max(1, tot)


def choose_spot(im, tgt, sw, sh, r, k, rr, occupied, fname):
    """在控件附近找一个空白、不重叠、方向随机的小落点，让箭头保持短促。"""
    W, H = im.size
    tx, ty = tgt
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1),
            (0.85, 0.55), (-0.85, 0.55), (0.85, -0.55), (-0.85, -0.55)]
    # 顶部按钮/筛选区：禁止把数字圆推到页面最上方的标题栏，统一往下方空白走
    if ty < 0.18 * H:
        dirs = [v for v in dirs if v[1] >= 0]
    rr.shuffle(dirs)
    best = None
    for dx, dy in dirs:
        D = (70 + rr.uniform(0, 48)) * k
        cx, cy = tx + dx * D, ty + dy * D
        if cx - r < 5 * k or cx + r > W - 5 * k or cy - r < 5 * k or cy + r > H - 5 * k:
            continue
        if abs(dx) >= abs(dy):
            opts = [(cx + r + 8 * k, cy - sh / 2),
                    (cx - r - 8 * k - sw, cy - sh / 2),
                    (cx - sw / 2, cy + r + 8 * k),
                    (cx - sw / 2, cy - r - 8 * k - sh)]
        else:
            opts = [(cx - sw / 2, cy + r + 8 * k),
                    (cx - sw / 2, cy - r - 8 * k - sh),
                    (cx + r + 8 * k, cy - sh / 2),
                    (cx - r - 8 * k - sw, cy - sh / 2)]
        for px, py in opts:
            if px < 5 * k or py < 5 * k or px + sw > W - 5 * k or py + sh > H - 5 * k:
                continue
            tbox = (px, py, px + sw, py + sh)
            cbox = (cx - r, cy - r, cx + r, cy + r)
            sc = 0.62 * clean_ratio(im, tbox) + 0.38 * clean_ratio(im, cbox)
            # 弹窗页：优先把说明写在四周灰色遮罩上，别压住弹窗内容
            if fname in POPUPS:
                midx = (px + sw / 2) / W
                sc += 0.32 if (midx < 0.33 or midx > 0.66) else -0.28
            # 避开页面顶栏、底栏与左侧菜单
            if cy < 0.07 * H or cy > 0.95 * H:
                sc -= 0.60
            if py < 0.055 * H or py + sh > 0.97 * H:
                sc -= 0.45
            if px < 0.14 * W:
                sc -= 0.30
            for ob in occupied:
                ix = max(0, min(tbox[2], ob[2]) - max(tbox[0], ob[0]))
                iy = max(0, min(tbox[3], ob[3]) - max(tbox[1], ob[1]))
                if ix * iy > 0:
                    sc -= 0.40
                if ix * iy > 0.05 * sw * sh:
                    sc -= 1.00
            sc += rr.uniform(-0.06, 0.06)
            if best is None or sc > best[0]:
                best = (sc, cx, cy, px, py, tbox, cbox)
    if best is None:                       # 极端兜底：贴着控件右下方
        cx, cy = tx + 46 * k, ty + 46 * k
        px, py = cx + r + 8 * k, cy - sh / 2
        px = max(5 * k, min(W - sw - 5 * k, px))
        py = max(5 * k, min(H - sh - 5 * k, py))
        best = (0, cx, cy, px, py, (px, py, px + sw, py + sh),
                (cx - r, cy - r, cx + r, cy + r))
    return best


def mark_one(fname):
    src = os.path.join(SRC, fname)
    # 先对敏感信息打马赛克，再叠加手写标注（批注在最上层，不会被盖住）
    base, _ = desensitize(src, fname, save=False)
    im = base.convert('RGBA')
    W, H = im.size
    k = W / 1600.0
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    occupied = []

    for idx, (n, tgt, _text, _lab) in enumerate(MARKS[fname]):
        rr = rng(fname, n)
        color = tuple(max(0, min(255, c + rr.randint(-9, 9))) for c in RED_BASE) + (255,)
        tx, ty = tgt[0] * W, tgt[1] * H
        r = 24 * k * rr.uniform(0.92, 1.10)

        text = SHORT[fname][idx]
        sticker = text_sticker(text, 34, color, rr.uniform(-2.0, 2.0), k)
        sw, sh = sticker.size
        if fname in FORCE_SPOT:
            fx, fy = FORCE_SPOT[fname][idx]
            lx, ly = fx * W, fy * H
            px, py = lx + r + 6 * k, ly - sh / 2
            if px + sw > W - 4 * k:
                px = lx - r - 6 * k - sw
            px = max(4 * k, min(W - sw - 4 * k, px))
            py = max(4 * k, min(H - sh - 4 * k, py))
            tbox = (px, py, px + sw, py + sh)
            cbox = (lx - r, ly - r, lx + r, ly + r)
        else:
            _, lx, ly, px, py, tbox, cbox = choose_spot(
                im, (tx, ty), sw, sh, r, k, rr, occupied, fname)
        occupied.extend([tbox, cbox])

        # 数字圆
        hand_circle(d, lx, ly, r, color, k, rr)
        nf = ImageFont.truetype(BOLD, max(15, int(28 * k)))
        s = str(n)
        nb = nf.getbbox(s)
        d.text((lx - (nb[2] - nb[0]) / 2, ly - (nb[3] - nb[1]) / 2 - nb[1]),
               s, font=nf, fill=(255, 255, 255, 255))

        # 短箭头：从圆边缘指向控件
        ang = math.atan2(ty - ly, tx - lx)
        start = (lx + (r + 3 * k) * math.cos(ang), ly + (r + 3 * k) * math.sin(ang))
        hand_arrow(d, start, (tx, ty), color, k, rr)

        # 操作说明：直接写在步骤旁边
        layer.alpha_composite(sticker, (int(px), int(py)))

        # 偶尔补一道手绘下划线
        if rr.random() < 0.4:
            uy = py + sh - 3 * k
            d.line([(px + 2 * k, uy),
                    (px + sw * rr.uniform(0.5, 0.9), uy + rr.uniform(-2, 2) * k)],
                   fill=color, width=max(1, int(1.7 * k)))

    out = Image.alpha_composite(im, layer).convert('RGB')
    dst = os.path.join(DST, fname)
    out.save(dst, quality=94)
    return dst, (W, H)


if __name__ == '__main__':
    missing = [f for f in MARKS if not os.path.exists(os.path.join(SRC, f))]
    if missing:
        raise SystemExit('missing source: ' + str(missing))
    for f in sorted(MARKS):
        p, size = mark_one(f)
        print(f'{f:26s} {size[0]}x{size[1]}  {os.path.getsize(p) // 1024:4d} KB  {len(MARKS[f])} 处标注')
    print('\n输出目录:', DST)
