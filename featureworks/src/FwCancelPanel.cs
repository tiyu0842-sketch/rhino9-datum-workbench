using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using Eto.Forms;
using Rhino;
using Rhino.Commands;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input.Custom;
using Rhino.UI;

namespace RhinoFeatureWorks;

/// <summary>
/// 取消面板（v1.6 严格两模块 + 常驻双向联动）。
///
/// 用户 v1.5 的三点批评与 v1.6 的对应改动：
///   1. 「为什么选了框之后只能在框里选，不能在原有界面上框选标红的物体」
///      → 常驻 FwMouseWatcher 接管左键，视口直接点选/拖框；conduit 画框选矩形与三态高亮。
///   2. 「两边可以同时相互交互，而不是去选择那一边」
///      → 删掉 OnListPicked 里的互斥清空，改为一份 FwSelectionState 共享选中集，
///        视口 / 面板 / 两个模块共同读写。
///   3. 「分成两个模块：单独去除圆角、去除布尔；去布尔是不是必须先去完圆角」
///      → 两个独立执行器 + 各自按钮。布尔走 RemoveHoles(指定内环)，与圆角无关、任意顺序。
///      → 按用户拍板「严格两模块、不要总开关」，删除「全部取消 → 回毛坯」按钮。
///
/// 圆角若连带抹平孔，执行器会在命令行与本报告里**明确报出**，不偷偷改（用户拍板）。
/// </summary>
[Guid("B4D8E21A-7C36-4F59-8A0D-3E7B1C6F9D24")]
public class FwCancelPanel : Eto.Forms.Panel, IPanel
{
    public static readonly Guid PanelId = new Guid("B4D8E21A-7C36-4F59-8A0D-3E7B1C6F9D24");

    private delegate void PanelAction();

    private readonly CheckBoxList _filletList = new CheckBoxList
    {
        Height = 150, Orientation = Orientation.Vertical
    };
    private readonly CheckBoxList _holeList = new CheckBoxList
    {
        Height = 130, Orientation = Orientation.Vertical
    };
    private readonly Label _source = new Label { Text = "（未选实体 / no target）" };
    private readonly Label _status = new Label { Text = "" };
    private readonly Button _btnRunFillet;
    private readonly Button _btnRunHole;
    private readonly Button _btnKeepAll;
    private readonly Button _btnLocate;
    private bool _updating;
    private static bool _registered;

    public FwCancelPanel()
    {
        var btnPick = new Button { Text = "选实体并识别 / Pick solid" };
        btnPick.Click += (_, __) => Safe(DoPick);
        var btnRefresh = new Button { Text = "刷新 / Refresh" };
        btnRefresh.Click += (_, __) => Safe(Refresh);

        _btnLocate = new Button { Text = "缩放到选中项 / Zoom to selected" };
        _btnLocate.Click += (_, __) => Safe(DoLocate);

        _btnRunFillet = new Button { Text = "模块 A · 去除圆角（选中 0）" };
        _btnRunFillet.Click += (_, __) => Safe(() => DoRunModule("Fillet"));
        _btnRunHole = new Button { Text = "模块 B · 去除布尔切割（选中 0）" };
        _btnRunHole.Click += (_, __) => Safe(() => DoRunModule("Hole"));

        // 「保留全部」= 什么都不改、关掉聚焦显示。不是取消总开关，纯粹是退出。
        _btnKeepAll = new Button { Text = "关闭聚焦 / 保留全部（不改模型）" };
        _btnKeepAll.Click += (_, __) => Safe(DoKeepAll);

        _filletList.SelectedKeysChanged += (_, __) => Safe(OnListChanged);
        _holeList.SelectedKeysChanged += (_, __) => Safe(OnListChanged);

        // 视口拖框 / 点选 / 命令行点边 都写同一份共享选中集，面板订阅它即可。
        FwSelectionState.Changed -= OnSelectionChanged;
        FwSelectionState.Changed += OnSelectionChanged;

        var hint = new Label
        {
            Text = "视口：左键点选 / 拖框选中标红特征，Shift 或 Ctrl 加减选，点空白清空。\n" +
                   "面板：勾选 = 要取消；两个模块各按各的按钮，互不牵连。F1/H1 编号与模型标签对应。"
        };
        var root = new TableLayout
        {
            Rows =
            {
                new TableRow(hint),
                new TableRow(btnPick, btnRefresh),
                new TableRow(_source),
                new TableRow(new GroupBox
                {
                    Text = "模块 A · 去除圆角（删整圈过渡面 + 重缝；圆角无法 untrim）",
                    Content = _filletList,
                    Padding = new Eto.Drawing.Padding(4)
                }),
                new TableRow(_btnRunFillet),
                new TableRow(new GroupBox
                {
                    Text = "模块 B · 去除布尔切割（RemoveHoles 指定内环，与圆角无关）",
                    Content = _holeList,
                    Padding = new Eto.Drawing.Padding(4)
                }),
                new TableRow(_btnRunHole),
                new TableRow(_btnLocate, _btnKeepAll),
                new TableRow(_status),
            },
            Spacing = new Eto.Drawing.Size(4, 5)
        };

        Content = new Scrollable
        {
            Content = new Eto.Forms.Panel
            {
                Content = root,
                Padding = new Eto.Drawing.Padding(6)
            },
            ExpandContentWidth = true,
            MinimumSize = new Eto.Drawing.Size(410, 560)
        };

        Refresh();
    }

    private void Safe(PanelAction action)
    {
        try { action(); }
        catch (Exception ex)
        {
            RhinoApp.WriteLine("FwCancelPanel 错误 / panel error: " + ex.Message);
            _status.Text = "错误 / Error: " + ex.Message;
        }
    }

    private void DoPick()
    {
        RhinoDoc? doc = RhinoDoc.ActiveDoc;
        if (doc == null) return;

        if (FwFocusSession.HasActive) FwFocusSession.End(doc);

        var go = new GetObject
        {
            GeometryFilter = ObjectType.Brep,
            SubObjectSelect = false
        };
        go.SetCommandPrompt("选择要取消特征的实体 / Select a Brep solid");
        go.Get();
        if (go.CommandResult() != Result.Success) return;

        ObjRef? ore = go.Object(0);
        if (ore == null) return;
        Brep? brep = ore.Brep();
        if (brep == null)
        {
            _status.Text = "不是 B-Rep 实体 / Not a Brep.";
            return;
        }

        var (_, feats, _) = FwApi.Recognize(brep, doc.ModelAbsoluteTolerance);
        if (feats.Count == 0)
        {
            _status.Text = "没有识别到可取消的特征 / No features recognized.";
            return;
        }

        RhinoApp.WriteLine(FwFocusSession.Begin(doc, ore.ObjectId, brep, feats));
        Refresh();
        _status.Text = "已识别：可在视口直接点选/拖框，或勾选后按对应模块按钮。";
    }

    // ---------------------------------------------------------------- 一份共享选中集

    /// <summary>面板勾选变化 → 写回共享集（两个列表合并，不再互斥清空另一边）。</summary>
    private void OnListChanged()
    {
        if (_updating) return;
        var keys = new List<int>();
        foreach (CheckBoxList list in new[] { _filletList, _holeList })
            foreach (string key in list.SelectedKeys)
                if (int.TryParse(key, out int i)) keys.Add(i);
        FwSelectionState.ReplaceAll(keys, "panel");

        // 勾选即在视口定位最后一次操作的那组。
        var ordered = keys.OrderBy(k => k).ToList();
        if (ordered.Count > 0) FwFocusSession.SetFocus(ordered[ordered.Count - 1]);
    }

    /// <summary>视口 / 命令行 / 执行器改了共享集 → 两个列表一起刷新勾选与按钮计数。</summary>
    private void OnSelectionChanged(string origin)
    {
        _updating = true;
        try
        {
            int cut = FwFocusSession.FilletGroups.Count;
            var f = new List<string>();
            var h = new List<string>();
            foreach (int i in FwSelectionState.Selected)
                (i < cut ? f : h).Add(i.ToString());
            _filletList.SelectedKeys = f.ToArray();
            _holeList.SelectedKeys = h.ToArray();
        }
        finally { _updating = false; }
        UpdateCounts();
    }

    private void UpdateCounts()
    {
        int nf = FwSelectionState.FilletCount;
        int nh = FwSelectionState.HoleCount;
        _btnRunFillet.Text = "模块 A · 去除圆角（选中 " + nf + "）";
        _btnRunHole.Text = "模块 B · 去除布尔切割（选中 " + nh + "）";
        _status.Text = FwFocusSession.HasActive
            ? string.Format("共享选中集：共 {0} 项（圆角 {1} / 布尔 {2}）。勾选 ≠ 执行；各模块单独按按钮。",
                FwSelectionState.Count, nf, nh)
            : "（未开启聚焦 / focus off）";
    }

    // ---------------------------------------------------------------- 两个独立模块

    private void DoRunModule(string module)
    {
        if (!FwFocusSession.HasActive)
        {
            _status.Text = "先选实体 / Pick a solid first.";
            return;
        }

        List<int> indices = FwSelectionState.IndicesInChannel(module);
        if (indices.Count == 0)
        {
            _status.Text = module == "Fillet"
                ? "模块 A 没有勾选圆角；不勾不会删任何东西 / Nothing ticked in module A."
                : "模块 B 没有勾选布尔切割；不勾不会删任何东西 / Nothing ticked in module B.";
            return;
        }

        var targets = new List<FwFocusGroup>();
        foreach (int i in indices)
        {
            FwFocusGroup? g = FwFocusSession.GroupAt(i);
            if (g != null) targets.Add(g);
        }
        if (targets.Count == 0) return;

        bool ok = FwCancelRunner.TryApply(RhinoDoc.ActiveDoc, module, targets, out string message);
        RhinoApp.WriteLine(message);   // 连带影响孔时，这里会原文报出，不藏在面板里
        _status.Text = ok
            ? (module == "Fillet" ? "模块 A 已执行 / fillet module applied." : "模块 B 已执行 / boolean module applied.")
            : Short(message);
        Refresh();
    }

    /// <summary>关闭聚焦：模型一个字节都不改。</summary>
    private void DoKeepAll()
    {
        if (!FwFocusSession.HasActive)
        {
            _status.Text = "当前没有聚焦会话 / No active session.";
            return;
        }
        FwFocusSession.End(RhinoDoc.ActiveDoc);
        Refresh();
        _status.Text = "已保留全部：模型未改动，聚焦显示已关闭 / Kept all; model untouched.";
    }

    private void DoLocate()
    {
        var picked = FwSelectionState.Selected.ToList();
        if (picked.Count == 0)
        {
            _status.Text = "请先勾选或在视口框选特征 / Nothing selected.";
            return;
        }
        Brep? src = FwFocusSession.SourceBrep;
        RhinoView? view = RhinoDoc.ActiveDoc?.Views.ActiveView;
        if (src == null || view == null) return;

        BoundingBox bb = BoundingBox.Unset;
        foreach (int i in picked)
        {
            FwFocusGroup? g = FwFocusSession.GroupAt(i);
            if (g == null) continue;
            foreach (int fi in g.Faces)
            {
                if (fi < 0 || fi >= src.Faces.Count) continue;
                BoundingBox one = src.Faces[fi].GetBoundingBox(true);
                if (!one.IsValid) continue;
                bb = bb.IsValid ? BoundingBox.Union(bb, one) : one;
            }
        }
        if (!bb.IsValid) return;
        view.ActiveViewport.ZoomBoundingBox(bb);
        view.Redraw();
        _status.Text = "已缩放到 " + picked.Count + " 个选中组 / Zoomed to selection.";
    }

    private static string Short(string s) =>
        string.IsNullOrEmpty(s) ? "失败 / failed"
        : s.Length <= 110 ? s : s.Substring(0, 110) + "...";

    public void Refresh()
    {
        bool active = FwFocusSession.HasActive;
        _source.Text = active
            ? string.Format("源对象 {0} · 面 {1} · 半透明锁定 {2} · 特征 {3} 组（圆角 {4} / 布尔 {5}）",
                FwFocusSession.SourceId.ToString("N").Substring(0, 8),
                FwFocusSession.SourceBrep?.Faces.Count ?? 0,
                FwFocusSession.LockedFaces.Count,
                FwFocusSession.AllGroupCount,
                FwFocusSession.FilletGroups.Count,
                FwFocusSession.HoleGroups.Count)
            : "（未选实体 / no target）";

        _updating = true;
        try
        {
            Fill(_filletList, FwFocusSession.FilletGroups, 0);
            Fill(_holeList, FwFocusSession.HoleGroups, FwFocusSession.FilletGroups.Count);
        }
        finally { _updating = false; }

        OnSelectionChanged("refresh");

        int n = FwFocusSession.AllGroupCount;
        _btnRunFillet.Enabled = active && FwFocusSession.FilletGroups.Count > 0;
        _btnRunHole.Enabled = active && FwFocusSession.HoleGroups.Count > 0;
        _btnKeepAll.Enabled = active;
        _btnLocate.Enabled = n > 0;
    }

    private static void Fill(CheckBoxList list, List<FwFocusGroup> groups, int offset)
    {
        list.Items.Clear();
        for (int i = 0; i < groups.Count; i++)
        {
            FwFocusGroup g = groups[i];
            string loopInfo = g.Loops.Count > 0
                ? " · " + g.Loops.Count + " 内环"
                : "";
            list.Items.Add(new ListItem
            {
                Text = string.Format("{0}  {1}  {2}  ·  {3} 面{4}",
                    g.Id, g.Name, g.Detail, g.Faces.Count, loopInfo),
                Key = (offset + i).ToString()
            });
        }
    }

    public void PanelShown(uint docSerialNumber, ShowPanelReason reason) => Refresh();
    public void PanelHidden(uint docSerialNumber, ShowPanelReason reason) { }
    public void PanelClosing(uint docSerialNumber, bool allowHiding)
    {
        FwSelectionState.Changed -= OnSelectionChanged;
    }

    public static void Register()
    {
        if (_registered) return;
        try
        {
            if (FeatureWorksPlugin.Instance == null) return;
            Panels.RegisterPanel(FeatureWorksPlugin.Instance, typeof(FwCancelPanel),
                                 "特征取消 / FeatureWorks Cancel", null, PanelType.System);
            _registered = true;
        }
        catch (Exception ex)
        {
            RhinoApp.WriteLine("FwCancelPanel 注册失败 / register failed: " + ex.Message);
        }
    }

    public static void Open()
    {
        Register();
        Panels.OpenPanel(PanelId);
    }
}

/// <summary>打开取消面板的命令 FWCancelPanel。</summary>
[CommandStyle(Style.ScriptRunner)]
public class FwCancelPanelCommand : Rhino.Commands.Command
{
    public override string EnglishName => "FWCancelPanel";

    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        FwCancelPanel.Open();
        return Result.Success;
    }
}
