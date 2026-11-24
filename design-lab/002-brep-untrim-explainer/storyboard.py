# -*- coding: utf-8 -*-
"""
storyboard.py —— 002 号实验的「唯一数据源」(single source of truth)

Claude 系代码视频的工程纪律：brief / storyboard / 渲染器 / 预览器 必须共享同一份数据，
改一句字幕只是 diff + 重渲染，不是重新抽卡。本文件被四处消费：

  render.py      → import BEATS / PALETTE / CONFIG，用 Pillow 逐帧出 PNG
  audio.py       → import BEATS / AUDIO，把镜头边界翻译成确定性声音事件
  encode.py      → 读 BEATS 得到镜头边界，按镜头分段合成再整片拼接
  preview.html   → 由 build_html.py 把 BEATS / AUDIO / 事件表序列化成内联 JSON，
                   Canvas 按 t 重画同套几何，Web Audio 按 t 复现同套音色

★ 三条禁令（确定性渲染）：不读系统时间、不用无种子随机、渲染时不联网。
  同一份代码 + 同一份 CONFIG，每次渲染出的每一帧逐像素相同；
  音轨同理：sample(t) 也是纯函数，同一份数据每次出的 WAV 逐字节相同。
"""

# ---------------------------------------------------------------------------
# 风格 token（style.md 是它的自然语言说明；这里是可执行版本）
# 深色 Manim / Tech-Glow 混合：#17181C 底 + 精确矢量描边 + 单色霓虹高亮
# ---------------------------------------------------------------------------
PALETTE = {
    "ground":   "#12141A",   # 背景
    "grid":     "#24262C",   # 细网格
    "vignette": "#0B0C10",   # 暗角
    "text":     "#ECEDEF",   # 主文字
    "muted":    "#9A9EA8",   # 次要文字
    "line":     "#8E929C",   # 中性描边
    "surface":  "#5CC8E8",   # 底层曲面 / 原生面（青）
    "feature":  "#FF8A28",   # 特征 / trim 环 / 圆角（橙，与插件视口一致）
    "accent":   "#FFD25A",   # 高亮 / 选中（黄）
    "good":     "#8BD17C",   # 结论 / 保留（绿）
    "bad":      "#FF6B5E",   # 否定 / 报错（红）
    "glow":     "#3A6EA5",   # 背景冷光斑
}

# ---------------------------------------------------------------------------
# 可调参数（全部是滑块的后端；preview.html 里 6 个滑块与之一一对应）
# ---------------------------------------------------------------------------
CONFIG = {
    "fps":              24,      # 帧率
    "width":            1600,    # 画面宽
    "height":           900,     # 画面高
    "iso_yaw":          0.62,    # 轴测旋转（弧度），控制立体感/镜头
    "fillet_radius":    3.0,     # 圆角半径 R（示意几何与数字）
    "isoline_density":  6,       # 等参线密度 ★ 用户明确要求「降密度而非全隐藏」
    "show_labels":      True,    # F1/H1 编号标签 + 上屏数字
    "playback_speed":   1.0,     # 预览播放速度（不影响离线渲染的帧内容）
    "theme":            "manim-dark",  # manim-dark / tech-glow / light
    "seed":             20261123,      # 固定种子：光斑位置由确定性公式生成
}

# ---------------------------------------------------------------------------
# 分镜。每个 beat 恰好奇一个概念；dur 单位秒；scene 是 render.py 的分派键。
# metrics = (标签, 起始值, 结束值, 小数位) —— 在 beat 内随进度滚动上屏。
# ---------------------------------------------------------------------------
BEATS = [
    {
        "id": 0, "scene": "title", "dur": 3.2,
        "title": "同一个立方体，两种「多出来的形状」",
        "sub": "为什么一个孔能一键消失，一个圆角不能？",
        "note": "B-rep 的两层结构 · Rhino 9 / FeatureWorks 实证",
        "metrics": [],
    },
    {
        "id": 1, "scene": "two_layers", "dur": 5.4,
        "title": "B-rep 有两层，不是一整块",
        "sub": "钻孔只动了第二层",
        "lines": [
            "① 底层曲面 UnderlyingSurface —— 一整张没被破坏的平面",
            "② 裁剪环 trim loops —— 只是画在它上面的边界",
        ],
        "metrics": [],
    },
    {
        "id": 2, "scene": "hole_untrim", "dur": 6.0,
        "title": "孔 = 加了一个 inner loop",
        "sub": "底层曲面一点没坏，所以「取消」就是删掉那个环",
        "lines": [
            "RemoveHoles(指定内环, tol)  →  孔闭合",
            "整面级 UntrimFace 会连外环一起抹掉 —— 那是错的粒度",
        ],
        "metrics": [
            ("面数 / faces", 8, 7, 0),
            ("体积 / volume", 233214.16, 236607.08, 2),
        ],
    },
    {
        "id": 3, "scene": "selective_holes", "dur": 6.6,
        "title": "两个孔，只勾一个（E-024）",
        "sub": "loop 级精度官方就有，不必先去圆角",
        "lines": [
            "H1 的两个内环 [7, 8] 被删，H2 纹丝不动",
            "旧实现 UntrimFace → 两个孔一起没；新实现只删选中的",
        ],
        "metrics": [
            ("inner loops", 4, 2, 0),
            ("体积 / volume", 233214.16, 236607.08, 2),
        ],
    },
    {
        "id": 4, "scene": "fillet", "dur": 7.2,
        "title": "圆角不是裁剪，是新增了一整圈曲面",
        "sub": "滚球扫出的过渡面，四边都与邻面共享边",
        "lines": [
            "没有更大的底层曲面可以还原  →  UntrimOuterLoop 恒为 null",
            "只能：删整圈过渡面 → 相邻面重新求交 → CreateSolid 缝合",
        ],
        "metrics": [],
    },
    {
        "id": 5, "scene": "independence", "dur": 7.0,
        "title": "打破伪约束：去布尔不需要先去圆角",
        "sub": "圆角盒 + 1 孔 → 只删孔的内环 → 得到纯圆角盒",
        "lines": [
            "删 [11, 12] 两个内环，4 组圆角面全部完好",
            "两个模块因此完全独立、任意顺序",
        ],
        "metrics": [
            ("面数 / faces", 11, 10, 0),
            ("体积 / volume", 235922.14, 239315.06, 2),
        ],
    },
    {
        "id": 6, "scene": "conclusion", "dur": 5.2,
        "title": "孔是可抹的边界，圆角是须重缝的实体",
        "sub": "机器给候选 · 人裁决 · 明确报出，不偷偷改",
        "lines": [
            "模块 B 去除布尔切割   ↔   RemoveHoles(指定内环)",
            "模块 A 去除圆角       ↔   删整圈 + 重缝",
            "两者互不依赖，没有总开关",
        ],
        "metrics": [],
    },
    {
        "id": 7, "scene": "outro", "dur": 4.0,
        "title": "每一帧都由代码算出",
        "sub": "frame(t) 纯函数 · 不读时钟 · 不用随机 · 不联网",
        "lines": [
            "改一句字幕 = 一次 diff + 重渲染，不是重新抽卡",
            "design-lab/002 · 参数与分镜在同一份 storyboard.py",
        ],
        "metrics": [],
    },
]

TOTAL_DURATION = sum(b["dur"] for b in BEATS)   # 44.6 s


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
# 音频 token（style.md §8 是它的自然语言说明；audio.py 是它的可执行版本）
# 与画面一样：全部由代码合成，不加载任何外部音频素材。
#
# v3（2026-11-24，E-029 拍板 D1-D6 推荐 A）：
#   D1 不开口子——纯标准库 wave/array/math；
#   D2 stereo + 三抽头房间回声（左右不同抽头）；
#   D3 固定 D major 四和弦循环，按【绝对秒】走，与 BEATS 编号解耦；
#   D5 四段情绪弧，"啊哈"揭示点落在 t=32.0s（正好 Dmaj9 回归）；
#   D6 pad 音量 0.16→0.06 + 80Hz 高通 + 固定 detune + 慢 LFO。
# 关键：配乐时间轴不读 BEATS —— 改字幕 / 改镜头 dur 不再牵动整条配乐。
# ---------------------------------------------------------------------------
AUDIO = {
    "sample_rate": 48000,   # 48 kHz / 16-bit / stereo
    "channels":    2,
    "master":      0.82,    # 总音量（归一化后再乘）

    # D3：固定 D major。每和弦 8 s 循环，4 和弦 = 32 s 一轮。
    # MIDI 音高（440 Hz = 69）；和弦最低 3 音用于 pad，全音符用于琶音。
    "progression": [
        {"name": "Dmaj9",    "notes": [50, 57, 62, 64, 66, 69]},
        {"name": "Bm9",      "notes": [47, 54, 62, 61, 66, 69]},
        {"name": "Gmaj7s11", "notes": [43, 50, 59, 61, 66, 71]},
        {"name": "Asus2",    "notes": [45, 52, 59, 61, 64, 69]},
    ],
    "chord_sec":    8.0,    # 每和弦时长；t=32.0 时 idx=4%4=0 → Dmaj9 主和弦回归
    "arpeggio_bpm": 60.0,   # 琶音八分音符 = 0.5 s；只在中段（积累）出现

    # D5：四段情绪弧（绝对秒，不读 BEATS）。energy 乘到 pad 与事件力度上。
    "arc": [
        {"name": "setup",   "t0": 0.0,  "t1": 8.6,  "energy": 0.30},
        {"name": "build",   "t0": 8.6,  "t1": 28.4, "energy": 0.65},
        {"name": "aha",     "t0": 28.4, "t1": 35.4, "energy": 1.00},
        {"name": "resolve", "t0": 35.4, "t1": 44.6, "energy": 0.70},
    ],
    "aha_hit": 32.0,        # 揭示帧：明亮主和弦 + 长尾，对应 independence 镜

    # D6：pad 层（连续）——低音量、高通、固定 detune、慢呼吸
    "pad_level":       0.06,   # 0.16 → 0.06（公开配方同量级）
    "pad_highpass_hz": 80.0,   # 一阶高通幅度响应，纯函数算，不用滤镜
    "pad_detune_hz":   0.12,   # 固定 ±0.12 Hz（不是 0.3% 比例失谐）
    "pad_lfo_hz":      0.07,   # 0.11 → 0.07 Hz
    "pad_lfo_depth":   0.20,   # ±38% → ±20%
    "fade_in":         2.5,
    "fade_out":        3.5,

    # D2：三抽头房间回声（毫秒, 增益），左右不同 → stereo 宽度
    "room_taps": {
        "L": [(83, 0.28), (191, 0.18), (370, 0.10)],
        "R": [(97, 0.28), (211, 0.18), (389, 0.10)],
    },

    # D4：离散事件（绝对秒，与 BEATS 解耦）。7 个，最小间隔 3.5 s。
    # 频率由 MIDI 换算，保证与当前和弦同调（修掉旧版 pad↔cue 不同源的 6.35×/10.68×）。
    "events": [
        {"t": 0.06,  "kind": "cue",   "midi": 69, "gain": 0.75},
        {"t": 8.66,  "kind": "cue",   "midi": 74, "gain": 0.80},
        {"t": 14.66, "kind": "cue",   "midi": 69, "gain": 0.80},
        {"t": 21.26, "kind": "thud",  "midi": 50, "gain": 0.70},
        {"t": 28.46, "kind": "cue",   "midi": 78, "gain": 0.85},
        {"t": 32.00, "kind": "chord", "midi": 62, "gain": 1.00},
        {"t": 40.66, "kind": "cue",   "midi": 69, "gain": 0.70},
    ],
}
