using System;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input.Custom;

namespace RhinoFeatureWorks;

/// <summary>
/// FWSelect —— 交互入口：点一个实体 → 识别 → 特征面亮橙、其余面半透明锁定。
/// 再次运行同一命令即关闭聚焦（toggle），不会留下任何文档改动。
/// </summary>
[CommandStyle(Style.ScriptRunner)]
public class FwSelectCommand : Command
{
    public override string EnglishName => "FWSelect";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        // 已在聚焦状态 → 本次运行就是关闭。
        if (FwFocusSession.HasActive)
        {
            FwFocusSession.End(doc);
            RhinoApp.WriteLine("聚焦已关闭，显示恢复 / Focus OFF.");
            return Result.Success;
        }

        var go = new GetObject
        {
            GeometryFilter = ObjectType.Brep,
            SubObjectSelect = false
        };
        go.SetCommandPrompt("选择要取消特征的实体 / Select a Brep solid");
        go.Get();
        if (go.CommandResult() != Result.Success) return go.CommandResult();

        ObjRef? ore = go.Object(0);
        if (ore == null) return Result.Cancel;

        Brep? brep = ore.Brep();
        if (brep == null)
        {
            RhinoApp.WriteLine("不是 B-Rep 实体 / Not a Brep.");
            return Result.Failure;
        }

        var (_, features, _) = FwApi.Recognize(brep, doc.ModelAbsoluteTolerance);
        if (features.Count == 0)
        {
            RhinoApp.WriteLine("没有识别到可取消的特征 / No features recognized.");
            return Result.Nothing;
        }

        RhinoApp.WriteLine(FwFocusSession.Begin(doc, ore.ObjectId, brep, features));
        RhinoApp.WriteLine(FwFocusSession.Report());
        RhinoApp.WriteLine("提示 / Tip: 再运行 FWSelect 关闭聚焦；FWFocus 只看通道清单。");
        return Result.Success;
    }
}

/// <summary>FWFocus —— 只打印当前两个通道的清单，不改显示。</summary>
[CommandStyle(Style.ScriptRunner)]
public class FwFocusCommand : Command
{
    public override string EnglishName => "FWFocus";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        RhinoApp.WriteLine(FwFocusSession.Report());
        return FwFocusSession.HasActive ? Result.Success : Result.Nothing;
    }
}
