# -*- coding: utf-8 -*-
"""Rhino 9: 底层曲面 / 修剪 / 缩回 API 反射 + 语义实验。
验证思路：面 = 完整 underlying surface + trim loops；布尔减/倒角只改 trim。
"""
import clr
import System
from System.Reflection import BindingFlags
import Rhino.Geometry as G

BF = BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static
out = []


def dump(t, keys, label):
    T = clr.GetClrType(t)
    out.append("==== %s : members matching %s ====" % (label, keys))
    for m in T.GetMethods(BF):
        if any(k.lower() in m.Name.lower() for k in keys):
            out.append("  M  " + m.ToString())
    for p in T.GetProperties(BF):
        if any(k.lower() in p.Name.lower() for k in keys):
            out.append("  P  " + p.ToString())


dump(G.BrepFace, ["underlying", "untrim", "shrink", "trim", "domain", "planar", "loop", "surface"], "BrepFace")
dump(G.Brep, ["untrim", "shrink", "cap", "repair", "trim", "create"], "Brep")
dump(G.Surface, ["domain", "planar", "nurbs", "tobrep", "extend", "pointat"], "Surface")
dump(G.BrepTrim, ["reversed", "curve", "edge", "loop", "iso"], "BrepTrim")
dump(G.BrepLoop, ["trim", "type", "face", "outer"], "BrepLoop")

TOL = 0.001
out.append("")
out.append("################ SEMANTIC EXPERIMENT ################")

box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
hole = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
holed = G.Brep.CreateBooleanDifference(box, hole, TOL)[0]
pk = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(20, 31)).ToBrep()
pocket = G.Brep.CreateBooleanDifference(holed, pk, TOL)[0]

b2 = G.Box(G.Plane.WorldXY, G.Interval(120, 170), G.Interval(0, 50), G.Interval(0, 30)).ToBrep()
top = [e.EdgeIndex for e in b2.Edges
       if abs(e.PointAtStart.Z - 30) < 0.01 and abs(e.PointAtEnd.Z - 30) < 0.01]
fil = G.Brep.CreateFilletEdges(b2, top, [3.0] * len(top), [3.0] * len(top),
                               G.BlendType.Fillet, G.RailType.RollingBall, TOL)


def inspect(brep, tag):
    if brep is None:
        return
    out.append("---- %s : %d faces ----" % (tag, brep.Faces.Count))
    for i in range(brep.Faces.Count):
        f = brep.Faces[i]
        try:
            us = f.UnderlyingSurface()
        except Exception as ex:
            out.append("  F%d UnderlyingSurface() FAILED: %s" % (i, ex))
            continue
        try:
            du, dv = us.Domain(0), us.Domain(1)
            cs = [us.PointAt(u, v) for u in (du.Min, du.Max) for v in (dv.Min, dv.Max)]
            sz = [c.Z for c in cs]
            dom = "U[%.2f,%.2f] V[%.2f,%.2f]" % (du.Min, du.Max, dv.Min, dv.Max)
        except Exception as ex:
            sz = []
            dom = "domain failed %s" % ex
        ez = []
        for e in brep.Edges:
            adj = e.AdjacentFaces()
            if adj is not None and i in [int(a) for a in adj]:
                ez.extend([e.PointAtStart.Z, e.PointAtEnd.Z])
        try:
            nloops = f.Loops.Count
            ntrims = sum(l.Trims.Count for l in f.Loops)
        except Exception:
            nloops = ntrims = -1
        extra = ""
        if hasattr(us, "Points"):
            try:
                extra = " NURBS CV=%dx%d deg=%d/%d" % (
                    us.Points.CountU, us.Points.CountV, us.DegreeU, us.DegreeV)
            except Exception:
                pass
        out.append("  F%-2d %-16s rev=%-5s loops=%d trims=%-2d %-30s surfZ=%s trimEdgeZ=%s%s" % (
            i, us.GetType().Name, f.OrientationIsReversed, nloops, ntrims, dom,
            ("%.2f..%.2f" % (min(sz), max(sz))) if sz else "-",
            ("%.2f..%.2f" % (min(ez), max(ez))) if ez else "-", extra))


inspect(box, "PLAIN BOX (untouched)")
inspect(holed, "BOX + R6 HOLE")
inspect(pocket, "BOX + HOLE + POCKET")
inspect(fil[0] if fil else None, "FILLET BOX")

# ---- ShrinkFace / Untrim feasibility on a copy ----
out.append("")
cp = pocket.DuplicateBrep()
f7 = cp.Faces[7]
try:
    du0, dv0 = f7.UnderlyingSurface().Domain(0), f7.UnderlyingSurface().Domain(1)
    out.append("before shrink F7 domain U[%.3f,%.3f] V[%.3f,%.3f]" % (du0.Min, du0.Max, dv0.Min, dv0.Max))
except Exception as ex:
    out.append("domain read failed %s" % ex)

for name in ("ShrinkFace", "Untrim"):
    try:
        fn = getattr(f7, name)
    except Exception:
        out.append("%s : NOT PRESENT" % name)
        continue
    try:
        import inspect as _ins
        nargs = len(_ins.getfullargspec(fn).args) if hasattr(_ins, "getfullargspec") else -1
    except Exception:
        nargs = -1
    try:
        res = fn()
        out.append("%s() -> %s (nargs=%s)" % (name, res, nargs))
        du1, dv1 = f7.UnderlyingSurface().Domain(0), f7.UnderlyingSurface().Domain(1)
        out.append("   after domain U[%.3f,%.3f] V[%.3f,%.3f]" % (du1.Min, du1.Max, dv1.Min, dv1.Max))
    except Exception as ex:
        out.append("%s() call failed: %s (nargs=%s)" % (name, ex, nargs))

print("\n".join(out))
