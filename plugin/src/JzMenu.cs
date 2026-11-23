using System;
using System.Collections.Generic;
using Rhino;
using Rhino.Commands;
using Rhino.Geometry;
using Rhino.Input;
using Rhino.Input.Custom;

namespace DatumPlanePlugin;

/// <summary>菜单范围：JZ 与 DatumPlane 都只列基准面，AliasStyle 只列显示风格（两类命令分开）。</summary>
internal enum JzScope { Datum, Style, All }

/// <summary>
/// v1.8 统一「字母菜单」。
///
/// 设计依据（Rhino 9 实机反射 + 官方 SDK 文档验证）：
///  1. Rhino 命令行选项会自动把「选项名里第一个尚未被引用的字母」当作加速键，
///     并在命令行给它加下划线；用户敲这个字母即可选中该选项（McNeel 论坛明确：
///     "the underlined option name letter in the command bar"）。
///  2. 选项名经 IsValidOptionName() 实测只允许字母数字（下划线亦合法），中文不能
///     直接做选项名，所以中文说明放在 AddOption 的第二个参数（等号后显示），
///     格式「字母_英文简写 = 中文 / English」。
///  3. 因为每个选项的首字母 A..M 全局唯一，加速键就固定是那个字母，敲字母必中，
///     不会像旧版 Plane / Pick、Recall / Restore 那样撞首字母导致字母飘忽。
///  4. 字母→功能在三个入口（JZ / DatumPlane / AliasStyle）中完全一致，记一次即可。
///
/// 命令别名：JZ 是一个真正的插件命令（不是偷偷写全局 Aliases 表），
/// 随 yak 安装/卸载，不污染用户设置；等价于 Rhino 的 command alias。
/// </summary>
internal static class JzMenu
{
    private readonly struct Entry
    {
        public readonly string Key;
        public readonly string Hint;
        public readonly char Letter;
        public readonly bool IsDatum;

        public Entry(string key, string hint, bool isDatum)
        {
            Key = key;
            Hint = hint;
            Letter = key[0];
            IsDatum = isDatum;
        }
    }

    // 固定代号表：字母 → 英文简写 → 中文说明（中文与英文并列保留在后面）。
    // A..H = 基准面效果，N = 关闭第5视图，I..M + O = Alias 观测显示效果。
    private static readonly Entry[] Entries =
    {
        new("A_3Point",       "三点定义新基准面 / Define plane by 3 points",                 true),
        new("B_Plane",        "直接点选实体/多重曲面上的平面面片（无需 Ctrl+Shift）/ Click a planar face", true),
        new("C_Pick",         "点选已有基准面切换（锁定也可点）/ Pick existing datum",        true),
        new("D_Recall",       "按编号调用已保存的基准面 / Recall saved datum by number",     true),
        new("E_Save",         "当前工作平面另存为命名基准面 / Save CPlane as named datum",   true),
        new("F_Lock",         "继续保持当前基准面坐标系 / Keep current datum axes locked",   true),
        new("G_NormalView",   "第5视图：基准面法向 / 5th normal view (split Top)",          true),
        new("H_Restore",      "退出并还原最初工作平面与操作轴 / Restore initial CPlane",     true),
        new("N_Close5th",     "关闭第5视窗恢复4视图 / Close 5th viewport, restore 4 views",    true),
        new("I_Light",        "浅色观测显示，只改当前视口（三度灰阶 + 结构线0）/ Light three-tone, active viewport only", false),
        new("J_Dark",         "深色观测显示，只改当前视口（三度灰阶 + 结构线1）/ Dark three-tone, active viewport only", false),
        new("K_Density",      "设置等参线密度看曲面走向 / Set isocurve density",              false),
        new("L_Status",       "查看当前显示状态 / Show current display status",              false),
        new("M_RestoreStyle", "还原为原显示模式（只还原改过的视口）/ Restore the previous display mode", false),
        new("O_Link",         "全视图联动 开/关（默认关，各视口独立）/ Toggle all-view sync (default OFF)", false),
    };

    private static bool InScope(Entry e, JzScope scope) =>
        scope == JzScope.All || (scope == JzScope.Datum ? e.IsDatum : !e.IsDatum);

    /// <summary>构造并显示菜单，把字母代号分发到对应的真实逻辑。</summary>
    public static Result Run(RhinoDoc doc, JzScope scope)
    {
        bool active = DatumPlaneCore.IsActive(doc);

        using var get = new GetOption();
        get.SetCommandPrompt(BuildPrompt(scope, active));

        // 用 AddOption 的返回值做索引，不硬编码顺序（SDK 要求 >0）。
        var indexByLetter = new Dictionary<char, int>();
        foreach (Entry e in Entries)
        {
            if (!InScope(e, scope)) continue;
            int idx = get.AddOption(e.Key, e.Hint);
            if (idx <= 0) return Result.Failure;
            indexByLetter[e.Letter] = idx;
        }

        GetResult res = get.Get();

        // 回车：与旧版一致——基准面已激活则还原，否则取消；显示风格菜单直接取消。
        if (res == GetResult.Nothing)
            return scope == JzScope.Style
                ? Result.Cancel
                : active
                    ? DatumUi.Finish(doc, DatumPlaneCore.Deactivate(doc))
                    : Result.Cancel;
        if (res != GetResult.Option)
            return get.CommandResult() == Result.Success ? Result.Cancel : get.CommandResult();

        int choice = get.OptionIndex();
        char letter = '?';
        foreach (var kv in indexByLetter)
        {
            if (kv.Value == choice) { letter = kv.Key; break; }
        }
        return Dispatch(doc, letter);
    }

    private static string BuildPrompt(JzScope scope, bool active)
    {
        string head = scope switch
        {
            JzScope.All   => "JZ 基准面 + 显示风格 / Datum plane + display style",
            JzScope.Style => "Alias 观测显示 / Alias study display",
            _             => "基准面 / Datum plane",
        };

        string state = active
            ? "（已启用 / ACTIVE，回车还原 / Enter=restore）"
            : "（回车取消 / Enter=cancel）";

        // 字母→中文的速查表放在提示里，保证中文始终可见；
        // 每个选项自身也带「字母_英文简写 = 中文 / English」的完整说明。
        return head + state + "：" + Legend(scope) +
               "　敲下划线字母选择 / type the underlined letter";
    }

    private static string Legend(JzScope scope)
    {
        var parts = new List<string>();
        foreach (Entry e in Entries)
        {
            if (!InScope(e, scope)) continue;
            string cn = e.Hint.Split('/')[0].Trim();
            parts.Add(e.Letter + "=" + cn);
        }
        return string.Join(" ", parts);
    }

    private static Result Dispatch(RhinoDoc doc, char letter)
    {
        switch (letter)
        {
            case 'A':
            case 'B':
            {
                Plane plane;
                Result r = letter == 'A'
                    ? DatumPlaneCommand.GetThreePoints(out plane)
                    : DatumPlaneCommand.GetFace(doc, out plane);
                return r == Result.Success
                    ? DatumUi.Finish(doc, DatumPlaneCore.Create(doc, plane))
                    : r;
            }
            case 'C': return DatumUi.Pick(doc);
            case 'D': return DatumUi.Recall(doc);
            case 'E': return DatumUi.SaveCurrent(doc);
            case 'F': return DatumUi.Finish(doc, DatumPlaneCore.Lock(doc));
            case 'G': return DatumPlaneNormalView.Show(doc);
            case 'H': return DatumUi.Finish(doc, DatumPlaneCore.Deactivate(doc));
            case 'N': return DatumPlaneNormalView.Close(doc);
            case 'I': return AliasStyleUi.ApplyAndReport(doc, false);
            case 'J': return AliasStyleUi.ApplyAndReport(doc, true);
            case 'K': return AliasStyleUi.SetDensity(doc);
            case 'L': AliasStyleUi.Report(doc); return Result.Success;
            case 'M': return AliasStyleUi.RestoreAndReport(doc);
            case 'O': return AliasStyleLinkUi.ToggleAndReport(doc);
            default: return Result.Cancel;
        }
    }
}

/// <summary>
/// v1.9 命令别名 JZ（"基准"拼音首字母）：只列基准面命令（A-H），显示风格不再混入。
/// 显示模式请用独立命令 AliasStyle / AliasStyleLight / AliasStyleDark / AliasStyleRestore，
/// 可自行设别名或按钮。
/// 做成插件命令而非写全局 CommandAliasList，是为了随 yak 安装/卸载自动生效，
/// 不改动用户自己的 Aliases 设置。
/// </summary>
[CommandStyle(Style.ScriptRunner)]
public class DatumPlaneJzCommand : Command
{
    public override string EnglishName => "JZ";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) => JzMenu.Run(doc, JzScope.Datum);
}
