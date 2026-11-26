# -*- coding: utf-8 -*-
"""
make_clips.py —— 从母版按镜头切出 10 段独立片段（剪辑友好的核心交付）

每段文件名带编号 + scene key，供剪辑软件直接拖拽重排。
带 -0.4s 头 / +0.4s 尾余量（素材范围内），方便剪辑做转场。
用 stream copy（-c copy）不重编码，秒级完成、画质无损。
"""

import os
import subprocess
import shutil

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(_HERE, "datum_plane_master_1080p.mp4")
CLIPS = os.path.join(_HERE, "clips")


def find_ffmpeg():
    for c in [r"C:\Program Files\KS2024\bin\ffmpeg.exe",
              r"C:\Program Files\KeyShot Studio\bin\ffmpeg.exe"]:
        if os.path.isfile(c):
            return c
    return shutil.which("ffmpeg")


def main():
    ff = find_ffmpeg()
    os.makedirs(CLIPS, exist_ok=True)
    fps = SB.CONFIG["fps"]
    for bid, a, b in SB.cumulative_starts():
        beat = SB.BEATS[bid]
        f0 = max(0, int(a * fps) - int(0.4 * fps))
        f1 = min(int(SB.TOTAL_DURATION * fps), int(b * fps) + int(0.4 * fps))
        t0, t1 = f0 / fps, f1 / fps
        out = os.path.join(CLIPS, "%02d_%s.mp4" % (bid, beat["scene"]))
        cmd = [ff, "-y", "-hide_banner", "-loglevel", "error",
               "-ss", "%.3f" % t0, "-to", "%.3f" % t1, "-i", MASTER,
               "-c", "copy", "-avoid_negative_ts", "make_zero", out]
        subprocess.run(cmd, check=True)
        print("CLIP %02d %-11s %.2f-%.2fs  %.2f MB" %
              (bid, beat["scene"], t0, t1, os.path.getsize(out) / 1e6))
    print("CLIPS_DONE", len(SB.BEATS))


if __name__ == "__main__":
    main()
