# -*- coding: utf-8 -*-
"""connected_growth.py —— 面级连通生长（P1 核心，自研）

解决什么问题
------------
猫爪笔筒的 5 个肉垫，法向筛（+Z, 30°）只留下了每个肉垫**顶部的小球冠**。
用这批窄冠点做球拟合，覆盖半角只有 31–36°，球心与半径强耦合、定不住：
实测 R=0.096/0.139/0.040/0.437/0.076，其中两块是病态解（球心跑到模型外）。

`pad_grow.py` 试过「全网格顶点到球心的距离直方图」补球壳，得到 5 个看起来
RELIABLE 的半径 —— **全是假峰**。原因：150 万面的密集网格里，任意大球壳都会
与筒壁、其他肉垫相交，band 点散落整个模型而不是一片连续曲面。
脚本已标 DEPRECATED，保留作反面教材。

本模块坚持唯一正确的判据：**一片连通曲面**。

    种子块 → 沿共享边 BFS 扩展 → 邻面必须同时满足
        (a) 质心到当前球心的距离落在 R ± tol（局部球壳）
        (b) 面法向 · 径向 > cos45°（凸球面外法向朝径向）
           → 每轮用生长后的点重拟合球 → 直到点数/半径稳定
           → 覆盖半角 ≥ 60° 才输出半径，否则只输出类型

设计要点 / 诚实边界
------------------
1. **邻接用 CSR 倒排**（vertex -> 面索引），内存 O(3n) 的 int32 数组，
   不建 450 万条边的 dict；两个面共享 ≥2 顶点才算相邻（即共享一条边）。
2. **tol 退火**：窄冠拟合的残差很小，但把小残差当 tol 外推到冠边缘会立刻失败
   （R 偏了，误差不在残差里而在外推里）。所以前几轮 tol 放到 0.20·R 让生长启动，
   随轮次指数收紧，后期交给 3·rms 主导。这是工程上绕过「窄冠外推病态」的办法，
   **不是**从数据里推出了额外信息——半径最终仍由生长后的覆盖角定住。
3. **axis 固定为种子块的平均面法向**，不随轮次变，覆盖半角才可前后比较。
4. 生长上限 `max_faces` 与 `max_iter`，防止沿筒壁无限蔓延；
   每轮记录 added / rejected_shell / rejected_normal，便于判断卡在哪一步。
5. 纯标准库，不依赖 Rhino / numpy，可在外部脚本与 Rhino 端共用。

用法
----
    python connected_growth.py --selftest   # 合成球冠测试，验证算法本身
    python connected_growth.py --real       # 真实猫爪笔筒 STL（150 万面）
"""
from __future__ import division

import json
import math
import os
import sys
import time
from array import array

_HERE = os.path.dirname(os.path.abspath(__file__))
_NFF = os.path.join(_HERE, "..", "..", "nff", "python")
for _p in (_HERE, _NFF):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import spherefit_core as SP
import surfacefit_core as SF
import nff_core as NFF
import segment_core as SEG
import stl_chain  # 复用 load_stl（其 __main__ 守卫不会触发）
from units import (MM_PER_UNIT, MODEL_HEIGHT_MM, BBOX_Z, mm, UNITS_HINT)

STL = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\stl\model.stl"
CATPAW_JSON = os.path.join(_HERE, "catpaw_result.json")
OUT_JSON = os.path.join(_HERE, "connected_growth_result.json")
OUT_TXT = os.path.join(_HERE, "connected_growth_report.txt")


# ---------------------------------------------------------------------------
# 邻接：CSR 倒排（vertex -> faces）
# ---------------------------------------------------------------------------
def build_adjacency(verts, faces):
    """返回 (off, adj)：off[vi]..off[vi+1] 是 adj 中该顶点所属的面索引。

    全网格 150 万面 / 75 万顶点时，adj 只有 450 万个 int32（约 18 MB），
    比建「边 -> 面」的 dict 省一个数量级。
    """
    nv = len(verts)
    deg = array("i", [0]) * nv
    for f in faces:
        for vi in f:
            deg[vi] += 1
    off = array("i", [0]) * (nv + 1)
    s = 0
    for i in range(nv):
        off[i] = s
        s += deg[i]
    off[nv] = s
    adj = array("i", [0]) * s
    cur = off[:-1]                      # 切片即副本，作填充游标
    for fi, f in enumerate(faces):
        for vi in f:
            adj[cur[vi]] = fi
            cur[vi] += 1
    return off, adj


def adjacent_faces(fi, faces, off, adj, shared_min=2):
    """与 fi 共享至少 shared_min 个顶点的邻面（共享一条边）。"""
    cnt = {}
    for vi in faces[fi]:
        for k in range(off[vi], off[vi + 1]):
            fj = adj[k]
            cnt[fj] = cnt.get(fj, 0) + 1
    return [fj for fj, c in cnt.items() if c >= shared_min and fj != fi]


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def _len(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _unit(v):
    L = _len(v)
    return (v[0] / L, v[1] / L, v[2] / L) if L > 1e-12 else None


def _centroid(verts, f):
    n = len(f)
    return tuple(sum(verts[vi][k] for vi in f) / n for k in range(3))


def _mean_face_normal(verts, faces, indices):
    acc = [0.0, 0.0, 0.0]
    used = 0
    for fi in indices:
        n = NFF.face_normal(verts, faces[fi])
        if n is None:
            continue
        for k in range(3):
            acc[k] += n[k]
        used += 1
    return _unit(acc) if used else (0.0, 0.0, 1.0)


def _points_of(verts, faces, indices):
    """去重顶点点集（与 SF.faces_to_points 同义，但接受 set）。"""
    seen = set()
    pts = []
    for fi in indices:
        for vi in faces[fi]:
            if vi not in seen:
                seen.add(vi)
                pts.append(verts[vi])
    return pts


DEFAULT_CFG = {
    "cos_normal_radial": 0.7071,   # cos45°：法向必须与径向同向
    "tol_rms_factor": 3.0,         # 后期 tol 下限 = 3·rms
    "tol_R_start": 0.20,           # 首轮 tol = 0.20·R（退火起点）
    "tol_R_decay": 0.88,           # 每轮 ×0.88
    "tol_R_floor": 0.01,           # 退火下限 = 0.01·R
    "tol_min_abs": 0.0005,         # 绝对下限（数值单位 = 0.05 mm）
    "max_iter": 150,           # 真实肉垫球冠圈数多，60 轮会被截断（实测三块都跑满）
    "max_faces": 200000,
    "converge_dR_rel": 1e-3,
    "min_span_deg": 60.0,          # 覆盖半角下限，达到才输出半径
    "max_span_deg": 120.0,         # 上限：超过 = 点包围球心 / 串入他物，不是球冠
    "degenerate_span_deg": 120.0,  # 种子病态阈值，命中则跳过生长
    "min_growth_factor": 1.2,      # 没长出去 = 判据全拒绝，不能给半径
    "R_drift_max": 0.02,           # 末 10 轮 R 漂移 >2% = 未收敛
    "rms_over_R_reliable": 0.05,   # rms/R 超过此值判不可靠
}


# ---------------------------------------------------------------------------
# 核心：面级连通生长 + 逐轮球重拟合
# ---------------------------------------------------------------------------
def grow_region(verts, faces, off, adj, seed, cfg=None):
    """从种子面集合沿共享边生长出完整球面片，逐轮重拟合球。

    seed : 可迭代的面索引（种子块，通常是法向筛留下来的顶部小球冠）
    返回 dict：含 seed/final 面数、球心、半径、rms、覆盖半角、可靠标记与逐轮日志。
    """
    return _grow_region_impl(verts, faces, off, adj, seed, cfg)


def _grow_region_impl(verts, faces, off, adj, seed, cfg_in):
    cfg = dict(DEFAULT_CFG)
    if cfg_in:
        cfg.update(cfg_in)

    S = set(int(i) for i in seed)
    if not S:
        return {"ok": False, "reason": "empty seed"}

    axis = _mean_face_normal(verts, faces, S)   # 固定主方向，覆盖半角可前后比较
    pts = _points_of(verts, faces, S)
    fit = SP.fit_sphere(pts)
    if fit is None:
        return {"ok": False, "reason": "seed sphere fit failed"}
    c, R = (fit[0], fit[1], fit[2]), fit[3]
    rms, mx = SP.rms_sphere(pts, c, R)
    span0 = SP.angular_span(pts, c, axis)

    # 种子病态前置检测：点集在球心两侧对称分布时，拟合出的是「点云包围球」
    # 而非球冠（catpaw 的 #3/#5 正是如此，span0=170°/180°）。此时 BFS 判据
    # 一个邻面都收不进，若强行跑会给出「span 巨大 → 可靠」的假阳性。
    if span0 > cfg["degenerate_span_deg"]:
        return {
            "ok": True, "seed_degenerate": True,
            "seed_faces": len(seed), "final_faces": len(seed),
            "growth_factor": 1.0, "iterations": 0,
            "axis": [round(x, 6) for x in axis],
            "center": [round(x, 6) for x in c],
            "radius": round(R, 6), "radius_mm": round(mm(R), 3),
            "rms": round(rms, 6), "rms_mm": round(mm(rms), 4),
            "span_deg": round(span0, 2), "span0_deg": round(span0, 2),
            "R0": round(R, 6), "truncated": False, "R_drift": 0.0,
            "radius_reliable": False,
            "reason": ("种子覆盖半角 %.1f° > %.0f°：点在球心两侧对称分布，"
                       "拟合出的是『点云包围球』而非球冠，生长判据无法启动；"
                       "只输出类型，不给半径（需换种子，属 P2）"
                       % (span0, cfg["degenerate_span_deg"])),
            "history": [], "face_indices": sorted(S),
        }

    log = []
    frontier = list(S)
    prev_R = R
    converged_rounds = 0

    for it in range(cfg["max_iter"]):
        # 用当前 S 的点重拟合（每轮一次，让 R 随覆盖角增大而收敛）
        pts = _points_of(verts, faces, S)
        fit = SP.fit_sphere(pts)
        if fit is not None:
            c, R = (fit[0], fit[1], fit[2]), fit[3]
            rms, mx = SP.rms_sphere(pts, c, R)

        # tol 退火：前期宽（外推病态），后期交给残差
        fac = max(cfg["tol_R_floor"],
                  cfg["tol_R_start"] * (cfg["tol_R_decay"] ** it))
        tol = max(cfg["tol_min_abs"], cfg["tol_rms_factor"] * rms, fac * R)

        added = 0
        rej_shell = rej_normal = rej_degenerate = 0
        new_frontier = []
        for fi in frontier:
            for fj in adjacent_faces(fi, faces, off, adj):
                if fj in S:
                    continue
                f = faces[fj]
                n = NFF.face_normal(verts, f)
                if n is None:
                    rej_degenerate += 1
                    continue
                cen = _centroid(verts, f)
                dvec = (cen[0] - c[0], cen[1] - c[1], cen[2] - c[2])
                d = _len(dvec)
                radial = _unit(dvec)
                if radial is None:
                    rej_degenerate += 1
                    continue
                if n[0] * radial[0] + n[1] * radial[1] + n[2] * radial[2] < cfg["cos_normal_radial"]:
                    rej_normal += 1
                    continue
                if abs(d - R) > tol:
                    rej_shell += 1
                    continue
                S.add(fj)
                new_frontier.append(fj)
                added += 1

        span = SP.angular_span(_points_of(verts, faces, S), c, axis)
        dR_rel = abs(R - prev_R) / max(R, 1e-12)
        log.append({
            "iter": it, "faces": len(S), "added": added, "tol": round(tol, 6),
            "R": round(R, 6), "center": [round(x, 6) for x in c],
            "rms": round(rms, 6), "span_deg": round(span, 2),
            "dR_rel": round(dR_rel, 6),
            "rej_shell": rej_shell, "rej_normal": rej_normal,
            "rej_degenerate": rej_degenerate,
        })
        prev_R = R
        frontier = new_frontier

        if added == 0:
            converged_rounds += 1
            if converged_rounds >= 1:
                break
        else:
            converged_rounds = 0
        if len(S) >= cfg["max_faces"]:
            break
        if dR_rel < cfg["converge_dR_rel"] and added < max(1, len(S) * 0.01):
            break

    # 最终统计
    pts = _points_of(verts, faces, S)
    fit = SP.fit_sphere(pts)
    if fit is not None:
        c, R = (fit[0], fit[1], fit[2]), fit[3]
        rms, mx = SP.rms_sphere(pts, c, R)
    span = SP.angular_span(pts, c, axis)
    plane = SF.fit_plane(pts)
    plane_rms = plane["rms"] if plane else None
    ratio = (plane_rms / rms) if (plane_rms is not None and rms > 1e-12) else None

    # 末 10 轮 R 漂移：区分「真收敛」与「还在单调漂」（#48 曾 0.040→0.050 一直涨）
    tail = [h["R"] for h in log[-10:]] if log else [R]
    R_drift = ((max(tail) - min(tail)) / max(sum(tail) / len(tail), 1e-12)
               if tail else 0.0)
    growth_factor = len(S) / max(1, len(seed))
    truncated = (len(log) >= cfg["max_iter"]
                 and bool(log) and log[-1]["added"] > 0)

    fails = []
    if span is None or span < cfg["min_span_deg"]:
        fails.append("覆盖半角 %.1f° < %.0f°" % (
            span if span is not None else -1.0, cfg["min_span_deg"]))
    if span is not None and span > cfg["max_span_deg"]:
        fails.append("覆盖半角 %.1f° > %.0f°（包围球/串入他物）" % (
            span, cfg["max_span_deg"]))
    if growth_factor < cfg["min_growth_factor"]:
        fails.append("生长倍率 %.2f < %.1f（邻面全被拒）" % (
            growth_factor, cfg["min_growth_factor"]))
    if R > 0 and rms / R > cfg["rms_over_R_reliable"]:
        fails.append("rms/R=%.3f > %.2f" % (rms / R, cfg["rms_over_R_reliable"]))
    if R_drift > cfg["R_drift_max"]:
        fails.append("末10轮 R 漂移 %.1f%% > %.0f%%（未收敛）" % (
            R_drift * 100, cfg["R_drift_max"] * 100))
    reliable = len(fails) == 0
    if reliable:
        reason = ("PASS：span %.1f° / 生长 ×%.1f / rms/R=%.3f / R漂移 %.1f%%" % (
            span, growth_factor, rms / R, R_drift * 100))
        if truncated:
            reason += " [警告：被 max_iter 截断，覆盖角可能仍能增长，但 R 已稳定]"
    else:
        reason = "；".join(fails) + " → 只输出类型，不给半径"

    return {
        "ok": True, "seed_degenerate": False,
        "seed_faces": len(seed),
        "final_faces": len(S),
        "growth_factor": round(growth_factor, 2),
        "iterations": len(log),
        "truncated": bool(truncated),
        "R_drift": round(R_drift, 6),
        "axis": [round(x, 6) for x in axis],
        "center": [round(x, 6) for x in c],
        "radius": round(R, 6),
        "radius_mm": round(mm(R), 3),
        "rms": round(rms, 6),
        "rms_mm": round(mm(rms), 4),
        "max_dev": round(mx, 6),
        "span_deg": round(span, 2),
        "span0_deg": round(span0, 2),
        "R0": round(log[0]["R"], 6) if log else None,
        "plane_rms": round(plane_rms, 6) if plane_rms is not None else None,
        "ratio_plane_over_sphere": round(ratio, 2) if ratio is not None else None,
        "radius_reliable": bool(reliable),
        "reason": reason,
        "history": log,
        "face_indices": sorted(S),
    }


# ---------------------------------------------------------------------------
# 合成测试：证明算法本身正确，不依赖真机大网格
# ---------------------------------------------------------------------------
def make_cap_mesh(R=1.0, theta0_deg=2.0, theta1_deg=80.0,
                  n_theta=40, n_phi=72, noise=0.004):
    """生成一片球冠三角网格（法向朝外），再附一块不连通的平面作干扰。

    noise：沿径向叠加确定性扰动，模拟扫描噪声。**必须有噪声**——
    否则窄冠点集精确落在球面上，最小二乘会直接给出 R=1.0000，
    就验证不到「窄冠 R 偏 → 生长后收敛」这个 P1 真正要修的病态。

    返回 (verts, faces, seed_faces)，seed = 极角 <= 25° 的窄冠。
    """
    verts, faces = [], []
    for i in range(n_theta + 1):
        th = math.radians(theta0_deg + (theta1_deg - theta0_deg) * i / n_theta)
        for j in range(n_phi):
            ph = 2.0 * math.pi * j / n_phi
            verts.append((R * math.sin(th) * math.cos(ph),
                          R * math.sin(th) * math.sin(ph),
                          R * math.cos(th)))
    if noise > 0:
        noisy = []
        for (x, y, z) in verts:
            L = math.sqrt(x * x + y * y + z * z)
            d = noise * math.sin(11.0 * x + 7.0 * y + 5.0 * z + 0.5)
            k = (L + d) / max(L, 1e-12)
            noisy.append((x * k, y * k, z * k))
        verts = noisy
    for i in range(n_theta):
        for j in range(n_phi):
            a = i * n_phi + j
            b = i * n_phi + (j + 1) % n_phi
            cc = (i + 1) * n_phi + j
            d = (i + 1) * n_phi + (j + 1) % n_phi
            faces.append((a, cc, b))
            faces.append((b, cc, d))
    # 干扰平面：独立顶点，不与球冠共享边
    base = len(verts)
    verts += [(3.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 1.0, 0.0), (3.0, 1.0, 0.0)]
    faces.append((base, base + 1, base + 2))
    faces.append((base, base + 2, base + 3))
    seed = []
    for i in range(n_theta):
        th = theta0_deg + (theta1_deg - theta0_deg) * (i + 0.5) / n_theta
        if th > 25.0:
            break
        for j in range(n_phi):
            seed.append(2 * (i * n_phi + j))
            seed.append(2 * (i * n_phi + j) + 1)
    return verts, faces, seed


def selftest():
    print("=== 合成球冠自检 ===")
    verts, faces, seed = make_cap_mesh()
    off, adj = build_adjacency(verts, faces)
    pts0 = _points_of(verts, faces, set(seed))
    f0 = SP.fit_sphere(pts0)
    ax0 = _mean_face_normal(verts, faces, seed)
    sp0 = SP.angular_span(pts0, f0[:3], ax0)
    print("  网格 %d 面 / 种子 %d 面" % (len(faces), len(seed)))
    print("  生长前：R=%.4f (真值 1.0)  覆盖半角=%.1f° (种子 25°)" % (f0[3], sp0))

    r = grow_region(verts, faces, off, adj, seed)
    print("  生长后：R=%.4f  覆盖半角=%.1f°  面数 %d→%d (×%.1f)  轮数 %d" % (
        r["radius"], r["span_deg"], r["seed_faces"], r["final_faces"],
        r["growth_factor"], r["iterations"]))
    print("  rms=%.6f  rms/R=%.4f  可靠=%s" % (
        r["rms"], r["rms"] / r["radius"], r["radius_reliable"]))
    print("  逐轮：")
    for h in r["history"]:
        print("    it=%-2d faces=%-6d +%-5d tol=%.4f R=%.4f span=%5.1f° "
              "rej(shell/normal)=%d/%d" % (
                  h["iter"], h["faces"], h["added"], h["tol"], h["R"],
                  h["span_deg"], h["rej_shell"], h["rej_normal"]))

    err_R0 = abs(f0[3] - 1.0) / 1.0
    err_R = abs(r["radius"] - 1.0) / 1.0
    ok_R = err_R < 0.02
    ok_converge = err_R < err_R0          # 核心：生长把偏掉的 R 拉回来
    ok_span = r["span_deg"] > 70.0
    ok_plane = all(fi < len(faces) - 2 for fi in r["face_indices"])
    ok_reliable = r["radius_reliable"]
    print("  半径误差：生长前 %.2f%% → 生长后 %.2f%%  (收敛改善 %s)" % (
        err_R0 * 100, err_R * 100, "OK" if ok_converge else "FAIL"))
    print("  判定：R误差 %s / 窄冠收敛 %s / 覆盖半角 %.1f° %s / 未串入干扰平面 %s / 半径可靠 %s" % (
        "OK" if ok_R else "FAIL",
        "OK" if ok_converge else "FAIL",
        r["span_deg"], "OK" if ok_span else "FAIL",
        "OK" if ok_plane else "FAIL",
        "OK" if ok_reliable else "FAIL"))
    passed = ok_R and ok_converge and ok_span and ok_plane and ok_reliable
    print("  => %s" % ("PASS" if passed else "FAIL"))
    return passed


# ---------------------------------------------------------------------------
# 真实猫爪笔筒 STL
# ---------------------------------------------------------------------------
def run_real():
    lines = []

    def say(*a):
        s = " ".join(str(x) for x in a)
        lines.append(s)
        print(s)

    say("=== 面级连通生长 · 真实猫爪笔筒 STL ===")
    t0 = time.time()
    say("[1] 解析二进制 STL ...")
    verts, faces, n_hdr = stl_chain.load_stl(STL)
    say("    面 %d / 唯一顶点 %d  (%.1fs)" % (
        len(faces), len(verts), time.time() - t0))

    t1 = time.time()
    say("[2] 建 CSR 顶点倒排 ...")
    off, adj = build_adjacency(verts, faces)
    say("    adj %d 条  (%.1fs)" % (len(adj), time.time() - t1))

    t2 = time.time()
    say("[3] 法向筛（+Z, 30°）+ 连通分区 + 逐块拟合 ...")
    r = NFF.filter_faces(verts, faces, (0, 0, 1), 30)
    segs = SEG.face_components(faces, r["kept"])
    # 必须与 stl_chain.py 一致：先按面数降序再编号，否则 fit_segments 的 id
    # 是并查集原始分组号（34/11/48/67/57），与 catpaw_result.json 的 0..5 对不上。
    segs.sort(key=len, reverse=True)
    fits = SEG.fit_segments(verts, faces, segs, rms_tol=0.5,
                            top_n=12, min_faces=8)
    say("    命中 %d 面 / 连通块 %d / 输出块 %d  (%.1fs)" % (
        len(r["kept"]), len(segs), len(fits), time.time() - t2))

    # 交叉校验：catpaw_result.json 的类型与初始半径
    prior = {}
    if os.path.exists(CATPAW_JSON):
        try:
            for s in json.load(open(CATPAW_JSON, encoding="utf-8"))["segments"]:
                prior[s["id"]] = s
        except Exception as e:
            say("    (catpaw_result.json 读取失败，跳过对照: %r)" % e)

    say("")
    say("%-4s %8s %8s %10s %10s %8s %-8s" % (
        "id", "seedF", "type", "planeRMS", "sphRMS", "ratio", "catpaw"))
    say("-" * 58)

    results = []
    for fit in fits:
        pts = [tuple(v) for v in fit["vertices"]]
        plane = SF.fit_plane(pts)
        p_rms = plane["rms"] if plane else None
        sph = SP.fit_sphere(pts)
        if sph:
            s_rms = SP.rms_sphere(pts, sph[:3], sph[3])[0]
            R0 = sph[3]
        else:
            s_rms, R0 = None, None
        ratio = (p_rms / s_rms) if (p_rms and s_rms and s_rms > 1e-12) else None
        stype = "SPHERE" if (ratio is not None and ratio > 2.0) else "PLANE"
        pj = prior.get(fit["id"], {})
        say("%-4s %8d %8s %10s %10s %8s %-8s" % (
            fit["id"], fit["faces"], stype,
            ("%.6f" % p_rms) if p_rms else "n/a",
            ("%.6f" % s_rms) if s_rms else "n/a",
            ("%.2f" % ratio) if ratio else "n/a",
            pj.get("type", "-")))
        results.append({
            "id": fit["id"], "seed_faces": fit["faces"],
            "seed_area": fit["area"], "type": stype,
            "plane_rms": p_rms, "sphere_rms": s_rms, "ratio": ratio,
            "R0": R0,
            "catpaw_R0": pj.get("sphere_radius"),
            "face_indices": fit["face_indices"],
            "seed_vertices": fit["vertices"],
        })

    say("")
    say("=== [4] 对 SPHERE 块做面级连通生长 ===")
    grown = []
    for seg in results:
        if seg["type"] != "SPHERE":
            continue
        say("")
        say("--- 块 #%d（种子 %d 面, R0=%.4f）---" % (
            seg["id"], seg["seed_faces"], seg["R0"] or 0))
        t3 = time.time()
        g = grow_region(verts, faces, off, adj, seg["face_indices"])
        say("    %s" % ("FAIL: %s" % g.get("reason") if not g.get("ok") else
                       "面数 %d → %d (×%.1f) / %d 轮 / %.1fs" % (
                           g["seed_faces"], g["final_faces"],
                           g["growth_factor"], g["iterations"], time.time() - t3)))
        if g.get("ok"):
            if g.get("seed_degenerate"):
                say("    [种子病态] 跳过生长：%s" % g["reason"])
            else:
                say("    R %.4f → %.4f (%.2f mm)   rms %.6f (%.4f mm)" % (
                    g["R0"] or 0, g["radius"], g["radius_mm"],
                    g["rms"], g["rms_mm"]))
                say("    覆盖半角 %.1f° → %.1f°   平面/球 RMS 比 %.2f" % (
                    g["span0_deg"], g["span_deg"],
                    g.get("ratio_plane_over_sphere") or 0))
                say("    末10轮 R漂移 %.1f%%   截断=%s" % (
                    g.get("R_drift", 0) * 100, g.get("truncated", False)))
            say("    半径可靠：%s —— %s" % (
                "YES" if g["radius_reliable"] else "NO", g["reason"]))
            if g.get("history"):
                say("    逐轮 R/span：" + "  ".join(
                    "%.3f/%.0f°" % (h["R"], h["span_deg"])
                    for h in g["history"][::max(1, len(g["history"]) // 12)]))
            grown.append({
                "id": seg["id"], "type": "SPHERE",
                "seed_degenerate": g.get("seed_degenerate", False),
                "seed_faces": g["seed_faces"], "final_faces": g["final_faces"],
                "growth_factor": g["growth_factor"],
                "iterations": g["iterations"],
                "truncated": g.get("truncated", False),
                "R_drift": g.get("R_drift", 0.0),
                "R0": g["R0"], "radius": g["radius"],
                "radius_mm": g["radius_mm"],
                "center": g["center"], "axis": g["axis"],
                "rms": g["rms"], "rms_mm": g["rms_mm"],
                "span0_deg": g["span0_deg"], "span_deg": g["span_deg"],
                "plane_rms": g.get("plane_rms"),
                "ratio_plane_over_sphere": g.get("ratio_plane_over_sphere"),
                "radius_reliable": g["radius_reliable"],
                "reason": g["reason"],
                "history": g["history"],
                "face_indices": g["face_indices"],
            })
        else:
            grown.append({"id": seg["id"], "type": "SPHERE",
                          "error": g.get("reason")})

    # 平面块原样保留，供 Rhino 回写
    for seg in results:
        if seg["type"] == "PLANE":
            grown.append({"id": seg["id"], "type": "PLANE",
                          "seed_faces": seg["seed_faces"],
                          "final_faces": seg["seed_faces"],
                          "face_indices": seg["face_indices"]})

    n_rel = sum(1 for g in grown
                if g.get("type") == "SPHERE" and g.get("radius_reliable"))
    n_sph = sum(1 for g in grown if g.get("type") == "SPHERE")
    n_deg = sum(1 for g in grown
                if g.get("type") == "SPHERE" and g.get("seed_degenerate"))
    n_trunc = sum(1 for g in grown
                  if g.get("type") == "SPHERE" and g.get("truncated"))
    say("")
    say("=== 汇总 ===")
    say("  球面块 %d，半径可靠 %d，种子病态（跳过生长）%d，生长被截断 %d；总耗时 %.1fs" % (
        n_sph, n_rel, n_deg, n_trunc, time.time() - t0))
    say("  单位换算：1 数值单位 = %.4f mm（用户实测高 %.0f mm ÷ STL Z=%.6f）" % (
        MM_PER_UNIT, MODEL_HEIGHT_MM, BBOX_Z))
    say("  注意：rms_tol=0.5 是数值单位，实际 = %.1f mm，仍过松；P2 应改为按 mm 给定" % mm(0.5))
    say("  可靠判据（5 条全过才给半径）：60° ≤ 覆盖半角 ≤ 120°、生长倍率 ≥1.2、")
    say("  rms/R ≤0.05、末10轮 R 漂移 ≤2%；种子覆盖半角 >120° 直接判病态跳过生长。")
    say("  诚实边界：未达标的块只输出类型，不给半径——这正是 P1 要解决的窄冠病态；")
    say("  两块病态种子需换种子（从肉垫边缘而非顶部法向筛取）才能修，属 P2。")

    out = {
        "source": STL,
        "units_hint": UNITS_HINT,
        "method": "面级连通生长：种子块 → 沿共享边 BFS（|d-R|<tol 且 法向·径向>cos45°）"
                  "→ 每轮重拟合球 → 5 条可靠判据全过才输出半径；"
                  "种子覆盖半角>120° 判病态跳过生长",
        "contrast_with_deprecated_pad_grow":
            "pad_grow.py 用全网格球壳距离直方图，假峰散落全模型；"
            "本模块坚持一片连通曲面，只沿共享边扩展",
        "config": DEFAULT_CFG,
        "total_faces": len(faces), "total_verts": len(verts),
        "normal_filter_kept": len(r["kept"]),
        "segments": grown,
        "summary": {"sphere_regions": n_sph, "reliable_radii": n_rel,
                    "degenerate_seeds": n_deg, "truncated_regions": n_trunc},
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    say("")
    say("-> %s" % OUT_JSON)
    say("-> %s" % OUT_TXT)
    return out


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--real" in sys.argv:
        run_real()
    else:
        print(__doc__)
        print("用法：python connected_growth.py --selftest | --real")
