# -*- coding: utf-8 -*-
"""catpaw_fit.py - Feature typing for the cat-paw pen holder STL.

Why this exists
---------------
The previous pass labelled segments #1..#5 as "false positives: local planar
fragments on a sphere". Once the part is identified as a CAT-PAW PEN HOLDER,
that reading is wrong: those five caps are the real paw pads (4 toes + 1 palm).
They are not noise, they are just fitted with the WRONG PRIMITIVE.

So instead of a plane-only verdict, fit every connected patch with BOTH a plane
and a sphere, then classify by which one explains the points better.

Input : stl_chain_result.json  (segments[].vertices)
Output: catpaw_result.json
Env   : Rhino 9 Python (MCP run_python)

Primary sphere fitter is the Rhino kernel (Sphere.FitSphereToPoints); a pure
python algebraic least-squares sphere is always computed as a cross-check and
as a fallback, so the report survives any API signature surprise.
"""
import json
import math
import os
import traceback

import Rhino
import Rhino.Geometry as G

_LOG = []


def say(*args):
    line = " ".join(str(a) for a in args)
    _LOG.append(line)
    print(line)


# exec()-loaded scripts do not receive __file__; fall back to the known folder.
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = r"C:\Users\21251\WorkBuddy\2026-11-21-15-41-26\_tmp\github-release\m2s\python"
_SRC = os.path.join(_HERE, "stl_chain_result.json")
_DST = os.path.join(_HERE, "catpaw_result.json")


def _solve(A, b):
    """Gauss elimination with partial pivoting for a small dense system."""
    n = len(b)
    M = [list(map(float, A[i])) + [float(b[i])] for i in range(n)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(M[r][i]))
        if abs(M[p][i]) < 1e-18:
            return None
        M[i], M[p] = M[p], M[i]
        pv = M[i][i]
        for j in range(i, n + 1):
            M[i][j] /= pv
        for r in range(n):
            if r == i:
                continue
            f = M[r][i]
            if f:
                for j in range(i, n + 1):
                    M[r][j] -= f * M[i][j]
    return [M[i][n] for i in range(n)]


def fit_sphere_algebraic(pts):
    """Least-squares sphere: 2*c.p + w = |p|^2, with w = R^2 - |c|^2."""
    A = [[0.0] * 4 for _ in range(4)]
    b = [0.0] * 4
    for (x, y, z) in pts:
        row = (2.0 * x, 2.0 * y, 2.0 * z, 1.0)
        q = x * x + y * y + z * z
        for i in range(4):
            for j in range(4):
                A[i][j] += row[i] * row[j]
            b[i] += row[i] * q
    s = _solve(A, b)
    if s is None:
        return None
    cx, cy, cz, w = s
    rr = w + cx * cx + cy * cy + cz * cz
    if rr <= 0:
        return None
    return (cx, cy, cz, math.sqrt(rr))


def rms_sphere(pts, c, r):
    ds = [math.sqrt((p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 +
                    (p[2] - c[2]) ** 2) - r for p in pts]
    return (math.sqrt(sum(d * d for d in ds) / len(ds)),
            max(abs(d) for d in ds))


def rms_plane(pts, origin, normal):
    ds = [abs((p[0] - origin[0]) * normal[0] +
              (p[1] - origin[1]) * normal[1] +
              (p[2] - origin[2]) * normal[2]) for p in pts]
    return (math.sqrt(sum(d * d for d in ds) / len(ds)),
            max(abs(d) for d in ds))


def bbox_of(pts):
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi, [hi[i] - lo[i] for i in range(3)]


def main():
    R = json.load(open(_SRC, encoding="utf-8"))
    segs = R["segments"]
    axis = R["side"]["kasa"]
    say("Rhino %s" % Rhino.RhinoApp.Version)
    say("cylinder axis cx=%.4f cy=%.4f r=%.4f  (Kasa 2D fit, %d pts)" %
          (axis["cx"], axis["cy"], axis["r"], axis["n"]))
    say("")
    hdr = "%-4s %7s %9s %11s %11s %8s %9s %-7s" % (
        "id", "faces", "area", "planeRMS", "sphRMS", "ratio", "radius", "type")
    say(hdr)
    say("-" * len(hdr))

    out = []
    for s in segs:
        pts = [tuple(map(float, v)) for v in s["vertices"]]
        lo, hi, dim = bbox_of(pts)
        p_rms, p_max = rms_plane(pts, s["origin"], s["normal"])

        alg = fit_sphere_algebraic(pts)
        a_rms = a_max = None
        radius = None
        if alg:
            a_rms, a_max = rms_sphere(pts, alg[:3], alg[3])
            radius = alg[3]

        # Rhino kernel sphere fit - signature is (result, Sphere) like Plane's
        rh = None
        try:
            ps = [G.Point3d(p[0], p[1], p[2]) for p in pts]
            raw = G.Sphere.FitSphereToPoints(ps)
            if isinstance(raw, tuple):
                res = raw[0]
                sph = raw[1] if len(raw) > 1 else None
            else:
                res, sph = None, raw
            if sph is not None and hasattr(sph, "Radius"):
                rh = {"center": [sph.Center.X, sph.Center.Y, sph.Center.Z],
                      "radius": sph.Radius, "result": str(res)}
        except Exception as e:
            rh = {"error": repr(e)}

        s_rms = a_rms if a_rms is not None else float("inf")
        ratio = p_rms / max(s_rms, 1e-12)
        # A genuine spherical cap: sphere clearly better AND radius finite
        # relative to patch size (a coplanar patch yields a near-infinite R).
        is_sphere = (ratio > 2.0 and radius is not None
                     and radius < 20 * max(dim))
        stype = "SPHERE" if is_sphere else "PLANE"
        say("%-4s %7d %9.5f %11.6f %11.6f %8.2f %9s %-7s" % (
            s["id"], s["faces"], s["area"], p_rms,
            s_rms if s_rms != float("inf") else -1.0, ratio,
            ("%.4f" % radius) if radius else "n/a", stype))

        out.append({
            "id": s["id"], "faces": s["faces"], "area": s["area"],
            "bbox_min": lo, "bbox_max": hi, "dims": dim,
            "normal": s["normal"],
            "plane_rms": p_rms, "plane_max": p_max,
            "sphere_rms": s_rms, "sphere_max": a_max,
            "sphere_center": list(alg[:3]) if alg else None,
            "sphere_radius": radius,
            "ratio_plane_over_sphere": ratio,
            "type": stype,
            "area_over_bbox_xy": s["area"] / max(1e-12, dim[0] * dim[1]),
            "rhino_sphere": rh,
        })

    say("")
    say("--- SPHERE candidates: centre layout relative to cylinder axis ---")
    for r in out:
        if r["type"] != "SPHERE" or not r["sphere_center"]:
            continue
        c = r["sphere_center"]
        dx, dy = c[0] - axis["cx"], c[1] - axis["cy"]
        say("  id=%-2s R=%.4f centre=(%7.3f,%7.3f,%7.3f) "
              "radial=%6.3f angle=%7.1f deg  z=[%.3f,%.3f]" % (
                  r["id"], r["sphere_radius"], c[0], c[1], c[2],
                  math.hypot(dx, dy), math.degrees(math.atan2(dy, dx)),
                  r["bbox_min"][2], r["bbox_max"][2]))

    say("")
    say("--- Rhino kernel sphere cross-check (radius) ---")
    for r in out:
        rh = r["rhino_sphere"] or {}
        say("  id=%-2s type=%-6s algR=%s rhinoR=%s result=%s" % (
            r["id"], r["type"],
            ("%.4f" % r["sphere_radius"]) if r["sphere_radius"] else "n/a",
            ("%.4f" % rh["radius"]) if "radius" in rh else "n/a",
            rh.get("result", rh.get("error", ""))))

    json.dump({"source": _SRC, "axis": axis, "segments": out},
              open(_DST, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    say("")
    say("-> " + _DST)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _LOG.append(traceback.format_exc())
        traceback.print_exc()
    finally:
        try:
            with open(os.path.join(_HERE, "catpaw_report.txt"), "w",
                      encoding="utf-8") as f:
                f.write("\n".join(_LOG) + "\n")
        except Exception:
            pass
