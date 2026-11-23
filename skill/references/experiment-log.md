# 实验台账（Experiment Log）

> **用途**：把每一次真机实验固化成「以后查一条就够」的结论，避免重复跑同样的验证、重复踩同样的坑——这是省 token 最直接的手段。
> **纪律**：每个实验当天回填；结论若被后续实验推翻，**不删旧条目**，加一条 `修正` 并指向新结论（保留判断演化的过程，才知道当初为什么错）。
> **字段固定**：编号 / 日期 / 假设 / 做法 / 实测 / 结论 / 回填到哪。实测必须带数字或可复现现象，不写「应该可以」。

## 台账模板（复制这一段追加）

```
### E-XXX · YYYY-MM-DD · 一句话标题
- 假设：
- 做法：（编译/反射/文档/截图，用了哪个脚本）
- 实测：（数字、字节数、面数、体积、PASS/FAIL、截图文件）
- 结论：✅ 成立 / ❌ 推翻 / ⚠️ 部分成立
- 回填：error-catalog.md「…」 / rhinocommon-pitfalls.md「…」 / 专题「…」
- 遗留：
```

---

## 已归档实验

### E-001 · 2026-11-21 · mock 层通过不等于真机能跑（NFF）
- 假设：24 项单元测试全过 → C# 插件也能编译运行。
- 做法：Python 模拟层测试 → Rhino 进程内 Roslyn 真编译 → 反射。
- 实测：24/24 模拟 PASS，真机编译暴露 5 个错误（`Mesh.CreateBox`、`Vector3d.DotProduct`、`PlugIn.EnglishName`、`RhinoGet.GetReal`、C# 点积）。
- 结论：❌ 推翻。mock 层自己造了 RhinoCommon 9 里根本不存在的方法。
- 回填：`error-catalog.md`「24 项模拟测试全过但真机一片错误」；写入复盘文档核心教训。
- 遗留：无。**这条是所有后续实验的元规则**。

### E-002 · 2026-11-22 · 显示模式三度灰阶
- 假设：用 Arctic 式 AO 能看出曲面结构。
- 做法：切 `AmbientOcclusion` vs `CustomLighting` + `FrontMaterial.Diffuse`，逐像素统计。
- 实测：`clip(≥253)` 从 2.3~9.5% → **0.00%**；P10/50/90 = **101/119/152**，跨度 51。
- 结论：❌ AO 只有接触遮蔽没有方向光；✅ 三度灰阶要靠方向光 + 中灰 albedo。
- 回填：`display-modes.md`；`SKILL.md` 决策表；复盘文档。
- 遗留：已注册模式无法原地更新，升级必须先删再建。

### E-003 · 2026-11-22 · 截图缓存帧
- 假设：改了显示参数，截图会跟着变。
- 做法：连续抓多张不同参数截图比对字节/像素。
- 实测：多张图完全一致；相机**小幅位移无效**，必须 `SetCameraDirection` 换朝向才拿得到新帧。
- 结论：⚠️ 部分成立。`CaptureToBitmap()` 会返回缓存帧。
- 回填：`error-catalog.md` 显示与视觉首条；`verification-playbook.md`。
- 修正（E-010）：补「必须换相机朝向，微移不够」。

### E-004 · 2026-11-23 · FeatureWorks v2 识别引擎（方向错误，已降级）
- 假设：按外包技术规格全新实现 AAG 邻接图识别是对的。
- 做法：三条判据（面类型 / 覆盖角 / G1 相切）全新写一套，真机验证圆角盒/带孔板/chamfer 盒。
- 实测：0 error / 15360 bytes；圆角盒识别 2 组（r=3, sweep=90°, conf=1.00），chamfer 1 组（0.85），带孔板 0 特征（孔不误判）。抓到 7 个 API 差异。
- 结论：❌ **技术成功但方向错误**。用户本意是「取消已做过的特征、恢复毛坯」，不是「识别+列出+高亮」；且已有 `FeatureWorks/` v1.2 本来就实现了本意。v2 降级为实验记录，不进正式物料。
- 回填：`feature-recognition.md` §0「先认清需求」；工作区 `MEMORY.md`。
- 遗留：❗动工前先确认「已有实现是不是本来就对」，别重复造轮子。

### E-005 · 2026-11-23 · v1.2 基线复检
- 假设：旧 `FeatureWorks/` v1.2 可能只是半成品。
- 做法：进程内 Roslyn 重编 11 个 .cs → 反射 → `FwSelfTest.Run()` → 真实文档端到端。
- 实测：rhp 68608 bytes / 0 error；13 个命令；**9/9 PASS**；布尔件 12 面 → 修复 6 面 solid **240000**；R3 倒角盒 10 面 → 6 面 **75000**；原文档 5 对象未动。
- 结论：✅ 成立。v1.2 是正确基线，后续应在其上增量优化而不是重写。
- 回填：`feature-recognition.md` §1 实测表；工作区 `MEMORY.md`。
- 遗留：证据只写命令行、面板不能逐面勾选、无 Undo 分组、无工具栏。

### E-006 · 2026-11-23 · 两类特征必须用两套取消算法
- 假设：孔洞和圆角可以统一用 untrim 处理。
- 做法：`UntrimFace` / `UntrimOuterLoop` / `CreateSolid` 分别跑带孔块与倒角盒。
- 实测：`UntrimFace` 抹内环 → 7 面 6 面 **240000**、孔+槽 12 面 → 11 面 **224000**；`UntrimOuterLoop` 对实体圆角**一律返回 null**；只删 1 个圆角 → 9 面 **74715.5**（变形），删全部 4 个 → 6 面 **75000**；完整链 229667.59 → 237301.66 → **240000**。
- 结论：❌ 推翻。孔=trim 内环改动，圆角=过渡面，**方法不同**（这正是用户事先的判断，被 API 证实）。圆角必须整圈删+重缝。
- 回填：`feature-recognition.md` §1；`rhinocommon-pitfalls.md` 几何。
- 遗留：`UntrimFace` 会抹同面所有内环（API 边界）；孔体重放 `240000 → 236607.08` 几何可行，待实现。

### E-007 · 2026-11-23 · 假半透明
- 假设：往实体上叠 0.85 透明灰就能做出「锁定」的淡化感。
- 做法：`PostDrawObjects` 里叠 `DisplayMaterial.Transparency=0.85` 灰层，截图比对。
- 实测：底色不变，看起来几乎没淡化。
- 结论：❌ 推翻。不透明实体上叠透明层无效。
- 回填：`feature-recognition.md` §4；`error-catalog.md` 显示与视觉。

### E-008 · 2026-11-23 · 真半透明（ObjectCulling）
- 假设：把源对象从绘制中剔除，只画自己的子 Brep，才是真玻璃壳。
- 做法：`DisplayConduit.ObjectCulling` → `e.CullObject = true`；锁定面浅灰 0.72 透明画 `PostDrawObjects`，特征面实心橙画 `DrawForeground`。
- 实测：得到真半透明玻璃壳 + 浮出的特征面；特征面放 `PostDrawObjects` 会被深度剔成线框，改 `DrawForeground` 后正常。
- 结论：✅ 成立。v1.3.2 采用。
- 回填：`feature-recognition.md` §4；`error-catalog.md`。
- 遗留：`DrawForeground` 不参与深度剔除，遮挡关系不真实，但视觉上可接受。

### E-009 · 2026-11-23 · 鬼影自愈
- 假设：源对象被 Replace/移动/删后，conduit 缓存的子面索引会失效，出现挪不走的橙灰蒙皮。
- 做法：挂文档事件 + 绘制前几何比对。
- 实测：`RhinoDoc.ReplaceRhinoObject` 等是**静态事件**（`doc.ReplaceRhinoObject +=` 编译 CS0176）；`ReferenceEquals` 比几何不可行（`ObjRef.Brep()` 返回副本）；改用面数 + 包围盒中心漂移 > 2% 的 `Stale()` 判定后自愈成功。多次 `Assembly.Load(byte[])` 会产生多实例，须全部扫描清理。
- 结论：✅ 成立。v1.3.1 采用。
- 回填：`feature-recognition.md` §4；`rhinocommon-pitfalls.md`。

### E-010 · 2026-11-23 · 隐藏对象「被删」误判
- 假设：枚举不到对象就是被插件删了。
- 做法：`ObjectTable` 迭代 / `GetObjectList` 统计。
- 实测：默认**不返回隐藏对象**；加 `ObjectEnumeratorSettings{ HiddenObjects = true }` 后确认 6 个对象完好。
- 结论：❌ 推翻。是枚举设置问题，不是数据丢失。
- 回填：`rhinocommon-pitfalls.md`；`error-catalog.md`。
- 修正 E-003：截图缓存帧必须换相机朝向。

### E-011 · 2026-11-23 · Eto 多选控件
- 假设：`ListBox` 能勾选多个特征通道。
- 做法：查 Rhino 9 的 Eto 控件成员。
- 实测：`ListBox` 无多选；`CheckBoxList.SelectedKeys` 才支持；`Items[i]` 是 `IListItem`，用 `.Key` 匹配。`RhinoGet.GetInteger` 有 bool 参数，漏传编译不过。
- 结论：❌ 推翻。改用 `CheckBoxList`。
- 回填：`rhinocommon-pitfalls.md` Eto 段；`error-catalog.md`。

### E-012 · 2026-11-23 · v1.3.2 分发
- 假设：编译产物能真安装并生效。
- 做法：逐版 yak 打包 → `Yak.exe install` → 核对安装目录。
- 实测：v1.3.0 → 1.3.1 → **1.3.2** 逐版真安装；rhp **88576 bytes / 0 error / 46 warning**；yak 48422 bytes；落到 `…\packages\9.0\特征识别工具\1.3.2.0\`。manifest `description` 里 `v1.3: pick` 的冒号+空格是非法 YAML，改写后通过。
- 结论：✅ 成立。
- 回填：`rhinocommon-pitfalls.md` 打包段；`verification-playbook.md`。
- 遗留：装完必须重开 Rhino 才加载新程序集。

---

### E-013 · 2026-11-23 · 相机/截图/Box 创建的 API 实测
- 假设：`CaptureToBitmap(False)` 可截图；`SetCameraUp(...)` 存在；`ChangeToPerspectiveProjection(True)` 够用；`AddBox` 返回 `Brep`。
- 做法：在真实文档里 `AddBox` 建 10 个立方体，逐一试相机与截图调用，截图后用视觉核对。
- 实测：`CaptureToBitmap` 只接受 `System.Drawing.Size`；`SetCameraUp` 不存在，`CameraUp` 是可写属性；`ChangeToPerspectiveProjection` 只有 `(bool,double)` / `(double,bool,double)`；`AddBox` 返回 **`Extrusion`**（按 Brep 筛得 0 个）；只调 `SetCameraLocation+SetCameraTarget` 会截出**空白帧**，加 `ZoomBoundingBox` 才稳定；沿排列方向看会造成"实际递增、视觉递减"的透视假象。
- 结论：✅ 记录为固定配方（见 pitfalls「相机、截图与 Box 创建」）。
- 回填：`rhinocommon-pitfalls.md`；`error-catalog.md` 已在显示段覆盖缓存帧。
- 遗留：`ObjectColor + ColorSource=ColorFromObject` 在 Shaded 下未生效，疑似材质色覆盖，待验证。

### E-014 · 2026-11-23 · 用户"没有交互界面"的真因：没重启，不是没做
- 假设：用户敲 `FWCancelPanel` 没面板 = 面板没实现 / 注册代码有 bug。
- 做法：只读体检——`AppDomain.GetAssemblies()` 查版本、`Panels.DockBarIdInUse(Guid)` 查注册、磁盘 packages 查安装版本、读源码确认命令与面板存在。
- 实测：磁盘只装了 **1.3.2.0** 一个版本且 rhp 在位；但当前进程 AppDomain 里有 **40+ 个**历史程序集（v1.2 / 1.3.0 / 1.3.1 / v2 全套），**没有 1.3.2**；`FWCancelPanel` 的 `DockBarIdInUse=False`。源码里 `FeatureWorksPlugin.OnLoad()` 明确注册 `FwPanel` + `FwCancelPanel`，`FWSelect`/`FWCancel` 命令齐全。
- 结论：✅ 界面**代码里有**，是本进程没重启导致新版 `OnLoad` 没跑。⚠️ 也说明此前"反射验证面板控件树 PASS"不等于"UI 真的出现"——两者是不同层级的验证。
- 回填：`error-catalog.md` 新增两条（装新版没重启 / 测试程序集污染）。
- 遗留：**待用户在干净重启的 Rhino 里敲 `FWSelect` + `FWCancelPanel` 实测**；这一步只有人能做（无界面槽位驱动不了停靠面板与交互拾取）。
- **修正 E-015**：用户随后重启并截图，报错 `type must have a GuidAttribute (Parameter 'type')`——真因**不是没重启**，而是面板类缺 `[Guid]`。E-014 的"没重启"判断被推翻，保留原文作为判断演化记录。

### E-015 · 2026-11-23 · 面板注册失败真因：缺类级 GuidAttribute
- 假设：面板注册失败是没重启 / 老程序集占位（E-014）。
- 做法：用户重启后截图命令行报错；查 `RhinoCommon.xml` 的 `Panels.RegisterPanel` 文档。
- 实测：报 `type must have a GuidAttribute (Parameter 'type')`；XML 明确写面板类"must have ... a GuidAttribute applied with a unique Id"。源码里 `FwPanel`/`FwCancelPanel` 只有 `public static readonly Guid PanelId` **字段**，没有类级 `[Guid]` 特性。
- 结论：❌ 推翻 E-014。✅ 给两个类加 `[Guid(与PanelId同值)]` 即修复。**关键区分：`static Guid` 字段 ≠ `[Guid]` 类特性**，Rhino 只认后者。
- 回填：`error-catalog.md`「面板注册」条（已加）；`rhinocommon-pitfalls.md` Eto 段。
- 遗留：需真机重启后敲命令确认面板出现（只有人能做）。

### E-016 · 2026-11-23 · 两段式交互（XNurbs 风格自动弹面板）
- 假设：点选物体后让用户再单独敲 `FWCancelPanel` 太绕，应像 XNurbs 辅助面板那样"命令→点选→识别→自动弹面板"。
- 做法：在 `FWSelect` 识别成功后调 `FwCancelPanel.Open()`；面板 `PanelShown` 回调自行 `Refresh` 出两通道清单；外层 try/catch 保证面板打不开不影响聚焦本身。
- 实测：进程内 Roslyn 编译 89088 bytes / 0 error / 46 warning；UTF-16 字节检索确认新提示串与 `1.4.0.0` 进入 rhp；打包 49409 bytes，安装目录 rhp 哈希与编译产物一致（c39ca77ff6418473）。XNurbs 官方页确认其"single simple UI for all kinds of modeling"的辅助面板范式，但具体自动弹出细节无公开源码，按用户描述实现。
- 结论：✅ 实现为 v1.4.0。
- 回填：`README` / `使用手册` 顶部加 v1.4 段落。
- 遗留：真机确认自动弹出时机与面板可用性。

## E-016 · 全网调研 + 只读探活：命令层 Untrim 能力 / 程序集枚举不可作安装判据

**假设**：(a) 上一轮的结论「loop 级手术 RhinoCommon 无现成 API、风险高」成立；
(b)「AppDomain 里没有 FeatureWorks 程序集」可作为「没安装 / 没重启」的判据（E-014 用过）。

**做法**：用户授权全网调研（xNurbs 交互范式 / SW FeatureWorks 流程 / 同类插件 / 显示模式参数 /
Rhino 官方 Untrim 命令族），并做一次真实 Rhino 9 只读探活（程序集枚举 + 面板 `DockBarIdInUse` +
命令枚举 + DisplayMode 枚举 + 源码核对）。

**实测 / 查证**：
- 官方文档 `docs.mcneel.com/rhino/9/help/zh-cn/commands/trim.htm` 明确列有
  `Untrim` / `UntrimAll` / `UntrimBorder`（只去外边界、**保留内部孔**）/ `UntrimHoles`
  （逐孔选边、框选、`全部`、按「最大边缘长度」筛选；菜单「实体 > 洞 > 将洞删除」）。
- `SurfaceIsocurveDensity` 官方值：`-1` 全隐藏 / `0` 边界+knot / `1` 加一条 interior / `>=2` 加 N+1 条；
  NOVEDGE 建议 modest 0–2；暗曲面配浅色结构线；AO 压暗部、高 AO 吃 FPS。
- SW FeatureWorks：Auto / Interactive 双模式；交互模式一次只认一类，顺序
  Fillet→Drafts→Holes→Ribs→Cut→Shell→Boss；`Delete Faces` 记尺寸以便重施加；
  `Select Tangency` 抓整圈相切边；`Recognize similar` / `Combine Features`；
  **父特征（Boss/Base）不可删**；官方忠告 "a workable feature tree, not a perfect feature tree"。
- xNurbs 官网只有 "one simple UI" 与「选曲线/点 → 生成曲面」两段式，**无公开自动弹面板源码**。
- 竞品：CADacombs（`RemoveTrim` / `DeleteFaces` / `MergeAllFaces`，LGPL 开源）、
  TIGER Fillet+（闭式解真实球面/圆柱面圆角 + 滑杆实时预览）。
- 探活：三个 Alias 模式在；两个面板 `inUse=False`；**进程内无任何 FeatureWorks 程序集**；
  `Panels.GetRegisteredPanelIds()` 不存在；`Command.GetCommandNames()` 无 0 参数重载。
- 源码核对：`FwSelectCommand.cs:65` 确有 `FwCancelPanel.Open()`；`FwCancelPanel.cs:33-34` 双
  `CheckBoxList`、`:208 Refresh()`、`:238 PanelShown`、`:242 Register()`、`:257 Open()`。

**结论**：
- **(a) 被推翻**：API 层整面级没错，但**命令层有 loop 级能力**。第 8 节「三路径」第 2 条改写为
  「复用官方 `UntrimHoles` 语义、API 层需搭桥」，不再说「无现成 API」。修正上一轮给用户的建议。
- **(b) 被推翻**：插件可能**按需加载**，「进程里没有程序集」不能推断「没安装 / 没重启」。
  这是对 **E-014 判断方法的第二次修正**（E-015 已修过真因 = 缺类级 `[Guid]`）。
  判安装查磁盘 `…\packages\9.0\<名>\<版本>\`；判面板注册查 `DockBarIdInUse`；别用程序集枚举。
- 定位修正：官方给了完整 Untrim 原语族，缺的是「识别 + 分组 + 回到毛坯」闭环 —— 这正是差异化。

**回填位置**：`feature-recognition.md` 第 8 节三路径；`rhinocommon-pitfalls.md` 新增只读探活段；
工作区新增 `FeatureWorks/INTERACTION_SPEC.md`（术语对照 / v1.5 规格 / 显示参数 / 验收清单 / 出处）。
**遗留**：v1.4 自动弹面板仍需用户重开 Rhino 实机验收；本轮未改插件代码、未动显示模式、未推 GitHub。

## E-017 · 2026-11-23 · 原理追问：FeatureWorks 的「重新识别」是不是按方法约束反推

**假设**：用户提出 SW FeatureWorks 无历史仍能重新识别，机制是「大致猜 + 交互只给大致种类 +
实现方法就那几种 → 按方法约束反向推导」。需核实是否成立、有无正式名称，以及第 8 节
「不适定 → 机器只能给候选」是否表述过粗。

**做法**：全网精准检索（SW 官方帮助 2025 / GoEngineer / CATI / Mechanitec 教程 +
Cardiff ORCA 综述 §2.4.3 / Wikipedia Feature recognition / ScienceDirect 混合图+规则法综述），
与专题第 8 节、`INTERACTION_SPEC.md` §2 交叉比对。**纯概念调研**：未改插件代码、未连 Rhino、未推 GitHub。

**证据**：
- 官方自动识别界面第一项 = 勾选**有限特征类型清单**（Extrudes / Drafts / Revolves / Holes /
  Fillets-Chamfers / Ribs / Volume / Sheet Metal）；Intermediate Stage 有 `Re-Recognize as alternate features`。
- 学术名称 **hint-based / evidence-based / trace-based**（Vandenbrande & Requicha 1993），
  流程 generate-and-test：hint 生成 → 补全 → 验证；hint = 特征边界不可或缺的最小残留；
  基于 feature presence rules，且**规则是 feature-type specific**（一类一套）。
- 识别过的特征**退出后续计算**；顺序为建模逆序
  `Fillet/Chamfer（尺寸递增）→ Drafts → Holes → Ribs → Cut → Shell → Boss`。
- SW 原生零件**有** FeatureManager 历史树；FeatureWorks 专用于导入的 dumb solid，
  输出 *rudimentary feature history* / *workable tree, not perfect tree*。
- 综述：graph-based 在特征相交时丢弧；3D / freeform 特征识别至今困难；真实工业零件数百面
  会让多数方法停机。

**结论**：✅ 用户猜想成立，且比「猜」更精确 —— 是**有限方法库上的受约束反向推断**。
⚠️ 精化第 8 节：不适定 = 同一结果对应多个合法假设，**不等于无约束乱猜**；假设空间封闭可枚举，
所以工程解法是模板匹配 + 置信度排序 + 多解交人裁决。这从原理上解释了「使用感差的结构性成分」
与「为何交互必须存在」。同时修正「它没有记录」：输入无历史，它重建一个粗糙的。

**回填**：`feature-recognition.md` 新增第 9 节；`INTERACTION_SPEC.md` 新增 §2.1 原理与六条落地决策；
`MEMORY.md` 核心愿景条目补原理精度；专题第 8 节不删改（保留判断演化）。

**遗留**：v1.5 实现时把「显式方法库表 + 置信度/依据 + 逆序剥离」落进 Core；仍等用户重开 Rhino
敲 `FWSelect` 验收 v1.4 自动弹面板，通过后再编码。

## E-018 · 2026-11-23 · 扒官网命令体系：全量 1256 条 + 官方原文，纠正「命令文档=原理」

**假设**：用户提出把 Rhino 官网所有指令与用法扒下来整理成文档、我学习一遍，做插件会方便很多
（「懂了原理、构造之后再去实现」）。需核实：(a) 官网是否有全量索引可扒；(b) 全量整理是否真省事；
(c) 命令文档是否等于内核原理。

**做法**：反射确认 `Command.GetCommandNames(bool english, bool loaded)` 签名；从运行中的
Rhino 9.1.26314.9001 导出 `loaded=True` 1052 / `loaded=False` **1256** 条到 `_tmp/rhino_commands_all.txt`。
官网探活：`index.htm` 200 但仅 1225B 跳转页、`commands/` 目录 403、单命令页需浏览器 UA 才 200；
`zh-cn`/`zh-tw` 中文版存在；`Untrim` 等是 `trim.htm` 锚点；`seealso/sak_*.htm` 是主题分类页。
批量下载 51 页、34 页提取出有效正文。本机检查：无完整离线命令手册（仅 RhinoScript.chm /
RhinoIronPython.chm），`Content/XML/<lang>/` 是模板与材质资源，不是命令文档。

**实测/证据**：
- `Brep` 关键词在 1256 条里命中 **0**；无任何特征识别 / 取消特征类命令 → 命令层不解释内核。
- `SetObjectDisplayMode` 官方 *"Their display in other viewports won't be affected"* → 逐视口独立是官方行为，
  Alias 全视图联动必须自己遍历视口。
- `FilletEdge` 官方 *"creates a tangent surface ... then trims and joins the original faces"* → 官方背书第 8 节
  「倒角 = 新增过渡面 + 原面裁小」；`ChainEdges` / 双击相切边印证「整圈一起删」。
- `DeleteFaces` 官方支持 **Polysurface** + face loop（单击→双击定方向、Ctrl 剔单面/整圈、sub-object filter）
  → 圆角整圈选取可直接复用官方语义。
- `History` 官方 = 输入几何↔结果的连接（construction history），不存操作意图 → **不是 SW 特征树**。
- `MakeHole` / `Trim` / `ShrinkTrimmedSrf` / `CreateSolid` 官方原文分别与内环、两层结构、重缝一一对应。
- 命令名表含 `FW2Panel`（已降级 v2、当前未加载）→ **命令名存在 ≠ 插件已加载 / 面板已注册**，与 E-016 同类。

**结论**：✅ 整理命令体系确实省试错（E-016 漏看 `UntrimHoles` 就是反例），但
❌ **命令文档 ≠ 内核原理**；真正提速靠「命令 ↔ RhinoCommon API ↔ B-rep 几何」三层对照。
⚠️ 全量 1256 条平铺会稀释检索 → 拆成「全量索引（只查）+ 精讲（才读）」才符合省 token。

**回填**：新增 `references/rhino-command-index.md`（1256 条、17 域 + 26 字母组、680 行）、
`references/rhino-command-reference.md`（精讲 + 9 条官方原文 + 6 条 v1.5 决策 + 检索纪律）、
`scripts/Export_Rhino_Commands.py`（可移植导出脚本）；`SKILL.md` 加第 8 步与参考清单。
`INTERACTION_SPEC.md` 未改。

**遗留**：未逐页扒全部 1256 个帮助页（官网无全量索引、多数为别名/锚点，无收益）；
34 页原文只留要点与缓存路径，未全文入库。v1.5 编码仍等 B 线面板验收。

## E-019 · Grasshopper：搭通 ≠ 有效，GH 只预览不落地（2026-11-23）

**假设**（三条都要被检验）：
1. 「求解器报 `solved=true`、0 报错 → 定义是对的」
2. 「GH 视口里看得到 → 文档里有几何」
3. 「要在活画布上搭定义，只能靠手点」

**做法**：
- 用 `g1_apply_graph` 在活画布搭「渐变立方体阵列」：滑块 + 8 组件 + 连线，一次提交
- 用 `g1_get_canvas_graph(include_data=true)` 逐输出核对 item 数与抽样值
- 平行投影正视图截图 + `doc.Objects.Count` 对照

**实测**：
- 第一版 **13 对象 / 17 连线**，`solved=true` / `reported=0` / 0 warning；
  但 `Series.Start` 漏接、默认 **0** → 序列 `0…9`，边长 `0,4,…,36`，
  `Center Box` 第 1 项 = **`Singular Box`**（尺寸为 0 的退化盒）
- 修正版 **14 对象 / 18 连线**：Series `1…10`、半径 `2…20`、边长 `4…40`、
  X `45…450`、点 `{45,0,2}`、Box 10 项全为 `Box`（无 Singular）
- **`doc.Objects.Count = 0`**（视口 10 个盒子，文档 0 实体）
- 组件库 `ObjectProxies` = **2336 个 / 29 类**（GH 核心 1344 + Kangaroo2 120 + 第三方 872）
- 工具链 `g1_*` 全套可用（search / describe / place / place_slider / connect / connect_many /
  solve / get_canvas_graph / clear_canvas / apply_graph），GH2 另有 `g2_*` 一套

**结论**：
- ✅ 推翻假设 1：`solved=true` 只表示没抛异常，**不校验几何有效性** → 必须读数据 + 看几何
- ✅ 推翻假设 2：GH 只画 preview，`Objects.Count=0` 是正常行为，不是失败
- ✅ 推翻假设 3：`g1_*` 可编程搭定义、求解、读回，无需手点
- ⚠️ 工具 schema 不统一：`g1_place_slider` 的 `min/value/max` 要求 object，
  而 `g1_apply_graph.sliders[]` 收数字 → **优先用批量路径**，别跟单接口绕
- ⚠️ GH 给的是「你亲手写下的历史」，不是从结果反推的历史 → 不能替代 FeatureWorks
  （见 `feature-recognition.md` §8 / §9）

**回填**：
- 新增 `references/grasshopper-spatial-logic.md`（三层对照 / Item-List-Tree / 匹配规则 /
  四步构造序列 / 坑位清单 / 何时 GH vs C#）
- 新增 `references/grasshopper-component-index.md`（2336 组件、29 类）
- 新增 `scripts/Export_GH_Components.py`（可移植导出）
- `SKILL.md`：description + 何时使用 + **第 9 步「参数化与演示纪律」** + 决策表 4 行 + 参考清单
- 仓库新增 `design-lab/`（协作载体：README + 001-gradient-boxes.md + 截图）

**遗留**：
- `place_slider` 的 object 参数正确形状未查明（选择了绕过）
- GH2（`g2_*`）未实测，两代 API 差异待对比
- 未验证「拖滑块 → 结果实时变」，未找到 set_slider_value 一类接口
- 001 条目的 6 项改进未做（X 从 0 起、累加间距、Bake、.gh 存档、GH2 版）

## E-020 · 面板"未注册"是误判：`DockBarIdInUse` 不是注册判据（2026-11-23）

**修正 E-014 / E-015**：那两条都用 `Panels.DockBarIdInUse(guid) == False` 判定"面板没注册"，**判据本身是错的**。

**假设**：`DockBarIdInUse(g) == False` → 面板未注册

**做法**：主动 `PlugIn.LoadPlugIn(guid)` → 查程序集 / 命令 / 面板；
再用 `Panels.GetOpenPanelIds()` 与 `Panels.IsPanelVisible(g)` 复核

**实测**：
- 用户重开后：FW 程序集 `(none)`；118 个已加载插件里无 FeatureWorks；
  注册表 `HKCU\…\Rhinoceros\9.0\Plug-ins\6d1f8a3c-…` = 「特征识别工具 / RhinoFeatureWorks」，`LoadMode=2`
- `PlugIn.LoadPlugIn(Guid("6D1F8A3C-2E47-4B95-A0D6-9C3E7F1B2D48"))` → **True**
- 加载后：`RhinoFeatureWorks v1.4.0.0`；**16 个 `FW*` 命令**全部注册
  （FWSelect / FWCancel / FWCancelPanel / FWPanel / FWFocus / FWRecognize / FWRepair…）
- `Panels.OpenPanel(g)` 无异常；`GetOpenPanelIds()` **包含**
  `b4d8e21a-…`（FWCancelPanel）与 `7a4e1c93-…`（FwPanel）；`IsPanelVisible(g)` 两者均 **True**
- 而 `DockBarIdInUse(g)` 全程 **False**

**结论**：
- ✅ 推翻判据：`DockBarIdInUse` ≈「是否已停靠为 dock bar」，**不能用作注册/可用判据**
- ✅ 正确判据：`GetOpenPanelIds()` 含该 guid，或 `IsPanelVisible(g)` 为 True
- ✅ **v1.4 面板是好的**。用户"没界面"的真因是**插件从未被加载**：
  `LoadMode=2`（按需加载）+ 命令未注册 → 敲任何命令都触发不了加载 → **死锁**
- ✅ 可编程解决：`PlugIn.LoadPlugIn(guid)` 主动加载，**无需重开 Rhino**

**回填**：`error-catalog.md` 改写"没有交互界面"那条并新增"DockBarIdInUse=False"一条；
`MEMORY.md` 硬约束第 2 条补主动加载与正确判据；`SKILL.md` 决策表加对应行。

**遗留**：
- 根治是把插件设为**启动加载**（`LoadMode=1`），需改注册表/插件设置后重启，未做
- 面板已打开但非停靠状态（`DockBarIdInUse=False` 与之自洽）
- **面板内控件交互（勾选→取消→回毛坯）仍未实测**，需用户点一次

## E-021 · 全视图联动：不是命令的锅，是 Rhino 的模型（2026-11-23）

**假设**：`AliasStyleLight`（菜单 `I`）只把**活动视口**切成了 Alias EyeCare，其余视口没跟着变。

**做法**：
1. 真机读回 4 个视口的当前模式（`doc.Views` → `ActiveViewport.DisplayMode.EnglishName`）
2. 反射确认 `DisplayPipeline.DisplayModeChanged` 是否静态事件
3. Python 订阅该事件 + 手写与插件等价的同步逻辑：把 Top 切到 `Shaded`，看其余是否跟随
4. 插件侧实现 `AliasStyleLink`（`Interlocked` 闸门 + Id 比对 + Mute 引用计数），
   编译 → 打包 → `Yak.exe install` 真安装 → 反射 + 真机双验

**实测数字**：
- **改前四视口本来就全一致**：
  `Perspective=Alias EyeCare | Top=Alias EyeCare | Front=Alias EyeCare | Right=Alias EyeCare`
  → 命令没坏，`Apply` 本来就 `foreach (RhinoView v in doc.Views)`
- `DisplayPipeline.DisplayModeChanged`：`GetAddMethod().IsStatic = **True**`（静态事件，可全局监听）；
  同一脚本内改两次 `vp.DisplayMode` → 同步回调 **2** 次，`args.Viewport` 精确指向被改视口
- 联动后：`Perspective=Shaded | Top=Shaded | Front=Shaded | Right=Shaded`
- 回调序列 `['blocked','blocked','blocked', 3]`：三次递归被闸门挡住，一次真同步了 3 个视口
- 还原后四视口全部回 `Alias EyeCare`
- v2.9 rhp **55296 B / 0 error / 23 warning**；yak **55952 B**；sha256 rhp `7454e87d…`
- 运行中实例仍是 2.8.0.0（`packages\9.0\基准面工具\2.8.0.0\`）；2.9.0.0 已落到隔壁目录

**结论**：
- ✅ 推翻假设：这不是命令 bug，是 **Rhino 一视口一 DisplayMode** 的原生模型；
  标题栏下拉 / 视图菜单 / `_SetDisplayMode` 都只作用当前视口（Alias 才是"全画布一套"）
- ✅ 联动可**纯事件驱动**，不需要轮询、不需要 UI 钩子
- ✅ 三个必守点：防重入闸门、先比 Id 再设（天然收敛）、**程序化批量改模式必须 Mute**
  （否则 `Restore` 要恢复的各不相同模式会被互相同步回去，还原直接失效）
- ⚠️ 踩到环境坑：装了 WeaverBird 后 `Action` 在 `WeaverBird.Core` 与 CoreLib 双定义，
  **连 `System.Action` 都 CS0433** → 把 `TrySilent(() => {})` 内联成 try/catch 解决
- ⚠️ `PersistentSettings.GetBool/SetBool` 是**实例方法**，静态调用 CS0120 → 用 `PlugIn.Settings`

**回填**：`display-modes.md` 新增「全视图联动（Alias 式）」；
`error-catalog.md`「编译与加载」+2 行、「显示与视觉」+2 行；
`rhinocommon-pitfalls.md` 记事件与 Settings 签名；`INDEX.md` §1 加入口；`MEMORY.md` 升 2.9。

**遗留**：
- 用户**用手点视口标题栏下拉**再验一次（脚本路径已通，UI 路径应同源，但未亲测）
- 布局页（Layout）detail 视窗不在 `doc.Views`，不同步 —— 已知边界
- 2.9 需重启 Rhino 才加载（当前进程是 2.8）

## 统计与复用提示

- 截至 2026-11-23：**22 条实验**，其中 **11 条推翻了初始假设**（E-015 推翻 E-014 真因，
  E-016 再推翻 E-014 的判断方法与 E-015 附带结论，E-019 推翻「solved=true 即成功」，
  **E-020 推翻 E-014 的"面板未注册"判据**，**E-021 推翻"命令只改了一个视口"的猜想**）。
  E-017 / E-018 为概念与资料精化，不计推翻，同样保留判断演化。高推翻率说明「先验证再相信」不是口号。
- 编号提示：台账历史上有两条 E-016（一条 `###` 一条 `##`），不作改动，新实验顺延编号。
- 查坑顺序：`error-catalog.md`（按症状）→ 本台账（按实验编号，看结论演化）→ 专题文档（按领域）。
- 新实验编号顺延；若结论修正旧条目，在本条写「修正 E-XXX」并在旧条补一行指向，不删改旧记录。
