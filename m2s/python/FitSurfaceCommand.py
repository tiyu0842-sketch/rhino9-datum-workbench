# -*- coding: utf-8 -*-
"""
FitSurfaceCommand.py —— Rhino 命令：把选中网格面拟合为平面，并报偏差

用法（Rhino 命令行）：
    _RunPythonScript  FitSurfaceCommand.py

流程：
  1. 选一个 Mesh 对象
  2. 输入要拟合的面索引（逗号分隔，如 0,1,2；留空=全部面）
  3. 取这些面的顶点 → Rhino 内核 FitPlaneToPoints 拟合 → 计算偏差
  4. 在文档里创建拟合出的平面曲面（透明棕，与 NFF 配色一致）
  5. 命令行打印 RMS / 最大偏差 / 命中率，并写文档字符串

依赖：surfacefit_core.py（纯 Python 兜底算法）在同目录。
真机验证 API（2026-11-25）：
  Plane.FitPlaneToPoints(IEnumerable<Point3d>, out Plane, out double)  ✅
  Mesh.ClosestPoint(point, out double)  签名见下方运行时探测，若不符改用备选
"""

import os
import sys
import math

import Rhino
import rhinoscriptsyntax as rs

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def collect_points(mesh, face_indices):
    """从网格的指定面收集去重顶点。"""
    seen, pts = set(), []
    for fi in face_indices:
        if fi < 0 or fi >= mesh.Faces.Count:
            continue
        face = mesh.Faces[fi]
        # 真机确认：MeshFace 不可 for 迭代，要用 .A/.B/.C/(.D)
        vis = [face.A, face.B, face.C]
        if not face.IsTriangle:
            vis.append(face.D)
        for vi in vis:
            if vi not in seen:
                seen.add(vi)
                pts.append(mesh.Vertices[vi])
    return pts


def fit_with_rhino(points):
    """用 Rhino 内核拟合平面，返回 (plane, fit_result)。

    真机实测（2026-11-25 Rhino 9）：
      Plane.FitPlaneToPoints(IEnumerable<Point3d>) → (PlaneFitResult, Plane)
    不是文档里写的 (bool, Plane, out double) 三元组——Python 绑定只有两个返回值。
    枚举 Success 表示拟合成功；拟合误差用 deviation() 自己算，不依赖 err 参数。
    """
    result, plane = Rhino.Geometry.Plane.FitPlaneToPoints(points)
    ok = (str(result).find("Success") >= 0) or (int(result) == 0)
    return (plane, result) if ok else (None, result)


def deviation(mesh, plane, points):
    """点到拟合平面的偏差统计。用 Plane.DistanceTo(point)（点到无限平面）。"""
    ds = [abs(plane.DistanceTo(p)) for p in points]
    if not ds:
        return None
    return {
        "mean": sum(ds) / len(ds),
        "rms": math.sqrt(sum(d * d for d in ds) / len(ds)),
        "max": max(ds),
        "within_0_5": sum(1 for d in ds if d <= 0.5) / len(ds),
        "n": len(ds),
    }


def parse_indices(text, count):
    text = (text or "").strip()
    if not text:
        return list(range(count))
    out, seen = [], set()
    for tok in text.replace(" ", "").split(","):
        try:
            i = int(tok)
            if 0 <= i < count and i not in seen:
                seen.add(i)
                out.append(i)
        except ValueError:
            pass
    return out


def get_doc():
    """取当前文档，兼容两种运行方式。

    - MCP `run_python`：注入全局 `__rhino_doc__`，优先用它（指向目标 slot 的文档）
    - 命令行 `_RunPythonScript`：没有这个变量，回退 `Rhino.RhinoDoc.ActiveDoc`
      （不用 `scriptcontext.doc`，Rhino 9 脚本上下文里它不稳定）。
      直接写 `doc = __rhino_doc__` 会在命令行下抛 NameError（用户真机已踩到）。
    """
    d = globals().get("__rhino_doc__")
    if d is not None:
        return d
    import Rhino
    return Rhino.RhinoDoc.ActiveDoc


def run_fit(doc, mesh, indices, name="FitPlane (m2s)"):
    """非交互执行体：拟合 → 偏差 → 建真实曲面 → 写文档字符串。

    与 main() 的交互取参解耦，便于真机自检直接调用（不需要人去点选对象）。
    返回 dict，供调用方断言/回看。
    """
    pts = collect_points(mesh, indices)
    plane, err = fit_with_rhino(pts)
    if plane is None or len(pts) < 3:
        print("拟合失败:", err)
        return {"ok": False, "reason": "fit_failed", "fit_result": str(err)}

    st = deviation(mesh, plane, pts)
    print("== 拟合结果 ==")
    print("  面数:", len(indices), " 顶点数:", len(pts))
    print("  原点:", plane.Origin)
    print("  法向:", plane.Normal)
    print("  RMS 偏差: %.4f mm" % st["rms"])
    print("  最大偏差: %.4f mm" % st["max"])
    print("  ≤0.5mm 占比: %.1f%%" % (st["within_0_5"] * 100))

    # 创建平面曲面（行业棕，与基准面插件一致）
    half = 0.0
    for p in pts:
        half = max(half, p.DistanceTo(plane.Origin))
    half = max(half, 1.0) * 1.05
    # 真机确认：PlaneSurface 构造是 (Plane, Interval, Interval)，不是 (Plane, [w,h])
    iv = Rhino.Geometry.Interval(-half, half)
    rect = Rhino.Geometry.PlaneSurface(plane, iv, iv)
    att = Rhino.DocObjects.ObjectAttributes()
    att.Name = name
    att.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
    import System.Drawing
    att.ObjectColor = System.Drawing.Color.FromArgb(176, 132, 70)
    idx = doc.Objects.AddSurface(rect, att)

    # 写文档字符串（随 .3dm 保存）
    # 真机确认：文档字符串是 Strings.SetString(section, key, value)，不是 SetValue
    doc.Strings.SetString("M2S", "LastFit",
                          "faces=%d rms=%.4f max=%.4f obj=%s" %
                          (len(indices), st["rms"], st["max"], idx))
    doc.Views.Redraw()
    print("已创建拟合平面对象 idx=%s" % idx)

    return {"ok": True, "fit_result": str(err), "plane": plane,
            "deviation": st, "object_id": idx,
            "points": len(pts), "faces": len(indices)}


def main():
    """交互入口：命令行 `_RunPythonScript FitSurfaceCommand.py` 后选网格、输面索引。"""
    doc = get_doc()

    # 1. 选网格
    go = Rhino.Input.Custom.GetObject()
    go.SetCommandPrompt("选择要拟合的网格 Mesh")
    go.GeometryFilter = Rhino.DocObjects.ObjectType.Mesh
    go.Get()
    if go.CommandResult() != Rhino.Commands.Result.Success:
        return
    obj = go.Object(0).Object()
    mesh = obj.Mesh()
    if mesh is None:
        print("不是有效 Mesh")
        return

    # 2. 面索引
    gs = Rhino.Input.Custom.GetString()
    gs.SetCommandPrompt("输入面索引（如 0,1,2；留空=全部）")
    gs.SetDefaultString("")
    gs.Get()
    indices = parse_indices(gs.StringResult(), mesh.Faces.Count)
    if not indices:
        print("没有有效面索引")
        return

    # 3. 交给非交互执行体
    run_fit(doc, mesh, indices)


if __name__ == "__main__":
    main()
