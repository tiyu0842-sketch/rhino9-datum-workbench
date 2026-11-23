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
/// 命中后调用 PickGroup：视口高亮该组 + 回写面板勾选行（不直接执行取消）。
/// 用户再决定「取消选中」还是「保留全部」，避免点一下就改模型。
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
            "已选中 " + label + "：视口已高亮，面板对应行已勾选；点「取消选中」才会改模型 / " +
            "Selected " + label + ". Click 'Cancel selected' in the panel to apply.");
        return Result.Success;
    }
}
