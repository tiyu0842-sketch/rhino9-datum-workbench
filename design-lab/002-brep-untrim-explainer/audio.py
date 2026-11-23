# -*- coding: utf-8 -*-
"""
audio.py —— 确定性程序化音轨：soundtrack.wav

与 render.py 的 frame(t) 同一套纪律：声音也是 sample(t) 纯函数。
采样点时间 t = i / sample_rate，时间轴的唯一来源是 storyboard.BEATS。
所以改一镜 dur，音轨自动跟着变，不需要手工对时间码。

三条禁令同样适用：不读系统时间、不用无种子随机、不联网。
包络全部在 Python 里算完，ffmpeg 只负责 -c:a aac 封装 —— 和「转场在帧内算」
是同一个思路：不把表现力押在编码器滤镜上。

三个最容易翻车的点（都在这里显式处理）：
  1. 每个事件的包络必须从 0 起、回到 0 收。波形硬跳变 = 爆音(click)。
  2. 镜头边界的氛围频率要滑过去（pad_glide），不能硬切。
  3. 最后统一归一化 + 限幅，避免叠加后削波失真。

用法：
    python audio.py            # 生成 soundtrack.wav
    python audio.py --info     # 只打印事件表与音量统计，不写文件
"""

import argparse
import array
import math
import os
import wave

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))
WAV = os.path.join(_HERE, "soundtrack.wav")

TAU = 2.0 * math.pi

# 每种事件的合成参数。用 dict 而不是 tuple：build_html.py 会把它原样注入
# preview.html，浏览器 Web Audio 读同一份 K.dur / K.h，音色定义只有这一处。
KIND = {
    "cue":   {"dur": 1.10, "atk": 0.006, "dec": 0.34,
              "h": [[1.0, 1.0], [2.0, 0.34], [3.0, 0.10]], "base": 1.00},
    "tick":  {"dur": 0.16, "atk": 0.002, "dec": 0.035,
              "h": [[4.0, 0.85], [5.4, 0.45]], "base": 0.52},
    "thud":  {"dur": 1.30, "atk": 0.010, "dec": 0.48,
              "h": [[1.0, 1.0], [0.5, 0.60]], "base": 0.95},
    "lift":  {"dur": 0.85, "atk": 0.008, "dec": 0.36,
              "h": [[1.0, 1.0], [2.0, 0.22]], "base": 0.80},
    "chord": {"dur": 2.60, "atk": 0.030, "dec": 1.05,
              "h": [[1.0, 1.0], [1.25, 0.62], [1.5, 0.42], [2.0, 0.16]], "base": 0.72},
}


def events():
    """纯函数：把 BEATS 翻译成按时间排序的声音事件表。

    返回 [(t秒, kind, 频率Hz, 力度0..1), ...]。
    build_html.py 把这张表注入 preview.html，浏览器用 Web Audio 复现同一套音色，
    保证「离线 WAV」与「在线预览」听感一致 —— 事件定义只有这一处。
    """
    out = []
    scale = SB.AUDIO["scale"]
    for bid, t0, t1 in SB.cumulative_starts():
        b = SB.BEATS[bid]
        f = scale[bid % len(scale)]

        # 每镜开头一声「叮」：音高按镜头编号阶梯上行，听得出进度
        out.append((round(t0 + 0.06, 6), "cue", f, 1.0))

        # 有滚动数字的镜头：每个指标给一个短促节拍点，标出「数字上屏」
        if b.get("metrics"):
            for j in range(max(1, len(b["metrics"]))):
                out.append((round(t0 + b["dur"] * (0.36 + 0.16 * j), 6),
                            "tick", f * 2.0, 0.70))

        # 语义重音：不是装饰，是让「否定 / 打破 / 收束」在听觉上可分辨
        if b["scene"] == "fillet":
            # UntrimOuterLoop → null：低频下扫，否定感
            out.append((round(t0 + b["dur"] * 0.56, 6), "thud", 98.0, 1.0))
        elif b["scene"] == "independence":
            # 打破伪约束：上滑音
            out.append((round(t0 + b["dur"] * 0.74, 6), "lift", f * 1.5, 0.9))
        elif b["scene"] == "outro":
            # 片尾收束和弦
            out.append((round(t0 + b["dur"] * 0.78, 6), "chord", f, 0.85))
    return sorted(out, key=lambda e: e[0])


def _smooth(u):
    """smoothstep：把线性进度变成两端导数为 0 的缓动，用来做无跳变过渡。"""
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def synth():
    """逐采样合成。返回 (pcm_array, peak, rms, n_samples)。纯函数。"""
    A = SB.AUDIO
    sr = A["sample_rate"]
    total = SB.TOTAL_DURATION
    n = int(round(total * sr))
    buf = array.array("f", [0.0]) * n
    starts = SB.cumulative_starts()          # [(id, t0, t1)]
    steps = A["pad_steps"]
    glide = A["pad_glide"]

    # ---- 1) 连续氛围层 ----
    # 三个低频正弦 + 一个 0.3% 失谐层（产生缓慢拍频，避免电子死板感）+ 0.11 Hz 呼吸 LFO。
    # 关键：f0 在每镜开头 glide 秒内从上一镜的半音滑到本镜，相位连续、频率不硬切。
    bi = 0
    for i in range(n):
        t = i / sr
        while bi < len(starts) - 1 and t >= starts[bi][2]:
            bi += 1
        bid, t0, t1 = starts[bi]
        prev = steps[(bid - 1) % len(steps)] if bid > 0 else steps[bid % len(steps)]
        cur = steps[bid % len(steps)]
        semi = prev + (cur - prev) * _smooth((t - t0) / glide)
        f0 = A["pad_root"] * (2.0 ** (semi / 12.0))

        breath = 0.62 + 0.38 * math.sin(TAU * 0.11 * t)
        p = (math.sin(TAU * f0 * t)
             + 0.45 * math.sin(TAU * f0 * 1.5 * t)
             + 0.22 * math.sin(TAU * f0 * 2.0 * t)
             + 0.30 * math.sin(TAU * f0 * 1.003 * t))

        # 镜头末尾轻微下压，给下一镜的 cue 留出空间；全局淡入淡出
        u = (t - t0) / (t1 - t0)
        duck = 1.0 - 0.30 * _smooth((u - 0.86) / 0.14)
        fade = _smooth(t / A["fade_in"]) * _smooth((total - t) / A["fade_out"])
        buf[i] = p * breath * duck * fade * A["pad_level"]

    # ---- 2) 离散事件层 ----
    # 只在自己的时间窗内写样本，复杂度 ~ 事件窗口总长，而不是 n × 事件数。
    for ts, kind, freq, strength in events():
        K = KIND[kind]
        dur, atk, dec = K["dur"], K["atk"], K["dec"]
        harmonics, base = K["h"], K["base"]
        i0 = int(round(ts * sr))
        cnt = int(round(dur * sr))
        for k in range(cnt):
            idx = i0 + k
            if idx < 0:
                continue
            if idx >= n:
                break
            tt = k / sr
            # 起音从 0 开始、衰减回 0：波形连续，不会 click
            env = (1.0 - math.exp(-tt / atk)) * math.exp(-tt / dec)
            f = freq
            if kind == "thud":
                f = freq * (1.0 - 0.22 * tt / dur)       # 下扫
            elif kind == "lift":
                f = freq * (0.72 + 0.55 * tt / dur)      # 上滑
            s = 0.0
            for mult, w in harmonics:
                s += w * math.sin(TAU * f * mult * tt)
            buf[idx] += strength * base * A["cue_level"] * env * s

    # ---- 3) 统一增益 + 限幅 ----
    peak = 0.0
    for v in buf:
        a = v if v >= 0 else -v
        if a > peak:
            peak = a
    target = A["master"] * 0.92
    g = 1.0 if peak < 1e-9 else min(target / peak, 2.5)
    pcm = array.array("h")
    acc = 0.0
    for v in buf:
        x = max(-1.0, min(1.0, v * g))
        pcm.append(int(x * 32767))
        acc += x * x
    rms = math.sqrt(acc / max(1, n))
    return pcm, peak, rms, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", action="store_true", help="只打印事件表与统计，不写 WAV")
    args = ap.parse_args()

    ev = events()
    print("AUDIO_SPEC  sr=%d  dur=%.2fs  events=%d"
          % (SB.AUDIO["sample_rate"], SB.TOTAL_DURATION, len(ev)))
    for bid, t0, t1 in SB.cumulative_starts():
        scene = SB.BEATS[bid]["scene"]
        here = [(round(t - t0, 2), k) for t, k, _, _ in ev if t0 <= t < t1]
        print("  BEAT %d  %-16s  %5.2f–%5.2fs  %s"
              % (bid, scene, t0, t1, here))

    pcm, peak, rms, n = synth()
    print("SYNTH  samples=%d  peak=%.4f  rms=%.4f  gain=%.3f"
          % (n, peak, rms, (SB.AUDIO["master"] * 0.92 / peak) if peak else 1.0))
    if args.info:
        print("INFO_ONLY  (no wav written)")
        return

    with wave.open(WAV, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SB.AUDIO["sample_rate"])
        w.writeframes(pcm.tobytes())
    print("WAV %s  %.2f MB  %.2fs"
          % (WAV, os.path.getsize(WAV) / 1024 / 1024,
             n / SB.AUDIO["sample_rate"]))


if __name__ == "__main__":
    main()
