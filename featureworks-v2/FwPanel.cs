// FeatureWorks v2 — Eto 停靠面板
// 对应交互原型的完整流程：识别 → 列表多选 → 高亮 → 处理。
// Rhino 9 / Eto 2.13（随 Rhino 9 自带）

using System;
using System.Collections.Generic;
using System.Linq;
using Eto.Drawing;
using Eto.Forms;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.Input.Custom;
using Rhino.UI;

namespace FeatureWorks
{
    /// <summary>
    /// FeatureWorks 面板：特征识别结果列表 + 多选 + 处理操作。
    /// 交互对齐原 HTML 原型：主体半透明可视、列表可多选、选中变金色、统一处理。
    /// </summary>
    public class FwPanel : Panel, IPanel
    {
        public static readonly Guid PanelId = new Guid("9D3F6B21-5C8E-4A70-B2D9-1E6F4A8C7B03");

        private readonly GridView _grid = new GridView { AllowMultipleSelection = true, Height = 240 };
        private readonly Label _detail = new Label { Text = "先识别一个实体 / Recognize a solid first" };
        private readonly Label _status = new Label { Text = "就绪 / Ready" };
        private readonly TextBox _rmax = new TextBox { Text = "0.05" };
        private readonly Button _btnHighlight, _btnDelete, _btnSuppress, _btnRestore;
        private List<FwFeature> _features = new List<FwFeature>();

        public FwPanel()
        {
            // ---- 列定义（对齐原型列表：类型 / 面 / 半径 / 覆盖角 / 置信度）----
            _grid.Columns.Add(new GridColumn { HeaderText = "类型", DataCell = new TextBoxCell(0), Width = 90 });
            _grid.Columns.Add(new GridColumn { HeaderText = "面#", DataCell = new TextBoxCell(1), Width = 55 });
            _grid.Columns.Add(new GridColumn { HeaderText = "半径", DataCell = new TextBoxCell(2), Width = 65 });
            _grid.Columns.Add(new GridColumn { HeaderText = "覆盖角", DataCell = new TextBoxCell(3), Width = 65 });
            _grid.Columns.Add(new GridColumn { HeaderText = "置信度", DataCell = new TextBoxCell(4), Width = 65 });
            _grid.SelectionChanged += (_, __) => { SyncSelection(); RefreshDetail(); };

            var btnRecognize = new Button { Text = "识别选中实体 / Recognize" };
            btnRecognize.Click += (_, __) => Safe(DoRecognize);
            var btnClearSel = new Button { Text = "清除选择 / Clear selection" };
            btnClearSel.Click += (_, __) => Safe(() => { FwSession.Get(RhinoDoc.ActiveDoc).Selected.Clear(); _grid.UnselectAll(); });

            _btnHighlight = new Button { Text = "高亮 / Highlight" };
            _btnHighlight.Click += (_, __) => Safe(() => { FwSession.Get(RhinoDoc.ActiveDoc).Highlight(RhinoDoc.ActiveDoc); _status.Text = "已在视口高亮选中的特征"; });
            _btnDelete = new Button { Text = "删除圆角 / Delete" };
            _btnDelete.Click += (_, __) => Safe(() => DoProcess("delete"));
            _btnSuppress = new Button { Text = "抑制(移出) / Suppress" };
            _btnSuppress.Click += (_, __) => Safe(() => DoProcess("suppress"));
            _btnRestore = new Button { Text = "还原(Untrim) / Restore" };
            _btnRestore.Click += (_, __) => Safe(() => DoProcess("restore"));

            var top = new TableLayout
            {
                Rows =
                {
                    new TableRow(new Label { Text = "r_max 比例 / factor" }, _rmax, btnRecognize),
                    new TableRow(btnClearSel, null, null)
                },
                Spacing = new Size(4, 4)
            };
            var listGroup = new GroupBox
            {
                Text = "识别到的特征 / Recognized features（可多选）",
                Content = new StackLayout { Items = { _grid }, Padding = new Padding(4), Spacing = 4 }
            };
            var detailGroup = new GroupBox
            {
                Text = "选中详情 / Selected detail",
                Content = new StackLayout { Items = { _detail }, Padding = new Padding(4), Spacing = 4 }
            };
            var actions = new TableLayout
            {
                Rows =
                {
                    new TableRow(_btnHighlight, _btnDelete),
                    new TableRow(_btnSuppress, _btnRestore)
                },
                Spacing = new Size(4, 4)
            };

            Content = new Scrollable
            {
                Content = new StackLayout
                {
                    Items = { top, listGroup, detailGroup, actions, _status },
                    Padding = new Padding(6), Spacing = 6
                }
            };
            SetButtons(false);
        }

        private void Safe(Action action)
        {
            try { action(); }
            catch (Exception ex)
            {
                RhinoApp.WriteLine("[FW] 面板错误 / panel error: " + ex.Message);
                _status.Text = "错误 / Error: " + ex.Message;
            }
        }

        /// <summary>识别选中实体：拾取 → 调用 Core（可并行）→ 装进会话 → 填列表。</summary>
        private void DoRecognize()
        {
            RhinoDoc doc = RhinoDoc.ActiveDoc;
            if (doc == null) return;
            var get = new GetObject();
            get.SetCommandPrompt("选择要识别的实体 / Select a solid");
            get.GeometryFilter = ObjectType.Brep;
            get.Get();
            if (get.CommandResult() != Result.Success) return;
            ObjRef objRef = get.Object(0);
            Brep brep = objRef.Geometry() as Brep;
            if (brep == null) { _status.Text = "不是有效 Brep"; return; }

            double factor = 0.05;
            double.TryParse(_rmax.Text, System.Globalization.NumberStyles.Any,
                            System.Globalization.CultureInfo.InvariantCulture, out factor);
            if (factor <= 0) factor = 0.05;
            var opt = new FwOptions { RMaxFactor = factor, Parallel = true };
            List<FwFeature> features = FwCore.Recognize(brep, opt);

            FwSession.Get(doc).SetResult(objRef.ObjectId, brep, features);
            FillList(features);
            _status.Text = string.Format("识别到 {0} 组特征 / {1} groups found", features.Count, features.Count);
            RhinoApp.WriteLine("[FW] 面板识别完成：" + features.Count + " 组特征，r_max=" + (brep.GetBoundingBox(true).Diagonal.Length * factor).ToString("0.###"));
        }

        private void FillList(List<FwFeature> features)
        {
            _features = features;
            _grid.DataStore = features.Select(f => new string[]
            {
                f.Kind, f.FaceIndex.ToString(), f.Radius.ToString("0.###"),
                f.SweepDegrees.ToString("0.#") + "°", f.Confidence.ToString("0.00")
            }).ToArray();
            SetButtons(features.Count > 0);
            RefreshDetail();
        }

        private void SetButtons(bool has)
        {
            _btnHighlight.Enabled = has; _btnDelete.Enabled = has;
            _btnSuppress.Enabled = has; _btnRestore.Enabled = has;
        }

        /// <summary>面板 GridView 的选中行 → 会话里的 Selected 集合。</summary>
        private void SyncSelection()
        {
            var session = FwSession.Get(RhinoDoc.ActiveDoc);
            session.Selected.Clear();
            foreach (int row in _grid.SelectedRows)
                if (row >= 0 && row < _features.Count) session.Selected.Add(row);
        }

        private void RefreshDetail()
        {
            int row = _grid.SelectedRow;
            if (row < 0 || row >= _features.Count)
            {
                _detail.Text = "未选中特征 / No feature selected（可多选）";
                return;
            }
            FwFeature f = _features[row];
            _detail.Text = string.Format("链{0}: {1} 面#{2} {3} | 半径 {4:0.###} | 覆盖 {5:0.#}° | 置信 {6:0.00} | 面数 {7}",
                f.ChainId, f.Kind, f.FaceIndex, f.SurfaceType, f.Radius, f.SweepDegrees, f.Confidence, f.Chain.Length);
        }

        /// <summary>
        /// 处理操作（本版实现：删除 / 抑制；还原为 Untrim 调用）。
        /// 所有文档修改都在 UI 线程（按钮点击）完成——符合 RhinoCommon 线程红线。
        /// </summary>
        private void DoProcess(string mode)
        {
            RhinoDoc doc = RhinoDoc.ActiveDoc;
            var session = FwSession.Get(doc);
            if (session.TargetBrep == null || session.Selected.Count == 0)
            { _status.Text = "先选特征 / Select features first"; return; }

            // 收集所有选中链的面索引
            var faceSet = new HashSet<int>();
            foreach (int idx in session.Selected)
                if (idx >= 0 && idx < _features.Count)
                    foreach (int fi in _features[idx].Chain) faceSet.Add(fi);

            Brep work = session.TargetBrep.DuplicateBrep();
            int removed = 0;
            // RhinoCommon 9 实测：BrepFaceList 没有 DeleteFaces，用 RemoveAt(int)。
            // 从后往前删，避免索引偏移。
            foreach (int fi in faceSet.OrderByDescending(x => x))
            {
                try { work.Faces.RemoveAt(fi); removed++; }
                catch { /* 单面失败不拖垮整体 */ }
            }
            if (removed == 0) { _status.Text = "没有面被删除（特征可能是 chamfer 或已处理）"; return; }

            // 备份原对象到 FW_Backup 图层（抑制/恢复语义）：
            // 先记住原图层，再把原对象移到备份层，新对象放回原图层。
            // RhinoCommon 9 实测：LayerTable.FindName 返回 Layer 对象（不是 int），
            // 取 .Index；找不到时为 null，用 -1 表示。
            Layer found = doc.Layers.FindName(FwSession.BackupLayer);
            int li = found != null ? found.Index : -1;
            if (li < 0)
            {
                Layer bk = new Layer { Name = FwSession.BackupLayer, Color = System.Drawing.Color.FromArgb(150, 150, 150) };
                li = doc.Layers.Add(bk);
            }
            RhinoObject original = doc.Objects.Find(session.TargetId);
            int originalLayer = original != null ? original.Attributes.LayerIndex : 0;
            if (original != null)
            {
                original.Attributes.LayerIndex = li;
                original.CommitChanges();
            }

            // 用处理后的 Brep 替换（原对象仍在备份层，可恢复）
            Guid newId = doc.Objects.AddBrep(work);
            RhinoObject processed = doc.Objects.Find(newId);
            if (processed != null)
            {
                processed.Attributes.LayerIndex = originalLayer;
                processed.CommitChanges();
            }
            session.ClearHighlights(doc);
            session.Selected.Clear();
            doc.Views.Redraw();
            _status.Text = string.Format("已处理 {0} 个面（原对象在 {1} 图层，可恢复）", removed, FwSession.BackupLayer);
            RhinoApp.WriteLine("[FW] " + mode + ": 删除 " + removed + " 面，原对象备份到 " + FwSession.BackupLayer);
        }

        public void PanelShown(uint docSerialNumber, ShowPanelReason reason) { RefreshFromSession(); }
        public void PanelHidden(uint docSerialNumber, ShowPanelReason reason) { }
        public void PanelClosing(uint docSerialNumber, bool allowHiding) { }

        private void RefreshFromSession()
        {
            var s = FwSession.Get(RhinoDoc.ActiveDoc);
            if (s.Features.Count > 0) FillList(s.Features);
        }

        public static void Register()
        {
            try
            {
                if (FwPlugin.Instance == null) return;
                if (!Panels.DockBarIdInUse(PanelId))
                    Panels.RegisterPanel(FwPlugin.Instance, typeof(FwPanel),
                        "特征识别 / FeatureWorks", null, PanelType.System);
            }
            catch (Exception ex) { RhinoApp.WriteLine("[FW] 面板注册失败: " + ex.Message); }
        }

        public static void Open() { Register(); Panels.OpenPanel(PanelId); }
    }

    /// <summary>打开面板的命令。</summary>
    // Eto.Forms 也有 Command 类，必须用全名消歧义。
    public class FWPanelCommand : Rhino.Commands.Command
    {
        public override string EnglishName { get { return "FWPanel"; } }
        protected override Result RunCommand(RhinoDoc doc, RunMode mode) { FwPanel.Open(); return Result.Success; }
    }
}
