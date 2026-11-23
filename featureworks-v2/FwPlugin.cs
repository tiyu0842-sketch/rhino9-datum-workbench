// FeatureWorks v2 插件入口
using System.Runtime.InteropServices;
using Rhino.PlugIns;

namespace FeatureWorks
{
    [Guid("3C9E7A15-8B42-4D6F-A0E3-7F15B2C9D840")]
    public class FwPlugin : PlugIn
    {
        public static FwPlugin Instance { get; private set; }
        public FwPlugin() { Instance = this; }

        // RhinoCommon 9 实测：PlugIn.OnLoad 签名是
        // LoadReturnCode OnLoad(ref string errorText)，返回 LoadReturnCode.Success。
        protected override Rhino.PlugIns.LoadReturnCode OnLoad(ref string errorText)
        {
            var rc = base.OnLoad(ref errorText);
            FwPanel.Register();   // 注册 Eto 停靠面板
            return rc;
        }
        // RhinoCommon 9 实测：PlugIn.EnglishName 不可 override（只有只读 Name）。
        // 插件名由程序集标题决定，见 AssemblyInfo.cs。
    }
}
