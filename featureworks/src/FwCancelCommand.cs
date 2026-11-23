using System;
using System.Collections.Generic;
using System.Linq;
using Rhino;
using Rhino.Commands;
using Rhino.Input;
using Rhino.Input.Custom;

namespace RhinoFeatureWorks;

/// <summary>
/// FWCancel —— 命令行取消入口（v1.6 严格两模块）。
///
/// 与面板共用 FwCancelRunner，但不再提供跨模块的 "All" 总开关（用户明确不要）。
/// 优先使用共享选中集里属于该模块的勾选；没有勾选时，才退回「按组号」选择，
/// 且 0 = 该模块全部（不是整件毛坯）。
/// 整个过程在一个 Undo 记录里，Ctrl+Z 一次回到操作前。
/// </summary>
[CommandStyle(Style.ScriptRunner)]
public class FwCancelCommand : Command
{
    public override string EnglishName => "FWCancel";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        if (!FwFocusSession.HasActive)
        {
            RhinoApp.WriteLine("先运行 FWSelect 选中实体并识别 / Run FWSelect first.");
            return Result.Nothing;
        }

        List<FwFocusGroup> fillets = FwFocusSession.FilletGroups;
        List<FwFocusGroup> holes = FwFocusSession.HoleGroups;
        if (fillets.Count == 0 && holes.Count == 0)
        {
            RhinoApp.WriteLine("当前没有可取消的特征 / Nothing to cancel.");
            return Result.Nothing;
        }

        RhinoApp.WriteLine(FwFocusSession.Report());
        RhinoApp.WriteLine(string.Format(
            "共享选中集：共 {0} 项（圆角 {1} / 布尔 {2}）",
            FwSelectionState.Count, FwSelectionState.FilletCount, FwSelectionState.HoleCount));

        var go = new GetOption();
        go.SetCommandPrompt("执行哪个模块 / Which module (no global cancel-all)");
        int oHole = go.AddOption("BooleanRemove");
        int oFillet = go.AddOption("FilletRemove");
        if (go.Get() != GetResult.Option) return Result.Cancel;

        int chosen = go.OptionIndex();
        string module = chosen == oFillet ? "Fillet" : "Hole";
        var pool = new List<FwFocusGroup>(module == "Fillet" ? fillets : holes);
        if (pool.Count == 0)
        {
            RhinoApp.WriteLine("该模块没有特征 / Module '" + module + "' is empty.");
            return Result.Nothing;
        }

        List<int> fromState = FwSelectionState.IndicesInChannel(module);
        var targets = new List<FwFocusGroup>();

        if (fromState.Count > 0)
        {
            foreach (int i in fromState)
            {
                FwFocusGroup? g = FwFocusSession.GroupAt(i);
                if (g != null) targets.Add(g);
            }
            RhinoApp.WriteLine("沿用共享选中集里本模块的 " + targets.Count + " 组 / using current selection.");
        }
        else
        {
            int pick = 0;
            if (pool.Count > 1)
            {
                Result rc = RhinoGet.GetInteger(
                    string.Format("组号 1..{0}，0 = 本模块全部 / Group index (0 = all of module {1})",
                        pool.Count, module),
                    true, ref pick, 0, pool.Count);
                if (rc != Result.Success) return rc;
            }
            if (pick == 0) targets.AddRange(pool);
            else targets.Add(pool[pick - 1]);
        }

        if (targets.Count == 0)
        {
            RhinoApp.WriteLine("没有选中要取消的特征组 / Nothing selected.");
            return Result.Nothing;
        }

        bool ok = FwCancelRunner.TryApply(doc, module, targets, out string message);
        RhinoApp.WriteLine(message);

        if (!ok) return Result.Failure;

        if (FwFocusSession.HasActive)
            RhinoApp.WriteLine("可继续运行 FWCancel 取消下一组，或 FWFocus 看清单 / Continue or run FWFocus.");
        else
            RhinoApp.WriteLine("已无剩余可识别特征，聚焦关闭 / No features left, focus off.");

        return Result.Success;
    }
}
