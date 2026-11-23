# 错误目录：症状 → 原因 → 怎么办

借鉴 Cordyceps（Grasshopper MCP 桥）的 `CommonErrorsGuide` 结构：**按"用户看到的现象"索引，不按代码模块索引**。Agent 遇到报错时先查这张表，而不是重新推理。

关键约定（学自 Cordyceps）：
- 每条写清「这是真的失败，还是'已经在工作/已回滚'的成功变体」。把"卡住"误判成"死了"会导致重试风暴。
- 明确说明"这次调用有没有改动任何东西"——决定了要不要清理现场。
- 只要是 UI 线程/模态框问题，写明"只有人能处理"，别让 Agent 死循环重试。

## 编译与加载

| 症状 | 原因 | 怎么办 |
|---|---|---|
| `CS0436 type conflicts with imported type` | 引用里含本机已加载的旧版自身程序集 | 收集 `MetadataReference` 时跳过 `AssemblyName == 目标程序集名` |
| `FileNotFoundException` on MetadataReference | AppDomain 里某程序集 Location 已被重命名/删除 | 加 `os.path.exists(loc)` 过滤 |
| `CS1701 System.Drawing.Primitives 8.0 → 10.0` | 本机噪声，非真错误 | 忽略；只看 `0 error` |
| `CS0266 double → int` | `FrontMaterial.ShineIntensity` 是 int，写了 `0.0` | 写 `0` |
| 重编译报 "being used by another process" | `Assembly.LoadFrom` 锁住 rhp | `Assembly.Load(File.ReadAllBytes(...))`，或输出到 `_vXX.rhp` 新文件名 |
| 反射调用时 `Plugin.Instance = null`，面板没注册 | 反射 `Assembly.Load` 不算插件加载，`OnLoad` 未触发 | 这是测试条件限制，不是 bug；用真实 `PlugIn.LoadPlugIn` 或用户敲命令验证 |
| `rhino_crashed` / 刷新后脚本全失败 | MCP 自动拉起的 Rhino 有加载竞态 | 先 `print('alive')` 探活；仍失败则重新 spawn；用户自己开的 Rhino 通常稳定，优先复用 |
| `PlugIn.EnglishName`: no suitable method found to override | Rhino 9 的 PlugIn 只有只读 `Name`，没有可 override 的 EnglishName（同 ProductName 坑） | 删掉 override，插件名交给程序集标题/构造函数 |
| `RhinoGet` does not contain a definition for `GetReal` | RhinoCommon 9 没有 `GetReal` | 用 `RhinoGet.GetNumber(prompt, true, ref v, lower, upper)` |
| `Vector3d` has no attribute `DotProduct` | RhinoCommon 9 的 Vector3d 没有任何 `Dot*` 静态方法，只有 `Multiply` | 点积写 `a * b`（C# 与 Python 都是） |
| `Mesh` has no attribute `CreateBox` | RhinoCommon 9 没有 `Mesh.CreateBox` | 用 `Mesh.CreateFromBox(BoundingBox, xCount, yCount, zCount)`，分段数必填，各 1 段得 6 面 |
| 24 项模拟测试全过但真机一片错误 | mock 层自己造了不存在的方法（`Vector3d.DotProduct` 等） | mock 通过不能替代真机编译；每个 mock 的 API 都要用 `RhinoCommon.xml` 或反射核对 |
| `BrepFace` does not contain `Edges` | RhinoCommon 9 的 BrepFace 没有 Edges 属性 | 用 `face.AdjacentEdges()` → int[]，再 `brep.Edges[idx]` |
| `RhinoApp.WriteLine` takes N arguments 报错 | 没有格式参数重载 | 先 `string.Format(...)` 再传给 WriteLine |
| 曲面覆盖角算成 360°，圆角被误判为孔 | Rhino 9 曲面参数域是**弧长**不是弧度；且柱面的 U 是轴向、V 才是周向 | 覆盖角 = 域跨度 / 半径；取 `min(degU,degV)` 作为周向（轴向跨度远大于周向） |
| `BlendType` has no `RollingBallBlend` | 枚举值是 `Fillet`/`Chamfer`/`Blend`；滚球在 `RailType.RollingBall` | 按实际枚举名写 |
| 加载 DLL 后文件被锁、重编译报 used by another process | 失败的 LoadPlugIn 仍把 DLL 加载进 AppDomain | 输出到新文件名（与基准面 `OUT_OVERRIDE` 同一招） |
| `PlugIn.OnLoad(EventArgs)` no suitable method to override | Rhino 9 的 OnLoad 签名是 `LoadReturnCode OnLoad(ref string errorText)` | 改签名并返回 `LoadReturnCode.Success`（或 base 的返回） |
| `Command` is ambiguous between Rhino.Commands and Eto.Forms | 两个命名空间都有 Command 类 | 用全名 `Rhino.Commands.Command` |
| `BrepFaceList` does not contain `DeleteFaces` | Rhino 9 用 `RemoveAt(int)` 删面 | 从后往前删，避免索引偏移 |
| `LayerTable.FindName` 返回值不能转 int | 返回 `Layer` 对象不是 int | 取 `.Index`；找不到为 null 用 -1 |
| Eto `ListBox` 无法多选 | ListBox 没有 AllowMultipleSelection | 用 `GridView.AllowMultipleSelection = true` + `SelectedRows` |
| 面板加载后 `LoadPlugIn` 超时 300s | 无界面 MCP 槽位无法完整呈现停靠面板 | 用反射 `Activator.CreateInstance(panelType)` 验证控件树和交互链路；最终显示交用户实机敲命令 |
| **装了新版本，用户说"没有交互界面 / 命令没出现"** | ①装完没重启，AppDomain 里是旧程序集；②**插件从未被加载**（注册表 `LoadMode=2` 按需加载，而命令未注册 → 敲什么都触发不了加载，死锁） | 判据**不要用 `DockBarIdInUse`**（它只表示"是否已停靠成 dock bar"）：查 `AppDomain` 版本 → 查 `Panels.GetOpenPanelIds()` 是否含该 guid / `IsPanelVisible(g)` → 主动 `PlugIn.LoadPlugIn(guid)`（实测返回 True 即完成加载+注册，无需重开 Rhino）→ 再确认 `FW*` 命令出现 |
| 面板已加载但 `DockBarIdInUse=False` | 该 API 语义是"是否已停靠"，浮动/未停靠面板恒为 False | 用 `IsPanelVisible(g)` / `GetOpenPanelIds()` 判断，**别误判为注册失败**（E-020 推翻 E-014 的判据） |
| 一个进程里堆了几十个同名程序集（v1.2/1.3/v2 全在） | 反复 `Assembly.Load(byte[])` 注入的历史实验程序集，无法卸载 | 这是测试污染，不是发布问题；重启即清空。真机验收**必须在干净重启后的进程**做，否则会拿旧程序集误判 |
| `doc.ReplaceRhinoObject +=` 报 CS0176 | `ReplaceRhinoObject` / `DeleteRhinoObject` / `CloseDocument` 是**静态事件** | 写 `RhinoDoc.ReplaceRhinoObject += ...`，不能挂实例 |
| `CS0433 The type 'Action' exists in both 'WeaverBird.Core' and 'System.Private.CoreLib'` | 装了 WeaverBird 后，它把 `Action` 塞进全局/System 命名空间；**写 `System.Action` 也救不了** | 不用委托：把 `TrySilent(() => {...})` 内联成 `try { ... } catch { }`。同类第三方（如老版 NGon）也可能污染 `Action`/`Color` 等常用名 |
| `CS0120 An object reference is required for PersistentSettings.GetBool/SetBool` | `Rhino.PersistentSettings` 的读写是**实例方法**，没有全局静态入口 | 用插件自己的 `PlugIn.Settings`（就是 PersistentSettings 实例）：`Instance?.Settings?.GetBool(key, def)` / `SetBool(key, val)` |
| `using Rhino.DocObjects;` 后 `Environment` 报 CS0104 二义 | 该命名空间含 `Rhino.DocObjects.Environment`，与 `System.Environment` 撞名 | 写全名 `System.Environment.NewLine` |
| 反射调 `End(doc)` 报 Parameter count mismatch | 方法加了可选参数 `bool redraw = true` | 反射调用必须传全部实参，可选参数不会自动补 |
| 改了代码重编译却还在跑旧逻辑 | 同名程序集被 AppDomain 复用（`Assembly.Load(byte[])` 多次） | 改 `ASSEMBLY_NAME`（如 `…C3/C4/C5/C6`）隔离各次验证 |
| `RhinoGet.GetInteger(...)` 编译不过 | Rhino 9 签名含 `bool acceptNothing` 参数 | 补齐布尔实参 |
| yak manifest 解析失败 | `description` 里出现 `v1.3: pick` 这种「冒号+空格」 | 改写描述，YAML 值里避免 `: ` |
| `CheckBoxList` 取不到勾选项 | 用了 `ListBox`（无多选）或按 `Items[i]` 值匹配 | 用 `CheckBoxList.SelectedKeys`；`Items[i]` 是 `IListItem`，按 `.Key` 匹配 |
| `ObjectEnumeratorSettings` 枚举结果是 0，以为对象被删 | 默认**不返回隐藏对象** | 设 `HiddenObjects = true` 再枚举，先排除误判 |

## 交互命令

| 症状 | 原因 | 怎么办 |
|---|---|---|
| `RunScript` 后命令停住、300 秒超时 | 脚本无法喂 `GetPoint` / `GetOption` 的交互式 `Get()` | 不要从脚本驱动交互；把业务拆成无交互 Core，反射调用 |
| `_4View` 挂死 | 无界面实例里视口布局命令等 UI | 用全新 spawn 实例，或 `FourViewLayout(true)` + 清 Id 字符串 |
| 交互测试一挂，整批验证结果全丢 | 把交互调用和断言放在同一脚本 | 交互测试单独一次调用；其余断言分批 |

**卡住 vs 死掉**：脚本超时但 Rhino 进程还在、窗口还能点 → 是模态框或交互等待，**只有人能清**；让 Agent 停手，别重试。

## 显示与视觉

| 症状 | 原因 | 怎么办 |
|---|---|---|
| 改了参数，几张截图字节数/像素完全一样 | `CaptureToBitmap` 返回缓存帧，改 `DisplayMode` 不触发重绘 | 置前窗口 + 相机微移 + `ZoomBoundingBox` + `Redraw()` + `Wait()` + sleep，每张图前重新置前 |
| 4 视图里截图颜色单一，像"背景没生效" | 抓到的是 605×206 的小格 | `view.Maximized = True` 再抓 |
| 等参线一片红绿 | 只设了 `SurfaceIsoUVColor`，U/V 仍是默认色 | `SurfaceIsoUColor` / `VColor` 同色 |
| 等参线开关设了却没线 | `SetSurfaceIsoColorUsage()` 把 `SurfaceIsoColorsUsed` 重置 false | 总开关最后赋值；密度 <2 的单跨曲面不出内部线 |
| 装了新版显示模式但观感没变 | 已注册模式无法原地更新，`UpdateDisplayMode` 返回 false 且不落盘 | `DeleteDisplayMode` + `SaveDisplayModes()` + `CopyDisplayMode` 重建 |
| 画面一片死白 | `DefaultLighting` + 白物体，受光面到 255 | 换 `CustomLighting` + 中灰 albedo；用 `clip(≥253)` 定量 |
| 曲面糊成一片没明暗 | 用了 `AmbientOcclusion`，只有接触遮蔽没有方向光 | 换 `CustomLighting` + `FrontMaterial.Diffuse` |
| 影子里出现大块深色椭圆 | CustomLighting 的方向光把地面阴影拉长 | 关 `ShadowsOn` / `CastShadows` / `CustomGroundPlaneOn` |
| 点多重曲面面片必须按 Ctrl+Shift | `GeometryFilter` 含 `Brep`，顶层对象抢先被选 | 只给 `ObjectType.Surface` + `SubObjectSelect=true` + `DisablePreSelect()` |
| 叠了 0.85 透明灰，实体看起来几乎没淡化 | 往**不透明实体**上叠透明层，底色不变 | 用 `DisplayConduit.ObjectCulling` → `e.CullObject = true` 剔除源对象，再画自己的半透明子 Brep |
| 高亮面只剩线框 / 被实体挡住 | 在 `PostDrawObjects` 里画，被实体深度剔掉 | 特征面改画 `DrawForeground`（不参与深度剔除）；锁定面可留 `PostDrawObjects` |
| 高亮/半透明蒙皮「鬼影」，移动删除后仍赖在界面上 | conduit 缓存按面索引抽的子面，源对象 Replace/删后索引失效 | ①挂静态 `RhinoDoc.ReplaceRhinoObject/DeleteRhinoObject/CloseDocument` ②每次绘制前 `Stale()` 比面数 + 包围盒中心漂移 >2% ③扫描所有同名程序集实例逐个 `End()` |
| 多帧截图完全一致（相机微移无效） | 缓存帧只认朝向变化 | 必须 `SetCameraDirection` 换相机朝向，微移/Redraw 不够 |
| `ReferenceEquals` 判几何过期永远为 true | `ObjRef.Brep()` 返回副本 | 用面数 + `GetBoundingBox` 中心漂移判定，别比引用 |
| 切显示模式只有当前视口变、其余没动 | Rhino 原生：一视口一个 DisplayMode；标题栏下拉 / 视图菜单 / `_SetDisplayMode` 都只作用当前视口 | 挂 `DisplayPipeline.DisplayModeChanged` 静态事件同步（E-021，`display-modes.md`「全视图联动」）。**先读回各视口真实模式**再判断是不是命令的锅 |
| 做了联动后 `Restore` 还原失效（视口被拉回同一模式） | 程序化批量改模式时钩子仍在工作，后写的覆盖先写的 | `Apply` / `Restore` 全程 `Mute()`（引用计数），`finally` 里 `Unmute()` |

## 几何特征识别与取消（FeatureWorks 类需求）

| 症状 | 原因 | 怎么办 |
|---|---|---|
| `Brep.UntrimOuterLoop(face)` 对圆角返回 null | 实体圆角面的外环四边全被邻面共享，不是自由边 | 圆角不能 untrim：删整圈过渡面 → 剩余面 `UnderlyingSurface().ToBrep()` → `Brep.CreateSolid(pieces, tol)` 重缝 |
| 只删 1 个圆角，缝出变形体（9 面 74715.5） | 圆角是**整圈**过渡面 | 必须整圈一起删，才得 6 面 75000 |
| 取消一个孔，同面其它孔也没了 | `UntrimFace(host, tol)` 抹掉宿主面**全部**内环，Rhino API 边界 | 在命令输出里明说；「只取消部分」需另做孔体重放 |
| 覆盖角算成 360°，圆角被误判为孔 | 参数域是**弧长**非弧度；柱面 U=轴向 V=周向 | 覆盖角 = 跨度/半径，取 `min(degU,degV)`；取 max 会把轴向长跨度截成 360° |
| 倒角面按曲面类型识别失败 | Rhino 里倒角面是 `NurbsSurface` 不是圆柱面 | 用识别引擎给的特征面索引，别按类型猜 |
| 带 trim 的面直接 `CreateSolid` 失败，孔口留洞 | trim 后的面不是完整解析面 | 必须先取回 `UnderlyingSurface().ToBrep()` 再缝 |

## 分发与安装

| 症状 | 原因 | 怎么办 |
|---|---|---|
| `.rhi` 报 "not compatible with the Rhino Installer Engine" | 老式 RhiExec 用 .NET Framework 反射检查 net8 的 rhp，抛 `System.Private.CoreLib` 解析失败 | 改用 `.yak`，不要用 .rhi |
| `yak install` 只打印 Installing... 然后 SIGTERM | 代理/梯子开着，Yak 联网校验被杀 | **关代理再装**；安装目录会残留空壳，重装即可覆盖 |
| `yak install` 末尾出现安全策略提示 | 沙箱提示，与 Yak 结果无关 | 核对 stdout 的 `Successfully installed X (版本)`，不要重试 |
| `yak uninstall` 报 Access denied | 后台 Rhino 占用 | 关掉 Rhino 再卸；多版本并存也不影响，manifest 指向最新即可 |
| 装完工具栏按钮消失 | 工具栏组 `Visible=False`（RUI 重新加载后状态丢失） | `ToolbarFiles[i].GetGroup(0).Visible=True` → **正常退出 Rhino** → 重开验证；不要对安装目录 RUI 调 `Save()` |
| 用 `Open(安装目录RUI)+Save()` 后重开又隐藏 | 状态存在用户配置 `UI\default.rui`，不是插件 RUI | 同上，必须走"设值→正常退出→重开" |
| 显示模式下拉里堆满 `ZZ_*` 测试项 | 参数扫描建的临时模式没删 | 建模式用 `TMP_` 前缀，验证完 `DeleteDisplayMode` + `SaveDisplayModes()`，删前确认没视口在用 |

## 平面/视口状态

| 症状 | 原因 | 怎么办 |
|---|---|---|
| 取消后 CPlane 恢复成基准面自己 | 在 `SetConstructionPlane(plane)` 之后才读"原平面" | 改任何状态**之前**先读原值 |
| 显示"已启用"但坐标锁其实松了 | 换视口时静默 `ReleaseGlobalSettings()`，却留着 `Active=1` | 迁移 owner 到新视口并重新施加 CPlane |
| 退出后 Front 视图歪了 | CPlane 被基准面覆盖，旧版只记最后一个 `ViewportId`，前面的视口还原不到 | 逐视口存档原 CPlane + 退出遍历还原 + 残留自愈 |
| "已有基准面，不能选择" | 激活态把"新建"当成禁止操作 | 激活态把 `Create` 映射为 `SwitchTo`，保留唯一恢复基线 |
| 第5视窗退出后网格和镜头错开 | 把它的 CPlane 改回世界 XY，而相机仍垂直基准面 | 第5视窗保留基准面 CPlane，不参与还原 |
