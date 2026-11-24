# 用代码做一支科普短片：从想法到 B 站的完整流程

> 这是 002 号片子（44 秒，讲「孔能删、圆角不能」）的**全过程讲解**。
> 不是概念介绍，是照着能复现的操作手册：每一节都对应仓库里的真实文件与真实命令。
> 读完你应该能做到：给定一个新题目，用同一套架子做出 30–60 秒的片，画面和音轨都可复现。

---

## 0. 先搞清楚：这不是「AI 文生视频」

网上那批「Claude 科普视频」不是模型直接吐出视频，而是**模型写代码，代码逐帧渲染**：

```
你写 frame(t)  →  渲染 1070 张 PNG  →  ffmpeg 封装成 MP4
你写 sample(t) →  合成一条 WAV      →  与画面合成
```

画面里每个字、每条线、每个数字的位置都在代码里，所以：

- 改一句字幕 = 改一行代码 + 重渲染，其余分毫不动（不是重新抽卡）
- 同一个 `t` 永远得到同一帧（可缓存、可并行、可断点续渲）
- 数字可以被追溯，不会被模型「猜」出一个好看但不真的数

**这份教程能教什么**：单文件级别的工程纪律、构图与声音的可计算做法、发布物料。
**不能教什么**：3D 建模、真人配音、剪辑软件、流量运营。片子里讲的是几何，不是靠剪辑撑起来的。

---

## 1. 选路线：四种做法，选依赖最少的那种

| 路线 | 做法 | 优点 | 代价 |
|---|---|---|---|
| Remotion | React + 帧级渲染 | 前端生态、组件化 | 要 Node + Chromium，包体大 |
| Manim | Python 数学动画 | 数学动画现成 | 要 LaTeX + 一堆依赖，样式偏「课堂」 |
| Canvas + 无头浏览器 | HTML 画 + 截图 | 排版能力强 | 要 Playwright/Chromium，字体加载坑多 |
| **Pillow 直算像素** | Python 算每个像素 | **零重依赖、完全可控、启动快** | 没有现成缓动/排版库，都要自己写 |

002 选第四种。原因很实际：本机没有 numpy / manim / LaTeX，也不想为一条 44 秒的片装一整套 Chromium。
Pillow 足够画矢量感的 2.5D 几何：多边形、圆弧、虚线、发光（高斯模糊叠加）。

> 判断标准：**你要讲的东西是「结构」还是「镜头」？**
> 讲结构（几何、拓扑、数据流）→ Pillow 够用且最省心；讲镜头（3D 运镜、粒子）→ 上 Manim 或 Blender。

---

## 2. 三条禁令：确定性渲染的根

这四条纪律决定了后面所有设计，先立规矩再写代码：

1. **不读系统时间**。`t` 只能来自帧号：`t = i / fps`。代码里出现 `time.time()` 就是 bug。
2. **不用无种子随机**。要么不用随机，要么 `rng = random.Random(CONFIG["seed"])`。
   背景光斑位置是公式算的（`seed=20261123`），不是每次抽。
3. **渲染时不联网**。字体、图标、音频素材全部本地；一旦联网，同参数可能出不同像素。
4. **不依赖外部滤镜做转场/包络**。本机 ffmpeg 是精简构建，连 `fade` 滤镜都没有；
   转场在 `frame(t)` 里做两次渲染混合，包络在采样点里乘。

代价与收益：

| 收益 | 说明 |
|---|---|
| 可 diff | 改一版，`git diff` 看的是参数与文案，不是一堆二进制 |
| 可缓存 | 帧文件按 `(参数, t)` 命名，改一镜只重渲那一段 |
| 可并行 / 可乱序 | `frame(t)` 不依赖前一帧，`--frames 300 400` 随便切 |
| 可断点续渲 | 崩了接着渲，不用从头 |

---

## 3. 最小工程结构

```
002-brep-untrim-explainer/
├── storyboard.py     ← 唯一数据源：PALETTE / CONFIG / BEATS / AUDIO
├── render.py         ← frame(t)：画一帧
├── audio.py          ← pad_sample(t) + 事件叠加：合成音轨
├── encode.py         ← 拼帧 + 混音 + 校验
├── build_html.py     ← 把同一份数据注入 preview.html
├── frames/           ← 00000.png … 01069.png
├── soundtrack.wav
├── brep_untrim.mp4            （无声，对照用）
└── brep_untrim_with_audio.mp4 （投稿用）
```

数据流只有一条：

```
storyboard.py ──┬── render.py ── frames/*.png ── encode.py ── MP4
                ├── audio.py  ── soundtrack.wav ──┘
                └── build_html.py ── preview.html（同一份 BEATS/AUDIO）
```

**为什么强调「唯一数据源」**：四处各写一份，改一镜时长就会漂移；
一处定义，画面 / 音轨 / 编码 / 预览一起变。这条纪律省下的返工比任何优化都多。

---

## 4. 第一步：写分镜表（`BEATS`）

一个 beat 就是「一个概念 + 一段时间 + 一句字幕」：

```python
BEATS = [
    {
        "id": 2, "scene": "hole_untrim", "dur": 6.0,
        "title": "孔 = 加了一个 inner loop",
        "sub":   "底层曲面一点没坏，所以「取消」就是删掉那个环",
        "lines": ["删 inner loop → 面自己合上", "8 面 → 7 面"],
        "metrics": ("faces", 8, 7, 0),   # 上屏数字随进度滚动
    },
    # …
]
TOTAL_DURATION = sum(b["dur"] for b in BEATS)   # 44.6 s
```

写分镜的四条经验（都是从这条片上踩出来的）：

1. **一镜一个概念**。出现两个概念，观众就掉队；宁可拆成两条片。
2. **3–7 秒一镜**。短于 3 秒来不及读字，长于 7 秒注意力跑掉。
3. **字幕一行 ≤ 22 个汉字**，最多两行。竖排/长句在手机上看就是灾难。
4. **数字必须能追溯**。`8→7`、`233214.16→236607.08` 都要能在实验记录里查到；
   查不到就别上屏，宁可写「示意」。

`beat_at(t)` 把时间翻译成「第几镜 + 镜内进度」，`cumulative_starts()` 给字幕/音轨用的绝对时间表。
这两件事必须只有一处实现，否则字幕和音轨会各自漂移。

---

## 5. 第二步：`frame(t)` —— 一帧的全部秘密

```python
class Renderer:
    def frame(self, t):          # 返回 PIL.Image，纯函数：同样的 t 永远同样一帧
        beat, u = SB.beat_at(t)  # u = 镜内进度 0..1
        ...
```

### 5.1 投影：不用 3D 库，用等轴测公式

```python
# u=(x−y)·cos30°, v=(x+y)·sin30°−z ，z 向上
def proj(x, y, z):
    return (cx + (x - y) * 0.866 * k,
            cy + (x + y) * 0.5 * k - z * k)
```

立方体 8 个顶点各算一次，按「背面 → 正面」排序贴四边形即可。
不需要矩阵库，也不需要光照；深色底 + 描边 + 半透明填充就有「技术感」。

### 5.2 绘制顺序（错了就漏元素）

```
背景（渐变 + 网格 + 暗角）
 → 底层曲面（比盒子大的平行四边形 + 虚线边，填充 0.045）
 → 实体各面（背面先、正面后）
 → 边（描边 1.5–2 px）
 → 特征（孔 = 参数化椭圆；圆角 = 4 条顶边弧带）
 → 上屏数字 / 标签
 → 标题字幕（title 镜不画底部字幕，避免重复）
```

### 5.3 孔怎么画

参数化圆（64 点）投影成椭圆；「删掉孔」的动画就是把半径从 1 缩到 0：

```python
pts = [proj(cx + r*cos(a), cy + r*sin(a), z) for a in angles]
# shrink: 1 → 0，配合内环颜色从橙渐变回青，观众就读懂「环被抹掉、面自己合上」
```

### 5.4 转场不要交给 ffmpeg

```python
def mix(a, b, u):                 # 两张 PIL 图按 u 混合
    return Image.blend(a, b, ease(u))
```

在 `frame(t)` 的镜尾 0.4 秒里同时渲染前后两镜再 blend。
好处：任意帧可独立重算；坏处：每帧多一次渲染（本机 0.18 s → 0.26 s，可接受）。

### 5.5 中文字体：等宽字体的「代码感」只在纯 ASCII 时成立

Consolas 没有中文字形，直接画就是 `□ / faces`。做法：

```python
def label(...):
    f = MONO if all(ord(c) < 128 for c in s) else YAHEI
```

代价是中英混排时字宽不一致，所以「数字 + 中文单位」要分段画，别塞进一个字符串。

---

## 6. 第三步：先渲样帧，再出拼图，最后才全片

这是**最省钱的一条流程纪律**。002 的构图返工有 6 轮，如果每轮都全片渲，就是 6 × 3.2 分钟。

```bash
python render.py --probe 0 8 25 32      # 只出 4 张样帧（秒）
python render.py --frames 700 760       # 只重渲某一段（约 60 帧 / 11 秒）
python render.py --scale 0.5            # 半尺寸快速小样
python encode.py --contact              # 八镜拼图 contact_sheet.png
```

规矩：**没看拼图不许 `--encode`**。八镜的构图问题（字压几何、元素糊成一片、孔消失太快）
在一张拼图里一眼就能看见，不必等整片出来再逐帧找。

---

## 7. 第四步：`sample(t)` —— 声音也是纯函数

### 7.1 只用标准库

```python
import wave, array, math     # 不需要 numpy / pydub / librosa
```

16-bit PCM 就是一个 `array('h')`，每个采样点乘 32767 写进 wav。够了。

### 7.2 三层结构（v3 配乐的实际做法）

| 层 | 做法 | 关键参数 |
|---|---|---|
| 和弦底座 | 当前和弦最低 3 音，每音 3 个固定 detune 正弦 | `Dmaj9–Bm9–Gmaj7♯11–Asus2`，8 s/和弦，`pad_level 0.06` |
| 琶音 | 60 BPM 八分音符，只在「积累」段 | 0.5 s 一颗，随能量弧渐强 |
| 离散事件 | 7 个（cue×5 / thud×1 / chord×1） | 最小间隔 3.54 s，`atk` 20–30 ms |

### 7.3 三个必须写对的公式

```python
# ① 包络：从 0 起、回 0 收，否则就是爆音（click）
env = (1 - math.exp(-tt / atk)) * math.exp(-tt / dec)

# ② 一阶高通幅度响应：80 Hz 以下压掉，解决「低频嗡鸣」
hp = f / math.sqrt(f * f + fc * fc)

# ③ 同调：事件频率从 MIDI 换算，别手写 Hz，否则和和弦打架
def midi_hz(m): return 440.0 * (2.0 ** ((m - 69) / 12.0))
```

### 7.4 立体声不是「复制两遍」

左右用不同抽头的房间回声（`L 83/191/370 ms`、`R 97/211/389 ms`），
声音才有宽度；直接复制双声道听起来还是 mono。

### 7.5 先跑 `--info`，再出 WAV

```bash
python audio.py --info
# events 7 | density 0.157/s | min_gap 3.54s
# atk_ms [20,25,30] | chord_tone_hits 6/7 | key_changes 5 | chord_loop 32.0s
```

这 6 个数字是**可计算的听感代理**，能在 0.2 秒内排掉「太密、太尖、不同调、音高乱飘」四类问题。
002 的教训是：v2 只验了 `peak/rms/哈希/AAC 流存在`，全过，但真人一听就「怪」——
因为那些指标测的是信号完整性，不是音乐性。

---

## 8. 第五步：编码（细节全是坑）

```bash
python encode.py --audio
```

内部实际执行（简化）：

```bash
ffmpeg -framerate 24 -i frames/%05d.png -i soundtrack.wav \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -ar 48000 -shortest \
  -movflags +faststart brep_untrim_with_audio.mp4
```

三个必须知道的点：

1. **`-pix_fmt yuv420p`**：不写的话某些播放器/B 站会黑屏或偏色。
2. **`-shortest`**：帧是 1070 张 = 44.583 s，音轨 44.60 s，取短的收尾，否则末尾静音拖尾。
3. **本机有两套 ffmpeg，能力不同**：`KeyShot Studio\bin` 是精简构建（0 个音频编码器），
   `KS2024\bin` 是完整构建。`find_ffmpeg(need_audio=True)` 会实测 `-encoders` 再挑，
   **不要凭路径猜**。

编码完必须校验，别信「命令没报错」：

```bash
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate,channels \
        -show_entries format=duration,size -of default=noprint_wrappers=1 brep_untrim_with_audio.mp4
# video h264 1600x900 24/1 | audio aac 48000 2ch | duration 44.583333
```

---

## 9. 第六步：预览页（可选，但强烈建议）

`build_html.py` 把 `BEATS / AUDIO / 事件表 / 音色表` 序列化成一个内联 JSON，
浏览器用 Canvas 重画同一套几何、用 Web Audio 复现同一张事件表。

两个坑：

- **`KIND` 必须是 dict**。tuple 序列化成 JSON 会变数组，浏览器读 `K.dur` 是 `undefined`。
- **`AudioContext` 需要用户手势解锁**。初始状态设成「暂停」，按钮写「播放」，
  点一下同时启动画面、解锁声音、重置进度；否则会出现「提示点播放，按钮却显示暂停」的矛盾。

控件收敛到 3–6 个（用户长期偏好）：配乐强度 / 张力→解决幅度 / 空间感 / 起音柔和度 /
提示音密度 / 低频量。控件太多等于没有控件。

---

## 10. 第七步：自检清单（发布前逐条过）

**画面**
- [ ] 八镜拼图看一遍：字没压几何、没出画、没有 `□`
- [ ] 上屏数字与旁白/字幕一致（8→7、11→10、体积变化）
- [ ] 镜尾转场没有闪黑/闪白

**声音**
- [ ] `python audio.py --info` 六项指标都在合理区间（密度 < 0.3/s、最小间隔 > 1 s、atk ≥ 20 ms）
- [ ] 不削波；`ffprobe` 确认 AAC **双声道**
- [ ] **完整听一遍**（不是只听 10 秒）

**确定性**
- [ ] 连跑两次 `audio.py`，WAV sha256 一致
- [ ] 任意两帧重渲，像素一致（`--probe` 对比）

**交付**
- [ ] 用的是带音轨的 `brep_untrim_with_audio.mp4`
- [ ] 封面、字幕、简介、标签按 `PUBLISH_bilibili.md` 配好

---

## 11. 第八步：发布（物料也是代码生成）

| 物料 | 生成方式 | 文件 |
|---|---|---|
| 封面 | `python make_cover.py`（从 `frames/00700.png` 合成，1146×717） | `cover_bilibili.png` |
| 字幕 | `python make_srt.py`（用 `narration.md` 的文案与时间码） | `brep_untrim.srt` |
| 投稿文案 | 手写（标题/简介/标签/置顶评论/检查清单） | `PUBLISH_bilibili.md` |

封面也遵守三条禁令：只用既有帧 + 程序绘制，不引入外部素材、不联网。
好处是以后改标题只改一行字，不用重新找人做图。

---

## 12. 换成你自己的题目：只改三处

1. **`storyboard.BEATS`**：把 8 镜换成你的 5–8 镜，每镜写 `scene / dur / title / sub / lines / metrics`
2. **`render.py` 的 scene 分派**：每个 `scene` 对应一个绘制方法；几何换掉，投影和排版骨架保留
3. **（可选）`storyboard.AUDIO`**：想换情绪就改 `progression / arc / events`，不用碰 `audio.py`

不用改：`encode.py`、`build_html.py`、`preview.html`、`make_cover.py`、`make_srt.py`。

**换题目时的第一条建议**：先把「一句话结论」写死（例如「孔是边界，圆角是实体」），
再倒推需要哪几镜才能让人相信这句话。反过来先想画面，最后一定会讲不清。

---

## 13. 踩坑目录（都是真踩过的）

| 症状 | 原因 | 解 |
|---|---|---|
| 中文变成 `□ / faces` | Consolas 无中文字形 | 检测 CJK 切微软雅黑；中英混排分段画 |
| 片头标题出现两次 | 居中大标题 + 底部字幕同时画 | title 镜不画底部字幕 |
| 标签压住几何 | 中文字宽估算偏小 | 先挪到空白区，再拆两行；留 4–8 px 余量 |
| 底层曲面和盒子顶面糊成一片 | 两者都是半透明青色四边形 | 底层改虚线边框 + 填充降到 0.045 |
| 孔消失太快看不见中间态 | `shrink` 区间太窄 | 0.40–0.72 → 0.45–0.85 |
| `FileNotFoundError`（路径明明存在） | Git Bash 的 `/c/...` 传给原生 Windows Python | 一律用工作目录内相对路径 |
| ffmpeg 报 `No such filter: fade` | 用了 `--disable-everything` 的精简构建 | 实测 `-encoders` 选完整构建；转场/包络自己算 |
| 浏览器读 `K.dur` 是 undefined | tuple 序列化成 JSON 数组 | 音色表用 dict |
| 预览页按钮显示「暂停」却没有声音 | `AudioContext` 需手势解锁，初始 `playing=true` | 初始暂停 + 点击解锁 |
| 想投 1080P 但成片是 1600×900 | 渲染分辨率就是 1600×900 | 改 `CONFIG.width/height` 到 1920×1080 重渲（布局不用改） |
| 音频「指标全过但听着怪」 | 只验信号完整性，没验音乐性 | 先跑 `--info` 六指标；固定调性 + 情绪弧 + 少事件 |

---

## 14. 成本账（本机实测，供你估算）

| 环节 | 成本 |
|---|---|
| 单帧渲染 | ≈ 0.18 s（1600×900，Pillow） |
| 全片 1070 帧 | ≈ 3.2 min |
| 音轨合成 | ≈ 2.8 s |
| 编码 + 整片解码校验 | 秒级 × 2（无声 + 带音轨） |
| 八镜拼图自检 | ≈ 1.5 s |
| **真正贵的** | **构图返工**（6 轮）、**环境试错**（4 轮） |

结论：算力不是瓶颈，**「看不见就想不出来」才是**。所以把「先样帧、再拼图、后全片」
做成硬流程，比任何渲染优化都值钱。

---

## 15. 最小可运行骨架（60 行，抄了就能跑）

```python
# mini.py —— 一条 6 秒、两镜、带声音的最小片
import math, os, subprocess, wave, array
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 960, 540, 24
BEATS = [("一镜：一个盒子", 3.0), ("二镜：盒子上多了一个孔", 3.0)]
TOTAL = sum(d for _, d in BEATS)
FONT = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 42)

def frame(t):
    im = Image.new("RGB", (W, H), (18, 20, 26))
    d = ImageDraw.Draw(im)
    # 进度 → 当前镜
    acc, idx, u = 0.0, 0, 0.0
    for i, (_, dur) in enumerate(BEATS):
        if t < acc + dur:
            idx, u = i, (t - acc) / dur
            break
        acc += dur
    # 盒子：等轴测投影，只画三个可见面（背面不画 = 自动消隐）
    cx, cy, s = W / 2, H / 2 + 60, 96
    def iso(x, y, z):
        return (cx + (x - y) * .866 * s, cy + (x + y) * .5 * s - z * s)
    top   = [iso(-1, -1, 1), iso(1, -1, 1), iso(1, 1, 1), iso(-1, 1, 1)]
    left  = [iso(-1, -1, 0), iso(-1, 1, 0), iso(-1, 1, 1), iso(-1, -1, 1)]
    right = [iso(1, -1, 0), iso(1, 1, 0), iso(1, 1, 1), iso(1, -1, 1)]
    for pts, fill in ((left, (28, 42, 56)), (right, (22, 34, 46)), (top, (44, 70, 90))):
        d.polygon(pts, fill=fill, outline=(120, 200, 230))
    # 二镜：孔 = 顶面上的一个环，半径随进度收缩到 0
    if idx == 1:
        r = 0.42 * (1 - u)
        ring = [iso(r * math.cos(a), r * math.sin(a), 1)
                for a in (k / 48 * 2 * math.pi for k in range(49))]
        d.line(ring, fill=(255, 138, 40), width=3, joint="curve")
    d.text((48, H - 88), BEATS[idx][0], font=FONT, fill=(240, 242, 246))
    return im

def sample(t):
    # 两个音：盒子入场 + 孔消失（都从 MIDI 换算，同调）
    s = 0.0
    for start, midi in ((0.06, 69), (3.06, 74)):
        tt = t - start
        if 0 <= tt < 2.0:
            f = 440 * 2 ** ((midi - 69) / 12)
            env = (1 - math.exp(-tt / 0.02)) * math.exp(-tt / 0.45)
            s += 0.25 * env * math.sin(2 * math.pi * f * tt)
    return s

def main():
    os.makedirs("mini_frames", exist_ok=True)
    for i in range(int(TOTAL * FPS)):
        frame(i / FPS).save("mini_frames/%05d.png" % i)
    # 音轨
    sr = 48000
    n = int(TOTAL * sr)
    pcm = array.array("h", (int(max(-1, min(1, sample(i / sr))) * 32767) for i in range(n)))
    with wave.open("mini.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    # 编码（换成你本机可用的 ffmpeg）
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", "mini_frames/%05d.png",
                    "-i", "mini.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", "mini.mp4"], check=True)

main()
```

跑通它你就掌握了全部骨架：`frame(t)`、`sample(t)`、逐帧、封装。
剩下的只是「画得更准、说得更清」。

---

## 16. 验收口径：四级，别跳级

| 级别 | 标准 | 002 的状态 |
|---|---|---|
| 能跑 | 一条命令出片，无报错 | ✅ |
| 能看 | 拼图里八镜构图成立、无豆腐块 | ✅ |
| 能听懂 | 不看字幕也能说出结论 | ✅（真人反馈「画面挺不错」） |
| 能复现 | 换机器、换时间，同参数同像素 | ✅（sha256 一致） |
| 能打动 | 真人听完觉得「啊，原来如此」 | ⚠️ **未闭环**：配乐 v3 已重做，仍需真人听感验证 |

最后一级不写「已完成」，因为它是主观的，而且只有你能判。
如果你听完觉得还差点意思，改 `storyboard.py:AUDIO` 的数值即可，画面一行都不用动——
这正是把声音做成参数而不是素材的好处。
