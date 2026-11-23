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
# ---------------------------------------------------------------------------
AUDIO = {
    "sample_rate": 48000,   # 48 kHz / 16-bit / mono：够用，且 WAV 只有 ~4 MB
    "master":      0.82,    # 总音量（归一化后再乘）
    "pad_level":   0.16,    # 氛围底层（连续层）
    "cue_level":   0.30,    # 离散事件层统一增益
    "pad_root":    55.0,    # A1，低频基底
    # 每镜目标半音偏移；镜头开头 glide 秒内滑过去，频率不做硬切（硬切 = click）
    "pad_steps":   [0, 3, 5, 7, 10, 12, 7, 0],
    "pad_glide":   0.90,
    "fade_in":     0.70,
    "fade_out":    1.40,
    # 每镜转场「叮」的基频（A3→D5，小调五声偏），按镜头编号走，不用随机
    "scale":       [220.00, 261.63, 293.66, 329.63,
                    392.00, 440.00, 523.25, 587.33],
}
