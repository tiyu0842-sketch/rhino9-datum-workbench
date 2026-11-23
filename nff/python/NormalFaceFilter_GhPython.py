# -*- coding: utf-8 -*-
"""
NormalFaceFilter_GhPython.py
============================
Grasshopper  GhPython 组件脚本：按参考方向（法线夹角）筛选 Mesh 面。

用法：
  1. 在 Grasshopper 里放一个 GhPython 组件（Rhino 7: GhPython / Rhino 8: Python 3 Script）。
  2. 点组件右上角的 ">"/"<" 添加下方输入、输出参数（名字必须完全一致）。
  3. 把本文件路径填进组件的 Script 输入框（或整段粘贴进去）。

输入参数（名字 / 建议类型 / 默认值）：
  Mesh              Mesh      /  必填，待筛选的网格
  Direction         Vector3d  /  (0,0,1)，参考方向；RefFace>=0 时此参数被忽略
  Angle             float     /  30.0，最大夹角（度）
  MinAngle          float     /  0.0，最小夹角（度），用于筛"斜向面带"
  RefFace           int       /  -1，>=0 时改用该序号面的法线作为参考方向
  IncludeOpposite   bool      /  False，True 时把参考方向当轴，正反两面都算
  Bins              str       /  "0,15,30,60,90,120,180"，角度分箱边界，逗号分隔；留空则不分组

输出参数：
  FilteredMesh      Mesh       —— 只含命中面的新网格（按角度着色：红0°→绿90°→蓝180°）
  KeptFaces         list[int]  —— 命中面的原索引
  RemovedFaces      list[int]  —— 被剔除面的原索引
  Angles            list[float]—— 每个面与参考方向的夹角（度），与原面序一致
  AngleGroups       tree       —— 按角度分箱的面索引（每个分支=一个角度区间）
  Info              str        —— 统计摘要

兼容性：IronPython 2.7 (Rhino 7) / Python 3 (Rhino 8)。
"""

import math
import Rhino.Geometry as rg


# ---------------------------------------------------------------------------
# 基础工具（与 python/nff_core.py 中的算法保持一致）
# ---------------------------------------------------------------------------
def _number(value, default):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _unit(v):
    """把 Vector3d / 元组 归一化为 Vector3d；零向量返回 None。"""
    if v is None:
        return None
    if isinstance(v, rg.Vector3d):
        vec = rg.Vector3d(v.X, v.Y, v.Z)
    else:
        try:
            vec = rg.Vector3d(float(v[0]), float(v[1]), float(v[2]))
        except (TypeError, ValueError, IndexError):
            return None
    if vec.Length < 1e-12:
        return None
    vec.Unitize()
    return vec


def _angle_between(a, b):
    """两个 Vector3d 的夹角（度）。"""
    if a is None or b is None:
        return None
    # 真机修正（2026-11-22）：RhinoCommon 9 的 Vector3d 没有 DotProduct 静态方法，
    # 点积用运算符 * （底层 Multiply）。
    dot = a * b
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


def _face_normal(mesh, face_index):
    """直接由顶点坐标叉乘得到面法线（不依赖 FaceNormals 缓存）。"""
    face = mesh.Faces[face_index]
    try:
        a = mesh.Vertices[face.A]
        b = mesh.Vertices[face.B]
        c = mesh.Vertices[face.C]
        n = rg.Vector3d.CrossProduct(b - a, c - a)
        if face.IsQuad:
            d = mesh.Vertices[face.D]
            n = n + rg.Vector3d.CrossProduct(c - a, d - a)
    except Exception:
        return None
    if n.Length < 1e-12:
        return None
    n.Unitize()
    return n


def _extract_faces(mesh, indices):
    """按原面索引重建一个只含命中面的新 Mesh，并复制原顶点位置。"""
    out = rg.Mesh()
    for face_index in indices:
        face = mesh.Faces[face_index]
        try:
            if face.IsTriangle:
                i0 = out.Vertices.Add(mesh.Vertices[face.A])
                i1 = out.Vertices.Add(mesh.Vertices[face.B])
                i2 = out.Vertices.Add(mesh.Vertices[face.C])
                out.Faces.AddFace(i0, i1, i2)
            elif face.IsQuad:
                i0 = out.Vertices.Add(mesh.Vertices[face.A])
                i1 = out.Vertices.Add(mesh.Vertices[face.B])
                i2 = out.Vertices.Add(mesh.Vertices[face.C])
                i3 = out.Vertices.Add(mesh.Vertices[face.D])
                out.Faces.AddFace(i0, i1, i2, i3)
        except Exception:
            continue
    try:
        out.Normals.ComputeNormals()
    except Exception:
        pass
    return out


def _color_for_angle(theta):
    """0°=红, 90°=绿, 180°=蓝，中间线性过渡。"""
    import System.Drawing
    if theta is None:
        return System.Drawing.Color.FromArgb(150, 150, 150)
    t = max(0.0, min(180.0, theta)) / 90.0
    if t <= 1.0:
        r = int(round(255 * (1.0 - t)))
        g = int(round(255 * t))
        b = 0
    else:
        r = 0
        g = int(round(255 * (2.0 - t)))
        b = int(round(255 * (t - 1.0)))
    return System.Drawing.Color.FromArgb(r, g, b)


def _paint_mesh(mesh, angles, indices):
    """给筛选后的网格按夹角着色（失败不影响主功能）。"""
    try:
        mesh.VertexColors.CreateMonotoneMesh(_color_for_angle(None))
        # 新网格每个面有自己的顶点，按面对应上色即可
        slot = 0
        for face_index in indices:
            color = _color_for_angle(angles[face_index])
            face = mesh.Faces[slot]
            mesh.VertexColors[face.A] = color
            mesh.VertexColors[face.B] = color
            mesh.VertexColors[face.C] = color
            if face.IsQuad:
                mesh.VertexColors[face.D] = color
            slot += 1
    except Exception:
        pass
    return mesh


def _parse_bins(text):
    if text is None:
        return []
    parts = []
    for chunk in str(text).replace("，", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            parts.append(float(chunk))
        except ValueError:
            continue
    parts = sorted(set(parts))
    return [(parts[i], parts[i + 1]) for i in range(len(parts) - 1)]


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
FilteredMesh = rg.Mesh()
KeptFaces = []
RemovedFaces = []
Angles = []
AngleGroups = []
Info = ""

if Mesh is None or Mesh.Faces.Count == 0:
    Info = "[NormalFaceFilter] 请输入非空 Mesh。"
else:
    max_angle = _number(Angle, 30.0)
    min_angle = _number(MinAngle, 0.0)
    max_angle = max(0.0, min(180.0, max_angle))
    min_angle = max(0.0, min(180.0, min_angle))
    if min_angle > max_angle:
        min_angle, max_angle = max_angle, min_angle

    opposite = bool(IncludeOpposite) if IncludeOpposite is not None else False

    # 参考方向：优先使用指定面的法线
    ref_face = int(_number(RefFace, -1))
    ref_dir = None
    if 0 <= ref_face < Mesh.Faces.Count:
        ref_dir = _face_normal(Mesh, ref_face)
    if ref_dir is None:
        ref_dir = _unit(Direction)
    if ref_dir is None:
        ref_dir = rg.Vector3d(0, 0, 1)  # 兜底：世界 Z 轴

    total = Mesh.Faces.Count
    for i in range(total):
        n = _face_normal(Mesh, i)
        theta = _angle_between(n, ref_dir)
        if theta is None:
            Angles.append(None)
            RemovedFaces.append(i)
            continue
        Angles.append(theta)
        hit = (min_angle <= theta <= max_angle)
        if opposite and (min_angle <= (180.0 - theta) <= max_angle):
            hit = True
        if hit:
            KeptFaces.append(i)
        else:
            RemovedFaces.append(i)

    FilteredMesh = _extract_faces(Mesh, KeptFaces)
    FilteredMesh = _paint_mesh(FilteredMesh, Angles, KeptFaces)

    bins = _parse_bins(Bins)
    if bins:
        AngleGroups = [[] for _ in bins]
        for i in KeptFaces:
            theta = Angles[i]
            if theta is None:
                continue
            for b, (low, high) in enumerate(bins):
                if low <= theta <= high:
                    AngleGroups[b].append(i)
                    break

    Info = ("总面数 %d | 命中 %d | 剔除 %d | 参考方向 (%.3f, %.3f, %.3f) "
            "| 角度区间 %.1f° ~ %.1f° | 反向包含 %s | 参考面 %s"
            % (total, len(KeptFaces), len(RemovedFaces),
               ref_dir.X, ref_dir.Y, ref_dir.Z,
               min_angle, max_angle,
               "是" if opposite else "否",
               str(ref_face) if 0 <= ref_face < total else "无"))
