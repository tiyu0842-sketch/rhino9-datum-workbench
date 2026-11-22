# 基准面工具 · 架构与数据流

## 模块职责（src/）

| 文件 | 职责 | 不做什么 |
|---|---|---|
| `DatumPlanePlugin.cs` | 插件壳，`OnLoad` 启动 Core 的 Idle 监视 | 不含业务 |
| `DatumPlaneCore.cs` | 状态机与平面数据：Create/SwitchTo/Recall/Lock/Deactivate、文档字符串持久化、全局设置租约、逐视口 CPlane 存档与自愈 | 不碰交互拾取 |
| `DatumPlaneCommand.cs` | 交互取平面：三点拾取、面拾取（含面质心标架、点击点兜底） | 不改状态机 |
| `DatumPlaneLayers.cs` | 编号子层 `DP_01…`、用户字符串标记、锁定/回滚清理 | 不决定平面 |
| `DatumPlaneNormalView.cs` | 第5视窗：分屏、相机垂直于基准面、跟随刷新、关闭回4视图 | 不处理主视口 |
| `AliasStyleDisplay.cs` | 两套观测显示模式的注册/参数/应用/还原、WireDensity 强制设置、状态汇报 | 与基准面状态机完全独立 |
| `JzMenu.cs` | 统一字母菜单 A–N / I–M，`JZ` 插件命令 | 只分发，不实现 |
| `PlaneText.cs` | Plane 序列化/反序列化（InvariantCulture，9 个 double） | — |
| `AssemblyInfo.cs` | GUID / 版本 / 描述 | — |

## 命令入口

- `JZ` / `DatumPlane` / `基准面` → `JzMenu.Run(JzScope.Datum)`，列 A–H + N
- `AliasStyle` → `JzMenu.Run(JzScope.Style)`，列 I–M
- 独立命令（给工具栏/脚本）：`DatumPlanePick` / `Restore` / `Save` / `Recall` / `Lock` / `NormalView` / `NormalViewClose` / `AliasStyleLight` / `Dark` / `Restore`

字母固定代号：A 三点 / B 拾面 / C 点选已有 / D 按编号调用 / E 另存 / F 锁定 / G 第5视图 / H 还原 / N 关第5视窗 / I 浅色显示 / J 深色显示 / K 等参线密度 / L 状态 / M 还原显示。

## 数据模型

- **唯一真源**：`doc.NamedConstructionPlanes`（平面几何）+ 文档字符串 `DatumPlane` 段（状态）
- 文档字符串：`Active` / `ActivePlane`（进入模式前的原始 CPlane）/ `LockedPlane` / `SavedName` / `ViewportId` / `Version` / `SavedCPlanes`（逐视口原平面）/ `NormalViewId`
- 基准面对象上只存三个 UserString：Kind / Name / Layer，**不再存第二份坐标**
- 显示模式还原串：`DatumPlane.AliasStyle.Original` = `视口Id=模式Id=网格0/1=轴0/1;`

## 关键流程

### 创建 / 切换
`Create` → 读当前 CPlane 作 `previous` → 建面质心标架 → 建子层（未锁）→ AddBrep → 命名平面 → `Activate` 或 `SwitchTo` → 全部成功后才锁子层；失败走 `CleanupEmptySubLayer`。

`SwitchTo` 只更新 `LockedPlane/SavedName/ViewportId`，**绝不覆盖 `ActivePlane`**（唯一恢复基线）。

### 跟随活动视口
`OnIdle`：若 Active=1，发现活动视口变化 → 迁移 owner、`RememberViewportCPlane` 存档、施加基准面 CPlane。这样任何视口（含第5视窗）都能建模。

### 退出还原
`Deactivate` → 读 `ActivePlane` → 遍历 `SavedCPlanes` 逐视口还原各自原平面 → 活动视口/旧 ViewportId 兜底 → `RepairLeakedCPlanes` 自愈 → 清状态、释放全局设置。
模式未激活时调用 `Deactivate` 也会跑自愈，用于救回旧版留下的歪视图。

### 显示模式
`AliasStyle.EnsureMode` 先删旧模式再 `CopyDisplayMode(Shaded)` 重建（已注册模式无法原地更新）。`Apply` 设 `CustomLighting` + albedo + 低环境光 + 关阴影 + 等参线/轮廓线，并强制设置 `WireDensity`（浅 0 / 深 1）。`Restore` 按还原串恢复模式与网格/轴。

## 依赖与约束

- Rhino 9 / .NET 8；测试机 `C:\Program Files\Rhino 9\System`
- 构建无 .NET SDK，靠进程内 Roslyn（见 `verification/Compile_Roslyn.py`）
- 插件不写用户全局 CommandAliasList、不回放旧 .3dm 的应用偏好
- `verification/` 下脚本：Compile_Roslyn（编译）、Build_Package（打包）、Verify_v16 / v18（历史回归）、Verify_Rhino（通用探针）
