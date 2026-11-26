# -*- coding: utf-8 -*-
"""
render.py —— 004「基准面」的 Pillow 确定性逐帧渲染器

用法：
    python render.py --probe 0 2 4 8    # 样帧自检
    python render.py                    # 全片 1500 帧 @1920x1080

设计要点（沿用 002，几何全换）：
  1. frame(t) 是纯函数：只依赖 t / CONFIG / storyboard，不读时钟、不用随机、不联网。
  2. 静态层（网格 + 光斑 + 暗角）构建一次，每帧 copy()。
  3. 几何是等轴测投影 + 多边形 / 2D UI 面板，讲空间逻辑不追求像素级软件还原。
  4. 转场在帧内做叠化，不依赖 ffmpeg 滤镜。
  5. 基准面棕 #B08246 来自插件 RGB(176,132,70)，画面与插件配色一致。
"""

import os
import math
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import storyboard as SB
import primitives as PR

_HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(_HERE, "frames")
FONTDIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
F_TITLE = os.path.join(FONTDIR, "msyhbd.ttc")
F_BODY = os.path.join(FONTDIR, "msyh.ttc")
F_MONO = os.path.join(FONTDIR, "consolab.ttf")

THEMES = {}   # 只用 manim-dark；保留入口以便换主题


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def hexrgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c1, c2, u):
    return tuple(int(a + (b - a) * u) for a, b in zip(c1, c2))


def clamp01(u):
    return max(0.0, min(1.0, u))


def ease(u):
    u = clamp01(u)
    return u * u * (3 - 2 * u)


def ramp(u, a, b):
    return clamp01((u - a) / (b - a))


def ease_out_back(u):
    u = clamp01(u)
    c = 1.70158
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


class Renderer:
    # ---- 委托给 primitives.py 的工具（基元函数通过 r.xxx 调用）----
    def rgba(self, color, a=255):
        return hexrgb(color, a)

    def ease(self, u):
        return ease(u)

    def ramp(self, u, a, b):
        return ramp(u, a, b)

    def __init__(self, cfg=None):
        self.cfg = dict(SB.CONFIG if cfg is None else cfg)
        self.W, self.H = self.cfg["width"], self.cfg["height"]
        self.pal = dict(SB.PALETTE)
        self.pal.update(THEMES.get(self.cfg["theme"], {}))
        # 字号按 1080p 放大（相对 002 的 1600x900 约 1.2×）
        k = self.H / 900.0
        f = lambda path, sz: ImageFont.truetype(path, int(sz * k))
        self.fonts = {
            "title": f(F_TITLE, 58), "sub": f(F_BODY, 29),
            "body": f(F_BODY, 26), "small": f(F_BODY, 21),
            "num": f(F_MONO, 40), "tag": f(F_MONO, 22),
            "code": f(F_MONO, 23), "huge": f(F_TITLE, 74),
            "cjk_tag": f(F_BODY, 21), "cjk_code": f(F_BODY, 22),
        }
        self.base = self._build_base()
        self.fade = 0.38

    # ---------------- 静态层 ----------------
    def _build_base(self):
        W, H, p = self.W, self.H, self.pal
        img = Image.new("RGBA", (W, H), hexrgb(p["ground"]))
        d = ImageDraw.Draw(img, "RGBA")
        step = int(64 * H / 900)
        for x in range(0, W, step):
            d.line([(x, 0), (x, H)], fill=hexrgb(p["grid"], 130), width=1)
        for y in range(0, H, step):
            d.line([(0, y), (W, y)], fill=hexrgb(p["grid"], 130), width=1)
        s = self.cfg["seed"]
        blobs = [
            (int(W * (0.16 + 0.02 * math.sin(s * 0.001))), int(H * 0.22),
             int(320 * H / 900), 0.16),
            (int(W * 0.84), int(H * (0.74 + 0.02 * math.cos(s * 0.001))),
             int(400 * H / 900), 0.11),
        ]
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow, "RGBA")
        for cx, cy, r, alpha in blobs:
            gd.ellipse([cx - r, cy - r, cx + r, cy + r],
                       fill=hexrgb(p["glow"], int(255 * alpha)))
        img = Image.alpha_composite(img, self._soft(glow, 90))
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vig, "RGBA")
        edge = 130
        for i in range(edge):
            a = int(52 * (1 - i / edge) ** 2)   # v3 暗角减弱，别把棕面压进黑里
            vd.rectangle([i, i, W - i, H - i], outline=hexrgb(p["vignette"], a), width=1)
        return Image.alpha_composite(img, vig)

    def _soft(self, layer, radius):
        w, h = layer.size
        small = layer.resize((max(1, w // 2), max(1, h // 2)), Image.Resampling.LANCZOS)
        small = small.filter(ImageFilter.GaussianBlur(radius / 2))
        return small.resize((w, h), Image.Resampling.LANCZOS)

    # ---------------- 等轴测投影 ----------------
    def proj(self, pt, cx=None, cy=None, scale=None, yaw=None):
        x, y, z = pt
        if yaw is None:
            yaw = self.cfg["iso_yaw"]
        if scale is None:
            scale = 6.8 * self.H / 900   # v3 几何整体放大 ~1.31×（v2 构图偏空）
        x1 = x * math.cos(yaw) - y * math.sin(yaw)
        y1 = x * math.sin(yaw) + y * math.cos(yaw)
        u = (x1 - y1) * 0.8660254
        v = (x1 + y1) * 0.5 - z
        if cx is None:
            cx = self.W * 0.62
        if cy is None:
            cy = self.H * 0.46
        return (cx + scale * u, cy + scale * v)

    def poly(self, d, pts3, fill=None, outline=None, width=2, **kw):
        kw = {k: v for k, v in kw.items() if v is not None}
        xy = [self.proj(q, **kw) for q in pts3]
        # ★ 坑（v3 真机踩到）：PIL 的 ImageDraw 在 RGBA 上**不做 alpha 混合**，
        # 而是直接写像素。fill=(r,g,b,0) 会把已有内容「擦成透明」。
        # 所以 alpha<=0 一律跳过，不能交给 polygon/line 去画。
        if fill is not None and fill[3] > 0:
            d.polygon(xy, fill=fill)
        if outline is not None and outline[3] > 0:
            d.line(xy + [xy[0]], fill=outline, width=width, joint="curve")

    def dashed(self, d, a3, b3, color, width=2, dash=13, gap=9, **kw):
        if color[3] <= 0:      # 同 poly：alpha=0 会擦除已有像素
            return
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

    def label(self, d, xy, text, color, font="tag", anchor="mm", a=255):
        if a <= 0:
            return
        f = self.fonts[font]
        if font in ("tag", "code", "num") and any(ord(c) > 0x2E80 for c in text):
            f = self.fonts["cjk_" + font]
        d.text(xy, text, font=f, fill=hexrgb(color, a), anchor=anchor)

    # ---------------- 基准面几何基元 ----------------
    def slanted_plate(self, d, p, alpha=255, tilt=0.55, yaw=None, **loc):
        return PR.slanted_plate(self, d, p, alpha=alpha, tilt=tilt, yaw=yaw, **loc)

    def datum_plane(self, d, p, alpha=255, tilt=0.55, yaw=None,
                    fill_alpha=0.22, edge_alpha=0.95, grid=False, **loc):
        return PR.datum_plane(self, d, p, alpha=alpha, tilt=tilt, yaw=yaw,
                              fill_alpha=fill_alpha, edge_alpha=edge_alpha,
                              grid=grid, **loc)

    def gumball(self, d, p, alpha=255, aligned=True, yaw=None):
        return PR.gumball(self, d, p, alpha=alpha, aligned=aligned, yaw=yaw)

    def layer_panel(self, d, p, x, y, w, h, alpha=255,
                    eyes=(True, False, False), locks=(False, True, True),
                    highlight=-1, u=1.0, stagger=False):
        return PR.layer_panel(self, d, p, x, y, w, h, alpha=alpha,
                              eyes=eyes, locks=locks, highlight=highlight,
                              u=u, stagger=stagger)

    def split_view(self, d, p, u, alpha=255):
        return PR.split_view(self, d, p, u, alpha=alpha)

    def alias_compare(self, d, p, u, alpha=255):
        return PR.alias_compare(self, d, p, u, alpha=alpha)


    # ---------------- 各镜几何 ----------------
    def geometry(self, beat, u, t):
        p = self.pal
        layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer, "RGBA")
        sc = beat["scene"]
        yaw = self.cfg["iso_yaw"] + 0.28 * math.sin(t * 0.42)

        if sc == "title":
            a = int(255 * ease(ramp(u, 0.05, 0.45)))
            # v3：几何移到中右并放大，与上方标题形成从文字到几何的对角引导线；
            # 棕面填充提到 0.66，修「主角在画面里等于不存在」。
            kw = dict(cx=self.W * 0.68, cy=self.H * 0.60,
                      scale=4.9 * self.H / 900)
            self.slanted_plate(d, p, alpha=a, yaw=yaw, **kw)
            k = ease(ramp(u, 0.22, 0.70))
            self.datum_plane(d, p, alpha=int(255 * k), yaw=yaw,
                             fill_alpha=0.66 * k, edge_alpha=k, **kw)
            q = self.proj((0, 0, 0), **kw)
            d.ellipse([q[0] - 10, q[1] - 10, q[0] + 10, q[1] + 10],
                      fill=hexrgb(p["accent"], a))

        elif sc == "pain":
            a = int(255 * ease(ramp(u, 0.0, 0.3)))
            self.slanted_plate(d, p, alpha=a, yaw=yaw)
            self.gumball(d, p, alpha=a, aligned=False, yaw=yaw)
            # 歪掉的网格：水平线，与斜面法线不一致
            for i in range(1, 6):
                f = i / 6
                y = self.H * (0.30 + 0.36 * f)
                d.line([(self.W * 0.34, y), (self.W * 0.86, y)],
                       fill=hexrgb(p["bad"], int(a * 0.35)), width=2)
            if u > 0.55:
                q = self.proj((0, 0, 0), yaw=yaw)
                self.label(d, (q[0] + 190, q[1] - 120), "CPlane ≠ 斜面",
                           p["bad"], "tag", a=int(255 * ease(ramp(u, 0.55, 0.8))))

        elif sc == "define":
            a = int(255 * ease(ramp(u, 0.0, 0.22)))
            self.slanted_plate(d, p, alpha=a, yaw=yaw)
            # v3：揭示提前到 u=0.60 完成（原来 0.78），抽帧点 0.65 才看得见主角
            rev = ease(ramp(u, 0.28, 0.60))
            self.datum_plane(d, p, alpha=int(255 * rev), yaw=yaw,
                             fill_alpha=0.72 * rev, edge_alpha=rev)
            # 三点依次点亮：A → B → C。
            # v3 起必须画在面**之上**：0.72 的实心填充会把先画的点盖死（v2 填充淡所以没暴露）。
            pts = [(-46, -30, -0.55 * 46), (46, -30, 0.55 * 46), (46, 30, 0.55 * 46)]
            for i, pt in enumerate(pts):
                kk = ease(ramp(u, 0.14 + i * 0.10, 0.28 + i * 0.10))
                if kk <= 0:
                    continue
                q = self.proj(pt, yaw=yaw)
                d.ellipse([q[0] - 9, q[1] - 9, q[0] + 9, q[1] + 9],
                          fill=hexrgb(p["accent"], int(255 * kk)))
                if i > 0:
                    qp = self.proj(pts[i - 1], yaw=yaw)
                    d.line([qp, q], fill=hexrgb(p["accent"], int(210 * kk)), width=2)
            if rev > 0.7:
                q = self.proj((0, 0, 0), yaw=yaw)
                self.label(d, (q[0], q[1] - 108), "面积质心 = 原点",
                           p["plane_hi"], "tag", a=int(255 * ramp(u, 0.70, 0.88)))

        elif sc == "align":
            # v3：这一镜固定视角。yaw 若跟着全片的缓慢摆动走，
            # 会在 45° 附近把基准面投影压成一条细线（实测 brown 只剩 0.19%）。
            ya = self.cfg["iso_yaw"]
            a = int(255 * ease(ramp(u, 0.0, 0.2)))
            self.slanted_plate(d, p, alpha=int(a * 0.75), yaw=ya)
            self.datum_plane(d, p, alpha=a, yaw=ya, grid=True)
            # 操作轴从「歪」插值到「贴合」：用 aligned 切换，不靠 yaw 摆动
            k = ease(ramp(u, 0.30, 0.72))
            self.gumball(d, p, alpha=a, aligned=(k > 0.5), yaw=ya)
            if k > 0.45:
                self.label(d, (self.W * 0.60, self.H * 0.30),
                           "CPlane + Gumball 同步", p["good"], "tag",
                           a=int(255 * ease(ramp(u, 0.45, 0.7))))

        elif sc == "normalview":
            a = int(255 * ease(ramp(u, 0.0, 0.22)))
            self.split_view(d, p, u, alpha=a)

        elif sc == "switch":
            a = int(255 * ease(ramp(u, 0.0, 0.22)))
            self.slanted_plate(d, p, alpha=int(a * 0.55), yaw=yaw)
            # v3 对标「流程传递：抵达之后，节点才响应」——
            # 传递线从 DP_01 中心走到 DP_02 中心，走完之前下游一律不响应。
            link = ease(ramp(u, 0.18, 0.48))
            qa = self.proj((0, 0, 0), yaw=yaw)
            qb = (self.W * 0.80, self.H * 0.26)
            qe = (qa[0] + (qb[0] - qa[0]) * link,
                  qa[1] + (qb[1] - qa[1]) * link)
            d.line([qa, qe], fill=hexrgb(p["accent"], int(210 * link)), width=3)
            d.ellipse([qe[0] - 7, qe[1] - 7, qe[0] + 7, qe[1] + 7],
                      fill=hexrgb(p["accent"], int(255 * link)))
            shift = ease(ramp(u, 0.46, 0.70)) if link >= 0.98 else 0.0
            self.datum_plane(d, p, alpha=int(a * (1 - shift * 0.45)),
                             yaw=yaw, fill_alpha=0.52)
            if shift > 0:
                # DP_02 缩到 0.5× 挪到右上：两块面不重叠，
                # 否则小 alpha 的填充会把已画好的 DP_01 擦掉（见 poly 里的坑注释）
                self.datum_plane(d, p, alpha=int(255 * shift), yaw=yaw + 0.9,
                                 fill_alpha=0.40, edge_alpha=0.95,
                                 cx=qb[0], cy=qb[1],
                                 scale=0.5 * 6.8 * self.H / 900)
            if shift > 0.3:
                # 标签放 DP_02 左侧空白区、右对齐，避免压在面板上被线穿过
                self.label(d, (qb[0] - 200, qb[1] + 4),
                           "DP_02 · 法向视图跟随", p["text"], "tag",
                           anchor="rm", a=int(255 * shift))

        elif sc == "alias":
            a = int(255 * ease(ramp(u, 0.0, 0.2)))
            self.alias_compare(d, p, u, alpha=a)

        elif sc == "lock":
            a = int(255 * ease(ramp(u, 0.0, 0.24)))
            px, py = int(self.W * 0.20), int(self.H * 0.20)
            self.layer_panel(d, p, px, py, int(self.W * 0.38), int(self.H * 0.56),
                             alpha=a, eyes=(True, True, True),
                             locks=(False, True, True), highlight=1,
                             u=u, stagger=True)
            # 删除被拒：红叉 + False
            k = ease(ramp(u, 0.48, 0.72))
            if k > 0:
                x, y = int(self.W * 0.72), int(self.H * 0.44)
                d.line([(x - 22, y - 22), (x + 22, y + 22)],
                       fill=hexrgb(p["bad"], int(255 * k)), width=6)
                d.line([(x - 22, y + 22), (x + 22, y - 22)],
                       fill=hexrgb(p["bad"], int(255 * k)), width=6)
                self.label(d, (x, y + 66), "Objects.Delete → False",
                           p["bad"], "tag", a=int(255 * k))
                self.label(d, (x, y + 112), "但 GetObject 仍可拾取",
                           p["good"], "tag", a=int(255 * k))

        elif sc == "hide":
            a = int(255 * ease(ramp(u, 0.0, 0.18)))
            px, py = int(self.W * 0.20), int(self.H * 0.20)
            phase = ease(ramp(u, 0.20, 0.52))   # 0→1 关灯
            back = ease(ramp(u, 0.62, 0.92))    # 0→1 复亮
            eyes_on = phase < 0.5 or back > 0.5
            self.layer_panel(d, p, px, py, int(self.W * 0.38), int(self.H * 0.56),
                             alpha=a, eyes=(eyes_on, eyes_on, eyes_on),
                             locks=(False, True, True), highlight=1,
                             u=u, stagger=True)
            # 右侧大字提示：锁定全程不变
            x, y = int(self.W * 0.72), int(self.H * 0.36)
            if phase < 0.5:
                self.label(d, (x, y), "jH 隐藏", p["accent"], "body", a=a)
            elif back < 0.5:
                self.label(d, (x, y), "只关灯", p["plane"], "body", a=a)
            else:
                self.label(d, (x, y), "jhh 快照还原", p["good"], "body", a=a)
            self.label(d, (x, y + 60), "锁定 = 1  →  1",
                       p["good"], "tag", a=a)

        elif sc == "restore":
            a = int(255 * ease(ramp(u, 0.0, 0.22)))
            self.slanted_plate(d, p, alpha=int(a * 0.35), yaw=yaw)
            # 歪轴回正：aligned 由进度切换
            k = ease(ramp(u, 0.25, 0.55))
            self.gumball(d, p, alpha=a, aligned=(k > 0.5), yaw=yaw)
            # 代码打字（片尾）：纯 ASCII 用等宽字体
            code = [
                "def frame(t):",
                "    beat, u, t0 = beat_at(t)",
                "    return render_beat(beat, u, t)",
                "# no clock / no random / no network",
            ]
            x = int(self.W * 0.10)
            for i, ln in enumerate(code):
                kk = ease(ramp(u, 0.40 + i * 0.10, 0.54 + i * 0.10))
                if kk <= 0:
                    continue
                self.label(d, (x, int(self.H * (0.52 + i * 0.075))),
                           ln[:max(0, int(len(ln) * kk))],
                           p["surface"] if i < 3 else p["muted"],
                           "code", anchor="la", a=255)

        # 光晕：半分辨率模糊一次
        glow = self._soft(layer, 9)
        layer = Image.alpha_composite(layer, Image.blend(
            Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0)), glow, 0.42))
        return layer

    # ---------------- 字幕 / HUD ----------------
    def captions(self, img, beat, u):
        p = self.pal
        d = ImageDraw.Draw(img, "RGBA")
        a = int(255 * ease(ramp(u, 0.02, 0.20)) * (1 - ease(ramp(u, 0.90, 1.0))))
        if a <= 0:
            return
        title, sub = beat.get("title", ""), beat.get("sub", "")
        k = self.H / 900.0
        # alias 镜的两块对照面板从 y≈0.17H 起，说明行放左上会压在浅色面板上，
        # 这一镜改为空出行（数字仍在上屏，靠 sub 说明即可）。
        no_lines = beat["scene"] in ("restore", "alias")
        lines = ([] if no_lines else beat.get("lines", []))
        for i, ln in enumerate(lines):
            kk = ease(ramp(u, 0.16 + i * 0.10, 0.34 + i * 0.10))
            if kk <= 0:
                continue
            la = int(a * kk)
            y = int(132 * k) + i * int(46 * k)
            d.ellipse([int(92 * k), y + 9, int(100 * k), y + 17],
                      fill=hexrgb(p["accent"], la))
            d.text((int(116 * k), y), ln, font=self.fonts["body"],
                   fill=hexrgb(p["muted"], la))
        if beat["scene"] != "title":
            ty = self.H - int(168 * k)
            d.text((int(92 * k), ty), title, font=self.fonts["title"],
                   fill=hexrgb(p["text"], a), anchor="la")
            d.text((int(94 * k), ty + int(76 * k)), sub, font=self.fonts["sub"],
                   fill=hexrgb(p["muted"], a), anchor="la")
            d.rounded_rectangle([int(62 * k), ty + int(4 * k),
                                 int(72 * k), ty + int(58 * k)], radius=5,
                                fill=hexrgb(p["accent"], a))
        metrics = beat.get("metrics", [])
        if metrics and self.cfg["show_labels"]:
            mk = ease(ramp(u, 0.34, 0.80))
            rx = self.W - int(110 * k)
            # alias 镜面板占到 0.65H，数字放右上会压在浅色面板上 → 挪到右下空白带
            my0 = int(700 * k) if beat["scene"] == "alias" else int(112 * k)
            for i, (lab, v0, v1, dec) in enumerate(metrics):
                val = v0 + (v1 - v0) * mk
                txt = ("%." + str(dec) + "f") % val
                y = my0 + i * int(96 * k)
                d.text((rx, y), txt, font=self.fonts["num"],
                       fill=hexrgb(p["good"] if i == 0 else p["accent"], a), anchor="ra")
                self.label(d, (rx, y + int(46 * k)), lab, p["muted"], "tag",
                           anchor="ra", a=a)
        if beat["scene"] == "title":
            kk = ease_out_back(clamp01(ramp(u, 0.06, 0.42)))
            ta = int(255 * clamp01(ramp(u, 0.06, 0.30)))
            cx, cy = self.W * 0.5, int(300 * k) + (1 - kk) * 46
            d.text((cx, cy), title, font=self.fonts["huge"],
                   fill=hexrgb(p["text"], ta), anchor="mm")
            d.text((cx, cy + int(92 * k)), sub, font=self.fonts["sub"],
                   fill=hexrgb(p["accent"], ta), anchor="mm")
            self.label(d, (cx, cy + int(150 * k)), beat.get("note", ""),
                       p["muted"], "tag", anchor="mm", a=ta)

    def hud(self, img, t, beat):
        p = self.pal
        d = ImageDraw.Draw(img, "RGBA")
        k = self.H / 900.0
        x0, x1, y = int(92 * k), self.W - int(92 * k), int(44 * k)
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
        d.text((x0, int(18 * k)), "DATUM PLANE / SPATIAL LOGIC",
               font=self.fonts["tag"], fill=hexrgb(p["muted"], 200), anchor="la")
        d.text((x1, int(18 * k)), "%02d / %02d   %.1fs" %
               (beat["id"] + 1, len(SB.BEATS), t),
               font=self.fonts["tag"], fill=hexrgb(p["muted"], 200), anchor="ra")

    def frame(self, t):
        """纯函数：输出只取决于 t 与 CONFIG。"""
        beat, u, t0 = SB.beat_at(t)
        geom = self.geometry(beat, u, t)
        if beat["id"] > 0 and (t - t0) < self.fade:
            prev = SB.BEATS[beat["id"] - 1]
            geom_prev = self.geometry(prev, 1.0, t0 - 0.001)
            geom = Image.blend(geom_prev, geom, ease((t - t0) / self.fade))

        # ★ 拍点呼吸脉冲（Remotion 对标 P0）：每拍起点几何层轻微放大再回落。
        # 只作用于几何层，字幕/HUD 不受影响；纯函数依赖 t，不破坏确定性。
        pulse = SB.beat_pulse(t)
        if pulse > 0.0005:
            nw = max(1, int(self.W * (1 + pulse)))
            nh = max(1, int(self.H * (1 + pulse)))
            scaled = geom.resize((nw, nh), Image.Resampling.BILINEAR)
            # 居中贴回原尺寸画布（几何缩放以画面中心为锚点）
            ox, oy = (nw - self.W) // 2, (nh - self.H) // 2
            base = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
            base.alpha_composite(scaled, (-ox, -oy))
            geom = base

        img = Image.alpha_composite(self.base.copy(), geom)
        self.captions(img, beat, u)
        self.hud(img, t, beat)
        return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", nargs="*", type=float, default=None)
    ap.add_argument("--frames", nargs=2, type=int, default=None)
    ap.add_argument("--out", default=FRAMES)
    ap.add_argument("--scale", type=float, default=1.0)
    args = ap.parse_args()
    cfg = dict(SB.CONFIG)
    if args.scale != 1.0:
        cfg["width"] = int(cfg["width"] * args.scale)
        cfg["height"] = int(cfg["height"] * args.scale)
    r = Renderer(cfg)
    os.makedirs(args.out, exist_ok=True)
    fps = cfg["fps"]
    if args.probe is not None:
        for t in args.probe:
            img = r.frame(t)
            img.save(os.path.join(args.out, "probe_%05.1f.png" % t))
            print("PROBE t=%.2f -> probe_%05.1f.png" % (t, t))
        print("PROBE_DONE", len(args.probe))
        return
    total = int(SB.TOTAL_DURATION * fps)
    lo, hi = (args.frames if args.frames else (0, total))
    for i in range(lo, hi):
        t = i / fps
        r.frame(t).save(os.path.join(args.out, "%05d.png" % i), compress_level=1)
        if i % 120 == 0 or i == hi - 1:
            print("FRAME %d / %d  t=%.2fs" % (i, hi, t), flush=True)
    print("RENDER_DONE %d frames  total=%.2fs  size=%dx%d" %
          (hi - lo, SB.TOTAL_DURATION, cfg["width"], cfg["height"]))


if __name__ == "__main__":
    main()
