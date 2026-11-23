# -*- coding: utf-8 -*-
"""In-process Roslyn compile of a Rhino 9 / .NET 8 plugin (no .NET SDK required).

Run INSIDE Rhino 9's Python 3 (ScriptEditor, or mcp__rhino__run_python),
with per-project globals set before exec:

    ROOT = r"C:\\path\\to\\YourPlugin"
    OUT_OVERRIDE = os.path.join(ROOT, "YourPlugin_v2.rhp")  # avoid LoadFrom lock
    FILES = ["AssemblyInfo.cs", "YourPlugin.cs", ...]
    ASSEMBLY_NAME = "YourPlugin"          # must match CSharpCompilation.Create name
    p = r"C:\\path\\to\\rhino9-plugin-workbench\\scripts\\Compile_Roslyn.py"
    exec(compile(open(p, encoding="utf-8").read(), p, "exec"))

Why Roslyn-in-Rhino: Rhino 9 ships Microsoft.CodeAnalysis.dll and has every
RhinoCommon reference loaded in its AppDomain, so the emitted .rhp targets the
exact runtime it will be loaded into.
"""
import os
import clr
import System
from System.IO import File, MemoryStream
from System.Text import Encoding
from System import AppDomain

ROS = globals().get("RHINO_SYSTEM") or r"C:\Program Files\Rhino 9\System"
ROOT = globals().get("ROOT") or os.getcwd()
SRC = os.path.join(ROOT, globals().get("SRC_DIR") or "src")
ASSEMBLY_NAME = globals().get("ASSEMBLY_NAME") or "DatumPlanePlugin"
OUT = globals().get("OUT_OVERRIDE") or os.path.join(ROOT, ASSEMBLY_NAME + ".rhp")

try:
    clr.AddReference(os.path.join(ROS, "Microsoft.CodeAnalysis.dll"))
    clr.AddReference(os.path.join(ROS, "Microsoft.CodeAnalysis.CSharp.dll"))
except Exception:
    import System.Reflection
    System.Reflection.Assembly.LoadFrom(os.path.join(ROS, "Microsoft.CodeAnalysis.dll"))
    System.Reflection.Assembly.LoadFrom(os.path.join(ROS, "Microsoft.CodeAnalysis.CSharp.dll"))

from Microsoft.CodeAnalysis import (MetadataReference, OutputKind, OptimizationLevel,
                                    NullableContextOptions, DiagnosticSeverity)
from Microsoft.CodeAnalysis.CSharp import (CSharpSyntaxTree, CSharpParseOptions,
                                           LanguageVersion, CSharpCompilation,
                                           CSharpCompilationOptions)

FILES = globals().get("FILES") or [
    "AssemblyInfo.cs", "DatumPlanePlugin.cs", "PlaneText.cs",
    "DatumPlaneLayers.cs", "DatumPlaneCore.cs",
    "DatumPlaneNormalView.cs", "AliasStyleDisplay.cs",
    "AliasStyleLink.cs", "JzMenu.cs", "DatumPlaneCommand.cs"]

refs, seen, skipped = [], set(), 0
for a in AppDomain.CurrentDomain.GetAssemblies():
    try:
        # Never reference an already-loaded older build of ourselves: it only
        # produces CS0436 "type conflicts with imported type" noise.
        if a.GetName().Name == ASSEMBLY_NAME:
            continue
        loc = a.Location
        if not loc or loc in seen:
            continue
        seen.add(loc)
        if not os.path.exists(loc):
            skipped += 1
            continue
        refs.append(MetadataReference.CreateFromFile(loc))
    except Exception:
        skipped += 1

parse = CSharpParseOptions(LanguageVersion.Latest)
trees = []
for f in FILES:
    path = os.path.join(SRC, f)
    trees.append(CSharpSyntaxTree.ParseText(File.ReadAllText(path, Encoding.UTF8), parse, path))

opts = CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary,
                                optimizationLevel=OptimizationLevel.Release,
                                nullableContextOptions=NullableContextOptions.Enable)
comp = CSharpCompilation.Create(ASSEMBLY_NAME, trees, refs, opts)
ms = MemoryStream()
res = comp.Emit(ms)

print("refs=%d skipped=%d" % (len(refs), skipped))
nerr = nwarn = 0
for d in res.Diagnostics:
    if d.Severity == DiagnosticSeverity.Error:
        nerr += 1
        print("ERROR " + d.ToString())
    elif d.Severity == DiagnosticSeverity.Warning:
        nwarn += 1
        print("WARN  " + d.ToString())
if res.Success:
    data = ms.ToArray()
    File.WriteAllBytes(OUT, data)
    print("COMPILE SUCCESS %d bytes, %d error, %d warning" % (len(data), nerr, nwarn))
else:
    print("COMPILE FAILED %d error, %d warning" % (nerr, nwarn))
