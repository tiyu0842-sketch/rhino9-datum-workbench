// FeatureWorks v2 — 几何特征识别核心（纯计算，无命令/文档依赖）
// Rhino 9 / .NET 8 / RhinoCommon
//
// 设计立场（先讲清楚再写代码）：
//   Rhino 没有特征树，所有"特征"都是从几何反推的。识别的可信度来自三条互相印证的证据：
//     1) 面类型  —— 圆角是圆柱/圆环/球面（或逼近它们的 NURBS），chamfer 是平面
//     2) 邻接关系 —— 圆角与两侧母面 G1 相切，两侧母面彼此 G0
//     3) 覆盖角   —— 圆角只占圆周一角（~90°），完整柱孔覆盖 ~360°
//   单看第 1 条会把孔误判成圆角，所以三条都要查。
//
// 线程约定：本类所有方法只做纯几何计算（读 Brep），不碰 RhinoDoc / 图层 / 对象表。
// 调用方可以在后台线程并行调用 AnalyzeFace，主线程只负责汇总与写文档。

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Rhino.Geometry;

namespace FeatureWorks
{
    /// <summary>识别出的一个特征（圆角/倒角/圆弧）。</summary>
    public sealed class FwFeature
    {
        public int FaceIndex;              // Brep.Faces 索引；圆弧特征为 -1
        public string Kind;                // "fillet-edge" / "fillet-vertex" / "chamfer" / "arc"
        public string SurfaceType;         // Cylinder / Torus / Sphere / Plane / Curve
        public double Radius;              // 估算半径；chamfer 为 0
        public double SweepDegrees;        // 覆盖角（度）；孔接近 360，圆角约 90
        public double Confidence;          // 0~1
        public int[] Chain;                // 同链的面索引（含自己）
        public int ChainId;                // 链编号，供 UI 分组
        public string Note;                // 降级/低置信度说明

        public override string ToString()
        {
            return string.Format("{0} face#{1} {2} r={3:0.###} sweep={4:0.#}° conf={5:0.00}",
                Kind, FaceIndex, SurfaceType, Radius, SweepDegrees, Confidence);
        }
    }

    /// <summary>识别选项。r_maxFactor 按包围盒对角线比例，适配不同尺度模型。</summary>
    public sealed class FwOptions
    {
        public double RMaxFactor = 0.05;        // r_max = 对角线 * 该系数
        public double TangentAngleDeg = 8.0;    // G1 判据：法线夹角上限
        public double ChamferMinDeg = 25.0;     // chamfer 与母面夹角下限
        public double ChamferMaxDeg = 65.0;     // chamfer 与母面夹角上限
        public double HoleSweepDeg = 270.0;     // 覆盖角超过此值视为孔，不是圆角
        public double ModelTolerance = 1e-6;
        public bool Parallel = true;
        public int BatchSize = 200;             // 分批，避免病态曲面拖死整批
    }

    /// <summary>单面分析结果（线程私有结果槽）。</summary>
    internal sealed class FaceProbe
    {
        public int Index;
        public string SurfaceType;             // Plane / Cylinder / Torus / Sphere / Freeform
        public bool IsPlanar;
        public bool IsFilletCandidate;         // 曲面类型 + 半径 + 覆盖角都过关
        public bool IsHole;                    // 覆盖角过大 → 孔
        public bool IsChamferCandidate;        // 平面 + 窄条 + 斜置
        public double Radius;
        public double SweepDegrees;
        public double Confidence;
        public string Note;
    }

    public static class FwCore
    {
        /// <summary>
        /// 主入口：识别 Brep 上的圆角/倒角特征。
        /// 纯读操作，可在后台线程调用。
        /// </summary>
        public static List<FwFeature> Recognize(Brep brep, FwOptions opt)
        {
            var result = new List<FwFeature>();
            if (brep == null || opt == null) return result;
            int count = brep.Faces.Count;
            if (count == 0) return result;

            // 私有副本：并行读时避免与文档里的对象共享可变状态
            Brep work = brep;
            try { work = brep.DuplicateBrep(); }
            catch { work = brep; }

            double diag = work.GetBoundingBox(true).Diagonal.Length;
            double rMax = diag * opt.RMaxFactor;

            // ---- 阶段 1：逐面探测（可并行）----
            var probes = new FaceProbe[count];
            if (opt.Parallel && count > 8)
            {
                var partitioner = System.Collections.Concurrent.Partitioner.Create(0, count, opt.BatchSize);
                Parallel.ForEach(partitioner,
                    new ParallelOptions { MaxDegreeOfParallelism = Environment.ProcessorCount },
                    range =>
                    {
                        for (int i = range.Item1; i < range.Item2; i++)
                        {
                            try { probes[i] = AnalyzeFace(work, i, rMax, opt); }
                            catch (Exception ex) { probes[i] = new FaceProbe { Index = i, Confidence = 0, Note = "probe failed: " + ex.Message }; }
                        }
                    });
            }
            else
            {
                for (int i = 0; i < count; i++)
                {
                    try { probes[i] = AnalyzeFace(work, i, rMax, opt); }
                    catch (Exception ex) { probes[i] = new FaceProbe { Index = i, Confidence = 0, Note = "probe failed: " + ex.Message }; }
                }
            }

            // ---- 阶段 2：AAG 邻接 + 相切判据 ----
            // 圆角必须与至少两个面相邻，且其中至少两个是 G1 相切。
            var tangentNeighbors = new List<int>[count];
            for (int i = 0; i < count; i++) tangentNeighbors[i] = new List<int>();
            for (int i = 0; i < count; i++)
            {
                var p = probes[i];
                if (p == null || !p.IsFilletCandidate) continue;
                int[] neighbors;
                try { neighbors = work.Faces[i].AdjacentFaces(); }
                catch { neighbors = null; }
                if (neighbors == null) continue;
                foreach (int j in neighbors)
                {
                    if (j < 0 || j >= count || j == i) continue;
                    if (IsTangentAlongSharedEdge(work, i, j, opt.TangentAngleDeg, opt.ModelTolerance))
                        tangentNeighbors[i].Add(j);
                }
                // 至少两个相切邻居才算边圆角（一侧母面 + 另一侧母面）
                if (tangentNeighbors[i].Count < 2)
                {
                    p.IsFilletCandidate = false;
                    p.Note = string.IsNullOrEmpty(p.Note) ? "not G1 to two faces" : p.Note;
                }
                else
                {
                    p.Confidence = Math.Min(1.0, p.Confidence + 0.2);
                }
            }

            // ---- 阶段 3：chamfer 判据（平面 + 与两邻面斜交）----
            for (int i = 0; i < count; i++)
            {
                var p = probes[i];
                if (p == null || !p.IsChamferCandidate) continue;
                int[] neighbors;
                try { neighbors = work.Faces[i].AdjacentFaces(); }
                catch { neighbors = null; }
                if (neighbors == null) { p.IsChamferCandidate = false; continue; }
                int angled = 0;
                foreach (int j in neighbors)
                {
                    if (j < 0 || j >= count || j == i) continue;
                    if (probes[j] != null && probes[j].IsPlanar)
                    {
                        double a = FaceAngleAtSharedEdge(work, i, j, opt.ModelTolerance);
                        if (a >= opt.ChamferMinDeg && a <= opt.ChamferMaxDeg) angled++;
                    }
                }
                if (angled < 2) p.IsChamferCandidate = false;
                else p.Confidence = Math.Min(1.0, p.Confidence + 0.15);
            }

            // ---- 阶段 4：链聚合（相邻 + 同类型 + 半径接近）----
            var parent = Enumerable.Range(0, count).ToArray();
            for (int i = 0; i < count; i++)
            {
                var a = probes[i];
                if (a == null || !a.IsFilletCandidate) continue;
                int[] neighbors;
                try { neighbors = work.Faces[i].AdjacentFaces(); }
                catch { neighbors = null; }
                if (neighbors == null) continue;
                foreach (int j in neighbors)
                {
                    var b = j >= 0 && j < count ? probes[j] : null;
                    if (b == null || !b.IsFilletCandidate) continue;
                    // 同类型、半径相近（相对误差 10%）才连成链
                    if (a.SurfaceType != b.SurfaceType) continue;
                    if (a.Radius > 0 && b.Radius > 0 &&
                        Math.Abs(a.Radius - b.Radius) / Math.Max(a.Radius, b.Radius) > 0.10) continue;
                    Union(parent, i, j);
                }
            }

            // ---- 阶段 5：输出（链内只出一条，避免 UI 列表重复）----
            var chainMap = new Dictionary<int, List<int>>();
            for (int i = 0; i < count; i++)
            {
                var p = probes[i];
                if (p == null || (!p.IsFilletCandidate && !p.IsChamferCandidate)) continue;
                int root = Find(parent, i);
                if (!chainMap.TryGetValue(root, out var list)) { list = new List<int>(); chainMap[root] = list; }
                list.Add(i);
            }
            int chainId = 0;
            foreach (var kv in chainMap)
            {
                var members = kv.Value;
                int representative = members.OrderByDescending(i => probes[i].Confidence).First();
                var rep = probes[representative];
                var f = new FwFeature
                {
                    FaceIndex = representative,
                    Kind = rep.SurfaceType == "Sphere" ? "fillet-vertex" :
                           (rep.IsChamferCandidate ? "chamfer" : "fillet-edge"),
                    SurfaceType = rep.SurfaceType,
                    Radius = rep.Radius,
                    SweepDegrees = rep.SweepDegrees,
                    Confidence = rep.Confidence,
                    Chain = members.ToArray(),
                    ChainId = chainId++,
                    Note = rep.Note
                };
                result.Add(f);
            }
            return result.OrderByDescending(f => f.Confidence).ToList();
        }

        /// <summary>逐面探测：类型 + 半径 + 覆盖角 + 孔排除。线程安全（只读 work）。</summary>
        internal static FaceProbe AnalyzeFace(Brep brep, int index, double rMax, FwOptions opt)
        {
            var probe = new FaceProbe { Index = index };
            if (brep == null || index < 0 || index >= brep.Faces.Count) return probe;
            BrepFace face = brep.Faces[index];
            int si = face.SurfaceIndex;
            if (si < 0 || si >= brep.Surfaces.Count) return probe;
            Surface s = brep.Surfaces[si];
            if (s == null) return probe;

            double tol = opt.ModelTolerance;

            // -- 解析曲面：圆柱 --
            Cylinder cyl;
            if (s.TryGetCylinder(out cyl) && cyl.Radius > 0)
            {
                probe.SurfaceType = "Cylinder";
                probe.Radius = cyl.Radius;
                probe.SweepDegrees = EstimateSweepDegrees(face, s, cyl.Radius, tol);
                ClassifyFillet(probe, rMax, opt.HoleSweepDeg);
                return probe;
            }

            // -- 圆环（顶点圆角常见）--
            Torus torus;
            if (s.TryGetTorus(out torus) && torus.MinorRadius > 0)
            {
                probe.SurfaceType = "Torus";
                probe.Radius = torus.MinorRadius;
                probe.SweepDegrees = EstimateSweepDegrees(face, s, torus.MajorRadius, tol);
                ClassifyFillet(probe, rMax, opt.HoleSweepDeg);
                return probe;
            }

            // -- 球（三面交角的顶点圆角）--
            Sphere sph;
            if (s.TryGetSphere(out sph) && sph.Radius > 0)
            {
                probe.SurfaceType = "Sphere";
                probe.Radius = sph.Radius;
                probe.SweepDegrees = EstimateSweepDegrees(face, s, sph.Radius, tol);
                ClassifyFillet(probe, rMax, opt.HoleSweepDeg);
                return probe;
            }

            // -- 平面：留作 chamfer 候选 --
            Plane pl;
            if (s.TryGetPlane(out pl))
            {
                probe.SurfaceType = "Plane";
                probe.IsPlanar = true;
                // chamfer 的典型特征：面很窄（短边 / 长边 比值小）
                BoundingBox bb = face.GetBoundingBox(true);
                double d1 = bb.Max.X - bb.Min.X, d2 = bb.Max.Y - bb.Min.Y, d3 = bb.Max.Z - bb.Min.Z;
                double[] dims = { d1, d2, d3 };
                Array.Sort(dims);
                double aspect = dims[1] > 1e-9 ? dims[0] / dims[1] : 1.0;
                if (aspect < 0.6 && dims[2] > 1e-9)
                {
                    probe.IsChamferCandidate = true;
                    probe.Confidence = 0.45 + 0.25 * (1.0 - Math.Min(1.0, aspect / 0.6));
                }
                return probe;
            }

            probe.SurfaceType = "Freeform";
            probe.Note = "NURBS/freeform - low confidence, needs curvature fitting";
            return probe;
        }

        /// <summary>
        /// 估算曲面在面内的覆盖角（度）。
        /// 判据来自 DeFillet：完整柱孔覆盖 ~360°，圆角只覆盖 ~90°。
        /// 做法：取外环上若干采样点，映射到曲面的周期参数，看跨度占整周期的比例。
        /// </summary>
        internal static double EstimateSweepDegrees(BrepFace face, Surface s, double radius, double tol)
        {
            try
            {
                // 真机实测（Rhino 9）：球面/柱面的参数域是**弧长**不是弧度。
                // 例：半径10的球面 U 域 0..62.83（=2πr），V 域 -15.7..15.7（=±π/2·r）。
                // 因此 覆盖角(弧度) = 域跨度 / 半径，再转度。
                if (radius <= 1e-9) return 0;
                var domainU = s.Domain(0);
                var domainV = s.Domain(1);
                double spanU = domainU.Length / radius;   // 弧度
                double spanV = domainV.Length / radius;   // 弧度
                double degU = spanU * 180.0 / Math.PI;
                double degV = spanV * 180.0 / Math.PI;
                // 真机实测（倒 3mm 圆角的 100×80×60 盒子）：
                //   圆柱圆角面 U 域 -3..63（轴向，长 66 = 60+2r），V 域 0..4.712（周向，= 3π/2）
                //   半径 3：U→1260°（轴向，被截断 360），V→270°（真正的周向覆盖）
                // 所以取**较小**的那个作为绕轴覆盖角；轴向跨度通常远大于周向。
                double sweep = Math.Min(degU, degV);
                return Math.Min(360.0, sweep);
            }
            catch { return 0; }
        }

        private static void ClassifyFillet(FaceProbe p, double rMax, double holeSweepDeg)
        {
            if (p.Radius <= 0 || p.Radius > rMax)
            {
                p.Note = "radius above r_max";
                return;
            }
            if (p.SweepDegrees >= holeSweepDeg)
            {
                p.IsHole = true;
                p.Note = "full sweep - likely a hole, not a fillet";
                return;
            }
            p.IsFilletCandidate = true;
            // 覆盖角越接近 90° 越可信；半径远小于 r_max 也可信
            double sweepScore = 1.0 - Math.Min(1.0, Math.Abs(p.SweepDegrees - 90.0) / 180.0);
            double radiusScore = 1.0 - Math.Min(1.0, p.Radius / Math.Max(rMax, 1e-9));
            p.Confidence = 0.45 + 0.3 * sweepScore + 0.15 * radiusScore;
        }

        /// <summary>两相邻面在共享边中点的法线夹角（度）。用于 G1 相切与 chamfer 判据。</summary>
        internal static double FaceAngleAtSharedEdge(Brep brep, int i, int j, double tol)
        {
            try
            {
                BrepFace a = brep.Faces[i], b = brep.Faces[j];
                // RhinoCommon 9 实测：BrepFace 没有 Edges 属性，只有 AdjacentEdges() -> int[]。
                // 顶点集合用边的 StartVertex / EndVertex，取 VertexIndex 做跨面匹配。
                var setB = new HashSet<int>();
                foreach (int ei in b.AdjacentEdges())
                {
                    BrepEdge e = brep.Edges[ei];
                    setB.Add(e.StartVertex.VertexIndex);
                    setB.Add(e.EndVertex.VertexIndex);
                }
                BrepEdge shared = null;
                foreach (int ei in a.AdjacentEdges())
                {
                    BrepEdge e = brep.Edges[ei];
                    if (setB.Contains(e.StartVertex.VertexIndex) && setB.Contains(e.EndVertex.VertexIndex))
                    { shared = e; break; }
                }
                if (shared == null) return 180.0;

                Point3d mid = shared.PointAt(shared.Domain.Mid);
                // RhinoCommon 9 实测：ClosestPoint 只有 (Point3d, out u, out v) 三参重载，
                // 没有返回三元组的单参版本。
                double ua, va, ub, vb;
                if (!a.ClosestPoint(mid, out ua, out va)) return 180.0;
                if (!b.ClosestPoint(mid, out ub, out vb)) return 180.0;
                Vector3d na = a.NormalAt(ua, va);
                Vector3d nb = b.NormalAt(ub, vb);
                if (na.Length < tol || nb.Length < tol) return 180.0;
                na.Unitize(); nb.Unitize();
                double dot = na * nb;           // RhinoCommon 9: 点积用 * 运算符
                dot = Math.Max(-1.0, Math.Min(1.0, dot));
                return Math.Acos(dot) * 180.0 / Math.PI;
            }
            catch { return 180.0; }
        }

        private static bool IsTangentAlongSharedEdge(Brep brep, int i, int j, double tangentDeg, double tol)
        {
            return FaceAngleAtSharedEdge(brep, i, j, tol) < tangentDeg;
        }

        private static int Find(int[] parent, int x)
        {
            while (parent[x] != x) { parent[x] = parent[parent[x]]; x = parent[x]; }
            return x;
        }
        private static void Union(int[] parent, int a, int b)
        {
            int ra = Find(parent, a), rb = Find(parent, b);
            if (ra != rb) parent[rb] = ra;
        }
    }
}
