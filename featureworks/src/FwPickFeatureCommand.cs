using System;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input.Custom;

namespace RhinoFeatureWorks;

/// <summary>
/// FWPickFeature —— 在视口里直接点「边 / 面」来选中要取消的特征（v1.5）。
///
/// 为什么需要它：FWSelect 之后面板里的 Fillet_1…N 只是一行文字，用户没法把
/// 「列表第 7 行」和「模型上哪一圈圆角」对上；用户说得直接 ——
/// 「我去选择边缘，然后取消它的特征不更好吗」。
///
/// 做法：GetObject 打开子对象选择，拿到 ObjRef.GeometryComponentIndex：
///   BrepFace → 直接查 FwFocusSession.FindGroupByFace(index)
///   BrepEdge → 用 BrepFace.AdjacentEdges() 反查该边属于哪个特征面
/// v1.6：常驻视口监听已经是主交互，本命令保留为「命令行精确点一条边」的补充入口。
/// 命中后 PickGroup 写入共享选中集（Toggle），面板订阅 FwSelectionState.Changed 自动同步；
/// 两个通道的勾选可以并存，不再像 v1.5 那样回写成单选。仍不直接执行取消。
/// </summary>
[CommandStyle(Style.ScriptRunner)]
public class FwPickFeatureCommand : Command
{
    public override string EnglishName => "FWPickFeature";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        if (!FwFocusSession.HasActive)
        {
            RhinoApp.WriteLine("请先运行 FWSelect 识别实体 / Run FWSelect first.");
            return Result.Nothing;
        }

        Brep? source = FwFocusSession.SourceBrep;
        if (source == null)
        {
            RhinoApp.WriteLine("源几何已失效 / Source geometry is gone.");
            return Result.Nothing;
        }

        var go = new GetObject
        {
            GeometryFilter = ObjectType.Brep,
            SubObjectSelect = true
        };
        go.SetCommandPrompt("点要取消的特征边或面（仅认已识别的组）/ Pick a feature edge or face");
        go.Get();
        if (go.CommandResult() != Result.Success) return go.CommandResult();

        ObjRef? ore = go.Object(0);
        if (ore == null)
        {
            RhinoApp.WriteLine("没有选中对象 / Nothing picked.");
            return Result.Nothing;
        }

        if (ore.ObjectId != FwFocusSession.SourceId)
        {
            RhinoApp.WriteLine("这不是当前识别的源对象 / Not the recognized source object.");
            return Result.Nothing;
        }

        ComponentIndex ci = ore.GeometryComponentIndex;
        int group = -1;
        if (ci.ComponentIndexType == ComponentIndexType.BrepFace)
            group = FwFocusSession.FindGroupByFace(ci.Index);
        else if (ci.ComponentIndexType == ComponentIndexType.BrepEdge)
            group = FwFocusSession.FindGroupByEdge(source, ci.Index);

        if (group < 0)
        {
            RhinoApp.WriteLine("这条边/面不属于已识别特征（比如主体平面）/ Not a recognized feature.");
            return Result.Nothing;
        }

        string label = FwFocusSession.GroupLabel(group);
        FwFocusSession.PickGroup(group, "viewport");
        RhinoApp.WriteLine(
            "已切换 " + label + " 的选中状态（共享选中集，面板同步）；按对应模块按钮才会改模型 / " +
            "Toggled " + label + " in the shared selection; press a module button to apply.");
        return Result.Success;
    }
}
