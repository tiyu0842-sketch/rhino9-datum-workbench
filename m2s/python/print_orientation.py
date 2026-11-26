# -*- coding: utf-8 -*-
"""print_orientation.py —— 把曲面法向分析整合成 FDM 打印朝向评估（重力模拟）。

原理（FDM 的重力/自支撑判据）
-----------------------------
打印时熔融塑料靠下一层支撑。面法向 n 与打印 Z 轴（重力反方向）的夹角 θ 决定
这一片能不能自支撑：

    θ = acos(n · +Z)
      θ < 45°   面朝上      —— 完全自支撑（顶面/爬坡）
    45–90°      近垂直      —— 自支撑，但接近临界（外壁）
    90–135°     悬垂        —— 需要支撑，或靠桥接/冷却（内壁、下坡）
    θ > 135°    朝下底面    —— 必须支撑（纯悬空）

判据依据：常规 FDM 的临界悬垂角约 45°（相对垂直），即 θ≈135°；
超过就基本必须加支撑。桥接（bridge）能覆盖一小段，但不能大面积。

本脚本做什么
------------
1. 解析二进制 STL，逐面算法向（面积加权，不用文件头里可能为零的法向）；
2. 按当前摆放（+Z 为打印方向）统计四个区间的**面积占比**；
3. 候选朝向搜索：把模型绕 X/Y 轴按 step 度旋转，找"朝下底面面积最小"的朝向
   —— 这就是重力意义下的最优摆放（支撑最少、翘边风险最低）；
4. 输出 JSON + 人类可读报告，供切片参数调整使用。

诚实边界
--------
* 这是**朝向评估**，不是力学仿真：不模拟材料下垂、热变形、层间结合强度。
* 面积加权比面数更接近实际打印耗时/支撑量。
* 内腔/中空结构的"朝下面"未必真需要支撑（可能只是内壁），报告会标注为提示而非定论。
* 150 万面时用 stride 抽样加速；要精确结果把 stride 设为 1。

用法
----
    python print_orientation.py                 # 当前 STL，默认 stride=1
    python print_orientation.py --stride 8      # 抽样
    python print_orientation.py --axis X        # 额外评估绕 X 轴旋转的候选
"""
from __future__ import annotations

import json
import math
import os
import struct
import sys
import time
from typing import Any

from units import mm, MM_PER_UNIT, UNITS_HINT, MODEL_HEIGHT_MM

_HERE = os.path.dirname(os.path.abspath(__file__))
STL = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\stl\model.stl"
OUT_JSON = os.path.join(_HERE, "print_orientation_result.json")
OUT_TXT = os.path.join(_HERE, "print_orientation_report.txt")

# 四个重力区间（相对 +Z 的夹角）
BANDS = [
    (0.0, 45.0, "self_support", "朝上/自支撑"),
    (45.0, 90.0, "near_vertical", "近垂直"),
    (90.0, 135.0, "overhang", "悬垂（临界/需支撑）"),
    (135.0, 181.0, "downward", "朝下底面（必须支撑）"),
]


def load_faces(path: str, stride: int = 1):
    """返回 (normals, areas)：按 stride 抽样的面法向与面积（数值单位）。"""
    with open(path, "rb") as f:
        head = f.read(84)
    n = struct.unpack_from("<I", head, 80)[0]
    normals: list[tuple[float, float, float]] = []
    areas: list[float] = []
    with open(path, "rb") as f:
        f.seek(84)
        for i in range(n):
            data = f.read(50)
            if len(data) < 50:
                break
            if stride > 1 and i % stride:
                continue
            v = struct.unpack_from("<12fH", data)
            ax, ay, az = v[3], v[4], v[5]
            bx, by, bz = v[6], v[7], v[8]
            cx, cy, cz = v[9], v[10], v[11]
            ux, uy, uz = bx - ax, by - ay, bz - az
            wx, wy, wz = cx - ax, cy - ay, cz - az
            nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
            L = math.sqrt(nx * nx + ny * ny + nz * nz)
            if L < 1e-15:
                continue
            area = L * 0.5
            normals.append((nx / L, ny / L, nz / L))
            areas.append(area)
    return normals, areas


def rotate_axis(n: tuple[float, float, float], axis: str, deg: float):
    """把法向绕 X 或 Y 轴旋转 deg 度（用于评估不同摆放朝向）。"""
    x, y, z = n
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    if axis == "X":
        return (x, c * y - s * z, s * y + c * z)
    if axis == "Y":
        return (c * x + s * z, y, -s * x + c * z)
    return n


def evaluate(normals, areas, axis: str = "Z", deg: float = 0.0) -> dict[str, Any]:
    """统计该朝向下四个重力区间的面积占比。"""
    totals = {key: 0.0 for _, _, key, _ in BANDS}
    total = 0.0
    for n, a in zip(normals, areas):
        nn = rotate_axis(n, axis, deg) if deg else n
        z = max(-1.0, min(1.0, nn[2]))
        theta = math.degrees(math.acos(z))
        total += a
        for lo, hi, key, _ in BANDS:
            if lo <= theta < hi:
                totals[key] += a
                break
    return {
        "axis": axis, "rotation_deg": deg,
        "total_area": total,
        "bands": {
            key: {
                "area": round(val, 6),
                # 面积是长度的平方：要乘 MM_PER_UNIT²，不能先 mm() 再平方
                # （mm(val)=val×153；再平方会变成 ×23409 而不是正确的 ×153²）
                "area_mm2": round(val * MM_PER_UNIT * MM_PER_UNIT, 1),
                "pct": round(100.0 * val / total, 2) if total else 0.0,
                "label": label,
            }
            for (_, _, key, label), val in ((b, totals[b[2]]) for b in BANDS)
        },
    }


def search_best(normals, areas, step: int = 15) -> list[dict[str, Any]]:
    """绕 X/Y 各 0–180° 搜索，按'朝下底面面积'升序返回前若干候选。"""
    cands = []
    for axis in ("X", "Y"):
        for deg in range(0, 181, step):
            r = evaluate(normals, areas, axis, deg)
            down = r["bands"]["downward"]["pct"]
            over = r["bands"]["overhang"]["pct"]
            cands.append({
                "axis": axis, "deg": deg,
                "down_pct": down, "overhang_pct": over,
                "support_index": round(down + 0.35 * over, 2),
            })
    cands.sort(key=lambda x: x["support_index"])
    return cands[:10]


def main() -> None:
    stride = 1
    if "--stride" in sys.argv:
        stride = int(sys.argv[sys.argv.index("--stride") + 1])
    t0 = time.time()
    normals, areas = load_faces(STL, stride)
    print("[1] 解析 STL: %d 面（stride=%d）耗时 %.1fs" % (len(normals), stride, time.time() - t0))

    current = evaluate(normals, areas)
    print("\n=== 当前摆放（+Z 为打印方向）===")
    for _, _, key, label in BANDS:
        b = current["bands"][key]
        print("  %-28s 面积 %7.2f%%  (%.0f mm²)" % (label, b["pct"], b["area_mm2"]))

    best = search_best(normals, areas, step=15)
    print("\n=== 候选朝向（support_index 越小越省支撑）===")
    for c in best[:6]:
        print("  绕 %s 旋转 %3d°  朝下 %.2f%%  悬垂 %.2f%%  index=%.2f" % (
            c["axis"], c["deg"], c["down_pct"], c["overhang_pct"], c["support_index"]))

    out = {
        "source": STL,
        "stride": stride,
        "faces_sampled": len(normals),
        "units_hint": UNITS_HINT,
        "scaling": "1 数值单位 = %.6f mm；面积换算为 (mm)²" % (mm(1.0)),
        "bands_definition": [{"lo": lo, "hi": hi, "key": key, "label": label}
                             for lo, hi, key, label in BANDS],
        "current": current,
        "best_orientations": best,
        "boundary_note": (
            "朝向评估基于面法向与 Z 轴夹角，不等于力学仿真；"
            "内腔朝下面未必真需要支撑。支撑/翘边结论需真人看切片预览确认。"
        ),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("=== FDM 打印朝向评估（重力模拟）· 猫爪笔筒 ===\n")
        f.write("实物高度 %.0f mm；1 数值单位 = %.6f mm\n\n" % (MODEL_HEIGHT_MM, mm(1.0)))
        f.write("当前摆放（+Z 为打印方向）：\n")
        for _, _, key, label in BANDS:
            b = current["bands"][key]
            f.write("  %-28s %7.2f%%  (%.0f mm²)\n" % (label, b["pct"], b["area_mm2"]))
        f.write("\n候选朝向（support_index = 朝下%% + 0.35×悬垂%%）：\n")
        for c in best:
            f.write("  绕 %s 旋转 %3d°  朝下 %.2f%%  悬垂 %.2f%%  index=%.2f\n" % (
                c["axis"], c["deg"], c["down_pct"], c["overhang_pct"], c["support_index"]))
        f.write("\n诚实边界：%s\n" % out["boundary_note"])
    print("\n-> %s\n-> %s" % (OUT_JSON, OUT_TXT))


if __name__ == "__main__":
    main()
