// FeatureWorks v2 — 会话状态（面板与命令共享）
// 保存当前文档上最近一次识别的结果，供面板列表与处理操作使用。

using System;
using System.Collections.Generic;
using Rhino;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace FeatureWorks
{
    public sealed class FwSession
    {
        /// <summary>识别目标对象 Id。</summary>
        public Guid TargetId = Guid.Empty;

        /// <summary>目标 Brep 的几何副本（处理时从这里重建，不直接改文档对象）。</summary>
        public Brep TargetBrep;

        /// <summary>识别结果。</summary>
        public List<FwFeature> Features = new List<FwFeature>();

        /// <summary>被面板/视口选中的特征索引（对应 Features 的序号）。</summary>
        public HashSet<int> Selected = new HashSet<int>();

        /// <summary>临时高亮对象 Id（清除时删掉）。</summary>
        public List<Guid> HighlightIds = new List<Guid>();

        /// <summary>备份图层名（抑制/删除时把原对象移到这里）。</summary>
        public const string BackupLayer = "FW_Backup";

        private static readonly Dictionary<uint, FwSession> Map = new Dictionary<uint, FwSession>();
        public static FwSession Get(RhinoDoc doc)
        {
            if (doc == null) return new FwSession();
            if (!Map.TryGetValue(doc.RuntimeSerialNumber, out var s)) { s = new FwSession(); Map[doc.RuntimeSerialNumber] = s; }
            return s;
        }

        /// <summary>把识别结果装进会话（由命令/面板调用）。</summary>
        public void SetResult(Guid targetId, Brep brep, List<FwFeature> features)
        {
            TargetId = targetId;
            TargetBrep = brep != null ? brep.DuplicateBrep() : null;
            Features = features ?? new List<FwFeature>();
            Selected.Clear();
        }

        /// <summary>清除视口里的临时高亮对象。</summary>
        public void ClearHighlights(RhinoDoc doc)
        {
            if (doc == null) return;
            foreach (Guid id in HighlightIds)
                doc.Objects.Delete(id, true);
            HighlightIds.Clear();
        }

        /// <summary>
        /// 把选中的特征面高亮成临时对象。
        /// 红=边圆角，蓝=顶点圆角，橙=chamfer —— 与命令层配色一致。
        /// </summary>
        public void Highlight(RhinoDoc doc)
        {
            if (doc == null || TargetBrep == null) return;
            ClearHighlights(doc);
            foreach (int idx in Selected)
            {
                if (idx < 0 || idx >= Features.Count) continue;
                FwFeature f = Features[idx];
                foreach (int faceIdx in f.Chain)
                {
                    try
                    {
                        if (faceIdx < 0 || faceIdx >= TargetBrep.Faces.Count) continue;
                        BrepFace face = TargetBrep.Faces[faceIdx];
                        Surface s = TargetBrep.Surfaces[face.SurfaceIndex];
                        Brep piece = s.ToBrep();
                        if (piece == null) continue;
                        Guid id = doc.Objects.AddBrep(piece);
                        RhinoObject obj = doc.Objects.Find(id);
                        if (obj != null)
                        {
                            System.Drawing.Color c = f.Kind == "chamfer" ? System.Drawing.Color.FromArgb(255, 200, 90)
                                : (f.Kind == "fillet-vertex" ? System.Drawing.Color.FromArgb(120, 180, 255)
                                                             : System.Drawing.Color.FromArgb(255, 90, 90));
                            obj.Attributes.ColorSource = ObjectColorSource.ColorFromObject;
                            obj.Attributes.ObjectColor = c;
                            obj.CommitChanges();
                            HighlightIds.Add(id);
                        }
                    }
                    catch { /* 单面高亮失败不影响其它 */ }
                }
            }
            doc.Views.Redraw();
        }
    }
}
