# -*- coding: utf-8 -*-
"""验证不依赖 OrientationIsReversed 的凹区内表面判据：
有效法向 n=NormalAt，面质心 proj=n·centroid；
若 proj 落在整体 bbox 8 角点沿 n 投影的极值处 => 外表面，否则 => 凹区内表面。
"""
import clr
import System
import Rhino.Geometry as G

TOL = 0.001
out = []


def V(p):
    return G.Vector3d(p.X, p.Y, p.Z)


def dot(a, b):
    return G.Vector3d.Multiply(a, b)


def corners(bb):
    return [G.Point3d(x, y, z)
            for x in (bb.Min.X, bb.Max.X)
            for y in (bb.Min.Y, bb.Max.Y)
            for z in (bb.Min.Z, bb.Max.Z)]


def flags(brep):
    bb = brep.GetBoundingBox(True)
    cs = corners(bb)
    res = []
    for f in brep.Faces:
        u, v = f.Domain(0).Mid, f.Domain(1).Mid
        n = f.NormalAt(u, v)
        n.Unitize()
        ctr = G.AreaMassProperties.Compute(f.DuplicateFace(False)).Centroid
        proj = dot(V(ctr), n)
        ps = [dot(V(c), n) for c in cs]
        gmin, gmax = min(ps), max(ps)
        inner = abs(proj - gmin) > 0.01 and abs(proj - gmax) > 0.01
        res.append((f.OrientationIsReversed, inner, proj, gmin, gmax, n))
    return res


def describe(brep, tag):
    out.append("---- %s faces=%d ----" % (tag, brep.Faces.Count))
    r = flags(brep)
    for i, (rev, inner, proj, gmin, gmax, n) in enumerate(r):
        out.append("  F%-2d rev=%-5s NEW_inner=%-5s proj=%8.3f range=%8.3f..%8.3f n=(%.1f,%.1f,%.1f)" % (
            i, rev, inner, proj, gmin, gmax, n.X, n.Y, n.Z))
    out.append("  new inner set = %s" % [i for i, x in enumerate(r) if x[1]])


box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
hole = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
s1 = G.Brep.CreateBooleanDifference(box, hole, TOL)[0]
describe(s1, "box + R6 through hole")

pk = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(20, 31)).ToBrep()
orig = G.Brep.CreateBooleanDifference(s1, pk, TOL)[0]
describe(orig, "box + hole + pocket (ORIGINAL)")

# rebuilt pocket with extrusion tool (bottom rev=False)
sup = G.Brep.CreateBooleanDifference(box, hole, TOL)[0]  # rough stand-in: no pocket
# reconstruct properly: suppress = remove pocket faces from orig by boolean union trick is complex;
# instead directly build the same geometry with the extrusion tool on a clean plate
clean_plate = G.Brep.CreateBooleanDifference(box, hole, TOL)[0]
c = G.Polyline([G.Point3d(50, 20, 30), G.Point3d(90, 20, 30),
                G.Point3d(90, 60, 30), G.Point3d(50, 60, 30), G.Point3d(50, 20, 30)]).ToPolylineCurve()
ext = G.Extrusion.Create(c, 18.04, True)
tool = ext.ToBrep()
tb = tool.GetBoundingBox(True)
# align tool so it spans z 11.98 .. 30.02
tool.Translate(G.Vector3d(0, 0, 11.98 - tb.Min.Z))
d = G.Brep.CreateBooleanDifference(clean_plate, tool, TOL)[0]
describe(d, "plate + extrusion-tool pocket (bottom rev expected False)")

# depth by edge-vertex projection for the rebuilt pocket
comp = [i for i, x in enumerate(flags(d)) if x[1]]
out.append("  edge-vertex proj span of inner set = %.4f" % (
    (lambda ps: max(ps) - min(ps))(
        [dot(V(e.PointAtStart), G.Vector3d(0, 0, 1)) for e in d.Edges
         if any(int(a) in comp for a in (e.AdjacentFaces() or []))] +
        [dot(V(e.PointAtEnd), G.Vector3d(0, 0, 1)) for e in d.Edges
         if any(int(a) in comp for a in (e.AdjacentFaces() or []))])))

print("\n".join(out))
