using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.Text;
using Rhino;
using Rhino.ApplicationSettings;
using Rhino.Commands;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace DatumPlanePlugin;

public static class DatumPlaneCore
{
    public const string LayerName = "基准面";
    public const string MaterialName = "基准面_半透明";
    /// <summary>基准面行业配色：棕/琥珀（Creo / SolidWorks / CATIA 基准面正面色）。
    /// 对象色同时用于线框/Ghosted 下的边线，避免默认黑色难辨。</summary>
    public static readonly System.Drawing.Color DatumColor = System.Drawing.Color.FromArgb(176, 132, 70);
    public const double ViewWidthRatio = 0.32;
    public const double DatumTransparency = 0.55;
    private const string Section = "DatumPlane";
    // NormalViewId 故意不进 Keys：退出基准面模式后仍要记住第 5 视口，
    // 否则重复运行 NormalView 会不断把 Top 越拆越多。
    private static readonly string[] Keys = { "Active", "ActivePlane", "ViewportId", "LockedPlane", "SavedName", "Version" };
    internal const string NormalViewKey = "NormalViewId";

    // v2.5：逐视口记录「进入基准面模式之前」的 CPlane。
    // 旧版只有一个 ActivePlane，而 OnIdle 会把基准面 CPlane 迁移到用户点过的每一个视口，
    // 退出时却只能还原「活动视口 + 最后一个 ViewportId」，前面被改过的视口（典型是 Front）
    // 就留着倾斜的基准面 CPlane —— 表现为「Front 视图是歪的、网格斜着」。
    // 这里按视口 Id 存档（顺带存视口名，文件重开后 Id 失效时按名字兜底），
    // 存进文档字符串，所以中途保存/重开也能原样还原。
    private const string CPlaneMapKey = "SavedCPlanes";
    private const char RecordSep = '\u001E';
    private const char FieldSep = '\u001F';
    private static readonly Dictionary<uint, Guid> Tracked = new();
    private static uint owner;
    private static Guid ownerView;
    private static GlobalSettings? baseline;
    private static bool watching;

    /// <summary>v2.5：一个视口在「第一次被本插件改写 CPlane 之前」的原始平面。</summary>
    private sealed class CPlaneRecord
    {
        internal Guid Id;
        internal string Name = "";
        internal Plane Plane;
    }

    // These are application settings, so a document/viewport owns a temporary lease.
    // Never replay application preferences from an old .3dm over today's preferences.
    private sealed class GlobalSettings
    {
        internal readonly GumballAlignment Alignment = GumballSettings.AutoGumballAlignment;
        internal readonly bool Enabled = GumballSettings.EnableGumball;
        internal readonly bool AutoCPlane = ModelAidSettings.AutoAlignCPlane;
        internal readonly bool AutoReset = ModelAidSettings.GumballAutoReset;
        internal readonly bool Universal = ModelAidSettings.UniversalConstructionPlaneMode;
        internal void Restore()
        {
            ModelAidSettings.UniversalConstructionPlaneMode = Universal;
            ModelAidSettings.AutoAlignCPlane = AutoCPlane;
            ModelAidSettings.GumballAutoReset = AutoReset;
            GumballSettings.AutoGumballAlignment = Alignment;
            GumballSettings.EnableGumball = Enabled;
        }
    }

    public static void StartWatching()
    {
        if (watching) return;
        RhinoApp.Idle += OnIdle;
        RhinoDoc.CloseDocument += OnClose;
        RhinoDoc.ActiveDocumentChanged += OnActiveDocumentChanged;
        watching = true;
    }

    public static void StopWatching()
    {
        if (watching) { RhinoApp.Idle -= OnIdle; RhinoDoc.CloseDocument -= OnClose; RhinoDoc.ActiveDocumentChanged -= OnActiveDocumentChanged; }
        ReleaseGlobalSettings();
        Tracked.Clear();
        watching = false;
    }

    private static void OnClose(object? sender, DocumentEventArgs e)
    {
        if (e.Document == null) return;
        if (owner == e.Document.RuntimeSerialNumber) ReleaseGlobalSettings();
        Tracked.Remove(e.Document.RuntimeSerialNumber);
    }

    private static void OnActiveDocumentChanged(object? sender, DocumentEventArgs e)
    {
        if (owner != 0 && (e.Document == null || owner != e.Document.RuntimeSerialNumber)) ReleaseGlobalSettings();
    }

    /// <summary>
    /// v1.6：基准面模式跟随「活动视口」。
    /// 旧版在切换到别的视口（或新增第 5 视口）时会静默 ReleaseGlobalSettings，
    /// 却把文档里的 Active=1 留着 —— 于是用户看到「已启用」但坐标锁定其实已松开，
    /// 再选 3Point/Plane 又撞上 Create 的 "已有基准面" 拦截，形成死锁。
    /// 现在切视口时把 owner 迁移过去并重新施加 CPlane，任何视口都能正常建模。
    /// </summary>
    private static void OnIdle(object? sender, EventArgs e)
    {
        if (Command.InCommand()) return;
        var doc = RhinoDoc.ActiveDoc;
        var vp = doc?.Views.ActiveView?.ActiveViewport;
        if (doc == null || vp == null) { if (owner != 0) ReleaseGlobalSettings(); return; }
        if (!IsActive(doc)) { if (owner == doc.RuntimeSerialNumber) ReleaseGlobalSettings(); return; }
        if (!TryDeserializePlane(Read(doc, "LockedPlane"), out var target)) return;

        if (owner != doc.RuntimeSerialNumber || ownerView != vp.Id)
        {
            // Migrate the lease to the viewport the user is actually working in.
            AcquireGlobalSettings(doc, vp);
            Write(doc, "ViewportId", vp.Id.ToString("D"));
            Tracked[doc.RuntimeSerialNumber] = vp.Id;
            RememberViewportCPlane(doc, vp);   // 先记住这个视口原本的平面，退出时才还原得回来
            vp.SetConstructionPlane(target);
            doc.Views.Redraw();
            return;
        }

        bool changed = ModelAidSettings.AutoAlignCPlane ||
            !ModelAidSettings.GumballAutoReset || !GumballSettings.EnableGumball ||
            GumballSettings.AutoGumballAlignment != GumballAlignment.ConstructionPlane ||
            ModelAidSettings.UniversalConstructionPlaneMode;
        if (changed) AcquireGlobalSettings(doc, vp);
        if (!vp.ConstructionPlane().EpsilonEquals(target, 1e-10))
        {
            vp.SetConstructionPlane(target);
            changed = true;
        }
        if (changed) doc.Views.Redraw();
    }

    private static void AcquireGlobalSettings(RhinoDoc doc, RhinoViewport vp)
    {
        StartWatching();
        if (owner != doc.RuntimeSerialNumber || ownerView != vp.Id)
        {
            ReleaseGlobalSettings();
            baseline = new GlobalSettings();
            owner = doc.RuntimeSerialNumber;
            ownerView = vp.Id;
        }
        // Prevent automatic CPlane switching and cross-viewport propagation.
        ModelAidSettings.UniversalConstructionPlaneMode = false;
        ModelAidSettings.AutoAlignCPlane = false;
        ModelAidSettings.GumballAutoReset = true;
        GumballSettings.EnableGumball = true;
        GumballSettings.AutoGumballAlignment = GumballAlignment.ConstructionPlane;
    }

    private static void ReleaseGlobalSettings()
    {
        baseline?.Restore();
        baseline = null; owner = 0; ownerView = Guid.Empty;
    }

    internal static string ReadString(RhinoDoc doc, string key) => doc.Strings.GetValue(Section, key) ?? "";
    internal static void WriteString(RhinoDoc doc, string key, string value) => doc.Strings.SetString(Section, key, value);
    private static string Read(RhinoDoc doc, string key) => ReadString(doc, key);
    private static void Write(RhinoDoc doc, string key, string value) => WriteString(doc, key, value);
    private static void Clear(RhinoDoc doc) { foreach (var key in Keys) doc.Strings.Delete(Section, key); }

    public static bool IsActive(RhinoDoc? doc) => doc != null && Read(doc, "Active") == "1";
    public static Result Toggle(RhinoDoc doc, Plane plane) => IsActive(doc) ? Deactivate(doc) : Create(doc, plane);
    public static Result Create(RhinoDoc doc, Plane plane) => Create(doc, plane, out _);

    public static Result Create(RhinoDoc doc, Plane plane, out Guid datumId)
    {
        datumId = Guid.Empty;
        var vp = doc?.Views.ActiveView?.ActiveViewport;
        if (doc == null || vp == null || !plane.IsValid) return Fail("没有活动视图或基准面无效 / No active view or invalid plane.");
        // v1.6：激活态下允许直接定义新基准面 —— 走「切换」路径并保留最初的恢复基线，
        // 不再用 "已有基准面，请先还原" 把用户卡死。
        var previous = vp.ConstructionPlane(); // Read before changing ANY state.
        var name = NextName(doc);
        var half = ComputeDatumSideLength(doc, plane.Origin) * 0.5;
        using var surface = new PlaneSurface(plane, new Interval(-half, half), new Interval(-half, half));
        using var brep = surface.ToBrep();
        if (brep == null || !brep.IsValid) return Fail("无法生成基准面矩形 / Cannot create datum rectangle.");
        // v1.2：每个基准面独占一个编号子图层。此时子图层是"未锁定"的，
        // 保证下面任何一步失败都不会留下一个锁死的空图层。
        int layer = DatumPlaneLayers.CreateNumberedSubLayer(doc, out string subLayerName);
        if (layer < 0) return Result.Failure;
        int material = EnsureTransparentMaterial(doc);
        if (material < 0) { CleanupEmptySubLayer(doc, layer); return Fail("半透明材质设置失败，已停止 / Transparent material failed; creation aborted."); }
        using var attr = new ObjectAttributes { LayerIndex = layer, Name = name,
            MaterialIndex = material, MaterialSource = ObjectMaterialSource.MaterialFromObject };
        // 只存"名字"这一处元数据：平面坐标由 NamedConstructionPlanes 统一管理，
        // 不在几何上再存一份 9 个 double，避免两处数据不一致。
        attr.SetUserString(DatumPlaneLayers.KindKey, DatumPlaneLayers.ReferenceKind);
        attr.SetUserString(DatumPlaneLayers.NameKey, name);
        attr.SetUserString(DatumPlaneLayers.LayerKey, subLayerName);
        // v1.3：虚线边线 + Ghosted 显示覆盖。线框视口下材质透明度不生效，
        // 必须靠这两样才能和普通平面区分开。
        DatumPlaneLayers.ApplyDatumAppearance(doc, attr);
        datumId = doc.Objects.AddBrep(brep, attr);
        if (datumId == Guid.Empty)
        {
            CleanupEmptySubLayer(doc, layer);
            return Fail("基准面对象添加失败 / Failed to add datum object.");
        }
        int namedIndex = doc.NamedConstructionPlanes.Add(name, plane);
        if (namedIndex < 0)
        {
            doc.Objects.Delete(datumId, true); datumId = Guid.Empty;
            CleanupEmptySubLayer(doc, layer);
            return Fail("命名基准面保存失败，已撤销 / Named CPlane save failed; geometry rolled back.");
        }
        // v1.6 核心修复：已激活时「切换」而非「拒绝」，ActivePlane 基线保持不变。
        var result = IsActive(doc)
            ? SwitchTo(doc, vp, plane, name)
            : Activate(doc, vp, plane, previous, name);
        if (result != Result.Success)
        {
            doc.NamedConstructionPlanes.Delete(namedIndex);
            doc.Objects.Delete(datumId, true); datumId = Guid.Empty;
            CleanupEmptySubLayer(doc, layer);
        }
        else
        {
            // 全部成功后才锁定：命令点选时用 GetObject.LockedObjectSelect 仍可拾取。
            DatumPlaneLayers.LockSubLayer(doc, layer);
            RhinoApp.WriteLine("已创建并保存 {0}（子图层 {1} 已锁定）/ Created and saved {0} (sublayer {1} locked); pick old datum to switch, run DatumPlane to restore.", name, subLayerName);
        }
        return result;
    }

    /// <summary>
    /// 创建失败时清掉刚建的空子图层。只删"本插件标记过且确实没有任何对象"的层，
    /// 绝不碰用户自己的图层；删除前再确认一次引用计数。
    /// </summary>
    private static void CleanupEmptySubLayer(RhinoDoc doc, int layerIndex)
    {
        if (layerIndex < 0 || layerIndex >= doc.Layers.Count) return;
        Layer? candidate = doc.Layers[layerIndex];
        if (candidate == null || candidate.GetUserString(DatumPlaneLayers.KindKey) != DatumPlaneLayers.LayerKind) return;
        foreach (var obj in doc.Objects)
        {
            if (!obj.IsDeleted && obj.Attributes.LayerIndex == layerIndex) return; // 有对象，保留
        }
        doc.Layers.Delete(layerIndex, true);
    }

    private static Result Activate(RhinoDoc doc, RhinoViewport vp, Plane plane, Plane previous, string name)
    {
        try
        {
            Write(doc, "ActivePlane", SerializePlane(previous));
            Write(doc, "ViewportId", vp.Id.ToString("D"));
            Write(doc, "LockedPlane", SerializePlane(plane));
            Write(doc, "SavedName", name);
            Write(doc, "Version", "2");
            AcquireGlobalSettings(doc, vp);
            RememberViewportCPlane(doc, vp);   // 这个视口的原平面（此前若已记录则不覆盖）
            vp.SetConstructionPlane(plane);
            Write(doc, "Active", "1"); // Commit marker last.
            Tracked[doc.RuntimeSerialNumber] = vp.Id;
            doc.Views.Redraw();
            DatumPlaneNormalView.Refresh(doc); // 若第 5 视口已存在，自动对齐到首个基准面
            return Result.Success;
        }
        catch (Exception ex)
        {
            // Restore while universal CPlanes are still disabled.
            vp.SetConstructionPlane(previous);
            ReleaseGlobalSettings(); Clear(doc); ClearCPlaneRecords(doc); Tracked.Remove(doc.RuntimeSerialNumber);
            return Fail("启用失败 / Activation failed: " + ex.Message);
        }
    }

    /// <summary>
    /// v1.6：已激活状态下切换到另一个基准面（新建、Recall、Lock 共用）。
    /// 绝不覆盖 ActivePlane —— 那是「进入模式前」的唯一恢复基线。
    /// 只更新当前锁定平面、名称、所属视口，并让法向视图跟随。
    /// </summary>
    private static Result SwitchTo(RhinoDoc doc, RhinoViewport vp, Plane plane, string name)
    {
        try
        {
            AcquireGlobalSettings(doc, vp);   // 顺带把 owner 迁移到当前视口
            RememberViewportCPlane(doc, vp);  // 切平面也是改写，先存原平面
            vp.SetConstructionPlane(plane);
            Write(doc, "LockedPlane", SerializePlane(plane));
            Write(doc, "SavedName", name);
            Write(doc, "ViewportId", vp.Id.ToString("D"));
            Write(doc, "Version", "2");
            Tracked[doc.RuntimeSerialNumber] = vp.Id;
            doc.Views.Redraw();
            DatumPlaneNormalView.Refresh(doc);
            return Result.Success;
        }
        catch (Exception ex)
        {
            return Fail("切换基准面失败 / Failed to switch datum: " + ex.Message);
        }
    }

    public static Result Recall(RhinoDoc doc, string name)
    {
        int index = doc.NamedConstructionPlanes.Find(name);
        if (index < 0) return Fail("找不到所保存的基准面 / Saved datum not found.");
        var plane = doc.NamedConstructionPlanes[index].Plane;
        var vp = doc.Views.ActiveView?.ActiveViewport;
        if (vp == null || !plane.IsValid) return Fail("保存的基准面或当前视图无效 / Saved datum or active view invalid.");
        // v1.6：不再要求「切回启用时的视口」。任意视口（含第 5 法向视图）都能切换。
        return IsActive(doc)
            ? SwitchTo(doc, vp, plane, name)
            : Activate(doc, vp, plane, vp.ConstructionPlane(), name);
    }

    public static Result Lock(RhinoDoc doc)
    {
        var vp = doc.Views.ActiveView?.ActiveViewport;
        if (vp == null) return Result.Failure;
        if (!IsActive(doc)) return Fail("请先创建或调用一个基准面 / Create or recall a datum first.");
        if (!TryDeserializePlane(Read(doc, "LockedPlane"), out var plane))
            return Fail("旧版未记录锁定平面，请先还原再重试 / Legacy file has no locked plane; restore then pick again.");
        var result = SwitchTo(doc, vp, plane, Read(doc, "SavedName"));
        if (result == Result.Success)
            RhinoApp.WriteLine("方向已锁定到基准面；换选物体、旋转完成后继续使用该方向 / Axes locked to datum; keep this direction when selecting or rotating other objects.");
        return result;
    }

    public static Result Deactivate(RhinoDoc doc)
    {
        if (doc == null) return Result.Failure;
        // v2.5：模式已关闭时不再只是"什么都不做"。
        // 旧版遗留的倾斜 CPlane 就是在这条路径上永久留在 Front 视图里的，
        // 所以这里补一次自愈：只矫正"CPlane 还是某个基准面"的视口，绝不碰用户自己的平面。
        if (!IsActive(doc))
        {
            int healed = RepairLeakedCPlanes(doc);
            if (healed > 0)
            {
                ClearCPlaneRecords(doc);
                doc.Views.Redraw();
                RhinoApp.WriteLine("当前没有启用基准面模式；已把 {0} 个视图的工作平面矫正回标准朝向 / Datum mode is not active; {0} viewport CPlane(s) reset to standard.", healed);
            }
            else
            {
                RhinoApp.WriteLine("当前没有启用基准面模式 / Datum mode is not active.");
            }
            return Result.Nothing;
        }
        var vp = doc.Views.ActiveView?.ActiveViewport;
        if (vp == null) return Fail("没有活动视图，原状态已保留，稍后重试 / No active view; original state kept, retry later.");
        if (!TryDeserializePlane(Read(doc, "ActivePlane"), out var previous)) return CorruptState();
        bool legacy = Read(doc, "Version") != "2";
        var records = ReadCPlaneRecords(doc);
        bool universal = ModelAidSettings.UniversalConstructionPlaneMode;
        bool autoAlign = ModelAidSettings.AutoAlignCPlane;
        // This method only writes viewports, never other documents' state.
        // AutoAlignCPlane 也临时关掉：否则还原过程中的视图变化可能反过来把 CPlane 贴合到视图上。
        ModelAidSettings.UniversalConstructionPlaneMode = false;
        ModelAidSettings.AutoAlignCPlane = false;
        int restored = 0;
        try
        {
            var done = new HashSet<Guid>();
            foreach (var rec in records)
            {
                var view = doc.Views.Find(rec.Id) ?? FindViewByName(doc, rec.Name, done);
                if (view == null) continue;
                var target = view.ActiveViewport;
                if (IsNormalView(target)) continue;   // 第 5 视窗刻意贴在基准面上，不动
                if (!target.ConstructionPlane().EpsilonEquals(rec.Plane, 1e-10))
                {
                    target.SetConstructionPlane(rec.Plane);
                    restored++;
                }
                done.Add(target.Id);
            }
            // 旧文件（无逐视口记录）与"记录丢失"的兜底：至少把活动视口还原成进入前的平面。
            if (!done.Contains(vp.Id) && !IsNormalView(vp))
            {
                vp.SetConstructionPlane(previous);
                restored++;
            }
            // 旧版只记了一个 ViewportId；该视口若没被上面的记录覆盖，也还原掉。
            if (Guid.TryParse(Read(doc, "ViewportId"), out var ownerId) && ownerId != vp.Id)
            {
                var ownerView = doc.Views.Find(ownerId);
                if (ownerView != null && !done.Contains(ownerId) && !IsNormalView(ownerView.ActiveViewport))
                {
                    ownerView.ActiveViewport.SetConstructionPlane(previous);
                    restored++;
                }
            }
            // 最后兜底自愈：清掉任何仍残留着基准面 CPlane 的视口（旧会话记录不全时的情况）。
            restored += RepairLeakedCPlanes(doc);
        }
        finally
        {
            ModelAidSettings.UniversalConstructionPlaneMode = universal;
            ModelAidSettings.AutoAlignCPlane = autoAlign;
        }
        if (owner == doc.RuntimeSerialNumber) ReleaseGlobalSettings();
        // Old files have no accurate prior global settings. Keep today's preferences.
        Clear(doc); ClearCPlaneRecords(doc); Tracked.Remove(doc.RuntimeSerialNumber);
        doc.Views.Redraw();
        RhinoApp.WriteLine("已还原 {0} 个视图的原构造平面，退出方向锁定；保存的基准面保留 / Restored original CPlane on {0} viewport(s), axes unlocked; saved datums retained.", restored);
        if (legacy) RhinoApp.WriteLine("旧版未保存原操作轴设置和视口平面记录；本次按标准视图朝向矫正 / Legacy file had no per-viewport record; standard view orientations were restored instead.");
        return Result.Success;
    }

    /// <summary>
    /// v2.5 自愈：把所有「CPlane 仍然等于某个基准面」的视口矫正回该视图自己的朝向。
    /// 判据刻意很窄 —— 只有平面上确实是本插件/用户保存的基准面才动手，
    /// 因此不会覆盖用户手工设定的工作平面。返回被矫正的视口数量。
    /// </summary>
    private static int RepairLeakedCPlanes(RhinoDoc doc)
    {
        var datumPlanes = CollectDatumPlanes(doc);
        if (datumPlanes.Count == 0) return 0;
        int healed = 0;
        foreach (var view in doc.Views)
        {
            var vp = view.ActiveViewport;
            if (vp == null || IsNormalView(vp)) continue;
            Plane current = vp.ConstructionPlane();
            bool leaked = false;
            foreach (var candidate in datumPlanes)
            {
                if (current.EpsilonEquals(candidate, 1e-8)) { leaked = true; break; }
            }
            if (!leaked) continue;
            Plane canonical = CanonicalPlane(vp);
            if (current.EpsilonEquals(canonical, 1e-6)) continue;
            vp.SetConstructionPlane(canonical);
            healed++;
        }
        return healed;
    }

    /// <summary>本插件管过的平面：当前锁定的、进入模式前的、以及所有命名基准面。</summary>
    private static List<Plane> CollectDatumPlanes(RhinoDoc doc)
    {
        var planes = new List<Plane>();
        if (TryDeserializePlane(Read(doc, "LockedPlane"), out var locked)) planes.Add(locked);
        if (TryDeserializePlane(Read(doc, "ActivePlane"), out var home)) planes.Add(home);
        foreach (var named in doc.NamedConstructionPlanes)
        {
            if (named != null && named.Plane.IsValid) planes.Add(named.Plane);
        }
        return planes;
    }

    /// <summary>
    /// 由视口相机反推"这个视图本来该有的 CPlane"：X = 相机方向 × 上方向、Y = 上方向。
    /// 实测与 Rhino 原生一致：Front → X=(1,0,0) Y=(0,0,1) Z=(0,-1,0)；Top → WorldXY；Right → X=(0,1,0) Y=(0,0,1)。
    /// 透视视口没有"标准朝向"，回落到 WorldXY。
    /// </summary>
    private static Plane CanonicalPlane(RhinoViewport vp)
    {
        if (vp.IsParallelProjection)
        {
            var dir = vp.CameraDirection;
            var up = vp.CameraUp;
            if (dir.Unitize() && up.Unitize())
            {
                var x = Vector3d.CrossProduct(dir, up);
                if (x.Unitize() && Math.Abs(Vector3d.Multiply(x, up)) < 1e-9)
                    return new Plane(Point3d.Origin, x, up);
            }
        }
        return Plane.WorldXY;
    }

    private static bool IsNormalView(RhinoViewport vp) => vp != null && vp.Name == DatumPlaneNormalView.ViewName;

    /// <summary>文件重开后视口 Id 可能变，退一步用唯一的视口名找回同一个视口。</summary>
    private static RhinoView? FindViewByName(RhinoDoc doc, string name, HashSet<Guid> skip)
    {
        if (string.IsNullOrEmpty(name)) return null;
        RhinoView? found = null;
        foreach (var view in doc.Views)
        {
            var vp = view.ActiveViewport;
            if (vp == null || skip.Contains(vp.Id) || !string.Equals(vp.Name, name, StringComparison.Ordinal)) continue;
            if (found != null) return null;   // 名字不唯一（例如两个 Top），宁可不猜
            found = view;
        }
        return found;
    }

    /// <summary>记下视口被本插件改写之前的 CPlane；同一视口只记第一次。</summary>
    internal static void RememberViewportCPlane(RhinoDoc doc, RhinoViewport vp)
    {
        if (doc == null || vp == null) return;
        if (IsNormalView(vp)) return;   // 第 5 视窗的 CPlane 本来就该贴基准面，退出时保留
        var records = ReadCPlaneRecords(doc);
        foreach (var rec in records) if (rec.Id == vp.Id) return;
        Plane plane = vp.ConstructionPlane();
        if (!plane.IsValid) return;
        records.Add(new CPlaneRecord { Id = vp.Id, Name = vp.Name ?? "", Plane = plane });
        WriteCPlaneRecords(doc, records);
    }

    private static List<CPlaneRecord> ReadCPlaneRecords(RhinoDoc doc)
    {
        var records = new List<CPlaneRecord>();
        string raw = Read(doc, CPlaneMapKey);
        if (raw.Length == 0) return records;
        foreach (string entry in raw.Split(RecordSep))
        {
            if (entry.Length == 0) continue;
            string[] parts = entry.Split(FieldSep);
            if (parts.Length < 3) continue;
            if (!Guid.TryParse(parts[0], out var id)) continue;
            if (!TryDeserializePlane(parts[2], out var plane)) continue;
            records.Add(new CPlaneRecord { Id = id, Name = parts[1], Plane = plane });
        }
        return records;
    }

    private static void WriteCPlaneRecords(RhinoDoc doc, List<CPlaneRecord> records)
    {
        if (records.Count == 0) { doc.Strings.Delete(Section, CPlaneMapKey); return; }
        var text = new StringBuilder();
        foreach (var rec in records)
        {
            if (text.Length > 0) text.Append(RecordSep);
            text.Append(rec.Id.ToString("D")).Append(FieldSep)
                .Append(rec.Name).Append(FieldSep)
                .Append(SerializePlane(rec.Plane));
        }
        Write(doc, CPlaneMapKey, text.ToString());
    }

    private static void ClearCPlaneRecords(RhinoDoc doc) => doc.Strings.Delete(Section, CPlaneMapKey);

    private static Result CorruptState() => Fail("原平面记录无效，未改动 CPlane / Invalid saved plane; CPlane unchanged, check document strings.");
    private static Result Fail(string message) { RhinoApp.WriteLine(message); return Result.Failure; }

    /// <summary>取当前生效的基准面：优先锁定平面，退化到已保存的命名平面。</summary>
    internal static bool TryGetActiveDatumPlane(RhinoDoc doc, out Plane plane)
    {
        plane = Plane.Unset;
        if (TryDeserializePlane(Read(doc, "LockedPlane"), out plane)) return true;
        string name = Read(doc, "SavedName");
        if (name.Length == 0) return false;
        int index = doc.NamedConstructionPlanes.Find(name);
        if (index < 0) return false;
        plane = doc.NamedConstructionPlanes[index].Plane;
        return plane.IsValid;
    }

    /// <summary>取当前基准面矩形的世界包围盒，供法向视图 ZoomBoundingBox 使用。</summary>
    internal static bool TryGetActiveDatumBoundingBox(RhinoDoc doc, out BoundingBox box)
    {
        box = BoundingBox.Unset;
        string name = Read(doc, "SavedName");
        if (name.Length == 0) return false;
        foreach (var obj in doc.Objects)
        {
            if (obj.IsDeleted) continue;
            if (obj.Attributes.GetUserString(DatumPlaneLayers.KindKey) != DatumPlaneLayers.ReferenceKind) continue;
            if (obj.Attributes.GetUserString(DatumPlaneLayers.NameKey) != name) continue;
            box = obj.Geometry.GetBoundingBox(false);
            return box.IsValid;
        }
        return false;
    }

    public static string NextName(RhinoDoc doc)
    {
        for (int n = 1; n < int.MaxValue; n++)
        {
            string name = "基准面_" + n.ToString("D3", CultureInfo.InvariantCulture);
            if (doc.NamedConstructionPlanes.Find(name) < 0) return name;
        }
        return "基准面_" + Guid.NewGuid().ToString("N");
    }

    public static Result SaveCurrent(RhinoDoc doc, string name)
    {
        var vp = doc.Views.ActiveView?.ActiveViewport;
        if (vp == null) return Result.Failure;
        name = name.Trim();
        if (name.Length == 0) name = NextName(doc);
        if (doc.NamedConstructionPlanes.Find(name) >= 0) return Fail("名称已存在，请换一个 / Name exists; pick another (existing datum not overwritten).");
        var plane = vp.ConstructionPlane();
        if (!plane.IsValid || doc.NamedConstructionPlanes.Add(name, plane) < 0) return Fail("保存失败 / Save failed.");
        RhinoApp.WriteLine("已保存工作平面：{0}。使用 DatumPlaneRecall 调用 / Saved CPlane: {0}. Use DatumPlaneRecall to retrieve.", name);
        return Result.Success;
    }

    public static string SerializePlane(Plane plane)
    {
        if (!plane.IsValid) return "";
        return string.Format(CultureInfo.InvariantCulture,
            "{0:R},{1:R},{2:R};{3:R},{4:R},{5:R};{6:R},{7:R},{8:R}",
            plane.OriginX, plane.OriginY, plane.OriginZ,
            plane.XAxis.X, plane.XAxis.Y, plane.XAxis.Z, plane.YAxis.X, plane.YAxis.Y, plane.YAxis.Z);
    }

    public static bool TryDeserializePlane(string? text, out Plane plane)
    {
        plane = Plane.Unset;
        if (!PlaneText.TryRead(text, out var v)) return false;
        plane = new Plane(new Point3d(v[0], v[1], v[2]), new Vector3d(v[3], v[4], v[5]), new Vector3d(v[6], v[7], v[8]));
        return plane.IsValid;
    }

    public static int EnsureTransparentMaterial(RhinoDoc doc)
    {
        int index = doc.Materials.Find(MaterialName, true);
        using var material = index >= 0 ? new Material(doc.Materials[index]) : new Material { Name = MaterialName };
        material.DiffuseColor = DatumColor;
        material.Transparency = DatumTransparency;
        if (index < 0) return doc.Materials.Add(material);
        return doc.Materials.Modify(material, index, true) ? index : -1;
    }

    public static int EnsureLayer(RhinoDoc doc)
    {
        // Find the TOP-LEVEL layer; another branch can have the same leaf name.
        foreach (Layer layer in doc.Layers)
        {
            if (layer.IsDeleted || layer.ParentLayerId != Guid.Empty || layer.Name != LayerName) continue;
            if (layer.IsLocked || !layer.IsVisible || layer.IsReference)
            {
                Fail("“基准面”图层被锁定/隐藏/引用，请在图层面板调整后重试 / Root layer is locked, hidden or referenced; fix it in Layers panel.");
                return -1;
            }
            return layer.Index;
        }
        using var created = new Layer { Name = LayerName, Color = DatumColor };
        return doc.Layers.Add(created);
    }

    public static double ComputeDatumSideLength(RhinoDoc doc) =>
        ComputeDatumSideLength(doc, doc.Views.ActiveView?.ActiveViewport.CameraTarget ?? Point3d.Origin);

    private static double ComputeDatumSideLength(RhinoDoc doc, Point3d origin)
    {
        const double fallback = 100.0;
        var vp = doc.Views.ActiveView?.ActiveViewport;
        if (vp == null) return fallback;
        using var info = new ViewportInfo(vp);
        if (!info.GetFrustum(out var left, out var right, out _, out _, out var near, out _)) return fallback;
        double width = right - left;
        if (info.IsPerspectiveProjection)
        {
            var forward = info.CameraDirection;
            if (!forward.Unitize() || !double.IsFinite(near) || near <= 0) return fallback;
            // Axial depth at the datum, not off-axis Euclidean camera-target distance.
            double depth = (origin - info.CameraLocation) * forward;
            if (!double.IsFinite(depth) || depth <= 0) return fallback;
            width *= depth / near;
        }
        return double.IsFinite(width) && width > 0 ? Math.Max(width * ViewWidthRatio, doc.ModelAbsoluteTolerance * 10) : fallback;
    }
}
