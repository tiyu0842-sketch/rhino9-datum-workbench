using System;
using System.Collections.Generic;
using System.Linq;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

public class FwTestItem
{
    public string Name { get; set; } = "";
    public bool Pass { get; set; }
    public string Detail { get; set; } = "";
}

public class FwTestReport
{
    public List<FwTestItem> Items { get; } = new();
    public int Pass => Items.Count(i => i.Pass);
    public int Total => Items.Count;
    public bool AllPass => Total > 0 && Pass == Total;

    public string Render()
    {
        var lines = new List<string>
        {
            "==========================================================",
            " RhinoFeatureWorks v1.1 端到端自测 / Self-test",
            "=========================================================="
        };
        for (int i = 0; i < Items.Count; i++)
            lines.Add(string.Format(" [{0}] {1,-46} {2,-4} | {3}",
                i + 1, Items[i].Name, Items[i].Pass ? "PASS" : "FAIL", Items[i].Detail));
        lines.Add("----------------------------------------------------------");
        lines.Add(string.Format(" RESULT: {0}/{1} PASS", Pass, Total));
        lines.Add("==========================================================");
        return string.Join(Environment.NewLine, lines);
    }
}

/// <summary>
/// 9 项端到端测试，移植自《项目总控与工程交付手册》第四部分，并针对 Rhino 9 修正：
///  - CreateFilletEdges 结果判空；Defillet 失败不抛异常；
///  - 每项独立 try/catch，一项失败不影响其余；
///  - 纯计算，不触碰 doc / UI，便于脚本反射调用。
/// </summary>
public static class FwSelfTest
{
    private const double Tol = 0.001;

    public static FwTestReport Run()
    {
        var rep = new FwTestReport();
        var engine = new FeatureRecognitionEngine();

        // 基准零件：100x80x30 底座 + R6 通孔 + 深度 10 的矩形盲槽
        Brep? solid = BuildBasePart();
        if (solid == null)
        {
            rep.Items.Add(new FwTestItem { Name = "构造基准零件", Pass = false, Detail = "boolean failed" });
            return rep;
        }

        Brep cleanBrep = solid;
        List<RecognizedFeature> features = new();
        try
        {
            var r = engine.RecognizeAll(solid.DuplicateBrep(), Tol);
            cleanBrep = r.CleanBrep;
            features = r.Features;
        }
        catch (Exception ex)
        {
            rep.Items.Add(new FwTestItem { Name = "识别引擎不抛异常", Pass = false, Detail = ex.Message });
            return rep;
        }

        var hole = features.FirstOrDefault(f => f.Type == FeatureType.SimpleHole);
        var pocket = features.FirstOrDefault(f => f.Type == FeatureType.ExtrudeCut);

        // 测试 1：孔半径 R6
        rep.Items.Add(new FwTestItem
        {
            Name = "测试 1 孔特征识别 (R6) / Hole recognition",
            Pass = hole != null && hole.Parameters.TryGetValue("Radius", out double r1) && Math.Abs(r1 - 6.0) < 0.05,
            Detail = hole == null ? "no hole found" : "Radius=" + (hole.Parameters.TryGetValue("Radius", out double rv) ? rv.ToString("0.####") : "?")
        });

        // 测试 2：槽深 10
        rep.Items.Add(new FwTestItem
        {
            Name = "测试 2 凹槽拉伸识别 (Depth 10) / Pocket",
            Pass = pocket != null && pocket.Parameters.TryGetValue("Depth", out double d2) && Math.Abs(d2 - 10.0) < 0.05,
            Detail = pocket == null ? "no pocket found" : "Depth=" + (pocket.Parameters.TryGetValue("Depth", out double dv) ? dv.ToString("0.####") : "?")
        });

        // 测试 3：孔抑制还原
        try
        {
            Brep sup = FeatureReconstructionService.SuppressFeature(cleanBrep, hole, Tol);
            var (_, after) = engine.RecognizeAll(sup.DuplicateBrep(), Tol);
            bool pass = after.All(f => f.Type != FeatureType.SimpleHole);
            rep.Items.Add(new FwTestItem
            {
                Name = "测试 3 孔抑制还原 / Hole suppression",
                Pass = pass,
                Detail = "IsSolid=" + sup.IsSolid + " faces=" + sup.Faces.Count + " holesRemaining=" + after.Count(f => f.Type == FeatureType.SimpleHole)
            });
        }
        catch (Exception ex)
        {
            rep.Items.Add(new FwTestItem { Name = "测试 3 孔抑制还原 / Hole suppression", Pass = false, Detail = ex.Message });
        }

        // 测试 4：孔径参数重算 R6 -> R10
        Brep rebuiltHole = cleanBrep;
        List<RecognizedFeature> feats4 = features;
        try
        {
            rebuiltHole = FeatureReconstructionService.RebuildWithUpdatedParameters(
                cleanBrep, hole, new Dictionary<string, double> { { "Radius", 10.0 } }, Tol);
            var (_, f4) = engine.RecognizeAll(rebuiltHole.DuplicateBrep(), Tol);
            feats4 = f4;
            var updated = f4.FirstOrDefault(f => f.Type == FeatureType.SimpleHole);
            bool pass = updated != null && updated.Parameters.TryGetValue("Radius", out double r4) && Math.Abs(r4 - 10.0) < 0.05;
            rep.Items.Add(new FwTestItem
            {
                Name = "测试 4 孔径重算 (R6->R10) / Hole rebuild",
                Pass = pass,
                Detail = updated == null ? "no hole after rebuild" : "Radius=" + (updated.Parameters.TryGetValue("Radius", out double rv4) ? rv4.ToString("0.####") : "?")
            });
        }
        catch (Exception ex)
        {
            rep.Items.Add(new FwTestItem { Name = "测试 4 孔径重算 (R6->R10) / Hole rebuild", Pass = false, Detail = ex.Message });
        }

        // 测试 5：槽深重算 10 -> 18
        try
        {
            var curPocket = feats4.FirstOrDefault(f => f.Type == FeatureType.ExtrudeCut);
            Brep rebuilt = FeatureReconstructionService.RebuildWithUpdatedParameters(
                rebuiltHole, curPocket, new Dictionary<string, double> { { "Depth", 18.0 } }, Tol);
            var (_, f5) = engine.RecognizeAll(rebuilt.DuplicateBrep(), Tol);
            var updated = f5.FirstOrDefault(f => f.Type == FeatureType.ExtrudeCut);
            bool pass = updated != null && updated.Parameters.TryGetValue("Depth", out double d5) && Math.Abs(d5 - 18.0) < 0.05;
            rep.Items.Add(new FwTestItem
            {
                Name = "测试 5 槽深重算 (10->18) / Pocket rebuild",
                Pass = pass,
                Detail = updated == null ? "no pocket after rebuild" : "Depth=" + (updated.Parameters.TryGetValue("Depth", out double dv5) ? dv5.ToString("0.####") : "?")
            });
        }
        catch (Exception ex)
        {
            rep.Items.Add(new FwTestItem { Name = "测试 5 槽深重算 (10->18) / Pocket rebuild", Pass = false, Detail = ex.Message });
        }

        // 测试 6：圆角识别 + 抑制还原尖角（6 面）
        try
        {
            Brep? filleted = BuildFilletedBox();
            if (filleted == null)
            {
                rep.Items.Add(new FwTestItem { Name = "测试 6 圆角识别与抑制还原尖角 / Defillet", Pass = false, Detail = "CreateFilletEdges returned null" });
            }
            else
            {
                var (fclean, ff) = engine.RecognizeAll(filleted, Tol);
                var filletFeat = ff.FirstOrDefault(f => f.Type == FeatureType.Fillet);
                Brep defilleted = filletFeat != null
                    ? FeatureReconstructionService.SuppressFeature(fclean, filletFeat, Tol)
                    : fclean;
                bool pass = filletFeat != null && defilleted.IsSolid && defilleted.Faces.Count == 6;
                rep.Items.Add(new FwTestItem
                {
                    Name = "测试 6 圆角识别与抑制还原尖角 / Defillet",
                    Pass = pass,
                    Detail = "fillets=" + ff.Count(f => f.Type == FeatureType.Fillet) +
                             " radius=" + (filletFeat != null && filletFeat.Parameters.TryGetValue("Radius", out double r6) ? r6.ToString("0.####") : "-") +
                             " after.IsSolid=" + defilleted.IsSolid + " faces=" + defilleted.Faces.Count + " (expect 6)"
                });
            }
        }
        catch (Exception ex)
        {
            rep.Items.Add(new FwTestItem { Name = "测试 6 圆角识别与抑制还原尖角 / Defillet", Pass = false, Detail = ex.Message });
        }

        // 附加：特征树序列化往返
        try
        {
            Brep carrier = cleanBrep.DuplicateBrep();
            FeatureTreeStorage.Save(carrier, features);
            var loaded = FeatureTreeStorage.Load(carrier);
            rep.Items.Add(new FwTestItem
            {
                Name = "测试 7 特征树持久化往返 / Tree round-trip",
                Pass = loaded.Count == features.Count,
                Detail = "saved=" + features.Count + " loaded=" + loaded.Count
            });
        }
        catch (Exception ex)
        {
            rep.Items.Add(new FwTestItem { Name = "测试 7 特征树持久化往返 / Tree round-trip", Pass = false, Detail = ex.Message });
        }

        // 测试 8：曲面原生/修剪证据——带孔+槽的零件应识别出内环面与未修剪余量
        try
        {
            SurfaceEvidenceReport ev = SurfaceEvidenceService.Analyze(solid.DuplicateBrep(), Tol);
            bool pass = ev.InnerLoopFaces >= 2 && ev.OverhangFaces >= 4 && ev.MaxOverhangZ > 0.5;
            rep.Items.Add(new FwTestItem
            {
                Name = "测试 8 曲面原生/修剪证据 / Surface evidence",
                Pass = pass,
                Detail = "innerLoops=" + ev.InnerLoopFaces + " overhang=" + ev.OverhangFaces +
                         " maxZ=" + ev.MaxOverhangZ.ToString("0.##")
            });
        }
        catch (Exception ex)
        {
            rep.Items.Add(new FwTestItem { Name = "测试 8 曲面原生/修剪证据 / Surface evidence", Pass = false, Detail = ex.Message });
        }

        // 测试 9：整体修复——删掉所有特征面（孔壁 + 槽内壁），用剩余外表面的
        // 原生曲面缝回 240000 毛坯。注意：基准零件同时有孔和槽，只删槽不够。
        try
        {
            var allFeatureFaces = new List<int>();
            foreach (RecognizedFeature feat in features)
                allFeatureFaces.AddRange(feat.FaceIndices);
            Brep? blank = SurfaceEvidenceService.RepairToBlank(solid, allFeatureFaces, Tol);
            double blankVol = 0.0;
            if (blank != null && blank.IsSolid)
                try { blankVol = VolumeMassProperties.Compute(blank)?.Volume ?? 0.0; } catch { }
            const double expected = 100 * 80 * 30; // 240000
            bool pass = blank != null && blank.IsSolid && Math.Abs(blankVol - expected) < 1.0;
            rep.Items.Add(new FwTestItem
            {
                Name = "测试 9 整体修复还原毛坯 / Repair to blank",
                Pass = pass,
                Detail = "removed=" + allFeatureFaces.Count + " faces ; " +
                         (blank == null ? "repair returned null" :
                          "solid=" + blank.IsSolid + " vol=" + blankVol.ToString("0.#") +
                          " (expect " + expected + ")")
            });
        }
        catch (Exception ex)
        {
            rep.Items.Add(new FwTestItem { Name = "测试 9 整体修复还原毛坯 / Repair to blank", Pass = false, Detail = ex.Message });
        }

        return rep;
    }

    private static Brep? BuildBasePart()
    {
        try
        {
            var baseBox = new Box(Plane.WorldXY,
                new Interval(0, 100), new Interval(0, 80), new Interval(0, 30));
            Brep solid = baseBox.ToBrep();

            var holeCyl = new Cylinder(new Circle(new Plane(new Point3d(20, 20, -1), Vector3d.ZAxis), 6.0), 32.0);
            Brep[]? r1 = Brep.CreateBooleanDifference(solid, holeCyl.ToBrep(true, true), Tol);
            if (r1 == null || r1.Length == 0) return null;
            solid = r1[0];

            var pocketBox = new Box(Plane.WorldXY,
                new Interval(50, 90), new Interval(20, 60), new Interval(20, 31));
            Brep[]? r2 = Brep.CreateBooleanDifference(solid, pocketBox.ToBrep(), Tol);
            if (r2 == null || r2.Length == 0) return null;
            return r2[0];
        }
        catch { return null; }
    }

    private static Brep? BuildFilletedBox()
    {
        try
        {
            var box = new Box(Plane.WorldXY,
                new Interval(120, 170), new Interval(0, 50), new Interval(0, 30));
            Brep b = box.ToBrep();
            int[] topEdges = b.Edges
                .Where(e => Math.Abs(e.PointAtStart.Z - 30.0) < 0.01 && Math.Abs(e.PointAtEnd.Z - 30.0) < 0.01)
                .Select(e => e.EdgeIndex).ToArray();
            if (topEdges.Length == 0) return null;
            Brep[]? res = Brep.CreateFilletEdges(b, topEdges,
                Enumerable.Repeat(3.0, topEdges.Length).ToArray(),
                Enumerable.Repeat(3.0, topEdges.Length).ToArray(),
                BlendType.Fillet, RailType.RollingBall, Tol);
            return res != null && res.Length > 0 ? res[0] : null;
        }
        catch { return null; }
    }
}
