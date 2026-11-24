# -*- coding: utf-8 -*-
"""
audio.py v3 —— 确定性程序化配乐：soundtrack.wav（stereo）

纪律与 render.py 的 frame(t) 完全相同：声音是 sample(t) 纯函数。
    t = i / sample_rate，时间轴来源是 storyboard.AUDIO（绝对秒），**不读 BEATS**。
所以改一句字幕 / 改一镜 dur，配乐一动不动 —— 这是 E-029 省算力清单第 9 条。

v3 相对 v2 的改动（E-029 拍板 D1–D6 推荐 A）：
  D1 纯标准库，不联网、不外部素材；
  D2 16-bit 48 kHz stereo + 左右不同三抽头房间回声（在采样点算，不靠 ffmpeg 滤镜）；
  D3 固定 D major 四和弦循环（8 s/和弦），pad / 事件同源同调；
  D4 事件 17 → 7，atk 2 ms → ≥20 ms，去掉 5.4 非整数倍频；
  D5 四段情绪弧：提出 / 积累 / 啊哈(32 s 主和弦落点) / 收束；
  D6 pad 0.16 → 0.06 + 80 Hz 高通 + 固定 ±0.12 Hz detune + 0.07 Hz 呼吸。

用法：
    python audio.py            # 生成 soundtrack.wav
    python audio.py --info     # 只打印事件表 + 6 项听感指标，不写文件
    python audio.py --preview  # 额外导出 10 s 试听片段（28–38 s，含啊哈落点）
"""

import argparse
import array
import math
import os
import wave

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))
WAV = os.path.join(_HERE, "soundtrack.wav")
PREVIEW = os.path.join(_HERE, "preview_10s.wav")

TAU = 2.0 * math.pi

# 事件音色：整数倍谐波（无 5.4 之类非整数倍），柔和起音（atk ≥ 20 ms）。
# KIND 必须是 dict（可序列化注入 preview.html，tuple 会变 JSON 数组 —— v2 踩过）。
KIND = {
    "cue":   {"dur": 1.60, "atk": 0.020, "dec": 0.42,
              "h": [[1.0, 1.0], [2.0, 0.30], [3.0, 0.10]], "base": 0.50},
    "thud":  {"dur": 1.80, "atk": 0.025, "dec": 0.55,
              "h": [[1.0, 1.0], [0.5, 0.55]], "base": 0.70},
    "chord": {"dur": 4.50, "atk": 0.030, "dec": 1.60,
              "h": [[1.0, 1.0], [1.25, 0.45], [1.5, 0.30], [2.0, 0.12]], "base": 0.62},
}


def midi_hz(m):
    """MIDI 音高 → 频率（A4=69=440 Hz）。纯函数。"""
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


def _smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def chord_at(t):
    """绝对秒 → 当前和弦（D3：按时间走，与 BEATS 编号解耦）。"""
    prog = SB.AUDIO["progression"]
    idx = int(t // SB.AUDIO["chord_sec"]) % len(prog)
    return prog[idx], idx


def energy_at(t):
    """四段情绪弧的能量包络（D5）。段间 0.8 s smoothstep 过渡，避免硬切。"""
    arcs = SB.AUDIO["arc"]
    e = arcs[-1]["energy"]
    for i, a in enumerate(arcs):
        if t < a["t1"]:
            e = a["energy"]
            if i > 0 and t < a["t0"] + 0.8:
                prev = arcs[i - 1]["energy"]
                e = prev + (a["energy"] - prev) * _smooth((t - a["t0"]) / 0.8)
            break
    return e


def highpass_gain(f, fc):
    """一阶高通幅度响应 f/sqrt(f²+fc²)。纯函数，替代滤波器。"""
    return f / math.sqrt(f * f + fc * fc)


def pad_sample(t):
    """D6：和弦最低 3 音 × 3 个固定 detune 正弦 × 高通 × 呼吸 × 能量包络。"""
    A = SB.AUDIO
    ch, _ = chord_at(t)
    notes = ch["notes"][:3]
    e = energy_at(t)
    breath = 1.0 + A["pad_lfo_depth"] * math.sin(TAU * A["pad_lfo_hz"] * t)
    s = 0.0
    for m in notes:
        f = midi_hz(m)
        hp = highpass_gain(f, A["pad_highpass_hz"])
        for d in (-A["pad_detune_hz"], 0.0, A["pad_detune_hz"]):
            s += math.sin(TAU * (f + d) * t)
    return s * hp * breath * e * A["pad_level"] * (1.0 / 9.0)


def events():
    """D4：7 个事件，绝对秒，与 BEATS 解耦。返回 [(t, kind, freq, gain), ...]。"""
    return [(e["t"], e["kind"], midi_hz(e["midi"]), e["gain"])
            for e in SB.AUDIO["events"]]


def fill(dry, total, sr):
    """填 dry buffer（pad + 事件，mono）。只写事件自身窗口，不是 n×事件数。"""
    for i in range(total):
        dry[i] = pad_sample(i / sr)

    for ts, kind, freq, gain in events():
        K = KIND[kind]
        i0 = int(round(ts * sr))
        cnt = int(round(K["dur"] * sr))
        for k in range(cnt):
            idx = i0 + k
            if idx >= total:
                break
            if idx < 0:
                continue
            tt = k / sr
            env = (1.0 - math.exp(-tt / K["atk"])) * math.exp(-tt / K["dec"])
            s = 0.0
            for mult, w in K["h"]:
                s += w * math.sin(TAU * freq * mult * tt)
            dry[idx] += gain * K["base"] * 0.30 * env * s * energy_at(idx / sr)

    fade_in = SB.AUDIO["fade_in"]
    fade_out = SB.AUDIO["fade_out"]
    dur_s = total / sr
    for i in range(total):
        t = i / sr
        dry[i] *= _smooth(t / fade_in) * _smooth((dur_s - t) / fade_out)


def synth():
    """生成 stereo PCM。返回 (pcm_interleaved, peak_raw, rms_final, n_per_ch)。"""
    A = SB.AUDIO
    sr = A["sample_rate"]
    total = int(round(SB.TOTAL_DURATION * sr))
    dry = array.array("f", [0.0]) * total
    fill(dry, total, sr)

    # D2：三抽头房间回声，左右不同延迟 → 立体声宽度
    taps_l = [(int(ms * sr / 1000.0), g) for ms, g in A["room_taps"]["L"]]
    taps_r = [(int(ms * sr / 1000.0), g) for ms, g in A["room_taps"]["R"]]

    wet_l = array.array("f", [0.0]) * total
    wet_r = array.array("f", [0.0]) * total
    for i in range(total):
        v = dry[i] * 0.86          # 干声稍低，给房间回声留空间
        l, r = v, v
        for d, g in taps_l:
            if i >= d:
                l += dry[i - d] * g
        for d, g in taps_r:
            if i >= d:
                r += dry[i - d] * g
        wet_l[i], wet_r[i] = l, r

    peak = 0.0
    for i in range(total):
        for v in (wet_l[i], wet_r[i]):
            a = v if v >= 0 else -v
            if a > peak:
                peak = a
    g = 1.0 if peak < 1e-9 else min(A["master"] * 0.92 / peak, 2.5)

    pcm = array.array("h")
    acc = 0.0
    for i in range(total):
        for src in (wet_l, wet_r):
            x = max(-1.0, min(1.0, src[i] * g))
            pcm.append(int(x * 32767))
            acc += x * x
    rms = math.sqrt(acc / max(1, total * 2))
    return pcm, peak, rms, total


def metrics():
    """6 项可计算的听感代理指标（E-029 省算力第 4 条）。不生成 WAV 也能跑。"""
    A = SB.AUDIO
    ev = events()
    ts = [e[0] for e in ev]
    gaps = [round(ts[i + 1] - ts[i], 3) for i in range(len(ts) - 1)]
    atks = sorted({KIND[k]["atk"] for _, k, _, _ in ev})

    # 协和判据：事件音高是否属于当前和弦的音级集合（任意八度）。
    # 这才是正确的定义 —— 之前用频率比 1..6 的绝对容差，跨八度的和弦音会被误判。
    hits = 0
    for t, kind, f, _ in ev:
        ch, _ = chord_at(t)
        # 用 MIDI 音级（mod 12）判断，等价于任意八度的和弦音归属
        ev_midi = next(e["midi"] for e in A["events"] if abs(e["t"] - t) < 1e-6)
        pitch_class = ev_midi % 12
        chord_pcs = {m % 12 for m in ch["notes"]}
        if pitch_class in chord_pcs:
            hits += 1

    return {
        "events": len(ev),
        "density_per_s": round(len(ev) / SB.TOTAL_DURATION, 3),
        "min_gap_s": min(gaps) if gaps else None,
        "atk_ms": [round(a * 1000, 1) for a in atks],
        "chord_tone_hits": "%d/%d" % (hits, len(ev)),
        "key_changes": int(SB.TOTAL_DURATION // A["chord_sec"]),
        "chord_loop_s": A["chord_sec"] * len(A["progression"]),
        "low_freq_note": "80 Hz 高通（原 55 Hz 持续嗡鸣已移除）",
    }


def write_wav(path, pcm, frames):
    with wave.open(path, "wb") as w:
        w.setnchannels(SB.AUDIO["channels"])
        w.setsampwidth(2)
        w.setframerate(SB.AUDIO["sample_rate"])
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", action="store_true", help="只打印事件表 + 6 指标，不写 WAV")
    ap.add_argument("--preview", action="store_true", help="额外导出 10 s 试听片段")
    args = ap.parse_args()

    A = SB.AUDIO
    print("AUDIO_SPEC v3  sr=%d  ch=%d  dur=%.2fs  key=D-major  chord=%.1fs"
          % (A["sample_rate"], A["channels"], SB.TOTAL_DURATION, A["chord_sec"]))
    print("ARC", " | ".join("%s %.1f-%.1f e=%.2f" % (a["name"], a["t0"], a["t1"], a["energy"])
                           for a in A["arc"]))
    print("=== LISTENING METRICS (E-029) ===")
    for k, v in metrics().items():
        print("  %-18s %s" % (k, v))

    if args.info:
        print("INFO_ONLY (no wav written)")
        return

    pcm, peak, rms, n = synth()
    print("SYNTH  samples/ch=%d  peak_raw=%.4f  rms_final=%.4f" % (n, peak, rms))
    write_wav(WAV, pcm, n)
    print("WAV %s  %.2f MB  %.2fs  stereo"
          % (WAV, os.path.getsize(WAV) / 1024 / 1024, n / A["sample_rate"]))

    if args.preview:
        sr = A["sample_rate"]
        t0 = A["aha_hit"] - 4.0
        i0 = int(t0 * sr)
        cnt = int(10.0 * sr) * A["channels"]
        seg = pcm[i0 * A["channels"]: i0 * A["channels"] + cnt]
        write_wav(PREVIEW, seg, len(seg) // A["channels"])
        print("PREVIEW %s  10.00s (t=%.1f-%.1f, 含啊哈落点)" % (PREVIEW, t0, t0 + 10.0))


if __name__ == "__main__":
    main()
