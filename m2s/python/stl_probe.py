# -*- coding: utf-8 -*-
"""stl_probe.py —— 二进制 STL 体检：规模 / 包围盒 / 法向-面积分布 / 平面度估计。

纯标准库，不经 Rhino。目的：在决定怎么跑拟合之前，先知道这模型长什么样。
"""
import struct
import math
import os
import collections

P = r"D:\浏览器下载\3fc5d89146009bc92124e5f0a9c958b3.stl"
size = os.path.getsize(P)

with open(P, "rb") as f:
    hdr = f.read(80)
    n = struct.unpack("<I", f.read(4))[0]
    print("file      : %s" % P)
    print("size      : %.2f MB" % (size / 1048576.0))
    print("triangles : %d   (expected %.1f MB)" % (n, (84 + n * 50) / 1048576.0))

    mn = [1e30, 1e30, 1e30]
    mx = [-1e30, -1e30, -1e30]
    hist = [0] * 19          # 与 +Z 夹角 0-180°，10° 一档
    hist_area = [0.0] * 19
    area_total = 0.0
    zero_normal = 0
    # 顶点量化去重（按 0.01mm 精度），估计唯一顶点数
    q = collections.Counter()
    CH = 40000
    done = 0
    while True:
        buf = f.read(50 * CH)
        if not buf:
            break
        for o in range(0, len(buf), 50):
            v = struct.unpack_from("<12fH", buf, o)
            nx, ny, nz = v[0], v[1], v[2]
            ax0, ay0, az0 = v[3], v[4], v[5]
            bx0, by0, bz0 = v[6], v[7], v[8]
            cx0, cy0, cz0 = v[9], v[10], v[11]
            for (x, y, z) in ((ax0, ay0, az0), (bx0, by0, bz0), (cx0, cy0, cz0)):
                if x < mn[0]: mn[0] = x
                if y < mn[1]: mn[1] = y
                if z < mn[2]: mn[2] = z
                if x > mx[0]: mx[0] = x
                if y > mx[1]: mx[1] = y
                if z > mx[2]: mx[2] = z
                q[(round(x * 100), round(y * 100), round(z * 100))] += 1
            # 几何法向（比 STL 头里的法向可靠）
            ux, uy, uz = bx0 - ax0, by0 - ay0, bz0 - az0
            vx, vy, vz = cx0 - ax0, cy0 - ay0, cz0 - az0
            gx = uy * vz - uz * vy
            gy = uz * vx - ux * vz
            gz = ux * vy - uy * vx
            L = math.sqrt(gx * gx + gy * gy + gz * gz)
            a = 0.5 * L
            area_total += a
            if L < 1e-12:
                continue
            c = max(-1.0, min(1.0, gz / L))
            ang = math.degrees(math.acos(c))
            b = min(18, int(ang // 10))
            hist[b] += 1
            hist_area[b] += a
            if abs(nx) + abs(ny) + abs(nz) < 1e-9:
                zero_normal += 1
    done = n

print("\nbbox min  : (%.2f, %.2f, %.2f)" % tuple(mn))
print("bbox max  : (%.2f, %.2f, %.2f)" % tuple(mx))
print("dims      : %.2f x %.2f x %.2f" % (mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]))
print("vertices  : ~%d 唯一（0.01 精度去重），均值 %.2f 面/顶点" % (
    len(q), n / max(1, len(q))))
print("复用的顶点占比: %.1f%%" % (
    100.0 * sum(1 for c in q.values() if c > 1) / max(1, len(q))))
print("STL 头法向为零的面: %d" % zero_normal)
print("总面积    : %.1f 平方单位" % area_total)

print("\n--- 与 +Z 夹角 / 面积占比 ---")
cum = 0.0
for i in range(19):
    if hist[i] == 0:
        continue
    ar = 100.0 * hist_area[i] / area_total
    cum += ar
    bar = "#" * int(ar / 2)
    print("  %3d-%3d°  faces=%7d  area=%6.2f%%  cum=%6.2f%%  %s" % (
        i * 10, i * 10 + 10, hist[i], ar, cum, bar))
