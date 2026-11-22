using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using Rhino;
using Rhino.DocObjects;
using Rhino.Display;

namespace DatumPlanePlugin;

/// <summary>
/// v1.2 增量：每个基准面独占一个编号子图层，并在几何成功写入后锁定，防止常规建模时误选/误删。
///
/// 构造顺序（故意这么排）：
///   确保根图层 → 扫描编号 → 新建未锁子图层 → 调用方往里加对象 → LockSubLayer 锁定。
/// 把"锁定"放在 AddBrep 之后，是因为任何添加失败的路径都不该留下一个空的锁定图层；
/// 而且脚本虽通常能往锁定图层写对象，先写后锁是更稳的顺序。
///
/// 识别子图层靠 Layer.UserString 标记，不靠名字前缀——避免误认用户自己建的 DP_01 图层。
/// </summary>
internal static class DatumPlaneLayers
{
    internal const string KindKey = "DatumPlane.Kind";
    internal const string LayerKind = "DatumSubLayer";
    internal const string ReferenceKind = "ReferencePlane";
    internal const string NameKey = "DatumPlane.Name";
    internal const string LayerKey = "DatumPlane.Layer";
    internal const string LinetypeName = "基准面_虚线";
    private const string Prefix = "DP_";

    /// <summary>确保顶层「基准面」根图层存在且可用。检查口径与 v1.1 的 EnsureLayer 一致。</summary>
    internal static int EnsureRoot(RhinoDoc doc)
    {
        foreach (Layer layer in doc.Layers)
        {
            if (layer.IsDeleted || layer.ParentLayerId != Guid.Empty || layer.Name != DatumPlaneCore.LayerName) continue;
            if (layer.IsLocked || !layer.IsVisible || layer.IsReference)
            {
                RhinoApp.WriteLine("“基准面”根图层被锁定/隐藏/引用，请在图层面板调整后重试 / Root layer is locked, hidden or referenced; fix in Layers panel.");
                return -1;
            }
            return layer.Index;
        }
        using var created = new Layer { Name = DatumPlaneCore.LayerName, Color = DatumPlaneCore.DatumColor };
        return doc.Layers.Add(created);
    }

    /// <summary>
    /// 在根图层下创建下一个编号子图层（DP_01、DP_02 …）。
    /// 返回的是尚未锁定的图层索引；调用方在几何成功加入后再调用 LockSubLayer。
    /// </summary>
    internal static int CreateNumberedSubLayer(RhinoDoc doc, out string subName)
    {
        subName = string.Empty;
        int rootIndex = EnsureRoot(doc);
        if (rootIndex < 0) return -1;
        Layer? root = doc.Layers[rootIndex];
        if (root == null) return -1;

        int max = 0;
        var children = root.GetChildren(); // 只取直接子层；可能为 null
        if (children != null)
        {
            foreach (var child in children)
            {
                if (child == null || child.IsDeleted) continue;
                // 只统计本插件标记过的子图层，不误认同名用户图层
                if (child.GetUserString(KindKey) != LayerKind) continue;
                string n = child.Name ?? string.Empty;
                if (!n.StartsWith(Prefix, StringComparison.Ordinal)) continue;
                if (int.TryParse(n.Substring(Prefix.Length), NumberStyles.None,
                        CultureInfo.InvariantCulture, out int num) && num > max) max = num;
            }
        }

        subName = Prefix + (max + 1).ToString("D2", CultureInfo.InvariantCulture);
        using var sub = new Layer
        {
            Name = subName,
            ParentLayerId = root.Id,
            Color = DatumPlaneCore.DatumColor,
            IsLocked = false
        };
        // UserString 必须在 Add 之前设好：Add 会复制 Layer 对象。
        sub.SetUserString(KindKey, LayerKind);
        int index = doc.Layers.Add(sub);
        if (index >= 0)
        {
            // 双保险：个别版本 Add 后不保证副本带上用户字符串，回写一次。
            var added = doc.Layers[index];
            if (added != null && added.GetUserString(KindKey) != LayerKind)
            {
                added.SetUserString(KindKey, LayerKind);
                doc.Layers.Modify(added, index, false);
            }
        }
        return index;
    }

    /// <summary>对象成功加入后，锁定它所在的基准面子图层。</summary>
    internal static void LockSubLayer(RhinoDoc doc, int index)
    {
        if (index < 0 || index >= doc.Layers.Count) return;
        Layer? layer = doc.Layers[index];
        if (layer == null || layer.IsLocked) return;
        layer.IsLocked = true;
        doc.Layers.Modify(layer, index, false);
    }

    /// <summary>列出全部基准面子图层索引（诊断 / 清理用）。</summary>
    internal static int[] GetDatumSubLayerIndices(RhinoDoc doc)
    {
        var list = new List<int>();
        foreach (Layer layer in doc.Layers)
        {
            if (layer.IsDeleted || layer.GetUserString(KindKey) != LayerKind) continue;
            list.Add(layer.Index);
        }
        return list.ToArray();
    }

    // ---------------- v1.3 显示区分 ----------------

    /// <summary>
    /// 取（或建）基准面专用虚线线型。正数=实线段，负数=空档。
    /// 线框模式下材质透明度不渲染，只有线型和颜色能区分 —— 所以必须有这一步。
    /// </summary>
    internal static int EnsureDashedLinetype(RhinoDoc doc)
    {
        int found = doc.Linetypes.Find(LinetypeName);
        if (found >= 0) return found;
        // 8 实 / 4 空 / 1.5 实 / 4 空：明显区别于 Continuous，又不至于碎成点
        var pattern = new double[] { 8.0, -4.0, 1.5, -4.0 };
        return doc.Linetypes.Add(LinetypeName, pattern);
    }

    /// <summary>
    /// 给基准面对象套上"一眼能认出"的显示：虚线边线 + Ghosted 显示模式覆盖。
    ///
    /// 关键点：SetDisplayModeOverride 让对象**无视视口当前显示模式**，始终按 Ghosted 绘制。
    /// 所以即便你在 Wireframe 里干活，基准面自己仍是半透明幽灵显示，不再和普通平面混淆。
    /// Ghosted 的 AllowObjectAssignment=True（已在本机 Rhino 9 核实），可作为对象覆盖。
    /// 材质 0.55 仍保留，给 Shaded/Rendered 视口用；两者叠加不冲突。
    /// </summary>
    internal static void ApplyDatumAppearance(RhinoDoc doc, ObjectAttributes attr)
    {
        int lt = EnsureDashedLinetype(doc);
        if (lt >= 0)
        {
            attr.LinetypeIndex = lt;
            attr.LinetypeSource = ObjectLinetypeSource.LinetypeFromObject;
        }

        // 对象色固定为基准面棕（行业惯例），避免跟随图层色被改掉失去辨识度。
        // 必须同时设 ColorSource 和 ObjectColor：只设 source 会用默认黑色，
        // 在 Ghosted / 线框下边线就是黑的，反而不易认（实测抓到）。
        attr.ColorSource = ObjectColorSource.ColorFromObject;
        attr.ObjectColor = DatumPlaneCore.DatumColor;

        var ghosted = DisplayModeDescription.FindByName("Ghosted");
        if (ghosted != null && ghosted.AllowObjectAssignment)
        {
            if (!attr.SetDisplayModeOverride(ghosted))
                RhinoApp.WriteLine("警告：显示模式覆盖失败，可能仍按视口模式显示 / Warning: display override failed; may follow viewport mode.");
        }
    }
}
