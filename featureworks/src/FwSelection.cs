using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Rhino;
using Rhino.Display;
using Rhino.Geometry;
using Rhino.UI;
// Rhino.Geometry 里也有 Point（灯光/标注用），这里所有 Point 都是屏幕像素坐标。
using Point = System.Drawing.Point;

namespace RhinoFeatureWorks;

/// <summary>
/// v1.6 共享选中集 —— 视口 / 面板 / 两个模块共同读写同一份 HashSet&lt;int&gt;。
///
/// 旧版 FwCancelPanel 有这段互斥逻辑：
///     (source == _filletList ? _holeList : _filletList).SelectedKeys = new string[0];
/// 用户的原话是「两边可以同时相互交互，而不是去选择那一边」——这份互斥就是根因。
/// v1.6 删掉它：两个通道的勾选合并成一份集合，任何一个入口改动都通知所有入口。
///
/// 不用 System.Action：本机 WeaverBird 把 Action 塞进 System 命名空间，
/// 连 System.Action 都 CS0433（见 rhinocommon-pitfalls.md），自定义委托最稳。
/// </summary>
public static class FwSelectionState
{
    public delegate void SelectionChangedHandler(string origin);
    public static SelectionChangedHandler? Changed;

    private static readonly HashSet<int> _selected = new();
    private static int _hover = -1;

    public static IReadOnlyCollection<int> Selected => _selected;
    public static int Count => _selected.Count;
    public static int HoverIndex => _hover;
    public static bool IsSelected(int i) => _selected.Contains(i);

    public static void Clear(bool notify = true)
    {
        _selected.Clear();
        _hover = -1;
        if (notify) Notify("clear");
    }

    /// <summary>Hover 只影响视口描边，不触发面板整体刷新，避免鼠标一动就重刷勾选。</summary>
    public static void SetHover(int index)
    {
        if (_hover == index) return;
        _hover = index;
        FwFocusSession.SyncSelectionVisuals();
        try { RhinoDoc.ActiveDoc?.Views.Redraw(); } catch { }
    }

    public static void Toggle(int index, string origin = "")
    {
        if (index < 0 || index >= FwFocusSession.AllGroupCount) return;
        if (!_selected.Add(index)) _selected.Remove(index);
        Notify(origin);
    }

    /// <summary>视口点选/框选：additive=false 时先清空，true 时 Shift/Ctrl 累加。</summary>
    public static void SelectMany(IEnumerable<int> indices, bool additive, string origin = "")
    {
        var hit = new HashSet<int>();
        foreach (int i in indices)
            if (i >= 0 && i < FwFocusSession.AllGroupCount) hit.Add(i);
        if (!additive) _selected.Clear();
        _selected.UnionWith(hit);
        Notify(origin);
    }

    /// <summary>面板把两个列表的勾选一次性写回（不再互斥）。</summary>
    public static void ReplaceAll(IEnumerable<int> indices, string origin = "panel")
    {
        _selected.Clear();
        foreach (int i in indices)
            if (i >= 0 && i < FwFocusSession.AllGroupCount) _selected.Add(i);
        Notify(origin);
    }

    public static int FilletCount => _selected.Count(i => i < FwFocusSession.FilletGroups.Count);
    public static int HoleCount => _selected.Count(i => i >= FwFocusSession.FilletGroups.Count);

    /// <summary>严格两模块：执行器只取自己通道里的选中项，另一通道的勾选不动。</summary>
    public static List<int> IndicesInChannel(string channel)
    {
        int cut = FwFocusSession.FilletGroups.Count;
        var list = new List<int>();
        foreach (int i in _selected)
        {
            if (channel == "Fillet" && i < cut) list.Add(i);
            if (channel == "Hole" && i >= cut) list.Add(i);
        }
        list.Sort();
        return list;
    }

    public static void Notify(string origin)
    {
        try { Changed?.Invoke(origin); } catch { }
        FwFocusSession.SyncSelectionVisuals();
        try { RhinoDoc.ActiveDoc?.Views.Redraw(); } catch { }
    }
}

/// <summary>
/// v1.6 常驻视口监听器 —— 把「在原有 Rhino 界面上鼠标框选已经标红的物体」变成真的。
///
/// 为什么必须自己接管左键（E-024 的根因）：
///   FwFocusConduit 用 DrawForeground 画出来的橙色特征面只是「显示影子」，不是文档对象；
///   ObjectCulling 又把源对象从绘制里剔除，所以 Rhino 原生点选/框选都够不到它们。
///   用户看到的就是「只能在那个框里面去选择」。
/// 做法：MouseCallback 接管左键 → 自己画框选矩形 → 用 WorldToClient 把每个特征组的
///   世界包围盒投影成屏幕矩形 → 与拖框做相交测试 → 写回 FwSelectionState。
///   不建文档对象、不进 Undo、不污染 .3dm；关闭聚焦即 Stop()。
///
/// 已离线核对（RhinoCommon.xml + 活进程反射）：
///   MouseCallback.OnMouseDown/OnMouseMove/OnMouseUp/OnMouseLeave(MouseCallbackEventArgs)
///   MouseCallbackEventArgs.View / MouseButton / ViewportPoint / ShiftKeyDown / CtrlKeyDown / Cancel
///   RhinoViewport.WorldToClient(Point3d) -> Point2d
///   DisplayPipeline.Draw2dRectangle(Rectangle, Color, Int32, Color)
/// </summary>
public class FwMouseWatcher : MouseCallback
{
    private static FwMouseWatcher? _instance;
    public static bool IsActive => _instance != null && _instance.Enabled;

    private Point _down = Point.Empty;
    private Point _current = Point.Empty;
    private bool _dragging;
    private bool _additive;
    private const int DragThreshold = 4;

    public static Point DragStart => _instance?._down ?? Point.Empty;
    public static Point DragCurrent => _instance?._current ?? Point.Empty;
    public static bool Dragging => _instance?._dragging ?? false;

    public static void Begin()
    {
        Stop();
        try
        {
            var w = new FwMouseWatcher { Enabled = true };
            _instance = w;
        }
        catch (Exception ex)
        {
            RhinoApp.WriteLine("FwMouseWatcher 启动失败 / start failed: " + ex.Message);
            _instance = null;
        }
    }

    public static void Stop()
    {
        if (_instance == null) return;
        try { _instance.Enabled = false; } catch { }
        _instance = null;
    }

    protected override void OnMouseDown(MouseCallbackEventArgs e)
    {
        base.OnMouseDown(e);
        if (!FwFocusSession.HasActive || e.MouseButton != MouseButton.Left) return;
        RhinoView? view = e.View;
        if (view == null) return;

        _down = e.ViewportPoint;
        _current = _down;
        _dragging = true;
        _additive = e.ShiftKeyDown || e.CtrlKeyDown;
        // 接管左键：不取消的话 Rhino 会同时画自己的框选矩形，且选不中被 cull 的源对象。
        e.Cancel = true;
    }

    protected override void OnMouseMove(MouseCallbackEventArgs e)
    {
        base.OnMouseMove(e);
        if (!FwFocusSession.HasActive) return;
        RhinoView? view = e.View;
        if (view == null) return;
        _current = e.ViewportPoint;

        if (_dragging)
        {
            try { RhinoDoc.ActiveDoc?.Views.Redraw(); } catch { }
        }
        else
        {
            FwSelectionState.SetHover(HitTest(view, _current));
        }
    }

    protected override void OnMouseUp(MouseCallbackEventArgs e)
    {
        base.OnMouseUp(e);
        if (!FwFocusSession.HasActive || e.MouseButton != MouseButton.Left) return;
        RhinoView? view = e.View;
        if (view == null) { Reset(); return; }

        _current = e.ViewportPoint;
        bool wasDrag = _dragging &&
            (Math.Abs(_current.X - _down.X) > DragThreshold ||
             Math.Abs(_current.Y - _down.Y) > DragThreshold);

        var hits = new List<int>();
        if (wasDrag)
        {
            hits = HitTestRect(view, _down, _current);
        }
        else
        {
            int h = HitTest(view, _current);
            if (h >= 0) hits.Add(h);
        }

        Reset();
        // 点空白 = 清空；Shift/Ctrl = 加减选；拖框 = 一次选一片。
        FwSelectionState.SelectMany(hits, _additive,
            wasDrag ? "viewport-window" : "viewport-click");
    }

    protected override void OnMouseLeave(MouseCallbackEventArgs e)
    {
        base.OnMouseLeave(e);
        if (_dragging) return;
        FwSelectionState.SetHover(-1);
    }

    private void Reset()
    {
        _dragging = false;
        _down = Point.Empty;
        _current = Point.Empty;
        try { RhinoDoc.ActiveDoc?.Views.Redraw(); } catch { }
    }

    /// <summary>点选：落在哪个组的屏幕包围盒里，取面积最小者（避免大面盖住小孔）。</summary>
    private static int HitTest(RhinoView view, Point p)
    {
        int best = -1;
        double bestArea = double.MaxValue;
        IReadOnlyList<FwGroupVisual> visuals = FwFocusSession.Visuals;
        for (int i = 0; i < visuals.Count; i++)
        {
            Rectangle r = Project(view, visuals[i]);
            if (r.Width <= 0 || r.Height <= 0 || !r.Contains(p)) continue;
            double area = (double)r.Width * r.Height;
            if (area < bestArea) { bestArea = area; best = i; }
        }
        return best;
    }

    /// <summary>框选：组屏幕包围盒与拖框相交即命中（对齐 Rhino 官方 UntrimHoles 的 window selection）。</summary>
    private static List<int> HitTestRect(RhinoView view, Point a, Point b)
    {
        var rect = new Rectangle(
            Math.Min(a.X, b.X), Math.Min(a.Y, b.Y),
            Math.Abs(a.X - b.X), Math.Abs(a.Y - b.Y));
        var hits = new List<int>();
        IReadOnlyList<FwGroupVisual> visuals = FwFocusSession.Visuals;
        for (int i = 0; i < visuals.Count; i++)
        {
            Rectangle r = Project(view, visuals[i]);
            if (r.Width > 0 && r.Height > 0 && rect.IntersectsWith(r)) hits.Add(i);
        }
        return hits;
    }

    /// <summary>世界包围盒 8 角投影到视口 client 坐标，取轴对齐屏幕矩形。</summary>
    private static Rectangle Project(RhinoView view, FwGroupVisual v)
    {
        if (v == null || !v.Bounds.IsValid) return Rectangle.Empty;
        RhinoViewport vp = view.ActiveViewport;
        if (vp == null) return Rectangle.Empty;

        double minX = double.MaxValue, minY = double.MaxValue;
        double maxX = double.MinValue, maxY = double.MinValue;
        BoundingBox bb = v.Bounds;
        for (int k = 0; k < 8; k++)
        {
            var pt = new Point3d(
                (k & 1) == 0 ? bb.Min.X : bb.Max.X,
                (k & 2) == 0 ? bb.Min.Y : bb.Max.Y,
                (k & 4) == 0 ? bb.Min.Z : bb.Max.Z);
            Point2d c;
            try { c = vp.WorldToClient(pt); }
            catch { return Rectangle.Empty; }
            minX = Math.Min(minX, c.X); maxX = Math.Max(maxX, c.X);
            minY = Math.Min(minY, c.Y); maxY = Math.Max(maxY, c.Y);
        }
        if (minX > maxX || minY > maxY) return Rectangle.Empty;
        return Rectangle.FromLTRB(
            (int)Math.Floor(minX), (int)Math.Floor(minY),
            (int)Math.Ceiling(maxX), (int)Math.Ceiling(maxY));
    }
}
