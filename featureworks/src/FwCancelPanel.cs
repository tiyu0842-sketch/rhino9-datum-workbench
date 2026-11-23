using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Eto.Forms;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input.Custom;
using Rhino.UI;

namespace RhinoFeatureWorks;

/// <summary>
/// 取消面板：两个通道各一列，勾选后一键取消。
///
/// 交互对应视口里的聚焦状态：
///   视口 —— 特征面亮橙、其余半透明锁定（FwFocusSession 的 DisplayConduit 画的）
///   面板 —— 同一份数据的文字视图，圆角通道 / 孔洞通道分列
///   点"取消" —— 走 FwCancelRunner，两个通道背后是两套不同的几何算法
///
/// Rhino 9 自带 Eto 2.13 实测：
///   ListBox 只有 Items(string) / SelectedIndex(单值)，没有多选；
///   CheckBoxList 才有 SelectedValues(IEnumerable&lt;object&gt;) —— 正好是"勾选要取消的孔"。
///
/// 改文档的操作都落在同一个 Undo 记录里，Ctrl+Z 一次回退。
/// </summary>
[Guid("B4D8E21A-7C36-4F59-8A0D-3E7B1C6F9D24")]
public class FwCancelPanel : Eto.Forms.Panel, IPanel
{
    public static readonly Guid PanelId = new Guid("B4D8E21A-7C36-4F59-8A0D-3E7B1C6F9D24");

    private readonly CheckBoxList _filletList = new CheckBoxList { Height = 104 };
    private readonly CheckBoxList _holeList = new CheckBoxList { Height = 126 };
    private readonly Label _source = new Label { Text = "（未选实体 / no target）" };
    private readonly Label _status = new Label { Text = "先点「选实体」或运行 FWSelect。" };
    private readonly Button _btnCancelFillet;
    private readonly Button _btnCancelHole;
    private readonly Button _btnCancelAll;

    public FwCancelPanel()
    {
        var btnPick = new Button { Text = "选实体并识别 / Pick solid" };
        btnPick.Click += (_, __) => Safe(DoPick);
        var btnRefresh = new Button { Text = "刷新 / Refresh" };
        btnRefresh.Click += (_, __) => Safe(Refresh);

        _btnCancelFillet = new Button { Text = "取消勾选的圆角（不勾=全部）/ Cancel fillets" };
        _btnCancelFillet.Click += (_, __) => Safe(() =>
            DoCancel(FwFocusSession.FilletGroups, _filletList, "圆角 / Fillet"));

        _btnCancelHole = new Button { Text = "取消勾选的孔洞（不勾=全部）/ Cancel holes" };
        _btnCancelHole.Click += (_, __) => Safe(() =>
            DoCancel(FwFocusSession.HoleGroups, _holeList, "孔洞 / Hole"));

        _btnCancelAll = new Button { Text = "全部取消 → 回毛坯 / Cancel all" };
        _btnCancelAll.Click += (_, __) => Safe(DoCancelAll);

        var root = new TableLayout
        {
            Rows =
            {
                new TableRow(btnPick, btnRefresh),
                new TableRow(_source),
                new TableRow(new GroupBox
                {
                    Text = "圆角通道 / Fillet   取消方式：删过渡面 + 底层曲面重缝",
                    Content = _filletList,
                    Padding = new Eto.Drawing.Padding(4)
                }),
                new TableRow(_btnCancelFillet),
                new TableRow(new GroupBox
                {
                    Text = "孔洞通道 / Hole   取消方式：UntrimFace 抹内环",
                    Content = _holeList,
                    Padding = new Eto.Drawing.Padding(4)
                }),
                new TableRow(_btnCancelHole),
                new TableRow(_btnCancelAll),
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
            MinimumSize = new Eto.Drawing.Size(360, 460)
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
        _status.Text = "已识别：勾选要取消的项 / Recognized. Tick what to cancel.";
    }

    /// <summary>取消某个通道里勾选的组；若一个都没勾，就把该通道全部取消。</summary>
    private void DoCancel(List<FwFocusGroup> pool, CheckBoxList list, string channelLabel)
    {
        if (!FwFocusSession.HasActive)
        {
            _status.Text = "先选实体 / Pick a solid first.";
            return;
        }

        var picked = new HashSet<string>();
        foreach (string key in list.SelectedKeys) picked.Add(key);

        var targets = new List<FwFocusGroup>();
        for (int i = 0; i < pool.Count; i++)
        {
            if (picked.Contains(i.ToString()))
                targets.Add(pool[i]);
        }

        if (targets.Count == 0)
        {
            targets = new List<FwFocusGroup>(pool);
            if (targets.Count == 0)
            {
                _status.Text = channelLabel + " 通道为空 / channel empty.";
                return;
            }
        }

        bool ok = FwCancelRunner.TryApply(RhinoDoc.ActiveDoc, targets, pool, out string message);
        RhinoApp.WriteLine(message);
        _status.Text = ok ? "已取消 " + targets.Count + " 组 / cancelled." : Short(message);
        Refresh();
    }

    private void DoCancelAll()
    {
        if (!FwFocusSession.HasActive)
        {
            _status.Text = "先选实体 / Pick a solid first.";
            return;
        }

        var all = new List<FwFocusGroup>();
        all.AddRange(FwFocusSession.FilletGroups);
        all.AddRange(FwFocusSession.HoleGroups);
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

    private static string Short(string s) =>
        string.IsNullOrEmpty(s) ? "失败 / failed"
        : s.Length <= 110 ? s : s.Substring(0, 110) + "...";

    public void Refresh()
    {
        bool active = FwFocusSession.HasActive;
        _source.Text = active
            ? string.Format("源对象 {0} · 面 {1} · 锁定(半透明) {2}",
                FwFocusSession.SourceId.ToString("N").Substring(0, 8),
                FwFocusSession.SourceBrep?.Faces.Count ?? 0,
                FwFocusSession.LockedFaces.Count)
            : "（未选实体 / no target）";

        Fill(_filletList, FwFocusSession.FilletGroups);
        Fill(_holeList, FwFocusSession.HoleGroups);

        int nf = FwFocusSession.FilletGroups.Count;
        int nh = FwFocusSession.HoleGroups.Count;
        _btnCancelFillet.Enabled = nf > 0;
        _btnCancelHole.Enabled = nh > 0;
        _btnCancelAll.Enabled = nf + nh > 0;
    }

    private static void Fill(CheckBoxList list, List<FwFocusGroup> groups)
    {
        list.Items.Clear();
        for (int i = 0; i < groups.Count; i++)
            list.Items.Add(new ListItem { Text = Line(groups[i], i), Key = i.ToString() });
    }

    private static string Line(FwFocusGroup g, int i) => string.Format(
        "{0}. {1}  [{2}]  {3} 面  {4}", i + 1, g.Name, g.Type, g.Faces.Count, g.Detail);

    public void PanelShown(uint docSerialNumber, ShowPanelReason reason) => Refresh();
    public void PanelHidden(uint docSerialNumber, ShowPanelReason reason) { }
    public void PanelClosing(uint docSerialNumber, bool allowHiding) { }

    public static void Register()
    {
        try
        {
            if (FeatureWorksPlugin.Instance == null) return;
            if (!Panels.DockBarIdInUse(PanelId))
                Panels.RegisterPanel(FeatureWorksPlugin.Instance, typeof(FwCancelPanel),
                                     "特征取消 / FeatureWorks Cancel", null, PanelType.System);
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
