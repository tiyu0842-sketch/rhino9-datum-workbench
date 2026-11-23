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
- `Rhino.PersistentSettings.GetBool/SetBool/GetString/SetString` 全是**实例方法**，静态调用报 CS0120；没有全局静态入口。正确用法：`PlugIn.Settings`（本身就是 PersistentSettings 实例）→ `DatumPlanePlugin.Instance?.Settings?.GetBool(key, true)`。落到 `%AppData%\McNeel\Rhinoceros\9.0\Plug-ins\<guid>\`，跨文档跨会话。
- **要改默认值，必须换键名**：旧版本已把 `true` 落盘，`GetBool(key, false)` 读到的是已存的 `true`，新默认值不会生效。加版本后缀（`...LinkAllViews.v2`）让旧键失效。
- 装了 WeaverBird 后，它把 `Action` 类型塞进全局/`System` 命名空间：任何 `Action` 引用都 **CS0433**（WeaverBird.Core vs System.Private.CoreLib），**写 `System.Action` 也救不了**。解法：不用委托，`try { ... } catch { }` 内联。

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
- **显示模式是「一个视口一份」**：`viewport.DisplayMode` 只管自己；标题栏下拉 / 视图菜单 / `_SetDisplayMode` 都只作用当前视口 —— **这是默认正确行为，也是多数用户要的**。`foreach (RhinoView v in doc.Views) v.ActiveViewport.DisplayMode = m` 才是全视口（顺手改一个视口的正确写法：`doc.Views.ActiveView.ActiveViewport.DisplayMode = m`）。
- 只改部分视口后做"还原"时，**不要按全量回放**：用 `doc.Strings` 存一份改过的视口 Id 名单，只还原名单内的，否则会抹掉用户自己切过的视口。
- `Rhino.Display.DisplayPipeline.DisplayModeChanged` 是**静态事件**（`GetAddMethod().IsStatic = True`，since 6.18），参数 `DisplayModeChangedEventArgs{ Viewport, RhinoDoc, OldDisplayModeId, ChangedDisplayModeId }`。API 写 `DisplayMode` 会**同步**触发；Python 可直接 `+=` / `-=`。
- 事件里再改其他视口会**递归触发**同一事件 → 必须闸门（`Interlocked.Exchange`）+ 先比 `DisplayMode.Id` 再设；程序化批量改模式（尤其还原各不相同的原模式）时必须整体静音，否则被自己同步覆盖。
- `doc.Views` 只列**顶级视口**（实测 4 个）；布局页（Layout）里的 detail 视窗不在其中，需另走 page view API。

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
- **`Panels.RegisterPanel(plugin, type, caption, icon, panelType)` 要求面板类有类级 `[Guid("...")]` 特性**（`System.Runtime.InteropServices.GuidAttribute`），否则报 `type must have a GuidAttribute (Parameter 'type')`。只有 `public static readonly Guid PanelId` **字段不算**——Rhino 读的是特性不是字段。修法：给类加 `[Guid(与 PanelId 同值)]`。`Panels.OpenPanel(guid)` 用的就是这个 Guid。
- 想让命令触发后自动弹面板（XNurbs 风格两段式）：在命令拿到对象、算完结果后直接调 `面板类.Open()`（内部 `Register()` + `Panels.OpenPanel(PanelId)`）；面板实现 `PanelShown(uint docSerialNumber, ShowPanelReason reason)` 回调并在其中 `Refresh()`，弹出时即可显示刚算好的数据。外层 try/catch 包住，面板失败不能连累命令主流程。
- 遇到"面板注册失败"先分清两层原因：①类缺 `[Guid]`（真 bug，截图会报 GuidAttribute）；②插件没 `OnLoad`（没重启或反射加载）。报错文本能直接区分。
- **多选：`ListBox` 没有多选**。勾选多个用 `CheckBoxList`，读 `SelectedKeys`（`IEnumerable<string>`）；`Items[i]` 返回 `IListItem`，按 `.Key` 匹配组号，别拿索引当身份。
- `RhinoGet.GetInteger(prompt, bool acceptNothing, ...)` 有 bool 参数；`GetNumber(prompt, bool, ref v, lo, hi)` 同理。漏传编译不过。

## 文档事件与对象枚举

- `RhinoDoc.ReplaceRhinoObject` / `DeleteRhinoObject` / `AddRhinoObject` / `CloseDocument` / `OpenDocument` **全是静态事件**，用类名订阅；挂 `doc.` 实例会 CS0176。
- `Rhino.DocObjects` 命名空间含 `Environment` 类型，与 `System.Environment` 撞名（CS0104）；`using Rhino.DocObjects` 的文件里写 `System.Environment.NewLine` 全名。
- `ObjectTable` 迭代与 `doc.Objects.GetObjectList(...)` **默认不含隐藏对象**。要统计/清理隐藏对象必须传 `new ObjectEnumeratorSettings { HiddenObjects = true }`。排查「对象是不是被删了」前先加这个，否则会误判。
- `ObjRef.Brep()` / `ObjRef.Geometry()` 返回**副本**，不能用 `ReferenceEquals` 判断几何是否被替换。改用面数、`GetBoundingBox(true)` 中心漂移等粗粒度指纹（>2%）。
- 反射调用带可选参数的方法（如 `End(RhinoDoc doc, bool redraw = true)`）必须传齐全部实参，反射不会补默认值。
- 多次 `Assembly.Load(File.ReadAllBytes(...))` 同一程序集名会**复用 AppDomain 里最早那份代码**；验证迭代时改 `ASSEMBLY_NAME`（`…C3/C4/C5/C6`）隔离。副作用是每个实例各自持有静态 conduit，清理要全部扫描 `End()`。

## DisplayConduit 聚焦显示

- 回调顺序：`CalculateBoundingBox` → `ObjectCulling` → `PreDrawObjects` → `PostDrawObjects` → `DrawForeground`（后者不参与深度剔除）。
- 想让源对象「变半透明」，不能叠透明层（底色不变）。正确做法：`ObjectCulling(CullObjectEventArgs e)` 里对目标对象 `e.CullObject = true`，然后在 `PostDrawObjects` 画自己的 `DisplayMaterial{ Transparency=0.72 }` 子 Brep。
- 需要「浮在实体前面」的高亮面必须画在 `DrawForeground`；放 `PostDrawObjects` 会被深度剔成线框。
- 自己画的 Brep 要在 `CalculateBoundingBox` 里 `e.IncludeBoundingBox(brep.GetBoundingBox(true))`，否则视口裁剪/缩放会算错。
- `DrawBrepShaded(Brep, DisplayMaterial)` 的 `Transparency` 取值 0..1。
- 长时间存活的 conduit 必须做过期自愈：缓存的子面按面索引抽取，源对象一换就失效，会留下挪不走的蒙皮。见 `error-catalog.md`「鬼影」条。

## B-rep 特征取消（Untrim）

- `Brep.UntrimFace(int faceIndex, double tolerance)` 抹掉该面的**外环 + 全部内环**（官方 since 9.0：
  「outer boundary is untrimmed and all inner loops are removed」），孔/槽壁随之自动清理。
  实测 盒+2孔 8 面 → 6 面 240000：**两个孔一起没了**。
- ★ **loop 级精度官方就有（E-024 修正 E-018 的旧结论）**：
  `Brep.RemoveHoles(IEnumerable<ComponentIndex>, double)`（since 6.8）只删**指定的** inner loop，
  参数须为 `BrepLoop.LoopType == Inner` 的 loop 的 `ComponentIndex`。实测 盒+2孔 8 面 → 7 面
  vol 232365.93，只删 1 个孔，另一孔与外环全留；圆角盒+1孔 11 面 → 10 面 239315.06，**圆角完好**。
  `Brep.RemoveHoles(double)`（since 6.0）删全部内环。**别再用 UntrimFace 做「取消单个孔」**，
  也别再「在 Core 层按 inner loop 搭桥」或 `RunScript` 调命令。
- `Brep.UntrimOuterLoop(int faceIndex)` 官方 since 9.0：「only untrimmed when **all of its edges are naked**;
  otherwise the operation fails to avoid corrupting adjacent faces」「Inner loops are left in place」。
  对**实体圆角/倒角一律返回 null**（外环边被邻面共享）。圆角不能用 untrim。
- `Brep.UntrimOuterLoop(int faceIndex)` 对**实体圆角/倒角一律返回 null**（外环边被邻面共享）。圆角不能用 untrim。
- 圆角/倒角唯一可行路径：删掉整圈过渡面 → 剩余面 `UnderlyingSurface().ToBrep()` → `Brep.CreateSolid(IEnumerable<Brep>, tolerance)` 重缝。**必须整圈删**：10 面盒只删 1 个 → 9 面 74715.5 变形；删 4 个 → 6 面 75000。
- 带 trim 的面直接 `CreateSolid` 会因孔口/槽口留洞失败，必须先还原成完整解析面。
- 证据信号：`face.UnderlyingSurface()`、`face.Loops.Count`、`face.Trims`、`TrimIndices()`、domain 跨度 vs trim 边界差（overhangZ）、面朝向反转（reversed）。倒角面是 `NurbsSurface`，别按曲面类型猜。
- 曲面参数域是**弧长不是弧度**；柱面 U=轴向、V=周向。覆盖角 = 跨度/半径，取 `min(degU, degV)`。

## 只读探活 / 插件状态判断（Rhino 9，E-016 实测）

- `Rhino.UI.Panels.GetRegisteredPanelIds()` **不存在**（Python 反射报 `type object 'Panels' has no attribute ...`）。
  查面板用 `Panels.DockBarIdInUse(Guid)`；别自己猜 `GetRegisteredPanelIds` / `IsPanelVisible` 之类名字。
- `Rhino.Commands.Command.GetCommandNames()` **无 0 参数重载**（报 `No overload for method ... takes 0 arguments()`）。
  别用 `Command.GetCommandNames()` 直接列命令。
- **插件按需加载**：`AppDomain.CurrentDomain.GetAssemblies()` 里没有某插件程序集，
  **不等于**没安装或没重启。判安装查磁盘 `…\packages\9.0\<名>\<版本>\`；
  判面板注册查 `DockBarIdInUse`；这条修正了 E-014 的判断方法。
- 显示模式枚举可用：`Rhino.Display.DisplayModeDescription.GetDisplayModes()` → `m.EnglishName`。
- 官方 Untrim 命令族（命令层）：`Untrim` / `UntrimAll` / `UntrimBorder`（**留内部孔**）/
  `UntrimHoles`（逐孔选边、**window selection 框选**、`All` / `MaximumEdgeLength` / `KeepTrimObjects`）。
  **API 层对应表（E-024 修正）**：整面级 `UntrimFace` / 只删外环 `UntrimOuterLoop`（有 naked 限制）/
  删指定内环 `RemoveHoles(IEnumerable<ComponentIndex>)` / 删全部内环 `RemoveHoles(double)`。
  ~~API 层只有整面级~~ 是错的，别再沿用。
- `DuplicateSubBrep(剩余面)` 与 `UntrimOuterLoop` 在同一进程内连调会**导致 Rhino 进程崩溃**
  （E-024，slot armadillo pid 4396）。崩溃后按纪律不盲目重试，拆成独立脚本、单步验证。
- `DisplayConduit.ObjectCulling` 剔除源对象后，conduit 自绘的面是**显示影子，不是文档对象**，
  Rhino 原生点选/框选拾取不到。想让用户在原视口直接框选，必须保留源对象可拾取
  （改用 `RhinoObject.SelectSubObject` + `RhinoDoc.SelectObjects` 静态事件），或挂 `MouseCallback` 自做命中。

## 打包补充

- Yak `manifest.yml` 的 `description` 是 YAML 值，出现 `v1.3: pick` 这种「冒号+空格」会解析失败；改写成不含 `: ` 的句子。

## 相机、截图与 Box 创建（2026-11-23 实测）

- `doc.Objects.AddBox(Box)` 创建的是 **`Extrusion`**，不是 `Brep`。按 `isinstance(geom, Brep)` 筛会得到 0 个；用 `type(geom).__name__` 或包围盒条件筛。
- `RhinoView.CaptureToBitmap` **只有 `CaptureToBitmap(System.Drawing.Size)` 一个重载**，传 `bool` 会报 "bool cannot be converted to Size"。
- `ChangeToPerspectiveProjection` 重载是 `(bool updateView, double lensLength)` 和 `(double lens, bool, double)`；**没有单 bool 版本**。
- 视口没有 `SetCameraUp(...)` 方法；`CameraUp` 是**可写属性**：`vp.CameraUp = rg.Vector3d(0,0,1)`。`SetCameraLocation/Target/Direction` 都是 `(…, bool)` 两参（第二参数 updateView）。
- 最稳的「摆好视角 + 截图」配方：
  ```python
  vp.ChangeToPerspectiveProjection(True, 50.0)
  vp.CameraUp = rg.Vector3d(0,0,1)
  vp.SetCameraDirection(rg.Vector3d(0,1,-0.35), False)   # 定朝向
  vp.ZoomBoundingBox(bb)                                 # 按朝向自动退到合适距离
  vv.Redraw(); Rhino.RhinoApp.Wait()
  vv.CaptureToBitmap(sd.Size(1600,900)).Save(path, sd.Imaging.ImageFormat.Png)
  ```
  只调 `SetCameraLocation + SetCameraTarget` 再截图曾得到**空白帧**；加 `ZoomBoundingBox` 后才稳定。
- **透视会掩盖尺寸关系**：沿物体排列方向（+X）看，近处小物体被放大，出现"实际递增、视觉递减"的假象。要展示尺寸梯度就把相机放在**垂直于排列方向**的一侧（如沿 +Y 看）。
- 正视图/俯视图用 `vp.SetToPlanView(origin, xAxis, yAxis, false)` + `ChangeToParallelProjection(True)`，平行投影下尺寸关系才是真的；注意沿 Y 投影时不同 y 的物体会在 x-z 上重叠，选投影方向要避开干扰物。
- `ObjectColor` + `ColorSource=ColorFromObject` 在默认 Shaded 下**未生效**（对象仍是统一蓝色），疑似 display mode 用 material color 覆盖；要稳定上色需同时设材质或改显示模式的着色来源（待验证）。
- `doc.BeginUndoRecord("...")` / `EndUndoRecord(undo)` 包住整批创建，用户可一次 `Ctrl+Z` 撤销。

## v1.6 新增：B-rep loop 级取消 / 常驻鼠标 / 命名歧义（E-025，2026-11-23）

- ★ **`Brep.RemoveHoles(IEnumerable<ComponentIndex>, double)` 返回 `Brep`，不是 `bool`**：
  XML `<returns>` 原文「The Brep without holes if successful, **null** otherwise」，since 6.8。
  参数须为 `BrepLoop.LoopType == BrepLoopType.Inner` 的 loop 的
  `new ComponentIndex(ComponentIndexType.BrepLoop, loop.LoopIndex)`。
  实测 盒+2孔 8 面 → 只删 H1 的 2 个环 → 7 面 / inner 2 / vol 236607.08。
- `BrepLoop.LoopIndex` 是**全局编号**，不要直接当 `brep.Loops[i]` 的索引用；
  稳妥做法是线性查找 `brep.Loops[k].LoopIndex == li`。
  `BrepLoop.Face` / `BrepLoop.Trims` / `BrepTrim.Edge`（→ `BrepEdge.AdjacentFaces()`）都可用，
  用来把孔洞组映射到它对应的 inner loop。
- **`FeatureType` 枚举默认值是 `Fillet`**（`Fillet, Chamfer, SimpleHole, …`）。
  用 `g.Type == FeatureType.Fillet` 判断「是不是圆角模块」会把未显式赋值的孔洞组误判成圆角。
  模块归属一律用显式字符串标记（`FwFocusGroup.Channel`）。E-025 实测踩过，导致 `RemoveHoles` 静默收不到内环。
- `Rhino.UI.MouseCallback`：`Enabled` 是**基类属性**（可读写）；事件签名统一为
  `OnMouseDown/OnEndMouseDown/OnMouseMove/OnEndMouseMove/OnMouseUp/OnEndMouseUp/OnMouseDoubleClick/
   OnMouseEnter/OnMouseLeave/OnMouseHover(MouseCallbackEventArgs e)`。
  `MouseCallbackEventArgs` 实测成员：`View : RhinoView`、`MouseButton : Rhino.UI.MouseButton`
  （`None/Left/Right/Middle`）、`Button : System.Windows.Forms.MouseButtons`、`ShiftKeyDown`、
  `CtrlKeyDown`、`ViewportPoint : System.Drawing.Point`、`Cancel : Boolean`、`IsOverGumball()`。
  左键接管设 `e.Cancel = true`，避免 Rhino 同时画自己的框选矩形。
- `RhinoViewport.WorldToClient(Point3d) -> Point2d`（屏幕像素，X/Y 为 double）；
  `DisplayPipeline.Draw2dRectangle(System.Drawing.Rectangle, Color, Int32, Color)`、
  `Draw2dLine(Point, Point, Color, Single)`、`Draw2dText(...)`。
  `Draw2d*` 与 `MouseCallbackEventArgs.ViewportPoint` 同一坐标系，可直接画拖框。
- **CS0104 命名歧义（本机高频）**：同时 `using System.Drawing` + `Rhino.Geometry` 时
  `Point` 双定义；同时 `using System` + `Rhino.DocObjects` 时 `Environment` 双定义。
  解法：文件顶部加 `using Point = System.Drawing.Point;`，或写全 `System.Environment.NewLine`。
  v1.6 首轮编译 16 个 error 全是这两类，加别名后 0 error。
- `Brep.CreateFilletEdges(Brep, IEnumerable<int>, IEnumerable<double>, IEnumerable<double>,
   BlendType, RailType, Double)` 可造圆角盒：实测 100×80×30 顶面 4 边 R3 →
  10 面 / solid / vol 239315.06（FwSelfTest 的用法，`BlendType.Fillet` + `RailType.RollingBall`）。
  比 `UntrimOuterLoop` 连调安全，做几何验证优先用它。
