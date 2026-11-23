using System;
using System.Collections.Generic;
using System.Linq;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

/// <summary>特征抑制（删面补洞）与参数驱动几何重建（抑制 → 布尔重新切削）。</summary>
public static class FeatureReconstructionService
{
    public static Brep SuppressFeature(Brep currentBrep, RecognizedFeature? feature, double tolerance = 0.001)
    {
        if (currentBrep == null || feature == null || feature.FaceIndices.Count == 0)
            return currentBrep;

        if (feature.Type == FeatureType.Fillet)
            return Defillet(currentBrep, feature.FaceIndices, tolerance);

        Brep working = currentBrep.DuplicateBrep();

        // 修复隐患1：逆序删除，避免 RemoveAt 后索引错位。
        var valid = feature.FaceIndices
            .Where(i => i >= 0 && i < working.Faces.Count)
            .Distinct().OrderByDescending(i => i).ToList();
        foreach (int idx in valid)
        {
            try { working.Faces.RemoveAt(idx); } catch { }
        }
        working.Compact();
        try { working.Repair(tolerance); } catch { }

        if (!working.IsSolid &&
            (feature.Type == FeatureType.SimpleHole ||
             feature.Type == FeatureType.CounterboreHole ||
             feature.Type == FeatureType.ExtrudeCut))
        {
            try
            {
                Brep? capped = working.CapPlanarHoles(tolerance);
                if (capped != null && capped.IsSolid)
                {
                    capped.MergeCoplanarFaces(tolerance);
                    return capped;
                }
            }
            catch { }
        }
        return working;
    }

    /// <summary>
    /// 圆角抑制还原尖角。Rhino 9 实测策略：
    /// 删掉圆角面后，把剩余支撑平面外扩为完整解析平面，用 Brep.CreateSolid 重新求交缝合。
    /// </summary>
    public static Brep Defillet(Brep brep, List<int> filletFaceIndices, double tolerance)
    {
        Brep result = brep.DuplicateBrep();
        try
        {
            var filletSet = new HashSet<int>(filletFaceIndices.Where(
                i => i >= 0 && i < brep.Faces.Count));
            if (filletSet.Count == 0) return result;

            double extend = brep.GetBoundingBox(true).Diagonal.Length * 0.5 + 10.0;
            var pieces = new List<Brep>();

            for (int i = 0; i < brep.Faces.Count; i++)
            {
                if (filletSet.Contains(i)) continue;
                BrepFace f = brep.Faces[i];
                try
                {
                    if (f.TryGetPlane(out Plane pl, tolerance))
                    {
                        var ps = new PlaneSurface(pl,
                            new Interval(-extend, extend), new Interval(-extend, extend));
                        Brep? b = ps.ToBrep();
                        if (b != null) { pieces.Add(b); continue; }
                    }
                }
                catch { }
                Brep? single = f.DuplicateFace(false);
                if (single != null) pieces.Add(single);
            }

            if (pieces.Count > 0)
            {
                Brep[]? solids = Brep.CreateSolid(pieces, tolerance);
                Brep? best = solids?.FirstOrDefault(s => s != null && s.IsSolid);
                if (best != null)
                {
                    best.MergeCoplanarFaces(tolerance);
                    result = best;
                }
            }
        }
        catch { /* 失败时返回原实体，交由上层报告 */ }
        return result;
    }

    /// <summary>参数驱动重建：先抑制该特征得到「干净基体」，再用新参数重新布尔切削。</summary>
    public static Brep RebuildWithUpdatedParameters(
        Brep currentBrep, RecognizedFeature? feature,
        Dictionary<string, double>? newParams, double tolerance = 0.001)
    {
        if (currentBrep == null || feature == null) return currentBrep;
        if (newParams != null)
            foreach (var kv in newParams) feature.Parameters[kv.Key] = kv.Value;

        Brep baseSolid = SuppressFeature(currentBrep, feature, tolerance);
        if (baseSolid == null || !baseSolid.IsSolid) return currentBrep;

        double margin = tolerance * 20.0;
        Brep? result = null;

        if (feature.Type == FeatureType.SimpleHole || feature.Type == FeatureType.CounterboreHole)
            result = RebuildHole(baseSolid, feature, margin, tolerance);
        else if (feature.Type == FeatureType.ExtrudeCut && feature.ProfileCurve != null)
            result = RebuildPocket(baseSolid, feature, margin, tolerance);

        // 失败时保留原实体，不静默返回「已抑制的干净基体」把特征弄丢。
        return result ?? currentBrep;
    }

    /// <summary>孔重建：工具沿孔轴摆正到覆盖整个基体（通孔）或指定深度（盲孔）。</summary>
    private static Brep? RebuildHole(Brep baseSolid, RecognizedFeature feature,
                                     double margin, double tolerance)
    {
        double radius = feature.Parameters.TryGetValue("Radius", out double r) ? r : 0.0;
        double depth = feature.Parameters.TryGetValue("Depth", out double d) ? d : 0.0;
        if (radius <= 0.0) return null;

        Plane p = feature.ReferencePlane;
        Vector3d axis = p.ZAxis;
        if (!axis.Unitize()) return null;

        GetProjectionRange(baseSolid, axis, out double aMin, out double aMax);
        double cut = feature.IsThrough ? (aMax - aMin) : Math.Max(depth, 0.0);
        double height = cut + margin * 2.0;
        double targetMin = feature.IsThrough ? aMin - margin : aMax - cut - margin;

        try
        {
            var cyl = new Cylinder(new Circle(new Plane(p.Origin, axis), radius), height);
            Brep tool = cyl.ToBrep(true, true);
            AlignTool(tool, axis, targetMin);
            Brep[]? diff = Brep.CreateBooleanDifference(baseSolid, tool, tolerance);
            if (diff != null && diff.Length > 0 && diff[0] != null)
            {
                diff[0].MergeCoplanarFaces(tolerance);
                return diff[0];
            }
        }
        catch { }
        return null;
    }

    /// <summary>
    /// 槽重建。原实现把轮廓从「底面」抬 depth 再向下挤，结果工具只覆盖
    /// 原底面到槽口之间，切出的深度恒为旧槽深（10→18 失败）。
    /// 正确做法：ReferencePlane 存的是槽口平面，把轮廓抬到槽口，再向下切新深度。
    /// </summary>
    private static Brep? RebuildPocket(Brep baseSolid, RecognizedFeature feature,
                                       double margin, double tolerance)
    {
        double depth = feature.Parameters.TryGetValue("Depth", out double d) ? d : 0.0;
        if (depth <= 0.0) return null;
        Vector3d outDir = feature.ExtrudeDirection;
        if (!outDir.Unitize()) return null;

        try
        {
            Curve c = feature.ProfileCurve!.DuplicateCurve();
            Point3d profileCenter = c.GetBoundingBox(true).Center;
            // 轮廓原本位于旧底面；用槽口点把它抬到开口平面。
            Vector3d lift = feature.ReferencePlane.Origin - profileCenter;
            c.Translate(outDir * Vector3d.Multiply(lift, outDir));

            double h = depth + margin * 2.0;
            Extrusion? ext = Extrusion.Create(c, h, true);
            if (ext == null) return null;
            Brep tool = ext.ToBrep();

            Point3d mouth = feature.ReferencePlane.Origin;
            double mouthProj = Vector3d.Multiply(new Vector3d(mouth.X, mouth.Y, mouth.Z), outDir);
            // 工具沿 outDir 覆盖 [槽口-depth, 槽口+margin]，与挤出方向无关。
            // 底部不再多留 margin：那 0.02 会被识别成真实槽深（18 变 18.02）。
            AlignTool(tool, outDir, mouthProj - depth);

            Brep[]? diff = Brep.CreateBooleanDifference(baseSolid, tool, tolerance);
            if (diff != null && diff.Length > 0 && diff[0] != null)
            {
                diff[0].MergeCoplanarFaces(tolerance);
                return diff[0];
            }
        }
        catch { }
        return null;
    }

    /// <summary>把布尔工具沿轴摆正：令其在 axis 上的最小投影等于 targetMin。
    /// 这样无论 Extrusion.Create / Cylinder 的挤出方向朝哪，工具覆盖范围都确定。</summary>
    private static void AlignTool(Brep tool, Vector3d axis, double targetMin)
    {
        BoundingBox tb = tool.GetBoundingBox(true);
        double tMin = Vector3d.Multiply(new Vector3d(tb.Min.X, tb.Min.Y, tb.Min.Z), axis);
        tool.Translate(axis * (targetMin - tMin));
    }

    /// <summary>实体包围盒 8 个角点在给定轴上的投影范围（比 Diagonal.Length 精确）。</summary>
    private static void GetProjectionRange(Brep brep, Vector3d axis, out double min, out double max)
    {
        BoundingBox bb = brep.GetBoundingBox(true);
        min = double.PositiveInfinity;
        max = double.NegativeInfinity;
        for (int i = 0; i < 8; i++)
        {
            var c = new Point3d(
                (i & 1) == 0 ? bb.Min.X : bb.Max.X,
                (i & 2) == 0 ? bb.Min.Y : bb.Max.Y,
                (i & 4) == 0 ? bb.Min.Z : bb.Max.Z);
            double p = Vector3d.Multiply(new Vector3d(c.X, c.Y, c.Z), axis);
            if (p < min) min = p;
            if (p > max) max = p;
        }
    }
}
