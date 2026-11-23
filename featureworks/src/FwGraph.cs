using System;
using System.Collections.Generic;
using System.Linq;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

/// <summary>属性面邻接图中的一个面节点。</summary>
public class FaceNode
{
    public int Index { get; set; }
    public SurfaceCategory Category { get; set; } = SurfaceCategory.Freeform;
    public double Area { get; set; }
    public Point3d Centroid { get; set; }
    public Plane PlaneData { get; set; } = Plane.WorldXY;
    public Cylinder CylinderData { get; set; }
    public Torus TorusData { get; set; }
    public Cone ConeData { get; set; }
    public bool IsConcaveSurface { get; set; }
    /// <summary>Rhino 原始面朝向标记。Rhino 9 实测不稳定：布尔减工具的朝向不同会让
    /// 同一凹区底面的 rev 在 True/False 间翻转，不能直接当作凹区判据。</summary>
    public bool OrientationIsReversed { get; set; }
    /// <summary>凹区内表面：该面不在实体外轮廓（整体 bbox 沿有效法向的极值）上。</summary>
    public bool IsInnerFace { get; set; }
    public List<AdjacencyEdge> Neighbors { get; } = new();
}

public class AdjacencyEdge
{
    public int NeighborFaceIndex { get; set; }
    public int BrepEdgeIndex { get; set; }
    public EdgeConvexity Convexity { get; set; }
    public double EdgeLength { get; set; }
}

/// <summary>
/// Attributed Face Adjacency Graph (AFAG)。Rhino 9 实机验证：
///  - MergeCoplanarFaces(double) 返回 bool，Compact() 返回 void；
///  - AreaMassProperties 没有 Compute(BrepFace) 重载，改用 DuplicateFace(false) 得单面 Brep；
///  - 二面角符号 det = (nA × nB)·dirInA，det&gt;0 判 Convex（实测 plain box 12/12 Convex）；
///  - OrientationIsReversed 不能当凹区判据（重建后 rev 会翻转），改用「外轮廓极值」判据。
/// </summary>
public class AttributedFaceAdjacencyGraph
{
    public Brep WorkingBrep { get; private set; } = null!;
    public Dictionary<int, FaceNode> Nodes { get; } = new();
    public double Tolerance { get; private set; }

    public void Build(Brep inputBrep, double tolerance = 0.001)
    {
        Tolerance = tolerance;
        WorkingBrep = inputBrep.DuplicateBrep();
        WorkingBrep.MergeCoplanarFaces(tolerance);
        WorkingBrep.Compact();
        Nodes.Clear();
        BoundingBox globalBox = WorkingBrep.GetBoundingBox(true);

        foreach (BrepFace face in WorkingBrep.Faces)
        {
            var node = new FaceNode
            {
                Index = face.FaceIndex,
                OrientationIsReversed = face.OrientationIsReversed
            };

            // 面积/质心：用单面 Brep 而不是直接 Compute(face)，Rhino 9 无此重载。
            try
            {
                using (Brep? single = face.DuplicateFace(false))
                {
                    if (single != null)
                    {
                        var amp = AreaMassProperties.Compute(single);
                        if (amp != null) { node.Area = amp.Area; node.Centroid = amp.Centroid; }
                    }
                }
            }
            catch { /* 退化面忽略 */ }
            if (node.Area <= 0.0)
                node.Centroid = face.GetBoundingBox(true).Center;

            node.IsInnerFace = ComputeIsInnerFace(face, node.Centroid, globalBox, tolerance);

            if (face.TryGetPlane(out Plane plane, tolerance))
            {
                node.Category = SurfaceCategory.Plane;
                node.PlaneData = plane;
            }
            else if (face.TryGetCylinder(out Cylinder cyl, tolerance))
            {
                node.Category = SurfaceCategory.Cylinder;
                node.CylinderData = cyl;
                node.IsConcaveSurface = CheckCylinderIsInnerWall(face, cyl);
            }
            else if (face.TryGetTorus(out Torus torus, tolerance))
            {
                node.Category = SurfaceCategory.Torus;
                node.TorusData = torus;
            }
            else if (face.TryGetCone(out Cone cone, tolerance))
            {
                node.Category = SurfaceCategory.Cone;
                node.ConeData = cone;
            }
            else if (face.TryGetSphere(out _, tolerance))
            {
                node.Category = SurfaceCategory.Sphere;
            }
            else
            {
                node.Category = SurfaceCategory.Freeform;
            }

            Nodes[face.FaceIndex] = node;
        }

        foreach (BrepEdge edge in WorkingBrep.Edges)
        {
            int[] adj = edge.AdjacentFaces();
            if (adj == null || adj.Length != 2) continue;
            int f1 = adj[0], f2 = adj[1];
            // Rhino 圆柱面有 seam 接缝边，AdjacentFaces() 返回 [f, f]。
            // 若建成自环，会给该面凭空添 2 条 Tangent 邻接，导致 Pass 1
            // 把任何圆柱孔壁误判成「圆角链」。实测 100x80x30 + R6 通孔即触发。
            if (f1 == f2) continue;
            if (!Nodes.ContainsKey(f1) || !Nodes.ContainsKey(f2)) continue;

            EdgeConvexity conv = EvaluateEdgeConvexity(edge, f1, f2);
            double len = edge.GetLength();

            Nodes[f1].Neighbors.Add(new AdjacencyEdge
            { NeighborFaceIndex = f2, BrepEdgeIndex = edge.EdgeIndex, Convexity = conv, EdgeLength = len });
            Nodes[f2].Neighbors.Add(new AdjacencyEdge
            { NeighborFaceIndex = f1, BrepEdgeIndex = edge.EdgeIndex, Convexity = conv, EdgeLength = len });
        }
    }

    /// <summary>
    /// 凹区内表面判据（不依赖 OrientationIsReversed）。
    /// 取面的有效法向 n = NormalAt(u,v)（Rhino 已按 rev 修正，恒指向材料外），
    /// 面质心在 n 上的投影 proj；整体 bbox 8 个角点在 n 上的投影极值 gmin/gmax。
    /// 位于外轮廓上的面 proj 恰等于 gmin 或 gmax；凹区内表面严格落在二者之间。
    /// Rhino 9 实测：外表面 6/6 判 False，槽 4 壁 + 底 5/5 判 True；
    /// 且用挤出工具重建后 rev=False 的槽底同样判 True（rev 判据会漏掉它）。
    /// </summary>
    private static bool ComputeIsInnerFace(BrepFace face, Point3d centroid,
                                           BoundingBox global, double tolerance)
    {
        try
        {
            double u = face.Domain(0).Mid, v = face.Domain(1).Mid;
            Vector3d n = face.NormalAt(u, v);
            if (!n.Unitize()) return false;
            double proj = Vector3d.Multiply(new Vector3d(centroid.X, centroid.Y, centroid.Z), n);
            double gmin = double.PositiveInfinity, gmax = double.NegativeInfinity;
            for (int i = 0; i < 8; i++)
            {
                var c = new Point3d(
                    (i & 1) == 0 ? global.Min.X : global.Max.X,
                    (i & 2) == 0 ? global.Min.Y : global.Max.Y,
                    (i & 4) == 0 ? global.Min.Z : global.Max.Z);
                double p = Vector3d.Multiply(new Vector3d(c.X, c.Y, c.Z), n);
                if (p < gmin) gmin = p;
                if (p > gmax) gmax = p;
            }
            double eps = Math.Max(tolerance * 10.0, 1e-6);
            return Math.Abs(proj - gmin) > eps && Math.Abs(proj - gmax) > eps;
        }
        catch { return false; }
    }

    /// <summary>内圆柱壁判定：法向指向轴线则有 dot(normal, toAxis)&gt;0。实测 R6 通孔 dot=6.0。</summary>
    private bool CheckCylinderIsInnerWall(BrepFace face, Cylinder cyl)
    {
        try
        {
            double uMid = face.Domain(0).Mid;
            double vMid = face.Domain(1).Mid;
            Point3d ptOnFace = face.PointAt(uMid, vMid);
            Vector3d normal = face.NormalAt(uMid, vMid);
            var axisLine = new Line(cyl.Center, cyl.Center + cyl.Axis);
            Point3d ptOnAxis = axisLine.ClosestPoint(ptOnFace, false);
            Vector3d toAxis = ptOnAxis - ptOnFace;
            return Vector3d.Multiply(normal, toAxis) > 0;
        }
        catch { return false; }
    }

    /// <summary>
    /// 二面角凸凹性。手册约定 det = (nA×nB)·dirInA，det&gt;0 为 Convex；
    /// Rhino 9 实测该符号正确（plain box 12 条边全 Convex，带孔 box 出现 2 条 Concave）。
    /// </summary>
    private EdgeConvexity EvaluateEdgeConvexity(BrepEdge edge, int faceAIdx, int faceBIdx)
    {
        try
        {
            double midT = edge.Domain.Mid;
            Point3d pt = edge.PointAt(midT);
            Vector3d tangent = edge.TangentAt(midT);
            if (!tangent.Unitize()) return EdgeConvexity.Unknown;

            BrepFace fA = WorkingBrep.Faces[faceAIdx];
            BrepFace fB = WorkingBrep.Faces[faceBIdx];

            if (!fA.ClosestPoint(pt, out double uA, out double vA) ||
                !fB.ClosestPoint(pt, out double uB, out double vB))
                return EdgeConvexity.Unknown;

            Vector3d nA = fA.NormalAt(uA, vA);
            Vector3d nB = fB.NormalAt(uB, vB);

            double angle = Vector3d.VectorAngle(nA, nB);
            if (angle < 0.02) return EdgeConvexity.Tangent;

            Vector3d dirInA = tangent;
            foreach (int trimIdx in edge.TrimIndices())
            {
                BrepTrim trim = WorkingBrep.Trims[trimIdx];
                if (trim.Face != null && trim.Face.FaceIndex == faceAIdx)
                {
                    if (trim.IsReversed()) dirInA = -tangent;
                    break;
                }
            }

            Vector3d cross = Vector3d.CrossProduct(nA, nB);
            double det = Vector3d.Multiply(cross, dirInA);
            return det > 0 ? EdgeConvexity.Convex : EdgeConvexity.Concave;
        }
        catch { return EdgeConvexity.Unknown; }
    }
}
