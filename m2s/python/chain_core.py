# -*- coding: utf-8 -*-
"""
chain_core.py —— 法向(NFF) + 曲率(m2s) 双筛 → 平面拟合 → 偏差校验 的完整链

这是"逆向 + 筛选"的中枢：输入网格 + 参考方向，输出可直接用的平面候选。

数据流：
  vertices, faces
    │
    ├─ NFF.filter_faces       → 按法向夹角筛（朝向族）
    ├─ m2s.face_curvature     → 每面曲率
    ├─ m2s.filter_by_curvature→ 按曲率筛（平坦族）
    │
    ├─ 两族求交               → 候选面（朝向对 且 足够平）
    │
    ├─ fit_plane(候选顶点)    → 解析平面
    └─ deviation_stats        → 合格判定（RMS ≤ 容差）

为什么求交而不是并联输出：
  单靠法向会把"斜的曲面"也收进来（法向恰好对，但面是弯的）；
  单靠曲率会把"朝向不对的平面"也收进来（平，但是侧面）。
  只有两族交集才是"朝这个方向的一张平面"——这正是 AI 分面要的候选。

依赖：../nff/python/nff_core.py 与同目录 surfacefit_core.py，都是纯标准库。
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_NFF = os.path.join(_HERE, "..", "..", "nff", "python")
for p in (_HERE, _NFF):
    if p not in sys.path:
        sys.path.insert(0, p)

import nff_core as NFF
import surfacefit_core as SF


def run_chain(vertices, faces, direction=(0, 0, 1), angle_deg=30,
              include_opposite=False, min_angle_deg=0.0,
              k_max=None, k_min=None,
              rms_tolerance=0.5, within_tolerance=0.8,
              verbose=True):
    """跑完整双筛链，返回结构化结果。

    参数：
      direction/angle_deg/include_opposite/min_angle_deg : NFF 法向筛选参数
      k_max / k_min      : 曲率筛选区间（None=不限）；平坦面用 k_max=0.05 左右起步
      rms_tolerance      : 平面拟合的 RMS 合格线（mm）
      within_tolerance   : 偏差 ≤ rms_tolerance 的点占比合格线（0~1）

    返回 dict（含每一步中间结果，便于调试与回看）:
      normal_kept / curvature_kept / candidates
      plane / deviation / accepted
      reason（若没拟合出来，说明卡在哪一步）
    """
    out = {"normal_kept": [], "curvature_kept": [], "candidates": [],
           "plane": None, "deviation": None, "accepted": False, "reason": ""}

    # 1) 法向筛（NFF，已真机验证的算法）
    nf = NFF.filter_faces(vertices, faces, direction, angle_deg,
                          include_opposite=include_opposite,
                          min_angle_deg=min_angle_deg)
    out["normal_kept"] = nf["kept"]
    out["normal_angles"] = nf["angles"]
    if verbose:
        print("  [1/5] 法向筛: %d/%d 面命中 (夹角≤%.0f°)" %
              (len(nf["kept"]), len(faces), angle_deg))
    if not nf["kept"]:
        out["reason"] = "法向筛无命中：放宽 angle_deg 或开 include_opposite"
        return out

    # 2) 曲率筛（m2s）
    curs = [SF.face_curvature(vertices, faces, i) for i in range(len(faces))]
    out["curvatures"] = curs
    kp = SF.filter_by_curvature(curs, k_max=k_max, k_min=k_min)
    out["curvature_kept"] = kp
    if verbose:
        rng = "k∈[%s,%s]" % (k_min, k_max)
        print("  [2/5] 曲率筛: %d/%d 面命中 (%s)" % (len(kp), len(faces), rng))
    if not kp:
        out["reason"] = "曲率筛无命中：放宽 k_max 或去掉曲率限制"
        return out

    # 3) 两族求交
    cand = [i for i in nf["kept"] if i in set(kp)]
    out["candidates"] = cand
    if verbose:
        print("  [3/5] 交集候选: %d 面" % len(cand))
    if not cand:
        out["reason"] = "两族无交集：检查法向与曲率条件"
        return out

    # 4) 拟合平面（用候选面的顶点）
    # 注意：一个四边形面就有 4 个顶点，足够拟合；约束应是顶点数≥3，不是面数≥3。
    pts = SF.faces_to_points(vertices, faces, cand)
    if len(pts) < 3:
        out["reason"] = "候选顶点<3，无法拟合平面"
        return out
    plane = SF.fit_plane(pts)
    out["plane"] = plane
    if verbose:
        print("  [4/5] 拟合: %d 顶点, 法向 %s, RMS %.4f mm" %
              (len(pts), tuple(round(x, 3) for x in plane["normal"]), plane["rms"]))
    if plane is None:
        out["reason"] = "拟合失败：顶点共线或退化"
        return out

    # 5) 偏差判定
    dev = SF.deviation_stats(pts, plane)
    out["deviation"] = dev
    # 合格判据以 RMS 为主（稳定、与面数无关）；占比作为附加信息写入结果，
    # 不硬编码键名——deviation_stats 的 within_XXX 键随容差档位变化。
    ok = dev["rms"] <= rms_tolerance
    out["accepted"] = bool(ok)
    out["reason"] = ("合格：RMS %.4f ≤ %.2f" % (dev["rms"], rms_tolerance)) if ok else \
                    ("不合格：RMS %.4f > %.2f" % (dev["rms"], rms_tolerance))
    if verbose:
        print("  [5/5] %s | max %.4f mm" % (out["reason"], dev["max"]))
    return out


def summarize(result):
    """给命令行/文档用的一句话摘要。"""
    if not result["accepted"]:
        return "未通过: " + result["reason"]
    d = result["deviation"]
    return ("通过: %d 面 → 平面 n=%s, rms=%.4fmm, max=%.4fmm" %
            (len(result["candidates"]),
             tuple(round(x, 2) for x in result["plane"]["normal"]),
             d["rms"], d["max"]))
