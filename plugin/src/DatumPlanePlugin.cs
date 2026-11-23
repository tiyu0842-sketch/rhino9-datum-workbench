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
        // v2.9：Alias 式全视图联动。Rhino 原生是"一个视口一个显示模式"，
        // 手动切换只影响当前视口；靠 DisplayPipeline.DisplayModeChanged 静态事件补齐。
        AliasStyleLink.Start();
        return LoadReturnCode.Success;
    }
    protected override void OnShutdown()
    {
        AliasStyleLink.Stop();
        DatumPlaneCore.StopWatching();
    }
}
