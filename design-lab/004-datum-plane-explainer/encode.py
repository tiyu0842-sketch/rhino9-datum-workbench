# -*- coding: utf-8 -*-
"""
encode.py —— 帧序列（+ 音轨）→ MP4，外加关键帧 contact sheet 自检

用法：
    python encode.py --contact      # 每镜取一帧拼九宫格，先看构图再出片
    python encode.py --encode       # 编码无声版 brep_untrim.mp4
    python encode.py --audio        # 编码带音轨版 brep_untrim_with_audio.mp4
    python encode.py --all          # 三个都做
    python encode.py --audio --narration path.wav   # 再叠一层人声旁白

为什么不依赖 ffmpeg 滤镜做转场 / 包络：
    本机有两个 ffmpeg，能力不同，不能凭印象选：
      KeyShot Studio/bin/ffmpeg.exe —— --disable-everything 精简构建，
          只有 scale / palettegen / paletteuse，无 fade、无任何音频编码器。
      KS2024/bin/ffmpeg.exe —— 完整构建，有 aac / libmp3lame / pcm_s16le
          与 amix / afade / volume。
    所以画面叠化在 render.py 的帧内算、音频包络在 audio.py 的采样点里算，
    编码器只负责封装；任意帧 / 任意采样点都能独立重算，可乱序并行。
    find_ffmpeg(need_audio=True) 会实测 -encoders 再挑，不写死某一台机器的路径。
"""

import argparse
import os
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(_HERE, "frames")
OUT = os.path.join(_HERE, "datum_plane_master_1080p.mp4")
OUT_AUDIO = os.path.join(_HERE, "datum_plane_with_audio.mp4")
# v2 起成片音轨改用 edge-tts 晓晓女声混音（mix_edge.py 产出）。
# v1 的 narration_mix.wav 是 SAPI 慧慧机械版，仅留档，绝不能进成片。
WAV = os.path.join(_HERE, "narration_edge.wav")
NARRATION = os.path.join(_HERE, "__unused_narration.wav")  # 不自动叠；旁白已在 WAV 里
SHEET = os.path.join(_HERE, "contact_sheet.png")
FONTDIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")


def _has_audio_encoder(ffmpeg):
    """实测编码器能力，而不是靠路径猜。精简构建 -encoders 里没有 aac。"""
    try:
        p = subprocess.run([ffmpeg, "-hide_banner", "-encoders"],
                           capture_output=True, text=True, timeout=20)
        txt = (p.stdout or "") + (p.stderr or "")
        return " aac " in txt or "\naac " in txt or "aac " in txt
    except Exception:
        return False


def find_ffmpeg(explicit=None, need_audio=False):
    """按 顺序找编码器：显式参数 → 环境变量 → PATH → 常见安装路径。
    need_audio=True 时跳过没有 aac 的精简构建。
    不写死用户目录，保证仓库里的脚本在别人机器上也能跑。"""
    cands = [
        explicit,
        os.environ.get("FFMPEG"),
        shutil.which("ffmpeg"),
        r"C:\Program Files\KS2024\bin\ffmpeg.exe",       # 完整构建，优先
        r"C:\Program Files\KeyShot Studio\bin\ffmpeg.exe",  # 精简构建
        r"C:\ffmpeg\bin\ffmpeg.exe",
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
    ]
    for c in cands:
        if c and os.path.isfile(c):
            if need_audio and not _has_audio_encoder(c):
                continue
            return c
    raise SystemExit("找不到%sffmpeg。用 --ffmpeg 指定完整路径，或把 ffmpeg 加进 PATH。"
                     % ("带音频编码器的 " if need_audio else ""))


def contact_sheet(cols=2, cell_w=760, tag_h=26):
    """每个镜头取 u≈0.65 的一帧，拼成一张对照图。
    先说构图再渲染，是这类代码视频最省时间的一步：一眼就能看出哪镜空了、哪镜挤了。"""
    from render import Renderer

    r = Renderer()
    picks = []
    for b in SB.BEATS:
        t0 = sum(x["dur"] for x in SB.BEATS[:b["id"]])
        picks.append((t0 + b["dur"] * 0.65, b))

    cell_h = int(cell_w * 9 / 16)
    rows = (len(picks) + cols - 1) // cols
    gap = 10
    W = cols * cell_w + (cols + 1) * gap
    H = rows * (cell_h + tag_h) + (rows + 1) * gap
    sheet = Image.new("RGB", (W, H), (18, 20, 26))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype(os.path.join(FONTDIR, "msyh.ttc"), 17)
    except Exception:
        f = ImageFont.load_default()

    for i, (t, b) in enumerate(picks):
        img = r.frame(t).resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        cx = gap + (i % cols) * (cell_w + gap)
        cy = gap + (i // cols) * (cell_h + tag_h + gap)
        d.text((cx, cy), "#%d  %s  t=%.1fs" % (b["id"], b["scene"], t),
               font=f, fill=(200, 205, 215))
        sheet.paste(img, (cx, cy + tag_h))

    sheet.save(SHEET)
    print("CONTACT_SHEET", SHEET, sheet.size)
    return SHEET


def encode(ffmpeg, fps=24, out=OUT, crf=18, preset="medium",
           start=0, count=None, audio=False, narration=None):
    pattern = os.path.join(FRAMES, "%05d.png")
    if not os.path.isfile(os.path.join(FRAMES, "%05d.png" % start)):
        raise SystemExit("帧序列缺失：%s 不存在，先跑 render.py" % pattern)
    if audio and not os.path.isfile(WAV):
        raise SystemExit("音轨缺失：%s 不存在，先跑 audio.py" % WAV)

    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "warning",
           "-framerate", str(fps), "-start_number", str(start), "-i", pattern]
    has_narr = bool(audio and narration and os.path.isfile(narration))
    if audio:
        cmd += ["-i", WAV]
        if has_narr:
            cmd += ["-i", narration]
    if count:
        cmd += ["-frames:v", str(count)]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-pix_fmt", "yuv420p"]
    if audio:
        if has_narr:
            # 程序化音轨 100%，旁白 85%，以第一条流（音轨）的时长为准
            cmd += ["-filter_complex",
                    "[1:a]volume=1.0[a1];[2:a]volume=0.85[a2];"
                    "[a1][a2]amix=inputs=2:duration=first:dropout_transition=0[a]",
                    "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-map", "0:v", "-map", "1:a"]
        cmd += ["-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest"]
    cmd += ["-movflags", "+faststart", out]

    print("ENCODE", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("ENCODED %s  %.2f MB" % (out, os.path.getsize(out) / 1024 / 1024))
    return out


def verify(ffmpeg, out=OUT, expect_audio=False):
    """整片解码一遍：能解完即结构完好。再从 stderr 里抓 Duration / Video / Audio 行。"""
    p = subprocess.run([ffmpeg, "-hide_banner", "-i", out,
                        "-f", "null", "-"], capture_output=True, text=True)
    tail = (p.stderr or "")
    keep = [ln.strip() for ln in tail.splitlines()
            if ("Duration" in ln or "Video:" in ln or "Audio:" in ln or "frame=" in ln)]
    has_audio = any("Audio:" in ln for ln in tail.splitlines())
    print("VERIFY exit=%s  audio_stream=%s" % (p.returncode, has_audio))
    for ln in keep[-5:]:
        print("  ", ln[:160])
    if expect_audio and not has_audio:
        print("  !! 期望有音轨，但封装结果里没有 Audio 流")
        return False
    return p.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", default=None)
    ap.add_argument("--contact", action="store_true")
    ap.add_argument("--encode", action="store_true")
    ap.add_argument("--audio", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--narration", default=None,
                    help="人声旁白 wav；省略时自动检测同目录 narration.wav")
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()
    do_contact = args.contact or args.all
    do_silent = args.encode or args.all
    do_audio = args.audio or args.all
    if not (do_contact or do_silent or do_audio):
        do_contact = do_silent = do_audio = True

    if do_contact:
        contact_sheet()

    fps = SB.CONFIG["fps"]
    narr = args.narration or (NARRATION if os.path.isfile(NARRATION) else None)
    if narr and not os.path.isfile(narr):
        raise SystemExit("指定的旁白文件不存在：%s" % narr)

    if do_silent:
        ff = find_ffmpeg(args.ffmpeg)
        print("FFMPEG(silent)", ff)
        encode(ff, fps=fps, crf=args.crf, out=OUT, audio=False)
        verify(ff, OUT)

    if do_audio:
        ff_a = find_ffmpeg(args.ffmpeg, need_audio=True)
        print("FFMPEG(audio) ", ff_a, "narration=", bool(narr))
        encode(ff_a, fps=fps, crf=args.crf, out=OUT_AUDIO,
               audio=True, narration=narr)
        verify(ff_a, OUT_AUDIO, expect_audio=True)


if __name__ == "__main__":
    main()
