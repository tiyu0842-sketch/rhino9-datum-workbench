# -*- coding: utf-8 -*-
"""验证修复方案：顶点法算 depth + 槽口平面定位 + 工具 bbox 摆正重建。"""
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
BF = BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance
TOL = 0.001
out = []


def V(p):
    return G.Vector3d(p.X, p.Y, p.Z)


def dot(a, b):
    return G.Vector3d.Multiply(a, b)


# ---- build handbook base part ----
box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
hole = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
solid = G.Brep.CreateBooleanDifference(box, hole, TOL)[0]
pk = G.Box(G.Plane.WorldXY, G.Interval(50, 90), G.Interval(20, 60), G.Interval(20, 31)).ToBrep()
solid = G.Brep.CreateBooleanDifference(solid, pk, TOL)[0]

eng = System.Activator.CreateInstance(Eng)
r = Eng.GetMethod("RecognizeAll", BF).Invoke(eng, [solid, TOL])
clean, feats = r.Item1, r.Item2
pocket = None
for i in range(feats.Count):
    if feats[i].Type.ToString() == "ExtrudeCut":
        pocket = feats[i]
        break
out.append("pocket=%s stored Depth=%s outDir=%s" % (
    pocket is not None,
    pocket.Parameters.get_Item("Depth") if pocket is not None else "-",
    pocket.ExtrudeDirection if pocket is not None else "-"))

comp = set(int(x) for x in pocket.FaceIndices)
outDir = G.Vector3d(pocket.ExtrudeDirection)
outDir.Unitize()

# ---- 1. 顶点法 depth：只取真实 Brep 边端点，不用 face.GetBoundingBox ----
projs = []
mouthEdgeProjs = []
for e in clean.Edges:
    adj = e.AdjacentFaces()
    if adj is None or len(adj) != 2:
        continue
    a, b = int(adj[0]), int(adj[1])
    inA, inB = a in comp, b in comp
    if not (inA or inB):
        continue
    for pt in (e.PointAtStart, e.PointAtEnd):
        projs.append(dot(V(pt), outDir))
    if inA != inB:  # 槽口边：内表面 <-> 外表面
        mouthEdgeProjs.append(dot(V(e.PointAtStart), outDir))
        mouthEdgeProjs.append(dot(V(e.PointAtEnd), outDir))

out.append("edge-vertex proj range = %.4f .. %.4f  span=%.4f" % (
    min(projs), max(projs), max(projs) - min(projs)))
out.append("mouth-edge proj = %s" % ", ".join("%.4f" % x for x in sorted(set(round(v, 4) for v in mouthEdgeProjs))))
out.append("face-bbox proj span (old, wrong) = %.4f" % dot(
    V(clean.Faces[list(comp)[0]].GetBoundingBox(True).Max), outDir))

# ---- 2. 检查 Surface.CreateExtrusion 是否存在 ----
try:
    meths = [m.Name for m in G.Surface.GetMethods() if "Extrusion" in m.Name]
    out.append("Surface extrusion methods = %s" % meths)
except Exception as ex:
    out.append("Surface method probe failed: %s" % ex)

# ---- 3. 用新方案重建 depth = 18 ----
sup = Recon.GetMethod("SuppressFeature", BF).Invoke(None, [clean, pocket, TOL])
out.append("suppress: faces=%d IsSolid=%s" % (sup.Faces.Count, sup.IsSolid))

depth = 18.0
margin = TOL * 20.0
span = max(projs) - min(projs)                      # 真实槽深 = 10
c = pocket.ProfileCurve.DuplicateCurve()
pc = c.GetBoundingBox(True).Center                  # 底面外环中心 (70,40,20)
mouth = pc + outDir * span                          # 槽口平面点 (70,40,30)
out.append("profile center=%s  mouth=%s  span=%.4f" % (pc, mouth, span))

c.Translate(outDir * span)                           # 曲线抬到槽口平面
h = depth + 2.0 * margin
ext = G.Extrusion.Create(c, h, True)
out.append("Extrusion.Create(h=%.4f) -> %s" % (
    h, "null" if ext is None else str(ext.GetBoundingBox(True))))
tool = ext.ToBrep()
tb = tool.GetBoundingBox(True)
tmin = dot(V(tb.Min), outDir)
tmax = dot(V(tb.Max), outDir)
target_min = dot(V(mouth), outDir) - depth - margin
tool.Translate(outDir * (target_min - tmin))
tb2 = tool.GetBoundingBox(True)
out.append("tool aligned: proj %.4f .. %.4f (target %.4f .. %.4f)" % (
    dot(V(tb2.Min), outDir), dot(V(tb2.Max), outDir),
    target_min, target_min + h))
diff = G.Brep.CreateBooleanDifference(sup, tool, TOL)
out.append("diff -> %s" % ("null/empty" if diff is None or len(diff) == 0 else
                           "faces=%d bbox=%s" % (diff[0].Faces.Count, diff[0].GetBoundingBox(True))))
if diff is not None and len(diff) > 0:
    eng2 = System.Activator.CreateInstance(Eng)
    r2 = Eng.GetMethod("RecognizeAll", BF).Invoke(eng2, [diff[0], TOL])
    out.append("re-recognized %d:" % r2.Item2.Count)
    for i in range(r2.Item2.Count):
        out.append("   " + r2.Item2[i].OneLine(i))

print("\n".join(out))
