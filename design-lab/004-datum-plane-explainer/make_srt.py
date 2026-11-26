# -*- coding: utf-8 -*-
"""make_srt.py —— 由 storyboard.BEATS 生成 10 条 SRT 字幕（与镜头边界同源）。"""

import os
import storyboard as SB

_HERE = os.path.dirname(os.path.abspath(__file__))


def ts(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def main():
    out = os.path.join(_HERE, "datum_plane.srt")
    blocks = []
    for i, (bid, a, b) in enumerate(SB.cumulative_starts()):
        beat = SB.BEATS[bid]
        # 每条字幕留 0.2s 内缩，避免与叠化打架
        text = beat["title"]
        sub = beat.get("sub", "")
        blocks.append("%d\n%s --> %s\n%s\n%s\n" %
                      (i + 1, ts(a + 0.2), ts(b - 0.2), text, sub))
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    print("SRT", out, len(blocks), "cues")


if __name__ == "__main__":
    main()
