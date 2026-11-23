using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using Rhino;
using Rhino.Commands;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Input;
using Rhino.Input.Custom;

namespace DatumPlanePlugin;

/// <summary>
/// Alias 建模风格的观测显示（v2.6：方向光三度灰阶 + 等参线 + 轮廓线）。
///
/// 为什么要重做：v2.4 走的是 Rhino 内置 **Arctic（极地）** 那条路 —— 纯
/// AmbientOcclusion。官方对 Arctic 的定义是"全白 + 柔和阴影"，它只有接触/凹角遮蔽，
/// 没有受光面、侧光面、背光面的明暗梯度，所以曲面会"糊成一片，没有明暗灰三度"。
/// 官方 **Monochrome（单色）** 的定义恰好是"白色物件 + 灰度明暗 + 黑色轮廓"，
/// 社区（NOVEDGE 的 display-mode / white-model 指南）也一致强调：看形体靠的是
/// 方向光带来的高光—中间调—暗部，而不是把 AO 堆满。
///
/// 实机反射结论（Rhino 9）：
///  * LightingSchema 是枚举不是 flag（None/Default/Scene/Custom/AmbientOcclusion），
///    "DefaultLighting | AmbientOcclusion" 是无效值，AO 与方向光只能二选一。
///  * Shaded 用 CustomLighting（多盏方向光），Arctic 用 AmbientOcclusion，
///    Monochrome 用 SceneLighting（白模但 FrontDiffuse 255，会过曝）。
///  * 真正能改物体亮度的不是 FrontDiffuse / ObjectColor，而是
///    UseCustomObjectMaterial = true + FrontMaterial.Diffuse（v2.4 漏试了这一对）。
///
/// v2.6 配方：以 Shaded 为母版 → CustomLighting（方向光给三度）+
/// 中灰 albedo（把最亮面压在 255 以下）+ 低环境光（暗部不死黑）+
/// IgnoreHighlights / Shine=0（去掉刺眼高光）+ 等参线 + 轮廓线。
/// 刻意**关掉投影阴影**：CustomLighting 下地面投影会被拉成大片深色椭圆，
/// 实测比没有阴影更抢视线（E/G 组），三度灰阶本身已经足够表达体积。
///
/// 实测坑 1：SetSurfaceIsoColorUsage() 会把 SurfaceIsoColorsUsed 重置为 false，
///           所以总开关必须在它之后赋值，否则等参线一直用默认黑色。
/// 实测坑 2：只设 SurfaceIsoUVColor 不够 —— 从 Shaded 继承的模式 U 红 V 绿，
///           必须把 SurfaceIsoUColor / VColor 也赋成同色，否则曲面上一片红绿经线。
/// 实测坑 3：UseCustomObjectColor 必须在 ObjectColor 之后写，顺序反了会被静默重置。
/// </summary>
internal static class AliasStyle
{
    public const string LightName = "Alias EyeCare";
    public const string DarkName = "Alias EyeCare Dark";

    /// 原显示模式记录（每个视口一行 "视口Id=模式Id=网格=轴;"），用于精确还原。
    public const string SaveKey = "DatumPlane.AliasStyle.Original";
    /// v2.10：被我们实际改过模式的视口 Id 列表（"id;id;"）。
    /// Restore 只还原这些 —— 用户自己手动切过的其他视口不该被我们抹掉。
    public const string TouchedKey = "DatumPlane.AliasStyle.Touched";
    /// 当前启用的是哪套：Light / Dark。
    public const string ActiveKey = "DatumPlane.AliasStyle.Active";

    private readonly struct Palette
    {
        public readonly Color BgTop;
        public readonly Color BgBottom;
        public readonly Color Surface;
        public readonly Color Ambient;
        public readonly Color Iso;
        public readonly Color Edge;
        public readonly Color Curve;
        public readonly Color Grid;

        public Palette(Color bgTop, Color bgBottom, Color surface, Color ambient,
                       Color iso, Color edge, Color curve, Color grid)
        {
            BgTop = bgTop;
            BgBottom = bgBottom;
            Surface = surface;
            Ambient = ambient;
            Iso = iso;
            Edge = edge;
            Curve = curve;
            Grid = grid;
        }
    }

    // v2.6 定稿（逐像素扫描 4 组 albedo × 环境光 + 阴影/深色对照后选中）：
    //   albedo 0xC0 / ambient 0x0A 的物体区间 P10=101 / P50=119 / P90=152，
    //   三度跨度 51、纯白像素 0.00%；albedo 0x90 太闷、ambient 0x22 又把层次抹平。
    //   背景压到 #B9BEC2→#8F979C（比物体亮面暗），白模才不会和背景糊在一起。
    private static readonly Palette Light = new Palette(
        Color.FromArgb(0xB9, 0xBE, 0xC2), Color.FromArgb(0x8F, 0x97, 0x9C),
        Color.FromArgb(0xC0, 0xC0, 0xC0), Color.FromArgb(0x0A, 0x0A, 0x0A),
        Color.FromArgb(0x50, 0x5C, 0x66), Color.FromArgb(0x2B, 0x2B, 0x2B),
        Color.FromArgb(0x2B, 0x2B, 0x2B), Color.FromArgb(0x8A, 0x8A, 0x8A));

    // 深色：石墨底 + 略暗一点的物体（0xA8），三度依旧清楚，夜里不刺眼。
    private static readonly Palette Dark = new Palette(
        Color.FromArgb(0x2B, 0x31, 0x34), Color.FromArgb(0x3C, 0x44, 0x48),
        Color.FromArgb(0xA8, 0xA8, 0xA8), Color.FromArgb(0x0A, 0x0A, 0x0A),
        Color.FromArgb(0x8F, 0xA8, 0xB4), Color.FromArgb(0xB2, 0xBC, 0xC2),
        Color.FromArgb(0x9E, 0xD8, 0xC6), Color.FromArgb(0x5A, 0x64, 0x68));

    // 注意：StringTable 的 GetValue(string, string) 是 (section, entry)，
    // 不是 (key, defaultValue)。写入用的是无 section 的 SetString(key, value)，
    // 所以读取必须用单参数 GetValue(key)，否则永远读不到。
    public static bool IsActive(RhinoDoc doc) =>
        !string.IsNullOrEmpty(doc.Strings.GetValue(ActiveKey));

    public static string ActiveFlavour(RhinoDoc doc) =>
        doc.Strings.GetValue(ActiveKey) ?? string.Empty;

    /// <summary>找到或创建（并刷新参数）指定主题的显示模式。</summary>
    public static DisplayModeDescription? EnsureMode(bool dark)
    {
        string name = dark ? DarkName : LightName;

        DisplayModeDescription? mode = null;
        try { mode = DisplayModeDescription.FindByName(name); }
        catch { mode = null; }

        // 已存在的旧版本模式必须**删掉重建**，不能原地 UpdateDisplayMode：
        // 实测对已注册的模式调用 UpdateDisplayMode 会返回 false 且参数不落盘 ——
        // 结果就是升级后名字一样、观感还是老样子（v2.4 踩过：深色版背景一直是旧的浅灰）。
        if (mode != null)
        {
            try
            {
                DisplayModeDescription.DeleteDisplayMode(mode.Id);
                mode = null;
                DisplayModeDescription.SaveDisplayModes();
            }
            catch { mode = null; }
        }

        {
            // v2.6 母版换成 Shaded：它自带 CustomLighting 的多盏方向光，
            // 而 Alias Style / Arctic 分别是 DefaultLighting / AmbientOcclusion，
            // 从它们复制会丢掉"三度灰阶"的光源配置。
            DisplayModeDescription? basis = null;
            try { basis = DisplayModeDescription.FindByName("Shaded"); }
            catch { basis = null; }
            if (basis == null)
                basis = DisplayModeDescription.GetDisplayMode(DisplayModeDescription.ShadedId);
            if (basis == null) return null;

            Guid created = DisplayModeDescription.CopyDisplayMode(basis.Id, name);
            if (created == Guid.Empty) return null;
            mode = DisplayModeDescription.GetDisplayMode(created);
            if (mode == null) return null;
        }

        Configure(mode.DisplayAttributes, dark);
        mode.InMenu = true;

        // 返回 false 只表示"参数无变化、无需更新"，不是失败：
        // 实测同一模式重复应用时 UpdateDisplayMode 恒返回 false，但参数本身是有效的。
        DisplayModeDescription.UpdateDisplayMode(mode, true);
        DisplayModeDescription.SaveDisplayModes();
        return DisplayModeDescription.GetDisplayMode(mode.Id) ?? mode;
    }

    private static void Configure(DisplayPipelineAttributes a, bool dark)
    {
        Palette p = dark ? Dark : Light;

        // —— 背景：低饱和双色渐变，护眼的关键 ——
        a.FillMode = DisplayPipelineAttributes.FrameBufferFillMode.Gradient2Color;
        a.SetFill(p.BgTop, p.BgBottom);

        // —— 着色：方向光三度灰阶（亮面 / 中间调 / 暗面），不是纯 AO 白模 ——
        a.ShadingEnabled = true;
        // CustomLighting = Shaded 母版自带的多盏方向光，曲面法线不同 → 明暗连续过渡。
        // AmbientOcclusion（v2.4）只有接触遮蔽，曲面没有受光/背光之差，所以"糊成一片"。
        a.LightingScheme = DisplayPipelineAttributes.LightingSchema.CustomLighting;
        a.AmbientLightingColor = p.Ambient;   // 环境光只兜住暗部，压很低才有三度
        // albedo 是唯一真正能改物体亮度的旋钮：UseCustomObjectMaterial + FrontMaterial.Diffuse。
        // 0xC0 时最亮面约 152，纯白像素 0.00%（旧版 AO/白材质动不动就削到 255）。
        a.UseCustomObjectMaterial = true;
        a.FrontMaterial.Diffuse = p.Surface;
        a.FrontMaterial.Shine = 0.0;
        a.FrontMaterial.ShineIntensity = 0;
        a.FrontMaterialShine = 0.0;
        a.IgnoreHighlights = true;              // 关掉镜面热点，读形体不被高光骗
        // 下面三个是兼容位：某些管线路径仍读 FrontDiffuse / ObjectColor，一起给同一灰度。
        a.FrontOverrideObjectColor = true;
        a.FrontDiffuse = p.Surface;
        a.ObjectColor = p.Surface;
        a.UseCustomObjectColor = true;
        a.CullBackfaces = false;

        // —— 不投影阴影（v2.6 的重要取舍）——
        // CustomLighting 的方向光会把地面阴影拉成大片深色椭圆，实测比没有阴影更抢视线；
        // 三度灰阶 + 轮廓线 + 等参线已经给出足够的体积与前后关系。
        a.ShadowsOn = false;
        a.CastShadows = false;
        a.CustomGroundPlaneOn = false;

        // —— 形体分离：轮廓线（灰度接近时靠这一圈线救回来）——
        a.ShowSilhouttes = true;

        // —— 曲面走向：等参线（核心）。两套主题都开，关闭后就只剩"白块"——
        a.ShowIsoCurves = true;
        a.SurfaceIsoUVColor = p.Iso;
        // U/V 也一起赋同色：从 Shaded 继承的模式 U 红 V 绿，只设 UVColor 会漏出彩色线。
        a.SurfaceIsoUColor = p.Iso;
        a.SurfaceIsoVColor = p.Iso;
        a.SurfaceIsoSingleColor = true;
        a.SurfaceIsoThickness = 1;
        a.SetSurfaceIsoThicknessUsage(
            DisplayPipelineAttributes.SurfaceIsoThicknessUse.SingleWidthForAllCurves);
        a.SetSurfaceIsoColorUsage(
            DisplayPipelineAttributes.SurfaceIsoColorUse.SingleColorForAll);
        // 必须最后赋值：上面这个 Set* 会把总开关重置为 false。
        a.SurfaceIsoColorsUsed = true;

        // —— 边缘：不画内部边线，只留裸边细线；两套主题都用单一深色，避免对象色花掉 ——
        a.ShowSurfaceEdges = true;
        a.ShowSurfaceEdge = false;
        a.ShowSurfaceNakedEdge = true;
        a.SurfaceEdgeColor = p.Edge;
        a.SurfaceEdgeColorUsage = DisplayPipelineAttributes.SurfaceEdgeColorUse.SingleColorForAll;
        a.SurfaceNakedEdgeColor = p.Edge;
        a.SurfaceNakedEdgeColorUsage = DisplayPipelineAttributes.SurfaceNakedEdgeColorUse.SingleColorForAll;
        a.SurfaceEdgeThickness = 1;
        a.SetSurfaceEdgeThicknessUsage(
            DisplayPipelineAttributes.SurfaceThicknessUse.Pixels);

        // —— 曲线：细线，单一颜色，不抢曲面 ——
        a.ShowCurves = true;
        a.UseSingleCurveColor = true;
        a.CurveColor = p.Curve;
        a.CurveThickness = 1;

        // —— 去掉多余装饰线（轮廓线保留）——
        a.ShowCreases = false;
        a.ShowSeams = false;

        // —— 构建网格压到几乎看不见 ——
        a.GridTransparency = dark ? 95 : 92;
        a.GridPlaneColor = p.Grid;

        a.ShowClippingPlanes = true;

        // 收尾补一次：整段配置里改照明方案 / 材质相关项都可能把这两个开关重置，
        // 一旦失效物体会回退到白色材质，被方向光打到 255（"一片死白"）。
        a.UseCustomObjectMaterial = true;
        a.FrontMaterial.Diffuse = p.Surface;
        a.ObjectColor = p.Surface;
        a.UseCustomObjectColor = true;
    }

    /// <summary>
    /// v2.10：**只把主题应用到当前活动视口**，其他视口一律不动（用户明确要的）。
    /// 返回改动的视口数（成功=1，无活动视口=0）。
    /// 旧版（≤v2.9）遍历 `doc.Views` 全改 —— 「四个窗口一起变」的真正来源就是这里，
    /// 不是 Rhino 的设计问题。
    /// </summary>
    public static int Apply(RhinoDoc doc, bool dark)
    {
        DisplayModeDescription? mode = EnsureMode(dark);
        if (mode == null) return 0;

        RhinoView? active = doc.Views.ActiveView;
        RhinoViewport? vp = active?.ActiveViewport;
        if (active == null || vp == null) return 0;

        // 联动若被用户打开过，程序化写 DisplayMode 会立刻把其他视口牵走 —— 必须静音。
        AliasStyleLink.Mute();
        try
        {
            // 记录所有视口的原始状态（只在第一次记录、有就不再覆盖），
            // 这样先改 Top 再改 Front 也能各自还原回原本各自的模式。
            RememberOriginal(doc);

            // v2.8：两套主题用不同密度来区分 —— 浅色 0（只显示裸边，画面最干净），
            // 深色 1（每条曲面多一条内部等参线，配深色底刚好能读曲面走向）。
            // 必须**强制设置**，否则从深色切回浅色时残留的 1 不会被降回 0。
            // 注意：WireDensity 是**对象级**属性，跨视口生效 —— 这是唯一压不住范围的一项，
            // 但它是"密度"不是"显示模式"，其他视口的模式本身不会被改。
            SetAllWireDensity(doc, dark ? 1 : 0);

            try
            {
                vp.DisplayMode = mode;
                // 构建平面网格在浅色/深色下都很抢视觉，Alias 工作区默认也没有网格。
                // 只动当前视口，并把原状态记进还原串，Restore 时一并恢复。
                vp.ConstructionGridVisible = false;
                // 世界坐标轴（红绿蓝三根线）会横穿模型，是"影棚白模"观感的最大破坏物。
                try { vp.ConstructionAxesVisible = false; } catch { }
                MarkTouched(doc, vp.Id);
                active.Redraw();
            }
            catch { return 0; }

            doc.Strings.SetString(ActiveKey, dark ? "Dark" : "Light");
            doc.Views.Redraw();
            return 1;
        }
        finally
        {
            AliasStyleLink.Unmute();
        }
    }

    /// <summary>
    /// v2.8：把所有曲面对象的 WireDensity 强制设成 target（不是"只补低值"），
    /// 这样浅色 0 / 深色 1 来回切换时两套模式的等参线密度始终各归各位。
    /// 只改显示属性，随时可用 AliasStyle → Density（菜单 K）再手动覆盖。
    /// </summary>
    private static int SetAllWireDensity(RhinoDoc doc, int target)
    {
        int changed = 0;
        var all = doc.Objects.GetObjectList(
            ObjectType.Brep | ObjectType.Surface | ObjectType.Extrusion);
        if (all == null) return 0;

        foreach (RhinoObject obj in all)
        {
            if (obj == null || obj.IsDeleted) continue;
            if (obj.Attributes.WireDensity == target) continue;
            try
            {
                obj.Attributes.WireDensity = target;
                if (obj.CommitChanges()) changed++;
            }
            catch { }
        }
        return changed;
    }

    /// <summary>首次应用前记录每个视口原本的显示模式、网格与世界轴可见性，只记一次。
    /// 格式：视口Id=模式Id=网格(0/1)=轴(0/1);</summary>
    private static void RememberOriginal(RhinoDoc doc)
    {
        string? existing = doc.Strings.GetValue(SaveKey);
        if (!string.IsNullOrEmpty(existing)) return;

        var sb = new StringBuilder();
        foreach (RhinoView view in doc.Views)
        {
            RhinoViewport? vp = view.ActiveViewport;
            if (vp == null) continue;
            Guid modeId = vp.DisplayMode?.Id ?? Guid.Empty;
            bool axes = true;
            try { axes = vp.ConstructionAxesVisible; } catch { }
            sb.Append(vp.Id.ToString("N")).Append('=')
              .Append(modeId.ToString("N")).Append('=')
              .Append(vp.ConstructionGridVisible ? '1' : '0').Append('=')
              .Append(axes ? '1' : '0').Append(';');
        }
        doc.Strings.SetString(SaveKey, sb.ToString());
    }

    /// <summary>把某个视口记进"我们改过"的名单（去重），Restore 时只碰这些视口。</summary>
    private static void MarkTouched(RhinoDoc doc, Guid viewportId)
    {
        string id = viewportId.ToString("N");
        string current = doc.Strings.GetValue(TouchedKey) ?? string.Empty;
        foreach (string part in current.Split(';', StringSplitOptions.RemoveEmptyEntries))
            if (string.Equals(part, id, StringComparison.OrdinalIgnoreCase)) return;

        doc.Strings.SetString(TouchedKey, current + id + ";");
    }

    /// <summary>
    /// v2.10：只还原**我们改过的**视口（TouchedKey 名单）。
    /// 名单为空时（例如 v2.9 及更早留下的记录）退回旧行为：凡有原模式记录的视口都还原。
    /// </summary>
    public static int Restore(RhinoDoc doc)
    {
        string? data = doc.Strings.GetValue(SaveKey);
        if (string.IsNullOrEmpty(data)) return 0;

        // 若联动被打开过，还原"各不相同的原模式"会被立即同步回上一个 —— 整段静音。
        AliasStyleLink.Mute();
        try
        {
            var map = new Dictionary<Guid, (Guid Mode, bool Grid, bool Axes)>();
            foreach (string part in data.Split(';', StringSplitOptions.RemoveEmptyEntries))
            {
                string[] seg = part.Split('=');
                if (seg.Length < 2) continue;
                if (!Guid.TryParseExact(seg[0], "N", out Guid viewId)) continue;
                if (!Guid.TryParseExact(seg[1], "N", out Guid modeId)) continue;
                bool grid = seg.Length >= 3 && seg[2] == "1";
                bool axes = seg.Length < 4 || seg[3] == "1";
                map[viewId] = (modeId, grid, axes);
            }

            var only = new HashSet<Guid>();
            string touched = doc.Strings.GetValue(TouchedKey) ?? string.Empty;
            foreach (string part in touched.Split(';', StringSplitOptions.RemoveEmptyEntries))
                if (Guid.TryParseExact(part, "N", out Guid id)) only.Add(id);

            int restored = 0;
            foreach (RhinoView view in doc.Views)
            {
                RhinoViewport? vp = view.ActiveViewport;
                if (vp == null) continue;
                if (only.Count > 0 && !only.Contains(vp.Id)) continue;
                if (!map.TryGetValue(vp.Id, out var wanted)) continue;

                DisplayModeDescription? target =
                    wanted.Mode == Guid.Empty ? null : DisplayModeDescription.GetDisplayMode(wanted.Mode);
                if (target == null)
                    target = DisplayModeDescription.GetDisplayMode(DisplayModeDescription.ShadedId);
                if (target == null) continue;

                try
                {
                    vp.DisplayMode = target;
                    vp.ConstructionGridVisible = wanted.Grid;
                    try { vp.ConstructionAxesVisible = wanted.Axes; } catch { }
                    view.Redraw();
                    restored++;
                }
                catch { }
            }

            doc.Strings.Delete(SaveKey);
            doc.Strings.Delete(TouchedKey);
            doc.Strings.Delete(ActiveKey);
            doc.Views.Redraw();
            return restored;
        }
        finally
        {
            AliasStyleLink.Unmute();
        }
    }

    /// <summary>设置曲面等参线密度：有选中就只改选中的，否则改全部。</summary>
    public static int SetDensity(RhinoDoc doc, int density)
    {
        var targets = new List<RhinoObject>();

        var selected = doc.Objects.GetSelectedObjects(false, false);
        if (selected != null)
            targets.AddRange(selected.Where(o => o != null && !o.IsDeleted));

        if (targets.Count == 0)
        {
            var all = doc.Objects.GetObjectList(
                ObjectType.Brep | ObjectType.Surface | ObjectType.Extrusion);
            if (all != null)
                targets.AddRange(all.Where(o => o != null && !o.IsDeleted));
        }

        int changed = 0;
        foreach (RhinoObject obj in targets)
        {
            try
            {
                obj.Attributes.WireDensity = density;
                if (obj.CommitChanges()) changed++;
            }
            catch { }
        }

        doc.Views.Redraw();
        return changed;
    }
}

/// <summary>命令层的双语提示与结果汇报。</summary>
internal static class AliasStyleUi
{
    public static Result ApplyAndReport(RhinoDoc doc, bool dark)
    {
        // v2.10：先记住"要作用的视口名"，供回报里说清楚是哪一个。
        string viewName = "当前视口";
        try
        {
            RhinoView? v = doc.Views.ActiveView;
            if (v != null) viewName = v.MainViewport.Name;
        }
        catch { }

        int count = AliasStyle.Apply(doc, dark);
        if (count == 0)
        {
            RhinoApp.WriteLine("显示模式应用失败（或没有活动视口），请确认 Rhino 版本 ≥ 8 / Failed to apply display mode.");
            return Result.Failure;
        }

        string name = dark ? AliasStyle.DarkName : AliasStyle.LightName;
        RhinoApp.WriteLine(
            $"已把「{name}」应用到当前视口（{viewName}），其他视口保持不变 / " +
            $"Applied '{name}' to the active viewport ({viewName}) only; other viewports untouched.");
        RhinoApp.WriteLine(
            $"方向光三度灰阶 + 等参线（亮面/中间调/暗面，纯白 0.00%）/ " +
            $"directional three-tone clay + isocurves (no 255 clipping).");
        RhinoApp.WriteLine(
            $"结构线密度已设为 { (dark ? 1 : 0) }（浅色 0=仅边界 / 深色 1=一条内部等参线）；" +
            $"密度是对象级属性、对所有视口生效，想更密可用 AliasStyle → Density（菜单 K）改 / " +
            $"Wire density set to { (dark ? 1 : 0) } (object-level, applies to all viewports); " +
            $"use AliasStyle -> Density (menu K) to override.");
        return Result.Success;
    }

    public static Result RestoreAndReport(RhinoDoc doc)
    {
        int count = AliasStyle.Restore(doc);
        if (count == 0)
        {
            RhinoApp.WriteLine("没有记录到可还原的显示模式 / Nothing to restore.");
            return Result.Nothing;
        }

        RhinoApp.WriteLine(
            $"已把 {count} 个视口还原为原显示模式 / Restored {count} viewport(s) to the previous display mode.");
        return Result.Success;
    }

    public static void Report(RhinoDoc doc)
    {
        if (!AliasStyle.IsActive(doc))
        {
            RhinoApp.WriteLine("当前：未启用 Alias 观测显示 / Alias study display is OFF.");
            return;
        }

        string flavour = AliasStyle.ActiveFlavour(doc);
        string label = flavour == "Dark" ? "深色 / Dark" : "浅色 / Light";
        RhinoApp.WriteLine($"当前：Alias 观测显示已启用（{label}）/ Alias study display is ON ({flavour}).");

        // 这里原先是 TrySilent(() => {...})。本机装了 WeaverBird，它把 Action 塞进了
        // System 命名空间，任何 Action 引用都会 CS0433（WeaverBird.Core vs CoreLib），
        // 连 System.Action 也救不了 —— 直接内联 try/catch，不引入委托最省事。
        try
        {
            DisplayModeDescription? m = AliasStyle.EnsureMode(flavour == "Dark");
            if (m != null)
            {
                DisplayPipelineAttributes a = m.DisplayAttributes;
                RhinoApp.WriteLine(
                    $"  照明={a.LightingScheme}  物体灰度={a.FrontMaterial.Diffuse}  环境光={a.AmbientLightingColor}" +
                    $"  等参线 IsoCurves={a.ShowIsoCurves}  颜色={a.SurfaceIsoUVColor}  背景={a.FillMode}");
            }
        }
        catch { }
    }

    /// <summary>等参线密度交互（v1.8 由 JzMenu 的 K_Density 统一调用）。</summary>
    internal static Result SetDensity(RhinoDoc doc)
    {
        int density = 4;
        Result rc = RhinoGet.GetInteger(
            "等参线密度 0-10（0=仅边界，4≈能看清走向）/ Isocurve density 0-10 (0=edges only, 4=clear flow)",
            true, ref density, 0, 10);
        if (rc != Result.Success) return rc;

        int changed = AliasStyle.SetDensity(doc, density);
        if (changed == 0)
        {
            RhinoApp.WriteLine("没有可设置的曲面对象 / No surfaces to update.");
            return Result.Nothing;
        }

        RhinoApp.WriteLine(
            $"已把 {changed} 个曲面的等参线密度设为 {density} / " +
            $"Set isocurve density {density} on {changed} surface(s).");
        return Result.Success;
    }

}

[CommandStyle(Style.ScriptRunner)]
public class AliasStyleCommand : Command
{
    public override string EnglishName => "AliasStyle";

    /// <summary>v1.8：菜单统一由 JzMenu 生成（I..M 字母代号 + 中文说明）。</summary>
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => JzMenu.Run(doc, JzScope.Style);
}

[CommandStyle(Style.ScriptRunner)]
public class AliasStyleLightCommand : Command
{
    public override string EnglishName => "AliasStyleLight";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        => AliasStyleUi.ApplyAndReport(doc, false);
}

[CommandStyle(Style.ScriptRunner)]
public class AliasStyleDarkCommand : Command
{
    public override string EnglishName => "AliasStyleDark";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        => AliasStyleUi.ApplyAndReport(doc, true);
}

[CommandStyle(Style.ScriptRunner)]
public class AliasStyleRestoreCommand : Command
{
    public override string EnglishName => "AliasStyleRestore";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        => AliasStyleUi.RestoreAndReport(doc);
}
