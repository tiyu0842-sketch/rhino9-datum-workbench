using System;
using System.Collections.Generic;
using System.Linq;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

/// <summary>
/// 一个面的「原生/修剪」证据。Rhino 的 B-rep 面 = 完整底层曲面 + trim 环。
/// 布尔减 / 打孔 / 倒角只改 trim，不动底层曲面——所以比较 domain 与 trim
/// 边界，就能反推这个面被做过什么操作。
/// </summary>
public class FaceEvidence
{
    public int FaceIndex { get; set; }
    public string UnderlyingType { get; set; } = "";
    public int LoopCount { get; set; }
    public int TrimCount { get; set; }
    public double DomainSpanZ { get; set; }
    public double TrimSpanZ { get; set; }
    /// <summary>底层曲面相对 trim 在 Z 向多出的跨度 = 布尔工具余量 / 倒角削减量。</summary>
    public double OverhangZ => Math.Max(0.0, DomainSpanZ - TrimSpanZ);
    public int NurbsRows { get; set; }
    public int NurbsCols { get; set; }
    public int DegreeU { get; set; }
    public int DegreeV { get; set; }
    public bool IsInnerFace { get; set; }
    public string OperationHint { get; set; } = "";

    public string OneLine() => string.Format(
        "F{0,-2} {1,-14} loops={2} trims={3,-2} overhangZ={4,6:0.00} rev={5,-5} hint={6}",
        FaceIndex, UnderlyingType, LoopCount, TrimCount, OverhangZ,
        IsInnerFace, OperationHint);
}

/// <summary>整件实体的加工史推断结果。</summary>
public class SurfaceEvidenceReport
{
    public List<FaceEvidence> Faces { get; } = new();
    public int InnerLoopFaces { get; set; }
    public int OverhangFaces { get; set; }
    public int ReversedFaces { get; set; }
    public double MaxOverhangZ { get; set; }
    public List<string> Conclusions { get; } = new();

    public string Render()
    {
        var lines = new List<string>
        {
            "=== 曲面原生/修剪证据 / Surface evidence ===",
            string.Format("faces={0} innerLoops={1} overhang={2} maxOverhangZ={3:0.####} reversed={4}",
                Faces.Count, InnerLoopFaces, OverhangFaces, MaxOverhangZ, ReversedFaces),
        };
        lines.AddRange(Faces.Select(f => "  " + f.OneLine()));
        if (Conclusions.Count > 0)
        {
            lines.Add("  --- 加工史推断 / inferred operations ---");
            lines.AddRange(Conclusions.Select(c => "  * " + c));
        }
        return string.Join(Environment.NewLine, lines);
    }
}

/// <summary>
/// 曲面证据分析 + untrim 驱动的整体修复。
/// 实测（Rhino 9）关键事实：
///  - UnderlyingSurface().ToBrep() 对平面/解析面/自由曲面都能取回原生完整曲面；
///  - 删掉特征面后，只用剩余外表面的底层曲面 CreateSolid 可缝合回毛坯
///    （100x80x30 带槽块 → 6 面实体 240000，与原始 box 体积一致）；
///  - 带着 trim 直接 CreateSolid 会因槽口留洞而失败——恢复原生曲面是必需步骤。
/// </summary>
public static class SurfaceEvidenceService
{
    private const double OverhangThreshold = 0.5;

    /// <summary>逐面采集原生/修剪证据，并推断加工史。</summary>
    public static SurfaceEvidenceReport Analyze(Brep brep, double tolerance = 0.001)
    {
        var rep = new SurfaceEvidenceReport();
        if (brep == null) return rep;

        for (int i = 0; i < brep.Faces.Count; i++)
        {
            BrepFace face = brep.Faces[i];
            var ev = new FaceEvidence { FaceIndex = i, IsInnerFace = face.OrientationIsReversed };
            try
            {
                Surface s = face.UnderlyingSurface();
                ev.UnderlyingType = s.GetType().Name;
                Interval du = s.Domain(0), dv = s.Domain(1);
                var corners = new[]
                {
                    s.PointAt(du.Min, dv.Min), s.PointAt(du.Min, dv.Max),
                    s.PointAt(du.Max, dv.Min), s.PointAt(du.Max, dv.Max)
                };
                ev.DomainSpanZ = corners.Max(p => p.Z) - corners.Min(p => p.Z);

                var ns = s.ToNurbsSurface();
                if (ns != null)
                {
                    ev.NurbsRows = ns.Points.CountU;
                    ev.NurbsCols = ns.Points.CountV;
                    // RhinoCommon 里是 OrderU/OrderV（阶数 = Order - 1），不是 DegreeU/DegreeV。
                    ev.DegreeU = ns.OrderU - 1;
                    ev.DegreeV = ns.OrderV - 1;
                }
            }
            catch { ev.UnderlyingType = ev.UnderlyingType.Length == 0 ? "?" : ev.UnderlyingType; }

            try
            {
                ev.LoopCount = face.Loops.Count;
                ev.TrimCount = face.Loops.Sum(l => l.Trims.Count);
            }
            catch { }

            try
            {
                var zs = new List<double>();
                foreach (BrepEdge edge in brep.Edges)
                {
                    int[] adj = edge.AdjacentFaces();
                    if (adj == null || !adj.Contains(i)) continue;
                    zs.Add(edge.PointAtStart.Z);
                    zs.Add(edge.PointAtEnd.Z);
                }
                if (zs.Count > 0) ev.TrimSpanZ = zs.Max() - zs.Min();
            }
            catch { }

            if (ev.LoopCount > 1) rep.InnerLoopFaces++;
            if (ev.OverhangZ > OverhangThreshold) rep.OverhangFaces++;
            if (ev.IsInnerFace) rep.ReversedFaces++;
            rep.MaxOverhangZ = Math.Max(rep.MaxOverhangZ, ev.OverhangZ);

            // 加工史推断：把几何信号翻译成人话。
            var hints = new List<string>();
            if (ev.LoopCount > 1) hints.Add("孔/槽开口(inner loop)");
            if (ev.OverhangZ > OverhangThreshold) hints.Add("布尔/倒角修剪(trimmed)");
            if (ev.IsInnerFace && ev.OverhangZ <= OverhangThreshold) hints.Add("特征内壁(feature wall)");
            ev.OperationHint = string.Join("+", hints);
            rep.Faces.Add(ev);
        }

        if (rep.InnerLoopFaces > 0)
            rep.Conclusions.Add("发现 " + rep.InnerLoopFaces + " 个带内环的面 → 有孔或槽切入外表面");
        if (rep.OverhangFaces > 0)
            rep.Conclusions.Add(string.Format("{0} 个面的底层曲面比 trim 长最多 {1:0.##} → 布尔工具有余量/倒角削过 trim",
                rep.OverhangFaces, rep.MaxOverhangZ));
        if (rep.ReversedFaces > 0)
            rep.Conclusions.Add(rep.ReversedFaces + " 个反向面 → 布尔减产生的内表面");
        if (rep.Conclusions.Count == 0)
            rep.Conclusions.Add("未见明显加工痕迹，可能已是毛坯或未修剪的原生曲面");
        return rep;
    }

    /// <summary>
    /// 整体修复：删掉给定特征面，剩余面取底层原生曲面，CreateSolid 重新缝合还原毛坯。
    /// 实测 100x80x30 带槽块（删 5 内面 + 6 外面原生曲面）→ 单一实体 240000。
    /// </summary>
    public static Brep? RepairToBlank(Brep brep, IEnumerable<int> featureFaceIndices,
                                      double tolerance = 0.001)
    {
        if (brep == null) return null;
        var drop = new HashSet<int>(featureFaceIndices.Where(
            i => i >= 0 && i < brep.Faces.Count));
        if (drop.Count == 0) return brep.DuplicateBrep();

        var pieces = new List<Brep>();
        for (int i = 0; i < brep.Faces.Count; i++)
        {
            if (drop.Contains(i)) continue;
            BrepFace face = brep.Faces[i];
            // 关键：取底层完整曲面而不是带 trim 的面，否则槽口留洞无法缝合。
            try
            {
                Surface s = face.UnderlyingSurface();
                Brep? native = s.ToBrep();
                if (native != null && native.Faces.Count > 0)
                {
                    pieces.Add(native);
                    continue;
                }
            }
            catch { }
            try
            {
                Brep? fallback = face.DuplicateFace(false);
                if (fallback != null) pieces.Add(fallback);
            }
            catch { }
        }

        if (pieces.Count < 2) return null;
        try
        {
            Brep[]? solids = Brep.CreateSolid(pieces, tolerance);
            if (solids == null) return null;
            // 选体积最大且为实体的结果——通常就是还原的毛坯。
            Brep? best = null;
            double bestVol = double.NegativeInfinity;
            foreach (Brep s in solids)
            {
                if (s == null || !s.IsSolid) continue;
                double v = 0.0;
                try { v = VolumeMassProperties.Compute(s)?.Volume ?? 0.0; } catch { }
                if (v > bestVol) { bestVol = v; best = s; }
            }
            if (best != null)
            {
                best.MergeCoplanarFaces(tolerance);
                return best;
            }
        }
        catch { }
        return null;
    }

    /// <summary>一键整体修复：删掉所有识别出的特征面，还原毛坯；失败时回退原实体。</summary>
    public static Brep RepairAll(Brep brep, List<RecognizedFeature> features, double tolerance = 0.001)
    {
        if (brep == null || features == null || features.Count == 0) return brep;
        var all = new HashSet<int>();
        foreach (RecognizedFeature f in features)
            foreach (int idx in f.FaceIndices)
                all.Add(idx);
        return RepairToBlank(brep, all, tolerance) ?? brep;
    }
}
