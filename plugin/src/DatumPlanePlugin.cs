using System.Runtime.InteropServices;
using Rhino.PlugIns;
namespace DatumPlanePlugin;

[Guid("8B7C4E52-6F3A-4C1D-9A2E-5D8F0B3C7E14")]
public class DatumPlanePlugin : PlugIn
{
    public static DatumPlanePlugin? Instance { get; private set; }
    public DatumPlanePlugin() { Instance = this; }
    protected override LoadReturnCode OnLoad(ref string errorMessage)
    {
        DatumPlaneCore.StartWatching();
        return LoadReturnCode.Success;
    }
    protected override void OnShutdown() { DatumPlaneCore.StopWatching(); }
}
