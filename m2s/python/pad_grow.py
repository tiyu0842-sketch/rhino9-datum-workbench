# -*- coding: utf-8 -*-
"""pad_grow.py - 【DEPRECATED / 方法错误，仅留作反面教材】

结论先行：本脚本的"全局球壳距离直方图"会产出假峰。
150 万面的密集网格里，任意大球壳都与筒壁、其他肉垫相交，交面散布整个球面，
于是"覆盖角 94-171 度"是假象，band 里 3 万个点不是一片连续曲面。
实测给出 R=0.10/0.40/0.50/0.62/0.56 且全部 RELIABLE——全是错的。
正确做法是面级连通生长（见 README「猫爪笔筒特征分解」）。

以下为原始说明，保留以便复现错误：

pad_grow.py - 用整张网格验证每个球冠，并重拟合半径。

为什么要做
----------
上一轮只把「+Z ±30° 法向筛」留下的球冠小片拿去拟合球，覆盖角很窄，
拟合是病态的：代数解与 Rhino 内核解在 #3 上差 2.5 倍（0.437 vs 0.175）。
一个球半径只有在**网格上确实存在对应球壳**时才可信。

方法（便宜且稳）
----------------
1. 全网格 764k 顶点到初始球心的距离直方图（step 0.002）
2. 在 R0 附近找最显著的峰 —— 峰存在 = 球壳真实存在，峰位 = 更好的半径
3. 取峰带 ±0.008 的点重拟合，再迭代一轮
4. 报告：粗半径 R0 / 峰半径 / 重拟合半径 / 峰带点数 / 覆盖半角

覆盖半角 < 20° 的块，半径一律标 "unreliable"——这是数据问题，不是算法问题。

纯标准库 + stl_chain.load_stl，不经 Rhino。可直接 python 跑。
"""
import json
import math
import os
import sys

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\github-release\m2s\python"
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import spherefit_core as SP
import stl_chain as SC

_CHAIN = os.path.join(_HERE, "stl_chain_result.json")
_CATPAW = os.path.join(_HERE, "catpaw_result.json")
_OUT = os.path.join(_HERE, "pad_grow_result.json")

STEP = 0.002
BAND = 0.008


def hist_peak(dists, lo, hi, step):
    """在 [lo, hi) 上做直方图，返回 (峰中心, 该 bin 原始计数, 平滑后计数)。"""
    nb = max(1, int((hi - lo) / step) + 1)
    h = [0] * nb
    for d in dists:
        if lo <= d < hi:
            k = int((d - lo) / step)
            if 0 <= k < nb:
                h[k] += 1
    best_i, best_s = 0, -1
    for i in range(nb):
        s = h[max(0, i - 1)] + h[i] + h[min(nb - 1, i + 1)]
        if s > best_s:
            best_s, best_i = s, i
    return lo + (best_i + 0.5) * step, h[best_i], best_s


def main():
    chain = json.load(open(_CHAIN, encoding="utf-8"))
    cat = json.load(open(_CATPAW, encoding="utf-8"))
    verts, faces, n_hdr = SC.load_stl(chain["source"])
    print("mesh: %d verts / %d faces (STL declares %d)" %
          (len(verts), len(faces), n_hdr))
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]

    out = []
    print("")
    print("%-4s %8s %8s %8s %7s %8s %8s %9s" % (
        "id", "R0(coarse)", "R_peak", "R_refit", "band#", "rms", "span_deg", "verdict"))
    print("-" * 76)
    for c in cat["segments"]:
        if c["type"] != "SPHERE":
            continue
        cx, cy, cz = c["sphere_center"]
        R0 = c["sphere_radius"]
        d0 = [math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
              for x, y, z in zip(xs, ys, zs)]
        lo = max(0.0, R0 * 0.4)
        hi = max(d0) * 1.001
        Rp, cnt_p, cnt_s = hist_peak(d0, lo, hi, STEP)

        # 峰带内的点
        band = [(x, y, z) for d, x, y, z in zip(d0, xs, ys, zs)
                if abs(d - Rp) <= BAND]
        fit = SP.fit_sphere(band) if len(band) >= 10 else None
        rms = span = None
        R1 = Rp
        if fit:
            R1 = fit[3]
            # 第二轮：以新球收敛
            d1 = [math.sqrt((x - fit[0]) ** 2 + (y - fit[1]) ** 2 +
                            (z - fit[2]) ** 2) for x, y, z in band]
            band2 = [(x, y, z) for d, (x, y, z) in zip(d1, band)
                     if abs(d - R1) <= BAND]
            fit2 = SP.fit_sphere(band2) if len(band2) >= 10 else None
            if fit2:
                fit = fit2
                R1 = fit2[3]
                band = band2
            rms, _mx = SP.rms_sphere(band, fit[:3], R1)
            span = SP.angular_span(band, fit[:3], c["normal"])

        reliable = (span is not None and span >= 20.0 and len(band) >= 200)
        verdict = "RELIABLE" if reliable else "narrow-cap"
        print("%-4s %8.4f %8.4f %8.4f %7d %8s %8s %9s" % (
            c["id"], R0, Rp, R1, len(band),
            ("%.5f" % rms) if rms is not None else "n/a",
            ("%.1f" % span) if span is not None else "n/a", verdict))

        out.append({
            "id": c["id"],
            "R_coarse": R0,
            "R_peak": Rp,
            "R_refit": R1,
            "band_points": len(band),
            "rms": rms,
            "span_deg": span,
            "reliable": reliable,
            "center_refit": list(fit[:3]) if fit else None,
            "peak_count_raw": cnt_p,
            "peak_count_smooth": cnt_s,
        })

    json.dump({"source": chain["source"], "step": STEP, "band": BAND,
               "segments": out},
              open(_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("")
    print("-> " + _OUT)


if __name__ == "__main__":
    main()
