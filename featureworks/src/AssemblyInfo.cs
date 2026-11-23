using System.Reflection;
using System.Runtime.InteropServices;

// 独立插件：与已安装的「基准面工具」(8B7C4E52-...) 完全隔离，两个 Yak 包并存。
[assembly: Guid("6D1F8A3C-2E47-4B95-A0D6-9C3E7F1B2D48")]
[assembly: AssemblyTitle("特征识别工具 / RhinoFeatureWorks")]
[assembly: AssemblyDescription("Rhino 9 FeatureWorks 风格特征取消 v1.6：常驻双向联动（视口左键点选/拖框/Shift-Ctrl 加减选，面板与模型共享一份选中集）；严格两独立模块 —— A 去除圆角（删整圈过渡面+重缝，连带影响孔时明确报出、不偷偷改）、B 去除布尔切割（Brep.RemoveHoles 指定 inner loop，与圆角无关、任意顺序）；FWSelect 两段式自动弹面板；F1/H1 编号标签；AFAG + 洋葱剥皮识别 + 两个 Eto 停靠面板")]
[assembly: AssemblyVersion("1.6.0.0")]
[assembly: AssemblyFileVersion("1.6.0.0")]
