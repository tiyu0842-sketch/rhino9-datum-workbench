# 项目状态 · 已决与未决

## 已确定、不要再反复讨论的决定

1. **两个插件包完全独立**：`DatumPlane_v1_2`（基准面）与 `FeatureWorks`（特征识别）互不合并；`JZ` 只管基准面，显示命令走独立 `AliasStyle`。
2. **基准面配色** = 行业棕琥珀 `176,132,70`，透明 0.55。不用紫色（在 Creo 里是铣削体积块）。
3. **观测显示目的** = 看曲面走向与结构，不是追求 Alias 的纯白观感。因此 v2.4 弃用复刻路线，v2.6 改为方向光三度灰阶。
4. **浅色 = 密度 0（仅边界），深色 = 密度 1（一条内部等参线）**，两套模式靠这个区分。
5. **不投影阴影**：CustomLighting 下地面阴影被拉成大块深色椭圆，比无阴影更抢视线。
6. **第5视窗退出时保留基准面 CPlane**（相机本就垂直基准面，改回世界 XY 反而歪）。
7. **B 拾面直接点击，不需要 Ctrl+Shift**。
8. **Yak 分发，不用 .rhi**；安装前关代理。
9. **命令别名做成插件 Command 类**，不写用户全局 AliasList。
10. **不把用户提供的两个图标接进工具栏**（Alias 显示、FeatureWorks）——用户当时给了但未要求接入，留待明确指示。
11. **全视图联动默认开启**（v2.9）：切任一视口的显示模式，其余视口跟随，这是用户明确要的 Alias 式体验；
    想单视口对比时用 `AliasStyleLink`（菜单 `O_Link`）关掉。开关存 `PlugIn.Settings`，跨会话记住。
    实现事实：Rhino **一视口一份 DisplayMode** 是原生模型，靠 `DisplayPipeline.DisplayModeChanged` 静态事件补齐，
    同步时闸门防重入、先比 Id、`Apply`/`Restore` 全程 `Mute()`（否则还原会被同步覆盖）。

## 未完成 / 等待用户实机确认

- **FeatureWorks 面板 `FWPanel`**：v1.2 已编译打包，但反射条件下插件 `Instance=null`、`OnLoad` 不触发，无法证明面板真正注册。需用户在自己的 Rhino 里敲 `FWPanel` 验证。
- **FeatureWorks 曲面证据层 / 整体修复**：`FwSurfaceEvidence.cs` 已实现（9/9 PASS），但"用 UnderlyingSurface / trim 环判断加工史"的后续设想尚未落地。
- **v2.8 实机观感**：浅色密度 0 / 深色密度 1 的切换已反射实测，用户重启后需确认是否合意。
- **v2.9 全视图联动**：算法已用等价脚本真机跑通（Top→Shaded 后四视口全 Shaded，回调序列 `blocked×3 + 3`），
  插件 2.9.0.0 已 yak 真安装（sha256 `7454e87d…`），但**运行中的 Rhino 仍是 2.8**，需重开才加载。
  待验：用户**用手点视口标题栏下拉**确认 UI 路径与脚本路径一致。
- **布局页 detail 视窗**不同步（`doc.Views` 只列顶级视口）——已知边界，未排期。
- **用户提供的两个图标**：见已决第 10 条。

## 已知环境陷阱（这台机器）

- 无 .NET SDK，只有运行时；编译必须走 Rhino 进程内 Roslyn。
- `Yak.exe install` 前若代理未关会 SIGTERM 假失败；末尾安全策略提示不影响结果。
- 自动拉起的 Rhino 槽位偶发加载竞态，先 `print('alive')` 探活。
- `GetObject/GetOption` 交互无法从脚本同步驱动（300s 超时），只测拆出来的 Core。
- 截图必须置前窗口 + 相机微调 + Redraw + Wait，否则拿到缓存帧。
- 调参临时显示模式必须当场删，用户已明确要求列表里只留自己的三个 + 系统自带。

## 下一步（用户此前约定）

> "等你修复完了，我们讨论下一个问题" / "修改完之后呢，我们再来讨论 Future work 怎么去做"

FeatureWorks 的操作流程优化讨论尚未开始。用户此前反馈"感觉还是有一些问题"，具体卡点（识别步骤、结果可读性、参数修改、面板布局）待其描述。

## 复用资产

跨项目可复用的能力已固化为**用户级技能** `~/.workbuddy/skills/rhino9-plugin-workbench/`（含 API 坑位、显示模式配方、验证手册、通用 Roslyn 编译与 yak 打包脚本）。打包副本在 `_tmp/rhino9-plugin-workbench.zip`。
