# -*- coding: utf-8 -*-
r"""rhino_growth_view.py —— 把面级连通生长结果回写 Rhino 视口（真机目视验证）

在 MCP run_python 里用 wrapper 执行（exec 环境没有 __file__，必须注入）：

    P = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\github-release\m2s\python\rhino_growth_view.py"
    globals()["__file__"] = P
    exec(compile(open(P, encoding="utf-8").read(), P, "exec"), globals())

为什么自己解析 STL：Rhino 9 的 STL 导入器会**重排面顺序**，
JSON 里的 face_indices 是 Python 解析器的顺序，直接拿来索引 Rhino Mesh 会错位
（实测质心差 0.26）。所以按坐标重建，不复用 Rhino 的 Mesh 对象。

配色约定：
  - 可靠球面块 = 冷色系（青 / 蓝 / 紫 / 橙 / 绿）
  - 不可靠（生长过冲）= 灰
  - 种子病态（跳过生长）= 暗红
  - 筒口环平面 = 棕
  - 球心点：可靠=红，不可靠=黄
"""
import os
import sys
import json
import traceback

import Rhino
import Rhino.Geometry as G
import System.Drawing as SD

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\github-release\m2s\python"
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import stl_chain

SRC = os.path.join(_HERE, "connected_growth_result.json")
STL = stl_chain.STL
PREFIX = "M2S_Grow_"
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s)


COLORS = {
    0: (176, 132, 70),
    1: (80, 200, 220),
    2: (90, 140, 235),
    3: (220, 90, 90),
    4: (240, 170, 70),
    5: (150, 110, 210),
}
OLD_PREFIXES = ("M2S_Pad", "M2S_Seg", "M2S_Centre", "M2S_SelfTest_")


def all_objects(doc):
    st = Rhino.DocObjects.ObjectEnumeratorSettings()
    st.HiddenObjects = True
    st.NormalObjects = True
    st.LockedObjects = True
    return list(doc.Objects.GetObjectList(st))


def clean_old(doc):
    """只删本脚本自己上次留下的 M2S_Grow_ 对象，不碰用户的其他对象。"""
    ids = [o.Id for o in all_objects(doc)
           if o.Name and o.Name.startswith(PREFIX)]
    for i in ids:
        doc.Objects.Delete(i, True)
    return len(ids)


def make_mesh(verts, faces, fi_list):
    loc, vlist, lfaces = {}, [], []
    for fi in fi_list:
        lf = []
        for vi in faces[fi]:
            if vi not in loc:
                loc[vi] = len(vlist)
                vlist.append(verts[vi])
            lf.append(loc[vi])
        lfaces.append(lf)
    m = G.Mesh()
    for v in vlist:
        m.Vertices.Add(float(v[0]), float(v[1]), float(v[2]))
    for lf in lfaces:
        if len(lf) == 3:
            m.Faces.AddFace(lf[0], lf[1], lf[2])
        elif len(lf) >= 4:
            m.Faces.AddFace(lf[0], lf[1], lf[2], lf[3])
    try:
        m.Normals.ComputeNormals()
    except Exception:
        pass
    return m, len(vlist)


def color_for(seg):
    if seg["type"] == "PLANE":
        return COLORS[0]
    if seg.get("seed_degenerate"):
        return (140, 60, 60)
    if not seg.get("radius_reliable"):
        return (150, 150, 150)
    return COLORS.get(seg["id"], (180, 180, 180))


def status_for(seg):
    if seg["type"] == "PLANE":
        return "PLANE"
    if seg.get("seed_degenerate"):
        return "DEGENERATE"
    return "RELIABLE" if seg.get("radius_reliable") else "UNRELIABLE"


def main():
    doc = Rhino.RhinoDoc.ActiveDoc
    say("Rhino", Rhino.RhinoApp.Version, "doc objects =", doc.Objects.Count)
    say("清理旧", PREFIX, "对象:", clean_old(doc))

    R = json.load(open(SRC, encoding="utf-8"))
    say("解析 STL ...")
    verts, faces, _ = stl_chain.load_stl(STL)
    say("  faces", len(faces), "verts", len(verts))
    say("  汇总:", R["summary"])

    doc.Objects.UnselectAll()
    for seg in R["segments"]:
        fis = seg.get("face_indices", [])
        if not fis:
            continue
        m, nv = make_mesh(verts, faces, fis)
        col = color_for(seg)
        attr = Rhino.DocObjects.ObjectAttributes()
        attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
        attr.ObjectColor = SD.Color.FromArgb(col[0], col[1], col[2])
        attr.Name = "%sSeg%02d_%s_%s" % (
            PREFIX, seg["id"], seg["type"], status_for(seg))
        doc.Objects.AddMesh(m, attr)
        say("  #%d %-6s %-10s faces=%-6d verts=%-6d color=%s R=%s span=%s" % (
            seg["id"], seg["type"], status_for(seg), len(fis), nv, col,
            seg.get("radius"), seg.get("span_deg")))

        c = seg.get("center")
        if c and seg["type"] == "SPHERE":
            pc = (SD.Color.FromArgb(255, 40, 40) if seg.get("radius_reliable")
                  else SD.Color.FromArgb(220, 220, 40))
            pa = Rhino.DocObjects.ObjectAttributes()
            pa.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
            pa.ObjectColor = pc
            pa.Name = PREFIX + "Centre%02d" % seg["id"]
            doc.Objects.AddPoint(G.Point3d(c[0], c[1], c[2]), pa)

    # 视口清干净：隐藏上一轮 catpaw 回写对象 + 原始 150 万面大 STL（避免 z-fighting）
    # 只隐藏、不删除；用户随时可以用 _Show / 对象管理器恢复。
    hidden_old = hidden_big = 0
    for o in all_objects(doc):
        if o.Name and o.Name.startswith(PREFIX):
            continue
        try:
            if o.Name and o.Name.startswith(OLD_PREFIXES):
                doc.Objects.Hide(o.Id, True)
                hidden_old += 1
            elif isinstance(o.Geometry, G.Mesh) and o.Geometry.Faces.Count > 100000:
                doc.Objects.Hide(o.Id, True)
                hidden_big += 1
        except Exception:
            pass
    say("隐藏旧 catpaw 对象", hidden_old, "/ 原始大网格", hidden_big,
        "（仅隐藏，未删除）")

    doc.Views.Redraw()
    try:
        doc.Views.ActiveView.ActiveViewport.ZoomExtents()
        doc.Views.Redraw()
    except Exception as e:
        say("ZoomExtents 失败:", repr(e))
    say("DONE doc objects =", doc.Objects.Count)


try:
    main()
except Exception:
    LOG.append(traceback.format_exc())
    traceback.print_exc()
finally:
    try:
        with open(os.path.join(_HERE, "rhino_growth_view_report.txt"),
                  "w", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
    except Exception:
        pass
