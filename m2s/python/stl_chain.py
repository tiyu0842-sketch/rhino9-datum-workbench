# -*- coding: utf-8 -*-
"""stl_chain.py —— 大网格适配层：150 万面 STL 上的法向筛选 + 平面/圆拟合。

为什么不直接调 chain_core.run_chain：
  run_chain 会对**每一个面**调 face_curvature，而 face_curvature 内部又遍历全部面找邻居
  → O(n²)。150 万面 = 2.2 万亿次比较，不可能跑完。这是真机数据暴露的架构边界。

本模块的替代策略（全部 O(n) 或 O(n log n)）：
  1. 法向筛：NFF.filter_faces 全量，O(n)
  2. 主朝向聚类：法向四舍五入到 0.1，统计 top 方向族（回答"这模型有几个朝向面"）
  3. 顶面（近 +Z）：取面顶点 → 最小二乘平面 → 偏差统计
  4. 侧壁（近水平）：2D 圆拟合（Kasa 最小二乘）+ z 分层半径剖面（判圆柱/锥/花瓶）
  5. 输出 JSON，供 Rhino 端建几何

纯标准库，不经 Rhino。
"""
import os
import sys
import json
import math
import struct
import collections

_HERE = os.path.dirname(os.path.abspath(__file__))
_NFF = os.path.join(_HERE, "..", "..", "nff", "python")
for _p in (_HERE, _NFF):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import surfacefit_core as SF
import nff_core as NFF
import segment_core as SEG
from units import UNITS_HINT, SCALE_HINT

STL = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\stl\model.stl"
OUT = os.path.join(_HERE, "stl_chain_result.json")


def load_stl(path):
    """解析二进制 STL，返回 (verts, faces)，顶点按 float 精确去重。"""
    verts, vmap, faces = [], {}, []
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        got = 0
        CH = 40000
        while got < n:
            buf = f.read(50 * CH)
            if not buf:
                break
            for o in range(0, len(buf), 50):
                v = struct.unpack_from("<12fH", buf, o)
                tri = []
                for k in (3, 6, 9):
                    key = (v[k], v[k + 1], v[k + 2])
                    idx = vmap.get(key)
                    if idx is None:
                        idx = len(verts)
                        vmap[key] = idx
                        verts.append(key)
                    tri.append(idx)
                faces.append(tuple(tri))
                got += 1
    return verts, faces, n


def fit_circle_2d(pts):
    """Kasa 最小二乘圆拟合：x²+y² + D x + E y + F = 0。

    解 3x3 正规方程（纯手写高斯消元，不依赖 numpy）。
    返回 {cx, cy, r, rms, n}。
    """
    n = len(pts)
    if n < 3:
        return None
    sx = sy = sxx = syy = sxy = sz = sxz = syz = 0.0
    for (x, y) in pts:
        z = x * x + y * y
        sx += x; sy += y; sz += z
        sxx += x * x; syy += y * y; sxy += x * y
        sxz += x * z; syz += y * z
    # [sxx sxy sx][D]   [-sxz]
    # [sxy syy sy][E] = [-syz]
    # [sx  sy  n ][F]   [-sz ]
    A = [[sxx, sxy, sx, -sxz],
         [sxy, syy, sy, -syz],
         [sx, sy, float(n), -sz]]
    # 高斯消元
    for i in range(3):
        p = max(range(i, 3), key=lambda r: abs(A[r][i]))
        if abs(A[p][i]) < 1e-18:
            return None
        A[i], A[p] = A[p], A[i]
        pv = A[i][i]
        for j in range(i, 4):
            A[i][j] /= pv
        for r in range(3):
            if r == i:
                continue
            f = A[r][i]
            if f:
                for j in range(i, 4):
                    A[r][j] -= f * A[i][j]
    D, E, F = A[0][3], A[1][3], A[2][3]
    cx, cy = -D / 2.0, -E / 2.0
    rr = cx * cx + cy * cy - F
    if rr <= 0:
        return None
    r = math.sqrt(rr)
    ds = [math.hypot(x - cx, y - cy) - r for (x, y) in pts]
    rms = math.sqrt(sum(d * d for d in ds) / n)
    return {"cx": cx, "cy": cy, "r": r, "rms": rms, "n": n,
            "max": max(abs(d) for d in ds)}


def main():
    print("=== 1. 读 STL ===")
    verts, faces, n_hdr = load_stl(STL)
    print("  声明面数 %d / 实际 %d, 唯一顶点 %d" % (n_hdr, len(faces), len(verts)))
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]; zs = [v[2] for v in verts]
    bbox = {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}
    dims = [bbox["max"][i] - bbox["min"][i] for i in range(3)]
    print("  bbox %s ~ %s  dims=%.3f x %.3f x %.3f" % (
        [round(v, 3) for v in bbox["min"]], [round(v, 3) for v in bbox["max"]],
        dims[0], dims[1], dims[2]))

    print("\n=== 2. 法向筛（+Z, 30°）===")
    r = NFF.filter_faces(verts, faces, (0, 0, 1), 30)
    print("  命中 %d / %d 面 (%.2f%%)" % (len(r["kept"]), len(faces),
                                       100.0 * len(r["kept"]) / len(faces)))
    angles = r["angles"]

    print("\n=== 3. 主朝向族（法向取整 0.1 聚类）===")
    cnt = collections.Counter()
    for fi in range(len(faces)):
        f = faces[fi]
        nn = NFF.face_normal(verts, f)
        if not nn:
            continue
        key = (round(nn[0], 1), round(nn[1], 1), round(nn[2], 1))
        cnt[key] += 1
    top = cnt.most_common(8)
    for k, c in top:
        print("  %-22s %8d 面 (%5.2f%%)" % (str(k), c, 100.0 * c / len(faces)))

    print("\n=== 4. 顶面拟合（近 +Z 的 %d 面）===" % len(r["kept"]))
    top_pts = SF.faces_to_points(verts, faces, r["kept"])
    plane = SF.fit_plane(top_pts)
    dev = SF.deviation_stats(top_pts, plane) if plane else None
    if plane:
        print("  normal=%s  origin=%s" % (
            tuple(round(x, 4) for x in plane["normal"]),
            tuple(round(x, 4) for x in plane["origin"])))
        print("  顶点 %d, RMS=%.4f  max=%.4f  within0.5=%.1f%%" % (
            dev["n"], dev["rms"], dev["max"], dev["within_0_5mm"] * 100))
    else:
        print("  拟合失败")

    print("\n=== 5. 侧壁圆拟合（80–100°，居中水平面）===")
    side_idx = [i for i, a in enumerate(angles) if a is not None and 80 <= a <= 100]
    print("  侧壁面 %d (%.2f%%)" % (len(side_idx), 100.0 * len(side_idx) / len(faces)))
    # 侧壁点：按 z 分层取，避免 4 万个点全塞进 2D 拟合（也顺便得到剖面）
    zmin, zmax = bbox["min"][2], bbox["max"][2]
    NB = 12
    layers = [[] for _ in range(NB)]
    all_side = []
    for fi in side_idx:
        f = faces[fi]
        for vi in f:
            v = verts[vi]
            all_side.append(v)
            b = min(NB - 1, int((v[2] - zmin) / max(1e-9, zmax - zmin) * NB))
            layers[b].append((v[0], v[1]))
    prof = []
    for b in range(NB):
        zc = zmin + (b + 0.5) * (zmax - zmin) / NB
        if len(layers[b]) < 8:
            continue
        # 每层用质心半径（对开口环也稳），再跑 Kasa 圆
        cx = sum(p[0] for p in layers[b]) / len(layers[b])
        cy = sum(p[1] for p in layers[b]) / len(layers[b])
        rr = [math.hypot(p[0] - cx, p[1] - cy) for p in layers[b]]
        circ = fit_circle_2d(layers[b])
        prof.append({"z": round(zc, 4), "n": len(layers[b]),
                     "r_mean": round(sum(rr) / len(rr), 4),
                     "r_min": round(min(rr), 4), "r_max": round(max(rr), 4),
                     "circle": {k: round(v, 4) for k, v in circ.items()} if circ else None})
        print("  z=%6.3f  n=%6d  r_mean=%.4f  [%.4f, %.4f]  %s" % (
            zc, len(layers[b]), sum(rr) / len(rr), min(rr), max(rr),
            ("kasa r=%.4f rms=%.5f" % (circ["r"], circ["rms"])) if circ else ""))

    # 全侧壁圆柱（若 z 剖面近似常半径）
    circ_all = fit_circle_2d([(p[0], p[1]) for p in all_side])
    if circ_all:
        print("\n  全侧壁 Kasa: cx=%.4f cy=%.4f r=%.4f rms=%.5f (n=%d)" % (
            circ_all["cx"], circ_all["cy"], circ_all["r"], circ_all["rms"], circ_all["n"]))

    print("\n=== 6. 连通分区 + 逐块平面拟合（修正版）===")
    segs = SEG.face_components(faces, r["kept"])
    segs.sort(key=len, reverse=True)
    print("  连通块 %d 个（最大 %d 面 / 最小 %d 面）" % (
        len(segs), len(segs[0]) if segs else 0, len(segs[-1]) if segs else 0))
    fits = SEG.fit_segments(verts, faces, segs, rms_tol=0.5, top_n=12, min_faces=8)
    print("  面积 top 块：")
    for s in fits[:8]:
        print("   " + SEG.summarize(s))
    ok_n = sum(1 for s in fits if s["accepted"])
    print("  合格块(RMS<=0.5): %d/%d" % (ok_n, len(fits)))

    result = {
        "source": STL,
        "units_hint": UNITS_HINT + " " + SCALE_HINT
                       + " 旧结论『1.044 读作 104.4 mm / ×100』已被用户实测 16 cm 推翻。",
        "faces": len(faces), "verts": len(verts), "bbox": bbox, "dims": dims,
        "normal_filter": {"dir": [0, 0, 1], "angle_deg": 30,
                          "kept": len(r["kept"]), "total": len(faces)},
        "normal_families": [{"normal": list(k), "faces": c} for k, c in top],
        "top_plane": ({"origin": list(plane["origin"]), "normal": list(plane["normal"]),
                       "rms": plane["rms"], "max_dev": plane["max_dev"], "n": plane["n"],
                       "deviation": dev} if plane else None),
        "side": {"faces": len(side_idx), "kasa": circ_all, "z_profile": prof},
        "segments": [{"id": s["id"], "faces": s["faces"], "verts": s["verts"],
                      "area": s["area"], "origin": s["origin"],
                      "normal": s["normal"], "rms": s["rms"], "max": s["max"],
                      "accepted": s["accepted"],
                      "vertices": s["vertices"],
                      "local_faces": s["local_faces"]} for s in fits],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("\n-> %s" % OUT)


if __name__ == "__main__":
    main()
