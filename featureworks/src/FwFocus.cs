using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

/// <summary>
/// 一条「可取消的特征通道」——圆角通道或孔洞通道。
/// 两类特征的取消方法在几何上不同，所以从数据层就分开：
///   圆角/倒角 → Brep.UntrimOuterLoop(faceIndex)：只把外环扩回底层曲面，内环保留
///   孔/槽     → Brep.UntrimFace(faceIndex, tol)：外环 + 所有内环一起去掉，孔消失
/// </summary>
public class FwFocusGroup
{
    /// <summary>稳定编号：圆角 F1/F2…，孔洞 H1/H2…。视口标签与面板行共用同一个编号，
    /// 解决用户说的「一个一个 flat，不知道哪个跟哪个」。</summary>
    public string Id = "";
    public string Channel = "";          // "Fillet" / "Hole"
    public FeatureType Type;
    public string Name = "";
    public List<int> Faces = new();
    public string Detail = "";

    public string OneLine(int i) => string.Format(
        "[{0}] {1,-18} {2,-15} faces={3,-2} {4}", i, Name, Type, Faces.Count, Detail);
}

/// <summary>一个特征组在视口里的显示代理：子 Brep + 编号 + 锚点。</summary>
public class FwGroupVisual
{
    public Brep Brep = null!;
    public string Label = "";
    public Point3d Center;
}

/// <summary>
/// 聚焦显示：特征面画成亮橙不透明，其余面蒙成半透明灰。
/// 灰 + 高透明度正好是 Rhino 里「锁定对象」的视觉语言，用户一眼知道那些不用管。
///
/// 实测依据（本机 RhinoCommon.xml + 反射均已核对）：
///  - DisplayConduit.PostDrawObjects(DrawEventArgs) 在对象绘制之后调用，深度关系正常；
///  - CalculateBoundingBox 必须 IncludeBoundingBox，否则 conduit 不会被绘制；
///  - DisplayPipeline.DrawBrepShaded(Brep, DisplayMaterial) 支持 Transparency 0..1；
///  - Brep.DuplicateSubBrep(IEnumerable&lt;int&gt;) 抽面成新 Brep，面顺序与传入索引一致。
///
/// 整个方案不改文档、不建对象、不进 Undo —— 关闭命令即完全恢复，不会污染用户的 .3dm。
/// </summary>
public class FwFocusConduit : DisplayConduit
{
    public Brep? FeatureBrep { get; set; }
    public Brep? LockedBrep { get; set; }

    /// <summary>逐组显示代理（编号标签 + 独立颜色）。列表行号与这里的 Label 一一对应。</summary>
    public readonly List<FwGroupVisual> FeatureVisuals = new();

    /// <summary>当前被面板行/视口点选命中的组（-1=无）。命中组画高亮粗线，其余压暗。</summary>
    public int FocusedIndex = -1;

    /// <summary>源对象 Id 与「画这些子面时」的几何指纹 —— 用来判断缓存是否已经过期。</summary>
    public Guid SourceId { get; set; } = Guid.Empty;
    public int SourceFaceCount { get; set; }
    public BoundingBox SourceBounds { get; set; }

    /// <summary>
    /// 鬼影自愈：FeatureBrep / LockedBrep 是「某一时刻」按面索引从源 Brep 抽出来的子面。
    /// 一旦源对象被删、被 Replace、被移动，或者面数变了，这些子面就和视口里的实体对不上，
    /// 继续画只会在界面上留一层挪不走的橙色/灰色蒙皮。
    /// 这里只负责「不再画」；真正的状态清理交给 FwFocusSession 挂在文档事件上的处理器。
    /// 注意不能用 ReferenceEquals 比对几何实例：ObjRef.Brep() 返回的是副本，会误判成过期。
    /// </summary>
    private bool Stale()
    {
        if (SourceId == Guid.Empty) return false;
        RhinoDoc? doc = RhinoDoc.ActiveDoc;
        if (doc == null) return true;
        RhinoObject? obj = doc.Objects.FindId(SourceId);
        if (obj == null) return true;
        if (obj.Geometry is not Brep now) return true;
        if (SourceFaceCount > 0 && now.Faces.Count != SourceFaceCount) return true;
        if (!SourceBounds.IsValid) return false;

        BoundingBox bb = now.GetBoundingBox(true);
        if (!bb.IsValid) return true;
        double span = SourceBounds.Diagonal.Length;
        if (span <= RhinoMath.ZeroTolerance) span = 1.0;
        double drift = (bb.Center - SourceBounds.Center).Length;
        return drift > span * 0.02;
    }

    protected override void CalculateBoundingBox(CalculateBoundingBoxEventArgs e)
    {
        base.CalculateBoundingBox(e);
        if (Stale()) return;
        if (FeatureBrep != null) e.IncludeBoundingBox(FeatureBrep.GetBoundingBox(true));
        foreach (FwGroupVisual v in FeatureVisuals)
            if (v.Brep != null) e.IncludeBoundingBox(v.Brep.GetBoundingBox(true));
        if (LockedBrep != null) e.IncludeBoundingBox(LockedBrep.GetBoundingBox(true));
    }

    /// <summary>
    /// 把源对象本身从绘制里剔除，只画我们自己抽出来的两组子面。
    /// 实测原因：只往上叠一层高透明度灰，底色仍是原实体的不透明蓝，看起来「几乎没变」；
    /// 必须先把原对象剔除，剩下的半透明灰才真的能看穿。
    /// 纯显示层，不影响拾取、不改文档。
    /// </summary>
    protected override void ObjectCulling(CullObjectEventArgs e)
    {
        base.ObjectCulling(e);
        if (SourceId == Guid.Empty) return;
        RhinoObject? obj = e.RhinoObject;
        if (obj == null || obj.Id != SourceId) return;
        if (Stale()) return;
        e.CullObject = true;
    }

    protected override void PostDrawObjects(DrawEventArgs e)
    {
        base.PostDrawObjects(e);
        if (Stale()) return;

        // 非特征面：浅灰 + 0.72 透明 → 原对象已被 ObjectCulling 剔除，这一层就真的是「玻璃壳」。
        // 几何仍留在原对象里可被选中，选择过滤放到逻辑层（框选时只接受特征面索引）。
        if (LockedBrep != null)
        {
            var locked = new DisplayMaterial(Color.FromArgb(224, 228, 233));
            locked.Transparency = 0.72;
            e.Display.DrawBrepShaded(LockedBrep, locked);
            e.Display.DrawBrepWires(LockedBrep, Color.FromArgb(120, 126, 134), 1);
        }
    }

    /// <summary>
    /// 特征面画在 DrawForeground。
    /// 实测原因：孔壁/槽壁在实体内侧，若在 PostDrawObjects 里画，原实体的深度已经写入，
    /// 填充会被深度测试剔掉、只剩 DrawBrepWires 的线框（第一版截图就是这样）。
    /// DrawForeground 不参与深度剔除，特征面才能稳定显示成实体块。
    /// </summary>
    protected override void DrawForeground(DrawEventArgs e)
    {
        base.DrawForeground(e);
        if (Stale()) return;

        // v1.5：逐组编号显示。用户不再需要猜「列表里的 Fillet_7 是模型上哪一块」——
        // 每个特征组旁边直接画 F1/F2…/H1/H2…，面板行首是同一个编号；点行或点模型边/面，
        // 该组立刻变亮、其余压暗（FocusedIndex）。
        if (FeatureVisuals.Count > 0)
        {
            for (int i = 0; i < FeatureVisuals.Count; i++)
            {
                FwGroupVisual v = FeatureVisuals[i];
                if (v.Brep == null) continue;
                bool hot = i == FocusedIndex;
                var mat = new DisplayMaterial(hot ? Color.FromArgb(80, 220, 255) : Color.FromArgb(255, 138, 40));
                mat.Transparency = hot ? 0.05 : 0.35;
                e.Display.DrawBrepShaded(v.Brep, mat);
                e.Display.DrawBrepWires(v.Brep,
                    hot ? Color.FromArgb(0, 90, 130) : Color.FromArgb(200, 50, 0), hot ? 3 : 1);
                if (v.Center.IsValid)
                    e.Display.Draw2dText(v.Label,
                        hot ? Color.FromArgb(255, 255, 120) : Color.FromArgb(255, 245, 220),
                        v.Center, true, 13, "Arial");
            }
        }
        else if (FeatureBrep != null)
        {
            var feature = new DisplayMaterial(Color.FromArgb(255, 138, 40));
            feature.Transparency = 0.15;
            e.Display.DrawBrepShaded(FeatureBrep, feature);
            e.Display.DrawBrepWires(FeatureBrep, Color.FromArgb(200, 50, 0), 2);
        }
    }
}

/// <summary>聚焦会话：持有 conduit、两个通道的分组、锁定面索引。</summary>
public static class FwFocusSession
{
    private static FwFocusConduit? _conduit;

    public static bool HasActive => _conduit != null;
    public static Guid SourceId { get; private set; }
    public static Brep? SourceBrep { get; private set; }
    public static List<FwFocusGroup> FilletGroups { get; } = new();
    public static List<FwFocusGroup> HoleGroups { get; } = new();
    public static List<int> LockedFaces { get; } = new();

    // ---------------------------------------------------------------- v1.5 双向选择
    // 不用 C# event/Action：本机 WeaverBird 把 Action 塞进 System 命名空间，
    // 连 System.Action 都 CS0433。自定义委托最稳。
    public delegate void FocusPickHandler(int groupIndex, string origin);

    /// <summary>面板把回调挂到这里；视口点边/面选中组后回写勾选行。</summary>
    public static FocusPickHandler? PanelReceiver { get; set; }

    public static int AllGroupCount => FilletGroups.Count + HoleGroups.Count;

    public static FwFocusGroup? GroupAt(int index)
    {
        if (index < 0) return null;
        if (index < FilletGroups.Count) return FilletGroups[index];
        int h = index - FilletGroups.Count;
        return h < HoleGroups.Count ? HoleGroups[h] : null;
    }

    public static string GroupLabel(int index) => GroupAt(index)?.Id ?? "-";

    /// <summary>面板行被点：让视口把这一组标亮（不改变文档、不执行取消）。</summary>
    public static void SetFocus(int index)
    {
        if (_conduit == null || index < -1 || index >= AllGroupCount) return;
        _conduit.FocusedIndex = index;
        try { RhinoDoc.ActiveDoc?.Views.Redraw(); } catch { }
    }

    /// <summary>从面索引反查组；边索引用 BrepFace.AdjacentEdges() 反查所属面。</summary>
    public static int FindGroupByFace(int faceIndex)
    {
        for (int i = 0; i < AllGroupCount; i++)
            if (GroupAt(i)?.Faces.Contains(faceIndex) == true) return i;
        return -1;
    }

    public static int FindGroupByEdge(Brep brep, int edgeIndex)
    {
        for (int i = 0; i < AllGroupCount; i++)
        {
            FwFocusGroup? g = GroupAt(i);
            if (g == null) continue;
            foreach (int fi in g.Faces)
            {
                if (fi < 0 || fi >= brep.Faces.Count) continue;
                int[] adjacent;
                try { adjacent = brep.Faces[fi].AdjacentEdges(); }
                catch { continue; }
                if (adjacent != null && Array.IndexOf(adjacent, edgeIndex) >= 0) return i;
            }
        }
        return -1;
    }

    /// <summary>视口选中一组：高亮 + 通知面板把对应行勾上。</summary>
    public static bool PickGroup(int index, string origin)
    {
        if (_conduit == null || index < 0 || index >= AllGroupCount) return false;
        SetFocus(index);
        try { PanelReceiver?.Invoke(index, origin); } catch { }
        return true;
    }

    /// <summary>所有特征面索引（两个通道合并），框选时用作白名单。</summary>
    public static HashSet<int> FeatureFaceSet()
    {
        var set = new HashSet<int>();
        foreach (var g in FilletGroups) set.UnionWith(g.Faces);
        foreach (var g in HoleGroups) set.UnionWith(g.Faces);
        return set;
    }

    public static string Begin(RhinoDoc doc, Guid id, Brep brep, List<RecognizedFeature> features)
    {
        End(doc);

        FilletGroups.Clear();
        HoleGroups.Clear();
        LockedFaces.Clear();
        SourceId = id;
        SourceBrep = brep;

        foreach (RecognizedFeature f in features)
        {
            bool isFillet = f.Type == FeatureType.Fillet || f.Type == FeatureType.Chamfer;
            var g = new FwFocusGroup
            {
                Channel = isFillet ? "Fillet" : "Hole",
                Type = f.Type,
                Name = f.DisplayName,
                Faces = new List<int>(f.FaceIndices),
                Detail = f.Parameters.Count == 0
                    ? "-"
                    : string.Join(", ", f.Parameters.Select(kv => kv.Key + "=" + kv.Value.ToString("0.####")))
            };
            g.Id = isFillet
                ? "F" + (FilletGroups.Count + 1).ToString()
                : "H" + (HoleGroups.Count + 1).ToString();
            if (isFillet) FilletGroups.Add(g);
            else HoleGroups.Add(g);
        }

        HashSet<int> featureFaces = FeatureFaceSet();
        for (int i = 0; i < brep.Faces.Count; i++)
            if (!featureFaces.Contains(i)) LockedFaces.Add(i);

        var conduit = new FwFocusConduit
        {
            SourceId = id,
            SourceFaceCount = brep.Faces.Count,
            SourceBounds = brep.GetBoundingBox(true)
        };
        if (featureFaces.Count > 0)
            conduit.FeatureBrep = brep.DuplicateSubBrep(featureFaces.ToList());
        if (LockedFaces.Count > 0)
            conduit.LockedBrep = brep.DuplicateSubBrep(LockedFaces);

        // 每个特征组单独抽一份子 Brep，画上编号标签；面板行首用同一个 Id。
        conduit.FeatureVisuals.Clear();
        for (int i = 0; i < AllGroupCount; i++)
        {
            FwFocusGroup? g = GroupAt(i);
            if (g == null) continue;  // 理论上不会发生；索引必须始终与 AllGroupCount 对齐
            Brep? sub = null;
            Point3d center = Point3d.Unset;
            try
            {
                sub = brep.DuplicateSubBrep(new List<int>(g.Faces));
                BoundingBox bb = sub.GetBoundingBox(true);
                if (bb.IsValid) center = bb.Center;
            }
            catch { }
            // 索引必须和 AllGroupCount 一一对齐，失败也放占位（Brep 为 null 时不画）。
            conduit.FeatureVisuals.Add(new FwGroupVisual
            {
                Brep = sub ?? null!,
                Label = g.Id,
                Center = center
            });
        }
        conduit.Enabled = true;
        _conduit = conduit;

        Hook(doc);

        doc.Views.Redraw();

        return string.Format(
            "聚焦已开启 / Focus ON: 特征面 {0}（圆角 {1} 组 / 孔洞 {2} 组），其余 {3} 面半透明锁定",
            featureFaces.Count, FilletGroups.Count, HoleGroups.Count, LockedFaces.Count);
    }

    // ---------------------------------------------------------------- 事件自愈
    // 用户（或我们自己）替换/删除源对象后，conduit 里的面索引立刻失效。
    // 挂在文档事件上主动收尾，比等用户再敲一次 FWSelect 靠谱。

    // 注意：Rhino 9 的 ReplaceRhinoObject / DeleteRhinoObject / CloseDocument 是**静态事件**
    // （RhinoDoc.ReplaceRhinoObject += ...），不能挂在 doc 实例上，否则 CS0176。
    private static bool _hooked;

    private static void Hook(RhinoDoc? doc)
    {
        if (doc == null) return;
        Unhook();
        RhinoDoc.ReplaceRhinoObject += OnReplaceObject;
        RhinoDoc.DeleteRhinoObject += OnDeleteObject;
        RhinoDoc.CloseDocument += OnCloseDocument;
        _hooked = true;
    }

    private static void Unhook()
    {
        if (!_hooked) return;
        try
        {
            RhinoDoc.ReplaceRhinoObject -= OnReplaceObject;
            RhinoDoc.DeleteRhinoObject -= OnDeleteObject;
            RhinoDoc.CloseDocument -= OnCloseDocument;
        }
        catch { }
        _hooked = false;
    }

    private static void OnReplaceObject(object? sender, RhinoReplaceObjectEventArgs e)
    {
        if (_conduit == null || e.ObjectId != SourceId) return;
        End(e.Document, false);
        try { e.Document?.Views.Redraw(); } catch { }
    }

    private static void OnDeleteObject(object? sender, RhinoObjectEventArgs e)
    {
        if (_conduit == null || e.ObjectId != SourceId) return;
        End(RhinoDoc.ActiveDoc, false);
    }

    private static void OnCloseDocument(object? sender, DocumentEventArgs e)
    {
        End(null, false);
    }

    /// <summary>关闭聚焦。<paramref name="redraw"/>=false 用于从文档事件里回调，避免重入重绘。</summary>
    public static void End(RhinoDoc? doc, bool redraw = true)
    {
        Unhook();
        if (_conduit == null) return;
        _conduit.Enabled = false;
        _conduit.FeatureBrep = null;
        _conduit.LockedBrep = null;
        _conduit.FeatureVisuals.Clear();
        _conduit.FocusedIndex = -1;
        _conduit.SourceId = Guid.Empty;
        _conduit.SourceFaceCount = 0;
        _conduit = null;
        FilletGroups.Clear();
        HoleGroups.Clear();
        LockedFaces.Clear();
        SourceBrep = null;
        if (redraw) { try { doc?.Views.Redraw(); } catch { } }
    }

    public static string Report()
    {
        if (_conduit == null) return "聚焦未开启 / Focus is OFF —— 先运行 FWSelect。";

        var lines = new List<string>
        {
            "=== 可取消特征 / cancellable features ===",
            string.Format("源对象 {0} · 面总数 {1} · 锁定(半透明) {2}",
                SourceId.ToString("N").Substring(0, 8),
                SourceBrep?.Faces.Count ?? 0, LockedFaces.Count),
            "-- 圆角通道 / fillet channel（取消方式 UntrimOuterLoop）--"
        };
        if (FilletGroups.Count == 0) lines.Add("  (无 / none)");
        for (int i = 0; i < FilletGroups.Count; i++)
            lines.Add(string.Format("  {0,-4} {1}", FilletGroups[i].Id, FilletGroups[i].OneLine(i)));
        lines.Add("-- 孔洞通道 / hole channel（取消方式 UntrimFace）--");
        if (HoleGroups.Count == 0) lines.Add("  (无 / none)");
        for (int i = 0; i < HoleGroups.Count; i++)
            lines.Add(string.Format("  {0,-4} {1}", HoleGroups[i].Id, HoleGroups[i].OneLine(i)));

        return string.Join(System.Environment.NewLine, lines);
    }
}
