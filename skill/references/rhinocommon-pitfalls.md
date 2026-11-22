# RhinoCommon 9 实测坑位清单

全部经过本机 `C:\Program Files\Rhino 9\System\RhinoCommon.xml`、反射或真实文档验证。写新代码前先扫一遍，避免"看名字猜 API"。

## 编译与加载

- 本机 `C:\Program Files\dotnet\dotnet.exe` 只有运行时没有 SDK；网络装 SDK 超时。用 Rhino 进程内 Roslyn：`clr.AddReference` 加载 `Microsoft.CodeAnalysis.dll` 与 `.CSharp.dll`，用 `AppDomain.CurrentDomain.GetAssemblies()` 的 `Location` 做 `MetadataReference`（跳过本插件自身以消除 CS0436、跳过已不存在的 Location 否则 FileNotFoundException）。
- `LanguageVersion.Latest` + `NullableContextOptions.Enable` 是 v1.1 风格源码的必需编译选项。
- `CS1701 System.Drawing.Primitives 8.0→10.0` 是本机噪声警告，可忽略。
- `Assembly.LoadFrom(rhp)` 会锁文件导致重编译失败；改用 `Assembly.Load(File.ReadAllBytes(path))`。注意反射加载的插件 `Instance=null`，`OnLoad` 不会触发——面板注册等只能在真实插件加载下验证。
- `PlugIn.ProductName` 在 Rhino 9 不可 override。`RhinoView` 在 `Rhino.Display` 命名空间。

## 设置与状态

- `StringTable.GetValue(section, entry)` 是两参数；但用 `SetString(key, value)` 写入时，读取必须用**单参数** `GetValue(key)`。搞混会永远读不到。
- `DisplayModeDescription.UpdateDisplayMode(mode, true)` 返回 false 只表示"参数无变化"，不是失败。
- **已注册的显示模式无法原地更新参数**（返回 false 且不落盘）。要升级现有模式：先 `DeleteDisplayMode(oldId)` + `SaveDisplayModes()`，再 `CopyDisplayMode(basis.Id, name)` 重建。否则用户装了新版观感还是旧的。
- `ObjectColor` 与 `UseCustomObjectColor` 有**赋值顺序坑**：先写颜色、最后写 `UseCustomObjectColor=true`；顺序反了开关被静默重置回 false。同样地 `SetSurfaceIsoColorUsage()` 会把 `SurfaceIsoColorsUsed` 重置为 false，总开关必须最后赋值。
- `ModelAidSettings.UniversalConstructionPlaneMode` / `AutoAlignCPlane` 是**应用级全局设置**，插件只是在借用；退出时恢复基线快照，不要从旧文件回放偏好。

## 几何与对象

- `RhinoViewport.ConstructionPlane()` 是**方法**返回 `Plane`（有 `.Origin`）；`GetConstructionPlane()` 返回 `ConstructionPlane` 对象（要 `.Plane`）。
- `ObjectAttributes` 没有 `Color` 属性，用 `ObjectColor`；只设 `ColorSource=ColorFromObject` 而不设 `ObjectColor` 会得到黑色（线框/Ghosted 下更难认）。
- `GetDisplayModeOverride(Guid)` 返回 **Guid** 不是 DisplayModeDescription，要和 `Ghosted.Id` 比较。
- `Surface.GetBoundingBox(bool)` 有必填参数；曲面最近点是 `ClosestPoint(pt, out u, out v)`，不是 `GetClosestPoint`。
- `BrepFace.TryGetPlane(out Plane, double tol)` 可判平面；取面质心必须先 `DuplicateFace(false)` 再 `AreaMassProperties.Compute().Centroid`——trimmed 面的参数域中点可能落在面外。
- `LayerTable.FindName(string)` 在 9.0 返回 `Layer` 对象不是 int，用返回对象的 `.Index`。
- `Layer.GetChildren()` 与 `RhinoViewport.Id` 真实存在；不要凭印象否定。
- `NurbsSurface` 的阶数属性是 `OrderU/OrderV`（阶数 = Order - 1），**不是** `DegreeU/DegreeV`。
- `GetObject.LockedObjectSelect = true` 是 Rhino 9 原生能力，选中锁定物件不需要临时解锁图层。`EnablePreSelect(bool,bool)` 的第二参数是 `ignoreUnacceptablePreselectedObjects`，与锁定图层无关。
- 多重曲面上直接点选子面：`GeometryFilter = ObjectType.Surface`（**只给 Surface，不要 |Brep**，Brep 会让顶层对象抢先被选中）+ `SubObjectSelect = true` + `DisablePreSelect()`。这是 Rhino 原生 `ExtrudeBrepFace` / `ExtractSrf` 的交互配方，用户不需要 Ctrl+Shift。
- `GetObject.SetCustomGeometryFilter` 委托签名 `(RhinoObject, GeometryBase, ComponentIndex) -> bool`。
- `Command.IsValidCommandName("JZ")=True`；`AddOption` 名字只能字母数字（下划线合法），中文放第二参数；同一 `GetOption` 重复 AddOption 同名返回 0，必须校验 >0。加速键 = 选项名里第一个未被引用的字母，首字母唯一即可固定。
- `GetOption` 没有 `SetDefaultOption`；回车走 `GetResult.Nothing` 自己分派。

## 视口与布局

- `RhinoViewport.SetToPlanView(origin, XAxis, YAxis, false)` 后实测 `CameraDirection=-Normal`、`CameraUp=YAxis`、`CameraTarget=Origin`；配合 `ChangeToParallelProjection(true)` + `SetConstructionPlane(plane)` + `ZoomBoundingBox` 得到正对基准面的平面视图。
- `doc.Views.FourViewLayout(true)` 有必填参数；`SplitViewportVertical` 可脚本驱动，`_4View` 在无界面实例会挂 300 秒。
- `Rhino.RhinoApp.ToolbarFiles` 才是正确入口（不是 `Rhino.UI.ToolbarFiles`）。工具栏组可见性存在**用户配置的 `UI\default.rui`**，只对插件 RUI 调 `Save()` 不持久化；必须设 `Visible=True` → `Rhino.RhinoApp.RunScript('_Quit', False)` 正常退出 → 重开验证。
- 工具栏消失 ≠ 文件坏，先查 `ToolbarGroup.Visible`。

## 打包与安装

- `.rhi` 用 .NET Framework 的 `ReflectionOnly` 检查 .rhp，对 net8 插件抛 `FileLoadException: System.Private.CoreLib` → 报"package is not compatible"。**Rhino 9 / .NET 8 一律用 yak**。
- `Yak.exe install <本地.yak>` 成功标志：`Successfully installed <中文名> (<版本>)`，文件落到 `%APPDATA%\McNeel\Rhinoceros\packages\9.0\<中文名>\<版本>\`。末尾安全策略提示每次都出现但不影响结果，不要重试。
- 安装前若用户开了梯子/代理，Yak 联网校验会被杀掉（SIGTERM 假失败，目录建了但 rhp 没落盘）。先关代理再装。
- 多版本可并存，`manifest.txt` 指向最新即加载最新；后台 Rhino 实例占用会让 `yak uninstall` 报 Access denied。
- `Compress-Archive -LiteralPath 文件数组` 会扁平化目录；要保结构先建暂存区再 `-Path "$pack\*"`。

## Eto 面板

- Rhino 9 面板类 = `Eto.Forms.Panel` 子类 + `IPanel`；注册用 `Rhino.UI.Panels.RegisterPanel(plugin, type, title, icon, PanelType.System)`，打开用 `Panels.OpenPanel(guid)`。
- `Command` 在 `Rhino.Commands` 与 `Eto.Forms` 之间歧义，用全名。`TableLayout.Spacing` 是 `Eto.Drawing.Size`，`StackLayout.Spacing` 是 `int`。`GetObject` 用 `SetCommandPrompt()` 方法而非属性。
- 反射 Assembly.Load 不会触发插件 `OnLoad`，面板不会注册——这是测试条件限制，别误判为代码 bug。
