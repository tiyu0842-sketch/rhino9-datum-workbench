using System;
using System.Threading;
using Rhino;
using Rhino.Commands;
using Rhino.Display;

namespace DatumPlanePlugin;

/// <summary>
/// 全视图联动（**可选功能，默认关闭**）。
///
/// v2.10 方向纠正（E-022）：用户原话是「我只改变我在编辑的那个窗口，而不是所有的窗口
/// 一起变成那个模式」。也就是说 —— **各视口独立**才是用户要的，v2.9 把「全画布跟随」
/// 当成需求做进来、还默认开启，正好做反了。现在：
///   * 默认关：切、改显示模式只作用当前视口，与 Rhino 原生模型一致；
///   * 需要对照观察时，`AliasStyleLink`（菜单 O）可临时打开联动，再执行一次关闭。
///
/// Rhino 的模型本来就是「一个视口一份 DisplayMode」：点视口标题栏下拉、走
/// 「视图 → 显示模式」、执行 `_SetDisplayMode`，都只作用当前视口。v2.9 之前真正让
/// 四个视口一起变的是 `AliasStyle.Apply` 自己遍历了 `doc.Views`（v2.10 已改成只改
/// 活动视口），不是 Rhino 干的。
///
/// 真要做联动只能自己挂事件（实测 Rhino 9 / E-021）：
///   `DisplayPipeline.DisplayModeChanged` 是**静态事件**（`GetAddMethod().IsStatic = True`），
///   通过 API 写 `viewport.DisplayMode` 会**同步**触发，`args.Viewport` 精确指向被改的视口。
/// 三条纪律（只在开了联动时才走）：
///  1. **防重入**：同步时改其他视口会再次触发本事件 → `_busy` 闸门挡住。
///  2. **同步前先比 Id**：已经是该模式就跳过，天然收敛。
///  3. **程序化改模式必须静音**：`AliasStyle.Apply/Restore` 全程 Mute()，否则改一个视口
///     会被联动牵走，还原也还原不回去。
///
/// 开关持久化在 PersistentSettings（跨文档、跨会话）。设置键带 `.v2` 后缀：
/// v2.9 已把旧键写成 true，换键才能保证升级后真的是关的。
/// </summary>
internal static class AliasStyleLink
{
    private const string SettingKey = "DatumPlane.AliasStyle.LinkAllViews.v2";

    private static int _hooked;
    private static int _busy;
    private static int _mute;
    private static bool _enabled;

    public static bool Enabled => _enabled;

    /// <summary>插件 OnLoad 调用；重复调用安全。</summary>
    public static void Start()
    {
        // 注意：Rhino.PersistentSettings 的 GetBool/SetBool 是**实例方法**（CS0120 实测），
        // 全局静态入口并不存在。插件自己的 Settings 就是 PersistentSettings 实例，写在这里
        // 会落到 %AppData%\McNeel\Rhinoceros\9.0\Plug-ins\<guid>\settings 下，跨文档跨会话有效。
        // 默认 false = 各视口独立（用户要的行为）。
        try { _enabled = DatumPlanePlugin.Instance?.Settings?.GetBool(SettingKey, false) ?? false; }
        catch { _enabled = false; }

        if (Interlocked.Exchange(ref _hooked, 1) == 1) return;
        try
        {
            DisplayPipeline.DisplayModeChanged += OnDisplayModeChanged;
        }
        catch (Exception ex)
        {
            Interlocked.Exchange(ref _hooked, 0);
            RhinoApp.WriteLine("[Alias] 全视图联动挂载失败 / Failed to hook display-mode sync: " + ex.Message);
        }
    }

    public static void Stop()
    {
        if (Interlocked.Exchange(ref _hooked, 0) == 0) return;
        try { DisplayPipeline.DisplayModeChanged -= OnDisplayModeChanged; } catch { }
    }

    /// <summary>开/关切换并立即落盘，返回切换后的状态。</summary>
    public static bool Toggle()
    {
        _enabled = !_enabled;
        try { DatumPlanePlugin.Instance?.Settings?.SetBool(SettingKey, _enabled); } catch { }
        return _enabled;
    }

    /// <summary>程序化批量改显示模式前必须先 Mute，否则会被自己同步回去。</summary>
    internal static void Mute() => Interlocked.Increment(ref _mute);

    internal static void Unmute()
    {
        if (Volatile.Read(ref _mute) > 0) Interlocked.Decrement(ref _mute);
    }

    internal static bool Muted => Volatile.Read(ref _mute) > 0;

    /// <summary>
    /// 把 doc 内所有视口同步成 modeId，跳过 sourceViewportId 与已经是该模式的视口。
    /// 返回真正改动过的视口数。
    /// </summary>
    internal static int SyncTo(RhinoDoc? doc, Guid sourceViewportId, Guid modeId)
    {
        if (doc == null || modeId == Guid.Empty) return 0;

        DisplayModeDescription? mode;
        try { mode = DisplayModeDescription.GetDisplayMode(modeId); }
        catch { mode = null; }
        if (mode == null) return 0;

        int changed = 0;
        foreach (RhinoView view in doc.Views)
        {
            RhinoViewport? vp = view.ActiveViewport;
            if (vp == null) continue;
            if (vp.Id == sourceViewportId) continue;
            try
            {
                DisplayModeDescription? current = vp.DisplayMode;
                if (current != null && current.Id == modeId) continue;
                vp.DisplayMode = mode;
                view.Redraw();
                changed++;
            }
            catch { }
        }
        return changed;
    }

    /// <summary>以活动视口的显示模式为基准同步一次（打开开关时立刻对齐）。</summary>
    internal static int SyncFromActive(RhinoDoc? doc)
    {
        RhinoView? active = doc?.Views.ActiveView;
        RhinoViewport? vp = active?.ActiveViewport;
        if (vp == null) return 0;
        DisplayModeDescription? mode = vp.DisplayMode;
        if (mode == null) return 0;
        return SyncTo(doc, vp.Id, mode.Id);
    }

    private static void OnDisplayModeChanged(object? sender, DisplayModeChangedEventArgs e)
    {
        if (!_enabled || Muted) return;
        if (Interlocked.Exchange(ref _busy, 1) == 1) return;
        try
        {
            RhinoViewport? source = e.Viewport;
            if (source == null) return;
            Guid target = e.ChangedDisplayModeId;
            if (target == Guid.Empty) return;

            RhinoDoc? doc = e.RhinoDoc ?? RhinoDoc.ActiveDoc;
            int changed = SyncTo(doc, source.Id, target);
            if (changed > 0)
            {
                string name = "?";
                try { name = DisplayModeDescription.GetDisplayMode(target)?.EnglishName ?? "?"; }
                catch { }
                RhinoApp.WriteLine(
                    $"全视图联动：已把「{name}」同步到另外 {changed} 个视口 / " +
                    $"All-view sync: '{name}' applied to {changed} more viewport(s).");
            }
        }
        catch { }
        finally
        {
            Interlocked.Exchange(ref _busy, 0);
        }
    }
}

/// <summary>命令层提示。</summary>
internal static class AliasStyleLinkUi
{
    public static Result ToggleAndReport(RhinoDoc doc)
    {
        bool on = AliasStyleLink.Toggle();
        if (on)
        {
            int n = AliasStyleLink.SyncFromActive(doc);
            RhinoApp.WriteLine(
                $"全视图联动：已开启，本次把活动视口的模式对齐到另外 {n} 个视口 / " +
                $"All-view display sync ON ({n} viewport(s) aligned).");
            RhinoApp.WriteLine(
                "之后你在任意视口标题栏切显示模式，其余视口都会跟随；再执行 AliasStyleLink 可关闭 / " +
                "Switch a viewport's display mode and the others will follow; run AliasStyleLink again to turn off.");
            RhinoApp.WriteLine(
                "注意：这是可选功能，默认关闭 —— 平时各视口独立 / Note: optional, OFF by default; viewports are independent.");
        }
        else
        {
            RhinoApp.WriteLine(
                "全视图联动：已关闭（默认状态），各视口独立设置显示模式，改哪个只影响哪个 / " +
                "All-view display sync OFF (default): each viewport keeps its own display mode.");
        }
        return Result.Success;
    }
}

[CommandStyle(Style.ScriptRunner)]
public class AliasStyleLinkCommand : Command
{
    public override string EnglishName => "AliasStyleLink";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
        => AliasStyleLinkUi.ToggleAndReport(doc);
}
