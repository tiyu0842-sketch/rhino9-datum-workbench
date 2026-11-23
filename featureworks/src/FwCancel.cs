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
    /// <summary>被"顺带"取消的其它特征组数（圆角通道走整件重建时会 &gt; 0）。</summary>
    public int Collateral { get; set; }
    public bool Ok => Brep != null;

    public static FwCancelOutcome Fail(string msg) => new() { Message = msg };
}

/// <summary>
/// 取消特征：两个通道走两套几何算法，这不是实现取舍，是 Rhino 的几何事实。
///
/// 通道 A —— 孔洞/槽（布尔做出来的）
///   布尔减只改宿主面的 trim 内环，底层曲面没动。
///   所以 Brep.UntrimFace(宿主面, tol) 直接把内环抹掉，孔就消失了，
///   而且 Rhino 会顺手清掉变多余的孔壁面。
///   实测：100x80x30 带 R6 通孔（7 面）→ UntrimFace → 6 面实体 240000。
///
/// 通道 B —— 圆角/倒角（过渡面做出来的）
///   圆角面是滚球扫出来的过渡面，四边全部与相邻面共享，不是自由边。
///   实测：对倒角盒任意一圈圆角面调用 UntrimOuterLoop 全部返回 null ——
///   该 API 要求外环边是自由边，实体里的圆角面不满足。
///   所以只能：删掉圆角面 → 剩余面取底层完整曲面 → CreateSolid 缝回毛坯。
///
///   代价（本版明确告知，不藏）：剩余面取底层曲面会把同件其它特征（孔/槽）
///   一并抹平，因为底层曲面本身是未修剪的完整曲面。也就是说
///   「取消圆角」在本版 = 「整件回到毛坯」。
///   对"倒完角不满意、要重新倒"这个主场景这正是想要的结果；
///   对"只取消一处圆角、其它孔都留着"则需要后续的孔体重放（见 README 待办）。
/// </summary>
public static class FwCancelService
{
    /// <summary>取消一组特征（按 group.Channel 自动分派到对应算法）。</summary>
    public static FwCancelOutcome CancelGroup(Brep brep, FwFocusGroup group,
        IList<FwFocusGroup>? allGroups, double tolerance = 0.001)
    {
        if (brep == null) return FwCancelOutcome.Fail("几何为空 / Brep is null.");
        if (group == null) return FwCancelOutcome.Fail("特征组为空 / Group is null.");

        bool isFillet = group.Channel == "Fillet" ||
                        group.Type == FeatureType.Fillet || group.Type == FeatureType.Chamfer;
        return isFillet
            ? CancelFillet(brep, group, allGroups, tolerance)
            : CancelHole(brep, group, tolerance);
    }

    /// <summary>
    /// 一次取消多组（含"整通道全部"）。
    /// 多组无法逐组顺序处理——每取消一组面索引就失效，所以合并面集后
    /// 一次重缝到毛坯，并把"顺带取消了几组"如实报出来。
    /// </summary>
    public static FwCancelOutcome CancelMany(Brep brep, IList<FwFocusGroup> groups,
        IList<FwFocusGroup>? allGroups, double tolerance = 0.001)
    {
        if (brep == null) return FwCancelOutcome.Fail("几何为空 / Brep is null.");
        if (groups == null || groups.Count == 0) return FwCancelOutcome.Fail("没有选中任何组 / Nothing selected.");

        var drop = new HashSet<int>();
        foreach (FwFocusGroup g in groups)
            foreach (int i in g.Faces) drop.Add(i);

        if (drop.Count == 0) return FwCancelOutcome.Fail("这些组没有面索引 / Empty face list.");

        Brep? rebuilt = SurfaceEvidenceService.RepairToBlank(brep, drop, tolerance);
        if (rebuilt == null)
            return FwCancelOutcome.Fail(
                "重建毛坯失败 / RepairToBlank returned null (CreateSolid failed).");

        double vol = VolumeOf(rebuilt);
        int total = allGroups?.Count ?? groups.Count;
        int collateral = Math.Max(0, total - groups.Count);

        var o = new FwCancelOutcome { Brep = rebuilt, Volume = vol, Collateral = collateral };
        o.Message = string.Format(
            "已取消 {0} 组（{1} 个面）→ 毛坯 faces={2} solid={3} vol={4:0.#}",
            groups.Count, drop.Count, rebuilt.Faces.Count, rebuilt.IsSolid, vol);
        if (collateral > 0)
            o.Message += Environment.NewLine +
                "注意 / Note: 整件重缝会连带恢复另外 " + collateral + " 组特征（圆角/孔洞）。";
        return o;
    }

    // ---------------------------------------------------------------- 孔洞通道

    private static FwCancelOutcome CancelHole(Brep brep, FwFocusGroup group, double tol)
    {
        var groupFaces = new HashSet<int>(group.Faces);
        int host = FindHostFace(brep, groupFaces);
        if (host < 0)
            return FwCancelOutcome.Fail(
                "没找到承载该孔洞的外表面（要求带内环且与该孔壁相邻）/ No host face with inner loop found.");

        int loopsBefore = SafeLoopCount(brep, host);

        Brep? result = null;
        try { result = brep.DuplicateBrep().UntrimFace(host, tol); }
        catch (Exception ex) { return FwCancelOutcome.Fail("UntrimFace 异常 / threw: " + ex.Message); }

        if (result == null)
            return FwCancelOutcome.Fail("UntrimFace 返回 null，该面内环无法恢复 / UntrimFace returned null.");

        int loopsAfter = SafeLoopCount(result, host);
        int restored = Math.Max(0, loopsBefore - loopsAfter);
        double vol = VolumeOf(result);

        var o = new FwCancelOutcome { Brep = result, Volume = vol };
        o.Message = string.Format(
            "已取消孔洞 [{0}]：宿主面 F{1} 的 loop 数 {2} → {3}（恢复 {4} 个开口）；结果 faces={5} solid={6} vol={7:0.#}",
            group.Name, host, loopsBefore, loopsAfter, restored,
            result.Faces.Count, result.IsSolid, vol);

        if (restored > 1)
            o.Message += Environment.NewLine +
                "注意 / Note: 该宿主面原本带 " + restored +
                " 个开口，UntrimFace 会把它们一并恢复（Rhino API 边界，不是实现取舍）；" +
                "需要保留的孔请先单独取消、或后续用孔体重放。";
        return o;
    }

    /// <summary>找出承载孔洞的外表面：与该组孔壁面共享边、且自身带内环（&gt;1 loop）。</summary>
    private static int FindHostFace(Brep brep, HashSet<int> groupFaces)
    {
        foreach (BrepEdge edge in brep.Edges)
        {
            int[]? adj = edge.AdjacentFaces();
            if (adj == null || adj.Length == 0) continue;

            bool touchesGroup = false;
            foreach (int a in adj)
                if (groupFaces.Contains(a)) { touchesGroup = true; break; }
            if (!touchesGroup) continue;

            foreach (int a in adj)
            {
                if (a < 0 || a >= brep.Faces.Count) continue;
                if (groupFaces.Contains(a)) continue;
                if (SafeLoopCount(brep, a) > 1) return a;
            }
        }

        // 退化：任意带内环且不属于该组的面。
        for (int i = 0; i < brep.Faces.Count; i++)
            if (!groupFaces.Contains(i) && SafeLoopCount(brep, i) > 1) return i;
        return -1;
    }

    // ---------------------------------------------------------------- 圆角通道

    private static FwCancelOutcome CancelFillet(Brep brep, FwFocusGroup group,
        IList<FwFocusGroup>? allGroups, double tol)
    {
        // 圆角必须「整圈」一起删。
        // 实测（Rhino 9）：10 面倒角盒只删 1 个圆角面 → 剩 9 面 74715.5，
        // 因为另外 3 个圆角面被当成"保留面"去取底层曲面了，缝出来的是变形过渡面而不是尖角。
        // 删掉全部 4 个圆角面 → 6 面 75000（正确毛坯）。
        // 所以这里把同通道的所有组并进 drop，不管用户点了哪一组。
        var drop = new HashSet<int>(group.Faces);
        int mergedGroups = 1;
        if (allGroups != null)
        {
            foreach (FwFocusGroup g in allGroups)
            {
                if (g.Channel != "Fillet" &&
                    g.Type != FeatureType.Fillet && g.Type != FeatureType.Chamfer) continue;
                int before = drop.Count;
                foreach (int i in g.Faces) drop.Add(i);
                if (drop.Count > before) mergedGroups++;
            }
        }

        if (drop.Count == 0)
            return FwCancelOutcome.Fail("该圆角组没有面索引 / Empty face list.");

        Brep? rebuilt = SurfaceEvidenceService.RepairToBlank(brep, drop, tol);
        if (rebuilt == null)
            return FwCancelOutcome.Fail(
                "重建毛坯失败：删掉圆角面后剩余面无法缝合 / RepairToBlank returned null (CreateSolid failed).");

        double vol = VolumeOf(rebuilt);
        int holeGroups = 0;
        if (allGroups != null)
            foreach (FwFocusGroup g in allGroups)
                if (g.Channel != "Fillet" &&
                    g.Type != FeatureType.Fillet && g.Type != FeatureType.Chamfer) holeGroups++;

        var o = new FwCancelOutcome { Brep = rebuilt, Volume = vol, Collateral = holeGroups };
        o.Message = string.Format(
            "已取消圆角 [{0}]：整圈共 {1} 组 / {2} 个过渡面一并删除 → 剩余面取底层原生曲面重缝 → faces={3} solid={4} vol={5:0.#}",
            group.Name, mergedGroups, drop.Count, rebuilt.Faces.Count, rebuilt.IsSolid, vol);

        if (holeGroups > 0)
            o.Message += Environment.NewLine +
                "注意 / Note: 圆角只能整件重缝（UntrimOuterLoop 在实体圆角面上返回 null），" +
                "所以本件另外 " + holeGroups + " 组孔洞/槽也一并被恢复了。若只想取消圆角、保留孔洞，" +
                "需要孔体重放 / hole replay —— 几何路径已实测可行（毛坯 240000 → 重挖孔 236607.08），列入下一版。";
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

    private static int CountInnerLoops(Brep brep)
    {
        int n = 0;
        for (int i = 0; i < brep.Faces.Count; i++) n += Math.Max(0, SafeLoopCount(brep, i) - 1);
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
/// 两边都走这里，保证 Ctrl+Z 一次回退、聚焦状态一致、报告文字一致。
/// </summary>
public static class FwCancelRunner
{
    public static bool TryApply(RhinoDoc? doc, List<FwFocusGroup> targets,
        IList<FwFocusGroup> pool, out string message)
    {
        message = "";
        if (doc == null) { message = "没有活动文档 / No active document."; return false; }
        if (!FwFocusSession.HasActive)
        {
            message = "聚焦未开启：先运行 FWSelect 或点面板「选实体」/ Focus is OFF.";
            return false;
        }
        if (targets == null || targets.Count == 0)
        {
            message = "没有选中要取消的特征组 / Nothing selected.";
            return false;
        }

        Brep? source = FwFocusSession.SourceBrep;
        Guid id = FwFocusSession.SourceId;
        if (source == null || id == Guid.Empty)
        {
            message = "聚焦会话丢失源几何 / Source geometry missing.";
            return false;
        }

        double tol = doc.ModelAbsoluteTolerance;
        uint undo = doc.BeginUndoRecord("FeatureWorks Cancel");
        try
        {
            FwCancelOutcome outcome = targets.Count == 1
                ? FwCancelService.CancelGroup(source, targets[0], pool, tol)
                : FwCancelService.CancelMany(source, targets, pool, tol);

            message = outcome.Message;
            if (!outcome.Ok) return false;

            Brep result = outcome.Brep!;

            // 先关聚焦：conduit 还指着旧 Brep，不关会在 Replace 后画出错位的面。
            FwFocusSession.End(doc);

            // 先识别再替换：写进文档的 Brep 必须和特征面索引来自同一份几何，
            // 否则视口高亮会和实体错位（CleanBrep 可能被清理过，面序号与 result 不一定一致）。
            var (clean, feats, _) = FwApi.Recognize(result, tol);
            Brep inDoc = clean ?? result;

            if (!doc.Objects.Replace(id, inDoc))
            {
                message += Environment.NewLine + "替换文档几何失败（对象可能已删除）/ Replace failed.";
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
