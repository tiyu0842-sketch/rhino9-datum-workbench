# -*- coding: utf-8 -*-
"""verify_v3.py —— 004 v3 成片验收（只读，不改片）。

比 verify_v2 多两节：
  5) 画面量化：brown%（基准面像素占比）、meanL、content%
     —— 专门验证 v2 暴露的「主角在画面里等于不存在」是否修好
  6) 与 v2 的逐镜对比表

输出到 004/verify_v3/。
"""
import os
import sys
import json
import math
import array
import wave
import subprocess

from PIL import Image, ImageDraw

FF = r"C:\Program Files\KS2024\bin\ffmpeg.exe"
FP = r"C:\Program Files\KS2024\bin\ffprobe.exe"
D = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\github-release\design-lab\004-datum-plane-explainer"
MP4 = os.path.join(D, "datum_plane_with_audio.mp4")
WAV = os.path.join(D, "narration_edge.wav")
OUT = os.path.join(D, "verify_v3")
os.makedirs(OUT, exist_ok=True)

SHOTS = [(0, 4.0, "title"), (1, 6.0, "pain"), (2, 6.5, "define"), (3, 6.5, "align"),
         (4, 7.0, "normalview"), (5, 6.0, "switch"), (6, 7.0, "alias"),
         (7, 6.0, "lock"), (8, 7.0, "hide"), (9, 6.5, "restore")]

# v2 实测值（analyze_frames.py，u≈0.65 抽帧），用于对比
V2_BROWN = {0: 0.00, 1: 0.35, 2: 0.00, 3: 0.00, 4: 0.00,
            5: 0.00, 6: 0.00, 7: 0.11, 8: 0.04, 9: 0.00}
V2_MEANL = 28.0

GROUND = (0x16, 0x19, 0x20)


def is_brown(c):
    """行业棕在深底上半透明混合后的色域（含 v3 亮边 #D9A45E）。

    r 下限取 85：fill_alpha=0.50 的面混合后 r≈99，阈值卡 100 会把它整片排除
    （004 v3 的 align 镜因此一度只量到 0.19%，其实是判据太严，不是画面没面）。
    """
    return (85 <= c[0] <= 238 and 55 <= c[1] <= 188 and 22 <= c[2] <= 140
            and c[0] > c[1] > c[2])


def stats(p):
    im = Image.open(p).convert("RGB")
    W, H = im.size
    px = im.load()
    n = brown = ls = content = 0
    for y in range(0, H, 4):
        for x in range(0, W, 4):
            c = px[x, y]
            n += 1
            ls += (c[0] * 299 + c[1] * 587 + c[2] * 114) // 1000
            if is_brown(c):
                brown += 1
            if (abs(c[0] - GROUND[0]) + abs(c[1] - GROUND[1])
                    + abs(c[2] - GROUND[2])) > 28:
                content += 1
    return (100.0 * brown / n, ls / float(n), 100.0 * content / n)


print("=== 1. 流规格 ===")
if os.path.exists(FP):
    r = subprocess.run(
        [FP, "-v", "error", "-show_entries",
         "format=duration,size,bit_rate:stream=index,codec_name,codec_type,width,height,"
         "r_frame_rate,sample_rate,channels,duration,bit_rate",
         "-of", "json", MP4], capture_output=True, text=True)
    info = json.loads(r.stdout)
    fmt = info.get("format", {})
    print("  duration=%ss  size=%.2fMB  bitrate=%s" % (
        fmt.get("duration"), int(fmt.get("size", 0)) / 1048576.0, fmt.get("bit_rate")))
    for s in info.get("streams", []):
        print("  [%s] %s  %sx%s  fps=%s  sr=%s ch=%s dur=%s bitrate=%s" % (
            s.get("index"), s.get("codec_name"), s.get("width") or "-",
            s.get("height") or "-", s.get("r_frame_rate") or "-",
            s.get("sample_rate") or "-", s.get("channels") or "-",
            s.get("duration"), s.get("bit_rate")))
else:
    print("  ffprobe 缺失，跳过")

print("\n=== 2. 分镜抽帧（u=0.65）===")
t0 = 0.0
frames = []
for sid, dur, name in SHOTS:
    t = t0 + 0.65 * dur
    p = os.path.join(OUT, "s%02d_%s_%.2fs.png" % (sid, name, t))
    subprocess.run([FF, "-y", "-ss", "%.3f" % t, "-i", MP4, "-frames:v", "1",
                    "-loglevel", "error", p], check=True)
    frames.append((sid, name, t, p))
    print("  shot%02d %-11s t=%6.2fs" % (sid, name, t))
    t0 += dur

print("\n=== 3. 拼 contact sheet（v3）===")
cols, rows, tw = 2, 5, 760
ims = []
for sid, name, t, p in frames:
    im = Image.open(p).convert("RGB")
    im = im.resize((tw, int(im.height * tw / im.width)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 210, 26], fill=(0, 0, 0))
    d.text((6, 7), "shot %02d %s  %.2fs" % (sid, name, t), fill=(255, 255, 255))
    ims.append(im)
cw, chh = tw, ims[0].height
sheet = Image.new("RGB", (cols * cw, rows * chh), (18, 18, 22))
for k, im in enumerate(ims):
    sheet.paste(im, ((k % cols) * cw, (k // cols) * chh))
sp = os.path.join(OUT, "contact_sheet_v3.png")
sheet.save(sp)
print("  -> %s  %dx%d" % (sp, sheet.size[0], sheet.size[1]))

print("\n=== 4. 逐镜旁白能量（narration_edge.wav）===")
with wave.open(WAV, "rb") as w:
    sr, nch, sw, nfr = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
    raw = w.readframes(nfr)
print("  sr=%d ch=%d sampwidth=%d frames=%d dur=%.2fs" % (sr, nch, sw, nfr, nfr / float(sr)))
a = array.array("h")
a.frombytes(raw)
if sys.byteorder == "big":
    a.byteswap()
if nch == 2:
    mono = [(a[i] + a[i + 1]) / 2.0 for i in range(0, len(a) - 1, 2)]
else:
    mono = list(a)

t0 = 0.0
rows_out = []
for sid, dur, name in SHOTS:
    i0, i1 = int(t0 * sr), min(len(mono), int((t0 + dur) * sr))
    seg = mono[i0:i1]
    if seg:
        rms = math.sqrt(sum(x * x for x in seg) / len(seg)) / 32768.0
        peak = max(abs(x) for x in seg) / 32768.0
        db = 20 * math.log10(rms) if rms > 0 else -99.0
        voiced = rms > 0.01
        rows_out.append((sid, name, t0, t0 + dur, rms, db, peak, voiced))
        print("  shot%02d %-11s %5.1f-%5.1fs rms=%.4f (%6.1f dBFS) peak=%.3f voice=%s" % (
            sid, name, t0, t0 + dur, rms, db, peak, "YES" if voiced else "no"))
    t0 += dur
silent = [r[1] for r in rows_out if not r[7]]
print("\n  无旁白镜头: %s" % (silent if silent else "无"))

print("\n=== 5. 画面量化（v3，抽样 4x4）===")
print("  %-6s %-11s %8s %8s %9s   %8s" % (
    "shot", "scene", "brown%", "meanL", "content%", "brown% v2"))
quant = []
for sid, name, t, p in frames:
    br, ml, ct = stats(p)
    quant.append((sid, name, br, ml, ct))
    print("  %-6s %-11s %7.2f%% %8.1f %8.2f%%   %7.2f%%" % (
        sid, name, br, ml, ct, V2_BROWN.get(sid, 0.0)))

brs = [q[2] for q in quant]
mls = [q[3] for q in quant]
print("\n  brown%%: min=%.2f avg=%.2f max=%.2f  (v2 全片 min=0.00 avg≈0.05)" % (
    min(brs), sum(brs) / len(brs), max(brs)))
print("  meanL : min=%.1f avg=%.1f  (v2 avg=%.1f)" % (
    min(mls), sum(mls) / len(mls), V2_MEANL))
low = [q[1] for q in quant if q[2] < 0.5]
print("  棕面仍偏弱的镜头(brown<0.5%%): %s" % (low if low else "无"))
print("\n=== DONE ===")
