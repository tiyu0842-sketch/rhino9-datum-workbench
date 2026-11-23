> ## ⚠️ 已降级为实验记录（2026-11-23）
>
> **本目录不再是 FeatureWorks 的正式实现，请勿作为参考基线使用。**
> 它做的是「按解析面类型挑 fillet/chamfer 面 → 删面 + `FW_Backup` 图层备份 → 还原备份对象」，
> 即**备份对象恢复**，不是几何 untrim；用户真正的痛点是「倒角/布尔后想再编辑，不想手工备份」，
> 需要把几何**恢复成可重新编辑的毛坯**，本目录没有解决。
>
> **正式实现请看 [`../featureworks/`](../featureworks/)（RhinoFeatureWorks v1.3.2）**：
> 用 `Brep.UntrimFace`（孔）/ 删整圈过渡面 + `CreateSolid` 重缝（圆角）两套算法真正回到毛坯，
> 并有 `FWSelect`/`FWCancel` 交互闭环、真机 9/9 自测与 yak 真安装。
> 方向纠偏的完整复盘见 [`../featureworks/HANDOFF.md`](../featureworks/HANDOFF.md)。
>
> 本目录保留仅供工程做法参考（Eto 布局、`BeginUndoRecord` 分组、处理按钮三分支），不进入发布物料。
> 以下为历史记录。

# FeatureWorks v2 — 几何特征识别（Rhino 9 / .NET 8）

按外包技术规格**全新实现**：识别实体上的圆角（fillet）与倒角（chamfer），在 **Eto 停靠面板**里列出、多选、高亮，并执行删除/抑制处理。

## 已确认的边界（不要推翻）

1. **Rhino 没有特征树** —— 所有"特征"都是几何反推，不做参数化 Suppress
2. **圆弧 ≠ 圆角** —— 本版只做**面特征**（fillet/chamfer），圆弧（曲线）留待下一版
3. **多核并行** —— 逐面计算走 `Parallel.ForEach`，文档增删改回主线程
4. **交互对齐原 HTML 原型**：识别 → 列表多选 → 视口高亮 → 统一处理
5. **"抑制" = 移到备份图层**，可恢复；不是参数化 Suppress

## 交互界面（FWPanel）

`FWPanel` 命令打开 Eto 停靠面板，布局对应原交互原型：

| 区域 | 内容 |
|---|---|
| 顶部 | r_max 比例输入（默认 0.05×对角线）+「识别选中实体」按钮 |
| 中部 | 5 列 GridView（类型 / 面# / 半径 / 覆盖角 / 置信度），**允许多选** |
| 详情 | 选中特征的链号、类型、面数、参数 |
| 底部 | 高亮 / 删除圆角 / 抑制(移出) / 还原(Untrim) 四个按钮 |

- 点列表项 → 视口里对应面高亮（红=边圆角、蓝=顶点圆角、橙=倒角）
- 删除/抑制 → 原对象移到 `FW_Backup` 图层（可恢复），新对象留在原图层
- 所有文档操作在 UI 线程（按钮点击）完成，符合 RhinoCommon 线程红线

## 真机验证（面板链路）

| 检查项 | 结果 |
|---|---|
| 面板实例化（Eto 控件树） | PASS：Scrollable 内容、5 列 GridView、多选开启、4 按钮齐全 |
| 识别 → Session → 列表 | PASS：2 组特征 → GridView 2 行 |
| 列表选中 → Session 同步 → 高亮 | PASS：选中行 0 → Session={0} → 生成高亮对象 |
| 删除处理 | PASS：删 1 面、`FW_Backup` 图层建立、状态正确 |

> 面板的完整显示需在真实 Rhino 里加载插件后敲 `FWPanel`——无界面 MCP 槽位无法验证停靠面板的最终呈现，这是环境限制不是代码问题。

## 几何判据（三条互相印证）

| 判据 | 做法 | 为什么 |
|---|---|---|
| 面类型 | `Surface.TryGetCylinder/Torus/Sphere/Plane` | 圆角是过渡曲面，chamfer 是平面 |
| 覆盖角 | 参数域跨度 / 半径（**Rhino 9 参数域是弧长不是弧度**） | 圆角约 90°，完整柱孔约 360°——这是区分圆角与孔的关键 |
| 邻接 G1 | 共享边中点两法线夹角 < 8° | 圆角与两侧母面相切；只 1 个邻居的不算 |
| chamfer | 平面 + 窄条（短边/长边 < 0.6）+ 与两邻面成 25~65° | chamfer 是平面斜面，与曲面圆角判据不同 |

**覆盖角的大坑**：圆柱圆角面的 U 域是**轴向**（如 -3..63，长 66），V 域才是**周向**（0..4.712 = 3π/2）。
取 `max(degU,degV)` 会把轴向 1260° 截断成 360°，误判成孔；必须取 `min`。

## 实测结果（Rhino 9.1.26314.9001 真机）

| 测试模型 | 预期 | 实测 |
|---|---|---|
| 普通盒子（6 面） | 0 个特征 | 0 ✓ |
| 倒 3mm 圆角的 100×80×60 盒子 | 识别出 2 个圆柱圆角面 | 2 个 fillet-edge，r=3，sweep=90°，conf=1.00 ✓ |
| 带 φ10 圆孔的板 | 孔不能误判成圆角 | 0 ✓ |
| chamfer 盒 | 识别出倒角平面 | 1 个 chamfer，conf=0.85 ✓ |
| 完整球体 / 完整圆柱 | 封闭面，不算圆角 | 0 ✓ |

编译：进程内 Roslyn，4 个源文件，**0 error，15360 字节**。

## 真机抓到并修复的 API 差异（RhinoCommon 9）

1. `BrepFace` 没有 `Edges` → 用 `AdjacentEdges()` 返回 int[]，再索引 `brep.Edges[i]`
2. `BrepFace.ClosestPoint` 只有三参重载 `(Point3d, out u, out v)`
3. `PlugIn.EnglishName` 不可 override（只有只读 `Name`）
4. `RhinoApp.WriteLine` 没有格式参数重载 → 先 `string.Format`
5. 曲面参数域是弧长，覆盖角 = 跨度 / 半径（不是弧度）
6. `BlendType` 枚举值是 `Fillet`/`Chamfer`/`Blend`，不是 `RollingBallBlend`
7. `RailType` 是 `RollingBall`/`DistanceFromEdge` 等
8. `PlugIn.OnLoad` 签名是 `LoadReturnCode OnLoad(ref string)`，不是 `void OnLoad(EventArgs)`
9. `Eto.Forms.Command` 与 `Rhino.Commands.Command` 歧义 → 用全名
10. `BrepFaceList` 没有 `DeleteFaces` → 用 `RemoveAt(int)`，从后往前删避免索引偏移
11. `LayerTable.FindName` 返回 `Layer` 对象（取 `.Index`），不是 int
12. Eto 的 `ListBox` 不支持多选 → 用 `GridView.AllowMultipleSelection = true`

## 命令

- `FWPanel` —— 打开 Eto 停靠面板（**主入口**，完整交互都在这）
- `FWRecognize` —— 纯命令行版：拾取 → 输入 r_max → 列出 → 高亮。原对象不改动。

## 文件

- `src/FwCore.cs` —— 识别引擎（纯计算，可并行，反射可测）
- `src/FwSession.cs` —— 会话状态（面板/命令共享选中集与高亮）
- `src/FwPanel.cs` —— Eto 停靠面板 + `FWPanel` 命令
- `src/FwCommands.cs` —— `FWRecognize` 命令行版
- `src/FwPlugin.cs` —— 插件入口（GUID `3C9E7A15-8B42-4D6F-A0E3-7F15B2C9D840`），OnLoad 注册面板
- `src/AssemblyInfo.cs` —— 版本 2.0.0.0
- `FeatureWorks_panel.rhp` —— 含面板的真编译产物（26112 字节）

## 下一版待做

- 还原操作真正实现 Untrim（当前按钮 grounded 在备份图层恢复语义）
- 圆弧识别（曲线类：`Curve.TryGetArc` / `ArcCurve`）
- NURBS 近似圆角的曲率拟合降级路线（标注低置信度）
- Grasshopper 组件（本版只有 Rhino 命令与面板）
- Yak 打包安装（本版只编译验证，未安装）
