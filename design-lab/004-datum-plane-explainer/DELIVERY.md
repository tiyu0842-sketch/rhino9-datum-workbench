# 004 · 基准面视频交付说明

> 生成时间：2026-11-25 00:00–00:08（用户临时改口"先生成视频并配音"，提前执行；
> 渲染链本身不联网，全程离线完成，零付费）。
> **v2 优化（2026-11-25 09:45–09:55）**：按 Remotion 对标做了三项改动并全片重渲——
> ① `primitives.py` 动效库（6 个基元抽成可跨片复用纯函数）；
> ② 拍点呼吸脉冲（storyboard `BPM=60 / beat_pulse()`，每拍起点几何层轻微放大再回落，
>    字幕/HUD 不缩放，画面"跟着音乐呼吸"）；
> ③ SPEC 补风格锚点 + AI 味禁令（粒子/紫渐变/随机3D/伪科技装饰）+ 锁放清单。
> 音轨沿用晓晓女声版 `narration_edge.wav`，未重合成。v2 渲染 4m33s（脉冲 resize 比 v1 慢约 1 分钟）。
> v2 的两个 mp4 落盘时间为 09:51，已被 v3 覆盖。
>
> **v3 重生成（2026-11-25 10:55–11:03）**：按两个 B 站对标视频（BV1wvJB6aEp5 / BV1CSHS6BEQr）再迭代一版——
> ① **叙事动效三件套**：流程传递（switch：传递线走完 DP_02 才响应）、
>    画中画连续移动（normalview：同一块基准面从 Top 滑到法向视图）、stagger 逐个弹入；
> ② **修 v2 验收的 4 处构图硬伤**：棕面 `fill_alpha` 0.22 → 0.50/0.72 + 1px 亮边 `#D9A45E`、
>    几何 `scale` 5.2 → 6.8、标题镜移到中右形成引导线、背景提亮（meanL 28 → 35.5）；
> ③ **align 镜固定视角**（yaw 摆动到 45° 会把基准面压成细线）；
> ④ **修 PIL RGBA 坑**：`ImageDraw` 不做 alpha 混合，`fill=(r,g,b,0)` 是"擦除"不是"不画"，
>    `Renderer.poly/dashed/label` 加 alpha 门后 switch 镜不再只剩两个小三角。
> 全片重渲 1500 帧（4m49s）+ align 段局部重渲 156 帧。
> **两个 mp4 的落盘时间是 11:03，目录下就是最新版。**

## 成片（可直接用）

| 文件 | 规格 | 用途 |
|---|---|---|
| **`datum_plane_with_audio.mp4`** | 1920×1080 / 24 fps / H.264 High + **AAC 48 kHz stereo（中文旁白）** | **投稿用成片（v3）**，4.89 MB |
| `datum_plane_master_1080p.mp4` | 同画面，**无音轨** | 剪辑母版（v3），3.66 MB |
| `clips/00_title.mp4` … `09_restore.mp4` | 10 段，各带 ±0.4 s 余量，stream copy 无损 | 剪辑核心：拖拽重排、单独重渲 |
| **`narration_edge.wav`** | 48 kHz / 16-bit / stereo / 62.5 s | **v2 / v3 成片实际使用的音轨**（edge-tts 晓晓女声） |
| `narration_mix.wav` | 同规格 | v1 SAPI 版混音，仅留档对比，v2 / v3 均未使用 |
| `soundtrack.wav` | 同规格，纯配乐 | 无旁白版音轨，可自行混 |
| `datum_plane.srt` | 10 条，按镜头边界对齐 | CC 字幕 |
| `cover_bilibili.png` | 1146×717 | B 站封面（代码合成，无外部素材） |
| `contact_sheet.png` | 1550×2325，10 镜 u≈0.65 帧 | 剪辑前扫一眼定位镜头 |
| `verify_v3/contact_sheet_v3.png` | 1520×2135 | v3 验收拼图（10 镜） |

## 配音怎么做的（可复现）

- **v1（已弃用，仅留档）**：Windows SAPI `Microsoft Huihui Desktop`，`win32com` 离线合成
  （`narration.py`，rate +2）→ `mix_audio.py` 混成 `narration_mix.wav`。机械感明显，用户否决。
- **v2 / v3（成片实际使用）**：`edge-tts` 神经语音 `zh-CN-XiaoxiaoNeural`（晓晓女声），
  `RATE="+8%"`，由 `edge_narration.py` 逐句合成 → `mix_edge.py` 混成 `narration_edge.wav`。
  **本机已锁定女声，男声不再使用**（用户反馈"男声太难听了"）。
  安装走阿里镜像：`python -m pip install edge-tts -i https://mirrors.aliyun.com/pypi/simple/`，
  只需国内网、无需翻墙；**只有合成音轨这一步需要联网，渲染/编码链全程离线**。
- **对齐**：按 `storyboard.cumulative_starts()` 把第 i 句放在第 i 镜起点 +0.25 s。
- **混音原则**：先压配乐到 0.30，再叠旁白 0.85/0.90；顺序反了会把人声一起压低（v1 踩过）。
- **编码**：`encode.py` 显式用 `narration_edge.wav` 作 AAC 音源，与 62.5 s 画面对齐
  （v2 曾误指向 v1 的 SAPI 混音，v3 已修正为该行硬编码）。

## 复现命令

```bash
python audio.py --info        # 配乐指标自检
python audio.py               # soundtrack.wav（62.5s stereo）
python edge_narration.py      # vo_edge/vo_00..09.wav（需联网 + edge-tts）
python mix_edge.py            # narration_edge.wav ← v2 / v3 成片音轨
python render.py --probe 0 2 39 51   # 样帧自检
python render.py              # 1500 帧 @1920x1080（v3：叙事动效 + 提亮构图 + 固定 align 视角）
python encode.py --all        # 母版 + 带旁白成片 + contact sheet
python make_srt.py && python make_cover.py && python make_clips.py
python verify_v3.py           # 只读验收：抽帧/拼图/旁白能量/画面量化 → verify_v3/
```

> v1 的 SAPI 路径 `narration.py --rate 2` → `mix_audio.py` 仍可跑，仅用于对照，不再进成片。

依赖：Python + Pillow 13 + edge-tts（仅音轨合成）+ Windows 中文字体（msyhbd/msyh/consolab）+
ffmpeg `KS2024\bin\ffmpeg.exe`（完整构建，有 aac）。
注：本机 `ffprobe.exe` 缺失，`verify_v3.py` 的"流规格"一节会跳过；
流规格改用 `ffmpeg -i` 读取，其余验收项不受影响。

## 核验记录

- v1 渲染：1500 帧，`RENDER_DONE`，3m16s；整片解码 `frame=1500`、`exit=0`。
- v1 流规格：H.264 yuv420p 1920×1080 24fps / AAC LC 48000 Hz stereo 162 kb/s。
- **v2 重渲**：1500 帧全部重算并重新编码，09:51 落盘；沿用 v1 已验证的编码参数，
  **未重跑整片解码校验**（如需可补一条 `ffmpeg -v error -i ... -f null -`）。
- 封面：中文正常（曾因等宽字体渲染成方块，已改雅黑）；标题残影已压掉。
- contact sheet：10 镜全部可读，无空白/纯黑。
- **v3 重渲**：1500 帧全量重算（4m49s）+ align 段 396–552 共 156 帧局部重渲，
  11:03 落盘并重新编码；`encode.py` 音源显式指向 `narration_edge.wav`。
- **v3 编码校验**：`VERIFY exit=0 audio_stream=True`（ffmpeg 整片解码无错）。
- clips / SRT / 封面 / contact sheet 已按 v3 帧重新生成。

### v2 画面验收（2026-11-25 10:2x，`verify_v2.py` + `analyze_frames.py`）

- 流规格：62.50 s / 1920×1080 / 24 fps / H.264 High 434 kb/s / AAC 48 kHz stereo 160 kb/s。
- 逐镜旁白：10/10 镜都有，RMS −26.0 ～ −28.9 dBFS，峰值 0.370（无削波）。
- 画面：10 镜全抽帧，无空白/纯黑，中文无方块、无裁切。
- **构图缺陷（量化）**：棕色基准面 `#B08246` 的像素占比只有 **0.00–0.35%**（9 镜），
  在深底 + 暗角下几乎不可见；标题镜几何落在右下角，与左上文字断开。
  结论：**技术交付合格，视觉说服力不足，建议修一版再投稿**。
  修法：`plane_alpha` 0.55→0.78 且加 1px 亮边 `#D9A45E`；几何整体放大 1.3–1.4×；
  标题镜几何移到中右形成引导线；背景网格提亮一档。

### v3 画面验收（2026-11-25 11:0x，`verify_v3.py`，只读复跑确认）

- 流规格（`ffmpeg -i`）：62.50 s / 1920×1080 / 24 fps / **H.264 High 489 kb/s** /
  AAC LC 48000 Hz stereo 160 kb/s（总 655 kb/s）。
- 逐镜旁白：10/10 镜都有，RMS −26.0 ～ −28.9 dBFS，峰值 0.370（无削波），**无静音镜**。
- 画面量化（u≈0.65 抽帧，4×4 抽样；brown% 判据 `is_brown()` 下限 r≥85，
  避免把 `fill_alpha=0.50` 混合后 r≈99 的面整片排除）：

| 镜 | brown%（v2 → v3） | meanL | content% |
|---|---|---|---|
| 00 title | 0.00 → **2.67** | 36.4 | 24.10 |
| 01 pain | 0.35 → 0.07 | 33.8 | 24.85 |
| 02 define | 0.00 → **5.40** | 36.4 | 25.84 |
| 03 align | 0.00 → 0.61 | 34.5 | 25.63 |
| 04 normalview | 0.00 → 0.42 | 30.9 | 17.22 |
| 05 switch | 0.00 → **1.16** | 35.5 | 28.17 |
| 06 alias | 0.00 → 0.35 | 47.3 | 36.84 |
| 07 lock | 0.11 → 0.27 | 33.6 | 24.85 |
| 08 hide | 0.04 → 0.21 | 33.1 | 24.52 |
| 09 restore | 0.00 → 0.01 | 33.7 | 21.95 |

- **结论**：棕面全片均值 0.05% → **1.12%**（max 5.40%），整体 meanL 28.0 → **35.5**，
  v2「主角在画面里等于不存在」的硬伤已修好；title / define / switch 三镜提升最明显。
  align 镜固定视角后不再被压成细线，define 镜 A/B/C 三点改到面之后绘制，不再被盖住。
- **诚实边界**：仍有 6 镜 brown<0.5%（pain / normalview / alias / lock / hide / restore），
  这些镜叙事上本就不展示基准面（讲痛点、讲操作、讲锁定/隐藏/恢复），低占比是分镜设计、
  不是渲染缺陷；若要「每镜都有棕面」需另改分镜，未做。

## 诚实边界

1. 画面是代码算的示意几何（等轴测投影 + 2D UI 面板），不是 Rhino 视口录屏。
2. 中文旁白是 edge-tts 晓晓女声（神经语音），**真人听感未验收**；v1 的 SAPI 机械版已弃用。
   不满意可改 `edge_narration.py:VOICE` 重合成，或用真人录音直接替换 `narration_edge.wav`。
3. 配乐代理指标（`audio.py --info`）不等于"好听"，需真人听一遍。
4. Remotion 对标已做**文字整理版**（BV 号 + 动效清单 + 拍点呼吸公式），
   但外网视频源、YouTube/Sider 自动总结、百度网盘 AI 导图因外网/登录限制未做；
   **未逐帧看 B 站视频**，v3 改动基于笔记与文字整理，不是对原片的像素级复刻。
5. GitHub 上传仍卡 GitHub App 403 + 外网，与视频独立；B 站投稿包 `PUBLISH_bilibili.md` 待补。
6. v3 验收是代码量化（像素占比 / 亮度 / 音频能量），**真人观感仍未验收**。

哈希（sha256 前 24 位，2026-11-25 11:05 重算，对应 v3 文件）：
- 成片 `datum_plane_with_audio.mp4` **4a69d826f0b3ef08da748456**（5,122,584 B / 4.89 MB）
- 母版 `datum_plane_master_1080p.mp4` **50d239dc997522937831ac66**（3,839,763 B / 3.66 MB）
- 晓晓音轨 `narration_edge.wav` `4d69b0fb1f15a329b991bc78`（沿用 v2，未重合成）
- 封面 `cover_bilibili.png` `607988968bab588d239e9ae8`
- 字幕 `datum_plane.srt` `b014c6a4da51ff20ec886636`
- v2 留档哈希（便于对照）：母版 `45112b542bf38bf14f278f97` / 成片 `8b045c9e4d952a62128f09d6`
- v1 混音（留档）`d6402569b0ae841da8013407`
