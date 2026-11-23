# -*- coding: utf-8 -*-
"""
render.py —— Pillow 确定性逐帧渲染器

用法：
    python render.py                 # 渲染全部帧到 frames/
    python render.py --probe 0 1 2   # 只渲染指定秒数的样帧，用于 contact sheet 自检
    python render.py --frames 0 24   # 只渲染前 24 帧，测速用

设计要点（也是这支片子想讲的原理之一）：
  1. frame(t) 是纯函数：输出只取决于 t 与 CONFIG，不读时钟、不用随机、不联网。
     所以 1070 帧可以任意顺序、任意并行地渲染，结果逐像素一致。
  2. 静态层（网格 + 暗角 + 字体）只构建一次，每帧 copy()；动态层才随 t 重算。
  3. glow 在 1/2 分辨率上做 GaussianBlur 再放大 —— 效果更柔、耗时约 1/4。
     科普片里「光晕」是廉价但最出效果的质感来源，别在每帧全尺寸上烧 CPU。
  4. 转场不靠 ffmpeg 滤镜（KeyShot 自带的 ffmpeg 是 --disable-everything 精简版，
     没有 fade/overlay），而是在帧内用两次纯函数渲染做叠化。
  5. 所有几何是等轴测投影 + 多边形，不是真 3D：一张完整的「底层曲面」用放大的
     平行四边形表示，trim loop 用参数化圆投影成椭圆，圆角用参数化弧带表示。
     —— 讲原理的片子要的是「结构一眼可辨」，不是渲染精度。
"""

import os
import sys
import math
import json
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(_HERE, "frames")

# ---------------------------------------------------------------------------
# 字体：中文必须微软雅黑，数字/代码用 Consolas（Windows 自带，无需下载）
# ---------------------------------------------------------------------------
FONTDIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
F_TITLE = os.path.join(FONTDIR, "msyhbd.ttc")
F_BODY = os.path.join(FONTDIR, "msyh.ttc")
F_MONO = os.path.join(FONTDIR, "consolab.ttf")


def hexrgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c1, c2, u):
    """颜色插值，u∈[0,1]"""
    return tuple(int(a + (b - a) * u) for a, b in zip(c1, c2))


def ease(u):
    """easeInOutCubic —— 所有运动的基础缓动，避免线性动画的机械感"""
    u = max(0.0, min(1.0, u))
    return 4 * u * u * u if u < 0.5 else 1 - pow(-2 * u + 2, 3) / 2


def clamp01(u):
    return max(0.0, min(1.0, u))


def ramp(u, a, b):
    """在 [a,b] 区间内 0→1"""
    return clamp01((u - a) / max(1e-6, b - a))


def ease_out_back(u):
    """标题弹入：轻微过冲，Claude 科普片最常见的「有手感」来源"""
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * pow(u - 1, 3) + c1 * pow(u - 1, 2)


THEMES = {
    "manim-dark": {},
    "tech-glow": {
        "ground": "#101426", "grid": "#262B47", "vignette": "#080A14",
        "glow": "#5B4BD6", "surface": "#69D2FF",
    },
    "light": {
        "ground": "#F2F3F6", "grid": "#DCDCE4",
        "vignette": "#E7E9EE", "text": "#1B1E26", "muted": "#5A6070",
        "line": "#7A8190", "glow": "#D9E2F2",
    },
}


class Renderer:
    def __init__(self, cfg=None):
        self.cfg = dict(SB.CONFIG if cfg is None else cfg)
        self.W, self.H = self.cfg["width"], self.cfg["height"]
        self.pal = dict(SB.PALETTE)
        self.pal.update(THEMES.get(self.cfg["theme"], {}))
        self.fonts = {
            "title": ImageFont.truetype(F_TITLE, 58),
            "sub": ImageFont.truetype(F_BODY, 29),
            "body": ImageFont.truetype(F_BODY, 26),
            "small": ImageFont.truetype(F_BODY, 21),
            "num": ImageFont.truetype(F_MONO, 40),
            "tag": ImageFont.truetype(F_MONO, 22),
            "code": ImageFont.truetype(F_MONO, 23),
            "huge": ImageFont.truetype(F_TITLE, 74),
            # Consolas 没有中文字形：任何含中文的「等宽位置」都要切雅黑，
            # 否则渲染成方块（第一轮样帧实测到的 bug）。
            "cjk_tag": ImageFont.truetype(F_BODY, 21),
            "cjk_code": ImageFont.truetype(F_BODY, 22),
        }
        self.base = self._build_base()
        self.fade = 0.38  # 叠化时长（秒）

    # ---------------- 静态层 ----------------
    def _build_base(self):
        W, H, p = self.W, self.H, self.pal
        img = Image.new("RGBA", (W, H), hexrgb(p["ground"]))
        d = ImageDraw.Draw(img, "RGBA")

        # 细网格：间距 64px，1px，极低对比 —— 给画面一个「坐标感」但不抢主体
        step = 64
        for x in range(0, W, step):
            d.line([(x, 0), (x, H)], fill=hexrgb(p["grid"], 90), width=1)
        for y in range(0, H, step):
            d.line([(0, y), (W, y)], fill=hexrgb(p["grid"], 90), width=1)

        # 两粒冷光斑：确定性位置（seed 参与公式，不用随机）
        s = self.cfg["seed"]
        blobs = [
            (int(W * (0.16 + 0.02 * math.sin(s * 0.001))), int(H * 0.22), 320, 0.16),
            (int(W * 0.84), int(H * (0.74 + 0.02 * math.cos(s * 0.001))), 400, 0.11),
        ]
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow, "RGBA")
        for cx, cy, r, alpha in blobs:
            gd.ellipse([cx - r, cy - r, cx + r, cy + r],
                       fill=hexrgb(p["glow"], int(255 * alpha)))
        glow = self._soft(glow, 90)
        img = Image.alpha_composite(img, glow)

        # 暗角：四边压暗，把视线收拢到中间
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vig, "RGBA")
        edge = 130
        for i in range(edge):
            a = int(70 * (1 - i / edge) ** 2)
            vd.rectangle([i, i, W - i, H - i], outline=hexrgb(p["vignette"], a), width=1)
        img = Image.alpha_composite(img, vig)
        return img

    def _soft(self, layer, radius):
        """半分辨率模糊再放大：glow 的性能/质感平衡"""
        w, h = layer.size
        small = layer.resize((max(1, w // 2), max(1, h // 2)), Image.Resampling.LANCZOS)
        small = small.filter(ImageFilter.GaussianBlur(radius / 2))
        return small.resize((w, h), Image.Resampling.LANCZOS)

    # ---------------- 等轴测投影 ----------------
    def proj(self, pt, cx=None, cy=None, scale=5.2, yaw=None):
        """3D → 2D。标准等轴测：u=(x-y)cos30°, v=(x+y)sin30° - z
        yaw 让盒子缓慢转起来（依赖传入的数值，不读系统时间）。"""
        x, y, z = pt
        if yaw is None:
            yaw = self.cfg["iso_yaw"]
        x1 = x * math.cos(yaw) - y * math.sin(yaw)
        y1 = x * math.sin(yaw) + y * math.cos(yaw)
        u = (x1 - y1) * 0.8660254
        v = (x1 + y1) * 0.5 - z
        if cx is None:
            cx = self.W * 0.63
        if cy is None:
            cy = self.H * 0.46
        return (cx + scale * u, cy + scale * v)

    def poly(self, d, pts3, fill=None, outline=None, width=2, **kw):
        kw = {k: v for k, v in kw.items() if v is not None}
        xy = [self.proj(p, **kw) for p in pts3]
        if fill is not None:
            d.polygon(xy, fill=fill)
        if outline is not None:
            d.line(xy + [xy[0]], fill=outline, width=width, joint="curve")

    def dashed(self, d, a3, b3, color, width=2, dash=11, gap=7, **kw):
        """屏幕空间虚线：Pillow 没有原生虚线，按弧长切段实现。
        底层曲面用虚线，才能一眼读成「一张底图」而不是另一个盒子。"""
        x0, y0 = self.proj(a3, **kw)
        x1, y1 = self.proj(b3, **kw)
        ln = math.hypot(x1 - x0, y1 - y0)
        if ln < 1e-6:
            return
        ux, uy = (x1 - x0) / ln, (y1 - y0) / ln
        s = 0.0
        while s < ln:
            e = min(ln, s + dash)
            d.line([(x0 + ux * s, y0 + uy * s),
                    (x0 + ux * e, y0 + uy * e)], fill=color, width=width)
            s = e + gap

    # ---------------- 几何基元 ----------------
    @staticmethod
    def box_points(L=45, Wd=32, H=24):
        return [(-L, -Wd, 0), (L, -Wd, 0), (L, Wd, 0), (-L, Wd, 0),
                (-L, -Wd, H), (L, -Wd, H), (L, Wd, H), (-L, Wd, H)]

    def draw_box(self, d, p, alpha=255, show_iso=True, yaw=None):
        """画盒子：三可见面 + 棱线。fill 用低 alpha 保持「透光的示意图」质感"""
        B = self.box_points()
        top = [B[4], B[5], B[6], B[7]]
        front = [B[0], B[1], B[5], B[4]]
        right = [B[1], B[2], B[6], B[5]]
        surf = hexrgb(p["surface"], int(alpha * 0.16))
        side = hexrgb(p["surface"], int(alpha * 0.09))
        line = hexrgb(p["line"], int(alpha * 0.85))
        self.poly(d, front, fill=side, outline=line, width=2, yaw=yaw)
        self.poly(d, right, fill=side, outline=line, width=2, yaw=yaw)
        self.poly(d, top, fill=surf, outline=line, width=2, yaw=yaw)

        # 等参线：★ 用户明确反馈「结构线太密要降密度，而不是全隐藏」
        # 所以这里下限是 2，滑块不可能把它关成 0。
        if show_iso:
            n = max(2, int(self.cfg["isoline_density"]))
            iso = hexrgb(p["surface"], int(alpha * 0.16))
            for i in range(1, n):
                f = i / n
                x = -45 + 90 * f
                self.poly(d, [(x, -32, 24), (x, 32, 24)],
                          outline=iso, width=1, yaw=yaw)
                yy = -32 + 64 * f
                self.poly(d, [(-45, yy, 24), (45, yy, 24)],
                          outline=iso, width=1, yaw=yaw)

    def draw_underlying_surface(self, d, p, alpha=255):
        """一张比盒子大的完整平面 = UnderlyingSurface 的可视化。
        它先出现，再让盒子「被裁」出来，是第 1 镜的核心证据。"""
        big = [(-78, -60, 24), (78, -60, 24), (78, 60, 24), (-78, 60, 24)]
        # 底层曲面要比盒子「更虚」：填充极淡、边框更亮，否则两层糊成一片
        self.poly(d, big, fill=hexrgb(p["surface"], int(alpha * 0.045)))
        edge = hexrgb(p["surface"], int(alpha * 0.80))
        for i in range(4):
            self.dashed(d, big[i], big[(i + 1) % 4], edge, width=2)
        n = max(2, int(self.cfg["isoline_density"]))
        iso = hexrgb(p["surface"], int(alpha * 0.14))
        for i in range(1, n):
            f = i / n
            x = -78 + 156 * f
            self.poly(d, [(x, -60, 24), (x, 60, 24)], outline=iso, width=1)
            yy = -60 + 120 * f
            self.poly(d, [(-78, yy, 24), (78, yy, 24)], outline=iso, width=1)

    def draw_hole(self, d, p, cxy, r, ring_color, alpha=255, ring_w=4,
                  hole_wall=True, shrink=1.0):
        """孔 = 底层曲面上的一个 inner loop。
        shrink 从 1→0 就是「删掉这个环，孔自己合上」的动画。"""
        cx, cy = cxy
        rr = max(0.001, r * shrink)
        pts = [(cx + rr * math.cos(2 * math.pi * i / 64),
                cy + rr * math.sin(2 * math.pi * i / 64), 24) for i in range(64)]
        xy = [self.proj(q) for q in pts]
        d.polygon(xy, fill=hexrgb(p["ground"], int(alpha * 0.94)))
        if hole_wall and shrink > 0.02:
            wall = hexrgb(p["surface"], int(alpha * 0.52))
            n = max(2, int(self.cfg["isoline_density"]))
            for i in range(0, n):
                a = 2 * math.pi * i / n
                q0 = (cx + rr * math.cos(a), cy + rr * math.sin(a), 24)
                q1 = (cx + rr * math.cos(a), cy + rr * math.sin(a), 0)
                self.poly(d, [q0, q1], outline=wall, width=1)
        d.line(xy + [xy[0]], fill=hexrgb(ring_color, alpha), width=ring_w, joint="curve")
        # 环上的发光点：让「环」被看成一条独立的边界，而不是一个色块
        if shrink > 0.05:
            q = (cx + rr, cy, 24)
            px, py = self.proj(q)
            d.ellipse([px - 5, py - 5, px + 5, py + 5],
                      fill=hexrgb(p["accent"], alpha))

    def draw_fillet_band(self, d, p, radius, alpha=255, lift=0.0):
        """圆角 = 滚球扫出的一整圈新增过渡曲面。
        用 4 条参数化弧带表示；lift 让整圈「剥离」飞出去一点。"""
        R = radius
        edges = [
            ((-45, -32), (45, -32), (0, 1)),   # y=-32 边，向内 +y
            ((45, -32), (45, 32), (-1, 0)),
            ((45, 32), (-45, 32), (0, -1)),
            ((-45, 32), (-45, -32), (1, 0)),
        ]
        feat = hexrgb(p["feature"], int(alpha * 0.34))
        edge_c = hexrgb(p["feature"], alpha)
        for (a, b, inward) in edges:
            outer, inner = [], []
            for i in range(25):
                f = i / 24
                x = a[0] + (b[0] - a[0]) * f
                y = a[1] + (b[1] - a[1]) * f
                z = 24 + lift
                outer.append((x, y, z))
                # 截面用「顶面边 → 内缩 R / 下沉 0.72R」两点近似：
                # 讲原理要的是轮廓一眼可辨，不是精确滚球扫掠面
                inner.append((x + inward[0] * R,
                              y + inward[1] * R,
                              z - R * 0.72 + lift))
            self.poly(d, outer + list(reversed(inner)), fill=feat,
                      outline=None, width=1)
            self.poly(d, outer, outline=edge_c, width=3)
            self.poly(d, inner, outline=hexrgb(p["feature"], int(alpha * 0.7)), width=2)

    @staticmethod
    def _has_cjk(s):
        return any(ord(ch) > 0x2E80 for ch in s)

    def label(self, d, xy, text, color, font="tag", anchor="mm", a=255):
        f = self.fonts[font]
        if font in ("tag", "code", "num") and self._has_cjk(text):
            f = self.fonts["cjk_" + font]
        d.text(xy, text, font=f, fill=hexrgb(color, a), anchor=anchor)

    # ---------------- 各镜几何 ----------------
    def geometry(self, beat, u, t):
        """返回一张 RGBA 几何层。纯函数：只依赖 (beat, u, t, CONFIG)。"""
        p = self.pal
        layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer, "RGBA")
        sc = beat["scene"]

        if sc == "title":
            # 缓慢自转的小线框盒放在右下：yaw 由 t 决定（纯函数允许依赖 t），
            # 位置/缩放单独给，避免压住居中的超大标题。
            yaw = self.cfg["iso_yaw"] + 0.55 * math.sin(t * 0.55)
            a = int(255 * ease(ramp(u, 0.05, 0.45)))
            B = self.box_points()
            edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7),
                     (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
            kw = dict(cx=self.W * 0.78, cy=self.H * 0.68,
                      scale=2.45, yaw=yaw)
            for i, j in edges:
                a0, b0 = self.proj(B[i], **kw), self.proj(B[j], **kw)
                d.line([a0, b0], fill=hexrgb(p["line"], int(a * 0.75)), width=2)
            # 两个光点暗示「两种形状」
            q = self.proj((0, 0, 24), **kw)
            for i, col in enumerate([p["surface"], p["feature"]]):
                x = q[0] + (i * 2 - 1) * 62
                y = q[1] + 18 * math.sin(t * 1.2 + i)
                d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=hexrgb(col, a))

        elif sc == "two_layers":
            a = int(255 * ease(ramp(u, 0.0, 0.30)))
            self.draw_underlying_surface(d, p, alpha=a)
            # 完整平面先独立存在，随后盒子轮廓「被裁」出来
            k = ease(ramp(u, 0.32, 0.72))
            self.draw_box(d, p, alpha=int(a * (0.35 + 0.65 * k)))
            if k > 0.05 and self.cfg["show_labels"]:
                q = self.proj((0, 0, 24))
                self.label(d, (q[0], q[1] - 66), "UnderlyingSurface",
                           p["surface"], "tag")
            # 最后浮出 trim loop
            if u > 0.58:
                self.draw_hole(d, p, (0, 0), 10,
                               p["feature"], alpha=int(255 * ease(ramp(u, 0.58, 0.82))),
                               hole_wall=False)
                if self.cfg["show_labels"]:
                    q = self.proj((0, 0, 24))
                    self.label(d, (q[0] + 132, q[1] + 8), "trim loop",
                               p["feature"], "tag")

        elif sc == "hole_untrim":
            a = int(255 * ease(ramp(u, 0.0, 0.22)))
            self.draw_underlying_surface(d, p, alpha=max(0, a - 90))
            self.draw_box(d, p, alpha=a)
            # 环在 0.42→0.78 收缩到 0 = 删掉 inner loop
            shrink = 1.0 - ease(ramp(u, 0.42, 0.78))
            self.draw_hole(d, p, (0, 0), 10, p["feature"], alpha=a, shrink=shrink)
            if shrink < 0.12 and self.cfg["show_labels"]:
                q = self.proj((0, 0, 24))
                self.label(d, (q[0], q[1] - 54), "孔闭合 / hole closed",
                           p["good"], "tag")

        elif sc == "selective_holes":
            a = int(255 * ease(ramp(u, 0.0, 0.20)))
            self.draw_box(d, p, alpha=a)
            s1 = 1.0 - ease(ramp(u, 0.46, 0.76))   # H1 被删
            self.draw_hole(d, p, (-24, 0), 10, p["feature"], alpha=a, shrink=s1)
            self.draw_hole(d, p, (24, 0), 10, p["line"], alpha=a, shrink=1.0)
            if self.cfg["show_labels"]:
                for i, (x, s) in enumerate([(-24, "H1 [7,8]"), (24, "H2 保留")]):
                    q = self.proj((x, 0, 24))
                    col = p["accent"] if i == 0 else p["muted"]
                    self.label(d, (q[0], q[1] - 58), s, col, "tag")
                # H1 选中框
                q = self.proj((-24, 0, 24))
                d.rectangle([q[0] - 68, q[1] - 42, q[0] + 68, q[1] + 42],
                            outline=hexrgb(p["accent"], a), width=2)

        elif sc == "fillet":
            a = int(255 * ease(ramp(u, 0.0, 0.22)))
            self.draw_box(d, p, alpha=a, show_iso=False)
            R = self.cfg["fillet_radius"]
            grow = ease(ramp(u, 0.18, 0.52))
            lift = 26 * ease(ramp(u, 0.62, 0.92))
            self.draw_fillet_band(d, p, R * max(0.08, grow), alpha=a, lift=lift)
            # 「untrim 失败」：红叉 + null。放在 3D 主体右外侧的空白区，
            # 不要压在橙带或左上说明文字上（第一版样帧实测压住了）。
            if u > 0.52:
                k = ease(ramp(u, 0.52, 0.68))
                x, y = 1330, 236
                d.line([(x - 18, y - 18), (x + 18, y + 18)],
                       fill=hexrgb(p["bad"], int(255 * k)), width=5)
                d.line([(x - 18, y + 18), (x + 18, y - 18)],
                       fill=hexrgb(p["bad"], int(255 * k)), width=5)
                if self.cfg["show_labels"]:
                    # 拆两行：单行宽约 340px 会顶到橙带，拆开后左端有安全距离
                    self.label(d, (x, y + 56), "UntrimOuterLoop", p["bad"], "tag")
                    self.label(d, (x, y + 88), "→ null", p["bad"], "tag")
            if self.cfg["show_labels"] and u < 0.55:
                q = self.proj((0, 0, 24))
                self.label(d, (q[0], q[1] + 96),
                           "新增过渡面 R=%.1f" % R, p["feature"], "tag")

        elif sc == "independence":
            a = int(255 * ease(ramp(u, 0.0, 0.20)))
            self.draw_box(d, p, alpha=a, show_iso=False)
            R = self.cfg["fillet_radius"]
            self.draw_fillet_band(d, p, R, alpha=a)   # 圆角全程不动
            # 环收缩放慢：让「孔还在消失中」这个中间态被看见，而不是一闪就没
            shrink = 1.0 - ease(ramp(u, 0.45, 0.85))
            self.draw_hole(d, p, (0, 0), 10, p["accent"], alpha=a, shrink=shrink)
            if self.cfg["show_labels"]:
                q = self.proj((0, 0, 24))
                self.label(d, (q[0] - 250, q[1] + 6),
                           "4 组圆角面 完好", p["feature"], "tag", anchor="rm")
                if shrink < 0.55:
                    self.label(d, (q[0] - 232, q[1] + 60),
                               "= 纯圆角盒", p["good"], "tag", anchor="rm")

        elif sc == "conclusion":
            # 不画 3D，改画对照卡片：左「孔」右「圆角」，中线分隔
            a = int(255 * ease(ramp(u, 0.0, 0.28)))
            d.rounded_rectangle([150, 190, 760, 570], radius=18,
                                fill=hexrgb(p["surface"], int(a * 0.09)),
                                outline=hexrgb(p["surface"], int(a * 0.65)), width=2)
            d.rounded_rectangle([840, 190, 1450, 570], radius=18,
                                fill=hexrgb(p["feature"], int(a * 0.09)),
                                outline=hexrgb(p["feature"], int(a * 0.65)), width=2)
            d.line([(800, 210), (800, 550)], fill=hexrgb(p["line"], int(a * 0.5)), width=2)
            self.label(d, (455, 250), "孔 / HOLE", p["surface"], "body")
            self.label(d, (1145, 250), "圆角 / FILLET", p["feature"], "body")
            self.label(d, (455, 330), "裁剪环 inner loop", p["text"], "body")
            self.label(d, (1145, 330), "新增过渡曲面", p["text"], "body")
            self.label(d, (455, 390), "可抹 → RemoveHoles", p["good"], "body")
            self.label(d, (1145, 390), "须重缝 → CreateSolid", p["bad"], "body")
            self.label(d, (455, 470), "模块 B 去除布尔切割", p["surface"], "body")
            self.label(d, (1145, 470), "模块 A 去除圆角", p["feature"], "body")
            if u > 0.62:
                k = ease(ramp(u, 0.62, 0.82))
                self.label(d, (800, 620), "互不依赖 · 任意顺序 · 没有总开关",
                           p["accent"], "sub")

        elif sc == "outro":
            # 代码感：等宽字体逐行「打字」
            code = [
                "def frame(t):",
                "    beat, u, t0 = beat_at(t)",
                "    return render_beat(beat, u, t)   # 纯函数",
                "",
                "# 不读时钟 · 不用随机 · 不联网",
                "# 改一句字幕 = diff + 重渲染",
            ]
            for i, ln in enumerate(code):
                k = ease(ramp(u, 0.08 + i * 0.085, 0.20 + i * 0.085))
                if k <= 0:
                    continue
                shown = ln[:max(0, int(len(ln) * k))]
                self.label(d, (150, 210 + i * 52), shown,
                           p["surface"] if i < 3 else p["muted"],
                           "code", anchor="la", a=255)
            if u > 0.72:
                d.rounded_rectangle([150, 560, 1450, 640], radius=12,
                                    fill=hexrgb(p["surface"], 22),
                                    outline=hexrgb(p["surface"], 110), width=1)
                self.label(d, (800, 600),
                           "storyboard.py  →  render.py  →  encode.py  →  preview.html",
                           p["text"], "code")

        # 光晕层：半分辨率模糊一次就够，叠 0.42 保持主体线条不发虚
        glow = self._soft(layer, 9)
        layer = Image.alpha_composite(layer, Image.blend(
            Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0)), glow, 0.42))
        return layer

    # ---------------- 字幕 / 数字 / HUD ----------------
    def captions(self, img, beat, u):
        p = self.pal
        d = ImageDraw.Draw(img, "RGBA")
        # 每个镜头的字幕自带淡入；末尾 0.12 淡出，避免叠化时两层字打架
        a = int(255 * ease(ramp(u, 0.02, 0.20)) * (1 - ease(ramp(u, 0.90, 1.0))))
        if a <= 0:
            return
        title = beat.get("title", "")
        sub = beat.get("sub", "")

        # 左上：逐条出现的说明行
        # 对照卡片 / 片尾代码本身就是说明，别再叠一层左上文字造成打架
        lines = ([] if beat["scene"] in ("conclusion", "outro")
                 else beat.get("lines", []))
        for i, ln in enumerate(lines):
            k = ease(ramp(u, 0.16 + i * 0.10, 0.34 + i * 0.10))
            if k <= 0:
                continue
            la = int(a * k)
            y = 132 + i * 46
            d.ellipse([92, y + 9, 100, y + 17], fill=hexrgb(p["accent"], la))
            d.text((116, y), ln, font=self.fonts["body"], fill=hexrgb(p["muted"], la))

        # 底部：标题 + 副标题。片头已有居中大标题，不再重复一遍
        if beat["scene"] != "title":
            ty = self.H - 168
            d.text((92, ty), title, font=self.fonts["title"],
                   fill=hexrgb(p["text"], a), anchor="la")
            d.text((94, ty + 76), sub, font=self.fonts["sub"],
                   fill=hexrgb(p["muted"], a), anchor="la")
            # 标题左侧的短竖条：Claude 科普片常见的「节拍标记」
            d.rounded_rectangle([62, ty + 4, 72, ty + 58], radius=5,
                                fill=hexrgb(p["accent"], a))

        # 右下：数字滚动上屏
        metrics = beat.get("metrics", [])
        if metrics and self.cfg["show_labels"]:
            mk = ease(ramp(u, 0.34, 0.80))
            for i, (lab, v0, v1, dec) in enumerate(metrics):
                val = v0 + (v1 - v0) * mk
                txt = ("%." + str(dec) + "f") % val
                # 数字放右上角：3D 主体已移到中右偏下，顶部这条带子正好空出来
                y = 112 + i * 96
                d.text((1510, y), txt, font=self.fonts["num"],
                       fill=hexrgb(p["good"] if i == 0 else p["accent"], a),
                       anchor="ra")
                self.label(d, (1510, y + 46), lab, p["muted"], "tag",
                           anchor="ra", a=a)

        # 片头专属：超大标题压在中间
        if beat["scene"] == "title":
            k = ease_out_back(clamp01(ramp(u, 0.06, 0.42)))
            ta = int(255 * clamp01(ramp(u, 0.06, 0.30)))
            cx = self.W * 0.5
            cy = 300 + (1 - k) * 46
            d.text((cx, cy), title, font=self.fonts["huge"],
                   fill=hexrgb(p["text"], ta), anchor="mm")
            d.text((cx, cy + 92), sub, font=self.fonts["sub"],
                   fill=hexrgb(p["accent"], ta), anchor="mm")
            self.label(d, (cx, cy + 150), beat.get("note", ""),
                       p["muted"], "tag", anchor="mm", a=ta)
        if beat["scene"] == "outro":
            d.text((92, self.H - 168), title, font=self.fonts["title"],
                   fill=hexrgb(p["text"], a), anchor="la")

    def hud(self, img, t, beat):
        p = self.pal
        d = ImageDraw.Draw(img, "RGBA")
        # 顶部进度条：按镜头分段，让「看到第几节」一目了然
        x0, x1, y = 92, self.W - 92, 44
        d.line([(x0, y), (x1, y)], fill=hexrgb(p["grid"], 200), width=3)
        dur = SB.TOTAL_DURATION
        for bid, a, b in SB.cumulative_starts():
            xa = x0 + (x1 - x0) * a / dur
            xb = x0 + (x1 - x0) * b / dur
            col = p["accent"] if bid == beat["id"] else p["line"]
            d.line([(xa, y), (xb - 4, y)],
                   fill=hexrgb(col, 235 if bid == beat["id"] else 110), width=3)
        xp = x0 + (x1 - x0) * clamp01(t / dur)
        d.ellipse([xp - 7, y - 7, xp + 7, y + 7], fill=hexrgb(p["accent"], 255))
        d.text((x0, 18), "B-REP / FEATURE CANCELLATION", font=self.fonts["tag"],
               fill=hexrgb(p["muted"], 200), anchor="la")
        d.text((x1, 18), "%02d / %02d   %.1fs" %
               (beat["id"] + 1, len(SB.BEATS), t),
               font=self.fonts["tag"], fill=hexrgb(p["muted"], 200), anchor="ra")

    # ---------------- frame(t) ----------------
    def frame(self, t):
        """★ 纯函数：输出只取决于 t 与 CONFIG。"""
        beat, u, t0 = SB.beat_at(t)
        geom = self.geometry(beat, u, t)

        # 叠化：镜头开头 fade 秒内，与上一镜的末帧做 alpha 混合。
        # 两次调用都是纯函数，所以整支片子仍然可以乱序 / 并行渲染。
        if beat["id"] > 0 and (t - t0) < self.fade:
            prev = SB.BEATS[beat["id"] - 1]
            geom_prev = self.geometry(prev, 1.0, t0 - 0.001)
            geom = Image.blend(geom_prev, geom, ease((t - t0) / self.fade))

        img = Image.alpha_composite(self.base.copy(), geom)
        self.captions(img, beat, u)
        self.hud(img, t, beat)
        return img.convert("RGB")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", nargs="*", type=float, default=None,
                    help="只渲染这些秒数的样帧")
    ap.add_argument("--frames", nargs=2, type=int, default=None,
                    help="只渲染帧区间 [a,b)")
    ap.add_argument("--out", default=FRAMES)
    ap.add_argument("--scale", type=float, default=1.0,
                    help="输出缩放（0.5 可快速出小样）")
    args = ap.parse_args()

    cfg = dict(SB.CONFIG)
    if args.scale != 1.0:
        cfg["width"] = int(cfg["width"] * args.scale)
        cfg["height"] = int(cfg["height"] * args.scale)
    r = Renderer(cfg)
    os.makedirs(args.out, exist_ok=True)
    fps = cfg["fps"]

    if args.probe is not None:
        times = args.probe
        for t in times:
            img = r.frame(t)
            img.save(os.path.join(args.out, "probe_%05.1f.png" % t))
            print("PROBE t=%.2f -> probe_%05.1f.png" % (t, t))
        print("PROBE_DONE", len(times))
        return

    total = int(SB.TOTAL_DURATION * fps)
    lo, hi = (args.frames if args.frames else (0, total))
    for i in range(lo, hi):
        t = i / fps
        img = r.frame(t)
        img.save(os.path.join(args.out, "%05d.png" % i), compress_level=1)
        if i % 120 == 0 or i == hi - 1:
            print("FRAME %d / %d  t=%.2fs" % (i, hi, t), flush=True)
    print("RENDER_DONE %d frames  total=%.2fs  size=%dx%d" %
          (hi - lo, SB.TOTAL_DURATION, cfg["width"], cfg["height"]))


if __name__ == "__main__":
    main()
