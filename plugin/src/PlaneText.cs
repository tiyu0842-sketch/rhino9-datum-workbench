using System;
using System.Globalization;
namespace DatumPlanePlugin;

// Pure numeric validation, independently testable without Rhino's native runtime.
internal static class PlaneText
{
    internal static bool TryRead(string? text, out double[] values)
    {
        values = Array.Empty<double>();
        if (string.IsNullOrWhiteSpace(text)) return false;
        var parts = text.Split(';');
        if (parts.Length != 3) return false;
        var result = new double[9];
        for (int i = 0; i < 3; i++)
        {
            var xyz = parts[i].Split(',');
            if (xyz.Length != 3) return false;
            for (int j = 0; j < 3; j++)
                if (!double.TryParse(xyz[j], NumberStyles.Float, CultureInfo.InvariantCulture, out result[i * 3 + j]) ||
                    !double.IsFinite(result[i * 3 + j])) return false;
        }
        values = result;
        return true;
    }
}
