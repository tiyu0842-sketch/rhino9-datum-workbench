using System;
using System.Globalization;
using System.Linq;
using System.Runtime.InteropServices;
using Eto.Forms;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Input.Custom;
using Rhino.UI;

namespace RhinoFeatureWorks;

/// <summary>
/// 停靠面板：把命令行菜单做成可视化界面（类似 XNurbs 的侧边面板）。
/// 实测 Rhino 9：面板类就是 Eto.Forms.Panel 的子类，用
/// Panels.RegisterPanel(plugin, type, title, icon) 注册；Eto 2.13 随 Rhino 9 自带。
/// </summary>
[Guid("7A4E1C93-5B2D-4E68-9F31-0C8D5E6A7B42")]
public class FwPanel : Panel, IPanel
{
    public static readonly Guid PanelId = new Guid("7A4E1C93-5B2D-4E68-9F31-0C8D5E6A7B42");

    private readonly ListBox _list = new ListBox { Height = 200 };
    private readonly Label _detail = new Label { Text = "（先识别一个实体 / Recognize a solid first）" };
    private readonly TextBox _paramKey = new TextBox { ReadOnly = true };
    private readonly TextBox _paramValue = new TextBox();
    private readonly Label _status = new Label { Text = "就绪 / Ready" };
    private readonly Button _btnHighlight, _btnSuppress, _btnRebuild;

    public FwPanel()
    {
        var btnRecognize = new Button { Text = "识别选中实体 / Recognize" };
        btnRecognize.Click += (_, __) => Safe(() => DoRecognize());
        var btnClear = new Button { Text = "清除 / Clear" };
        btnClear.Click += (_, __) => Safe(() => { FwSession.Clear(RhinoDoc.ActiveDoc); Refresh(); });

        _btnHighlight = new Button { Text = "高亮 / Highlight" };
        _btnHighlight.Click += (_, __) => Safe(() => DoHighlight());
        _btnSuppress = new Button { Text = "抑制 / Suppress" };
        _btnSuppress.Click += (_, __) => Safe(() => DoSuppress());
        var btnRebuild = new Button { Text = "应用重建 / Rebuild" };
        btnRebuild.Click += (_, __) => Safe(() => DoRebuild());
        _btnRebuild = btnRebuild;

        var btnEvidence = new Button { Text = "曲面证据 / Evidence" };
        btnEvidence.Click += (_, __) => Safe(() => RhinoApp.WriteLine(FwApi.Evidence(RhinoDoc.ActiveDoc)));
        var btnRepair = new Button { Text = "整体修复毛坯 / Repair all" };
        btnRepair.Click += (_, __) => Safe(() =>
        {
            RhinoApp.WriteLine(FwApi.RepairAll(RhinoDoc.ActiveDoc));
            Refresh();
        });
        var btnTest = new Button { Text = "自测 / Self-test" };
        btnTest.Click += (_, __) => Safe(() => RhinoApp.WriteLine(FwApi.SelfTest()));

        _list.SelectedIndexChanged += (_, __) => RefreshDetail();

        var top = new TableLayout
        {
            Rows = { new TableRow(btnRecognize, btnClear) },
            Spacing = new Eto.Drawing.Size(4, 4)
        };

        var featureGroup = new GroupBox
        {
            Text = "特征树 / Feature tree",
            Content = new StackLayout
            {
                Items = { _list },
                Padding = new Eto.Drawing.Padding(4),
                Spacing = 4
            }
        };

        var paramGroup = new GroupBox
        {
            Text = "选中特征 / Selected feature",
            Content = new StackLayout
            {
                Items =
                {
                    _detail,
                    new TableLayout
                    {
                        Rows =
                        {
                            new TableRow(new Label { Text = "参数名 / Parameter" }, _paramKey),
                            new TableRow(new Label { Text = "新值 / New value" }, _paramValue),
                        },
                        Spacing = new Eto.Drawing.Size(4, 4)
                    }
                },
                Padding = new Eto.Drawing.Padding(4),
                Spacing = 4
            }
        };

        var actions = new TableLayout
        {
            Rows =
            {
                new TableRow(_btnHighlight, _btnSuppress),
                new TableRow(_btnRebuild, btnEvidence),
                new TableRow(btnRepair, btnTest),
            },
            Spacing = new Eto.Drawing.Size(4, 4)
        };

        Content = new Scrollable
        {
            Content = new StackLayout
            {
                Items = { top, featureGroup, paramGroup, actions, _status },
                Padding = new Eto.Drawing.Padding(6),
                Spacing = 6
            }
        };

        Refresh();
    }

    private void Safe(Action action)
    {
        try { action(); }
        catch (Exception ex)
        {
            RhinoApp.WriteLine("FeatureWorks 面板错误 / panel error: " + ex.Message);
            _status.Text = "错误 / Error: " + ex.Message;
        }
    }

    private void DoRecognize()
    {
        RhinoDoc doc = RhinoDoc.ActiveDoc;
        if (doc == null) return;
        var go = new GetObject
        {
            GeometryFilter = ObjectType.Brep,
            SubObjectSelect = false
        };
        go.SetCommandPrompt("选择要识别的 B-Rep 实体 / Select a Brep solid");
        go.Get();
        if (go.CommandResult() != Result.Success) return;
        ObjRef? ore = go.Object(0);
        if (ore == null) return;
        _status.Text = FwApi.RecognizeInDocument(doc, ore.ObjectId);
        Refresh();
    }

    private int SelectedIndex => _list.SelectedIndex;

    private void DoHighlight()
    {
        int i = SelectedIndex;
        if (i < 0 || i >= FwSession.Features.Count) { _status.Text = "先选一个特征 / Select a feature"; return; }
        FwSession.Highlight(RhinoDoc.ActiveDoc, i);
        _status.Text = "高亮 / Highlighting: " + FwSession.Features[i].DisplayName;
    }

    private void DoSuppress()
    {
        int i = SelectedIndex;
        if (i < 0 || i >= FwSession.Features.Count) { _status.Text = "先选一个特征 / Select a feature"; return; }
        _status.Text = FwApi.Suppress(RhinoDoc.ActiveDoc, i);
        Refresh();
    }

    private void DoRebuild()
    {
        int i = SelectedIndex;
        if (i < 0 || i >= FwSession.Features.Count) { _status.Text = "先选一个特征 / Select a feature"; return; }
        string key = _paramKey.Text ?? "";
        if (string.IsNullOrWhiteSpace(key) || key == "-") { _status.Text = "该特征无可改参数 / No editable parameter"; return; }
        if (!double.TryParse(_paramValue.Text, NumberStyles.Any, CultureInfo.InvariantCulture, out double val))
        {
            _status.Text = "新值必须是数字 / New value must be a number";
            return;
        }
        _status.Text = FwApi.Rebuild(RhinoDoc.ActiveDoc, i, key, val);
        Refresh();
    }

    private void RefreshDetail()
    {
        int i = SelectedIndex;
        if (i < 0 || i >= FwSession.Features.Count)
        {
            _detail.Text = "（未选中特征 / No feature selected）";
            _paramKey.Text = "-";
            _paramValue.Text = "";
            return;
        }
        RecognizedFeature f = FwSession.Features[i];
        _detail.Text = "[" + i + "] " + f.DisplayName + "  " + f.Type +
                       "  面数=" + f.FaceIndices.Count;
        string[] keys = f.Parameters.Keys.ToArray();
        if (keys.Length == 0)
        {
            _paramKey.Text = "-";
            _paramValue.Text = "";
        }
        else
        {
            string first = keys[0];
            _paramKey.Text = first;
            _paramValue.Text = f.Parameters[first].ToString("0.####", CultureInfo.InvariantCulture);
        }
    }

    public void Refresh()
    {
        _list.Items.Clear();
        var feats = FwSession.Features;
        for (int i = 0; i < feats.Count; i++)
            _list.Items.Add(feats[i].OneLine(i));
        bool has = feats.Count > 0;
        _btnHighlight.Enabled = has;
        _btnSuppress.Enabled = has;
        _btnRebuild.Enabled = has;
        _status.Text = FwSession.HasTarget
            ? FwSession.LastSummary + "  |  容差 " + FwSession.Tolerance.ToString("0.######")
            : "未识别 / Not recognized. 点「识别选中实体」开始。";
        RefreshDetail();
    }

    public void PanelShown(uint docSerialNumber, ShowPanelReason reason) => Refresh();
    public void PanelHidden(uint docSerialNumber, ShowPanelReason reason) { }
    public void PanelClosing(uint docSerialNumber, bool allowHiding) { }

    /// <summary>注册面板（插件 OnLoad 调用一次）。</summary>
    public static void Register()
    {
        try
        {
            if (FeatureWorksPlugin.Instance == null) return;
            if (!Panels.DockBarIdInUse(PanelId))
                Panels.RegisterPanel(FeatureWorksPlugin.Instance, typeof(FwPanel),
                                     "特征识别 / FeatureWorks", null, PanelType.System);
        }
        catch (Exception ex)
        {
            RhinoApp.WriteLine("FeatureWorks 面板注册失败 / panel register failed: " + ex.Message);
        }
    }

    public static void Open()
    {
        Register();
        Panels.OpenPanel(PanelId);
    }
}

/// <summary>打开特征识别面板的命令 FWPanel。</summary>
[CommandStyle(Style.ScriptRunner)]
public class FwPanelCommand : Rhino.Commands.Command
{
    public override string EnglishName => "FWPanel";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        FwPanel.Open();
        return Result.Success;
    }
}
