# -*- coding: utf-8 -*-
"""Print per-edge dihedral intermediates for a pocketed solid.

Compares two normal-source strategies and two sign conventions, to find why
plane-plane pocket edges are all classified Convex while the hole circle is Concave.
"""
import clr
import System
import Rhino.Geometry as G

TOL = 0.001
box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
pk = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(20, 31)).ToBrep()
solid = G.Brep.CreateBooleanDifference(box, pk, TOL)[0]
solid.MergeCoplanarFaces(TOL)
solid.Compact()

out = ["faces=%d edges=%d" % (solid.Faces.Count, solid.Edges.Count)]


def normals_at_closest(fa, fb, pt):
    okA, ua, va = fa.ClosestPoint(pt)
    okB, ub, vb = fb.ClosestPoint(pt)
    if not (okA and okB):
        return None
    return fa.NormalAt(ua, va), fb.NormalAt(ub, vb)


def dir_in_a(brep, edge, faceAIdx, tangent):
    d = G.Vector3d(tangent)
    for ti in edge.TrimIndices():
        tr = brep.Trims[ti]
        if tr.Face is not None and tr.Face.FaceIndex == faceAIdx:
            if tr.IsReversed():
                d = -tangent
            break
    return d


for e in solid.Edges:
    adj = e.AdjacentFaces()
    if len(adj) != 2 or adj[0] == adj[1]:
        continue
    f1, f2 = adj[0], adj[1]
    fa, fb = solid.Faces[f1], solid.Faces[f2]
    midT = e.Domain.Mid
    pt = e.PointAt(midT)
    tan = e.TangentAt(midT)
    if not tan.Unitize():
        continue
    ns = normals_at_closest(fa, fb, pt)
    if ns is None:
        continue
    nA, nB = ns
    ang = G.Vector3d.VectorAngle(nA, nB)
    if ang < 0.02:
        conv = "Tangent"
        det = 0.0
    else:
        d = dir_in_a(solid, e, f1, tan)
        cross = G.Vector3d.CrossProduct(nA, nB)
        det = G.Vector3d.Multiply(cross, d)
        conv = "Convex" if det > 0 else "Concave"
    # face orientation + plane normals for context
    def nrm(f):
        return f.NormalAt(f.Domain(0).Mid, f.Domain(1).Mid)
    out.append("E%-2d F%-2d/F%-2d revA=%-5s revB=%-5s nA=(%5.2f,%5.2f,%5.2f) nB=(%5.2f,%5.2f,%5.2f) tan=(%5.2f,%5.2f,%5.2f) ang=%5.2f det=%8.3f -> %s" % (
        e.EdgeIndex, f1, f2,
        str(fa.OrientationIsReversed), str(fb.OrientationIsReversed),
        nA.X, nA.Y, nA.Z, nB.X, nB.Y, nB.Z,
        tan.X, tan.Y, tan.Z, ang, det, conv))

print("\n".join(out))
