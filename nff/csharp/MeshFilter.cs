using System;
using System.Collections.Generic;
using System.Drawing;
using Rhino.Geometry;

namespace NormalFaceFilter.Core
{
    /// <summary>筛选参数。</summary>
    public sealed class FilterOptions
    {
        public Vector3d Direction { get; set; }
        public double MaxAngle { get; set; }
        public double MinAngle { get; set; }
        public bool IncludeOpposite { get; set; }
        public int RefFace { get; set; }

        public FilterOptions()
        {
            Direction = new Vector3d(0, 0, 1);
            MaxAngle = 30.0;
            MinAngle = 0.0;
            IncludeOpposite = false;
            RefFace = -1;
        }
    }

    /// <summary>筛选结果。</summary>
    public sealed class FilterResult
    {
        public List<int> Kept { get; set; }
        public List<int> Removed { get; set; }
        public List<double?> Angles { get; set; }
        public Vector3d Reference { get; set; }
        public double MinAngle { get; set; }
        public double MaxAngle { get; set; }
        public int Total { get; set; }
    }

    /// <summary>按法线与参考方向夹角筛选网格面的核心算法（Rhino / Grasshopper 共用）。</summary>
    public static class MeshFilter
    {
        private const double Eps = 1e-12;
        private const double RadToDeg = 180.0 / Math.PI;

        /// <summary>计算单个网格面的单位法线；退化面返回 null。</summary>
        public static Vector3d? FaceNormal(Mesh mesh, int faceIndex)
        {
            if (mesh == null || faceIndex < 0 || faceIndex >= mesh.Faces.Count)
                return null;

            MeshFace face = mesh.Faces[faceIndex];
            Point3d a, b, c;
            try
            {
                a = mesh.Vertices[face.A];
                b = mesh.Vertices[face.B];
                c = mesh.Vertices[face.C];
            }
            catch
            {
                return null;
            }

            Vector3d n = Vector3d.CrossProduct(b - a, c - a);
            if (face.IsQuad)
            {
                try
                {
                    Point3d d = mesh.Vertices[face.D];
                    n += Vector3d.CrossProduct(c - a, d - a);
                }
                catch
                {
                    return null;
                }
            }

            if (n.Length < Eps)
                return null;
            n.Unitize();
            return n;
        }

        /// <summary>两个方向的夹角（度，0~180）。</summary>
        public static double AngleBetween(Vector3d a, Vector3d b)
        {
            // RhinoCommon 9 没有 Vector3d.DotProduct 静态方法；点积用 * 运算符。
            double dot = a * b;
            if (dot > 1.0) dot = 1.0;
            if (dot < -1.0) dot = -1.0;
            return Math.Acos(dot) * RadToDeg;
        }

        /// <summary>执行筛选。</summary>
        public static FilterResult Filter(Mesh mesh, FilterOptions options)
        {
            if (mesh == null)
                throw new ArgumentNullException("mesh");
            if (options == null)
                options = new FilterOptions();

            double hi = Clamp(options.MaxAngle, 0.0, 180.0);
            double lo = Clamp(options.MinAngle, 0.0, 180.0);
            if (lo > hi)
            {
                double tmp = lo;
                lo = hi;
                hi = tmp;
            }

            Vector3d reference;
            if (options.RefFace >= 0 && options.RefFace < mesh.Faces.Count)
            {
                Vector3d? faceDir = FaceNormal(mesh, options.RefFace);
                reference = faceDir.HasValue ? faceDir.Value : options.Direction;
            }
            else
            {
                reference = options.Direction;
            }

            if (reference.Length < Eps)
                reference = new Vector3d(0, 0, 1);
            reference.Unitize();

            var result = new FilterResult
            {
                Kept = new List<int>(),
                Removed = new List<int>(),
                Angles = new List<double?>(),
                Reference = reference,
                MinAngle = lo,
                MaxAngle = hi,
                Total = mesh.Faces.Count
            };

            for (int i = 0; i < mesh.Faces.Count; i++)
            {
                Vector3d? normal = FaceNormal(mesh, i);
                if (!normal.HasValue)
                {
                    result.Angles.Add(null);
                    result.Removed.Add(i);
                    continue;
                }

                double theta = AngleBetween(normal.Value, reference);
                result.Angles.Add(theta);

                bool hit = lo <= theta && theta <= hi;
                if (options.IncludeOpposite)
                {
                    double oppositeAngle = 180.0 - theta;
                    hit = hit || (lo <= oppositeAngle && oppositeAngle <= hi);
                }

                if (hit)
                    result.Kept.Add(i);
                else
                    result.Removed.Add(i);
            }

            return result;
        }

        /// <summary>按原面索引提取命中面，生成新网格。</summary>
        public static Mesh ExtractFaces(Mesh mesh, IList<int> indices)
        {
            Mesh output = new Mesh();
            if (mesh == null)
                return output;

            foreach (int faceIndex in indices)
            {
                if (faceIndex < 0 || faceIndex >= mesh.Faces.Count)
                    continue;
                MeshFace face = mesh.Faces[faceIndex];
                try
                {
                    if (face.IsTriangle)
                    {
                        int i0 = output.Vertices.Add(mesh.Vertices[face.A]);
                        int i1 = output.Vertices.Add(mesh.Vertices[face.B]);
                        int i2 = output.Vertices.Add(mesh.Vertices[face.C]);
                        output.Faces.AddFace(i0, i1, i2);
                    }
                    else if (face.IsQuad)
                    {
                        int i0 = output.Vertices.Add(mesh.Vertices[face.A]);
                        int i1 = output.Vertices.Add(mesh.Vertices[face.B]);
                        int i2 = output.Vertices.Add(mesh.Vertices[face.C]);
                        int i3 = output.Vertices.Add(mesh.Vertices[face.D]);
                        output.Faces.AddFace(i0, i1, i2, i3);
                    }
                }
                catch
                {
                    // 跳过坏面
                }
            }

            try
            {
                output.Normals.ComputeNormals();
            }
            catch
            {
                // 忽略法线计算失败
            }
            return output;
        }

        /// <summary>角度配色：0° 红 → 90° 绿 → 180° 蓝。</summary>
        public static Color ColorForAngle(double? theta)
        {
            if (!theta.HasValue)
                return Color.FromArgb(150, 150, 150);

            double t = Clamp(theta.Value, 0.0, 180.0) / 90.0;
            if (t <= 1.0)
            {
                int r = (int)Math.Round(255 * (1.0 - t));
                int g = (int)Math.Round(255 * t);
                return Color.FromArgb(r, g, 0);
            }
            int green = (int)Math.Round(255 * (2.0 - t));
            int blue = (int)Math.Round(255 * (t - 1.0));
            return Color.FromArgb(0, green, blue);
        }

        /// <summary>给筛选后的网格按夹角着色，便于在视窗中直接观察分面。</summary>
        public static void PaintByAngle(Mesh mesh, IList<int> indices, IList<double?> angles)
        {
            if (mesh == null || indices == null || angles == null)
                return;

            try
            {
                mesh.VertexColors.CreateMonotoneMesh(ColorForAngle(null));
                int slot = 0;
                foreach (int faceIndex in indices)
                {
                    if (slot >= mesh.Faces.Count || faceIndex < 0 || faceIndex >= angles.Count)
                        break;
                    Color color = ColorForAngle(angles[faceIndex]);
                    MeshFace face = mesh.Faces[slot];
                    mesh.VertexColors[face.A] = color;
                    mesh.VertexColors[face.B] = color;
                    mesh.VertexColors[face.C] = color;
                    if (face.IsQuad)
                        mesh.VertexColors[face.D] = color;
                    slot++;
                }
            }
            catch
            {
                // 着色失败不影响几何结果
            }
        }

        /// <summary>解析 "0,15,30,60,90,120,180" 形式的边界，返回相邻区间。</summary>
        public static List<double> ParseBins(string text)
        {
            var values = new List<double>();
            if (string.IsNullOrWhiteSpace(text))
                return values;

            string[] parts = text.Replace("，", ",").Split(',');
            foreach (string part in parts)
            {
                double v;
                if (double.TryParse(part.Trim(), out v))
                    values.Add(v);
            }
            values.Sort();
            return values;
        }

        /// <summary>按角度区间把面索引分组，每个区间对应一个 DataTree 分支。</summary>
        public static List<List<int>> GroupByBins(IList<int> indices,
                                                  IList<double?> angles,
                                                  IList<double> boundaries)
        {
            var groups = new List<List<int>>();
            if (boundaries == null)
                return groups;
            for (int i = 0; i < boundaries.Count - 1; i++)
                groups.Add(new List<int>());

            foreach (int faceIndex in indices)
            {
                if (faceIndex < 0 || faceIndex >= angles.Count)
                    continue;
                double? theta = angles[faceIndex];
                if (!theta.HasValue)
                    continue;
                for (int b = 0; b < groups.Count; b++)
                {
                    if (theta.Value >= boundaries[b] && theta.Value <= boundaries[b + 1])
                    {
                        groups[b].Add(faceIndex);
                        break;
                    }
                }
            }
            return groups;
        }

        /// <summary>解析方向字符串：预设词 / x,y,z / face:N。</summary>
        public static Vector3d? ParseDirection(string text, Mesh mesh)
        {
            if (string.IsNullOrWhiteSpace(text))
                return new Vector3d(0, 0, 1);

            string value = text.Trim();
            string lower = value.ToLowerInvariant();

            switch (lower)
            {
                case "top":
                case "上":
                case "顶":
                    return new Vector3d(0, 0, 1);
                case "bottom":
                case "下":
                case "底":
                    return new Vector3d(0, 0, -1);
                case "left":
                case "左":
                    return new Vector3d(-1, 0, 0);
                case "right":
                case "右":
                    return new Vector3d(1, 0, 0);
                case "front":
                case "前":
                    return new Vector3d(0, -1, 0);
                case "back":
                case "后":
                    return new Vector3d(0, 1, 0);
            }

            if (lower.StartsWith("face:") || lower.StartsWith("面:") || lower.StartsWith("f:"))
            {
                string digits = value.Substring(value.IndexOf(':') + 1).Trim();
                int index;
                if (!int.TryParse(digits, out index))
                    return null;
                if (mesh == null || index < 0 || index >= mesh.Faces.Count)
                    return null;
                return FaceNormal(mesh, index);
            }

            string[] parts = value.Replace("，", ",").Replace(' ', ',').Split(',');
            if (parts.Length != 3)
                return null;
            double x, y, z;
            if (!double.TryParse(parts[0].Trim(), out x) ||
                !double.TryParse(parts[1].Trim(), out y) ||
                !double.TryParse(parts[2].Trim(), out z))
                return null;

            var vec = new Vector3d(x, y, z);
            if (vec.Length < Eps)
                return null;
            vec.Unitize();
            return vec;
        }

        /// <summary>生成命令行 / Info 输出用的统计摘要。</summary>
        public static string Summary(FilterResult result, bool opposite, int refFace)
        {
            if (result == null)
                return string.Empty;
            string refInfo = (refFace >= 0 && refFace < result.Total)
                ? refFace.ToString()
                : "无";
            return string.Format(
                "总面数 {0} | 命中 {1} | 剔除 {2} | 参考方向 ({3:F3}, {4:F3}, {5:F3}) " +
                "| 区间 {6:F1}° ~ {7:F1}° | 反向包含 {8} | 参考面 {9}",
                result.Total, result.Kept.Count, result.Removed.Count,
                result.Reference.X, result.Reference.Y, result.Reference.Z,
                result.MinAngle, result.MaxAngle,
                opposite ? "是" : "否", refInfo);
        }

        private static double Clamp(double value, double low, double high)
        {
            if (double.IsNaN(value))
                return low;
            return Math.Max(low, Math.Min(high, value));
        }
    }
}
