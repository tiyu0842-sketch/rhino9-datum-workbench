# -*- coding: utf-8 -*-
"""In-process Roslyn compile of RhinoFeatureWorks for Rhino 9 / .NET 8.

Run INSIDE Rhino 9's Python 3 (ScriptEditor, or mcp__rhino__run_python):

    p = r"C:\\Users\\21251\\WorkBuddy\\2026-11-21-15-41-26\\FeatureWorks\\verification\\Compile_Roslyn.py"
    exec(compile(open(p, encoding="utf-8").read(), p, "exec"))

Rationale (same as DatumPlanePlugin): no standalone .NET 8 SDK on this machine,
but Rhino 9 ships Microsoft.CodeAnalysis and has every RhinoCommon reference
already loaded. Compiling against the live AppDomain guarantees the emitted
.rhp targets exactly the runtime it will be loaded into.

The output assembly name is RhinoFeatureWorks -- a SEPARATE plugin from the
already-installed DatumPlanePlugin, so both Yak packages coexist.
"""
import os
import clr
import System
from System.IO import File, MemoryStream
from System.Text import Encoding
from System import AppDomain

ROS = r"C:\Program Files\Rhino 9\System"
ROOT = os.environ.get("FEATUREWORKS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
# 与 DatumPlane 一样支持 OUT_OVERRIDE：Rhino 可能正锁着 canonical .rhp，
# 编译输出要能改名，否则 Assembly.LoadFrom 锁文件会让新版本写不进去。
OUT = globals().get("OUT_OVERRIDE") or os.path.join(ROOT, "RhinoFeatureWorks.rhp")
ASSEMBLY_NAME = "RhinoFeatureWorks"

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

FILES = globals().get("FILES") or ["AssemblyInfo.cs", "FeatureWorksPlugin.cs", "FwModel.cs", "FwGraph.cs",
         "FwEngine.cs", "FwReconstruct.cs", "FwSurfaceEvidence.cs", "FwSelfTest.cs",
         "FwSession.cs", "FwPanel.cs", "FwCommands.cs",
         "FwFocus.cs", "FwSelectCommand.cs", "FwPickFeatureCommand.cs",
         "FwCancel.cs", "FwCancelCommand.cs", "FwCancelPanel.cs"]

refs, seen, skipped = [], set(), 0
for a in AppDomain.CurrentDomain.GetAssemblies():
    try:
        # Never reference an already-loaded older build of ourselves.
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
nerr = nwarn = noise1701 = 0
for d in res.Diagnostics:
    s = d.ToString()
    if d.Severity == DiagnosticSeverity.Error:
        nerr += 1
        print("ERROR " + s)
    elif d.Severity == DiagnosticSeverity.Warning:
        nwarn += 1
        if "CS1701" in s:          # System.Drawing 版本绑定噪声（Rhino 9 自带）
            noise1701 += 1
        else:
            print("WARN  " + s)
if noise1701:
    print("WARN  (CS1701 System.Drawing version noise x%d, suppressed)" % noise1701)
if res.Success:
    data = ms.ToArray()
    File.WriteAllBytes(OUT, data)
    print("COMPILE SUCCESS %d bytes, %d error, %d warning" % (len(data), nerr, nwarn))
else:
    print("COMPILE FAILED %d error, %d warning" % (nerr, nwarn))
