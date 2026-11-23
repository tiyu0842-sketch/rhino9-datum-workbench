# -*- coding: utf-8 -*-
"""查清新布尔差集产生的槽内表面为何不被识别：比较 rev / 法向 / 包围盒边界判据。"""
import clr
import os
import System
from System.Reflection import Assembly, BindingFlags
import Rhino.Geometry as G

# Portable path: this script lives in featureworks/verification/, parent is the plugin root.
_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
RHP = globals().get("RHP") or os.path.join(os.path.dirname(_HERE), "RhinoFeatureWorks.rhp")
asm = Assembly.LoadFrom(RHP)
Eng = asm.GetType("RhinoFeatureWorks.FeatureRecognitionEngine")
Recon = asm.GetType("RhinoFeatureWorks.FeatureReconstructionService")
Graph = asm.GetType("RhinoFeatureWorks.AttributedFaceAdjacencyGraph")
BF = BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance
TOL = 0.001
out = []


def V(p):
    return G.Vector3d(p.X, p.Y, p.Z)


def dot(a, b):
    return G.Vector3d.Multiply(a, b)


def describe(brep, tag):
    out.append("---- %s : faces=%d IsSolid=%s bbox=%s ----" % (
        tag, brep.Faces.Count, brep.IsSolid, brep.GetBoundingBox(True)))
    g = System.Activator.CreateInstance(Graph)
    Graph.GetMethod("Build", BF).Invoke(g, [brep, TOL])
    wb = Graph.GetProperty("WorkingBrep", BF).GetValue(g)
    nodes = Graph.GetProperty("Nodes", BF).GetValue(g)
    for i in range(wb.Faces.Count):
        f = wb.Faces[i]
        pl = None
        ok, plane = f.TryGetPlane(TOL)
        if ok:
            pl = plane
        n = "-"
        if pl is not None:
            n = "(%.1f,%.1f,%.1f)" % (pl.Normal.X, pl.Normal.Y, pl.Normal.Z)
        bb = f.GetBoundingBox(True)
        out.append("  F%-2d rev=%-5s area=%9.2f ctr=(%6.1f,%6.1f,%6.1f) N=%-18s bboxZ=%.2f..%.2f" % (
            i, f.OrientationIsReversed, G.AreaMassProperties.Compute(f.DuplicateFace(False)).Area,
            f.GetBoundingBox(True).Center.X, f.GetBoundingBox(True).Center.Y,
            f.GetBoundingBox(True).Center.Z, n, bb.Min.Z, bb.Max.Z))


# ---- original pocket (rev=True reference) ----
box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
hole = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
solid = G.Brep.CreateBooleanDifference(box, hole, TOL)[0]
pk = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(20, 31)).ToBrep()
orig = G.Brep.CreateBooleanDifference(solid, pk, TOL)[0]

eng = System.Activator.CreateInstance(Eng)
r = Eng.GetMethod("RecognizeAll", BF).Invoke(eng, [orig, TOL])
clean, feats = r.Item1, r.Item2
pocket = None
for i in range(feats.Count):
    if feats[i].Type.ToString() == "ExtrudeCut":
        pocket = feats[i]
        break
describe(clean, "ORIGINAL (recognized as pocket)")

# ---- rebuilt pocket (the one that is NOT recognized) ----
sup = Recon.GetMethod("SuppressFeature", BF).Invoke(None, [clean, pocket, TOL])
depth = 18.0
margin = TOL * 20.0
outDir = G.Vector3d(pocket.ExtrudeDirection)
outDir.Unitize()
c = pocket.ProfileCurve.DuplicateCurve()
pc = c.GetBoundingBox(True).Center
span = 10.0
c.Translate(outDir * span)
ext = G.Extrusion.Create(c, depth + 2.0 * margin, True)
tool = ext.ToBrep()
tb = tool.GetBoundingBox(True)
tmin = dot(V(tb.Min), outDir)
tool.Translate(outDir * (dot(V(pc + outDir * span), outDir) - depth - margin - tmin))
diff = G.Brep.CreateBooleanDifference(sup, tool, TOL)[0]
describe(diff, "REBUILT (not recognized)")

# ---- try flipped tool ----
tool2 = ext.ToBrep()
try:
    tool2.Flip()
    out.append("Flip() ok")
except Exception as ex:
    out.append("Flip() failed: %s" % ex)
tb2 = tool2.GetBoundingBox(True)
tool2.Translate(outDir * (dot(V(pc + outDir * span), outDir) - depth - margin - dot(V(tb2.Min), outDir)))
d2 = G.Brep.CreateBooleanDifference(sup, tool2, TOL)[0]
describe(d2, "REBUILT with FLIPPED tool")
eng2 = System.Activator.CreateInstance(Eng)
r2 = Eng.GetMethod("RecognizeAll", BF).Invoke(eng2, [d2, TOL])
out.append("flipped-tool re-recognized %d:" % r2.Item2.Count)
for i in range(r2.Item2.Count):
    out.append("   " + r2.Item2[i].OneLine(i))

# ---- alternate: box tool built the same way as original ----
pk2 = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(12, 31)).ToBrep()
d3 = G.Brep.CreateBooleanDifference(sup, pk2, TOL)[0]
describe(d3, "REBUILT with BOX tool (12..31)")
eng3 = System.Activator.CreateInstance(Eng)
r3 = Eng.GetMethod("RecognizeAll", BF).Invoke(eng3, [d3, TOL])
out.append("box-tool re-recognized %d:" % r3.Item2.Count)
for i in range(r3.Item2.Count):
    out.append("   " + r3.Item2[i].OneLine(i))

print("\n".join(out))
