using System;
using System.Linq;
using Rhino;
using Rhino.ApplicationSettings;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;

namespace DatumPlanePlugin;

[CommandStyle(Style.ScriptRunner)]
public class DatumPlaneCommand : Command
{
    public override string EnglishName => "DatumPlane";

    /// <summary>
    /// 统一入口：一个 DatumPlane 就能选全部基准面状态。
    /// v1.8 起菜单统一由 JzMenu 生成（字母代号 + 中文说明），敲字母即可选效果。
    /// 各独立命令（Pick/Restore/Save/Recall/Lock/NormalView）仍保留，供工具栏和脚本调用。
    /// </summary>
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => JzMenu.Run(doc, JzScope.Datum);

    internal static Result GetThreePoints(out Plane plane)
    {
        plane = Plane.Unset;
        var pts = new Point3d[3];
        string[] prompts =
        {
            "指定基准面原点 / Specify datum origin",
            "指定 X 轴方向点 / Specify point on X axis",
            "指定第三点决定 Y 方向 / Specify third point (sets Y direction)"
        };
        for (int i = 0; i < 3; i++)
        {
            using var get = new GetPoint();
            get.SetCommandPrompt(prompts[i]);
            if (i > 0) { get.SetBasePoint(pts[0], true); get.DrawLineFromPoint(pts[0], true); }
            if (get.Get() != GetResult.Point) return get.CommandResult() == Result.Success ? Result.Cancel : get.CommandResult();
            pts[i] = get.Point();
        }
        plane = new Plane(pts[0], pts[1], pts[2]);
        if (plane.IsValid) return Result.Success;
        RhinoApp.WriteLine("三点共线或重合，无法建立基准面 / Points are collinear or coincident; cannot define a plane.");
        return Result.Failure;
    }

    /// <summary>
    /// v2.7：B 选项「拾取平面」把两种交互整合成一次点选。
    ///
    /// 参考 Rhino 原生 ExtrudeBrepFace / ExtractSrf（抽离曲面、抽离结构线）的交互：
    /// GeometryFilter **只给 ObjectType.Surface** + SubObjectSelect + DisablePreSelect，
    /// 鼠标点哪个面就直接拿到那个面，不需要 Ctrl+Shift。
    /// 旧版写的是 Surface | Brep —— Brep 会让顶层对象抢先被选中，这正是必须按
    /// Ctrl+Shift 才能选面的根因（McNeel 论坛「How to Select Surface Subsets via
    /// GetObject Without Ctrl Key」与官方 ExtrudeBrepFace 示例均确认这一点）。
    ///
    /// 再加一条兜底：万一 Rhino 返回的仍是整个对象，就用点击位置在这个 Brep 里
    /// 找距离最近的**平面**面片 —— 于是「单独平面曲面 / 多重曲面上的单一面 /
    /// Ctrl+Shift 精确选面」三种情形走同一套逻辑，用户不用记任何修饰键。
    /// </summary>
    internal static Result GetFace(RhinoDoc doc, out Plane plane)
    {
        plane = Plane.Unset;
        using var get = new GetObject();
        get.SetCommandPrompt(
            "点选平面面片：直接点击实体/多重曲面上的那个面即可（无需 Ctrl+Shift）/ Click a planar face directly (no Ctrl+Shift needed)");
        get.GeometryFilter = ObjectType.Surface;
        get.SubObjectSelect = true;
        get.DisablePreSelect();      // 预选会走整对象路径，必须关掉
        get.SubObjectSelect = true;  // DisablePreSelect 之后重申一次，避免内部被重置
        if (get.Get() != GetResult.Object) return get.CommandResult() == Result.Success ? Result.Cancel : get.CommandResult();
        if (get.ObjectCount < 1) return Result.Cancel;
        using var obj = get.Object(0);
        if (obj == null) return Result.Failure;

        double tol = doc.ModelAbsoluteTolerance;
        Point3d pick = PickPoint(get, obj);
        Brep? owned = null;
        try
        {
            BrepFace? face = obj.Face();
            Surface? standalone = null;
            if (face == null)
            {
                var geom = obj.Geometry();
                if (geom is Surface surface) standalone = surface;
                else if (geom is Extrusion extrusion)
                {
                    owned = extrusion.ToBrep();
                    face = FindPlanarFaceNear(owned, pick, tol);
                }
                else if (geom is Brep brep)
                    face = FindPlanarFaceNear(brep, pick, tol);
            }
            if (face == null && standalone == null) return NotPlanar();

            // 先确认是平面。
            bool planar = face != null
                ? face.TryGetPlane(out _, tol)
                : standalone!.TryGetPlane(out _, tol);
            if (!planar) return NotPlanar();

            // v2.0 起：原点取面的“面积质心”而不是点击点，
            // X/Y 取该点 UV 标架、Z 取法线 —— 基准面正好落在面中心，不再偏。
            if (!TryBuildFacePlane(face, standalone, tol, out plane))
                return NotPlanar();
            return Result.Success;
        }
        finally { owned?.Dispose(); }
    }

    /// <summary>取点击位置：优先 ObjRef 上的选择点，退化到 GetObject 的拾取点。</summary>
    private static Point3d PickPoint(GetObject get, ObjRef objRef)
    {
        Point3d point = Point3d.Unset;
        try { point = objRef.SelectionPoint(); } catch { }
        if (!point.IsValid) { try { point = get.Point(); } catch { } }
        return point;
    }

    /// <summary>
    /// 在 Brep 里找离点击位置最近的平面面片（跳过圆角、曲面等非平面面）。
    /// 点击点无效时退化为包围盒中心；Brep 只有一个面时直接返回它。
    /// 抽成 internal 便于反射测试：多面体上点顶面就该拿到顶面。
    /// </summary>
    internal static BrepFace? FindPlanarFaceNear(Brep brep, Point3d pick, double tol)
    {
        if (brep == null || brep.Faces.Count == 0) return null;
        if (brep.Faces.Count == 1)
            return brep.Faces[0].TryGetPlane(out _, tol) ? brep.Faces[0] : null;
        if (!pick.IsValid) pick = brep.GetBoundingBox(true).Center;

        BrepFace? best = null;
        double nearestPlanar = double.MaxValue;
        double nearestAny = double.MaxValue;
        foreach (BrepFace candidate in brep.Faces)
        {
            double distance;
            if (candidate.ClosestPoint(pick, out double u, out double v))
                distance = candidate.PointAt(u, v).DistanceTo(pick);
            else
                distance = candidate.GetBoundingBox(true).Center.DistanceTo(pick);
            if (distance < nearestAny) nearestAny = distance;
            if (candidate.TryGetPlane(out _, tol) && distance < nearestPlanar)
            {
                nearestPlanar = distance;
                best = candidate;
            }
        }
        if (best == null) return null;
        // 点到的是明显更近的圆角/曲面时，不要偷偷拿另一块平面糊弄用户 —— 交回 NotPlanar 提示。
        BoundingBox box = brep.GetBoundingBox(true);
        double slack = (box.Max - box.Min).Length * 0.02 + tol;
        return nearestPlanar > nearestAny + slack ? null : best;
    }

    /// <summary>
    /// 以面的面积质心为原点、UV 切向为 X/Y、法线为 Z 构造平面。
    /// 用 DuplicateFace 求质心（trimmed 面的参数域中点可能落在面外），
    /// 再 ClosestPoint 回 (u,v) 取 FrameAt，得到与曲面 UV 对齐的原生标架。
    /// </summary>
    internal static bool TryBuildFacePlane(BrepFace? face, Surface? standalone, double tol, out Plane plane)
    {
        plane = Plane.Unset;
        try
        {
            Point3d centroid;
            double u, v;
            if (face != null)
            {
                using (Brep? single = face.DuplicateFace(false))
                {
                    var amp = single != null ? AreaMassProperties.Compute(single) : null;
                    centroid = amp != null && amp.Area > 0 ? amp.Centroid : face.GetBoundingBox(true).Center;
                }
                if (!face.ClosestPoint(centroid, out u, out v)) return false;
                if (!face.FrameAt(u, v, out plane)) return false;
                if (face.OrientationIsReversed) plane.Flip();
            }
            else if (standalone != null)
            {
                var amp = AreaMassProperties.Compute(standalone);
                centroid = amp != null && amp.Area > 0 ? amp.Centroid : standalone.GetBoundingBox(true).Center;
                if (!standalone.ClosestPoint(centroid, out u, out v)) return false;
                if (!standalone.FrameAt(u, v, out plane)) return false;
            }
            else return false;

            plane.Origin = plane.ClosestPoint(centroid);  // 原点精确落在面积质心
            return plane.IsValid;
        }
        catch { return false; }
    }
    private static Result NotPlanar()
    {
        RhinoApp.WriteLine("点到的是非平面面片；请直接点击实体/多重曲面上的平面面片（无需 Ctrl+Shift）/ That face is not planar; click a planar face of the solid/polysurface (no Ctrl+Shift needed).");
        return Result.Failure;
    }
}

[CommandStyle(Style.ScriptRunner)]
public class DatumPlaneZhCommand : DatumPlaneCommand { public override string EnglishName => "基准面"; }

[CommandStyle(Style.ScriptRunner)]
public class DatumPlaneRecallCommand : Command
{
    public override string EnglishName => "DatumPlaneRecall";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => DatumUi.Recall(doc);
}

[CommandStyle(Style.ScriptRunner)]
public class DatumPlaneLockCommand : Command
{
    public override string EnglishName => "DatumPlaneLock";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => DatumUi.Finish(doc, DatumPlaneCore.Lock(doc));
}

[CommandStyle(Style.ScriptRunner)]
public class DatumPlaneRestoreCommand : Command
{
    public override string EnglishName => "DatumPlaneRestore";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => DatumUi.Finish(doc, DatumPlaneCore.Deactivate(doc));
}

public class DatumPlaneSaveCommand : Command
{
    public override string EnglishName => "DatumPlaneSave";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => DatumUi.SaveCurrent(doc);
}

/// <summary>
/// v1.2 新增：点选一个已有基准面直接切换工作坐标系。
/// 关键点是 GetObject.LockedObjectSelect = true（Rhino 9 起才有），
/// 这样锁定子图层上的基准面也能被点到，无需临时解锁图层。
/// </summary>
[CommandStyle(Style.ScriptRunner)]
public class DatumPlanePickCommand : Command
{
    public override string EnglishName => "DatumPlanePick";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => DatumUi.Pick(doc);
}

internal static class DatumUi
{
    /// <summary>保存当前工作平面为命名基准面。主命令 Save 选项与 DatumPlaneSave 共用。</summary>
    internal static Result SaveCurrent(RhinoDoc doc)
    {
        using var get = new GetString();
        get.SetCommandPrompt("为当前工作平面命名（回车用默认名）/ Name this CPlane (Enter for default)");
        get.SetDefaultString(DatumPlaneCore.NextName(doc));
        get.AcceptNothing(true);
        var result = get.Get();
        if (result != GetResult.String && result != GetResult.Nothing) return get.CommandResult();
        var name = result == GetResult.Nothing ? DatumPlaneCore.NextName(doc) : get.StringResult();
        return DatumPlaneCore.SaveCurrent(doc, name);
    }

    internal static Result Recall(RhinoDoc doc)
    {
        var names = doc.NamedConstructionPlanes.Select(p => p.Name).ToArray();
        if (names.Length == 0)
        {
            RhinoApp.WriteLine("尚未保存基准面，先运行 DatumPlane 创建 / No saved datum yet; run DatumPlane to create one.");
            return Result.Nothing;
        }
        for (int i = 0; i < names.Length; i++) RhinoApp.WriteLine("{0}: {1}", i + 1, names[i]);
        using var get = new GetInteger();
        get.SetCommandPrompt("输入要调用的基准面编号 / Enter the number of the datum to recall");
        get.SetLowerLimit(1, false); get.SetUpperLimit(names.Length, false);
        if (get.Get() != GetResult.Number) return get.CommandResult() == Result.Success ? Result.Cancel : get.CommandResult();
        return Finish(doc, DatumPlaneCore.Recall(doc, names[get.Number() - 1]));
    }

    /// <summary>
    /// 点选已有基准面 → 只切换 CPlane，不新建任何几何 / 图层。
    /// 用自定义过滤器把拾取范围限定在本插件创建的基准面上；
    /// ExitRestore 选项走 Deactivate，精确恢复最初的 CPlane 与操作轴设置。
    /// </summary>
    internal static Result Pick(RhinoDoc doc)
    {
        using var get = new GetObject();
        get.SetCommandPrompt("点选一个已有基准面切换（锁定子图层也可拾取）/ Pick an existing datum to switch (locked layers OK)；ExitRestore 退出还原 / exit and restore");
        get.GeometryFilter = ObjectType.Surface | ObjectType.Brep;
        get.LockedObjectSelect = true;   // Rhino 9：允许选中锁定物件
        get.SubObjectSelect = false;
        get.AcceptNothing(true);         // 空回车 = 什么都不改，直接退出
        get.SetCustomGeometryFilter((rhObj, geometry, ci) =>
            rhObj != null && rhObj.Attributes.GetUserString(DatumPlaneLayers.KindKey) == DatumPlaneLayers.ReferenceKind);
        int restore = get.AddOption("ExitRestore");

        var res = get.Get();
        if (res == GetResult.Nothing) return Result.Cancel;
        if (res == GetResult.Option)
            return get.OptionIndex() == restore
                ? Finish(doc, DatumPlaneCore.Deactivate(doc))
                : Result.Cancel;
        if (res != GetResult.Object)
            return get.CommandResult() == Result.Success ? Result.Cancel : get.CommandResult();
        if (get.ObjectCount < 1) return Result.Cancel;

        using var objRef = get.Object(0);
        var obj = objRef?.Object();
        if (obj == null) return Result.Failure;
        var name = obj.Attributes.GetUserString(DatumPlaneLayers.NameKey);
        if (string.IsNullOrEmpty(name))
        {
            RhinoApp.WriteLine("所选基准面缺少名称元数据，无法调用（可能是旧版本创建的对象）/ Selected datum has no name metadata (possibly from an older version).");
            return Result.Failure;
        }
        // Recall 内部：已激活时保留"最初的恢复基线"只换平面；未激活时以当前平面为基线激活。
        // 两条路径都不 AddBrep、不新建图层 —— 这就是"切换不重复创建"。
        return Finish(doc, DatumPlaneCore.Recall(doc, name));
    }

    internal static Result Finish(RhinoDoc doc, Result result)
    {
        if (result != Result.Success || !GumballSettings.EnableGumball) return result;
        // Setting the property alone does not rebuild a gumball already on screen.
        string? mode = GumballSettings.AutoGumballAlignment switch
        {
            GumballAlignment.WorldPlane => "World",
            GumballAlignment.ConstructionPlane => "CPlane",
            GumballAlignment.ObjectPlane => "Object",
            GumballAlignment.ViewPlane => "View",
            _ => null
        };
        if (mode != null && !RhinoApp.RunScript(doc.RuntimeSerialNumber, "_GumballAlignment _" + mode, false))
            RhinoApp.WriteLine("操作轴偏好已设置；若屏幕操作轴未刷新，请重新选择对象 / Gumball preference set; if the on-screen gumball did not refresh, reselect the object.");
        doc.Views.Redraw();
        return result;
    }
}
