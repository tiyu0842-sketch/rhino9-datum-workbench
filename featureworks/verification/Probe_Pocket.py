# -*- coding: utf-8 -*-
"""Diagnose why Pass 3 does not find the rectangular pocket."""
import clr
import System
import os
from System.Reflection import Assembly, BindingFlags
import Rhino.Geometry as G

# Portable path: this script lives in featureworks/verification/, parent is the plugin root.
_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
RHP = globals().get("RHP") or os.path.join(os.path.dirname(_HERE), "RhinoFeatureWorks.rhp")
asm = Assembly.LoadFrom(RHP)
Graph = asm.GetType("RhinoFeatureWorks.AttributedFaceAdjacencyGraph")
Node = asm.GetType("RhinoFeatureWorks.FaceNode")
Adj = asm.GetType("RhinoFeatureWorks.AdjacencyEdge")
Engine = asm.GetType("RhinoFeatureWorks.FeatureRecognitionEngine")

TOL = 0.001
out = []

def build(with_hole=True, with_pocket=True):
    box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
    solid = box
    if with_hole:
        hole = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
        solid = G.Brep.CreateBooleanDifference(solid, hole, TOL)[0]
    if with_pocket:
        pk = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(20, 31)).ToBrep()
        solid = G.Brep.CreateBooleanDifference(solid, pk, TOL)[0]
    return solid

for label, wh, wp in [("pocket only", False, True), ("hole + pocket", True, True)]:
    solid = build(wh, wp)
    out.append("\n=== %s : faces=%d edges=%d solid=%s ===" % (
        label, solid.Faces.Count, solid.Edges.Count, solid.IsSolid))

    g = System.Activator.CreateInstance(Graph)
    Graph.GetMethod("Build", BindingFlags.Public | BindingFlags.Instance).Invoke(
        g, [solid, TOL])
    wb = Graph.GetProperty("WorkingBrep").GetValue(g, None)
    nodes = Graph.GetProperty("Nodes").GetValue(g, None)
    out.append("  after MergeCoplanarFaces+Compact: faces=%d nodes=%d" % (wb.Faces.Count, nodes.Count))

    for k in nodes.Keys:
        n = nodes.get_Item(k)
        cat = n.Category.ToString()
        ctr = n.Centroid
        conv = {}
        for e in n.Neighbors:
            key = e.Convexity.ToString()
            conv[key] = conv.get(key, 0) + 1
        # plane normal if plane
        extra = ""
        try:
            pl = n.PlaneData
            extra = " N=(%.1f,%.1f,%.1f)" % (pl.Normal.X, pl.Normal.Y, pl.Normal.Z)
        except Exception:
            pass
        out.append("  F%-2d %-9s area=%8.2f ctr=(%6.1f,%6.1f,%6.1f) concave=%-5s edges=%s%s" % (
            k, cat, n.Area, ctr.X, ctr.Y, ctr.Z, str(n.IsConcaveSurface), str(conv), extra))

    eng = System.Activator.CreateInstance(Engine)
    r = Engine.GetMethod("RecognizeAll", BindingFlags.Public | BindingFlags.Instance).Invoke(
        eng, [solid, TOL])
    feats = r.Item2
    out.append("  RECOGNIZED %d features:" % feats.Count)
    for i in range(feats.Count):
        out.append("     " + feats[i].OneLine(i))
    diag = eng.Diagnostics
    out.append("  diag = " + str(dict((str(k), int(diag.get_Item(k))) for k in diag.Keys)))

print("\n".join(out))
