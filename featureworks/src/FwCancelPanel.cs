using System;
using System.Collections.Generic;
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
/// 取消面板（v1.5 重做交互）。
///
/// 旧版把特征摊成一行扁平 checkbox，用户的原话是「一个一个 flat，我都不知道这是哪个跟哪个」，
/// 而且「不勾 = 全部取消」极容易误删。v1.5 三点改动：
///   1. 每个特征组有稳定编号 F1/F2…/H1/H2…，视口直接画同样的编号标签；
///   2. 双向选择 —— 点面板行 → 视口高亮该组；点「视口拾取」后点边/面 → 对应行自动勾选；
///   3. 操作语义显式化 —— 保留全部 / 取消选中(N) / 全部取消，不勾绝不删任何东西。
///
/// 取消算法本身不变（两个通道两套几何算法），仍走 FwCancelRunner，同一个 Undo 记录。
/// </summary>
[Guid("B4D8E21A-7C36-4F59-8A0D-3E7B1C6F9D24")]
public class FwCancelPanel : Eto.Forms.Panel, IPanel
{
    public static readonly Guid PanelId = new Guid("B4D8E21A-7C36-4F59-8A0D-3E7B1C6F9D24");

    private readonly CheckBoxList _filletList = new CheckBoxList
    {
        Height = 150, Orientation = Orientation.Vertical
    };
    private readonly CheckBoxList _holeList = new CheckBoxList
    {
        Height = 120, Orientation = Orientation.Vertical
    };
    private readonly Label _source = new Label { Text = "（未选实体 / no target）" };
    private readonly Label _status = new Label
    {
        Text = "勾选 = 要取消；不勾 = 保留。点行可在视口定位。"
    };
    private readonly Button _btnCancelSelected;
    private readonly Button _btnKeepAll;
    private readonly Button _btnCancelAll;
    private readonly Button _btnPickEdge;
    private readonly Button _btnLocate;
    private bool _updating;
    private static bool _registered;

    public FwCancelPanel()
    {
        var btnPick = new Button { Text = "选实体并识别 / Pick solid" };
        btnPick.Click += (_, __) => Safe(DoPick);
        var btnRefresh = new Button { Text = "刷新 / Refresh" };
        btnRefresh.Click += (_, __) => Safe(Refresh);

        _btnPickEdge = new Button { Text = "视口拾取边/面 → 选中特征 / Pick edge in model" };
        _btnPickEdge.Click += (_, __) => Safe(() =>
        {
            RhinoApp.RunScript("_FWPickFeature", false);
        });

        _btnLocate = new Button { Text = "缩放到选中项 / Zoom to selected" };
        _btnLocate.Click += (_, __) => Safe(DoLocate);

        _btnCancelSelected = new Button { Text = "取消选中 0 项 / Cancel selected" };
        _btnCancelSelected.Click += (_, __) => Safe(DoCancelSelected);
        _btnKeepAll = new Button { Text = "保留全部（不改模型）/ Keep all" };
        _btnKeepAll.Click += (_, __) => Safe(DoKeepAll);
        _btnCancelAll = new Button { Text = "全部取消 → 回毛坯 / Cancel all" };
        _btnCancelAll.Click += (_, __) => Safe(DoCancelAll);

        _filletList.SelectedKeysChanged += (_, __) => Safe(() => OnListPicked(_filletList));
        _holeList.SelectedKeysChanged += (_, __) => Safe(() => OnListPicked(_holeList));
        // 视口点边/面命中的组会回写到这里（自定义委托，避开 WeaverBird 的 Action 冲突）
        FwFocusSession.PanelReceiver = OnViewportPicked;

        var hint = new Label
        {
            Text = "用法：点行=视口高亮；视口拾取=点模型的边/面来选中；勾选=要删除的特征"
        };
        var root = new TableLayout
        {
            Rows =
            {
                new TableRow(hint),
                new TableRow(btnPick, btnRefresh),
                new TableRow(_btnPickEdge),
                new TableRow(_source),
                new TableRow(new GroupBox
                {
                    Text = "圆角通道 / Fillet   删除过渡面 + 底层曲面重缝",
                    Content = _filletList,
                    Padding = new Eto.Drawing.Padding(4)
                }),
                new TableRow(new GroupBox
                {
                    Text = "孔洞通道 / Hole   UntrimFace 抹内环",
                    Content = _holeList,
                    Padding = new Eto.Drawing.Padding(4)
                }),
                new TableRow(_btnLocate),
                new TableRow(_btnCancelSelected),
                new TableRow(_btnKeepAll, _btnCancelAll),
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
            MinimumSize = new Eto.Drawing.Size(390, 520)
        };

        Refresh();
    }

    private void Safe(Action action)
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
        _status.Text = "已识别：点行定位、点边选中、勾选后取消 / Pick a row or an edge, tick, then cancel.";
    }

    // ---------------------------------------------------------------- 双向选择

    private void OnListPicked(CheckBoxList source)
    {
        if (_updating) return;
        var keys = new List<string>(source.SelectedKeys);
        if (keys.Count != 1) return;
        if (!int.TryParse(keys[0], out int index)) return;

        // 同一时刻只允许一边有勾选，避免"两个通道各勾一个"的歧义
        _updating = true;
        try { (source == _filletList ? _holeList : _filletList).SelectedKeys = new string[0]; }
        finally { _updating = false; }

        FwFocusSession.SetFocus(index);
        _status.Text = "已定位 " + FwFocusSession.GroupLabel(index) +
            "：视口高亮中；点「取消选中」才执行 / Highlighted; click 'Cancel selected' to apply.";
        UpdateSelectedCount();
    }

    private void OnViewportPicked(int index, string origin)
    {
        _updating = true;
        try
        {
            string key = index.ToString();
            _filletList.SelectedKeys = new string[0];
            _holeList.SelectedKeys = new string[0];
            CheckBoxList target = index < FwFocusSession.FilletGroups.Count ? _filletList : _holeList;
            target.SelectedKeys = new[] { key };
        }
        finally { _updating = false; }

        FwFocusSession.SetFocus(index);
        _status.Text = "视口选中 " + FwFocusSession.GroupLabel(index) +
            "：对应行已勾选；点「取消选中」执行 / Selected from viewport.";
        UpdateSelectedCount();
    }

    private List<int> CollectSelected()
    {
        var picked = new List<int>();
        foreach (CheckBoxList list in new[] { _filletList, _holeList })
            foreach (string key in list.SelectedKeys)
                if (int.TryParse(key, out int i) && !picked.Contains(i)) picked.Add(i);
        return picked;
    }

    private void UpdateSelectedCount()
    {
        _btnCancelSelected.Text = "取消选中 " + CollectSelected().Count + " 项 / Cancel selected";
    }

    private void DoLocate()
    {
        List<int> picked = CollectSelected();
        if (picked.Count != 1)
        {
            _status.Text = "请先选中一行 / Select exactly one row.";
            return;
        }
        FwFocusGroup? g = FwFocusSession.GroupAt(picked[0]);
        Brep? src = FwFocusSession.SourceBrep;
        RhinoView? view = RhinoDoc.ActiveDoc?.Views.ActiveView;
        if (g == null || src == null || view == null) return;

        BoundingBox bb = BoundingBox.Unset;
        foreach (int fi in g.Faces)
        {
            if (fi < 0 || fi >= src.Faces.Count) continue;
            BoundingBox one = src.Faces[fi].GetBoundingBox(true);
            if (!one.IsValid) continue;
            bb = bb.IsValid ? BoundingBox.Union(bb, one) : one;
        }
        if (!bb.IsValid) return;
        view.ActiveViewport.ZoomBoundingBox(bb);
        view.Redraw();
        _status.Text = "已缩放到 " + g.Id + " / Zoomed to " + g.Id + ".";
    }

    // ---------------------------------------------------------------- 显式操作语义

    /// <summary>只取消勾选的组；一个都没勾时**什么也不做**（旧版会误删全部）。</summary>
    private void DoCancelSelected()
    {
        if (!FwFocusSession.HasActive)
        {
            _status.Text = "先选实体 / Pick a solid first.";
            return;
        }

        List<int> picked = CollectSelected();
        if (picked.Count == 0)
        {
            _status.Text = "请先勾选或在视口中点边/面；不勾不会删除任何特征 / Nothing ticked, nothing changed.";
            return;
        }

        var targets = new List<FwFocusGroup>();
        foreach (int i in picked)
        {
            FwFocusGroup? g = FwFocusSession.GroupAt(i);
            if (g != null) targets.Add(g);
        }
        if (targets.Count == 0) return;

        bool ok = FwCancelRunner.TryApply(RhinoDoc.ActiveDoc, targets, AllGroups(), out string message);
        RhinoApp.WriteLine(message);
        _status.Text = ok ? "已取消 " + targets.Count + " 组 / cancelled." : Short(message);
        Refresh();
    }

    /// <summary>保留全部：模型一个字节都不改，只关掉聚焦显示。</summary>
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

    private void DoCancelAll()
    {
        if (!FwFocusSession.HasActive)
        {
            _status.Text = "先选实体 / Pick a solid first.";
            return;
        }

        var all = AllGroups();
        if (all.Count == 0)
        {
            _status.Text = "没有可取消的特征 / Nothing to cancel.";
            return;
        }

        bool ok = FwCancelRunner.TryApply(RhinoDoc.ActiveDoc, all, all, out string message);
        RhinoApp.WriteLine(message);
        _status.Text = ok ? "已回到毛坯 / Back to blank" : Short(message);
        Refresh();
    }

    private static List<FwFocusGroup> AllGroups()
    {
        var all = new List<FwFocusGroup>();
        all.AddRange(FwFocusSession.FilletGroups);
        all.AddRange(FwFocusSession.HoleGroups);
        return all;
    }

    private static string Short(string s) =>
        string.IsNullOrEmpty(s) ? "失败 / failed"
        : s.Length <= 110 ? s : s.Substring(0, 110) + "...";

    public void Refresh()
    {
        bool active = FwFocusSession.HasActive;
        _source.Text = active
            ? string.Format("源对象 {0} · 面 {1} · 半透明锁定 {2} · 特征 {3} 组",
                FwFocusSession.SourceId.ToString("N").Substring(0, 8),
                FwFocusSession.SourceBrep?.Faces.Count ?? 0,
                FwFocusSession.LockedFaces.Count,
                FwFocusSession.AllGroupCount)
            : "（未选实体 / no target）";

        _updating = true;
        try
        {
            Fill(_filletList, FwFocusSession.FilletGroups, 0);
            Fill(_holeList, FwFocusSession.HoleGroups, FwFocusSession.FilletGroups.Count);
        }
        finally { _updating = false; }

        int n = FwFocusSession.AllGroupCount;
        _btnCancelSelected.Enabled = n > 0;
        _btnKeepAll.Enabled = active;
        _btnCancelAll.Enabled = n > 0;
        _btnPickEdge.Enabled = active;
        _btnLocate.Enabled = n > 0;
        UpdateSelectedCount();
    }

    private static void Fill(CheckBoxList list, List<FwFocusGroup> groups, int offset)
    {
        list.Items.Clear();
        for (int i = 0; i < groups.Count; i++)
        {
            FwFocusGroup g = groups[i];
            list.Items.Add(new ListItem
            {
                Text = string.Format("{0}  {1}  {2}  ·  {3} 面", g.Id, g.Name, g.Detail, g.Faces.Count),
                Key = (offset + i).ToString()
            });
        }
    }

    public void PanelShown(uint docSerialNumber, ShowPanelReason reason) => Refresh();
    public void PanelHidden(uint docSerialNumber, ShowPanelReason reason) { }
    public void PanelClosing(uint docSerialNumber, bool allowHiding) { }

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
