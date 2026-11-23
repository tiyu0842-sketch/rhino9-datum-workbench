using System;
using System.Collections.Generic;
using Rhino;
using Rhino.Commands;
using Rhino.Input;
using Rhino.Input.Custom;

namespace RhinoFeatureWorks;

/// <summary>
/// FWCancel —— 取消特征。必须先在 FWSelect 的聚焦状态里才能用。
///
/// 交互：
///   1. 打印当前两个通道的清单（你能看到有哪些可取消）
///   2. 选通道：Hole / Fillet / All
///   3. 选组号（0 = 该通道全部）
///   4. 取消 → 替换文档几何 → 重新识别 → 重新开聚焦（可以连着取消下一组）
///
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

        var go = new GetOption();
        go.SetCommandPrompt("取消哪一类 / Cancel which channel");
        int oHole = go.AddOption("Hole");
        int oFillet = go.AddOption("Fillet");
        int oAll = go.AddOption("All");
        if (go.Get() != GetResult.Option) return Result.Cancel;

        int chosen = go.OptionIndex();
        string channel;
        var pool = new List<FwFocusGroup>();
        if (chosen == oAll) { channel = "All"; pool.AddRange(fillets); pool.AddRange(holes); }
        else if (chosen == oFillet) { channel = "Fillet"; pool.AddRange(fillets); }
        else { channel = "Hole"; pool.AddRange(holes); }

        if (pool.Count == 0)
        {
            RhinoApp.WriteLine("该通道没有特征 / Channel '" + channel + "' is empty.");
            return Result.Nothing;
        }

        int pick = 0;
        if (pool.Count > 1)
        {
            // Rhino 9 实测签名：GetInteger(prompt, acceptEnterAsDefault, ref value, lower, upper)
            Result rc = RhinoGet.GetInteger(
                string.Format("组号 1..{0}，0 = 全部 / Group index (0 = all of {1})", pool.Count, channel),
                true, ref pick, 0, pool.Count);
            if (rc != Result.Success) return rc;
        }

        var targets = new List<FwFocusGroup>();
        if (pick == 0) targets.AddRange(pool);
        else targets.Add(pool[pick - 1]);

        bool ok = FwCancelRunner.TryApply(doc, targets, pool, out string message);
        RhinoApp.WriteLine(message);

        if (!ok) return Result.Failure;

        if (FwFocusSession.HasActive)
            RhinoApp.WriteLine("可继续运行 FWCancel 取消下一组，或 FWFocus 看清单 / Continue or run FWFocus.");
        else
            RhinoApp.WriteLine("已无剩余可识别特征，聚焦关闭 / No features left, focus off.");

        return Result.Success;
    }
}
