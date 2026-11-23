using System;
using System.Collections.Generic;
using System.Linq;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

/// <summary>
/// 多阶段「洋葱剥皮」识别引擎：按特征形成的逆序消耗面节点。
/// Pass 1 圆角链（修饰） → Pass 2 复合孔（局部负） → Pass 3 拉伸切除（主负）。
/// </summary>
public class FeatureRecognitionEngine
{
    public double LastTolerance { get; private set; } = 0.001;
    public int LastFaceCount { get; private set; }
    public Dictionary<string, int> Diagnostics { get; } = new();

    public (Brep CleanBrep, List<RecognizedFeature> Features) RecognizeAll(Brep inputBrep, double tolerance = 0.001)
    {
        LastTolerance = tolerance;
        var afag = new AttributedFaceAdjacencyGraph();
        afag.Build(inputBrep, tolerance);
        LastFaceCount = afag.WorkingBrep.Faces.Count;

        var features = new List<RecognizedFeature>();
        var consumed = new HashSet<int>();

        var fillets = RecognizeFilletChains(afag, consumed);
        var holes = RecognizeHoles(afag, consumed);
        var cuts = RecognizeExtrudeCuts(afag, consumed);

        Diagnostics["Pass1_Fillets"] = fillets.Count;
        Diagnostics["Pass2_Holes"] = holes.Count;
        Diagnostics["Pass3_Cuts"] = cuts.Count;
        Diagnostics["Faces"] = LastFaceCount;

        features.AddRange(fillets);
        features.AddRange(holes);
        features.AddRange(cuts);

        FeatureTreeStorage.Save(afag.WorkingBrep, features);
        return (afag.WorkingBrep, features);
    }

    // ---- Pass 1：圆角链 ------------------------------------------------
    private List<RecognizedFeature> RecognizeFilletChains(AttributedFaceAdjacencyGraph afag, HashSet<int> consumed)
    {
        var result = new List<RecognizedFeature>();
        var visited = new HashSet<int>();
        int n = 1;

        foreach (var kv in afag.Nodes)
        {
            int start = kv.Key;
            FaceNode node = kv.Value;
            if (consumed.Contains(start) || visited.Contains(start)) continue;
            if (!IsCandidateFilletFace(node)) continue;

            double radius = GetFilletRadius(node);
            var chain = new List<int>();
            var q = new Queue<int>();
            q.Enqueue(start); visited.Add(start);

            while (q.Count > 0)
            {
                int cur = q.Dequeue();
                chain.Add(cur);
                foreach (var e in afag.Nodes[cur].Neighbors)
                {
                    int next = e.NeighborFaceIndex;
                    if (consumed.Contains(next) || visited.Contains(next)) continue;
                    if (!afag.Nodes.ContainsKey(next)) continue;
                    FaceNode nn = afag.Nodes[next];
                    if (e.Convexity == EdgeConvexity.Tangent &&
                        IsCandidateFilletFace(nn) &&
                        Math.Abs(GetFilletRadius(nn) - radius) < afag.Tolerance * 5 + 1e-6)
                    {
                        visited.Add(next);
                        q.Enqueue(next);
                    }
                }
            }

            foreach (int f in chain) consumed.Add(f);
            var feat = new RecognizedFeature
            {
                Type = FeatureType.Fillet,
                Name = "Fillet_" + n++,
                FaceIndices = chain
            };
            feat.Parameters["Radius"] = Math.Round(radius, 4);
            result.Add(feat);
        }
        return result;
    }

    private static bool IsCandidateFilletFace(FaceNode node)
    {
        if (node.Category != SurfaceCategory.Cylinder && node.Category != SurfaceCategory.Torus)
            return false;
        return node.Neighbors.Count(e => e.Convexity == EdgeConvexity.Tangent) >= 2;
    }

    private static double GetFilletRadius(FaceNode node)
    {
        if (node.Category == SurfaceCategory.Cylinder) return node.CylinderData.Radius;
        if (node.Category == SurfaceCategory.Torus) return node.TorusData.MinorRadius;
        return 0.0;
    }

    // ---- Pass 2：复合孔 ------------------------------------------------
    private List<RecognizedFeature> RecognizeHoles(AttributedFaceAdjacencyGraph afag, HashSet<int> consumed)
    {
        var result = new List<RecognizedFeature>();
        var innerCyls = afag.Nodes.Values
            .Where(n => !consumed.Contains(n.Index) &&
                        n.Category == SurfaceCategory.Cylinder && n.IsConcaveSurface)
            .ToList();

        var clustered = new HashSet<int>();
        int n = 1;

        foreach (var seed in innerCyls)
        {
            if (clustered.Contains(seed.Index)) continue;
            var group = new List<FaceNode> { seed };
            clustered.Add(seed.Index);
            var seedAxis = new Line(seed.CylinderData.Center, seed.CylinderData.Center + seed.CylinderData.Axis);

            foreach (var other in innerCyls)
            {
                if (clustered.Contains(other.Index)) continue;
                Vector3d a1 = seed.CylinderData.Axis, a2 = other.CylinderData.Axis;
                bool parallel = a1.IsParallelTo(a2, 0.01) != 0;
                double axisDist = seedAxis.DistanceTo(other.CylinderData.Center, false);
                if (parallel && axisDist < afag.Tolerance * 5 + 1e-6)
                {
                    group.Add(other);
                    clustered.Add(other.Index);
                }
            }

            var faceIds = group.Select(g => g.Index).ToList();
            var radii = group.Select(g => Math.Round(g.CylinderData.Radius, 4))
                             .Distinct().OrderByDescending(r => r).ToList();

            bool isThrough = true;
            foreach (var g in group)
            {
                foreach (var e in g.Neighbors)
                {
                    if (consumed.Contains(e.NeighborFaceIndex)) continue;
                    if (!afag.Nodes.ContainsKey(e.NeighborFaceIndex)) continue;
                    var nn = afag.Nodes[e.NeighborFaceIndex];
                    if (nn.Category == SurfaceCategory.Plane &&
                        e.Convexity == EdgeConvexity.Concave &&
                        nn.PlaneData.Normal.IsParallelTo(seed.CylinderData.Axis, 0.01) != 0 &&
                        nn.Neighbors.All(ne => faceIds.Contains(ne.NeighborFaceIndex)))
                    {
                        if (!faceIds.Contains(nn.Index)) faceIds.Add(nn.Index);
                        isThrough = false;
                    }
                }
            }

            BoundingBox bbox = BoundingBox.Empty;
            foreach (int fid in faceIds)
            {
                consumed.Add(fid);
                bbox.Union(afag.WorkingBrep.Faces[fid].GetBoundingBox(true));
            }

            Vector3d axisDir = seed.CylinderData.Axis;
            axisDir.Unitize();
            double depth = Math.Abs(Vector3d.Multiply(bbox.Diagonal, axisDir));
            var refPlane = new Plane(seed.CylinderData.Center, axisDir);

            var feat = new RecognizedFeature
            {
                Type = radii.Count > 1 ? FeatureType.CounterboreHole : FeatureType.SimpleHole,
                Name = radii.Count > 1 ? "CounterboreHole_" + n++ : "Hole_" + n++,
                FaceIndices = faceIds,
                ReferencePlane = refPlane,
                IsThrough = isThrough
            };
            feat.Parameters["Radius"] = radii.Count > 0 ? radii.Last() : 0.0;
            feat.Parameters["Depth"] = Math.Round(depth, 4);
            if (radii.Count > 1) feat.Parameters["CounterboreRadius"] = radii.First();
            result.Add(feat);
        }
        return result;
    }

    // ---- Pass 3：拉伸切除 ----------------------------------------------
    // Rhino 9 实测修正（两轮）：
    // ① 手册「沿 Concave 边搜索凹连通子图」在这里失效：凹槽内角边 det 全为 +1
    //    被判 Convex（二面角符号对 rev=true 的内表面手性推导不成立）。
    // ② OrientationIsReversed 也不能当判据：用挤出工具重建同一槽后，槽底面
    //    rev 会从 True 翻成 False，凹区连通分量直接丢掉底面 → 槽识别为 0。
    // 最终判据（见 FwGraph.ComputeIsInnerFace）：以「面不在整体 bbox 外轮廓上」
    // 定义凹区内表面，只依赖有效法向与包围盒，不受 rev / trim 手性影响。
    // 深度改用真实 Brep 边端点的投影跨度——面 GetBoundingBox(true) 会带上
    // untrimmed 曲面（实测槽侧壁 bbox 到 z=31，比实体顶面高 1，把 10 算成 11）。
    private List<RecognizedFeature> RecognizeExtrudeCuts(AttributedFaceAdjacencyGraph afag, HashSet<int> consumed)
    {
        var result = new List<RecognizedFeature>();
        var visited = new HashSet<int>();
        int n = 1;

        var innerFaces = new HashSet<int>(afag.Nodes.Values
            .Where(nd => nd.IsInnerFace && !consumed.Contains(nd.Index))
            .Select(nd => nd.Index));

        foreach (var kv in afag.Nodes.OrderBy(k => k.Key))
        {
            int start = kv.Key;
            if (!innerFaces.Contains(start) || visited.Contains(start) || consumed.Contains(start)) continue;

            var component = new List<int>();
            var q = new Queue<int>();
            q.Enqueue(start); visited.Add(start);
            while (q.Count > 0)
            {
                int cur = q.Dequeue();
                component.Add(cur);
                foreach (var e in afag.Nodes[cur].Neighbors)
                {
                    int next = e.NeighborFaceIndex;
                    if (consumed.Contains(next) || visited.Contains(next)) continue;
                    if (!innerFaces.Contains(next)) continue;   // 不跨到外表面（槽口顶面）
                    visited.Add(next);
                    q.Enqueue(next);
                }
            }
            if (component.Count < 2) continue;

            FaceNode? basePlane = null;
            foreach (int fid in component)
            {
                var cand = afag.Nodes[fid];
                if (cand.Category != SurfaceCategory.Plane) continue;
                var walls = component.Where(id => id != fid).Select(id => afag.Nodes[id]).ToList();
                bool allPerp = walls.All(w =>
                {
                    if (w.Category == SurfaceCategory.Plane)
                        return Math.Abs(Vector3d.Multiply(cand.PlaneData.Normal, w.PlaneData.Normal)) < 0.02;
                    if (w.Category == SurfaceCategory.Cylinder)
                        return cand.PlaneData.Normal.IsParallelTo(w.CylinderData.Axis, 0.02) != 0;
                    return false;
                });
                if (allPerp) { basePlane = cand; break; }
            }
            if (basePlane == null) continue;

            foreach (int fid in component) consumed.Add(fid);
            BrepFace baseFace = afag.WorkingBrep.Faces[basePlane.Index];
            Curve? outer = null;
            try { outer = baseFace.OuterLoop.To3dCurve(); } catch { }

            var componentSet = new HashSet<int>(component);

            // 切除方向必须由底面指向侧壁/开口外部
            Vector3d outDir = baseFace.NormalAt(baseFace.Domain(0).Mid, baseFace.Domain(1).Mid);
            var firstWall = component.Where(id => id != basePlane.Index)
                                     .Select(id => afag.Nodes[id]).FirstOrDefault();
            if (firstWall != null)
            {
                Vector3d baseToWall = firstWall.Centroid - basePlane.Centroid;
                if (Vector3d.Multiply(outDir, baseToWall) < 0) outDir = -outDir;
            }
            outDir.Unitize();

            // 深度 = 凹区相关「真实 trim 边端点」沿切除方向的投影跨度。
            // 不能用 GetBoundingBox：它读的是未修剪底层曲面 domain —— 实测槽侧壁
            // surfZ=20..31 而 trim 边只到 30，多出的 1 正是布尔工具的余量，
            // 会把深度 10 算成 11。这也是「检查曲面是否被修剪」最直接的信号。
            double pMin = double.PositiveInfinity, pMax = double.NegativeInfinity;
            foreach (BrepEdge edge in afag.WorkingBrep.Edges)
            {
                int[] adj = edge.AdjacentFaces();
                if (adj == null || adj.Length != 2) continue;
                if (!componentSet.Contains(adj[0]) && !componentSet.Contains(adj[1])) continue;
                foreach (Point3d pt in new[] { edge.PointAtStart, edge.PointAtEnd })
                {
                    double p = Vector3d.Multiply(new Vector3d(pt.X, pt.Y, pt.Z), outDir);
                    if (p < pMin) pMin = p;
                    if (p > pMax) pMax = p;
                }
            }
            double depth = pMax > pMin ? pMax - pMin : 0.0;
            if (depth <= 0.0) continue;

            // ReferencePlane 存「槽口平面」而不是底面：重建时把轮廓抬到开口，
            // 再沿 -outDir 切出新深度，避免工具起点仍钉在旧底面上（原 bug：只切 10）。
            Point3d mouthPoint = basePlane.Centroid + outDir * depth;

            var feat = new RecognizedFeature
            {
                Type = FeatureType.ExtrudeCut,
                Name = "ExtrudeCut_" + n++,
                FaceIndices = component,
                ReferencePlane = new Plane(mouthPoint, outDir),
                ExtrudeDirection = outDir,
                ProfileCurve = outer,
                IsThrough = false
            };
            feat.Parameters["Depth"] = Math.Round(depth, 4);
            result.Add(feat);
        }
        return result;
    }
}
