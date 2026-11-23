// FeatureWorks v2 — 命令层（交互拾取 + 结果汇报 + 视口高亮）
// Rhino 9 / .NET 8
//
// 本版范围（按用户确认）：只做「识别 + 列出 + 高亮」，三种处理操作留待下一版。
// 命令不写文档、不改对象——只读取 Brep 并把识别结果画成临时标注。

using System;
using System.Collections.Generic;
using System.Drawing;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;

namespace FeatureWorks
{
    public class FwRecognizeCommand : Command
    {
        public override string EnglishName { get { return "FWRecognize"; } }

        protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        {
            // 1. 拾取 Brep（实体/多重曲面）
            var get = new GetObject();
            get.SetCommandPrompt("选择要识别特征的实体/多重曲面 / Select a solid or polysurface");
            get.GeometryFilter = ObjectType.Brep;
            get.Get();
            if (get.CommandResult() != Result.Success) return get.CommandResult();
            ObjRef reference = get.Object(0);
            Brep brep = reference.Geometry() as Brep;
            if (brep == null || brep.Faces.Count == 0)
            {
                RhinoApp.WriteLine("[FW] 所选对象不是有效 Brep / Not a valid brep.");
                return Result.Failure;
            }

            // 2. r_max 比例（默认 5% 对角线，可回车接受）
            double factor = 0.05;
            Result rc = RhinoGet.GetNumber("半径上限比例 r_max（包围盒对角线的倍数）[0.05] ",
                                           true, ref factor, 0.001, 1.0);
            if (rc != Result.Success) return rc;

            // 3. 识别（Core 纯计算，内部按面数自动并行）
            var opt = new FwOptions { RMaxFactor = factor, Parallel = true };
            List<FwFeature> features = FwCore.Recognize(brep, opt);

            // 4. 命令行汇报
            double diag = brep.GetBoundingBox(true).Diagonal.Length;
            // RhinoCommon 9 实测：RhinoApp.WriteLine 没有带格式参数的重载，先 string.Format。
            RhinoApp.WriteLine(string.Format("[FW] 面数 {0} | 对角线 {1:0.###} | r_max {2:0.###} | 识别到 {3} 组特征",
                brep.Faces.Count, diag, diag * factor, features.Count));
            if (features.Count == 0)
            {
                RhinoApp.WriteLine("[FW] 未发现圆角/倒角。可尝试增大 r_max 比例 / No fillet or chamfer found.");
                return Result.Success;
            }
            foreach (FwFeature f in features)
                RhinoApp.WriteLine(string.Format("[FW] 链{0}: {1} 面#{2} {3} r={4:0.###} sweep={5:0.#}° conf={6:0.00}{7}",
                    f.ChainId, f.Kind, f.FaceIndex, f.SurfaceType, f.Radius, f.SweepDegrees, f.Confidence,
                    string.IsNullOrEmpty(f.Note) ? "" : "  (" + f.Note + ")"));

            // 5. 视口高亮：把候选面画成半透明临时对象
            // 第一版只高亮，不改原对象——用户确认后再做删除/抑制/还原。
            int marked = 0;
            foreach (FwFeature f in features)
            {
                foreach (int fi in f.Chain)
                {
                    try
                    {
                        BrepFace face = brep.Faces[fi];
                        Surface s = brep.Surfaces[face.SurfaceIndex];
                        Brep single = s.ToBrep();       // 用底层曲面做高亮片
                        if (single == null) continue;
                        Guid id = doc.Objects.AddBrep(single);
                        RhinoObject obj = doc.Objects.Find(id);
                        if (obj != null)
                        {
                            Color c = f.Kind == "chamfer" ? Color.FromArgb(255, 200, 90)
                                    : (f.Kind == "fillet-vertex" ? Color.FromArgb(120, 180, 255)
                                                                 : Color.FromArgb(255, 90, 90));
                            obj.Attributes.ColorSource = ObjectColorSource.ColorFromObject;
                            obj.Attributes.ObjectColor = c;
                            obj.CommitChanges();
                            marked++;
                        }
                    }
                    catch { /* 单面高亮失败不影响识别结果 */ }
                }
            }
            doc.Views.Redraw();
            RhinoApp.WriteLine(string.Format("[FW] 已用临时对象高亮 {0} 个面（红=边圆角 蓝=顶点圆角 橙=倒角）；原对象未改动。", marked));
            RhinoApp.WriteLine("[FW] 提示：临时高亮对象可直接删除，不影响原模型 / Highlight objects are temporary.");
            return Result.Success;
        }
    }
}
