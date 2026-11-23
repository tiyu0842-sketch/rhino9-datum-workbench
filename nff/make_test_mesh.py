# -*- coding: utf-8 -*-
"""
make_test_mesh.py — 在真实 Rhino 中一键生成 NFF 验证用测试网格。

运行方式：
  在 Rhino 命令行输入 _RunPythonScript，选中本文件即可。
  （也可作为 Rhino 8 的 Python 脚本直接运行）

生成内容：
  一个包含 7 个面的 Mesh：
    面 0~5：一个 10x8x6 的长方体，法线分别覆盖 +Z / -Z / +X / -X / +Y / -Y
    面 6   ：一个 45° 斜面，法线约 (0, 0.707, 0.707)
  同时打印每个面的序号、法线与「与 +Z 的夹角」，供验证筛选结果时对照。

预期参考值（Direction = 0,0,1, Angle = 30）：
  命中面 = 顶面（+Z），其余剔除。
  把 Angle 调到 60 时，45° 斜面也会命中。
  开 IncludeOpposite 后，底面（-Z）也会命中。

脚本会在同目录保存 NFF_TestMesh.3dm，并把它加入当前文档。
"""

import math
import os
import Rhino
import Rhino.Geometry as rg


def build_test_mesh():
    mesh = rg.Mesh()

    # 长方体：覆盖 ±X ±Y ±Z 六个朝向
    # 真机修正（2026-11-22）：RhinoCommon 9 没有 Mesh.CreateBox，
    # 正确入口是 Mesh.CreateFromBox(BoundingBox, xCount, yCount, zCount)。
    # 三轴各 1 段 → 恰好 6 个四边形面，与模拟层的预期一致。
    box = rg.Mesh.CreateFromBox(
        rg.BoundingBox(rg.Point3d(0, 0, 0), rg.Point3d(10, 8, 6)), 1, 1, 1)
    mesh.Append(box)

    # 45° 斜面：从 y=8 升起的斜坡
    slope = [(0, 8, 6), (10, 8, 6), (10, 12, 2), (0, 12, 2)]
    base = mesh.Vertices.Count
    for point in slope:
        mesh.Vertices.Add(rg.Point3d(point[0], point[1], point[2]))
    mesh.Faces.AddFace(base, base + 1, base + 2, base + 3)

    try:
        mesh.Normals.ComputeNormals()
    except Exception:
        pass
    return mesh


def face_normal(mesh, index):
    face = mesh.Faces[index]
    a = mesh.Vertices[face.A]
    b = mesh.Vertices[face.B]
    c = mesh.Vertices[face.C]
    n = rg.Vector3d.CrossProduct(b - a, c - a)
    if face.IsQuad:
        d = mesh.Vertices[face.D]
        n = n + rg.Vector3d.CrossProduct(c - a, d - a)
    if n.Length > 1e-12:
        n.Unitize()
    return n


def report(mesh):
    print("[NFF-TEST] 面数 = %d" % mesh.Faces.Count)
    print("[NFF-TEST] 序号 | 法线 (x,y,z) | 与 +Z 夹角")
    for i in range(mesh.Faces.Count):
        n = face_normal(mesh, i)
        dot = max(-1.0, min(1.0, n.Z))
        theta = math.degrees(math.acos(dot))
        print("[NFF-TEST] %2d   | (%.3f, %.3f, %.3f) | %.1f deg"
              % (i, n.X, n.Y, n.Z, theta))
    print("[NFF-TEST] 验证参考: Angle=30 命中 +Z 面; "
          "Angle=60 额外命中 45deg 面; IncludeOpposite 会额外命中 -Z 面。")


def main():
    mesh = build_test_mesh()
    doc = Rhino.RhinoDoc.ActiveDoc
    object_id = doc.Objects.AddMesh(mesh)
    doc.Objects.Select(object_id)
    doc.Views.Redraw()

    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        here = os.path.expanduser("~")
    output = os.path.join(here, "NFF_TestMesh.3dm")
    try:
        doc.SaveAs(output)
        print("[NFF-TEST] 已保存测试模型: " + output)
    except Exception as exc:
        print("[NFF-TEST] 保存失败（不影响使用）: " + str(exc))

    report(mesh)


main()
