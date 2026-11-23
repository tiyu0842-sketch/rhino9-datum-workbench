# -*- coding: utf-8 -*-
"""Probe Rhino 9 semantics that the V2.0 FeatureWorks source assumes.

Run inside Rhino 9 Python 3:
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"))

Checks:
  A) ArchivableDictionary round-trip (int[], GeometryBase/Curve, nested, Plane, Vector3d)
  B) Brep.UserDictionary survives AddBrep / Replace in the real document
  C) Dihedral convexity sign convention from the handbook (det>0 => Convex)
  D) Inner-cylinder (hole wall) sign convention
  E) RemoveAt + Compact + Repair + CapPlanarHoles actually re-closes a solid
"""
import clr
import System
from System import Guid
import Rhino
import Rhino.Geometry as G
from Rhino.Collections import ArchivableDictionary

TOL = 0.001
doc = __rhino_doc__
out = []


def sec(s):
    out.append("\n=== " + s + " ===")


def try_cyl(f):
    """Robustly call BrepFace.TryGetCylinder across IronPython out-param quirks."""
    try:
        r = f.TryGetCylinder(TOL)
        if isinstance(r, tuple) and len(r) > 1:
            return r[1] if r[0] else None
        return r
    except Exception:
        try:
            ref = clr.Reference[G.Cylinder]()
            ok = f.TryGetCylinder(ref, TOL)
            return ref.Value if ok else None
        except Exception:
            try:
                r2 = f.TryGetCylinder()
                return r2[1] if isinstance(r2, tuple) and len(r2) > 1 and r2[0] else None
            except Exception:
                return None


# ---------------------------------------------------------------- A
sec("A) ArchivableDictionary round-trip (Rhino 9 real overloads)")
d = ArchivableDictionary()


def tryset(label, key, val):
    try:
        ok = d.Set(key, val)
        out.append("  Set %-18s -> %s" % (label, ok))
    except Exception as e:
        out.append("  Set %-18s -> ERR %s" % (label, e))


tryset("Guid", "Id", Guid.NewGuid())
tryset("int", "Type", 3)
tryset("string", "Name", "Hole_1")
tryset("bool", "Supp", False)
tryset("double", "Radius", 6.0)
tryset("Plane", "RefPlane", G.Plane.WorldXY)
tryset("Vector3d", "ExtrudeDir", G.Vector3d.ZAxis)
tryset("int[]", "FaceIndices", System.Array[int]([1, 2, 3, 5]))
tryset("str-joined", "FaceIndicesStr", "1,2,3,5")
tryset("GeometryBase", "ProfileCurve", G.LineCurve(G.Point3d(0, 0, 0), G.Point3d(10, 0, 0)))
inner = ArchivableDictionary()
inner.Set("Radius", 6.0)
inner.Set("Depth", 10.0)
tryset("nested dict", "Parameters", inner)

out.append("  keys = " + str(sorted([str(k) for k in d.Keys])))
try:
    out.append("  scalar reads: Type=%s Bool=%s Radius=%s Plane=%s Vec=%s nested=%s" % (
        d.GetInteger("Type"), d.GetBool("Supp"), d.GetDouble("Radius"),
        d.GetPlane("RefPlane").Origin, d.GetVector3d("ExtrudeDir"),
        d.GetDictionary("Parameters").GetDouble("Radius")))
except Exception as e:
    out.append("  scalar reads ERR " + str(e))
for fn in ("GetIntArray", "GetGeometry"):
    out.append("  has %-12s = %s   (handbook assumes these)" % (fn, hasattr(d, fn)))

for key in ("FaceIndices", "FaceIndicesStr", "ProfileCurve"):
    try:
        r = d.TryGetValue(key)
        val = r[1] if isinstance(r, tuple) and len(r) > 1 else r
        out.append("  TryGetValue(%-15s) -> ok=%s type=%s val=%s" % (
            key, (r[0] if isinstance(r, tuple) else r), type(val).__name__, str(val)[:70]))
    except Exception as e:
        out.append("  TryGetValue(%-15s) ERR %s" % (key, e))
    try:
        ref = clr.Reference[System.Object]()
        ok = d.TryGetValue(key, ref)
        out.append("  TryGetValue(%-15s,ref) -> ok=%s type=%s" % (key, ok, type(ref.Value).__name__))
    except Exception as e:
        out.append("  TryGetValue(%-15s,ref) ERR %s" % (key, e))
try:
    out.append("  indexer FaceIndices -> " + str(type(d["FaceIndices"]).__name__) + " " + str(d["FaceIndices"])[:70])
except Exception as e:
    out.append("  indexer ERR " + str(e))

# ---------------------------------------------------------------- B
sec("B) Brep.UserDictionary persistence through the document")
b = G.Box(G.Plane.WorldXY, G.Interval(0, 10), G.Interval(0, 10), G.Interval(0, 10)).ToBrep()
b.UserDictionary.Set("FeatureTree", d)
gid = doc.Objects.AddBrep(b)
o = doc.Objects.FindId(gid)
has = o.Geometry.UserDictionary.ContainsKey("FeatureTree") if o else False
rad = None
if has:
    rad = o.Geometry.UserDictionary.GetDictionary("FeatureTree").GetDictionary("Parameters").GetDouble("Radius")
out.append("  AddBrep -> guid=%s hasTree=%s radius=%s" % (gid, has, rad))
b2 = o.Geometry.DuplicateBrep()
ok_rep = doc.Objects.Replace(gid, b2)
o2 = doc.Objects.FindId(gid)
has2 = o2.Geometry.UserDictionary.ContainsKey("FeatureTree") if o2 else False
out.append("  Replace -> ok=%s hasTree=%s" % (ok_rep, has2))

# ---------------------------------------------------------------- C
sec("C) Dihedral convexity sign (handbook: det>0 => Convex)")


def convexity(brep, edge):
    adj = edge.AdjacentFaces()
    if len(adj) != 2:
        return "Naked"
    f1, f2 = adj[0], adj[1]
    midT = edge.Domain.Mid
    tan = edge.TangentAt(midT)
    if not tan.Unitize():
        return "Unknown"
    fa, fb = brep.Faces[f1], brep.Faces[f2]
    nA = fa.NormalAt(fa.Domain(0).Mid, fa.Domain(1).Mid)
    nB = fb.NormalAt(fb.Domain(0).Mid, fb.Domain(1).Mid)
    ang = G.Vector3d.VectorAngle(nA, nB)
    if ang < 0.02:
        return "Tangent"
    dirInA = G.Vector3d(tan)
    for ti in edge.TrimIndices():
        tr = brep.Trims[ti]
        if tr.Face.FaceIndex == f1:
            if tr.IsReversed():
                dirInA = -tan
            break
    cross = G.Vector3d.CrossProduct(nA, nB)
    det = G.Vector3d.Multiply(cross, dirInA)
    return "Convex" if det > 0 else "Concave"


def stats(brep, label):
    c = {}
    for e in brep.Edges:
        k = convexity(brep, e)
        c[k] = c.get(k, 0) + 1
    out.append("  %-24s edges=%2d  %s" % (label, brep.Edges.Count, c))
    return c


box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
stats(box, "plain box (expect Convex)")
hole_tool = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
holed = G.Brep.CreateBooleanDifference(box, hole_tool, TOL)[0]
stats(holed, "box + R6 through hole")

# ---------------------------------------------------------------- D
sec("D) Inner-cylinder (hole wall) sign")
for f in holed.Faces:
    cyl = try_cyl(f)
    if cyl is None:
        continue
    uM, vM = f.Domain(0).Mid, f.Domain(1).Mid
    pt = f.PointAt(uM, vM)
    normal = f.NormalAt(uM, vM)
    axisLine = G.Line(cyl.Center, cyl.Center + cyl.Axis)
    ptOnAxis = axisLine.ClosestPoint(pt, False)
    toAxis = ptOnAxis - pt
    dot = G.Vector3d.Multiply(normal, toAxis)
    out.append("  cyl face#%d radius=%.3f dot(normal,toAxis)=%.4f -> inner=%s" % (
        f.FaceIndex, cyl.Radius, dot, dot > 0))
    break

# ---------------------------------------------------------------- E
sec("E) Suppress path: RemoveAt + Compact + Repair + CapPlanarHoles")
hole_face_indices = []
for f in holed.Faces:
    cyl = try_cyl(f)
    if cyl is not None and abs(cyl.Radius - 6.0) < 0.05:
        hole_face_indices.append(f.FaceIndex)
out.append("  hole cylinder faces = %s" % hole_face_indices)
w = holed.DuplicateBrep()
for idx in sorted(hole_face_indices, reverse=True):
    w.Faces.RemoveAt(idx)
w.Compact()
rep = w.Repair(TOL)
out.append("  after remove: faces=%d IsSolid=%s Repair=%s" % (w.Faces.Count, w.IsSolid, rep))
capped = w.CapPlanarHoles(TOL)
out.append("  CapPlanarHoles -> %s IsSolid=%s faces=%s" % (
    capped is not None, capped.IsSolid if capped else None, capped.Faces.Count if capped else None))
if capped is not None and capped.IsSolid:
    capped.MergeCoplanarFaces(TOL)
    out.append("  after MergeCoplanarFaces: faces=%d" % capped.Faces.Count)

print("\n".join(out))
