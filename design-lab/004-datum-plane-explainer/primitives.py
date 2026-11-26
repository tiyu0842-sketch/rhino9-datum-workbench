# -*- coding: utf-8 -*-
"""
primitives.py —— 可跨片复用的动效基元库（code-video-deterministic skill 的 P0 产出）

设计：每个基元是纯函数，第一个参数 r 是 Renderer 实例（提供 proj/poly/dashed/label/cfg/字体）。
这样几何逻辑与具体片子解耦——下一支片只需 import primitives，不必抄这些方法。

六个基元（2026-11-25 从 render.py 抽取）：
  slanted_plate / datum_plane / gumball / layer_panel / split_view / alias_compare

v3 增补（对标 B 站 BV1wvJB6aEp5 / BV1CSHS6BEQr）：
  - stagger_k()：逐个弹入的通用缓动（叙事型动效，不是装饰）
  - datum_plane()：默认 fill_alpha 0.22→0.50 + 1px 亮边 plane_hi，修「棕面几乎看不见」
  - split_view()：网格线 stagger + 画中画连续移动（同一主体从 Top 滑到法向视图）
  - layer_panel() / alias_compare()：行 / 等参线逐个弹入
"""

import math

from PIL import ImageDraw


def stagger_k(r, u, i, n, lead=0.08, step=0.09):
    """第 i 个元素（共 n 个）的逐个弹入进度 ∈[0,1]。

    Remotion 对标 P1「元素逐个弹入 / stagger，一拍一个」。
    每个元素比前一个晚 step 起，用 r.ease 平滑；纯函数，不读时钟。
    """
    start = lead + step * i
    return r.ease(r.ramp(u, start, start + 0.22))


def slanted_plate(r, d, p, alpha=255, tilt=0.55, yaw=None, **loc):
    """斜面板：沿 x 方向倾斜的矩形，是「斜面建模」的场景载体。
    **loc 透传 cx/cy/scale 给投影，让标题镜能把几何挪到指定位置。"""
    L, W_, Hh = 46, 30, tilt * 46
    corners = [(-L, -W_, -Hh), (L, -W_, Hh), (L, W_, Hh), (-L, W_, -Hh)]
    r.poly(d, corners,
           fill=r.rgba(p["surface"], int(alpha * 0.10)),
           outline=r.rgba(p["surface"], int(alpha * 0.55)), width=2,
           yaw=yaw, **loc)
    for i in (2, 3):
        a, b = corners[i], (corners[i][0], corners[i][1], corners[i][2] - 5)
        r.poly(d, [a, b], outline=r.rgba(p["line"], int(alpha * 0.45)),
               width=2, yaw=yaw, **loc)
    return corners


def datum_plane(r, d, p, alpha=255, tilt=0.55, yaw=None,
                fill_alpha=0.50, edge_alpha=0.95, grid=False, **loc):
    """基准面 = 贴在斜面上的半透明棕色矩形 + 虚线边（行业棕 RGB176,132,70）。

    v3：fill_alpha 默认 0.50（v2 是 0.22，实测棕面像素占比 0.00–0.35% 几乎看不见），
    并加 1px 实线亮边 plane_hi(#D9A45E)，把面从深底里「勾」出来。
    行业棕 #B08246 本身不变，保持与 Rhino 插件一致。
    """
    L, W_, Hh = 54, 36, tilt * 54
    corners = [(-L, -W_, -Hh), (L, -W_, Hh), (L, W_, Hh), (-L, W_, -Hh)]
    r.poly(d, corners, fill=r.rgba(p["plane"], int(alpha * fill_alpha)),
           yaw=yaw, **loc)
    hi = p.get("plane_hi", p["plane"])
    r.poly(d, corners, outline=r.rgba(hi, int(alpha * 0.60)), width=1,
           yaw=yaw, **loc)
    col = r.rgba(p["plane"], int(alpha * edge_alpha))
    for i in range(4):
        r.dashed(d, corners[i], corners[(i + 1) % 4], col, width=3, yaw=yaw, **loc)
    if grid:
        n = 6
        for i in range(1, n):
            f = i / n
            x = -L + 2 * L * f
            r.poly(d, [(x, -W_, tilt * x), (x, W_, tilt * x)],
                   outline=r.rgba(p["surface"], int(alpha * 0.22)),
                   width=1, yaw=yaw, **loc)
            y = -W_ + 2 * W_ * f
            r.poly(d, [(-L, y, tilt * -L), (L, y, tilt * L)],
                   outline=r.rgba(p["surface"], int(alpha * 0.22)),
                   width=1, yaw=yaw, **loc)
    return corners


def gumball(r, d, p, alpha=255, aligned=True, yaw=None):
    """操作轴：aligned=False 画歪的（痛点），True 画贴合基准面的三轴。"""
    o = (0, 0, 0)
    if aligned:
        axes = [((26, 0, 26 * 0.55), p["bad"]),
                ((0, 22, 0), p["good"]),
                ((-20, 0, 20 * 0.55), p["surface"])]
    else:
        axes = [((30, 0, 0), p["bad"]),
                ((0, 26, 0), p["good"]),
                ((0, 0, 26), p["surface"])]
    oc = r.proj(o, yaw=yaw)
    for v, col in axes:
        q = r.proj(v, yaw=yaw)
        d.line([oc, q], fill=r.rgba(col, int(alpha * 0.9)), width=4)
        d.ellipse([q[0] - 7, q[1] - 7, q[0] + 7, q[1] + 7],
                  fill=r.rgba(col, alpha))


def layer_panel(r, d, p, x, y, w, h, alpha=255,
                eyes=(True, False, False), locks=(False, True, True),
                highlight=-1, u=1.0, stagger=False):
    """模拟 Rhino 图层面板：根层 + 两个锁定子层；眼睛/锁图标可独立控制。
    这是 v2.13「jH 只关灯、锁不变」的核心证据画面。

    v3：stagger=True 时三行按 u 逐个弹入（对标「元素逐个弹入」）。
    """
    d.rounded_rectangle([x, y, x + w, y + h], radius=12,
                        fill=r.rgba(p["ground"], int(alpha * 0.85)),
                        outline=r.rgba(p["line"], int(alpha * 0.55)), width=2)
    d.text((x + 22, y + 14), "图层 / Layers", font=r.fonts["small"],
           fill=r.rgba(p["muted"], int(alpha * 0.9)), anchor="la")
    rows = [("基准面", 0), ("DP_01", 1), ("DP_02", 2)]
    rh = (h - 58) // 3
    for i, (name, _) in enumerate(rows):
        ra = (int(alpha * stagger_k(r, u, i, len(rows), lead=0.05, step=0.12))
              if stagger else alpha)
        if ra <= 0:
            continue
        ry = y + 50 + i * rh
        if i == highlight:
            d.rounded_rectangle([x + 10, ry - 4, x + w - 10, ry + rh - 8],
                                radius=6, fill=r.rgba(p["accent"], int(ra * 0.10)))
        indent = 24 if i == 0 else 52
        d.text((x + indent, ry + rh // 2 - 4), name, font=r.fonts["body"],
               fill=r.rgba(p["text"] if i == 0 else p["plane"], ra), anchor="lm")
        ex, ey = x + w - 112, ry + rh // 2 - 4
        ec = p["accent"] if eyes[i] else p["muted"]
        d.ellipse([ex - 13, ey - 9, ex + 13, ey + 9],
                  outline=r.rgba(ec, int(ra * 0.9)), width=2)
        d.ellipse([ex - 4, ey - 4, ex + 4, ey + 4],
                  fill=r.rgba(ec, ra if eyes[i] else int(ra * 0.4)))
        lx, ly = x + w - 52, ry + rh // 2 - 4
        lc = p["good"] if locks[i] else p["bad"]
        d.rounded_rectangle([lx - 12, ly - 2, lx + 12, ly + 13], radius=3,
                            outline=r.rgba(lc, int(ra * 0.9)), width=2)
        if locks[i]:
            d.arc([lx - 8, ly - 12, lx + 8, ly + 4], 180, 360,
                  fill=r.rgba(lc, ra), width=2)
        else:
            d.arc([lx - 2, ly - 12, lx + 14, ly + 4], 180, 360,
                  fill=r.rgba(lc, ra), width=2)


def split_view(r, d, p, u, alpha=255):
    """第 5 视图：Top 竖直一分为二，右半是「基准面法向」正投影。

    v3：网格线按 stagger 逐条弹入；再加「画中画 · 同一个主体，连续移动」——
    一块小基准面从左侧 Top 视图沿弧线连续滑到右侧法向视图，
    对应 BV1CSHS6BEQr 的「画中画·同一个主体，连续移动」。
    """
    x0, y0 = int(r.W * 0.10), int(r.H * 0.16)
    w, h = int(r.W * 0.80), int(r.H * 0.52)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=10,
                        fill=r.rgba(p["ground"], int(alpha * 0.6)),
                        outline=r.rgba(p["line"], int(alpha * 0.6)), width=2)
    mid = x0 + w // 2
    d.line([(mid, y0), (mid, y0 + h)], fill=r.rgba(p["plane"], int(alpha * 0.9)), width=3)
    r.label(d, (x0 + w // 4, y0 + 26), "Top 视图", p["muted"], "tag", a=alpha)
    r.label(d, (mid + w // 4, y0 + 26), "基准面法向", p["plane"], "tag", a=alpha)
    lcx, lcy = x0 + w // 4, y0 + h // 2 + 20
    d.polygon([(lcx - 130, lcy + 70), (lcx + 130, lcy - 10),
               (lcx + 90, lcy - 80), (lcx - 170, lcy + 0)],
              fill=r.rgba(p["plane"], int(alpha * 0.18)),
              outline=r.rgba(p["plane"], int(alpha * 0.8)))
    rcx, rcy = mid + w // 4, y0 + h // 2 + 20
    rr = int(100 * r.ease(r.ramp(u, 0.15, 0.6)))
    d.rectangle([rcx - rr, rcy - rr, rcx + rr, rcy + rr],
                fill=r.rgba(p["plane"], int(alpha * 0.15)),
                outline=r.rgba(p["plane"], int(alpha * 0.95)), width=3)
    for i in range(1, 5):
        k = stagger_k(r, u, i - 1, 4, lead=0.18, step=0.09)
        if k <= 0:
            continue
        f = i / 5
        xx = rcx - rr + 2 * rr * f
        d.line([(xx, rcy - rr), (xx, rcy + rr)],
               fill=r.rgba(p["surface"], int(alpha * 0.28 * k)), width=1)
        yy = rcy - rr + 2 * rr * f
        d.line([(rcx - rr, yy), (rcx + rr, yy)],
               fill=r.rgba(p["surface"], int(alpha * 0.28 * k)), width=1)
    # 画中画连续移动：同一块小基准面，从 Top 视图滑到法向视图
    mv = r.ease(r.ramp(u, 0.26, 0.80))
    sx = lcx + (rcx - lcx) * mv
    sy = lcy - 70 * math.sin(math.pi * mv)
    d.line([(lcx, lcy - 20), (sx, sy)],
           fill=r.rgba(p["plane"], int(alpha * 0.35)), width=2)
    quad = [(sx - 34, sy - 6), (sx + 6, sy - 22),
            (sx + 34, sy + 6), (sx - 6, sy + 22)]
    d.polygon(quad,
              fill=r.rgba(p["plane"], int(alpha * 0.58)),
              outline=r.rgba(p.get("plane_hi", p["plane"]), int(alpha * 0.95)))
    if u > 0.6:
        r.label(d, (rcx, rcy + rr + 40), "dot(dir, −N) = 1.0", p["good"], "tag", a=alpha)


def alias_compare(r, d, p, u, alpha=255):
    """Alias 浅/深观测显示对照：同样的球+环，两套主题；等参线显走向。

    v3：等参线按 stagger 逐条画出，避免一帧糊成一片。
    """
    x0, y0 = int(r.W * 0.12), int(r.H * 0.17)
    w, h = int(r.W * 0.35), int(r.H * 0.48)
    gap = int(r.W * 0.06)
    themes = [
        (x0, "#CBD0D5", "#A6ACB3", "#4A5A68", "#1E1E1E", "浅色 Light · I"),
        (x0 + w + gap, "#2B3134", "#3C4448", "#8FA8B4", "#9ED8C6", "深色 Dark · J"),
    ]
    swap = r.ease(r.ramp(u, 0.55, 0.75))
    for i, (x, bg1, bg2, iso, curve, name) in enumerate(themes):
        active = (i == 0 and swap < 0.5) or (i == 1 and swap >= 0.5)
        a = int(alpha * (1.0 if active else 0.5))
        d.rounded_rectangle([x, y0, x + w, y0 + h], radius=12,
                            fill=r.rgba(bg1, a),
                            outline=r.rgba(p["accent"] if active else p["line"], int(a * 0.9)),
                            width=3 if active else 1)
        cx, cy = x + w // 2, y0 + h // 2
        for j in range(7):
            k = stagger_k(r, u, j, 7, lead=0.06, step=0.055)
            if k <= 0:
                continue
            ry = 90 * (1 - (j / 7) ** 2) ** 0.5
            d.ellipse([cx - 95, cy - ry, cx + 95, cy + ry],
                      outline=r.rgba(iso, int(a * 0.85 * k)), width=2)
        for j in range(1, 7):
            k = stagger_k(r, u, j, 7, lead=0.06, step=0.055)
            if k <= 0:
                continue
            xr = 95 * math.sin(math.pi * j / 7)
            d.line([(cx - xr, cy - 90), (cx - xr, cy + 90)],
                   fill=r.rgba(iso, int(a * 0.5 * k)), width=1)
        d.ellipse([cx - 20, cy + 90, cx + w // 2 + 60, cy + 175],
                  outline=r.rgba(iso, int(a * 0.9)), width=2)
        d.ellipse([cx + 10, cy + 118, cx + w // 2 + 30, cy + 147],
                  outline=r.rgba(curve, int(a * 0.9)), width=2)
        r.label(d, (x + w // 2, y0 + h - 34), name,
                p["text"] if bg1.startswith("#2") else "#1E1E1E", "tag", a=a)
