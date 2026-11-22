---
name: rhino9-plugin-workbench
description: Rhino 9 / .NET 8 (RhinoCommon) C# plugin development workbench. Use when creating, modifying, compiling, packaging, deploying, or visually verifying Rhino 9 plugins — especially display modes, construction planes, viewport/datum tools, command menus, toolbars, or yak distribution. Loads a verification-first workflow plus verified API pitfalls and reusable scripts.
agent_created: true
---

# Rhino 9 插件工作台

## 目的

把 Rhino 9 / .NET 8 插件从"能编译"做到"真机验证过"，并避免重复踩已经踩过的坑。核心立场：**先验证再相信**——本机 SDK 缺失、API 行为与直觉相反、截图会返回缓存帧，任何没经真机验证的"应该可以"都必须当作未验证。

## 何时使用

- 创建或修改 Rhino 9 的 `.rhp` 插件（C# / RhinoCommon / net8）
- 调显示模式、光照、背景、等参线、轮廓线、阴影，或诊断"过曝/发灰/看不出结构"
- 处理工作平面 CPlane、视口相机、分屏视图、基准面/坐标系类工具
- 设计 `GetOption` 字母菜单、命令别名、Eto 面板、工具栏 RUI
- 打包 `.yak`、真安装、多版本并存、排障 Yak 安装失败
- 需要逐像素/反射/文档三件套验证 Rhino 侧改动

## 使用流程（按顺序执行）

1. **报错先查目录，再读环境事实**：遇到任何异常/反常现象，先查 `references/error-catalog.md`（按症状索引）。然后以 `C:\Program Files\Rhino 9\System\RhinoCommon.xml` 为 API 权威，反射 `GetMethods()/GetProperties()` 确认成员存在与签名。绝不凭记忆改代码。
2. **用进程内 Roslyn 编译**：本机只有 .NET 运行时无 SDK。直接执行 `scripts/Compile_Roslyn.py`（在 Rhino 的 Python 里 exec），用 `OUT_OVERRIDE` 全局指定输出路径，避免 `Assembly.LoadFrom` 锁文件。
3. **把交互逻辑与核心逻辑分离**：命令类只负责 `GetPoint/GetObject` 取参数，业务放进无交互的 public static Core。这样可以用 `Assembly.Load(File.ReadAllBytes(rhp))` 反射端到端验证，既不锁文件也不卡在交互命令上。
4. **验证三件套**（缺一不可）：
   - 反射断言：类型/命令/版本/API 存在
   - 真实文档状态：在临时或 headless 文档里跑 Core 方法，读回对象/字符串/属性
   - 视觉证据：截图 + 看图，必要时逐像素统计。见 `references/verification-playbook.md`
5. **打包分发**：一律 `.yak`，不要 `.rhi`。用 `scripts/Build_Package.py` 模板生成 manifest + zip，`Yak.exe install <本地.yak>` 真安装，核对安装目录 rhp 哈希与 manifest 版本。
6. **收尾清理**：调参临时显示模式用 `TMP_` 前缀并**当场删除**，绝不把 `ZZ_*` 之类测试模式留进用户的显示模式列表。

## 关键决策表

| Situation | 做法 |
|---|---|
| 本机无 .NET SDK | Rhino 进程内 Roslyn，收集 `AppDomain` 已加载程序集的 `Location` 作 MetadataReference |
| 插件覆盖安装被文件锁 | 先输出到新文件名，或 `Assembly.Load(File.ReadAllBytes(...))` 而非 LoadFrom |
| 要验证交互命令 | 不要从脚本同步驱动 `Get()`（会挂 300s）；反射调用拆出来的 Core |
| 显示"过曝一片白" | 先算 `clip(≥253)` 百分比；`DefaultLighting` + 白物体必削平，见显示模式参考 |
| 曲面糊成一片无明暗 | `AmbientOcclusion` 只有接触遮蔽；要三度灰阶用 `CustomLighting` + `FrontMaterial.Diffuse` |
| 截图看不出参数变化 | 大概率是缓存帧：置前窗口 + 相机轻微位移 + `ZoomBoundingBox` + `Redraw()` + `Wait()` + sleep |
| 选多重曲面上的单一面 | `GeometryFilter = ObjectType.Surface`（不要 |Brep）+ `SubObjectSelect=true` + `DisablePreSelect()` |
| 工具栏按钮装完消失 | 查 `ToolbarFiles[i].GetGroup(0).Visible`，设 True 后**正常退出 Rhino** 才写入 default.rui |
| Yak 安装 SIGTERM 假失败 | 先确认用户梯子/代理已关，再装；末尾的安全策略提示不影响安装结果 |
| `.rhi` 安装报不兼容 | .NET 8 插件天生不支持老式 RhiExec，改用 yak |

## 参考与脚本

- `references/error-catalog.md` — **先查这张表**：按"你看到的现象"索引（症状→原因→怎么办），并区分"真失败 / 已在工作 / 已回滚 / 只有人能处理"
- `references/rhinocommon-pitfalls.md` — 已实测的 API 行为、参数签名、赋值顺序坑
- `references/display-modes.md` — 显示模式/光照/等参线的实测参数组合与调参判据
- `references/verification-playbook.md` — 反射验证、像素统计、截图、Yak 安装的完整流程
- `scripts/Compile_Roslyn.py` — 进程内 Roslyn 编译（支持 `ROOT`/`FILES`/`OUT_OVERRIDE` 覆盖）
- `scripts/Build_Package.py` — manifest + yak 打包模板
- `assets/DatumPlane_light.svg` / `DatumPlane_dark.svg` — RUI 内联图标示例（40×40 viewBox，明暗两套）

需要某一类细节时再打开对应 reference，不要一次全读。
