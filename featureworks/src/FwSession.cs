using System;
using System.Collections.Generic;
using Rhino;
using Rhino.Display;
using Rhino.DocObjects;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

/// <summary>半透明高亮管线：把某个特征占用的面单独着色 + 黄线描边。</summary>
public class FeatureHighlightConduit : DisplayConduit
{
    private readonly DisplayMaterial _mat =
        new DisplayMaterial(System.Drawing.Color.FromArgb(255, 255, 140, 0)) { Transparency = 0.55 };

    public Brep? TargetBrep { get; set; }
    public List<int> HighlightFaceIndices { get; set; } = new();

    protected override void PostDrawObjects(DrawEventArgs e)
    {
        Brep? brep = TargetBrep;
        if (brep == null || HighlightFaceIndices == null || HighlightFaceIndices.Count == 0) return;
        foreach (int idx in HighlightFaceIndices)
        {
            if (idx < 0 || idx >= brep.Faces.Count) continue;
            try
            {
                Brep? single = brep.Faces[idx].DuplicateFace(false);
                if (single == null) continue;
                e.Display.DrawBrepShaded(single, _mat);
                e.Display.DrawBrepWires(single, System.Drawing.Color.FromArgb(255, 235, 90), 1);
            }
            catch { }
        }
    }
}

/// <summary>
/// 会话状态：当前被识别的对象、特征树与高亮管线。
/// 特征树真正的持久化在 Brep.UserDictionary（随 .3dm 保存），这里只缓存以便交互。
/// </summary>
public static class FwSession
{
    public static Guid TargetObjectId { get; private set; } = Guid.Empty;
    public static List<RecognizedFeature> Features { get; private set; } = new();
    public static Brep? CurrentBrep { get; private set; }
    public static double Tolerance { get; private set; } = 0.001;
    public static string LastSummary { get; private set; } = "";

    private static readonly FeatureHighlightConduit Conduit = new();
    private static bool _conduitRegistered;

    public static bool HasTarget => TargetObjectId != Guid.Empty;

    public static void Set(RhinoDoc doc, Guid id, Brep brep, List<RecognizedFeature> features, double tol)
    {
        TargetObjectId = id;
        CurrentBrep = brep;
        Features = features ?? new List<RecognizedFeature>();
        Tolerance = tol;
        LastSummary = Summarize();
        Conduit.TargetBrep = brep;
        Conduit.HighlightFaceIndices = new List<int>();
        EnsureConduit();
        doc.Views.Redraw();
    }

    public static void Highlight(RhinoDoc doc, int featureIndex)
    {
        if (!_conduitRegistered) EnsureConduit();
        if (featureIndex < 0 || featureIndex >= Features.Count)
        {
            Conduit.HighlightFaceIndices = new List<int>();
            Conduit.Enabled = false;
            doc.Views.Redraw();
            return;
        }
        Conduit.TargetBrep = CurrentBrep;
        Conduit.HighlightFaceIndices = new List<int>(Features[featureIndex].FaceIndices);
        Conduit.Enabled = true;
        doc.Views.Redraw();
    }

    public static void ClearHighlight(RhinoDoc doc)
    {
        Conduit.HighlightFaceIndices = new List<int>();
        Conduit.Enabled = false;
        doc.Views.Redraw();
    }

    public static void Clear(RhinoDoc doc)
    {
        TargetObjectId = Guid.Empty;
        Features = new List<RecognizedFeature>();
        CurrentBrep = null;
        LastSummary = "";
        ClearHighlight(doc);
    }

    private static void EnsureConduit()
    {
        if (_conduitRegistered) return;
        Conduit.Enabled = true;
        _conduitRegistered = true;
    }

    /// <summary>从文档里按 id 读回对象，并恢复特征树（重开文件后可用）。</summary>
    public static bool TryRestoreFromDocument(RhinoDoc doc, Guid id)
    {
        RhinoObject? obj = doc.Objects.FindId(id);
        if (obj?.Geometry is not Brep brep) return false;
        var list = FeatureTreeStorage.Load(brep);
        Set(doc, id, brep, list, doc.ModelAbsoluteTolerance);
        return true;
    }

    public static void RefreshBrep(RhinoDoc doc, Brep brep, List<RecognizedFeature> features)
    {
        CurrentBrep = brep;
        Features = features ?? new List<RecognizedFeature>();
        LastSummary = Summarize();
        Conduit.TargetBrep = brep;
        Conduit.HighlightFaceIndices = new List<int>();
        Conduit.Enabled = false;
        doc.Views.Redraw();
    }

    private static string Summarize()
    {
        int f = 0, h = 0, c = 0, x = 0;
        foreach (var t in Features)
        {
            if (t.Type == FeatureType.Fillet) f++;
            else if (t.Type == FeatureType.SimpleHole || t.Type == FeatureType.CounterboreHole) h++;
            else if (t.Type == FeatureType.ExtrudeCut) x++;
            else c++;
        }
        return string.Format("{0} 个特征 / features (圆角 {1}, 孔 {2}, 槽 {3}, 其他 {4})",
            Features.Count, f, h, x, c);
    }

    public static string Report(RhinoDoc doc)
    {
        var lines = new List<string>
        {
            "RhinoFeatureWorks 状态 / Status:",
            "  目标对象 / Target  : " + (HasTarget ? TargetObjectId.ToString() : "(无 / none)"),
            "  特征树 / Tree      : " + (HasTarget ? LastSummary : "(未识别 / not recognized)"),
            "  容差 / Tolerance   : " + Tolerance.ToString("0.######"),
        };
        for (int i = 0; i < Features.Count; i++)
            lines.Add("  " + Features[i].OneLine(i));
        return string.Join(System.Environment.NewLine, lines);
    }
}
