using System;
using System.Collections.Generic;
using System.Linq;
using Rhino;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

/// <summary>取消一组特征后的结果。</summary>
public class FwCancelOutcome
{
    public Brep? Brep { get; set; }
    public string Message { get; set; } = "";
    public double Volume { get; set; }
    /// <summary>被"顺带"影响的其它特征数（圆角整件重缝时会 &gt; 0）。v1.6 必须如实报出。</summary>
    public int Collateral { get; set; }
    public bool Ok => Brep != null;

    public static FwCancelOutcome Fail(string msg) => new() { Message = msg };
}

/// <summary>
/// v1.6 两个**独立**执行器。这不是实现取舍，是 B-rep 的几何事实（E-024 真机实测）：
///
/// 模块 B —— 去除布尔切割（孔 / 槽）
///   布尔减只改宿主面的 trim 内环，底层曲面没动。
///   Brep.RemoveHoles(IEnumerable&lt;ComponentIndex&gt;, tol)（since 6.8）只删**指定的** inner loop：
///     盒+2孔 8 面 / vol 228973.01 → RemoveHoles(loop7) → 7 面 / inner 2 / vol 232365.93
///     圆角盒+1孔 11 面 / vol 235922.14 → RemoveHoles(该孔内环) → 10 面 / vol 239315.06
///       = 纯圆角盒，**圆角完好**。所以「去布尔必须先去完圆角」是假的，两个模块任意顺序。
///   旧版用 UntrimFace(host, tol) 是错的：官方定义「outer boundary is untrimmed AND all
///     inner loops are removed」→ 8 面 / 2 孔 → 6 面 / 0 孔，两个孔一起没。
///
/// 模块 A —— 去除圆角
///   圆角是滚球扫出的**新增过渡曲面**，四边与邻面共享，没有更大的底层曲面可还原；
///   UntrimOuterLoop 官方要求外环边全 naked，对实体圆角面恒返回 null（实测）。
///   所以只能删整圈过渡面 + 相邻面重新求交缝合。代价：底层完整曲面重缝会把同件的
///   孔/槽 trim 一并抹平。用户拍板「明确报出，不偷偷改」——本版**如实报告**，
///   不做孔体重放、不假装只取消了圆角。
///
/// 两个模块共用一份 FwSelectionState 选中集，但执行时各取各的通道，互不牵连。
/// </summary>
public static class FwCancelService
{
    /// <summary>严格两模块只认显式 Channel。
    /// 不用 g.Type：FeatureType 枚举默认值恰好是 Fillet，手工构造或异常数据会把孔洞组
    /// 误判成圆角组（E-025 实测踩过，导致 RemoveHoles 收不到任何内环）。</summary>
    private static bool IsFilletChannel(FwFocusGroup g) => g.Channel == "Fillet";

    /// <summary>
    /// 模块 B：去除布尔切割。只删选中组对应的 inner loops，外环 / 圆角 / 其它孔全留。
    /// loop 索引由 FwFocusSession.FindInnerLoops 在识别时解析并存进 FwFocusGroup.Loops。
    /// </summary>
    public static FwCancelOutcome CancelBoolean(Brep brep, IList<FwFocusGroup> groups, double tol)
    {
        if (brep == null) return FwCancelOutcome.Fail("几何为空 / Brep is null.");
        if (groups == null || groups.Count == 0)
            return FwCancelOutcome.Fail("没有选中要取消的布尔特征 / Nothing selected.");

        var loops = new HashSet<int>();
        foreach (FwFocusGroup g in groups)
        {
            // 严格两模块：圆角组的勾选不进布尔执行器（只看 Channel，不看 Type）。
            if (IsFilletChannel(g)) continue;
            foreach (int li in g.Loops)
            {
                // LoopIndex 是全局编号，用线性查找比直接当列表索引更保险。
                BrepLoop? lp = null;
                for (int k = 0; k < brep.Loops.Count; k++)
                    if (brep.Loops[k].LoopIndex == li) { lp = brep.Loops[k]; break; }
                if (lp == null || lp.LoopType != BrepLoopType.Inner) continue;
                loops.Add(li);
            }
        }
        if (loops.Count == 0)
            return FwCancelOutcome.Fail(
                "选中的布尔特征没有解析到 trim 内环 / No inner loops resolved. " +
                "（可能识别结果把宿主面当成了孔壁面；请用 FWSelect 重新识别。）");

        int innerBefore = CountInnerLoops(brep);
        Brep? result = null;
        try
        {
            var cis = loops
                .Select(i => new ComponentIndex(ComponentIndexType.BrepLoop, i))
                .ToList();
            // 官方返回 Brep（不是 bool）：成功返回去掉孔的新 Brep，失败返回 null。
            result = brep.DuplicateBrep().RemoveHoles(cis, tol);
        }
        catch (Exception ex)
        {
            return FwCancelOutcome.Fail("RemoveHoles 异常 / threw: " + ex.Message);
        }
        if (result == null)
            return FwCancelOutcome.Fail(
                "RemoveHoles 返回 null / failed. 选中的内环可能已不存在，请重新识别。");

        int innerAfter = CountInnerLoops(result);
        int removed = Math.Max(0, innerBefore - innerAfter);
        double vol = VolumeOf(result);

        var o = new FwCancelOutcome { Brep = result, Volume = vol };
        o.Message = string.Format(
            "模块 B 去除布尔切割：删除 {0} 个指定内环 / inner loops {1} → {2}（恢复 {3} 个开口）；" +
            "结果 faces={4} solid={5} vol={6:0.#}；外环、圆角与其它孔保持原样。",
            loops.Count, innerBefore, innerAfter, removed,
            result.Faces.Count, result.IsSolid, vol);
        if (removed < loops.Count)
            o.Message += Environment.NewLine +
                "注意 / Note: 实际只少掉 " + removed + " 个环（请求 " + loops.Count +
                " 个），请核对结果；不会静默补做别的修改。";
        return o;
    }

    /// <summary>
    /// 模块 A：去除圆角。删整圈过渡面 + 相邻面重新求交缝合。
    /// <paramref name="allFillets"/> 用来保证「整圈」——实测只删 1 个圆角面会缝出变形过渡面。
    /// 若重缝连带抹平孔/槽，Collateral 与消息里**明确报出**，不做孔体重放、不偷偷改。
    /// </summary>
    public static FwCancelOutcome CancelFilletModule(Brep brep,
        IList<FwFocusGroup> selected, IList<FwFocusGroup> allFillets, double tol)
    {
        if (brep == null) return FwCancelOutcome.Fail("几何为空 / Brep is null.");
        if (selected == null || selected.Count == 0)
            return FwCancelOutcome.Fail("没有选中要取消的圆角 / Nothing selected.");

        var drop = new HashSet<int>();
        foreach (FwFocusGroup g in allFillets ?? selected)
            foreach (int fi in g.Faces)
                if (fi >= 0 && fi < brep.Faces.Count) drop.Add(fi);
        foreach (FwFocusGroup g in selected)
            foreach (int fi in g.Faces)
                if (fi >= 0 && fi < brep.Faces.Count) drop.Add(fi);

        if (drop.Count == 0)
            return FwCancelOutcome.Fail("圆角组没有面索引 / Empty face list.");

        int innerBefore = CountInnerLoops(brep);
        Brep? rebuilt = SurfaceEvidenceService.RepairToBlank(brep, drop, tol);
        if (rebuilt == null)
            return FwCancelOutcome.Fail(
                "重建失败：删掉圆角面后剩余面无法缝合 / RepairToBlank returned null (CreateSolid failed).");

        int innerAfter = CountInnerLoops(rebuilt);
        int lost = Math.Max(0, innerBefore - innerAfter);
        double vol = VolumeOf(rebuilt);

        var o = new FwCancelOutcome { Brep = rebuilt, Volume = vol, Collateral = lost };
        o.Message = string.Format(
            "模块 A 去除圆角：整圈共 {0} 个过渡面（选中 {1} 组 / 几何上整圈 {2} 组）" +
            " → 相邻面重新求交缝合 → faces={3} solid={4} vol={5:0.#}。",
            drop.Count, selected.Count, allFillets?.Count ?? selected.Count,
            rebuilt.Faces.Count, rebuilt.IsSolid, vol);

        if (lost > 0)
        {
            o.Message += Environment.NewLine +
                string.Format(
                    "【明确报出 / NOT silent】本件原有 {0} 个孔/槽 trim 内环，重缝后剩 {1} 个 —— " +
                    "另外 {2} 处布尔切割被一并恢复。原因是圆角没有底层曲面可 untrim，" +
                    "必须删过渡面后整件重缝（UntrimOuterLoop 在实体圆角面恒 null）。" +
                    "按你的选择，本版不做孔体重放、不偷偷改回去；如需保住孔，请先用模块 B " +
                    "单独处理布尔切割，或保留本结果后重挖孔。",
                    innerBefore, innerAfter, lost);
        }
        else
        {
            o.Message += " 未检测到连带影响的孔/槽（本件无内环）。";
        }
        return o;
    }

    // ---------------------------------------------------------------- 工具

    private static int SafeLoopCount(Brep brep, int faceIndex)
    {
        try
        {
            if (faceIndex < 0 || faceIndex >= brep.Faces.Count) return 0;
            return brep.Faces[faceIndex].Loops.Count;
        }
        catch { return 0; }
    }

    /// <summary>精确数 inner loop（旧版用 Loops.Count-1 假设每面一个外环，够用但不严谨）。</summary>
    private static int CountInnerLoops(Brep brep)
    {
        int n = 0;
        try
        {
            for (int i = 0; i < brep.Loops.Count; i++)
                if (brep.Loops[i].LoopType == BrepLoopType.Inner) n++;
        }
        catch { }
        return n;
    }

    public static double VolumeOf(Brep? brep)
    {
        if (brep == null) return 0.0;
        try { return VolumeMassProperties.Compute(brep)?.Volume ?? 0.0; }
        catch { return 0.0; }
    }
}

/// <summary>
/// 命令与面板共用的执行器：取消 → 替换文档几何 → 重新识别 → 重开聚焦。
/// v1.6：<paramref name="module"/> 必须显式给 "Fillet" 或 "Hole"，严格两模块、没有总开关；
/// 只执行该模块通道里的选中项，另一模块的勾选**原样保留**。
/// 两边都走这里，保证 Ctrl+Z 一次回退、聚焦状态一致、报告文字一致。
/// </summary>
public static class FwCancelRunner
{
    public static bool TryApply(RhinoDoc? doc, string module,
        List<FwFocusGroup> targets, out string message)
    {
        message = "";
        if (doc == null) { message = "没有活动文档 / No active document."; return false; }
        if (module != "Fillet" && module != "Hole")
        { message = "未知模块 / Unknown module: " + module; return false; }
        if (!FwFocusSession.HasActive)
        {
            message = "聚焦未开启：先运行 FWSelect 或点面板「选实体」/ Focus is OFF.";
            return false;
        }
        if (targets == null || targets.Count == 0)
        {
            message = "该模块没有选中要取消的特征组 / Nothing selected in this module.";
            return false;
        }
        // 严格两模块：拒绝跨模块混选，避免旧版「勾了圆角又勾孔洞 → 整件回毛坯」。
        foreach (FwFocusGroup t in targets)
        {
            // 与 Core 一致：只认显式 Channel，避免 FeatureType 默认值 Fillet 误判孔洞组。
            bool isFillet = t.Channel == "Fillet";
            if (isFillet != (module == "Fillet"))
            {
                message = "模块与选中项不匹配 / Selection belongs to the other module.";
                return false;
            }
        }

        Brep? source = FwFocusSession.SourceBrep;
        Guid id = FwFocusSession.SourceId;
        if (source == null || id == Guid.Empty)
        {
            message = "聚焦会话丢失源几何 / Source geometry missing.";
            return false;
        }

        double tol = doc.ModelAbsoluteTolerance;
        uint undo = doc.BeginUndoRecord("FeatureWorks " + module + " Cancel");
        try
        {
            FwCancelOutcome outcome = module == "Fillet"
                ? FwCancelService.CancelFilletModule(source, targets,
                    new List<FwFocusGroup>(FwFocusSession.FilletGroups), tol)
                : FwCancelService.CancelBoolean(source, targets, tol);

            message = outcome.Message;
            if (!outcome.Ok) return false;

            Brep result = outcome.Brep!;

            // 先关聚焦：conduit 还指着旧 Brep，不关会在 Replace 后画出错位的面。
            // End 内部会停常驻监听、清共享选中集。
            FwFocusSession.End(doc);

            // 先识别再替换：写进文档的 Brep 必须和特征面索引来自同一份几何，
            // 否则视口高亮会和实体错位。
            var (clean, feats, _) = FwApi.Recognize(result, tol);
            Brep inDoc = clean ?? result;

            if (!doc.Objects.Replace(id, inDoc))
            {
                message += Environment.NewLine +
                    "替换文档几何失败（对象可能已删除）/ Replace failed.";
                return false;
            }

            // 重开聚焦，方便连着取消下一组。
            if (feats.Count > 0)
                FwFocusSession.Begin(doc, id, inDoc, feats);

            doc.Views.Redraw();
            return true;
        }
        finally
        {
            doc.EndUndoRecord(undo);
        }
    }
}
