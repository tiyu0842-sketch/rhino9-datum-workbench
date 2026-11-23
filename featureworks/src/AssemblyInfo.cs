using System.Reflection;
using System.Runtime.InteropServices;

// 独立插件：与已安装的「基准面工具」(8B7C4E52-...) 完全隔离，两个 Yak 包并存。
[assembly: Guid("6D1F8A3C-2E47-4B95-A0D6-9C3E7F1B2D48")]
[assembly: AssemblyTitle("特征识别工具 / RhinoFeatureWorks")]
[assembly: AssemblyDescription("Rhino 9 SolidWorks FeatureWorks 风格特征取消 v1.3：选实体 → 曲面修剪证据识别 → 特征面亮橙/其余半透明锁定 → 圆角通道(删过渡面+底层曲面重缝) 与 孔洞通道(UntrimFace) 分开取消 → 恢复毛坯可再编辑；AFAG + 洋葱剥皮识别 + 特征树持久化 + 抑制与参数重建 + 两个 Eto 停靠面板")]
[assembly: AssemblyVersion("1.3.2.0")]
[assembly: AssemblyFileVersion("1.3.2.0")]
