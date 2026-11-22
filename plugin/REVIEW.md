# DatumPlanePlugin v1.2 审查与验证记录

交付版本 **1.2.0.0**，目标 Rhino 9 / .NET 8。插件 GUID 与程序集名保持 `8B7C4E52-6F3A-4C1D-9A2E-5D8F0B3C7E14`（已由反射核对：程序集 `GuidAttribute` 与插件类 `GuidAttribute` 均为该值）。

基线：用户上传的 `DatumPlane_Rhino9_v1_1_preview.zip`（v1.1，另一个 AI 在 Linux 工作区用 .NET SDK 8.0.428 编译，其 README/REVIEW 明确声明「Rhino 内交互和运行尚未验证」，开关验证表三行全为「未执行」）。本版以该包 `src/` 为基线做增量升级。

## 一、四项需求的落点

| 需求 | v1.1 现状 | v1.2 做法 |
|---|---|---|
| 独立编号 + 锁定子图层 | 无；所有基准面放单个顶层「基准面」图层 | 新增 `DatumPlaneLayers.cs`：`DP_01/02…`，几何成功后锁定 |
| 点击锁定的旧基准面调用 | 无；只能按编号输入调用 | 新增 `DatumPlanePickCommand` 与主命令 `Pick` 选项 |
| 切换不重复创建 | **已实现**（`Recall` 只切 CPlane） | 点选后复用 `Recall`，未改其状态机 |
| 退出恢复最初 CPlane 与操作轴 | **已实现**（`GlobalSettings` 6 项快照 + `ActivePlane` + `ViewportId`） | 原样保留，本版首次实机验证 |

判断依据：v1.1 的 `Deactivate` 用 `GlobalSettings.Restore()` 恢复 Gumball 开关/对齐、自动复位、自动 CPlane、通用构造平面；`Recall` 注释明确「Switching planes must preserve the ORIGINAL baseline」。推倒重写只会引入回归，因此只加增量。

## 二、API 核对（权威：本机 `C:\Program Files\Rhino 9\System\RhinoCommon.xml`）

| API | 结论 |
|---|---|
| `GetObject.LockedObjectSelect` | **存在，since 9.0**。官方原文「By default, locked objects cannot be selected… call LockedObjectSelect=true」。这是不临时解锁图层的关键 |
| `GetObject.EnablePreSelect(bool, bool)` | 第二参数是 `ignoreUnacceptablePreselectedObjects`（预选），**与锁定图层无关**。参考方案的注释与用法写反 |
| `GetObject.SetCustomGeometryFilter(GetObjectGeometryFilter)` | 存在；委托签名 `(RhinoObject, GeometryBase, ComponentIndex) -> bool` |
| `GetObject.AcceptNothing(bool)` | 存在 |
| `Layer.GetChildren()` / `GetChildren(bool)` | 存在；返回直接子层数组，无子层时返回 `null`（已按可空处理） |
| `Layer.SetUserString/GetUserString` | 存在，since 5.0；用于给子层打识别标记 |
| `Layer.ParentLayerId` / `IsLocked` | 存在 |
| `LayerTable.FindByFullPath(string, int)` | 存在（第二参数是 notFoundReturnValue） |
| `LayerTable.Modify(Layer, int, bool)` | 存在 |
| `LayerTable.Delete(int, bool)` | 存在；回滚清理空子层用 |
| `RhinoViewport.Id` | 存在（v1.1 已用） |
| `NamedConstructionPlaneTable.Add/Find/Delete` | 存在 |
| `ObjectAttributes.SetUserString/GetUserString` | 存在 |

**纠正自身的两个误判**：本轮初查时我一度怀疑 `Layer.GetChildren()` 与 `RhinoViewport.Id` 不存在，查 XML 后确认两者都存在。所有结论以本机 XML + 真实编译为准，不凭记忆。

## 三、关键设计决策

1. **不用临时解锁**：`LockedObjectSelect = true` 是 Rhino 9 原生能力，零副作用。临时解锁需要遍历/改用户图层状态，`try/finally` 之外若进程崩溃会残留解锁层。
2. **构造顺序**：`CreateNumberedSubLayer` 返回的是**未锁定**子层；`AddBrep`、命名平面保存、`Activate` 全部成功后才调用 `LockSubLayer`。失败路径用 `CleanupEmptySubLayer` 删空层（只删带本插件标记、且确实无对象的层）。避免锁死一个空图层。
3. **单一数据源**：平面坐标只由 `NamedConstructionPlanes` 管理，几何 `UserString` 只存 `Kind/Name/Layer`。点选 → 读 `Name` → `Recall(name)`。参考方案在 `UserDictionary` 再存 9 个 double 属于双数据源，且 `ArchivableDictionary.Set(key, double[])` 支持性未确认，不采用。
4. **识别靠标记不靠名字**：`Layer.GetUserString("DatumPlane.Kind") == "DatumSubLayer"`，避免误认用户自建的同名 `DP_01`；编号扫描也按 `InvariantCulture` + `NumberStyles.None` 解析。
5. **不硬恢复 World**：参考方案 `RunScript("_GumballAlignment _World")` 会覆盖用户进入前的对齐偏好。v1.1 的 6 项快照能精确恢复非默认状态，实测已覆盖 `ObjectPlane` + Gumball 关闭的组合。
6. **保留全部既有命令**：7 个命令类（含新增 `DatumPlanePickCommand`），主命令只多一个 `Pick` 选项，`IsActive → Deactivate` 的开关语义不变。

## 四、真实编译

在 Rhino 9 进程内加载自带 Roslyn（`Microsoft.CodeAnalysis.dll` / `.CSharp.dll`），收集 `AppDomain` 已加载程序集作 `MetadataReference`（跳过 `Location` 已不存在的失效路径）。

- v1.1 用了 file-scoped namespace、nullable 注解、`using var`、switch 表达式 → 必须 `CSharpParseOptions(LanguageVersion.Latest)` + `CSharpCompilationOptions(nullableContextOptions=Enable)`，否则语法/注解报错。这是与 v1.0 编译脚本最大的差别。
- 源码 6 个：`AssemblyInfo.cs`、`DatumPlanePlugin.cs`、`PlaneText.cs`、`DatumPlaneLayers.cs`、`DatumPlaneCore.cs`、`DatumPlaneCommand.cs`。
- 输出：`COMPILE SUCCESS 24064 bytes`，**0 错误 0 警告**，233 个引用，0 个跳过路径。
- `Emit` 传 `MemoryStream`（非路径），再 `WriteAllBytes` 落盘，避免文件锁。

## 五、真实文档端到端验证（35 项 PASS）

以字节加载新程序集（不占文件锁），反射调用 `Create / Recall / Deactivate / SerializePlane` 等，在**同一个脚本内连续执行**，避免切换视口等外部干扰。初始状态特意设成**非默认**（自定义 CPlane `3,4,5` + `ObjectPlane` + Gumball 关闭），才能验证"精确恢复"而非碰巧回到 World。

| 阶段 | Active | 存的初始平面 | CPlane | 操作轴 | 对象 | 命名平面 | 图层 |
|---|---|---|---|---|---|---|---|
| 起始 | 空 | 空 | `3,4,5;1,0,0;0,.707,-.707` | ObjectPlane/关 | 20 | 0 | 13 |
| 创建 A | `1` | `3,4,5…` | `10,20,30…` | ConstructionPlane/开 | 21 | 1 | 14 |
| 切换到 B | `1` | **仍 `3,4,5…`** | `-7,2,9…` | ConstructionPlane | **21** | **2** | **14** |
| 还原 | 空 | 空 | **`3,4,5…`** | **ObjectPlane/关** | **21** | 2 | 14 |
| 创建 B | `1` | `3,4,5…` | `-7,2,9…` | ConstructionPlane | 22 | 3 | 15 |

PASS 明细：

- 创建：`DP_01` 编号、子层锁定、`Kind` 标记、父层嵌套、对象三处元数据、材质 0.55、CPlane 对齐、命名平面保存、`ActivePlane` 记录激活前平面、`ViewportId` 记录视口。
- 切换：对象数 / 图层数 / 命名平面数**均不增**；CPlane 切到 B；`ActivePlane` 保留最初基线未覆盖。
- 点选数据链：`GetObject.LockedObjectSelect = True` 可设置；锁定对象能解析回 `基准面_001`。
- 还原：初始 CPlane、`ObjectPlane`、Gumball 关闭、`AutoReset`、`AutoAlignCPlane`、`UniversalConstructionPlaneMode` 全部精确恢复；Active 清空；基准面几何保留。
- 编号递增：第二次创建得到 `DP_02` 且锁定，`DP_01` 仍锁定。

**防误删实证**：对锁定子层上的对象直接 `doc.Objects.Delete(id, True)` 返回 `False`，对象仍存在；解锁后删除成功。说明锁定确实拦住了常规删除。

RUI：脚本原子插入第 6 个按钮（避开被截断的超长 icons 单行）后，`System.Xml.XmlDocument.Load` 通过，`ToolbarFiles.Open` 成功，工具栏名读到「基准面工具」、group `Visible=True`；6 个 tool_bar_item / 6 个 macro_item / 6 个 icon，引用链闭合，命令为 `! _DatumPlane` / `Save` / `Recall` / `Lock` / `Restore` / **`Pick`**。

清理：测试对象与两个子层已删除，文档字符串清空，CPlane 与全局设置复位。残留的 `IsDeleted=True` 图层槽位属于 Rhino 表内已删除记录；当前文档为未命名临时文档，关闭不保存即消失。

## 六、已知限制（未实机跑到）

1. 鼠标三点 / 选面、点选命令的 `GetObject.Get()` 交互本身——交互式拾取无法用脚本宏同步驱动（会停在等待输入）。本版验证的是其数据链与该 API 可设置性。
2. 安装加载、不同显示模式下的透明度观感、保存重开、撤销重做、空闲事件持续锁定、跨视口/跨文档切换。
3. 手工重定位过操作轴的对象可能保留自定义方向（Rhino 官方说明）；需先在 Gumball 菜单重置。
4. 命名平面是坐标快照，移动蓝色矩形不会自动更新保存项。
5. 创建中途若失败，按设计只留一个**未锁定**的空子层；正常路径不会触发。

## 七、参考

- 本机 `C:\Program Files\Rhino 9\System\RhinoCommon.xml`（9.x SDK 文档，签名以此为准）
- https://developer.rhino3d.com/api/rhinocommon/type/rhino.applicationsettings.gumballsettings/
- https://developer.rhino3d.com/api/rhinocommon/type/rhino.input.custom.getobject/
- https://developer.rhino3d.com/api/rhinocommon/type/rhino.docobjects.tables.namedconstructionplanetable/

---

# 八、v1.6 增量审查（2026-11-21）

交付版本 **1.6.0.0**。修复用户实机反馈的「已有基准面」卡死，并新增第 5 个法向视图。

## 8.1 卡死根因（两条，都在 v1.5 的状态机里）

1. `DatumPlaneCore.Create` 中的 `if (IsActive(doc)) return Fail("已有基准面模式，请先还原")`。
   v1.4 起主菜单在激活态仍列出 `3Point/Plane/Pick`，用户一选就撞上这堵墙 —— 屏幕上那句「已有基准面」正是这里打印的。
2. `Recall/Lock/Deactivate` 里的 `IsOwnerViewport` 要求「切回启用时的视口」。用户切到别的视口（或新增第 5 视图）后，切换/点选全部被 `WrongViewport()` 拒绝；`OnIdle` 还会在换视口时静默 `ReleaseGlobalSettings()`，却把文档里的 `Active=1` 留着，形成「显示已启用、但坐标锁定其实已松开」的半退出态。

## 8.2 修复

| 改动 | 做法 |
|---|---|
| 激活态可再定义/切换 | 新增 `SwitchTo(doc, vp, plane, name)`：保留 `ActivePlane` 基线，只更新 `LockedPlane/SavedName/ViewportId/Tracked`；`Create` 在 `IsActive` 时走 `SwitchTo` 而非 `Fail`；`Recall/Lock` 统一复用 |
| 移除视口硬限制 | 删掉 `IsOwnerViewport` / `WrongViewport`；`Deactivate` 按 `ViewportId` 找到原视口一并还原，不再要求用户切回 |
| Idle 跟随活动视口 | `OnIdle` 在换视口时把 owner 迁移过去并重新施加 CPlane，而不是静默释放全局设置 |

## 8.3 第 5 视图 API 核对（本机 RhinoCommon.xml + 真实反射，不凭记忆）

| API | 签名 / 结论 |
|---|---|
| `SplitViewportVertical` | Rhino 9 命令存在（get_commands 实证）；`RhinoApp.RunScript("_SplitViewportVertical")` 返回 True，Top 宽 1540→769，新增右半视口 |
| `RhinoViewport.SetToPlanView` | `(Point3d planeOrigin, Vector3d planeXaxis, Vector3d planeYaxis, bool setConstructionPlane) -> bool`；实测 `CameraDirection=-Normal`、`CameraUp=YAxis`、`CameraTarget=Origin` |
| `RhinoViewport.ChangeToParallelProjection` | `(bool symmetricFrustum) -> bool` |
| `RhinoViewport.ZoomBoundingBox` | 平行投影下保持相机方向（v1.6 验证脚本 dot=1.0 间接确认） |
| `ViewTable.Add` | `(string, DefinedViewportProjection, Rectangle, bool) -> RhinoView`；本次用原生拆分命令而非 Add，让 Rhino 自己管理停靠布局 |
| `ViewTable.Find(Guid)` / `Find(string,bool)` | 存在，用于按 Id / 名字找回法向视图 |
| `RhinoViewport.Name` / `ViewTable.ActiveView` | 均可写 |
| `RhinoView.ScreenRectangle` / `Bounds` | 只读；`Size` / `Floating` / `Maximized` 可写 |

**踩坑**：`_4View`（重置为 4 视图）在无界面 Rhino 里会挂住，导致 300s 超时。验证改用全新干净实例，不碰布局重置命令；`SplitViewportVertical` 则是同步、非交互、可脚本驱动的。

## 8.4 真实编译与验证

- Roslyn 进程内编译（7 源文件）：`COMPILE SUCCESS 33280 bytes`，0 错误。编译脚本过滤掉 AppDomain 里已加载的旧版 `DatumPlanePlugin`，消除 CS0436；余 5 个 CS1701 为 `System.Drawing.Primitives` 版本差异，无害。
- `verification/Verify_v16.py` 在**干净 Rhino 9**（4 标准视图、空文档）反射驱动真实文档：**44/44 PASS**。
- 关键数值：`dot(CameraDirection, -Normal)=1.0`、`dot(CameraUp, YAxis)=1.0`、Top `1540→769`、视口 `4→5`、重复 Show 保持 5、切换基准面后相机自动跟随（dot=1.0）、还原后初始 CPlane 与非默认 Gumball 设置精确恢复。
- 命令类 8 个（新增 `DatumPlaneNormalViewCommand`），程序集版本 1.6.0.0，GUID 不变。

## 8.5 已知限制

- 交互式三点 / 选面 / 点选仍需用户点击；脚本只验证数据链、反射路径与 API 可设置性。
- 法向视图是「相机垂直于基准面的正视图」，不是剖切实体；若要看实体截面请用 Rhino 自带 ClippingPlane。
- 文件重开后 `NormalViewId` 里的视口 Guid 可能变化，靠视口名 `基准面法向` 兜底。

---

# 9. v1.7 Alias 护眼显示复核

## 9.1 API 核对（Rhino 9 真实反射，不凭记忆）

| API | 签名 / 结论 |
|---|---|
| `DisplayModeDescription.GetDisplayModes()` | 返回 15 个模式；本机存在内置 `Alias Style`（id `7680d433-…`）与 `Cyberstrak Display` |
| `DisplayModeDescription.FindByName(string)` | 按英文名查；不存在时返回 null（已包 try/catch） |
| `DisplayModeDescription.CopyDisplayMode(Guid, string)` | `-> Guid`，实测复制 Alias Style 成功，新 id 可用 |
| `DisplayModeDescription.UpdateDisplayMode(mode, bool)` | `-> bool`，实测 True |
| `DisplayModeDescription.SaveDisplayModes()` | 落盘到用户配置 |
| `DisplayModeDescription.DeleteDisplayMode(Guid)` | `-> bool`，测试模式已清理 |
| `DisplayModeDescription.DisplayAttributes` | 类型是 `DisplayPipelineAttributes`（不是 DisplayAttributes），只读属性，但其成员可写 |
| `DisplayPipelineAttributes.SetFill(Color, Color)` | 双色渐变；`FillMode = Gradient2Color`；读回严格一致 |
| `FillMode` 枚举 | `DefaultColor / SolidColor / Gradient2Color / Gradient4Color / Bitmap / Renderer / Transparent` |
| `LightingSchema` 枚举 | `None / DefaultLighting / SceneLighting / CustomLighting / AmbientOcclusion` |
| `SurfaceIsoColorUse` 枚举 | `ObjectColor / SingleColorForAll / SpecifiedUV` |
| `SurfaceIsoThicknessUse` 枚举 | `ObjectWidth / SingleWidthForAllCurves / PixelsUV` |
| `SurfaceNakedEdgeColorUse` 枚举 | `UseSurfaceEdgeSettings / ObjectColor / IsoCurveColor / SingleColorForAll` |
| `SurfaceEdgeColorUse` 枚举 | `ObjectColor / IsocurveColor / SingleColorForAll` |
| `SurfaceThicknessUse` 枚举 | `ObjectWidth / Pixels` |
| `RhinoViewport.DisplayMode` | 可读写，赋值 `DisplayModeDescription` 后 `Redraw()` 立即生效（4 视口实测全部切换） |
| `ObjectAttributes.WireDensity` | `-1` 无内部线，`0` 仅结构线，`1` 单条，`N>=2` 画 `N+1` 条内部等参线；配合 `RhinoObject.CommitChanges()` |
| `StringTable.GetValue(key, default)` / `SetString` / `Delete` | 用于记录与还原原显示模式 |

## 9.2 关键踩坑

**`SetSurfaceIsoColorUsage()` 会把 `SurfaceIsoColorsUsed` 重置为 false。** 第一次按"先设总开关、再设 usage"的顺序写，读回 `isoUsed=False`，等参线在截图里始终是默认黑色。正确顺序是：

```csharp
a.SetSurfaceIsoColorUsage(SurfaceIsoColorUse.SingleColorForAll);
a.SurfaceIsoColorsUsed = true;   // 必须最后
```

**U/V 双色在着色管线下不稳定**：`SpecifiedUV` + `SurfaceIsoUColor/VColor` 读回值正确，但实际渲染仍走黑色。改为 `SingleColorForAll` + `SurfaceIsoUVColor` 后真实生效（截图确认）。

**`SurfaceNakedEdgeColor` 单独赋值不生效**：还必须设 `SurfaceNakedEdgeColorUsage = SingleColorForAll`，否则走 `UseSurfaceEdgeSettings`/`ObjectColor`，裸边仍是黑粗线。

**`GridPlaneVisibilityMode` 只有 `ShowOnlyIfGridVisible / AlwaysShow`，没有 Off**；想压掉网格只能靠 `GridTransparency`（本版设 95）。

**`doc.Settings.CurrentWireDensity` 在 RhinoDoc 上不存在**（那是 `Rhino.FileIO.File3dmSettings` 的成员），命令里改为逐对象设 `Attributes.WireDensity`。

**`StringTable.GetValue(string, string)` 是 `(section, entry)`，不是 `(key, defaultValue)`。** 写入用的是无 section 的 `SetString(key, value)`（两参数），读取若用 `GetValue(key, "")` 会去查 section=`key`、entry=`""`，**永远返回 null**。表现为：`IsActive` 恒 false、`Restore` 直接 return 0、状态键写完读不到。修复是用单参数 `GetValue(key)` 配对 `SetString(key, value)`（已用 `GetValue(key)` 实测读回 264 字符的视口记录）。

**`DisplayModeDescription.UpdateDisplayMode(mode, true)` 返回 false 表示"参数无变化、无需更新"，不是失败。** 实测同一模式连续三次 `UpdateDisplayMode` 全返回 false，但属性值确实已写入并读回一致；真正改值时返回 true。原代码把 false 当失败 `return null`，导致第二次应用（切回浅色）命令返回 Failure、`RunScript` 看到 False。修复：忽略返回值，用 `GetDisplayMode(id) ?? mode` 拿回有效对象。

**构建平面网格不受 `GridTransparency` 控制。** 把显示模式里 `GridTransparency` 拉到 95，浅色/深色截图里网格依然明显；真正管它的是**视口属性** `RhinoViewport.ConstructionGridVisible`。修复：应用时置 false 并记入还原串，Restore 时按视口恢复原值。

## 9.3 编译与实拍验证

- Roslyn 进程内编译（8 源文件）：`COMPILE SUCCESS 43520 bytes`，0 错误，14 警告全部是 `System.Drawing.Primitives` CS1701 版本噪声。
- 修正的两处编译问题：`GetSelectedObjects()` 返回 `IEnumerable<RhinoObject>` 而非数组（CS0266）；`view?.ActiveViewport` 让编译器认为 `view` 可能为 null（CS8602），改为直接访问。
- 实拍对比（同一块起伏 NURBS + 球 + 环面，`WireDensity=4`）：
  - v1：背景过亮偏雾、网格明显、ISO 黑色 → 问题定位
  - v2：网格收掉、背景转柔和灰绿，但 `isoUsed=False` 仍黑
  - v3：`isoUsed=True`，ISO 转深青灰、裸边变淡、高光压低 → 参数定稿
  - v1.7 成品：`evidence/alias_v17_light2.jpg`（浅色）、`alias_v17_dark2.jpg`（深色），网格已消失、等参线清晰
- 状态机全链路（干净 Rhino 9，Assemble 版本 1.7.0.0）：

| 步骤 | 结果 |
|---|---|
| 初始 | `Wireframe` ×4，网格 `True` ×4 |
| `AliasStyleLight` | `Alias EyeCare` ×4，网格 `False` ×4 |
| 记录键 | `Active='Light'`；`Original` 264 字符，首个视口记录的模式 Id 为 `1311adcb…`（= Wireframe） |
| `AliasStyleDark` | `Alias EyeCare Dark` ×4 |
| `AliasStyleLight`（重复切回） | `Alias EyeCare` ×4（验证 UpdateDisplayMode false 修复） |
| `AliasStyleRestore` | `Wireframe` ×4，网格 `True` ×4 |
| 还原后键 | `Active=None`、`Original=None`（清理干净） |

## 9.4 v1.7 已知限制

- 显示模式写入的是**用户级 Rhino 配置**（`SaveDisplayModes`），因此会出现在所有文档的显示模式下拉里；这是特性而非缺陷，卸载插件后模式仍会留着，可在 Rhino 显示模式面板手动删除。
- 等参线密度是**对象属性**，不随显示模式走；换新曲面需要再跑一次 `AliasStyle → Density`，或提前把文档默认密度调好。
- 本版不包含斑马纹/曲率梳等诊断着色（那属于 `Zebra` / `Emap` 一类分析工具，不是显示模式能力）。

---

## 10. v1.8：JZ 命令别名 + 字母代号菜单

### 10.1 需求拆解

用户原话：「做别名，别名就是 JZ；中文依然保留，但前面用一个英文单词去简写；这样使用命令时可以通过选择字母去选择想要的效果」。拆成两件事：

1. 主命令短别名 `JZ`（"基准"拼音首字母），一敲即唤起。
2. 每个效果/选项用**固定字母代号 + 英文简写**开头，中文说明完整保留在后面；命令行敲那个字母即可选中。

### 10.2 先证明 API，再写逻辑（Rhino 9 实机反射）

| 结论 | 证据 |
|---|---|
| `JZ` 是合法命令名 | `Command.IsValidCommandName("JZ") = True`（`"A B"` = False） |
| `Style` 枚举含 `Hidden` / `ScriptRunner` | `Enum.GetNames` 实测 7 个值 |
| `CommandAliasList` 可增删别名 | `Add / Delete / GetMacro / SetMacro / IsAlias / FindAlias` 签名齐全；`IsAlias("JZ") = False`（本机未占用） |
| 选项名只允许字母数字 | 官方 SDK 文档 `AddOption(String)`：「Must only consist of letters and numbers (no periods, spaces, or dashes)」；`IsValidOptionName` 实测 `"A_Three"=True`、`"三点"=True`、`"Three Point"=False`、`"A=Three"=False`、`"_A"=False` |
| 中文要放第二个参数 | `AddOption(String, String)` 的第二参数是「option value，**visualized after an equality sign**」，即命令行显示成 `关键字=中文 / English` |
| 敲字母选中是 Rhino 原生行为 | `CommandLineOption.AcceleratorChar` / `AcceleratorIndex`（`<since>9.0</since>`）实机反射确认存在；McNeel 论坛：「the underlined option name letter in the command bar」可用，脚本推荐用完整名 |
| 加速键自动分配 | Rhino 取选项名里第一个**尚未被引用**的字母；旧版 `Plane`/`Pick`、`Recall`/`Restore` 撞首字母，字母会飘到第 2 个字符，不好记 |

### 10.3 设计决策

- **别名做成插件命令而不是写全局 Aliases 表**。`CommandAliasList` 是用户级持久设置；插件偷偷写入会在卸载后残留、还可能覆盖用户已有的 `JZ`。做成 `DatumPlaneJzCommand`（`EnglishName = "JZ"`）随 yak 安装/卸载自动生效，行为完全等价。若用户想在 `Options → Aliases` 面板看到，文档给了手动添加方法。
- **固定字母代号表 `Entries`（A–M）**，格式 `字母_英文简写`，首字母全局唯一 ⇒ 加速键固定就是那个字母，敲字母必中。`A`–`H` 是基准面效果，`I`–`M` 是 Alias 护眼显示效果。
- **三个入口共用同一套代号**：`JZ` 列全部 13 项，`DatumPlane`/`基准面` 列 A–H，`AliasStyle` 列 I–M。字母含义一致，记一次到处能用；区别只在列出哪些效果。
- **中文完整保留**：每个选项的 `Hint` 是「中文 / English」并列，显示在等号后；`SetCommandPrompt` 另外给出 `A=三点定义新基准面 I=浅色护眼显示 …` 的中文速查表。
- **底层逻辑与独立命令零改动**：`JzMenu.Run` 只是把字母分发到原来的 `DatumPlaneCore` / `DatumUi` / `AliasStyleUi` / `DatumPlaneNormalView`；`GetThreePoints` / `GetFace` 从 `private` 放宽为 `internal`，`SetDensity` 从命令类移到 `AliasStyleUi`。9 个独立命令、工具栏 9 个按钮全部保留，**RUI 不改**（v1.8 改动全在 `.rhp` 里）。

### 10.4 探测时踩到的坑

- **同一个 `GetOption` 里重复 `AddOption` 同名会返回 0**。首次探测先用 `LocalizeStringPair` 加了 `A_3Point`/`B_Plane`/`C_Pick`，再用 `AddOption(name, value)` 加同名返回 0，一度误判成「带下划线名字非法」；`D_Recall`…`H_Restore` 都正常返回 4–8，证明名字合法、只是重复。`AddOption` 返回值必须校验 `>0`（代码里已做）。
- **`LocalizeStringPair("A_3Point", "三点定义新基准面")` 也合法**（返回 1–3），但本版没用它：中文做本地化显示名后，英文界面会退回纯字母，反而看不到英文简写；用 `AddOption(name, value)` 两个语言都能并列显示。
- `GetBaseClass.Option()` 在 `Get()` 之前恒为 `None`、`OptionIndex()` 为 `-1`，**不能用它读回加速键**；加速键只能靠 `Get()` 后的 `CommandLineOption` 或实际敲键验证。所以字母命中改用 `RunScript("_JZ _I")` 端到端实测。

### 10.5 验证（全新 Rhino 9 实例，实机）

- Roslyn 进程内编译（9 源文件）：`COMPILE SUCCESS 44544 bytes`，0 错误，14 个警告全是 `System.Drawing.Primitives` CS1701 版本噪声。
- **`verification/Verify_v18.py`：37 PASS / 0 FAIL / 0 SKIP** —— 版本 `1.8.0.0`、GUID 不变、13 个命令全部注册、`JZ` 类名与 `EnglishName`、代号表 13 项 A–M 唯一且中文/英文并列、范围过滤 `All=13 / Datum=8 / Style=5`、提示含中文与字母速查、三个独立显示命令全链路（`Wireframe → Light → Dark → Wireframe`）。
- **字母命中端到端实测**（`RunScript` 把单个字母喂给命令，全部 `True`）：

  | 宏 | 结果 |
  |---|---|
  | `_JZ _I` | 4 视口 → `Alias EyeCare`，状态键 `Light` |
  | `_JZ _J` | 4 视口 → `Alias EyeCare Dark`，状态键 `Dark` |
  | `_JZ _L` | 状态查询，显示模式保持不变 |
  | `_JZ _M` | 4 视口 → `Wireframe`，状态键清空 |
  | `_AliasStyle _I` / `_J` / `_M` | 同样命中（Style 范围含 I–M） |
  | `_DatumPlane _H` | 正常结束（Datum 范围含 H，未激活时还原为空操作） |
  | 再 `_JZ _I` → `_JZ _M` | 循环切换 + 最终还原，状态干净 |

- **基准面核心回归**（反射驱动真实文档）：`Create A` → Success / `active=True` / CPlane `10,20,30`；**激活态再建 B** → Success / CPlane `-7,2,9`（v1.6 修复保持）；`Recall A` → Success / CPlane `10,20,30` / 对象数仍为 2（不重复创建）；`Deactivate` → `active=False` / CPlane 精确回到 `0,0,0`。
- 安装目录 `1.8.0.0\DatumPlanePlugin.rui` 在 Rhino 里 `ToolbarFiles.Open` 成功（9 按钮未变）。
- `Yak.exe install` 报 `Successfully installed 基准面工具 (1.8.0.0)`，`manifest.txt` 指向 `1.8.0.0`；新实例加载的正是 `1.8.0.0`。
- 验证脚本刻意把交互类测试拆开，避免 `Get()` 阻塞吞掉其余结果（v1.6 时 `_4View` 曾挂 300 秒）。
- 探测时另确认：`RhinoViewport.ConstructionPlane()` 是**方法**（返回 `Plane`，有 `.Origin`），不是属性；`GetConstructionPlane()` 返回 `ConstructionPlane` 对象（需 `.Plane`）。
