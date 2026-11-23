using System;
using System.Collections.Generic;
using System.Linq;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;

namespace RhinoFeatureWorks;

/// <summary>
/// 公开静态 API：既能被 Rhino 命令调用，也能被 Python / Grasshopper / 反射直接调用。
/// 这是「插件」之外的第二种用法——纯调用。
/// </summary>
public static class FwApi
{
    /// <summary>对一个 Brep 执行完整识别，返回清洗后的 Brep 与特征树（不写文档）。</summary>
    public static (Brep Clean, List<RecognizedFeature> Features, Dictionary<string, int> Diag)
        Recognize(Brep brep, double tolerance = 0.001)
    {
        var engine = new FeatureRecognitionEngine();
        var r = engine.RecognizeAll(brep, tolerance);
        return (r.CleanBrep, r.Features, engine.Diagnostics);
    }

    /// <summary>识别文档里指定 id 的对象，替换几何并把特征树写入 .3dm。</summary>
    public static string RecognizeInDocument(RhinoDoc doc, Guid id)
    {
        RhinoObject? obj = doc.Objects.FindId(id);
        if (obj?.Geometry is not Brep brep) return "未找到 Brep 对象 / No Brep object found.";
        double tol = doc.ModelAbsoluteTolerance;
        var (clean, feats, diag) = Recognize(brep, tol);
        doc.Objects.Replace(id, clean);
        FwSession.Set(doc, id, clean, feats, tol);
        return string.Format("识别完成 / Done: {0} 个特征 / features  (faces={1}, fillet={2}, hole={3}, cut={4})",
            feats.Count, diag.GetValueOrDefault("Faces"),
            diag.GetValueOrDefault("Pass1_Fillets"), diag.GetValueOrDefault("Pass2_Holes"),
            diag.GetValueOrDefault("Pass3_Cuts"));
    }

    public static string Suppress(RhinoDoc doc, int index)
    {
        if (!FwSession.HasTarget) return "请先识别 / Recognize first (A_Recognize).";
        if (index < 0 || index >= FwSession.Features.Count) return "编号越界 / Index out of range.";
        var feat = FwSession.Features[index];
        Brep? cur = FwSession.CurrentBrep;
        if (cur == null) return "几何丢失 / Geometry missing.";
        Brep result = FeatureReconstructionService.SuppressFeature(cur, feat, FwSession.Tolerance);
        var (_, feats, _) = Recognize(result, FwSession.Tolerance);
        doc.Objects.Replace(FwSession.TargetObjectId, result);
        FwSession.RefreshBrep(doc, result, feats);
        return string.Format("已抑制 / Suppressed [{0}] {1}；重新识别得 {2} 个特征 / now {2} features (solid={3}, faces={4})",
            index, feat.DisplayName, feats.Count, result.IsSolid, result.Faces.Count);
    }

    public static string Rebuild(RhinoDoc doc, int index, string paramKey, double value)
    {
        if (!FwSession.HasTarget) return "请先识别 / Recognize first (A_Recognize).";
        if (index < 0 || index >= FwSession.Features.Count) return "编号越界 / Index out of range.";
        var feat = FwSession.Features[index];
        if (!feat.Parameters.ContainsKey(paramKey))
            return "该特征没有参数 / No such parameter: " + paramKey +
                   " (可用 / available: " + string.Join(",", feat.Parameters.Keys) + ")";
        Brep? cur = FwSession.CurrentBrep;
        if (cur == null) return "几何丢失 / Geometry missing.";
        Brep result = FeatureReconstructionService.RebuildWithUpdatedParameters(
            cur, feat, new Dictionary<string, double> { { paramKey, value } }, FwSession.Tolerance);
        var (_, feats, _) = Recognize(result, FwSession.Tolerance);
        doc.Objects.Replace(FwSession.TargetObjectId, result);
        FwSession.RefreshBrep(doc, result, feats);
        return string.Format("已重建 / Rebuilt [{0}] {1}: {2}={3} (solid={4}, faces={5})",
            index, feat.DisplayName, paramKey, value, result.IsSolid, result.Faces.Count);
    }

    /// <summary>曲面原生/修剪证据分析（当前目标对象）。</summary>
    public static string Evidence(RhinoDoc doc)
    {
        Brep? cur = FwSession.HasTarget ? FwSession.CurrentBrep : null;
        if (cur == null)
        {
            // 未识别时尝试从当前选中对象取几何
            var picked = doc.Objects.GetSelectedObjects(false, false);
            if (picked != null)
                foreach (RhinoObject o in picked)
                    if (o.Geometry is Brep b) { cur = b; break; }
        }
        if (cur == null) return "请先识别或选中实体 / Recognize or select a Brep first.";
        return SurfaceEvidenceService.Analyze(cur, doc.ModelAbsoluteTolerance).Render();
    }

    /// <summary>整体修复：删掉所有已识别特征面，用底层原生曲面缝回毛坯，替换文档几何。</summary>
    public static string RepairAll(RhinoDoc doc)
    {
        if (!FwSession.HasTarget) return "请先识别 / Recognize first (A_Recognize).";
        Brep? cur = FwSession.CurrentBrep;
        if (cur == null) return "几何丢失 / Geometry missing.";
        Brep? blank = SurfaceEvidenceService.RepairAll(cur, FwSession.Features, FwSession.Tolerance);
        if (blank == null) return "修复失败 / Repair failed (CreateSolid returned null).";
        double vol = 0.0;
        try { vol = VolumeMassProperties.Compute(blank)?.Volume ?? 0.0; } catch { }
        doc.Objects.Replace(FwSession.TargetObjectId, blank);
        FwSession.Clear(doc);
        return string.Format("已还原毛坯 / Restored to blank: faces={0} solid={1} vol={2:0.#}",
            blank.Faces.Count, blank.IsSolid, vol);
    }

    public static string SelfTest() => FwSelfTest.Run().Render();
}

/// <summary>固定字母代号表：字母 → 英文简写 → 中文/English 说明。三个入口共用同一套代号。</summary>
internal static class FwMenu
{
    private readonly struct Entry
    {
        public readonly string Key;
        public readonly string Hint;
        public readonly char Letter;
        public Entry(string key, string hint) { Key = key; Hint = hint; Letter = key[0]; }
    }

    private static readonly Entry[] Entries =
    {
        new("A_Recognize", "选择实体并识别特征 / Pick a Brep and recognize features"),
        new("B_List",      "列出特征树 / List the feature tree"),
        new("C_Highlight", "高亮第 N 个特征 / Highlight feature #N"),
        new("D_Suppress",  "抑制第 N 个特征（删面还原）/ Suppress feature #N"),
        new("E_Rebuild",   "改参数并重建第 N 个特征 / Edit a parameter and rebuild"),
        new("F_Test",      "运行 9 项端到端自测 / Run the end-to-end self-test"),
        new("G_Clear",     "清除高亮与缓存 / Clear highlight and cache"),
        new("H_Status",    "查看当前状态 / Show status"),
        new("I_Evidence",  "曲面原生/修剪证据 / Surface trim-vs-native evidence"),
        new("J_Repair",    "整体修复还原毛坯 / Repair all features to blank"),
    };

    private static string Legend() => string.Join("  ",
        Entries.Select(e => e.Letter + "=" + e.Hint.Split('/')[0].Trim()));

    public static Result Run(RhinoDoc doc)
    {
        using var get = new GetOption();
        get.SetCommandPrompt(
            "特征识别 / FeatureWorks（回车取消 / Enter=cancel）：" + Legend() +
            "　敲下划线字母选择 / type the underlined letter");

        var map = new Dictionary<int, char>();
        foreach (Entry e in Entries)
        {
            int idx = get.AddOption(e.Key, e.Hint);
            if (idx <= 0) return Result.Failure;
            map[idx] = e.Letter;
        }

        GetResult res = get.Get();
        if (res != GetResult.Option) return Result.Cancel;
        char letter = map.TryGetValue(get.OptionIndex(), out char c) ? c : '?';
        return Dispatch(doc, letter);
    }

    internal static Result Dispatch(RhinoDoc doc, char letter)
    {
        switch (letter)
        {
            case 'A': return Recognize(doc);
            case 'B': RhinoApp.WriteLine(FwSession.Report(doc)); return Result.Success;
            case 'C': return Highlight(doc);
            case 'D': return Suppress(doc);
            case 'E': return Rebuild(doc);
            case 'F': RhinoApp.WriteLine(FwApi.SelfTest()); return Result.Success;
            case 'G': FwSession.Clear(doc); RhinoApp.WriteLine("已清除 / Cleared."); return Result.Success;
            case 'H': RhinoApp.WriteLine(FwSession.Report(doc)); return Result.Success;
            case 'I': RhinoApp.WriteLine(FwApi.Evidence(doc)); return Result.Success;
            case 'J': RhinoApp.WriteLine(FwApi.RepairAll(doc)); return Result.Success;
            default: return Result.Cancel;
        }
    }

    private static Result Recognize(RhinoDoc doc)
    {
        var go = new GetObject();
        go.SetCommandPrompt("选择要识别的 B-Rep 实体 / Select a Brep solid for recognition");
        go.GeometryFilter = ObjectType.Brep;
        go.SubObjectSelect = false;
        go.Get();
        if (go.CommandResult() != Result.Success) return go.CommandResult();
        ObjRef? ore = go.Object(0);
        if (ore == null) return Result.Failure;
        RhinoApp.WriteLine(FwApi.RecognizeInDocument(doc, ore.ObjectId));
        RhinoApp.WriteLine(FwSession.Report(doc));
        return Result.Success;
    }

    private static Result Highlight(RhinoDoc doc)
    {
        if (!FwSession.HasTarget) { RhinoApp.WriteLine("请先识别 / Recognize first."); return Result.Nothing; }
        int n = 0;
        if (RhinoGet.GetInteger("特征编号 / Feature index (0-" + (FwSession.Features.Count - 1) + ")",
                false, ref n, 0, FwSession.Features.Count - 1) != Result.Success) return Result.Cancel;
        FwSession.Highlight(doc, n);
        RhinoApp.WriteLine("高亮 / Highlighting [" + n + "] " + FwSession.Features[n].DisplayName);
        return Result.Success;
    }

    private static Result Suppress(RhinoDoc doc)
    {
        if (!FwSession.HasTarget) { RhinoApp.WriteLine("请先识别 / Recognize first."); return Result.Nothing; }
        int n = 0;
        if (RhinoGet.GetInteger("要抑制的特征编号 / Feature index to suppress (0-" + (FwSession.Features.Count - 1) + ")",
                false, ref n, 0, FwSession.Features.Count - 1) != Result.Success) return Result.Cancel;
        RhinoApp.WriteLine(FwApi.Suppress(doc, n));
        return Result.Success;
    }

    private static Result Rebuild(RhinoDoc doc)
    {
        if (!FwSession.HasTarget) { RhinoApp.WriteLine("请先识别 / Recognize first."); return Result.Nothing; }
        int n = 0;
        if (RhinoGet.GetInteger("要重建的特征编号 / Feature index to rebuild (0-" + (FwSession.Features.Count - 1) + ")",
                false, ref n, 0, FwSession.Features.Count - 1) != Result.Success) return Result.Cancel;
        var feat = FwSession.Features[n];
        string keys = string.Join(", ", feat.Parameters.Keys);
        string key = "";
        if (RhinoGet.GetString("参数名 / Parameter name (" + keys + ")", false, ref key) != Result.Success)
            return Result.Cancel;
        if (!feat.Parameters.ContainsKey(key)) { RhinoApp.WriteLine("无此参数 / No such parameter: " + key); return Result.Nothing; }
        double val = feat.Parameters[key];
        if (RhinoGet.GetNumber("新值 / New value for " + key, false, ref val) != Result.Success)
            return Result.Cancel;
        RhinoApp.WriteLine(FwApi.Rebuild(doc, n, key, val));
        return Result.Success;
    }
}

// ---- 命令类 -----------------------------------------------------------

[CommandStyle(Style.ScriptRunner)]
public class FeatureWorksCommand : Command
{
    public override string EnglishName => "FeatureWorks";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Run(doc);
}

/// <summary>短别名 FW（"识"别 / FeatureWorks），等价于 JZ 那种一键入口。</summary>
[CommandStyle(Style.ScriptRunner)]
public class FeatureWorksAliasCommand : Command
{
    public override string EnglishName => "FW";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Run(doc);
}

[CommandStyle(Style.ScriptRunner)]
public class FwRecognizeCommand : Command
{
    public override string EnglishName => "FWRecognize";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Dispatch(doc, 'A');
}

[CommandStyle(Style.ScriptRunner)]
public class FwListCommand : Command
{
    public override string EnglishName => "FWList";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Dispatch(doc, 'B');
}

[CommandStyle(Style.ScriptRunner)]
public class FwTestCommand : Command
{
    public override string EnglishName => "FWTest";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Dispatch(doc, 'F');
}

[CommandStyle(Style.ScriptRunner)]
public class FwClearCommand : Command
{
    public override string EnglishName => "FWClear";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Dispatch(doc, 'G');
}

[CommandStyle(Style.ScriptRunner)]
public class FwStatusCommand : Command
{
    public override string EnglishName => "FWStatus";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Dispatch(doc, 'H');
}

[CommandStyle(Style.ScriptRunner)]
public class FwHighlightCommand : Command
{
    public override string EnglishName => "FWHighlight";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Dispatch(doc, 'C');
}

[CommandStyle(Style.ScriptRunner)]
public class FwSuppressCommand : Command
{
    public override string EnglishName => "FWSuppress";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Dispatch(doc, 'D');
}

[CommandStyle(Style.ScriptRunner)]
public class FwRebuildCommand : Command
{
    public override string EnglishName => "FWRebuild";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => FwMenu.Dispatch(doc, 'E');
}

/// <summary>曲面原生/修剪证据：反推这个面被做过什么操作。</summary>
[CommandStyle(Style.ScriptRunner)]
public class FwEvidenceCommand : Command
{
    public override string EnglishName => "FWEvidence";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        RhinoApp.WriteLine(FwApi.Evidence(doc));
        return Result.Success;
    }
}

/// <summary>整体修复：删特征面 → untrim 恢复原生曲面 → 重新缝合还原毛坯。</summary>
[CommandStyle(Style.ScriptRunner)]
public class FwRepairCommand : Command
{
    public override string EnglishName => "FWRepair";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        RhinoApp.WriteLine(FwApi.RepairAll(doc));
        return Result.Success;
    }
}
