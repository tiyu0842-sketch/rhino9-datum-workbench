using System;
using System.Drawing;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;
using NormalFaceFilter.Core;

namespace NormalFaceFilter.Rhino
{
    /// <summary>
    /// Rhino 命令：SelectFacesByNormal
    /// 选网格 → 输入参考方向 / 角度 → 把命中面提取成新网格并高亮。
    /// </summary>
    public class SelectFacesByNormalCommand : Command
    {
        public override string EnglishName
        {
            get { return "SelectFacesByNormal"; }
        }

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            var getter = new GetObject();
            getter.SetCommandPrompt("选择要筛选的网格 Mesh");
            getter.GeometryFilter = ObjectType.Mesh;
            getter.Get();
            if (getter.CommandResult() != Result.Success)
                return getter.CommandResult();

            Mesh mesh = getter.Object(0).Geometry() as Mesh;
            if (mesh == null || mesh.Faces.Count == 0)
            {
                RhinoApp.WriteLine("[NFF] 所选对象不是有效网格。");
                return Result.Failure;
            }

            string directionText = "0,0,1";
            if (RhinoGet.GetString(
                    "参考方向 (top/bottom/left/right/front/back 或 x,y,z 或 face:N) [回车=+Z] ",
                    true, ref directionText) != Result.Success)
                return Result.Cancel;

            Vector3d? parsed = MeshFilter.ParseDirection(directionText, mesh);
            if (!parsed.HasValue)
            {
                RhinoApp.WriteLine("[NFF] 方向解析失败，请用 0,0,1 这样的格式或 face:N。");
                return Result.Cancel;
            }

            double maxAngle = 30.0;
            // 真机修正（2026-11-22）：RhinoCommon 9 没有 RhinoGet.GetReal，
            // 正确入口是 GetNumber（带上下限重载）。
            if (RhinoGet.GetNumber("最大夹角(度) [30] ", true, ref maxAngle, 0.0, 180.0) != Result.Success)
                return Result.Cancel;

            double minAngle = 0.0;
            if (RhinoGet.GetNumber("最小夹角(度，0 表示从 0 开始) [0] ", true, ref minAngle, 0.0, 180.0) != Result.Success)
                return Result.Cancel;

            string answer = "n";
            if (RhinoGet.GetString("是否把参考方向当轴，正反两面都算? (y/n) [n] ",
                                   true, ref answer) != Result.Success)
                return Result.Cancel;
            bool opposite = answer.Trim().StartsWith("y", StringComparison.OrdinalIgnoreCase) ||
                            answer.Trim() == "是";

            var options = new FilterOptions
            {
                Direction = parsed.Value,
                MaxAngle = maxAngle,
                MinAngle = minAngle,
                IncludeOpposite = opposite,
                RefFace = -1
            };

            FilterResult result = MeshFilter.Filter(mesh, options);
            if (result.Kept.Count == 0)
            {
                RhinoApp.WriteLine("[NFF] 没有面落在指定角度区间内，未生成对象。");
                return Result.Success;
            }

            Mesh filtered = MeshFilter.ExtractFaces(mesh, result.Kept);
            MeshFilter.PaintByAngle(filtered, result.Kept, result.Angles);

            Guid newId = doc.Objects.AddMesh(filtered);
            RhinoObject obj = doc.Objects.Find(newId);
            if (obj != null)
            {
                try
                {
                    obj.Attributes.ColorSource = ObjectColorSource.ColorFromObject;
                    obj.Attributes.ObjectColor = Color.FromArgb(255, 70, 70);
                    obj.CommitChanges();
                }
                catch
                {
                    // 着色失败不影响几何结果
                }
                doc.Objects.Select(newId);
            }
            doc.Views.Redraw();

            RhinoApp.WriteLine("[NFF] " + MeshFilter.Summary(result, opposite, -1));
            RhinoApp.WriteLine("[NFF] 已生成 " + result.Kept.Count + " 个面的新网格对象（红色高亮）。");
            return Result.Success;
        }
    }
}
