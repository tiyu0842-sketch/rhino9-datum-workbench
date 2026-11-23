using System;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input.Custom;

namespace RhinoFeatureWorks;

/// <summary>
/// FWSelect —— 交互入口（两段式，参考 XNurbs 辅助面板）：
///   第一段：点一个实体（点选即"载入"，无需先把对象加进面板）
///   第二段：自动识别 → 视口里特征面亮橙、其余面半透明锁定 → 自动弹出取消面板
/// 面板列出识别到的特征并集（圆角通道 / 孔洞通道），在面板里勾选即可剥离/抑制特征回毛坯。
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

        // 两段式交互：点选 + 识别完成后自动弹出取消面板，省略"再单独开面板"那一步。
        // 面板的 PanelShown 回调会自己 Refresh 出刚识别的两通道特征清单。
        try
        {
            FwCancelPanel.Open();
            RhinoApp.WriteLine("已在「特征取消」面板列出识别结果，勾选即可剥离 / Feature panel opened.");
        }
        catch (Exception ex)
        {
            // 面板打不开不能连累聚焦本身——视口高亮仍然可用，命令行仍可 FWCancel。
            RhinoApp.WriteLine("面板自动弹出失败 / auto-open panel failed: " + ex.Message);
        }

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
