# -*- coding: utf-8 -*-
"""mix_edge.py —— 把 edge-tts 晓晓旁白按镜头对齐混入配乐

输入 soundtrack.wav（48k stereo 配乐）+ vo_edge/ve_*.mp3（晓晓神经语音）
输出 narration_edge.wav（48k stereo：配乐压低 + 晓晓旁白）

依赖 ffmpeg 把 mp3 解成 48k mono PCM，其余用标准库混音。
"""

import os
import sys
import wave
import array
import subprocess

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))
FF = r"C:\Program Files\KS2024\bin\ffmpeg.exe"
VO_DIR = os.path.join(_HERE, "vo_edge")

MUSIC_GAIN = 0.30
VO_GAIN = 0.90
LEAD = 0.25


def read_pcm(path):
    with wave.open(path, "rb") as w:
        a = array.array("h")
        a.frombytes(w.readframes(w.getnframes()))
        return w.getframerate(), w.getnchannels(), a


def mp3_to_wav(src, dst):
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                    "-i", src, "-ar", "48000", "-ac", "1", dst], check=True)


def main():
    sr, ch, bg = read_pcm(os.path.join(_HERE, "soundtrack.wav"))
    assert sr == 48000 and ch == 2
    n = len(bg) // 2
    left = [int(x * MUSIC_GAIN) for x in bg[0::2]]
    right = [int(x * MUSIC_GAIN) for x in bg[1::2]]

    for i, (bid, a, b) in enumerate(SB.cumulative_starts()):
        mp3 = os.path.join(VO_DIR, "ve_%02d.mp3" % i)
        if not os.path.exists(mp3):
            print("MISSING", mp3, file=sys.stderr)
            continue
        tmp = os.path.join(VO_DIR, "_tmp_%02d.wav" % i)
        mp3_to_wav(mp3, tmp)
        vsr, vch, vpcm = read_pcm(tmp)
        assert vsr == 48000 and vch == 1, (vsr, vch)
        off = int((a + LEAD) * sr)
        for j, v in enumerate(vpcm):
            idx = off + j
            if idx >= n:
                break
            val = int(max(-32768, min(32767, v * VO_GAIN)))
            left[idx] = int(max(-32768, min(32767, left[idx] + val * 0.5)))
            right[idx] = int(max(-32768, min(32767, right[idx] + val * 0.5)))
        os.remove(tmp)
        print("VO %02d @ %.2fs  %.2fs" % (i, a + LEAD, len(vpcm) / sr))

    peak = max(max(abs(x) for x in left[::100]), max(abs(x) for x in right[::100]))
    if peak > 30000:
        k = 30000.0 / peak
        left = [int(x * k) for x in left]
        right = [int(x * k) for x in right]
        print("LIMIT", round(k, 3))

    out = os.path.join(_HERE, "narration_edge.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        inter = array.array("h")
        for l, r in zip(left, right):
            inter.append(l); inter.append(r)
        w.writeframes(inter.tobytes())
    print("MIX_DONE", out, "%.2fs" % (n / sr))


if __name__ == "__main__":
    main()
