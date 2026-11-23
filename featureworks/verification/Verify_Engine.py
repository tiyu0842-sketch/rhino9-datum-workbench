# -*- coding: utf-8 -*-
"""Load the freshly compiled .rhp in-process and exercise the engine by reflection.

Run inside Rhino 9 Python 3 (no install / no Get() blocking):
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"))
"""
import clr
import System
import os
from System.Reflection import Assembly, BindingFlags

# Portable path: this script lives in featureworks/verification/, parent is the plugin root.
_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ROOT = globals().get("ROOT") or os.path.dirname(_HERE)
RHP = os.path.join(ROOT, "RhinoFeatureWorks.rhp")

out = []
def sec(s):
    out.append("\n=== " + s + " ===")

# Load the compiled plugin assembly into the live Rhino AppDomain.
asm = Assembly.LoadFrom(RHP)
out.append("asm = " + str(asm.GetName().Name) + " " + str(asm.GetName().Version))
out.append("size = " + str(os.path.getsize(RHP)) + " bytes")

types = [t for t in asm.GetTypes()]
out.append("types = " + str(len(types)))
cmd_types = [t for t in types if t.BaseType is not None and t.BaseType.Name == "Command"]
out.append("command classes = " + str(sorted([t.Name for t in cmd_types])))

sec("FwApi.SelfTest()  -- 7 end-to-end tests")
api = asm.GetType("RhinoFeatureWorks.FwApi")
selftest = api.GetMethod("SelfTest", BindingFlags.Public | BindingFlags.Static)
report_text = selftest.Invoke(None, None)
out.append(str(report_text))

# Also pull the structured report for machine-checkable PASS counts
st = asm.GetType("RhinoFeatureWorks.FwSelfTest")
rep = st.GetMethod("Run", BindingFlags.Public | BindingFlags.Static).Invoke(None, None)
out.append("STRUCTURED: total=%d pass=%d allpass=%s" % (
    rep.Total, rep.Pass, rep.AllPass))
for i in range(rep.Total):
    it = rep.Items[i]
    out.append("   %-52s %s  | %s" % (it.Name, "PASS" if it.Pass else "FAIL", it.Detail))

sec("FwApi.Recognize on a fresh dumb solid (public call path)")
import Rhino
import Rhino.Geometry as G
box = G.Box(G.Plane.WorldXY, G.Interval(0, 100), G.Interval(0, 80), G.Interval(0, 30)).ToBrep()
hole = G.Cylinder(G.Circle(G.Plane(G.Point3d(20, 20, -1), G.Vector3d.ZAxis), 6.0), 32.0).ToBrep(True, True)
solid = G.Brep.CreateBooleanDifference(box, hole, 0.001)[0]
rec = api.GetMethod("Recognize", BindingFlags.Public | BindingFlags.Static)
res = rec.Invoke(None, [solid, 0.001])
clean = res.Item1
feats = res.Item2
diag = res.Item3
out.append("clean faces = %d, solid = %s" % (clean.Faces.Count, clean.IsSolid))
out.append("features = %d" % feats.Count)
for i in range(feats.Count):
    f = feats[i]
    out.append("   " + f.OneLine(i))
out.append("diag = " + str(dict((str(k), int(diag.get_Item(k))) for k in diag.Keys)))
out.append("tree in clean.UserDictionary = " + str(
    clean.UserDictionary.ContainsKey("RhinoFeatureWorks_Tree_V1")))

print("\n".join(out))
