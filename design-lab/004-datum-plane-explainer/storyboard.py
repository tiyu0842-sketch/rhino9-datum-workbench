# -*- coding: utf-8 -*-
"""
storyboard.py —— 004「基准面」的唯一数据源 (single source of truth)

与 002 严格同构：render.py / audio.py / encode.py 都是 `import storyboard as SB`，
只读 BEATS / AUDIO / CONFIG / PALETTE + beat_at()/cumulative_starts()。
改一句字幕 = 一次 diff + 重渲染，不是重新抽卡。

★ 三条禁令：不读系统时间、不用无种子随机、渲染时不联网。
  同一份代码 + 同一份 CONFIG，每一帧逐像素相同；WAV 逐字节相同。

状态（2026-11-25）：v3 重生成（对标 BV1wvJB6aEp5 / BV1CSHS6BEQr）。
v2 已有拍点系统 + 动效库；v3 补流程传递 / 画中画连续移动 / stagger 逐个弹入，
并按 v2 画面验收修 4 处构图硬伤（棕面可见性、几何尺度、标题镜引导线、背景亮度）。
本文件只定义数据，不含任何渲染动作。
"""

import math

# ---------------------------------------------------------------------------
# 风格 token：沿用 002 的深色 Manim/Tech-Glow；只新增「基准面棕」
# 棕 #B08246 来自插件的行业棕 RGB(176,132,70)，让画面与插件一致。
# ---------------------------------------------------------------------------
PALETTE = {
    "ground":   "#161920",   # v3 提亮一档（v2 实测 meanL 仅 28，深底把棕面压没了）
    "grid":     "#33373F",   # v3 网格提亮
    "vignette": "#0E1015",
    "text":     "#ECEDEF",
    "muted":    "#9A9EA8",
    "line":     "#8E929C",
    "surface":  "#5CC8E8",   # 原生几何 / CPlane（青）
    "plane":    "#B08246",   # ★ 基准面（行业棕，RGB 176,132,70，不臆造）
    "plane_hi": "#D9A45E",   # v3 基准面 1px 亮边，把半透明面从深底勾出来
    "feature":  "#FF8A28",   # 选中 / 操作轴高亮
    "accent":   "#FFD25A",   # 揭示 / 主和弦落点
    "good":     "#8BD17C",   # 结论 / 锁定完好
    "bad":      "#FF6B5E",   # 痛点 / 歪掉的轴
    "glow":     "#3A6EA5",
}

# ---------------------------------------------------------------------------
# 可调参数（预览页滑块后端；明天渲染母版用 1080p）
# ---------------------------------------------------------------------------
CONFIG = {
    "fps":              24,
    "width":            1920,   # 比 002 的 1600 高一档；B 站可吃 1080P
    "height":           1080,
    "master_size":      "1920x1080",
    "iso_yaw":          0.62,
    "plane_alpha":      0.78,   # v3 规格值（实际由 primitives.datum_plane 的 fill_alpha 落实）
    "plane_origin":     "area_centroid",  # 原点落面积质心（v2.0 精度改进）
    "lock_icon":        True,   # 图层面板锁图标（v2.13 核心：隐藏时不动）
    "show_labels":      True,
    "playback_speed":   1.0,
    "theme":            "manim-dark",
    "seed":             20261124,
}

# ---------------------------------------------------------------------------
# 分镜：10 镜 / 62.5 s。每个 beat 只讲一个空间逻辑点。
# scene 是 render.py 的分派键；metrics=(标签,起,止,小数位) 仅部分镜有。
# ---------------------------------------------------------------------------
BEATS = [
    {
        "id": 0, "scene": "title", "dur": 4.0,
        "title": "在斜面上建模，为什么别扭？",
        "sub": "不是你手笨，是工作平面没对齐",
        "note": "Rhino 基准面 · 犀流 004 · 代码逐帧渲染",
        "lines": [
            "犀流 · Rhino/Grasshopper 编程与空间逻辑导师",
            "基准面不是显示效果，是一把可命名、可锁定、可还原的尺子",
        ],
        "metrics": [],
    },
    {
        "id": 1, "scene": "pain", "dur": 6.0,
        "title": "歪的不是相机，是 CPlane",
        "sub": "网格歪 / 操作轴歪 / 尺寸对不齐",
        "note": "v2.5 实测：歪的是视口 CPlane，不是相机",
        "lines": [
            "Front 视图看着歪，世界坐标三脚架却是正的",
            "v2.5 实测根因：视口的工作平面被写歪了",
        ],
        "metrics": [],
    },
    {
        "id": 2, "scene": "define", "dur": 6.5,
        "title": "基准面 = 一把可命名的尺子",
        "sub": "三点定面 A · 直接点平面 B（v2.7 起不用 Ctrl+Shift）",
        "note": "v1.3 行业棕 + v2.7 直接点面（面积质心为原点）",
        "lines": [
            "原点落面积质心，UV 当 X/Y，法线当 Z",
            "半透明棕 RGB(176,132,70) / 55% · 行业基准面色系",
        ],
        "metrics": [],
    },
    {
        "id": 3, "scene": "align", "dur": 6.5,
        "title": "CPlane 与操作轴，一起转过去",
        "sub": "斜面于是变成「顶视图」",
        "note": "工作平面 + Gumball 同步对齐；逐视口存档（v2.5）",
        "lines": [
            "工作平面 / Gumball 同时对齐到基准面",
            "v2.5：逐视口存档 CPlane，退出时各回各家",
        ],
        "metrics": [],
    },
    {
        "id": 4, "scene": "normalview", "dur": 7.0,
        "title": "第 5 视图：基准面法向",
        "sub": "Top 竖直一分为二，右半相机垂直于面",
        "note": "SetToPlanView + 平行投影；dot(dir,−N)=1.0（v1.6 实测）",
        "lines": [
            "SetToPlanView + 平行投影，dot(dir,−N)=1.0（实测）",
            "像顶视图一样，在斜面上直接画",
        ],
        "metrics": [],
    },
    {
        "id": 5, "scene": "switch", "dur": 6.0,
        "title": "C 点选 / D 调用 / E 保存",
        "sub": "命名平面 = 坐标快照，不重复建几何",
        "note": "NamedConstructionPlanes 单一数据源（v1.6）",
        "lines": [
            "切换基准面时，第 5 视图自动跟随",
            "数据模型：NamedConstructionPlanes 单一管理",
        ],
        "metrics": [],
    },
    {
        "id": 6, "scene": "alias", "dur": 7.0,
        "title": "看得清：Alias 浅 I / 深 J",
        "sub": "等参线显出曲面走向，三度灰阶不死白",
        "note": "P10/P50/P90=101/119/152 · 纯白 0.00%（v2.6 逐像素实测）",
        "lines": [
            "实测 P10/P50/P90 = 101/119/152，纯白 0.00%",
            "结构线密度区分：浅 0（裸边）/ 深 1（一条等参线）",
        ],
        "metrics": [("纯白像素 / clipped", 9.5, 0.0, 2)],
    },
    {
        "id": 7, "scene": "lock", "dur": 6.0,
        "title": "子层锁定：删不掉，但能点",
        "sub": "构造成功后才上锁",
        "note": "图层 UserString 标记；Delete 返回 False（实测）",
        "lines": [
            "实测 doc.Objects.Delete(锁面子层) 返回 False",
            "GetObject.LockedObjectSelect=true 仍可拾取切换",
        ],
        "metrics": [("删除成功 / deletable", 1, 0, 0)],
    },
    {
        "id": 8, "scene": "hide", "dur": 7.0,
        "title": "jH 隐藏 / jhh 快照还原",
        "sub": "隐藏只关灯，锁定一个字段都不碰",
        "note": "快照→还原；ForceLayerVisible + SetPersistentLocking（v2.13 / E-032）",
        "lines": [
            "v2.13：快照存 doc.Strings → 按快照原样还原",
            "逐视口 ForceLayerVisible / SetPersistentLocking",
        ],
        "metrics": [("锁定状态 / locked", 1, 1, 0)],
    },
    {
        "id": 9, "scene": "restore", "dur": 6.5,
        "title": "H 退出：CPlane 与操作轴精确还原",
        "sub": "每一帧都由代码算出，同一份代码同一条片",
        "note": "frame(t)/sample(t) 纯函数 · 三条禁令",
        "lines": [
            "frame(t)/sample(t) 纯函数 · 不读时钟 · 不用随机 · 不联网",
            "design-lab/004 · 改一句字幕 = 一次 diff + 重渲染",
        ],
        "metrics": [],
    },
]

TOTAL_DURATION = sum(b["dur"] for b in BEATS)   # 62.5 s

# ★ 拍点系统（对标 Remotion 的 beatFrame）：让画面"跟着音乐呼吸"。
# 配乐 arpeggio_bpm=60 → 每拍 1.0 s。所有脉冲/卡点按拍号定位，不写死帧号。
BPM = 60.0
BEAT_SEC = 60.0 / BPM   # 1.0 s/拍


def beat_time(n):
    """第 n 拍的绝对秒数（n 可为小数，如 2.5 拍）。纯函数。"""
    return n * BEAT_SEC


def beat_pulse(t, decay=18.0, amount=0.022):
    """底鼓呼吸脉冲：每拍起点一个快速衰减的缩放量，返回 [0, amount]。

    phase = t 在本拍内的位置；前 12% 拍长内有脉冲，指数衰减。
    这是 Remotion 教程里"每次底鼓给画面一个缩放脉冲"的纯函数版本。
    """
    phase = (t % BEAT_SEC) / BEAT_SEC
    if phase > 0.12:
        return 0.0
    return amount * math.exp(-phase * decay)


def beat_at(t):
    """返回 (beat, 局部进度 u∈[0,1], 全局起始时间 t0)。纯函数。"""
    t0 = 0.0
    for b in BEATS:
        if t < t0 + b["dur"] or b is BEATS[-1]:
            return b, max(0.0, min(1.0, (t - t0) / b["dur"])), t0
        t0 += b["dur"]
    return BEATS[-1], 1.0, t0


def cumulative_starts():
    out, t0 = [], 0.0
    for b in BEATS:
        out.append((b["id"], t0, t0 + b["dur"]))
        t0 += b["dur"]
    return out


# ---------------------------------------------------------------------------
# 音频：沿用 002 v3 已验证的 D 大调四和弦配方，按【绝对秒】走，与 BEATS 解耦。
# 情绪弧拉长到 62.5 s；啊哈落点 t=52.5（正好 hide 镜中段 + Dmaj9 回归）。
# ---------------------------------------------------------------------------
AUDIO = {
    "sample_rate": 48000,
    "channels":    2,
    "master":      0.82,

    "progression": [
        {"name": "Dmaj9",    "notes": [50, 57, 62, 64, 66, 69]},
        {"name": "Bm9",      "notes": [47, 54, 62, 61, 66, 69]},
        {"name": "Gmaj7s11", "notes": [43, 50, 59, 61, 66, 71]},
        {"name": "Asus2",    "notes": [45, 52, 59, 61, 64, 69]},
    ],
    # 6.25 s/和弦 → 一轮 25 s；t=52.5 时 idx=8, 8%4=0 → Dmaj9 主和弦回归，
    # 正好压在 hide 镜（49.0–56.0）中段。这是「啊哈」落点，别改回 8.0。
    "chord_sec":    6.25,
    "arpeggio_bpm": 60.0,

    "arc": [
        {"name": "setup",   "t0": 0.0,  "t1": 10.0, "energy": 0.30},
        {"name": "build",   "t0": 10.0, "t1": 49.0, "energy": 0.65},
        {"name": "aha",     "t0": 49.0, "t1": 56.0, "energy": 1.00},
        {"name": "resolve", "t0": 56.0, "t1": 62.5, "energy": 0.70},
    ],
    "aha_hit": 52.5,

    "pad_level":       0.06,
    "pad_highpass_hz": 80.0,
    "pad_detune_hz":   0.12,
    "pad_lfo_hz":      0.07,
    "pad_lfo_depth":   0.20,
    "fade_in":         2.5,
    "fade_out":        3.5,

    "room_taps": {
        "L": [(83, 0.28), (191, 0.18), (370, 0.10)],
        "R": [(97, 0.28), (211, 0.18), (389, 0.10)],
    },

    # 8 个事件 / 62.5 s ≈ 0.128 事件每秒，最小间隔 4.0 s（比 002 更留白）。
    # 全部按绝对秒，频率由 MIDI 换算保证与当前和弦同调。
    "events": [
        {"t": 0.06,  "kind": "cue",   "midi": 69, "gain": 0.72},
        {"t": 10.06, "kind": "cue",   "midi": 74, "gain": 0.78},
        {"t": 16.56, "kind": "cue",   "midi": 69, "gain": 0.78},
        {"t": 23.06, "kind": "thud",  "midi": 50, "gain": 0.68},
        {"t": 30.56, "kind": "cue",   "midi": 78, "gain": 0.82},
        {"t": 43.56, "kind": "cue",   "midi": 74, "gain": 0.80},
        {"t": 52.50, "kind": "chord", "midi": 62, "gain": 1.00},
        {"t": 56.56, "kind": "cue",   "midi": 69, "gain": 0.66},
    ],
}
