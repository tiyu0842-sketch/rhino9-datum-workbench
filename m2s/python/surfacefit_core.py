# -*- coding: utf-8 -*-
"""
surfacefit_core.py —— Mesh→Surface 逆向的纯数学内核（P0）

不依赖 Rhino / numpy，只用标准库。这样即使 Rhino 不可用也能验证算法。
与 NFF 的衔接：NFF 输出面索引 → 本模块取这些面的顶点 → 拟合 → 算偏差。

实现三个函数（P0 闭环）：
  1. face_curvature   —— 面/顶点的高斯曲率与平均曲率估计（离散差分）
  2. fit_plane        —— 点集最小二乘拟合平面（协方差最小特征向量，幂迭代求法向）
  3. deviation_stats  —— 点到平面的偏差统计（均值/RMS/最大）

约定：顶点是 (x,y,z) tuple，面是顶点索引 list。法向用右手定则。
"""

import math

# ---------------------------------------------------------------------------
# 向量基础（与 nff_core 保持同款约定，避免两套坐标系）
# ---------------------------------------------------------------------------
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def length(a):
    return math.sqrt(dot(a, a))


def normalize(v):
    L = length(v)
    return mul(v, 1.0 / L) if L > 1e-12 else (0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# 1. 曲率估计
# ---------------------------------------------------------------------------
def face_curvature(vertices, faces, face_index):
    """估计某个三角/四边形面的离散曲率（用相邻面法向夹角 / 边长）。

    返回 dict: {gaussian, mean, normal, area, center}
    - gaussian ≈ 相邻面法向夹角之和 / 面积（离散高斯曲率，角亏）
    - mean     ≈ 法向变化率沿边的投影平均
    这是 Shannon 离散曲率的简化版，用于"筛选"足够；不是精确微分几何值。
    """
    f = faces[face_index]
    if len(f) < 3:
        return None
    pts = [vertices[i] for i in f]
    # 面法向（Newell 法，对多边形比叉乘稳）
    n = (0.0, 0.0, 0.0)
    for i in range(len(pts)):
        p, q = pts[i], pts[(i + 1) % len(pts)]
        nx = (p[1] - q[1]) * (p[2] + q[2])
        ny = (p[2] - q[2]) * (p[0] + q[0])
        nz = (p[0] - q[0]) * (p[1] + q[1])
        n = (n[0] + nx, n[1] + ny, n[2] + nz)
    n = normalize(n)
    if dot(n, n) < 1e-12:
        return None
    center = mul(tuple(sum(p[k] for p in pts) for k in range(3)),
                 1.0 / len(pts))
    # 面积（三角扇）
    area = 0.0
    for i in range(1, len(pts) - 1):
        area += 0.5 * length(cross(sub(pts[i], pts[0]), sub(pts[i + 1], pts[0])))

    # 相邻面判断：
    # 不能只靠共享顶点索引——Rhino 的 Mesh.CreateFromBox 每个面用独立顶点
    # （6 面 24 顶点），索引不共享，纯拓扑判断会得到 neighbors=0 的假阴性。
    # 兜底：用面中心距离 < 阈值（阈值取本面尺寸 + 邻面尺寸）判定几何相邻。
    verts = set(f)
    neighbors = []
    diag = math.sqrt(area) if area > 0 else 1.0
    for j, g in enumerate(faces):
        if j == face_index or len(g) < 3:
            continue
        topo = bool(verts.intersection(g))
        gp = [vertices[i] for i in g]
        gc = tuple(sum(p[k] for p in gp) / len(gp) for k in range(3))
        dist = length(sub(gc, center))
        geo = dist < 1.5 * max(diag, math.sqrt(max(_area(vertices, g), 1e-9)))
        if topo or geo:
            gn = _face_normal(vertices, g)
            if gn:
                neighbors.append(gn)
    if not neighbors or area < 1e-12:
        return {"gaussian": 0.0, "mean": 0.0, "normal": n,
                "area": area, "center": center, "neighbors": 0}

    # 角亏（离散高斯曲率）：平均法向夹角 / 面积
    angles = []
    for gn in neighbors:
        c = max(-1.0, min(1.0, dot(n, gn)))
        angles.append(math.acos(c))
    mean_angle = sum(angles) / len(angles)
    gaussian = mean_angle / area
    mean = gaussian * 0.5  # 简化；平面/球面上与 k1≈k2 一致
    return {"gaussian": gaussian, "mean": mean, "normal": n,
            "area": area, "center": center, "neighbors": len(neighbors)}


def _face_normal(vertices, f):
    if len(f) < 3:
        return None
    a, b, c = (vertices[f[0]], vertices[f[1]], vertices[f[2]])
    return normalize(cross(sub(b, a), sub(c, a)))


def _area(vertices, f):
    """三角扇面积，用于相邻判定的尺度估计。"""
    pts = [vertices[i] for i in f]
    a = 0.0
    for i in range(1, len(pts) - 1):
        a += 0.5 * length(cross(sub(pts[i], pts[0]), sub(pts[i + 1], pts[0])))
    return a


# ---------------------------------------------------------------------------
# 2. 平面最小二乘拟合
# ---------------------------------------------------------------------------
def fit_plane(points, max_iter=80, tol=1e-10):
    """对点集拟合最小二乘平面。

    原理：点集协方差矩阵的最小特征向量 = 平面法向。
          没有 numpy，用幂迭代求 **最大** 特征向量，再用"移位矩阵" B = λI - C
          求最小特征向量（λ 取 trace(C)）。

    返回 dict: {origin, normal, rms, max_dev, n}
    """
    pts = [p for p in points if p is not None and len(p) == 3]
    n = len(pts)
    if n < 3:
        return None
    cx = tuple(sum(p[k] for p in pts) / n for k in range(3))
    # 协方差 3x3
    C = [[0.0] * 3 for _ in range(3)]
    for p in pts:
        d = sub(p, cx)
        for i in range(3):
            for j in range(3):
                C[i][j] += d[i] * d[j]
    for i in range(3):
        for j in range(3):
            C[i][j] /= n
    lam = C[0][0] + C[1][1] + C[2][2]
    # B = lam*I - C，其最大特征向量对应 C 的最小特征向量
    B = [[(lam if i == j else 0.0) - C[i][j] for j in range(3)] for i in range(3)]
    # 幂迭代初值必须避开任何特征向量：对角阵不会混合分量，
    # 若初值取 (1,0,0) 且它恰好是特征向量，会永远停在那里（实测踩坑）。
    v = (1.0, 1.0, 1.0)
    for _ in range(max_iter):
        w = (dot(B[0], v), dot(B[1], v), dot(B[2], v))
        w = normalize(w)
        if length(sub(w, v)) < tol:
            v = w
            break
        v = w
    if length(v) < 1e-12:
        return None
    # 法向定向：让正向分量较多（稳定朝向，便于复现）
    if v[2] < 0:
        v = mul(v, -1.0)
    # 偏差统计
    devs = [dot(sub(p, cx), v) for p in pts]
    rms = math.sqrt(sum(d * d for d in devs) / n)
    return {"origin": cx, "normal": v, "rms": rms,
            "max_dev": max(abs(d) for d in devs), "n": n}


def signed_distance(point, plane):
    """点到平面的有符号距离。plane 为 fit_plane 的返回。"""
    return dot(sub(point, plane["origin"]), plane["normal"])


def deviation_stats(points, plane):
    """一批点到平面的偏差统计（用于判断拟合是否合格）。"""
    ds = [abs(signed_distance(p, plane)) for p in points if p is not None]
    if not ds:
        return None
    m = sum(ds) / len(ds)
    rms = math.sqrt(sum(d * d for d in ds) / len(ds))
    return {"mean": m, "rms": rms, "max": max(ds),
            "within_0_1mm": sum(1 for d in ds if d <= 0.1) / len(ds),
            "within_0_5mm": sum(1 for d in ds if d <= 0.5) / len(ds),
            "n": len(ds)}


def filter_by_curvature(curvatures, k_max=None, k_min=None):
    """按高斯曲率区间筛面（与 NFF 的 filter_faces 同款区间语义）。"""
    out = []
    for idx, c in enumerate(curvatures):
        if c is None:
            continue
        k = c["gaussian"]
        if k_min is not None and k < k_min:
            continue
        if k_max is not None and k > k_max:
            continue
        out.append(idx)
    return out


def faces_to_points(vertices, faces, indices):
    """把若干面的顶点收集成点集（去重），供 fit_plane 使用。"""
    seen = set()
    pts = []
    for i in indices:
        for vi in faces[i]:
            if vi not in seen:
                seen.add(vi)
                pts.append(vertices[vi])
    return pts
