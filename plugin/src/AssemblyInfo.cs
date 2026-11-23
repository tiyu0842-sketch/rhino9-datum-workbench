using System.Reflection;
using System.Runtime.InteropServices;
// v1.2：插件 GUID 与程序集名保持不变，保证覆盖安装后工具栏按钮绑定不失效。
[assembly: Guid("8B7C4E52-6F3A-4C1D-9A2E-5D8F0B3C7E14")]
[assembly: AssemblyTitle("基准面工具")]
[assembly: AssemblyDescription("Rhino 9 基准面 v2.10：Alias 观测显示只作用于当前活动视口（其他视口不动，各视口独立；全视图联动改为可选、默认关）、两套主题用结构线密度区分（浅色 0=仅边界、深色 1=一条内部等参线）、还原只还原因本工具改过的视口、B 选平面直接点击无需 Ctrl+Shift、方向光三度灰阶、逐视口还原工作平面、自愈残留 CPlane、第5法向视图、中英双语")]
[assembly: AssemblyVersion("2.10.0.0")]
[assembly: AssemblyFileVersion("2.10.0.0")]
