# -*- coding: utf-8 -*-
"""
NormalFaceFilter_RhinoCommand.py
================================
RhinoPython 命令脚本：按参考方向筛选 Mesh 面，并把命中面提取成新网格对象。

运行方式（任选其一）：
  A. 命令行输入：_RunPythonScript  然后选中本文件
  B. 建议把它设成别名，之后直接输入 NFF 调用：
     命令行输入 _Alias → New → 名字填 NFF →
     宏内容填：_-RunPythonScript "本文件的完整路径"
  C. Rhino 8 也可放到 %APPDATA%\\McNeel\\Rhinoceros\\8.0\\scripts\\ 下从工具菜单运行

交互流程：
  1. 选择一个 Mesh
  2. 输入参考方向：
       - 预设词：top / bottom / left / right / front / back（也支持 上/下/左/右/前/后）
       - 任意向量：0,0,1  或  1,1,0
       - 取某个面的法线：face:12（0 起始，注意 Rhino 层面序号从 0 数）
       - 直接回车：用 +Z
  3. 最大夹角（度，默认 30）
  4. 最小夹角（度，默认 0，用于筛斜向面带）
  5. 是否把参考方向当"轴"，正反两面都算（y/n，默认 n）

结果：命中面生成新 Mesh 对象（红色高亮并选中），命令行打印统计。

兼容性：IronPython 2.7 (Rhino 7) / Python 3 (Rhino 8)。
"""

import math
import Rhino
import Rhino.Geometry as rg
import System.Drawing


# ---------------------------------------------------------------------------
# 几何工具
# ---------------------------------------------------------------------------
def _face_normal(mesh, face_index):
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


def _angle_between(a, b):
    if a is None or b is None:
        return None
    # 真机修正（2026-11-22）：RhinoCommon 9 的 Vector3d 没有 DotProduct 静态方法，
    # 点积用运算符 * （底层 Multiply）。
    dot = a * b
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


def parse_direction(text, mesh):
    """把用户输入的字符串解析成单位 Vector3d；失败返回 None。"""
    if text is None:
        return None
    value = str(text).strip()
    if not value:
        return rg.Vector3d(0, 0, 1)

    presets = {
        "top": (0, 0, 1), u"上": (0, 0, 1), u"顶": (0, 0, 1),
        "bottom": (0, 0, -1), u"下": (0, 0, -1), u"底": (0, 0, -1),
        "left": (-1, 0, 0), u"左": (-1, 0, 0),
        "right": (1, 0, 0), u"右": (1, 0, 0),
        "front": (0, -1, 0), u"前": (0, -1, 0),
        "back": (0, 1, 0), u"后": (0, 1, 0),
    }
    low = value.lower()
    if low in presets:
        return rg.Vector3d(*presets[low])

    # face:N / 面:N / f:N
    if low.startswith("face:") or low.startswith(u"面:") or low.startswith("f:"):
        digits = value.split(":", 1)[1].strip()
        try:
            index = int(digits)
        except ValueError:
            return None
        if 0 <= index < mesh.Faces.Count:
            return _face_normal(mesh, index)
        return None

    # x,y,z 或 x y z
    for sep in (",", " ", "，"):
        if sep in value:
            parts = value.replace("，", ",").replace(" ", ",").split(",")
            break
    else:
        parts = [value]
    parts = [p for p in parts if p.strip()]
    if len(parts) != 3:
        return None
    try:
        vec = rg.Vector3d(float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError:
        return None
    if vec.Length < 1e-12:
        return None
    vec.Unitize()
    return vec


def _extract_faces(mesh, indices):
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


def _ask_string(prompt, default):
    rc, value = Rhino.Input.RhinoGet.GetString(prompt, True, default)
    if rc != Rhino.Commands.Result.Success:
        return None
    return value


def _ask_real(prompt, default):
    rc, value = Rhino.Input.RhinoGet.GetReal(prompt, True, default)
    if rc != Rhino.Commands.Result.Success:
        return None
    return value


# ---------------------------------------------------------------------------
# 命令主体
# ---------------------------------------------------------------------------
def RunCommand():
    # 1. 选网格
    getter = Rhino.Input.Custom.GetObject()
    getter.SetCommandPrompt(u"选择要筛选的网格 Mesh")
    getter.GeometryFilter = Rhino.DocObjects.ObjectType.Mesh
    getter.Get()
    if getter.CommandResult() != Rhino.Commands.Result.Success:
        return
    mesh = getter.Object(0).Geometry()
    if mesh is None or mesh.Faces.Count == 0:
        print(u"[NFF] 所选对象不是有效网格。")
        return

    # 2. 参考方向
    raw = _ask_string(
        u"参考方向 (top/bottom/left/right/front/back 或 x,y,z 或 face:N) [回车=+Z] ",
        "0,0,1")
    if raw is None:
        return
    direction = parse_direction(raw, mesh)
    if direction is None:
        print(u"[NFF] 方向解析失败，请用 0,0,1 这样的格式或 face:N。")
        return

    # 3. 角度阈值
    max_angle = _ask_real(u"最大夹角(度) [30] ", 30.0)
    if max_angle is None:
        return
    min_angle = _ask_real(u"最小夹角(度，0 表示从 0 开始) [0] ", 0.0)
    if min_angle is None:
        return
    max_angle = max(0.0, min(180.0, max_angle))
    min_angle = max(0.0, min(180.0, min_angle))
    if min_angle > max_angle:
        min_angle, max_angle = max_angle, min_angle

    # 4. 反向开关
    answer = _ask_string(u"是否把参考方向当轴，正反两面都算? (y/n) [n] ", "n")
    if answer is None:
        return
    opposite = str(answer).strip().lower() in ("y", "yes", u"是")

    # 5. 筛选
    kept = []
    removed = []
    angles = []
    for i in range(mesh.Faces.Count):
        n = _face_normal(mesh, i)
        theta = _angle_between(n, direction)
        if theta is None:
            angles.append(None)
            removed.append(i)
            continue
        angles.append(theta)
        hit = (min_angle <= theta <= max_angle)
        if opposite and (min_angle <= (180.0 - theta) <= max_angle):
            hit = True
        (kept if hit else removed).append(i)

    if not kept:
        print(u"[NFF] 没有面落在 %.1f°~%.1f° 区间内，未生成对象。" % (min_angle, max_angle))
        return

    # 6. 生成新网格并加入文档
    result_mesh = _extract_faces(mesh, kept)
    doc = Rhino.RhinoDoc.ActiveDoc
    new_id = doc.Objects.AddMesh(result_mesh)
    obj = doc.Objects.Find(new_id)
    if obj is not None:
        try:
            obj.Attributes.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
            obj.Attributes.ObjectColor = System.Drawing.Color.FromArgb(255, 70, 70)
            obj.CommitChanges()
        except Exception:
            pass
        try:
            doc.Objects.Select(new_id)
        except Exception:
            pass
    doc.Views.Redraw()

    print(u"[NFF] 总面数 %d | 命中 %d | 剔除 %d | 参考方向 (%.3f, %.3f, %.3f) "
          u"| 区间 %.1f°~%.1f° | 反向 %s"
          % (mesh.Faces.Count, len(kept), len(removed),
             direction.X, direction.Y, direction.Z,
             min_angle, max_angle, u"是" if opposite else u"否"))
    print(u"[NFF] 已生成 %d 个面的新网格对象（红色高亮）。" % len(kept))


RunCommand()
