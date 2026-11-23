# -*- coding: utf-8 -*-
"""
nff_core.py — 法线方向筛选核心算法（纯 Python，无 Rhino 依赖）

这是整个插件的算法内核。Rhino/GhPython 脚本里内联了同一份逻辑，
本文件的作用是：可以在没有 Rhino 的环境里独立测试算法正确性。

兼容性：Python 2.7 (IronPython / Rhino 7) 与 Python 3.x (Rhino 8) 均可运行。
"""

from __future__ import division
import math

EPS = 1e-12


def normalize(v):
    """把三维向量归一化；零向量或无效输入返回 None。"""
    try:
        x = float(v[0])
        y = float(v[1])
        z = float(v[2])
    except (TypeError, ValueError, IndexError):
        return None
    length = math.sqrt(x * x + y * y + z * z)
    if length < EPS:
        return None
    return (x / length, y / length, z / length)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def angle_degrees(a, b):
    """两个向量的夹角，单位：度，范围 [0, 180]。无效向量返回 None。"""
    na = normalize(a)
    nb = normalize(b)
    if na is None or nb is None:
        return None
    d = dot(na, nb)
    if d > 1.0:
        d = 1.0
    elif d < -1.0:
        d = -1.0
    return math.degrees(math.acos(d))


def face_normal(vertices, face):
    """
    计算一个网格面的单位法线。
    vertices: [(x, y, z), ...]
    face: 顶点索引元组，三角形 (a,b,c) 或四边形 (a,b,c,d)
    返回单位法线元组，退化面/无效索引返回 None。
    """
    if face is None or len(face) < 3:
        return None
    try:
        p0 = vertices[face[0]]
        p1 = vertices[face[1]]
        p2 = vertices[face[2]]
    except (IndexError, TypeError, KeyError):
        return None

    try:
        n = cross(sub(p1, p0), sub(p2, p0))
        if len(face) >= 4:
            p3 = vertices[face[3]]
            n2 = cross(sub(p2, p0), sub(p3, p0))
            n = (n[0] + n2[0], n[1] + n2[1], n[2] + n2[2])
    except (IndexError, TypeError, KeyError):
        return None

    return normalize(n)


def clamp_angle(value, default=0.0):
    """把角度限制在 [0, 180]，非数值返回 default。"""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return float(default)
    return max(0.0, min(180.0, v))


def filter_faces(vertices, faces, direction, angle_deg,
                 include_opposite=False, min_angle_deg=0.0):
    """
    按参考方向筛选网格面。

    参数:
      vertices         : [(x,y,z), ...] 网格顶点
      faces            : [(i,j,k), ...] 或 [(i,j,k,l), ...] 网格面索引
      direction        : 参考方向向量（会归一化）
      angle_deg        : 允许的最大夹角（度）
      include_opposite : True 时，法线与参考方向夹角接近 180 度的面也算匹配
                         （即把参考方向当作"轴"而非"有向向量"）
      min_angle_deg    : 允许的最小夹角（度），用于筛选"斜向"面带，默认 0

    返回 dict:
      kept         : 保留面的索引列表
      removed      : 剔除面的索引列表
      angles       : 每个面与参考方向的夹角（度），退化面为 None
      reference    : 归一化后的参考方向
      max_angle    : 实际使用的最大夹角
      min_angle    : 实际使用的最小夹角
    """
    d = normalize(direction)
    if d is None:
        raise ValueError("参考方向为零向量或无效，无法计算夹角")

    hi = clamp_angle(angle_deg, 0.0)
    lo = clamp_angle(min_angle_deg, 0.0)
    if hi < lo:
        lo, hi = hi, lo

    kept = []
    removed = []
    angles = []

    for index, face in enumerate(faces):
        n = face_normal(vertices, face)
        theta = angle_degrees(n, d) if n is not None else None

        if theta is None:
            angles.append(None)
            removed.append(index)
            continue

        angles.append(theta)
        matched = (lo <= theta <= hi)
        if include_opposite:
            opposite = 180.0 - theta
            matched = matched or (lo <= opposite <= hi)

        if matched:
            kept.append(index)
        else:
            removed.append(index)

    return {
        "kept": kept,
        "removed": removed,
        "angles": angles,
        "reference": d,
        "max_angle": hi,
        "min_angle": lo,
    }


def group_by_bins(indices, angles, bins):
    """
    把面按夹角区间分组，便于后续分面策略。
    bins: [(下限, 上限), ...]，例如 [(0,15),(15,30),(30,60),(60,90)]
    返回 list，长度与 bins 一致，每项为落入该区间的面索引列表。
    """
    groups = [[] for _ in bins]
    for face_index in indices:
        if face_index < 0 or face_index >= len(angles):
            continue
        theta = angles[face_index]
        if theta is None:
            continue
        for i, (low, high) in enumerate(bins):
            if low <= theta <= high:
                groups[i].append(face_index)
                break
    return groups
