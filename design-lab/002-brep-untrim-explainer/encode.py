# -*- coding: utf-8 -*-
"""
encode.py —— 帧序列 → MP4，外加关键帧 contact sheet 自检

用法：
    python encode.py --contact      # 每镜取一帧拼九宫格，先看构图再出片
    python encode.py --encode       # 把 frames/00000.png… 编码成 brep_untrim.mp4
    python encode.py --all          # 两个都做

为什么不依赖 ffmpeg 滤镜做转场：
    本机可用的编码器是 KeyShot 附带的 ffmpeg 7.1 精简构建（--disable-everything），
    只保留 scale / palettegen / paletteuse 三个滤镜，没有 fade / overlay。
    所以叠化已经在 render.py 的帧内用两次纯函数渲染算完了，这里只负责封装编码。
"""

import os
import argparse
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(_HERE, "frames")
OUT = os.path.join(_HERE, "brep_untrim.mp4")
SHEET = os.path.join(_HERE, "contact_sheet.png")
FONTDIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")


def find_ffmpeg(explicit=None):
    """按 顺序找编码器：显式参数 → 环境变量 → PATH → 常见安装路径。
    不写死用户目录，保证仓库里的脚本在别人机器上也能跑。"""
    cands = [
        explicit,
        os.environ.get("FFMPEG"),
        shutil.which("ffmpeg"),
        r"C:\Program Files\KeyShot Studio\bin\ffmpeg.exe",
        r"C:\Program Files\KS2024\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    raise SystemExit("找不到 ffmpeg。用 --ffmpeg 指定完整路径，或把 ffmpeg 加进 PATH。")


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


def encode(ffmpeg, fps=24, out=OUT, crf=18, preset="medium", start=0, count=None):
    pattern = os.path.join(FRAMES, "%05d.png")
    if not os.path.isfile(os.path.join(FRAMES, "%05d.png" % start)):
        raise SystemExit("帧序列缺失：%s 不存在，先跑 render.py" % pattern)
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "warning",
           "-framerate", str(fps), "-start_number", str(start), "-i", pattern]
    if count:
        cmd += ["-frames:v", str(count)]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    print("ENCODE", " ".join(cmd))
    subprocess.run(cmd, check=True)
    size = os.path.getsize(out)
    print("ENCODED %s  %.2f MB" % (out, size / 1024 / 1024))
    return out


def verify(ffmpeg, out=OUT, fps=24):
    """没有 ffprobe（KeyShot 只带 ffmpeg），就整片解码一遍：能解完即结构完好。
    再从 stderr 里抓 Duration / Video 行，念出来核时长与分辨率。"""
    p = subprocess.run([ffmpeg, "-hide_banner", "-i", out,
                        "-f", "null", "-"], capture_output=True, text=True)
    tail = (p.stderr or "")
    keep = [ln.strip() for ln in tail.splitlines()
            if ("Duration" in ln or "Video:" in ln or "frame=" in ln)]
    print("VERIFY exit=%s" % p.returncode)
    for ln in keep[-4:]:
        print("  ", ln[:150])
    return p.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", default=None)
    ap.add_argument("--contact", action="store_true")
    ap.add_argument("--encode", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()
    do_contact = args.contact or args.all
    do_encode = args.encode or args.all
    if not (do_contact or do_encode):
        do_contact = do_encode = True

    if do_contact:
        contact_sheet()
    if do_encode:
        ff = find_ffmpeg(args.ffmpeg)
        print("FFMPEG", ff)
        encode(ff, fps=SB.CONFIG["fps"], crf=args.crf)
        verify(ff)


if __name__ == "__main__":
    main()
