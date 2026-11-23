---
name: rhino9-plugin-workbench
description: Rhino 9 / .NET 8 (RhinoCommon) C# plugin development workbench. Use when creating, modifying, compiling, packaging, deploying, or visually verifying Rhino 9 plugins — especially display modes, construction planes, viewport/datum tools, command menus, toolbars, yak distribution, B-rep feature recognition/untrim (fillets, holes, restoring a blank), DisplayConduit focus/translucent/highlight overlays, and Eto panels. Also covers Grasshopper parametric work: building/inspecting definitions on a live canvas (GH1/GH2 tools), data trees and list matching, choosing GH vs C#, and a 2336-component index. Loads a verification-first workflow, a symptom-indexed error catalog, an experiment log, verified API pitfalls, a full command index and reusable scripts.
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
- **B-rep 特征识别与取消**（圆角/孔/槽的 untrim、恢复毛坯、SolidWorks FeatureWorks 风格）→ 先读 `references/feature-recognition.md`
- **`DisplayConduit` 聚焦/半透明/高亮显示**，或排查半透明不生效、蒙皮"鬼影" → 同上专题 §4 + `rhinocommon-pitfalls.md` 对应段
- **Grasshopper 参数化 / 搭定义 / 数据树调错 / 阵列与渐变** → 先读 `references/grasshopper-spatial-logic.md`；查组件用 `references/grasshopper-component-index.md` 或 `g1_search_components`
- **在活画布上搭定义、改参数、读回结果** → `g1_*`（GH1）/ `g2_*`（GH2）两套工具，先用 `get_context` 看哪个画布开着；求解状态 ≠ 几何有效
- 做完任何一次真机实验 → 按下方「实验台账纪律」回填，别让结论只活在日志里

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
7. **实验台账纪律（每次真机实验后必做，这是能力累积的核心）**：
   - 结论被推翻也**不删旧记录**，加一条 `修正 E-XXX` 保留判断演化过程；
   - 按固定字段追加到 `references/experiment-log.md`（假设/做法/**实测数字**/结论/回填到哪/遗留）；
   - 同步把新坑按症状写进 `error-catalog.md`、把 API 事实写进 `rhinocommon-pitfalls.md`、把领域结论写进对应专题；
   - 下次遇到同类问题**先查这三处**，不要重新跑一遍验证——这是省 token 最直接的方式。
8. **动手实现前先查官方命令表**：先查 `rhino-command-index.md` 有没有现成命令（1256 条全量），
   有就抓官方页确认选项、再查 `rhino-command-reference.md` 的「命令 ↔ API ↔ 几何」对照；
   没有才反射 `RhinoCommon.xml` 找 API。**别凭命令名猜 API，也别重造官方已有交互**
   （`UntrimHoles` 逐孔选边、`DeleteFaces` face loop 都是这么漏掉的）。
9. **参数化与演示纪律（用户 2026-11-23 明确要求，长期有效）**：
   - **先讲原理再给结果**：每一步说清"在做什么、为什么"，不要只丢一张成功截图；
   - **失败也讲清为什么失败**、从中学到什么，别只报成功；
   - **交付必留手柄**：至少 3–6 个滑块/参数，别交付"只能看不能动"的死结果；
   - **一起改**：用户的想法先落成构造序列草图（意图 → 自由度 → 几何步骤 → 数据结构），确认后再连电池；
   - 想法落地后按 `design-lab/README.md` 六步存进仓库（想法原话 / 原理 / 构造序列 / 形态 / 证据 / 复盘）。

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
| 要"取消已做过的圆角/孔，恢复毛坯" | 先确认已有实现是否已做对；孔走 `UntrimFace`，圆角走删整圈+`CreateSolid` 重缝，**两套算法**；见 `feature-recognition.md` |
| 实体上叠半透明层看不出淡化 | 不透明底色不变；用 `DisplayConduit.ObjectCulling` 剔除源对象再画自己的子 Brep |
| 高亮面只剩线框 / 蒙皮鬼影 | 特征面画 `DrawForeground`；挂静态文档事件 + 包围盒指纹 `Stale()` 自愈 |
| Eto 要勾选多项 | `CheckBoxList.SelectedKeys`，不是 `ListBox` |
| 枚举不到对象、以为被删 | `ObjectEnumeratorSettings{ HiddenObjects=true }` 再判 |
| 同名程序集重编后跑旧代码 | AppDomain 复用；改 `ASSEMBLY_NAME` 隔离各次验证 |
| GH 求解 `solved=true` 但几何不对 | 求解器只保证没抛异常；必须读 `data.items` + 抽样数值 + 看几何（实测出现过尺寸为 0 的 `Singular Box`） |
| GH 视口有东西但文档 `Objects.Count = 0` | 正常：GH 只画 preview 不落地，要实体必须 Bake |
| GH 输出数量不对 / 配错对 | 先数每个输入的 item 数：单值广播、等长一一对应、不等长按最短；再查 path 是否一致 |
| `g1_*` 工具操作不到 GH2 画布 | 两套文档/API；先看 `get_context` 的 `version` 字段再选前缀 |
| 结论"应该可以"但没数字 | 一律当作**未验证**，不许写进交付物 |

## 参考与脚本

- `references/error-catalog.md` — **先查这张表**：按"你看到的现象"索引（症状→原因→怎么办），并区分"真失败 / 已在工作 / 已回滚 / 只有人能处理"
- `references/experiment-log.md` — **实验台账**：每条实验的假设/实测数字/结论/回填位置。查"这个坑以前踩过没、当时怎么判断的"就来这里
- `references/feature-recognition.md` — B-rep 特征识别与取消（两类算法、证据信号、DisplayConduit 聚焦、实测体积/面数）
- `references/grasshopper-spatial-logic.md` — **GH 空间逻辑精讲**：命令/构造/内核三层对照、Item-List-Tree、匹配规则、四步构造序列、坑位清单、何时 GH vs C#
- `references/grasshopper-component-index.md` — GH 组件索引（活进程导出 **2336 个 / 29 类**，原生全量 + 插件汇总 + 建模族速查）
- `references/rhino-command-index.md` — Rhino 9 全量 1256 命令索引（活进程导出，17 功能域 + 26 字母组，无遗漏）
- `references/rhino-command-reference.md` — 命令体系精讲：9 条官方原文、命令↔API↔几何三层对照、检索纪律
- `references/rhinocommon-pitfalls.md` — 已实测的 API 行为、参数签名、赋值顺序坑
- `references/display-modes.md` — 显示模式/光照/等参线的实测参数组合与调参判据
- `references/verification-playbook.md` — 反射验证、像素统计、截图、Yak 安装的完整流程
- `scripts/Compile_Roslyn.py` — 进程内 Roslyn 编译（支持 `ROOT`/`FILES`/`OUT_OVERRIDE` 覆盖）
- `scripts/Build_Package.py` — manifest + yak 打包模板
- `scripts/Export_Rhino_Commands.py` — 在 Rhino Python 里 exec，导出全量命令名（可移植路径，无本机硬编码）
- `scripts/Export_GH_Components.py` — 在 Rhino Python 里 exec，导出 GH 组件全集 TSV（装插件/升级后刷新索引）
- `assets/DatumPlane_light.svg` / `DatumPlane_dark.svg` — RUI 内联图标示例（40×40 viewBox，明暗两套）

需要某一类细节时再打开对应 reference，不要一次全读。
