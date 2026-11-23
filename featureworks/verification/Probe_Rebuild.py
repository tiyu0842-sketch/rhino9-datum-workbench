# -*- coding: utf-8 -*-
"""Diagnose pocket Depth=11 (expect 10) and pocket rebuild failure."""
import clr
import os
import System
from System.Reflection import Assembly, BindingFlags
import Rhino.Geometry as G

# Portable path: this script lives in featureworks/verification/, parent is the plugin root.
_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
RHP = globals().get("RHP") or os.path.join(os.path.dirname(_HERE), "RhinoFeatureWorks.rhp")
asm = Assembly.LoadFrom(RHP)
Api = asm.GetType("RhinoFeatureWorks.FwApi")
Eng = asm.GetType("RhinoFeatureWorks.FeatureRecognitionEngine")
Recon = asm.GetType("RhinoFeatureWorks.FeatureReconstructionService")
BF = BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance

TOL = 0.001
out = []

# Build the handbook base part
box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
hole = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
solid = G.Brep.CreateBooleanDifference(box, hole, TOL)[0]
pk = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(20, 31)).ToBrep()
solid = G.Brep.CreateBooleanDifference(solid, pk, TOL)[0]
out.append("solid: faces=%d IsSolid=%s bbox=%s" % (solid.Faces.Count, solid.IsSolid, solid.GetBoundingBox(True)))

eng = System.Activator.CreateInstance(Eng)
r = Eng.GetMethod("RecognizeAll", BF).Invoke(eng, [solid, TOL])
clean, feats = r.Item1, r.Item2
out.append("recognized %d:" % feats.Count)
for i in range(feats.Count):
    f = feats[i]
    out.append("  " + f.OneLine(i))
    out.append("      faceIdx=%s refOrigin=%s outDir=%s profile=%s" % (
        str(list(f.FaceIndices)), str(f.ReferencePlane.Origin), str(f.ExtrudeDirection),
        "null" if f.ProfileCurve is None else str(f.ProfileCurve.GetBoundingBox(True))))

pocket = None
for i in range(feats.Count):
    if feats[i].Type.ToString() == "ExtrudeCut":
        pocket = feats[i]
        break
out.append("\npocket found = %s" % (pocket is not None))

if pocket is not None:
    # What is the bbox of the pocket component faces?
    bb = G.BoundingBox.Empty
    for fid in pocket.FaceIndices:
        fb = clean.Faces[fid].GetBoundingBox(True)
        bb.Union(fb)
        out.append("   face %d bbox=%s  rev=%s" % (fid, fb, clean.Faces[fid].OrientationIsReversed))
    out.append("   component bbox=%s diagonal=%s dot(outDir)=%.4f" % (
        bb, bb.Diagonal, G.Vector3d.Multiply(bb.Diagonal, pocket.ExtrudeDirection)))
    out.append("   stored Depth=%s" % pocket.Parameters.get_Item("Depth"))

    # Suppress step
    sup = Recon.GetMethod("SuppressFeature", BF).Invoke(None, [clean, pocket, TOL])
    out.append("\nAFTER SUPPRESS: faces=%d IsSolid=%s bbox=%s" % (
        sup.Faces.Count, sup.IsSolid, sup.GetBoundingBox(True)))

    # Now manually reproduce what Rebuild does
    margin = TOL * 20.0
    depth = 18.0
    c = pocket.ProfileCurve.DuplicateCurve()
    out.append("\nprofile bbox BEFORE translate = %s" % c.GetBoundingBox(True))
    c.Translate(pocket.ExtrudeDirection * (depth + margin))
    out.append("profile bbox AFTER translate(+depth) = %s" % c.GetBoundingBox(True))
    ext = G.Extrusion.Create(c, -(depth + margin * 2), True)
    out.append("Extrusion.Create -> %s" % ("null" if ext is None else str(ext.GetBoundingBox(True))))
    if ext is not None:
        tool = ext.ToBrep()
        diff = G.Brep.CreateBooleanDifference(sup, tool, TOL)
        out.append("diff -> %s" % ("null/empty" if diff is None or len(diff) == 0 else
                                    "faces=%d bbox=%s" % (diff[0].Faces.Count, diff[0].GetBoundingBox(True))))
        if diff is not None and len(diff) > 0:
            eng2 = System.Activator.CreateInstance(Eng)
            r2 = Eng.GetMethod("RecognizeAll", BF).Invoke(eng2, [diff[0], TOL])
            out.append("   re-recognized %d:" % r2.Item2.Count)
            for i in range(r2.Item2.Count):
                out.append("      " + r2.Item2[i].OneLine(i))

print("\n".join(out))
