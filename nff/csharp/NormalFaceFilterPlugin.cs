using System.Runtime.InteropServices;
using Rhino.PlugIns;

namespace NormalFaceFilter.Rhino
{
    /// <summary>插件入口；Rhino 加载 .rhp 时通过此类注册命令。</summary>
    [Guid("E7BB0DD0-4DD5-4FC3-B2FB-F95AA29D3CF4")]
    public class NormalFaceFilterPlugin : PlugIn
    {
        public static NormalFaceFilterPlugin Instance { get; private set; }

        public NormalFaceFilterPlugin()
        {
            Instance = this;
        }

        // 真机修正（2026-11-22）：RhinoCommon 9 的 PlugIn 没有可 override 的 EnglishName
        // （只有只读 Name 属性，与 ProductName 同类坑）。插件名由程序集标题/构造函数决定。
    }
}
