using System.Reflection;
using System.Runtime.InteropServices;

// 独立插件：与已安装的「基准面工具」(8B7C4E52-...) 完全隔离，两个 Yak 包并存。
[assembly: Guid("6D1F8A3C-2E47-4B95-A0D6-9C3E7F1B2D48")]
[assembly: AssemblyTitle("特征识别工具 / RhinoFeatureWorks")]
[assembly: AssemblyDescription("Rhino 9 SolidWorks FeatureWorks 风格特征取消 v1.5：FWSelect 选实体→自动识别→自动弹面板；视口逐组编号标签与面板行双向选择（点行高亮/点边面反查选中）；显式『保留全部 / 取消选中 / 全部取消』语义；圆角通道(删过渡面+底层曲面重缝) 与 孔洞通道(UntrimFace) 分开取消；AFAG + 洋葱剥皮识别 + 两个 Eto 停靠面板")]
[assembly: AssemblyVersion("1.5.0.0")]
[assembly: AssemblyFileVersion("1.5.0.0")]
