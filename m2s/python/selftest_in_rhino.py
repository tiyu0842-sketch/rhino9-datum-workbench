# -*- coding: utf-8 -*-
r"""
selftest_in_rhino.py —— m2s / NFF 插件真机自检（必须在 Rhino 9 的 Python 里跑）

执行（MCP run_python）：
    P = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\github-release\m2s\python\selftest_in_rhino.py"
    exec(compile(open(P, encoding="utf-8").read(), P, "exec"), globals())

不依赖交互选对象：测试网格由脚本用 Rhino 内核直接造，跑完会在当前文档留下
一个灰色测试网格 + 一个棕色拟合平面，方便目视确认。

覆盖：
  T1 环境 / RhinoCommon 关键 API 探测
  T2 Rhino 内核网格 → 抽 vertices/faces（验证 MeshFace .A/.B/.C/.D）
  T3 chain_core.run_chain 法向+曲率双筛 → 平面拟合 → 合格判定
  T4 FitSurfaceCommand 的 Rhino 内核拟合 → 偏差 → 真实创建 PlaneSurface 对象
  T5 doc.Strings 文档字符串写回读回
  T6 异常输入不崩溃（退化点集 / 法向筛零命中）
  TX 汇总
"""

import os
import sys
import math
import importlib
import traceback

import Rhino
import System.Drawing

ROOT = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\github-release"
M2S = os.path.join(ROOT, "m2s", "python")
NFF = os.path.join(ROOT, "nff", "python")
for p in (M2S, NFF):
    if p not in sys.path:
        sys.path.insert(0, p)

import surfacefit_core as SF
import nff_core as NFFcore
import chain_core as CH
import FitSurfaceCommand as FC

# Rhino 进程会缓存模块，改过代码必须 reload，否则测的是旧版本
for _m in (SF, NFFcore, CH, FC):
    try:
        importlib.reload(_m)
    except Exception as _e:
        print("  WARN  reload %s: %r" % (_m.__name__, _e))

doc = globals().get("__rhino_doc__")
RESULTS = {}

# 重复跑自检时不堆积测试对象：先删掉自己上次留下的
if doc:
    try:
        _doomed = [o.Id for o in doc.Objects
                   if o.Attributes and o.Attributes.Name
                   and o.Attributes.Name.startswith("M2S_SelfTest_")]
        for _oid in _doomed:
            doc.Objects.Delete(_oid, True)
        if _doomed:
            print("  清理上次自检对象: %d 个" % len(_doomed))
    except Exception as _e:
        print("  WARN 清理失败: %r" % _e)


def mark(name, ok, detail=""):
    RESULTS[name] = {"ok": bool(ok), "detail": str(detail)}
    print(("  PASS  " if ok else "  FAIL  ") + name + " | " + str(detail)[:400])


def section(title):
    print("")
    print("--- " + title + " ---")


print("=== m2s 真机自检 START ===")

# ---------------------------------------------------------------------------
section("T1 环境 / RhinoCommon")
try:
    mark("T1 Rhino 版本", True, "RhinoApp.Version=%s / doc=%s" %
         (Rhino.RhinoApp.Version, "OK" if doc else "MISSING"))
except Exception as e:
    mark("T1 Rhino 版本", False, repr(e))

try:
    _sig = Rhino.Geometry.Plane.FitPlaneToPoints
    mark("T1 FitPlaneToPoints 可调用", callable(_sig), str(_sig)[:120])
except Exception as e:
    mark("T1 FitPlaneToPoints 可调用", False, repr(e))


# ---------------------------------------------------------------------------
def mesh_to_arrays(m):
    """Rhino Mesh -> (vertices tuples, faces index tuples)。同时验证 MeshFace API。"""
    vs = []
    for i in range(m.Vertices.Count):
        v = m.Vertices[i]
        vs.append((float(v.X), float(v.Y), float(v.Z)))
    fs = []
    for i in range(m.Faces.Count):
        f = m.Faces[i]
        idx = [int(f.A), int(f.B), int(f.C)]
        if not f.IsTriangle:
            idx.append(int(f.D))
        fs.append(tuple(idx))
    return vs, fs


meshA = None
vs = fs = None
section("T2 Rhino 内核网格")
try:
    # 扁盒 20x20x2，顶面细分 2x2：模拟"扫描网格里一层朝上的面"
    box = Rhino.Geometry.Box(
        Rhino.Geometry.Plane.WorldXY,
        Rhino.Geometry.Interval(-10, 10),
        Rhino.Geometry.Interval(-10, 10),
        Rhino.Geometry.Interval(0, 2))
    meshA = Rhino.Geometry.Mesh.CreateFromBox(box, 2, 2, 1)
    meshA.Normals.ComputeNormals()
    vs, fs = mesh_to_arrays(meshA)
    mark("T2 CreateFromBox + MeshFace 抽取",
         meshA.Faces.Count > 0 and len(vs) > 0,
         "faces=%d verts=%d 首面=%s 三角形=%s" %
         (meshA.Faces.Count, len(vs), fs[0], meshA.Faces[0].IsTriangle))
except Exception as e:
    mark("T2 CreateFromBox + MeshFace 抽取", False, traceback.format_exc())

# 把测试网格放进文档，方便目视核对
if meshA is not None and doc:
    try:
        att = Rhino.DocObjects.ObjectAttributes()
        att.Name = "M2S_SelfTest_Mesh"
        att.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
        att.ObjectColor = System.Drawing.Color.FromArgb(140, 148, 160)
        mid = doc.Objects.AddMesh(meshA, att)
        mark("T2 网格写入文档", mid is not None, "obj=%s" % mid)
    except Exception as e:
        mark("T2 网格写入文档", False, traceback.format_exc())


# ---------------------------------------------------------------------------
section("T3 chain_core 双筛链（真机网格输入）")
res = None
if vs and fs:
    try:
        res = CH.run_chain(vs, fs, direction=(0, 0, 1), angle_deg=30,
                           k_max=0.05, rms_tolerance=0.5,
                           within_tolerance=0.8, verbose=True)
        n = res["plane"]["normal"] if res["plane"] else (0, 0, 0)
        # 候选面是否都朝上（排除竖直侧面）
        cand_normals = []
        for fi in res["candidates"]:
            a, b, c = (vs[fs[fi][0]], vs[fs[fi][1]], vs[fs[fi][2]])
            u = SF.sub(b, a)
            v = SF.sub(c, a)
            cand_normals.append(SF.normalize(SF.cross(u, v))[2])
        all_up = all(z > 0.5 for z in cand_normals) if cand_normals else False
        ok = (res["accepted"] and abs(n[2]) > 0.9 and all_up
              and res["deviation"]["rms"] < 0.5)
        mark("T3 双筛→拟合→判定", ok,
             "normal=%s rms=%.6f max=%.6f cand=%d all_up=%s reason=%s" %
             (tuple(round(x, 4) for x in n),
              res["deviation"]["rms"] if res["deviation"] else -1,
              res["deviation"]["max"] if res["deviation"] else -1,
              len(res["candidates"]), all_up, res["reason"]))
    except Exception as e:
        mark("T3 双筛→拟合→判定", False, traceback.format_exc())
else:
    mark("T3 双筛→拟合→判定", False, "T2 未产出网格数据，跳过")


# ---------------------------------------------------------------------------
section("T4 FitSurfaceCommand 的 Rhino 内核路径")
plane_rh = None
pts_rh = None
if meshA is not None and res and res["candidates"]:
    try:
        pts_rh = FC.collect_points(meshA, res["candidates"])
        # Point3f -> Point3d 显式转换：真机已确认 Rhino 9 绑定会自动转换，
        # 这里显式转只是跨版本保险，避免旧版 IEnumerable<Point3d> 绑定失败
        pts_rh = [Rhino.Geometry.Point3d(float(p.X), float(p.Y), float(p.Z))
                  for p in pts_rh]
        plane_rh, fit_err = FC.fit_with_rhino(pts_rh)
        mark("T4 FitPlaneToPoints 拟合", plane_rh is not None,
             "result=%s origin=%s normal=%s pts=%d" %
             (fit_err, plane_rh.Origin if plane_rh else None,
              plane_rh.Normal if plane_rh else None, len(pts_rh)))
    except Exception as e:
        mark("T4 FitPlaneToPoints 拟合", False, traceback.format_exc())

    if plane_rh is not None:
        try:
            st = FC.deviation(meshA, plane_rh, pts_rh)
            mark("T4 偏差统计", st["rms"] < 0.5,
                 "n=%d mean=%.6f rms=%.6f max=%.6f within0.5=%.2f" %
                 (st["n"], st["mean"], st["rms"], st["max"], st["within_0_5"]))
        except Exception as e:
            mark("T4 偏差统计", False, traceback.format_exc())

        try:
            half = max(1.0, max(p.DistanceTo(plane_rh.Origin) for p in pts_rh)) * 1.05
            iv = Rhino.Geometry.Interval(-half, half)
            surf = Rhino.Geometry.PlaneSurface(plane_rh, iv, iv)
            att = Rhino.DocObjects.ObjectAttributes()
            att.Name = "M2S_SelfTest_FitPlane"
            att.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
            att.ObjectColor = System.Drawing.Color.FromArgb(176, 132, 70)
            oid = doc.Objects.AddSurface(surf, att)
            doc.Views.Redraw()
            mark("T4 创建 PlaneSurface 对象", oid is not None,
                 "obj=%s half=%.2f color=brown" % (oid, half))
        except Exception as e:
            mark("T4 创建 PlaneSurface 对象", False, traceback.format_exc())
else:
    mark("T4 FitSurfaceCommand 路径", False, "前置条件不足，跳过")


# ---------------------------------------------------------------------------
section("T5 doc.Strings 文档字符串")
if doc:
    try:
        doc.Strings.SetString("M2S", "LastFit",
                              "selftest rms=%.6f obj=auto" %
                              (res["deviation"]["rms"] if res and res["deviation"] else -1))
        got = None
        for getter in ("GetValue", "GetString"):
            try:
                got = getattr(doc.Strings, getter)("M2S", "LastFit")
                if got:
                    break
            except Exception:
                continue
        mark("T5 写入并读回", bool(got), "readback=%s (getter=%s)" % (got, getter))
    except Exception as e:
        mark("T5 写入并读回", False, traceback.format_exc())


# ---------------------------------------------------------------------------
section("T6 异常输入不崩溃")
try:
    r1 = SF.fit_plane([(0, 0, 0), (1, 1, 1)])  # 点数 < 3
    ok1 = r1 is None
    # 用 (1,1,1) 方向 + 5°：轴对齐盒子所有面法向与它夹角都是 54.7°，必然零命中
    r2 = CH.run_chain(vs or [], fs or [], direction=(1, 1, 1),
                      angle_deg=5.0, verbose=False)
    ok2 = (not r2["accepted"]) and ("法向筛无命中" in r2["reason"])
    mark("T6 退化/零命中", ok1 and ok2,
         "fit_plane(<3)=%r / zero-hit reason=%s" % (r1, r2["reason"]))
except Exception as e:
    mark("T6 退化/零命中", False, traceback.format_exc())


# ---------------------------------------------------------------------------
section("T7 倾斜带噪扫描面（法向方向筛选 + 带噪拟合）")
try:
    # 4x4 顶点 / 3x3 quad：z = 8 + 0.2*x + 确定性小噪声，理论倾角约 11.3°
    xs = [-9.0, -3.0, 3.0, 9.0]
    ys = [-9.0, -3.0, 3.0, 9.0]
    noise = [[0.00, 0.12, -0.08, 0.05],
             [0.10, -0.05, 0.14, -0.10],
             [-0.07, 0.09, 0.03, -0.12],
             [0.06, -0.11, 0.08, 0.02]]
    vertsB = []
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            vertsB.append((x, y, 8.0 + 0.2 * x + noise[i][j]))
    vid = lambda i, j: i * 4 + j
    facesB = []
    for i in range(3):
        for j in range(3):
            facesB.append((vid(i, j), vid(i + 1, j), vid(i + 1, j + 1), vid(i, j + 1)))
    # 3 个竖直侧面（x=9，法向 ±X，与 +Z 夹角 90°），用来验证"朝向不对会被剔除"
    side_start = len(vertsB)
    for j, y in enumerate(ys):
        vertsB.append((9.0, y, 0.0))
    for j in range(3):
        facesB.append((vid(3, j), vid(3, j + 1),
                       side_start + j + 1, side_start + j))

    rB = CH.run_chain(vertsB, facesB, direction=(0, 0, 1), angle_deg=20,
                      k_max=0.05, rms_tolerance=0.5, verbose=True)
    nB = rB["plane"]["normal"] if rB["plane"] else (0, 0, 0)
    nlen = math.sqrt(sum(x * x for x in nB))
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, nB[2] / nlen)))) if nlen else -1
    # 候选面不得包含侧面（侧面索引 >= 9）
    no_side = all(i < 9 for i in rB["candidates"])
    okB = (rB["accepted"] and no_side and 8 < tilt < 16
           and rB["deviation"]["rms"] < 0.5)
    mark("T7 倾斜面筛选+带噪拟合", okB,
         "tilt=%.2f° (理论 11.3°) rms=%.4f max=%.4f cand=%d(应≤9) no_side=%s" %
         (tilt, rB["deviation"]["rms"], rB["deviation"]["max"],
          len(rB["candidates"]), no_side))

    # 顺带验证 NFF 的"斜向面带"能力：min_angle 排除正对 +Z 的面
    band = NFFcore.filter_faces(vertsB, facesB, (0, 0, 1), 30,
                                min_angle_deg=8.0)
    band_ok = len(band["kept"]) == 9 and all(i < 9 for i in band["kept"])
    mark("T7 min_angle 斜向面带", band_ok,
         "kept=%d (预期 9 个倾斜面) angles=%s" %
         (len(band["kept"]),
          [round(band["angles"][i], 1) for i in band["kept"][:4]]))
except Exception as e:
    mark("T7 倾斜面筛选+带噪拟合", False, traceback.format_exc())


# ---------------------------------------------------------------------------
section("T8 FitSurfaceCommand.run_fit 非交互端到端")
try:
    _mesh = None
    for _o in doc.Objects:
        if _o.Attributes and _o.Attributes.Name == "M2S_SelfTest_Mesh":
            _mesh = _o.Geometry
            break
    fit = FC.run_fit(doc, _mesh, res["candidates"],
                     name="M2S_SelfTest_RunFit")
    exists = any(o.Attributes and o.Attributes.Name == "M2S_SelfTest_RunFit"
                 for o in doc.Objects)
    ok8 = (fit["ok"] and exists and fit["points"] >= 3
           and fit["deviation"]["rms"] < 0.5)
    mark("T8 run_fit 端到端（含真实建面）", ok8,
         "obj=%s pts=%d faces=%d rms=%.6f 对象在文档=%s" %
         (fit["object_id"], fit["points"], fit["faces"],
          fit["deviation"]["rms"], exists))
except Exception as e:
    mark("T8 run_fit 端到端（含真实建面）", False, traceback.format_exc())


# ---------------------------------------------------------------------------
section("TX 汇总")
passed = sum(1 for v in RESULTS.values() if v["ok"])
total = len(RESULTS)
print("  TOTAL: %d/%d PASS" % (passed, total))
for k in sorted(RESULTS):
    if not RESULTS[k]["ok"]:
        print("  FAILED ITEM: %s -> %s" % (k, RESULTS[k]["detail"][:200]))
print("=== m2s 真机自检 %s ===" % ("ALL GREEN" if passed == total else "HAS FAILURES"))
