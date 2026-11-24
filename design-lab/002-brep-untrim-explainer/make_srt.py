# -*- coding: utf-8 -*-
"""make_srt.py —— 用 narration.md 的逐镜文案生成 B 站 CC 字幕（确定性）。

不读时钟、不用随机、不联网：时间码与文案都是常量表（与 narration.md 同一份）。
输出 `brep_untrim.srt`，UTF-8 无 BOM，可直接在 B 站投稿页「字幕 → 上传」使用。

用法：
    python make_srt.py
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "brep_untrim.srt")

# (开始秒, 结束秒, 文案) —— 与 narration.md 的时间码一致；长句按标点切成两条
SCENES = [
    (0.00, 3.20, ["同一个立方体，", "两种「多出来的形状」。"]),
    (3.20, 8.60, ["B-rep 有两层：底层曲面是一整张没被破坏的平面，", "裁剪环只是画在它上面的边界。钻孔只动了第二层。"]),
    (8.60, 14.60, ["孔，就是多了一个内环。", "底层曲面一点没坏，取消它只要把那个环删掉。面数从八变成七。"]),
    (14.60, 21.20, ["两个孔，只勾一个。", "H1 的两个内环被删，H2 纹丝不动。", "「必须先去圆角」，其实是个伪约束。"]),
    (21.20, 28.40, ["圆角不一样。", "它是滚球扫出的一整圈新曲面，", "没有更大的底层曲面可以还原，UntrimOuterLoop 恒为 null。"]),
    (28.40, 35.40, ["所以，圆角盒加一个孔，", "只删那个孔的内环，得到的还是纯圆角盒。", "两个模块完全独立，任意顺序。"]),
    (35.40, 40.60, ["孔是可抹掉的边界，", "圆角是必须重新缝合的实体。", "机器给候选，人来裁决，明确报出，不偷偷改。"]),
    (40.60, 44.60, ["每一帧都由代码算出。", "改一句字幕，只是一次 diff 加一次重渲染，不是重新抽卡。"]),
]


def ts(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def main():
    idx = 0
    lines = []
    for t0, t1, texts in SCENES:
        n = len(texts)
        span = (t1 - t0) / n
        for i, text in enumerate(texts):
            a = t0 + span * i
            b = t0 + span * (i + 1)
            idx += 1
            lines.append(str(idx))
            lines.append("%s --> %s" % (ts(a), ts(b - 0.05)))
            lines.append(text)
            lines.append("")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("wrote", OUT, idx, "cues")


if __name__ == "__main__":
    main()
