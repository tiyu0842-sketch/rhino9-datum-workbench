# -*- coding: utf-8 -*-
"""segment_core.py —— 候选面的空间分区（连通分量）+ 逐块拟合。

解决真机 STL 暴露的核心问题：
  「法向筛出的面」不等于「一张平面」。真实扫描件里同朝向的面会散落在多处
  （多个台阶面、多个平顶），直接一次性 fit_plane 会被拉歪——
  实测 31,735 个近 +Z 面拟合出的法向与 +Z 差 51°，完全不可用。

正确顺序：法向筛 → 连通分区 → 每块独立拟合 → 按面积/偏差排序。
全部 O(n)（并查集 + 顶点→面倒排），不碰 O(n²) 的曲率。

约定：faces 是顶点索引 tuple；两个面共享 ≥2 个顶点才算相邻（共享一条边）。
"""
import math

_HAS_SF = True
try:
    import surfacefit_core as SF
except Exception:
    _HAS_SF = False


def face_components(faces, candidates):
    """把候选面按"共享边"分组成连通块。返回 [[face_idx, ...], ...]。"""
    cand = list(candidates)
    n = len(cand)
    if n == 0:
        return []
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    # 顶点 -> 候选面局部下标列表
    v2f = {}
    vset = {}
    for k, fi in enumerate(cand):
        f = faces[fi]
        vset[k] = set(f)
        for vi in f:
            v2f.setdefault(vi, []).append(k)

    for vi, ks in v2f.items():
        m = len(ks)
        if m < 2:
            continue
        for i in range(m):
            si = vset[ks[i]]
            for j in range(i + 1, m):
                if len(si & vset[ks[j]]) >= 2:
                    union(ks[i], ks[j])

    groups = {}
    for k in range(n):
        groups.setdefault(find(k), []).append(cand[k])
    return list(groups.values())


def tri_area(p0, p1, p2):
    ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
    cx = ay * bz - az * by
    cy = az * bx - ax * bz
    cz = ax * by - ay * bx
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def segment_area(vertices, faces, seg):
    a = 0.0
    for fi in seg:
        f = faces[fi]
        if len(f) >= 3:
            a += tri_area(vertices[f[0]], vertices[f[1]], vertices[f[2]])
    return a


def fit_segments(vertices, faces, segs, rms_tol=0.5, top_n=12,
                 min_faces=8, min_area=0.0):
    """逐块拟合平面，返回按面积降序的块信息列表。"""
    out = []
    for si, seg in enumerate(segs):
        if len(seg) < min_faces:
            continue
        area = segment_area(vertices, faces, seg)
        if area < min_area:
            continue
        pts = []
        seen = set()
        for fi in seg:
            for vi in faces[fi]:
                if vi not in seen:
                    seen.add(vi)
                    pts.append(vertices[vi])
        # 局部坐标 + 局部面索引：供 Rhino 端按坐标重建，
        # 不依赖 Rhino STL 导入器的面顺序（实测会被重排，直接复用面索引会错位）
        loc = {}
        vlist = []
        for vi in sorted(seen):
            loc[vi] = len(vlist)
            vlist.append(list(vertices[vi]))
        lfaces = []
        for fi in seg:
            lfaces.append([loc[vi] for vi in faces[fi]])
        if _HAS_SF:
            plane = SF.fit_plane(pts)
            dev = SF.deviation_stats(pts, plane) if plane else None
        else:
            plane = dev = None
        if not plane:
            continue
        out.append({
            "id": si,
            "faces": len(seg),
            "verts": len(pts),
            "area": area,
            "origin": list(plane["origin"]),
            "normal": list(plane["normal"]),
            "rms": dev["rms"],
            "max": dev["max"],
            "within_0_5": dev["within_0_5mm"],
            "accepted": dev["rms"] <= rms_tol,
            "face_indices": seg,
            "vertices": vlist,
            "local_faces": lfaces,
        })
    out.sort(key=lambda d: -d["area"])
    return out[:top_n]


def summarize(seg):
    """一行摘要，给人看。"""
    return ("#%d faces=%d area=%.4f n=%s rms=%.4f max=%.4f %s" % (
        seg["id"], seg["faces"], seg["area"],
        tuple(round(x, 3) for x in seg["normal"]),
        seg["rms"], seg["max"], "OK" if seg["accepted"] else "REJECT"))
