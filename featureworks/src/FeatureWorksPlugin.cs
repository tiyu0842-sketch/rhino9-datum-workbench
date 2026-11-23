using System.Runtime.InteropServices;
using Rhino.PlugIns;

namespace RhinoFeatureWorks;

[Guid("6D1F8A3C-2E47-4B95-A0D6-9C3E7F1B2D48")]
public class FeatureWorksPlugin : PlugIn
{
    public static FeatureWorksPlugin? Instance { get; private set; }
    public FeatureWorksPlugin() { Instance = this; }
    protected override LoadReturnCode OnLoad(ref string errorMessage)
    {
        // 注册两个停靠面板；各自内部已 try/catch，单个失败不影响插件其余命令。
        //   FWPanel       —— 特征树 / 抑制 / 重建（原有）
        //   FWCancelPanel —— 圆角通道 / 孔洞通道，勾选后取消特征（新增）
        FwPanel.Register();
        FwCancelPanel.Register();
        return LoadReturnCode.Success;
    }
}
