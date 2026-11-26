# -*- coding: utf-8 -*-
"""
narration.py —— 用本机 SAPI（Microsoft Huihui 中文语音）离线合成旁白

不联网、不付费、不用外部音频素材；语音包是 Windows 自带的
"Microsoft Huihui Desktop - Chinese (Simplified)"。
输出 narration.wav（22050 Hz / 16-bit / mono），由 mix_audio.py 按镜头
时间点对齐混入 48 kHz 立体声配乐。

用法： python narration.py            # 合成整条旁白
      python narration.py --probe     # 只合成第一句试听
"""

import os
import sys
import wave
import argparse

import win32com.client as win32

import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))

# 每镜一句旁白，按 BEATS 顺序；短句、口语化，配合画面节奏（每镜 4–7 s）。
# 字数上限按各镜 dur 算：Huihui 正常语速约 3.7 字/秒，rate=+2 约 4.2 字/秒；
# 每句留 0.8 s 余量给镜头淡入淡出，所以字数 ≈ (dur − 0.8) × 4.2。
# 不照读屏幕文字——屏幕给要点，旁白给因果。
VOICEOVER = [
    "斜面建模为什么别扭？不是你手笨。",                 # 镜0  4.0s → 16字
    "歪的不是相机，是工作平面没跟上斜面。",             # 镜1  6.0s → 18字
    "先立一面基准面，像一把可命名的尺子贴在斜面上。",   # 镜2  6.5s → 23字
    "工作平面和操作轴转过去对齐，斜面就成了顶视图。",   # 镜3  6.5s → 23字
    "第五视图让相机垂直于面，就能像顶视图一样在斜面上画。",  # 镜4 7.0s → 25字
    "可以点选、按号调用、存成命名平面，不重复建几何。", # 镜5  6.0s → 23字
    "Alias 观测显示用等参线看清走向，浅深两套不刺眼。", # 镜6  7.0s → 24字
    "基准面在锁定的子层里，删不掉，但仍能点选切换。",   # 镜7  6.0s → 23字
    "j H 只关灯，锁定不碰；j H H 按快照原样还原。",     # 镜8  7.0s → 22字
    "退出时各视口精确还原。每帧代码算出，同码同片。",   # 镜9  6.5s → 23字
]


def synthesize(voice, text, out_path, rate=0):
    """SAPI 把文本直接写成 wav。rate -10..10，0 为正常语速。"""
    token = voice.Speak(text, 0x08)   # SVSFlagsAsync = 8，避免阻塞式吞掉后续
    while voice.WaitUntilDone(100) is False:
        pass
    # 上面这句在部分 SAPI 实现返回 None，兜底再等一次
    voice.WaitUntilDone(5000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="只合成第一句")
    ap.add_argument("--rate", type=int, default=0, help="语速 -10..10")
    args = ap.parse_args()

    voice = win32.Dispatch("SAPI.SpVoice")
    # 选中文语音包
    chosen = None
    voices = voice.GetVoices()
    for i in range(voices.Count):
        v = voices.Item(i)
        desc = v.GetDescription()
        if "Huihui" in desc or "Chinese" in desc:
            chosen = v
            break
    if chosen is None:
        print("NO_CHINESE_VOICE", file=sys.stderr)
        return 2
    voice.Voice = chosen
    voice.Rate = args.rate
    print("VOICE", chosen.GetDescription(), "rate", args.rate)

    lines = VOICEOVER[:1] if args.probe else VOICEOVER
    outdir = os.path.join(_HERE, "vo")
    os.makedirs(outdir, exist_ok=True)

    done = []
    for i, text in enumerate(lines):
        # SAPI 需要文件对象作为输出：用 SPFileStream
        fs = win32.Dispatch("SAPI.SPFileStream")
        path = os.path.join(outdir, "vo_%02d.wav" % i)
        fs.Open(path, 3, False)   # SSFMCreateForWrite = 3
        voice.AudioOutputStream = fs
        voice.Speak(text, 0)      # 同步，等这句说完
        fs.Close()
        with wave.open(path, "rb") as w:
            dur = w.getnframes() / float(w.getframerate())
        done.append((i, dur, path))
        print("VO %02d  %.2fs  %s" % (i, dur, text[:28]))

    print("NARRATION_DONE", len(done), "clauses")
    if args.probe:
        print("probe ->", done[0][2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
