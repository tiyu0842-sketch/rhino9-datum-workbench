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
