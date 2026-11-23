# -*- coding: utf-8 -*-
"""验证整体修复链路：删特征面 -> untrim 相邻面恢复原生曲面 -> CreateSolid 重新缝合。
三个场景：盲槽、通孔、倒角。逐条打印面数/实体性/包围盒，确认能回到毛坯。"""
import clr
import System
import Rhino.Geometry as G

TOL = 0.001
out = []

# ShrinkDisableSide lives in Rhino.Geometry namespace but may not be bound in Python;
# not required for this chain (we use UnderlyingSurface + CreateSolid).
try:
    out.append("ShrinkDisableSide values = " + str(
        [x for x in dir(G.ShrinkDisableSide) if not x.startswith('_')]))
except Exception as ex:
    out.append("ShrinkDisableSide not bound in Python (" + str(ex) + ") - skipped")


def bbox(b):
    bb = b.GetBoundingBox(True)
    return "(%.0f,%.0f,%.0f)-(%.0f,%.0f,%.0f)" % (
        bb.Min.X, bb.Min.Y, bb.Min.Z, bb.Max.X, bb.Max.Y, bb.Max.Z)


def build_pocket():
    box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
    pk = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(20, 31)).ToBrep()
    return G.Brep.CreateBooleanDifference(box, pk, TOL)[0]


def build_hole():
    box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
    cyl = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
    return G.Brep.CreateBooleanDifference(box, cyl, TOL)[0]


def build_fillet():
    b = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
    top = [e.EdgeIndex for e in b.Edges
           if abs(e.PointAtStart.Z - 30) < 0.01 and abs(e.PointAtEnd.Z - 30) < 0.01]
    f = G.Brep.CreateFilletEdges(b, top, [3.0] * len(top), [3.0] * len(top),
                                 G.BlendType.Fillet, G.RailType.RollingBall, TOL)
    return f[0]


def faces_with_bbox_overhang(brep):
    """找出底层曲面 domain 相对 trim 边端点有超出的面（布尔余量信号）。"""
    res = []
    for i in range(brep.Faces.Count):
        f = brep.Faces[i]
        try:
            us = f.UnderlyingSurface()
            du, dv = us.Domain(0), us.Domain(1)
            cs = [us.PointAt(u, v) for u in (du.Min, du.Max) for v in (dv.Min, dv.Max)]
            ez = [e.PointAtStart.Z for e in brep.Edges
                  if e.AdjacentFaces() is not None and i in [int(a) for a in e.AdjacentFaces()]]
            ez += [e.PointAtEnd.Z for e in brep.Edges
                   if e.AdjacentFaces() is not None and i in [int(a) for a in e.AdjacentFaces()]]
            if not ez:
                continue
            surf_span = max(c.Z for c in cs) - min(c.Z for c in cs)
            trim_span = max(ez) - min(ez)
            if surf_span - trim_span > 0.5:
                res.append((i, surf_span, trim_span))
        except Exception:
            pass
    return res


def try_repair(brep, tag, feature_kind):
    out.append("\n---- %s ----" % tag)
    out.append("original: faces=%d solid=%s bbox=%s" % (brep.Faces.Count, brep.IsSolid, bbox(brep)))
    over = faces_with_bbox_overhang(brep)
    out.append("faces with untrim overhang (>=0.5): %s" % over)

    # 用底层曲面重建每个面（原生曲面），再 CreateSolid 缝合
    # 这对平面/解析面成立；自由曲面用 DuplicateFace 回退。
    pieces = []
    for i in range(brep.Faces.Count):
        f = brep.Faces[i]
        us = None
        try:
            us = f.UnderlyingSurface()
        except Exception:
            pass
        if us is not None:
            try:
                b = us.ToBrep()
                if b is not None and b.Faces.Count > 0:
                    pieces.append((i, b, "underlying"))
                    continue
            except Exception:
                pass
        try:
            b = f.DuplicateFace(False)
            if b is not None:
                pieces.append((i, b, "duplicate"))
        except Exception:
            pass
    out.append("pieces: %d (underlying=%d duplicate=%d)" % (
        len(pieces), sum(1 for p in pieces if p[2] == 'underlying'),
        sum(1 for p in pieces if p[2] == 'duplicate')))

    try:
        solids = G.Brep.CreateSolid([p[1] for p in pieces], TOL)
        out.append("CreateSolid -> %d result(s)" % (0 if solids is None else len(solids)))
        if solids:
            for k, s in enumerate(solids[:3]):
                out.append("   [%d] faces=%d solid=%s bbox=%s" % (k, s.Faces.Count, s.IsSolid, bbox(s)))
    except Exception as ex:
        out.append("CreateSolid FAILED: %s" % ex)

    # 单独试 UntrimFace：打印调用是否成功、面数变化
    cp = brep.DuplicateBrep()
    test_idx = over[0][0] if over else 0
    try:
        r = cp.UntrimFace(test_idx, TOL)
        out.append("UntrimFace(%d) -> %s ; faces %d->%d solid=%s bbox=%s" % (
            test_idx, "null" if r is None else "Brep", cp.Faces.Count,
            (r.Faces.Count if r is not None else -1), cp.IsSolid, bbox(cp)))
    except Exception as ex:
        out.append("UntrimFace(%d) FAILED: %s" % (test_idx, ex))
    try:
        r = cp.UntrimOuterLoop(test_idx)
        out.append("UntrimOuterLoop(%d) -> %s" % (test_idx, "null" if r is None else "Brep"))
    except Exception as ex:
        out.append("UntrimOuterLoop(%d) FAILED: %s" % (test_idx, ex))


try_repair(build_pocket(), "BLIND POCKET", "pocket")
try_repair(build_hole(), "THROUGH HOLE", "hole")
try_repair(build_fillet(), "FILLET BOX", "fillet")

print("\n".join(out))
