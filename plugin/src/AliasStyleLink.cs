using System;
using System.Threading;
using Rhino;
using Rhino.Commands;
using Rhino.Display;

namespace DatumPlanePlugin;

/// <summary>
/// v2.9：全视图联动（Alias 式）。
///
/// 用户反馈的原话：「我只改变我在编辑的那个窗口，而不是所有的窗口一起变成那个模式」。
/// Rhino 原生行为就是**每个视口各自持有 DisplayMode**，无论是点视口标题栏的下拉、
/// 走「视图 → 显示模式」菜单，还是 `_SetDisplayMode` 命令，都只作用当前视口 ——
/// 这是 McNeel 的设计，不是我们命令的 bug（实测 4 个视口同时被 `AliasStyleLight`
/// 改成 Alias EyeCare，命令层本来就是遍历所有视口的）。
///
/// 要实现 Alias 那种「切一次全画布跟着变」，只能自己挂事件：
///   实测（Rhino 9 / E-021）：`DisplayPipeline.DisplayModeChanged` 是**静态事件**
///   （`GetAddMethod().IsStatic = True`），且通过 API 写 `viewport.DisplayMode`
///   会**同步**触发，`args.Viewport` 精确指向被改的视口，`Old/ChangedDisplayModeId` 正确。
///   所以联动可以纯靠事件驱动，不需要轮询。
///
/// 三条必须守住的纪律：
///  1. **防重入**：同步时改其他视口会再次触发本事件 → `_busy` 闸门挡住，
///     否则 4 个视口互相触发会打成一团（实测同一 setter 立刻回调）。
///  2. **同步前先比 Id**：目标视口已经是该模式就跳过，天然收敛，也避免多余重绘。
///  3. **程序化改模式时必须静音**：`AliasStyle.Restore` 要把各视口还原成**不同的**
///     原模式，若联动还在工作，还原会被"同步"回去 —— 所以 Apply/Restore 全程 Mute()。
///
/// 开关持久化在 PersistentSettings（跨文档、跨会话），命令 `AliasStyleLink` / 菜单 O 切换。
/// 默认**开启**：用户明确要的是 Alias 式联动；想单视口对比时再关掉即可。
/// </summary>
internal static class AliasStyleLink
{
    private const string SettingKey = "DatumPlane.AliasStyle.LinkAllViews";

    private static int _hooked;
    private static int _busy;
    private static int _mute;
    private static bool _enabled = true;

    public static bool Enabled => _enabled;

    /// <summary>插件 OnLoad 调用；重复调用安全。</summary>
    public static void Start()
    {
        // 注意：Rhino.PersistentSettings 的 GetBool/SetBool 是**实例方法**（CS0120 实测），
        // 全局静态入口并不存在。插件自己的 Settings 就是 PersistentSettings 实例，写在这里
        // 会落到 %AppData%\McNeel\Rhinoceros\9.0\Plug-ins\<guid>\settings 下，跨文档跨会话有效。
        try { _enabled = DatumPlanePlugin.Instance?.Settings?.GetBool(SettingKey, true) ?? true; }
        catch { _enabled = true; }

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
        }
        else
        {
            RhinoApp.WriteLine(
                "全视图联动：已关闭，各视口可独立设置显示模式 / All-view display sync OFF: each viewport is independent.");
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
