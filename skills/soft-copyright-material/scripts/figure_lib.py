# -*- coding: utf-8 -*-
"""Portrait figure set matching the template's figure footprint
(~12 x 14 cm each, vertical flows).  8 caption-free figures.

Layout is auto-computed and validated (bounds + overlap + text fit).
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.environ.get('SC_FIG_DIR', r'C:\Users\admin\Documents\src\copyright\CMS\images')  # 新项目改此环境变量
os.makedirs(OUT, exist_ok=True)
SS = 2
YAHEI, YAHEIBD = r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\msyhbd.ttc'

INK, INK_SOFT, LINE = (38, 42, 48), (104, 112, 124), (120, 128, 140)
T_NEUTRAL = ((247, 248, 250), (150, 158, 170))
T_ACCENT  = ((231, 241, 254), (52, 120, 200))
T_WARM    = ((253, 245, 235), (194, 141, 66))
T_GREEN   = ((237, 248, 242), (78, 156, 122))
T_VIOLET  = ((243, 241, 251), (126, 108, 187))
T_ROSE    = ((253, 241, 244), (196, 110, 132))
T_BAND    = ((252, 252, 253), (208, 214, 224))

_fc = {}
def _font(p, s):
    k = (p, round(s, 1))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(p, int(s * SS))
    return _fc[k]
def F(s):  return _font(YAHEI, s)
def FB(s): return _font(YAHEIBD, s)


class Fig:
    """Portrait canvas, main column centred, branches to the right."""
    CX = 500
    BOX_W = 400
    DIA_W = 320

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new('RGB', (w * SS, h * SS), (255, 255, 255))
        self.d = ImageDraw.Draw(self.img)
        self.nodes, self.problems = [], []

    def text(self, xy, s, f, fill=INK, anchor='la'):
        self.d.text((xy[0]*SS, xy[1]*SS), s, font=f, fill=fill, anchor=anchor)

    def tw(self, s, f):
        b = self.d.textbbox((0, 0), s, font=f)
        return (b[2]-b[0])/SS

    def fit(self, s, maxw, base, bold=False, floor=8.0):
        size = base
        while size > floor:
            f = FB(size) if bold else F(size)
            if self.tw(s, f) <= maxw:
                return f
            size -= 0.5
        return FB(floor) if bold else F(floor)

    def rec(self, x, y, w, h, t):
        self.nodes.append((x, y, w, h, t))

    def box(self, x, y, w, h, title, sub=None, tint=T_NEUTRAL,
            tsize=14, ssize=11.5, radius=7, record=True):
        f_, s_ = tint
        self.d.rounded_rectangle([x*SS, y*SS, (x+w)*SS, (y+h)*SS], radius=radius*SS,
                                 fill=f_, outline=s_, width=max(1, int(1.7*SS)))
        if sub:
            self.text((x+w/2, y+h/2-14), title, self.fit(title, w-24, tsize, True), INK, 'mm')
            self.text((x+w/2, y+h/2+13), sub, self.fit(sub, w-24, ssize), INK_SOFT, 'mm')
        else:
            self.text((x+w/2, y+h/2), title, self.fit(title, w-24, tsize, True), INK, 'mm')
        if record:
            self.rec(x, y, w, h, title)

    def diamond(self, cx, cy, w, h, title, tint=T_WARM, tsize=13):
        f_, s_ = tint
        pts = [(cx, cy-h/2), (cx+w/2, cy), (cx, cy+h/2), (cx-w/2, cy)]
        self.d.polygon([(p[0]*SS, p[1]*SS) for p in pts], fill=f_, outline=s_,
                       width=max(1, int(1.7*SS)))
        self.text((cx, cy), title, self.fit(title, w*0.62, tsize, True), INK, 'mm')
        self.rec(cx-w/2, cy-h/2, w, h, title)

    def arrow(self, tip, direction, size=9.0, color=LINE):
        s_, tx, ty = size, tip[0], tip[1]
        if direction == 'd':
            pts = [(tx, ty), (tx-s_*.5, ty-s_), (tx+s_*.5, ty-s_)]
        elif direction == 'u':
            pts = [(tx, ty), (tx-s_*.5, ty+s_), (tx+s_*.5, ty+s_)]
        elif direction == 'r':
            pts = [(tx, ty), (tx-s_, ty-s_*.5), (tx-s_, ty+s_*.5)]
        else:
            pts = [(tx, ty), (tx+s_, ty-s_*.5), (tx+s_, ty+s_*.5)]
        self.d.polygon([(p[0]*SS, p[1]*SS) for p in pts], fill=color)

    def line(self, pts, color=LINE, w=1.7):
        self.d.line([(p[0]*SS, p[1]*SS) for p in pts], fill=color, width=max(1, int(w*SS)))

    def vlink(self, y1, y2, x, label=None, color=LINE, side='r'):
        a, b = (y1, y2) if y2 > y1 else (y2, y1)
        self.line([(x, a), (x, b + (-7 if y2 > y1 else 7))], color)
        self.arrow((x, y2), 'd' if y2 > y1 else 'u', 9, color)
        if label:
            lx = x + 12 if side == 'r' else x - 12
            self.text((lx, (a+b)/2 - 9), label, F(11.5), INK_SOFT,
                      'la' if side == 'r' else 'ra')

    def hlink(self, y, x1, x2, label=None, color=LINE):
        a, b = (x1, x2) if x2 > x1 else (x2, x1)
        self.line([(a, y), (b + (-7 if x2 > x1 else 7), y)], color)
        self.arrow((x2, y), 'r' if x2 > x1 else 'l', 9, color)
        if label:
            self.text(((a+b)/2, y-18), label, F(11.5), INK_SOFT, 'ma')

    def elbow(self, pts, color=LINE):
        self.line(pts, color)
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        d = ('d' if y2 > y1 else 'u') if abs(y2-y1) > abs(x2-x1) else ('r' if x2 > x1 else 'l')
        self.arrow((x2, y2), d, 9, color)

    def note(self, x, y, s, size=11.5):
        self.text((x, y), s, F(size), INK_SOFT)

    def band(self, x, y, w, h, label):
        f_, s_ = T_BAND
        self.d.rounded_rectangle([x*SS, y*SS, (x+w)*SS, (y+h)*SS], radius=9*SS,
                                 fill=f_, outline=s_, width=max(1, int(1.5*SS)))
        self.d.rectangle([(x+15)*SS, (y+14)*SS, (x+18)*SS, (y+28)*SS], fill=T_ACCENT[1])
        self.text((x+26, y+13), label, FB(13), INK_SOFT)

    def vflow(self, items, y0=50, gap=58, h=64, dh=112):
        """Vertical chain. items: (title, kind, tint, sub).
        Returns list of spans (top, bottom, cx)."""
        spans = []
        y = y0
        for (t, kind, tint, sub) in items:
            if kind == 'd':
                cx = self.CX
                self.diamond(cx, y + dh/2, self.DIA_W, dh, t, tint=tint or T_WARM)
                spans.append((y, y + dh, cx))
                y += dh + gap
            else:
                x = self.CX - self.BOX_W/2
                self.box(x, y, self.BOX_W, h, t, sub=sub, tint=tint or T_NEUTRAL)
                spans.append((y, y + h, self.CX))
                y += h + gap
        return spans, y - gap

    def chain_arrows(self, spans):
        for i in range(len(spans) - 1):
            self.vlink(spans[i][1], spans[i+1][0], self.CX)

    def validate(self):
        for (x, y, w, h, t) in self.nodes:
            if x < 0 or y < 0 or x + w > self.w or y + h > self.h:
                self.problems.append(f'OUT OF BOUNDS: "{t}" x={x:.0f} y={y:.0f}')
        for i in range(len(self.nodes)):
            for j in range(i+1, len(self.nodes)):
                x1, y1, w1, h1, t1 = self.nodes[i]
                x2, y2, w2, h2, t2 = self.nodes[j]
                ox = min(x1+w1, x2+w2) - max(x1, x2)
                oy = min(y1+h1, y2+h2) - max(y1, y2)
                if ox > 3 and oy > 3:
                    self.problems.append(f'OVERLAP: "{t1}" vs "{t2}"')
        return self.problems

    def save(self, name):
        probs = self.validate()
        self.img.resize((self.w, self.h), Image.LANCZOS).save(
            os.path.join(OUT, name), 'PNG', optimize=True)
        print(f'  [{"OK " if not probs else "WARN"}] {name:26s} '
              f'{self.w}x{self.h} nodes={len(self.nodes)}')
        for p in probs:
            print('        !', p)


# ===================================================== 1 系统架构（纵排）
def fig_arch():
    f = Fig(1000, 1210)
    M, IW = 40, 920
    # 接入层
    f.band(M, 40, IW, 250, '接入层')
    for i, s in enumerate(['运营控制台', '系统管理台', '媒体上传']):
        f.box(M+110, 80 + i*66, IW-220, 54, s, tsize=13.5)
    f.vlink(290, 312, f.CX)
    # 网关层
    f.band(M, 312, IW, 314, '接口网关层')
    for i, s in enumerate(['跨域处理', '请求日志', 'JWT 鉴权', '参数校验']):
        f.box(M+110, 352 + i*66, IW-220, 54, s, tint=T_ACCENT, tsize=13.5)
    f.vlink(626, 648, f.CX)
    # 业务服务层
    f.band(M, 648, IW, 306, '业务服务层')
    groups = [('内容管理', '剧集 / 视频 / 字幕图片', T_WARM),
              ('基础数据', '类型 / 国家地区 / 字典', T_GREEN),
              ('系统管理', '用户角色 / 菜单权限 / 日志', T_ROSE)]
    for i, (g, s, tint) in enumerate(groups):
        f.box(M+110, 688 + i*72, IW-220, 62, g, sub=s, tint=tint,
              tsize=13.5, ssize=11)
    f.vlink(954, 976, f.CX)
    # 数据与存储层
    f.band(M, 976, IW, 194, '数据与存储层')
    for i, (t, s) in enumerate([('MySQL 数据库', '业务主数据'), ('对象存储', '图片与字幕')]):
        f.box(M+110, 1016 + i*70, IW-220, 60, t, sub=s, tsize=13.5)
    f.save('fig_arch.png')


# ============================================ 2 剧集内容管理流程（纵排）
def fig_m1_content():
    f = Fig(1000, 980)
    items = [('新建剧集', 'b', T_ACCENT, None),
             ('录入基础信息', 'b', T_ACCENT, None),
             ('关联视频与字幕', 'b', T_ACCENT, None),
             ('参数校验', 'd', T_WARM, None),
             ('保存入库', 'b', T_GREEN, None),
             ('上架发布', 'b', T_GREEN, None)]
    spans, bottom = f.vflow(items, y0=50, gap=56)
    f.chain_arrows(spans)
    f.text((f.CX + 16, (spans[2][1] + spans[3][0]) / 2 - 9), '通过', F(11.5), INK_SOFT)
    # 不通过分支
    dy0, dy1, _ = spans[3]
    dmid = (dy0 + dy1) / 2
    bx, bw_, bh = 730, 240, 62
    f.hlink(dmid, f.CX + f.DIA_W/2, bx, label='不通过')
    f.box(bx, dmid - bh/2, bw_, bh, '返回修改', tint=T_ROSE, tsize=13.5)
    f.elbow([(bx + bw_/2, dmid - bh/2), (bx + bw_/2, spans[1][0] + 32),
             (f.CX + f.BOX_W/2, spans[1][0] + 32)])
    f.note(f.CX + f.BOX_W/2 + 12, spans[1][0] + 12, '修改后重新提交')
    f.save('fig_m1_content.png')


# ============================================ 3 基础数据维护流程（纵排）
def fig_m2_basedata():
    f = Fig(1000, 700)
    items = [('录入基础数据', 'b', T_ACCENT, '类型 / 国家 / 字典'),
             ('唯一性校验', 'b', T_WARM, '名称与编码查重'),
             ('保存基础数据', 'b', T_WARM, '写入基础数据表'),
             ('业务表引用', 'b', T_GREEN, '内容关联取值')]
    spans, bottom = f.vflow(items, y0=50, gap=52, h=68)
    f.chain_arrows(spans)
    f.note(f.CX - f.BOX_W/2, bottom + 40, '说明：基础数据供内容管理模块引用，修改后即时生效。')
    f.save('fig_m2_basedata.png')


# ============================================ 4 资料上传与存储流程（纵排）
def fig_m3_upload():
    f = Fig(1000, 880)
    items = [('选择本地文件', 'b', T_ACCENT, None),
             ('格式与大小校验', 'd', T_WARM, None),
             ('上传至对象存储', 'b', T_WARM, None),
             ('写入资料记录', 'b', T_WARM, None),
             ('返回文件标识', 'b', T_GREEN, None)]
    spans, bottom = f.vflow(items, y0=50, gap=56)
    f.chain_arrows(spans)
    f.text((f.CX + 16, (spans[0][1] + spans[1][0]) / 2 - 9), '通过', F(11.5), INK_SOFT)
    dy0, dy1, _ = spans[1]
    dmid = (dy0 + dy1) / 2
    bx, bw_, bh = 730, 240, 62
    f.hlink(dmid, f.CX + f.DIA_W/2, bx, label='不通过')
    f.box(bx, dmid - bh/2, bw_, bh, '返回错误提示', tint=T_ROSE, tsize=13.5)
    f.save('fig_m3_upload.png')


# ============================================ 5 角色权限分配流程（纵排）
def fig_m4_role():
    f = Fig(1000, 760)
    items = [('创建角色', 'b', T_ACCENT, None),
             ('勾选菜单与接口权限', 'b', T_ACCENT, None),
             ('保存权限策略', 'b', T_WARM, None),
             ('绑定用户', 'b', T_WARM, None),
             ('权限生效', 'b', T_GREEN, None)]
    spans, bottom = f.vflow(items, y0=50, gap=52, h=68)
    f.chain_arrows(spans)
    f.note(f.CX - f.BOX_W/2, bottom + 44,
           '说明：角色绑定权限策略后，用户重新登录即按新策略校验。')
    f.save('fig_m4_role.png')


# ============================================ 6 登录认证流程（纵排）
def fig_m5_auth():
    f = Fig(1000, 940)
    items = [('①  提交账号与密码', 'b', T_NEUTRAL, '参数非空校验'),
             ('②  校验账号状态', 'b', T_ACCENT, '查询用户记录'),
             ('③  校验密码', 'b', T_ACCENT, '比对密码摘要'),
             ('④  签发访问令牌', 'b', T_WARM, '含有效期与角色信息'),
             ('⑤  后续请求校验', 'b', T_VIOLET, '解析令牌有效性'),
             ('⑥  移交业务处理', 'b', T_NEUTRAL, '注入身份信息')]
    spans, bottom = f.vflow(items, y0=40, gap=46, h=70)
    f.chain_arrows(spans)
    anns = [(1, '失败计数', '连续失败后限制登录'),
            (2, '密码摘要', '不可逆摘要存储'),
            (3, '令牌有效期', '到期需重新登录'),
            (4, '免鉴权白名单', '登录接口不校验令牌')]
    bx, bw_ = 720, 250
    for idx, t, s in anns:
        y0, y1, _ = spans[idx]
        mid = (y0 + y1) / 2
        f.box(bx, mid - 31, bw_, 62, t, sub=s, tint=T_NEUTRAL, tsize=12, ssize=10.5)
        f.hlink(mid, f.CX + f.BOX_W/2, bx)
    f.save('fig_m5_auth.png')


# ======================================= 7 附录1 内容录入与发布流程（纵排）
def fig_a1_content_flow():
    f = Fig(1000, 1000)
    items = [('编辑登录', 'b', T_ACCENT, None),
             ('进入内容管理', 'b', T_ACCENT, None),
             ('新建或编辑剧集', 'b', T_ACCENT, None),
             ('上传视频与字幕', 'b', T_ACCENT, None),
             ('提交校验', 'd', T_WARM, None),
             ('保存并发布', 'b', T_GREEN, None),
             ('前端展示', 'b', T_GREEN, None)]
    spans, bottom = f.vflow(items, y0=46, gap=52, h=64, dh=110)
    f.chain_arrows(spans)
    f.text((f.CX + 16, (spans[3][1] + spans[4][0]) / 2 - 9), '通过', F(11.5), INK_SOFT)
    dy0, dy1, _ = spans[4]
    dmid = (dy0 + dy1) / 2
    bx, bw_, bh = 730, 240, 62
    f.hlink(dmid, f.CX + f.DIA_W/2, bx, label='不通过')
    f.box(bx, dmid - bh/2, bw_, bh, '返回修改', tint=T_ROSE, tsize=13.5)
    f.elbow([(bx + bw_/2, dmid - bh/2), (bx + bw_/2, spans[2][0] + 32),
             (f.CX + f.BOX_W/2, spans[2][0] + 32)])
    f.save('fig_a1_content_flow.png')


# ======================================= 8 附录2 权限校验流程（纵排）
def fig_a2_auth_flow():
    f = Fig(1000, 1000)
    items = [('收到业务请求', 'b', T_ACCENT, None),
             ('令牌是否有效', 'd', T_WARM, None),
             ('查询用户角色', 'b', T_ACCENT, None),
             ('是否为管理员', 'd', T_WARM, None),
             ('校验权限策略', 'b', T_ACCENT, None),
             ('是否具有权限', 'd', T_WARM, None),
             ('执行业务并记录日志', 'b', T_GREEN, None)]
    spans, bottom = f.vflow(items, y0=40, gap=40, h=62, dh=104)
    f.chain_arrows(spans)
    bx, bw_ = 720, 250
    for idx, t, tint, lbl in [(1, '返回未授权', T_ROSE, '否'),
                              (3, '直接放行', T_GREEN, '是'),
                              (5, '返回权限不足', T_ROSE, '否')]:
        y0, y1, _ = spans[idx]
        mid = (y0 + y1) / 2
        f.hlink(mid, f.CX + f.DIA_W/2, bx, label=lbl)
        f.box(bx, mid - 30, bw_, 60, t, tint=tint, tsize=12.5)
    f.save('fig_a2_auth_flow.png')


if __name__ == '__main__':
    fig_arch()
    fig_m1_content()
    fig_m2_basedata()
    fig_m3_upload()
    fig_m4_role()
    fig_m5_auth()
    fig_a1_content_flow()
    fig_a2_auth_flow()
    print('\n->', OUT)
