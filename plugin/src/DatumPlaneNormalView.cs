using System;
using System.Collections.Generic;
using Rhino;
using Rhino.ApplicationSettings;
using Rhino.Commands;
using Rhino.Display;
using Rhino.Geometry;

namespace DatumPlanePlugin;

/// <summary>
/// v1.6：第 5 个视口 —— 「基准面法向视图」。
///
/// 做法：调用 Rhino 9 原生 SplitViewportVertical 把 Top 视图沿竖直分割线一分为二
/// （左边保留 Top，右边成为新视口），再把这个新视口的相机摆成垂直于当前基准面。
/// 关键 API：RhinoViewport.SetToPlanView(origin, XAxis, YAxis, false)，实测后
/// CameraDirection = -Normal、CameraUp = YAxis、CameraTarget = Origin（点积 1.0），
/// 再切平行投影，于是基准面正对镜头，可以像顶视图一样在斜面上建模。
///
/// 视口靠「文档字符串里的 Id + 视口名」双重识别：文件重开后 Id 可能变化，名字兜底；
/// Id 不随 Deactivate 清除，重复运行命令只复用、不会越拆越多。
/// </summary>
internal static class DatumPlaneNormalView
{
    internal const string ViewName = "基准面法向";
    private const string SplitMacro = "_SplitViewportVertical";

    private static RhinoView? Find(RhinoDoc doc)
    {
        string text = DatumPlaneCore.ReadString(doc, DatumPlaneCore.NormalViewKey);
        if (Guid.TryParse(text, out var id))
        {
            var byId = doc.Views.Find(id);
            if (byId != null) return byId;
        }
        return doc.Views.Find(ViewName, true);
    }

    /// <summary>主命令 NormalView 选项 / 独立命令 DatumPlaneNormalView 的入口。</summary>
    internal static Result Show(RhinoDoc doc)
    {
        try
        {
            if (!DatumPlaneCore.TryGetActiveDatumPlane(doc, out var plane))
                return Fail("请先创建或调用一个基准面 / Create or recall a datum first, then run NormalView.");
            var view = Find(doc);
            if (view == null)
            {
                view = SplitTop(doc);
                if (view == null) return Fail("无法垂直分割 Top 视图 / Could not split the Top viewport.");
            }
            Apply(view, doc, plane);
            doc.Views.ActiveView = view;
            DatumPlaneCore.WriteString(doc, DatumPlaneCore.NormalViewKey, view.ActiveViewport.Id.ToString("D"));
            doc.Views.Redraw();
            RhinoApp.WriteLine("第 5 视图「基准面法向」已就绪：相机垂直于基准面，CPlane 与基准面一致 / 5th viewport 'Datum Normal' ready: camera perpendicular to datum, CPlane matched.");
            return Result.Success;
        }
        catch (Exception ex)
        {
            return Fail("法向视图创建失败 / Normal view failed: " + ex.Message);
        }
    }

    /// <summary>切换基准面时由 Core 调用：若第 5 视口已存在，自动跟随新平面。</summary>
    internal static void Refresh(RhinoDoc doc)
    {
        try
        {
            var view = Find(doc);
            if (view == null) return;
            if (!DatumPlaneCore.TryGetActiveDatumPlane(doc, out var plane)) return;
            Apply(view, doc, plane);
        }
        catch { /* 视图刷新绝不能影响核心状态机 */ }
    }

    // v2.5：第 5 视窗的 CPlane 刻意保留在基准面上，退出基准面模式时不再还原。
    // 它的相机本来就是「垂直于基准面」的平面视图，把 CPlane 改回世界 XY 会让网格
    // 与镜头错开、看着像"歪的" —— 视图自洽比符号上退出模式更重要。
    // 该视口不写进逐视口存档（见 DatumPlaneCore.RememberViewportCPlane），
    // 退出时也不会被自愈逻辑误矫正。

    private static RhinoView? SplitTop(RhinoDoc doc)
    {
        var before = new HashSet<Guid>();
        foreach (var v in doc.Views) before.Add(v.ActiveViewport.Id);
        var previousActive = doc.Views.ActiveView;
        var top = doc.Views.Find("Top", true) ?? previousActive;
        if (top == null) return null;
        doc.Views.ActiveView = top;
        bool ok = RhinoApp.RunScript(doc.RuntimeSerialNumber, SplitMacro, false);
        // 把焦点还给用户原来的视口；Show() 稍后会主动切到新建的法向视图。
        if (previousActive != null && doc.Views.Find(previousActive.ActiveViewport.Id) != null)
            doc.Views.ActiveView = previousActive;
        if (!ok) return null;
        foreach (var v in doc.Views)
            if (!before.Contains(v.ActiveViewport.Id)) return v;
        return null;
    }

    private static void Apply(RhinoView view, RhinoDoc doc, Plane plane)
    {
        var vp = view.ActiveViewport;
        vp.Name = ViewName;
        vp.SetToPlanView(plane.Origin, plane.XAxis, plane.YAxis, false);
        vp.ChangeToParallelProjection(true);
        // 只改这个视口的 CPlane，避免通用构造平面模式把其他视口一起改掉。
        bool universal = ModelAidSettings.UniversalConstructionPlaneMode;
        ModelAidSettings.UniversalConstructionPlaneMode = false;
        try { vp.SetConstructionPlane(plane); }
        finally { ModelAidSettings.UniversalConstructionPlaneMode = universal; }
        if (!DatumPlaneCore.TryGetActiveDatumBoundingBox(doc, out var box))
            box = new BoundingBox(plane.Origin - new Vector3d(50, 50, 50), plane.Origin + new Vector3d(50, 50, 50));
        vp.ZoomBoundingBox(box);
    }

    /// <summary>
    /// v2.0：单独关闭第 5 视窗，恢复标准 4 视图。
    /// 用 Rhino 原生 FourViewLayout()，并清掉记录视窗 Id 的文档字符串，
    /// 不影响基准面本身（CPlane/Gumball 保持当前状态）。
    /// </summary>
    internal static Result Close(RhinoDoc doc)
    {
        try
        {
            var view = Find(doc);
            bool hadView = view != null;
            doc.Views.FourViewLayout(true);
            DatumPlaneCore.WriteString(doc, DatumPlaneCore.NormalViewKey, "");
            doc.Views.Redraw();
            RhinoApp.WriteLine(hadView
                ? "已关闭第 5 视窗，恢复标准 4 视图 / 5th viewport closed, restored 4-view layout."
                : "当前没有第 5 视窗，已确保标准 4 视图 / No 5th viewport; standard 4-view layout ensured.");
            return Result.Success;
        }
        catch (Exception ex)
        {
            return Fail("关闭第 5 视窗失败 / Failed to close normal view: " + ex.Message);
        }
    }

    private static Result Fail(string message) { RhinoApp.WriteLine(message); return Result.Failure; }
}

[CommandStyle(Style.ScriptRunner)]
public class DatumPlaneNormalViewCommand : Command
{
    public override string EnglishName => "DatumPlaneNormalView";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => DatumPlaneNormalView.Show(doc);
}

/// <summary>v2.0：单独关闭第 5 视窗、恢复 4 视图（不动基准面）。</summary>
[CommandStyle(Style.ScriptRunner)]
public class DatumPlaneNormalViewCloseCommand : Command
{
    public override string EnglishName => "DatumPlaneNormalViewClose";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => DatumPlaneNormalView.Close(doc);
}
