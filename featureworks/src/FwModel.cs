using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Rhino.Collections;
using Rhino.Geometry;

namespace RhinoFeatureWorks;

public enum SurfaceCategory { Plane, Cylinder, Cone, Sphere, Torus, Freeform }
public enum EdgeConvexity { Convex, Concave, Tangent, Unknown }
public enum FeatureType { Fillet, Chamfer, SimpleHole, CounterboreHole, ExtrudeCut, ExtrudeBoss }

/// <summary>一个被识别出来的参数化特征。可序列化进 Brep.UserDictionary，随 .3dm 保存。</summary>
public class RecognizedFeature
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public FeatureType Type { get; set; }
    public string Name { get; set; } = "Feature";
    public bool IsSuppressed { get; set; }
    public List<int> FaceIndices { get; set; } = new();
    public Dictionary<string, double> Parameters { get; set; } = new();
    public Plane ReferencePlane { get; set; } = Plane.WorldXY;
    public Vector3d ExtrudeDirection { get; set; } = Vector3d.ZAxis;
    public Curve? ProfileCurve { get; set; }
    public bool IsThrough { get; set; }

    public string DisplayName => string.IsNullOrEmpty(Name) ? Type.ToString() : Name;

    public string OneLine(int index)
    {
        string ps = Parameters.Count == 0
            ? "-"
            : string.Join(", ", Parameters.Select(kv =>
                kv.Key + "=" + kv.Value.ToString("0.####", CultureInfo.InvariantCulture)));
        return string.Format("[{0}] {1,-20} {2,-16} faces={3,-3} {4}{5}",
            index, DisplayName, Type, FaceIndices.Count, ps, IsSuppressed ? " (SUPPRESSED)" : "");
    }

    // Rhino 9 实测：ArchivableDictionary 没有 GetIntArray / GetGeometry。
    // FaceIndices 用逗号分隔字符串存；ProfileCurve 用 Set(GeometryBase) 存、TryGetValue 读回。
    public ArchivableDictionary Serialize()
    {
        var d = new ArchivableDictionary();
        d.Set("Id", Id);
        d.Set("Type", (int)Type);
        d.Set("Name", Name ?? Type.ToString());
        d.Set("IsSuppressed", IsSuppressed);
        d.Set("IsThrough", IsThrough);
        d.Set("FaceIndices", string.Join(",", FaceIndices));
        d.Set("RefPlane", ReferencePlane);
        d.Set("ExtrudeDir", ExtrudeDirection);
        if (ProfileCurve != null)
            d.Set("ProfileCurve", (GeometryBase)ProfileCurve);

        var p = new ArchivableDictionary();
        p.Set("Count", Parameters.Count);
        int i = 0;
        foreach (var kv in Parameters)
        {
            p.Set("K" + i, kv.Key);
            p.Set("V" + i, kv.Value);
            i++;
        }
        d.Set("Parameters", p);
        return d;
    }

    public static RecognizedFeature Deserialize(ArchivableDictionary d)
    {
        var f = new RecognizedFeature
        {
            Id = d.ContainsKey("Id") ? d.GetGuid("Id") : Guid.NewGuid(),
            Type = (FeatureType)d.GetInteger("Type"),
            Name = d.GetString("Name"),
            IsSuppressed = d.ContainsKey("IsSuppressed") && d.GetBool("IsSuppressed"),
            IsThrough = d.ContainsKey("IsThrough") && d.GetBool("IsThrough"),
            ReferencePlane = d.ContainsKey("RefPlane") ? d.GetPlane("RefPlane") : Plane.WorldXY,
            ExtrudeDirection = d.ContainsKey("ExtrudeDir") ? d.GetVector3d("ExtrudeDir") : Vector3d.ZAxis,
        };

        // 兼容：先试新格式字符串，再试旧格式 int[]（若从别的版本读）
        if (d.ContainsKey("FaceIndices"))
        {
            object? raw = null;
            if (d.TryGetValue("FaceIndices", out raw) && raw is string s && s.Length > 0)
            {
                foreach (string part in s.Split(','))
                    if (int.TryParse(part.Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out int v))
                        f.FaceIndices.Add(v);
            }
            else if (raw is int[] arr)
            {
                f.FaceIndices.AddRange(arr);
            }
            else if (raw is System.Collections.IEnumerable en && !(raw is string))
            {
                foreach (object? o in en)
                    if (o is int iv) f.FaceIndices.Add(iv);
            }
        }

        if (d.ContainsKey("ProfileCurve"))
        {
            object? geo = null;
            if (d.TryGetValue("ProfileCurve", out geo))
                f.ProfileCurve = geo as Curve;
        }

        if (d.ContainsKey("Parameters"))
        {
            var p = d.GetDictionary("Parameters");
            int n = p.ContainsKey("Count") ? p.GetInteger("Count") : 0;
            for (int i = 0; i < n; i++)
            {
                string k = p.GetString("K" + i);
                double v = p.GetDouble("V" + i);
                if (!string.IsNullOrEmpty(k)) f.Parameters[k] = v;
            }
            // 兼容旧格式：直接按 key 存 double
            if (n == 0)
                foreach (string k in p.Keys)
                    if (k != "Count") f.Parameters[k] = p.GetDouble(k);
        }
        return f;
    }
}

/// <summary>特征树存取。写进 Brep.UserDictionary，Rhino 9 实测 AddBrep / Replace 后均保留。</summary>
public static class FeatureTreeStorage
{
    public const string RootKey = "RhinoFeatureWorks_Tree_V1";

    public static void Save(Brep brep, List<RecognizedFeature> features)
    {
        if (brep == null) return;
        if (brep.UserDictionary.ContainsKey(RootKey))
            brep.UserDictionary.Remove(RootKey);   // 修复隐患5：清脏数据

        var root = new ArchivableDictionary();
        root.Set("Count", features.Count);
        root.Set("Schema", 1);
        for (int i = 0; i < features.Count; i++)
            root.Set("Feat_" + i, features[i].Serialize());
        brep.UserDictionary.Set(RootKey, root);
    }

    public static List<RecognizedFeature> Load(Brep? brep)
    {
        var list = new List<RecognizedFeature>();
        if (brep == null || !brep.UserDictionary.ContainsKey(RootKey)) return list;
        var root = brep.UserDictionary.GetDictionary(RootKey);
        int count = root.ContainsKey("Count") ? root.GetInteger("Count") : 0;
        for (int i = 0; i < count; i++)
        {
            string key = "Feat_" + i;
            if (root.ContainsKey(key))
            {
                try { list.Add(RecognizedFeature.Deserialize(root.GetDictionary(key))); }
                catch { /* 单个坏节点不拖垮整棵树 */ }
            }
        }
        return list;
    }

    public static bool HasTree(Brep? brep) =>
        brep != null && brep.UserDictionary.ContainsKey(RootKey);

    public static void Clear(Brep brep)
    {
        if (brep != null && brep.UserDictionary.ContainsKey(RootKey))
            brep.UserDictionary.Remove(RootKey);
    }
}
