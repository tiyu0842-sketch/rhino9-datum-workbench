# -*- coding: utf-8 -*-
"""spherefit_core.py - 最小二乘球拟合，纯标准库。

方程：2*c·p + w = |p|²，其中 w = R² - |c|²
对 (cx, cy, cz, w) 是线性的，解 4x4 正规方程即可，不需要 numpy / Rhino，
所以既能在大网格脚本里跑，也能在 Rhino 外部跑。

注意：窄球冠（覆盖角 < 30°）的病态问题不是算法能解决的——
数据本身不含足够曲率信息，任何拟合都会把半径估偏。
本模块只保证"给定点集的最优球"，不保证"点集足以定球"。
"""
import math


def solve_linear(A, b):
    """高斯消元（列主元）。A: n*n，b: n。返回解列表或 None（奇异）。"""
    n = len(b)
    M = [list(map(float, A[i])) + [float(b[i])] for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(M[r][i]))
        if abs(M[p][i]) < 1e-18:
            return None
        M[i], M[p] = M[p], M[i]
        pv = M[i][i]
        for j in range(i, n + 1):
            M[i][j] /= pv
        for r in range(n):
            if r == i:
                continue
            f = M[r][i]
            if f:
                for j in range(i, n + 1):
                    M[r][j] -= f * M[i][j]
    return [M[i][n] for i in range(n)]


def fit_sphere(points):
    """返回 (cx, cy, cz, R) 或 None。points 为 [(x,y,z), ...]。"""
    n = len(points)
    if n < 4:
        return None
    A = [[0.0] * 4 for _ in range(4)]
    b = [0.0] * 4
    for (x, y, z) in points:
        row = (2.0 * x, 2.0 * y, 2.0 * z, 1.0)
        q = x * x + y * y + z * z
        for i in range(4):
            for j in range(4):
                A[i][j] += row[i] * row[j]
            b[i] += row[i] * q
    s = solve_linear(A, b)
    if s is None:
        return None
    cx, cy, cz, w = s
    rr = w + cx * cx + cy * cy + cz * cz
    if not (rr > 0):
        return None
    return (cx, cy, cz, math.sqrt(rr))


def rms_sphere(points, c, R):
    """径向距离误差的 (rms, max_abs)。"""
    if not points:
        return (None, None)
    ds = [math.sqrt((p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 +
                    (p[2] - c[2]) ** 2) - R for p in points]
    return (math.sqrt(sum(d * d for d in ds) / len(ds)),
            max(abs(d) for d in ds))


def angular_span(points, center, axis, step_deg=2.0):
    """点集相对球心、以 axis 为主方向的覆盖半角（度）。

    用于判断"这块数据到底覆盖了球的多大范围"：
    覆盖半角 < 20° 时，球半径基本定不住。
    """
    if not points:
        return None
    ax, ay, az = axis
    ln = math.sqrt(ax * ax + ay * ay + az * az)
    if ln < 1e-12:
        return None
    ax, ay, az = ax / ln, ay / ln, az / ln
    best = 0.0
    for p in points:
        vx, vy, vz = p[0] - center[0], p[1] - center[1], p[2] - center[2]
        l = math.sqrt(vx * vx + vy * vy + vz * vz)
        if l < 1e-12:
            continue
        d = (vx * ax + vy * ay + vz * az) / l
        d = max(-1.0, min(1.0, d))
        a = math.degrees(math.acos(d))
        if a > best:
            best = a
    return best
