# -*- coding: utf-8 -*-
"""
build_html.py —— 把 storyboard.py 的数据注入 preview.html

为什么单独一步而不是在 HTML 里手抄一份分镜：
    手抄就会漂移。视频、预览、编码器读同一份 BEATS，改字幕只改 storyboard.py 一处。
用法：python build_html.py
"""

import json
import os

import audio
import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(_HERE, "preview.html")

MARK_OPEN = '<script id="sb" type="application/json">'
MARK_CLOSE = "</script>"


def main():
    with open(TPL, encoding="utf-8") as f:
        html = f.read()

    payload = json.dumps(
        {"beats": SB.BEATS, "config": SB.CONFIG, "palette": SB.PALETTE,
         "audio": SB.AUDIO, "audio_events": audio.events(),
         "audio_kinds": audio.KIND},
        ensure_ascii=False, separators=(",", ":"),
    )

    i = html.find(MARK_OPEN)
    if i < 0:
        raise SystemExit("preview.html 里找不到数据占位 <script id=\"sb\">")
    j = html.find(MARK_CLOSE, i)
    if j < 0:
        raise SystemExit("数据占位没有闭合的 </script>")

    out = html[: i + len(MARK_OPEN)] + payload + html[j:]
    with open(TPL, "w", encoding="utf-8") as f:
        f.write(out)

    print("INJECTED %d beats, %d audio events, %d kinds, %d chars payload -> %s"
          % (len(SB.BEATS), len(audio.events()), len(audio.KIND), len(payload), TPL))


if __name__ == "__main__":
    main()
