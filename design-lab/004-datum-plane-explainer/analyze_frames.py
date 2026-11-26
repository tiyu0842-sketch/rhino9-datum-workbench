# -*- coding: utf-8 -*-
"""analyze_frames.py —— 对 verify_v2 的分镜帧做构图/对比度量化（只读）。"""
import os
import glob
from PIL import Image

D = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\github-release\design-lab\004-datum-plane-explainer\verify_v2"
GROUND = (0x12, 0x14, 0x1A)


def dist(c, g):
    return abs(c[0] - g[0]) + abs(c[1] - g[1]) + abs(c[2] - g[2])


def is_brown(c):
    return 110 <= c[0] <= 215 and 70 <= c[1] <= 170 and 30 <= c[2] <= 120 and c[0] > c[1] > c[2]


print("%-6s %-11s %8s %8s %8s %8s %8s" % (
    "shot", "scene", "content%", "brown%", "edge%", "meanL", "bright%"))
rows = []
for p in sorted(glob.glob(os.path.join(D, "s*.png"))):
    name = os.path.basename(p).split("_")
    sid, scene = name[0], name[1]
    im = Image.open(p).convert("RGB")
    W, H = im.size
    px = im.load()
    step = 4  # 4x4 抽样，够统计
    total = 0
    content = brown = edge = 0
    lsum = 0
    bright = 0
    for y in range(0, H, step):
        for x in range(0, W, step):
            c = px[x, y]
            total += 1
            lsum += (c[0] * 299 + c[1] * 587 + c[2] * 114) // 1000
            if dist(c, GROUND) > 25:
                content += 1
            if is_brown(c):
                brown += 1
            if x < W * 0.04 or x > W * 0.96 or y < H * 0.05 or y > H * 0.95:
                if dist(c, GROUND) > 25:
                    edge += 1
            if (c[0] + c[1] + c[2]) / 3 > 200:
                bright += 1
    cr = 100.0 * content / total
    br = 100.0 * brown / total
    er = 100.0 * edge / max(1, total * 0.15)  # 边缘带内占比
    ml = lsum / total
    bl = 100.0 * bright / total
    rows.append((sid, scene, cr, br, er, ml, bl))
    print("%-6s %-11s %7.2f%% %7.2f%% %7.2f%% %8.1f %7.2f%%" % (
        sid, scene, cr, br, er, ml, bl))

print("\n--- 判读口径 ---")
print("content% < 15  → 画面偏空（几何+UI 占屏不足）")
print("brown%   < 1.0 → 基准面在深底上存在感弱")
print("edge%    > 3.0 → 有元素贴边/可能被裁")
cr_vals = [r[2] for r in rows]
print("\ncontent%%: min=%.2f avg=%.2f max=%.2f" % (min(cr_vals), sum(cr_vals) / len(cr_vals), max(cr_vals)))
print("偏空镜头(<15%%): %s" % ", ".join(r[0] for r in rows if r[2] < 15))
