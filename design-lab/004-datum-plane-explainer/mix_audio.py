# -*- coding: utf-8 -*-
"""
mix_audio.py —— 把 10 句 SAPI 中文旁白按镜头起点对齐，混入程序合成配乐

输入：
  soundtrack.wav   由 audio.py 生成（48 kHz / 16-bit / stereo）
  vo/vo_00..09.wav 由 narration.py 生成（22050 Hz / 16-bit / mono）
输出：
  narration_mix.wav 48 kHz / 16-bit / stereo，旁白在中置、配乐压低 0.30

对齐规则：第 i 句旁白放在第 i 镜起点 + 0.25 s（给画面淡入留一点呼吸）。
旁白不做变速，各句时长已在 narration.py 里按镜头 dur 限过字。
纯标准库 wave/array；不联网、不用外部素材。
"""

import os
import sys
import wave
import array

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))


def read_pcm(path):
    with wave.open(path, "rb") as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    a = array.array("h")
    a.frombytes(raw)
    return sr, ch, a


def write_stereo(path, sr, left, right):
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        inter = array.array("h")
        for l, r in zip(left, right):
            inter.append(l)
            inter.append(r)
        w.writeframes(inter.tobytes())


def main():
    bg_path = os.path.join(_HERE, "soundtrack.wav")
    if not os.path.exists(bg_path):
        print("NO_SOUNDTRACK, run audio.py first", file=sys.stderr)
        return 2
    sr, ch, bg = read_pcm(bg_path)
    assert sr == 48000 and ch == 2, (sr, ch)
    n = len(bg) // 2
    # 先压低配乐，再叠旁白——顺序反了会把人声一起压掉
    MUSIC_GAIN = 0.30    # 有旁白时把配乐压低，避免盖住人声
    VO_GAIN = 0.85
    LEAD = 0.25          # 每镜起点后 0.25 s 才进旁白
    left = [int(x * MUSIC_GAIN) for x in bg[0::2]]
    right = [int(x * MUSIC_GAIN) for x in bg[1::2]]

    placed = 0
    for i, (bid, a, b) in enumerate(SB.cumulative_starts()):
        vpath = os.path.join(_HERE, "vo", "vo_%02d.wav" % i)
        if not os.path.exists(vpath):
            print("MISSING", vpath, file=sys.stderr)
            continue
        vsr, vch, vpcm = read_pcm(vpath)
        assert vsr == 22050 and vch == 1, (vsr, vch)
        # 22050 → 48000 线性插值重采样（SAPI 固定 22.05 kHz）
        ratio = 48000.0 / vsr
        m = int(len(vpcm) * ratio)
        off = int((a + LEAD) * sr)
        for j in range(m):
            idx = off + j
            if idx >= n:
                break
            src = j / ratio
            i0 = int(src)
            i1 = min(i0 + 1, len(vpcm) - 1)
            f = src - i0
            val = vpcm[i0] * (1 - f) + vpcm[i1] * f
            v = int(max(-32768, min(32767, val * VO_GAIN)))
            # 中置：左右各加一半
            left[idx] = int(max(-32768, min(32767, left[idx] + v * 0.5)))
            right[idx] = int(max(-32768, min(32767, right[idx] + v * 0.5)))
        placed += 1
        print("VO %02d @ %.2fs  %.2fs" % (i, a + LEAD, m / 48000.0))

    # 限幅，避免配乐+旁白峰值削波
    peak = max(max(abs(x) for x in left[::100]), max(abs(x) for x in right[::100]))
    if peak > 30000:
        k = 30000.0 / peak
        left = [int(x * k) for x in left]
        right = [int(x * k) for x in right]
        print("LIMIT gain", round(k, 3))

    out = os.path.join(_HERE, "narration_mix.wav")
    write_stereo(out, sr, left, right)
    print("MIX_DONE", placed, "clauses ->", out, "%.2fs" % (n / sr))
    return 0


if __name__ == "__main__":
    sys.exit(main())
