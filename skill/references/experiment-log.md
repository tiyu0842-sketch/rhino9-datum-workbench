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

> **修正 E-022（同日稍晚）**：本条技术实测全部成立（事件静态、可同步、防重入数字都对），
> 但**需求方向判断错误** —— 用户要的是「各视口独立」，联动应默认关闭。
> v2.10 已把 `Apply` 改为只写活动视口、联动降级为可选项。读本条时请连 E-022 一起看。

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

## E-022 · 方向做反了：用户要的是「各视口独立」（2026-11-23 晚，修正 E-021）

**背景**：E-021 把用户的「我只改变我在编辑的那个窗口，而不是所有的窗口一起变成那个模式」
读成"我要联动，你没做"，于是做了事件驱动同步并**默认开启**。用户当场纠正：
「其实我是不想让他跟着变动，只是更改我操作的那个窗口」。

**假设（更正后的）**：用户要的是**每个视口独立**；"四个窗口一起变"的根因在插件自己的 `Apply`
（`foreach (RhinoView v in doc.Views) v.ActiveViewport.DisplayMode = mode`），不是 Rhino 的行为。

**做法**：
1. 真机只对 `doc.Views.ActiveView` 写 `DisplayMode`（**不挂任何事件**），读回四视口验证是否连锁
2. v2.10 改 `Apply`：只写活动视口；新增 `Touched`（`doc.Strings`）记录改过哪些视口
3. `Restore` 只还原 `Touched` 名单内视口（名单为空才退回全量，兼容旧文档）
4. 联动降级：设置键改 `DatumPlane.AliasStyle.LinkAllViews.v2`、默认 `false`
5. 编译 → yak → 真安装 → 哈希核对

**实测数字**：
- 只写 `Perspective` 后：`Perspective=Wireframe | Top=Alias EyeCare | Front=Alias EyeCare | Right=Alias EyeCare`
- 0.3s 后复读：**仍只有 Perspective 变** → 无事件钩子时不存在连锁，证明 v2.10 方案可行
- `doc.Views.ActiveView = Perspective`（当前光标所在视口）
- v2.10 rhp **56320 B / 0 error / 23 warning**；yak **57575 B**；
  sha256 rhp `a4e6a168…`、yak `7d792912…`；已真安装到 `packages\9.0\基准面工具\2.10.0.0\`（哈希一致）
- 运行中实例仍是 **2.8.0.0**（`PlugIn.Find(guid).GetType().Assembly` 读回，且无 `AliasStyleLink` 类型）

**结论**：
- ✅ 推翻 E-021 的**需求判断**（不是推翻其技术实测）：联动事件机制本身是真的、可用的，
  但**默认不应开启**，用户要的是独立
- ✅ 需求方向口诀：句子主语是"我操作的那个窗口" → 独立；"所有窗口一起变" → 联动。
  拿不准就问，别赌
- ⚠️ **改默认值必须换键名**：旧键已被写成 `true`，`GetBool(key, false)` 仍读回 `true` ——
  换 `.v2` 后缀才真正生效，否则用户升级后会说"你根本没改"
- ⚠️ 只改部分视口后，全量 `Restore` 会顺手抹掉用户手动切过的视口 → 必须有 `Touched` 名单
- ⚠️ `WireDensity` 是对象级属性，无法按视口分开，要在文档里主动声明这是边界

**回填**：`display-modes.md` 新增「视口作用范围：默认只改当前视口」并重写联动节（标为可选、默认关）；
`error-catalog.md`「显示与视觉」+2 行；`INDEX.md` 症状表加"四个视口一起变"；`MEMORY.md` 升 2.10。

**遗留**：
- 用户重启后实机点菜单 `I` / `M` 确认（进程当前仍 2.8）
- 布局页 detail 不参与

## E-023 · FeatureWorks 面板重做：可辨识性 > 算法复杂度（2026-11-23 晚）

**用户原话**：「你不觉得这个界面的交互很麻烦嘛……为什么我不能去选择那个边缘？
我去选择边缘，然后取消它的特征不更好吗？……这一个一个 flat，我都不知道这是哪个跟哪个」
并明确要「勾选保留全部，还是将选择的删除」。

**假设**：问题不在识别算法，而在**识别结果没有可辨识映射** + **破坏性操作用了隐式默认**。
本轮不动算法、只重做交互层。

**做法**：
1. 反射核实 Eto / Rhino API（不凭印象写）：
   - `Eto.Forms.CheckBoxList`：有 `Orientation`、`SelectedKeys`（可读可写）、
     `SelectedKeysChanged`、`MouseDoubleClick`，**没有 SelectedIndex**；
   - `BrepFace.AdjacentEdges()` → `Int32[]`（边→面反查的关键）；
   - `Rhino.Geometry.ComponentIndexType.BrepFace / BrepEdge`；
   - `RhinoViewport.ZoomBoundingBox(BoundingBox)`；
   - `DisplayPipeline.Draw2dText(string, Color, Point3d, middleJustified, height, fontface)`。
2. `FwFocusGroup` 加稳定 Id（F1…/H1…）；`FwFocusConduit` 加 `FeatureVisuals` +
   `FocusedIndex`，逐组画编号标签，命中组青色粗线、其余压暗。
3. 新增 `FWPickFeature` 命令：`GetObject{SubObjectSelect=true}` → 面直接查组、边用
   `AdjacentEdges()` 反查 → `FwFocusSession.PickGroup` 通知面板勾选（自定义委托，避开 Action 冲突）。
4. 面板改成纵向编号列表 + 三个显式动作：`取消选中 N 项`（N=0 拒绝）、`保留全部`、`全部取消`。
5. 编译 → 反射 → yak → 真安装 → 哈希核对。

**实测数字**：
- 首编译 4 error：`RhinoView` 在 `Rhino.Display` 不是 `Rhino.DocObjects` → 补 using 后
  **96256 B / 0 error / 49 warning**（其余是既有 CS8603/CS0618/CS1701 噪声）
- 反射：程序集 1.5.0.0；`FwPickFeatureCommand` 存在；
  `FwFocusSession` 含 `GroupAt / FindGroupByEdge / PickGroup / SetFocus`
- yak **62259 B**，sha256 `44664b48…`；rhp sha256 `a03c0624…`，真安装
  `packages\9.0\特征识别工具\1.5.0.0\` 哈希一致
- **运行实例仍 1.4.0.0**（`has FwPickFeatureCommand: False`），需重开 Rhino

**结论**：
- ✅ 推翻「文字列表 + 勾选就够了」的设计假设：**可辨识性先于算法 sophistication**。
  用户要的是「能指认」而不是「更多特征类型」。
- ✅ 选中必须 ≠ 执行。视口点边只打勾；改模型要点显式按钮，且空勾选不执行。
  旧版「不勾=全部取消」是隐式破坏性默认。
- ✅ 交互 API 必须先反射：CheckBoxList 没有 SelectedIndex、RhinoView 在 Display 命名空间、
  `AdjacentEdges()` 返回 int[] —— 凭印象写会连续 4 个编译错误。
- ⚠️ 打包脚本会覆盖人工维护的 README/manifest（重写成 v1.0 模板）—— 已改成只在缺失时生成。
- ⚠️ 交互命令无法脚本同步驱动，`FWPickFeature` 的“点边→勾选”仍需用户实机点验。

**回填**：`INTERACTION_SPEC.md` §10；`feature-recognition.md` §10 + 版本线；
`error-catalog.md` 交互命令 +4 行；`INDEX.md` 症状表；`README.md` / `使用手册.md` v1.5 段落；
`MEMORY.md` 特征工具版本升 1.5。

## E-024 · 三个交互质疑的几何真相：去布尔不必先去圆角（2026-11-23 晚，v1.5 之后）

**用户原话（三点）**：①「为什么选择那个框之后，只能在那个框里面去选择？我为什么不能在原有界面上，
通过鼠标去框选那个物体上面已经标红的了？」②「可以把它分成两个模块，一个单独去除圆角，另一个去除布尔；
去除布尔是不是必须先通过去完圆角才能去，或者说有没有办法可以去？」③「有些地方我可以取消修剪然后还原，
你为什么不直接让那个面去取消修剪，而是直接去补那个面？」并定调「两边可以同时相互交互，而不是说去选择
那一边」「整体交互逻辑不清晰」，要求参考主流 CAD 界面布局。

**假设**：三个都是**实现选错 API / 交互架构**造成的，不是 Rhino 的限制。特别要验证
「去布尔必须先去圆角」是否成立 —— 记忆与旧注释都把它当成几何事实。

**做法**（Rhino 9.1.26314，纯内存 Brep，不动用户文档）：
1. 反射 `Brep` / `BrepFace` 全部 Untrim / Hole / Loop 方法 + 读 RhinoCommon.xml 官方 summary；
2. 官网抓 `trim.htm#UntrimHoles` 原文；抓 vcad `Selection` 的 Feature Tree Sync 定义；
3. 四组纯几何实验（盒+2 孔、圆角盒+1 孔）；
4. 反射常驻交互钩子可行性。

**实测数字**：

| 输入 | 操作 | 结果 |
|---|---|---|
| 盒+2 孔 8 面 / loops 12 / inner 4 / vol 228973.01 | `UntrimFace(host=4)` ← **当前实现** | **6 面 / inner 0 / vol 240000**：两个孔一起没了 |
| 同上 | `RemoveHoles([loop 7], tol)` | **7 面 / inner 2 / vol 232365.93**：只删 1 个孔，另一孔+外环全留 |
| 同上 | `RemoveHoles(tol)` | 6 面 / inner 0 / 240000 |
| 同上 | `UntrimOuterLoop(host)` | **NULL** |
| 圆角盒 R3 10 面 / 239315.06 | `CreateFilletEdges` 造 | solid=True |
| 圆角盒 + 1 孔 11 面 / inner 2 / 235922.14 | `RemoveHoles(该孔 2 个内环)` | **10 面 / inner 0 / 239315.06 = 纯圆角盒，圆角完好** |
| 同上 | `UntrimOuterLoop(圆角面)` | **NULL** |
| 同上 | `UntrimFace(host)` | 10 面 / 239315.06（孔没了，圆角还在） |

**官方原文（RhinoCommon.xml，权威）**：
- `Brep.RemoveHoles(IEnumerable<ComponentIndex>, double)` since 6.8：
  「Removes inner loops, or holes, in a Brep」，参数须为 `BrepLoop.LoopType == Inner` 的 loop 索引。
- `Brep.RemoveHoles(double)` since 6.0：Remove all inner loops。
- `Brep.UntrimFace(int,double)` since 9.0：「outer boundary is untrimmed **and all inner loops (holes) are removed**」。
- `Brep.UntrimOuterLoop(int)` since 9.0：「only untrimmed when **all of its edges are naked**; otherwise the operation
  fails to avoid corrupting adjacent faces」「Inner loops (holes) are left in place」。
- 命令层 `UntrimHoles`：「Select hole edges individually. **Or use window selection**」，
  支持 `All` / `MaximumEdgeLength` / `KeepTrimObjects`；`UntrimBorder`：「Interior trims (holes) will remain」。
- SolidWorks FeatureWorks 交互模式：「Under *Selected entities*, **select geometry from the graphics area**」，
  「You do not have to select every face of a feature」，有 `Chain fillet faces` / `Recognize similar`。
- vcad `Selection`：*Feature Tree Sync* ——「Selection state is synchronized between the viewport and the feature
  tree panel」「**Multi-selection works in both directions**」，另有 Hover Preview、Shift 加减选、点空白清空。

**结论**：
- ✅ **推翻「去布尔必须先去圆角」**：`RemoveHoles(指定内环)` 只删选中的孔，外环、圆角、其它孔全部保留
  （11→10 面，235922.14→239315.06）。用户观察到的顺序依赖，其实是**当前实现用错 API**：
  孔洞通道用 `UntrimFace`（把整个宿主面外环+全部内环一起抹），圆角通道用 `Defillet`
  （把所有剩余面外扩成完整平面再 `CreateSolid`）→ **去圆角会连带把孔一起抹平**，方向正好相反。
- ✅ **推翻 `rhinocommon-pitfalls.md` 旧结论「API 层只有整面级 Brep.UntrimFace」**（E-018 遗留）：
  loop 级精度官方就有，就是 `RemoveHoles(IEnumerable<ComponentIndex>, tol)`，且 since 6.8。
  这条是本次最大收获 —— 以后不用再「在 Core 层按 inner loop 搭桥」或 `RunScript` 调命令。
- ✅ **为什么圆角要「补面」而孔可以「取消修剪」**：孔 = 底层曲面 + trim 内环，抹环即还原；
  圆角 = 滚球扫出的**新增过渡曲面**，四边与邻面共享，没有「更大的底层曲面」可还原，
  `UntrimOuterLoop` 因外环边非 naked 恒返回 null。所以圆角只能删整圈过渡面 + 让相邻面重新求交。
  「补面」不是偷懒，但当前 `Defillet` 把**所有**非圆角面都换成完整平面，是把孔一起抹掉的元凶。
- ✅ **「只能在框里选」的技术根因**：`FwFocusConduit.ObjectCulling` 把源对象从绘制里剔除，
  视口里橙色面是 conduit 画的「影子」，不是文档对象 → Rhino 原生拾取/框选碰不到它；
  且 `FWPickFeature` 是一次性 `Get()` 模态命令，选完即退出；面板还写死「同一时刻只允许一边有勾选」。
- ✅ **常驻双向联动可行**（已反射确认存在）：`Rhino.UI.MouseCallback`
  （`OnMouseDown` / `OnEndMouseDown` / `OnMouseMove` / `OnMouseHover` / `Enabled`）、
  `RhinoDoc.SelectObjects` **静态事件**、`GetObject.GetMultiple(int,int)` + `SubObjectSelect` + `GroupSelect`。
- ⚠️ **进程崩溃（如实记录）**：最后一组实验把 `DuplicateSubBrep(剩余面)` 与 `UntrimOuterLoop` 连调，
  Rhino slot `armadillo` (pid 4396) 中途崩溃、槽被回收。**按纪律不盲目重试**，该路径列为待验证开放项；
  前 4 组数字均在同一进程内干净取得，结论不受影响。
- ⚠️ **未完成**：`UntrimBorder` 命令层「去外环保留内环」能否替代 `Defillet`（避免补面）尚未验证；
  常驻 MouseCallback 选择尚未编码；v1.6 交互方案待用户拍板。

**回填**：`feature-recognition.md` §11；`rhinocommon-pitfalls.md` 修正 + 新增 4 条；
`rhino-command-reference.md` UntrimHoles 官方原文；`error-catalog.md` 交互/崩溃 2 组；
`INDEX.md` 症状表与计数；`SKILL.md` 决策表；项目 `INTERACTION_SPEC.md` §11；今日日志与 MEMORY。

## E-025 — v1.6 常驻双向联动 + 严格两独立模块（实现与真机几何验证）

**假设**：用户三问（「只能在那个框里选」「去布尔是不是必须先去完圆角」「为什么不 untrim 而补面」）
可以在**不污染文档、不建临时对象**的前提下一起解决：
常驻 `MouseCallback` 接管左键 + 一份共享选中集 + 两个独立执行器
（模块 B 走 `RemoveHoles(指定内环)`，模块 A 走整圈重缝并明确报出连带影响）。
用户拍板：「按方案全做」「严格两模块、不要总开关」「明确报出，不偷偷改」。

**做法**：
- 新增 `FwSelection.cs`：`FwSelectionState`（一份 `HashSet<int>`，视口/面板/两模块共同读写）
  + `FwMouseWatcher : MouseCallback`（`OnMouseDown/Move/Up/Leave`，`e.Cancel=true` 接管左键，
  `WorldToClient` 把每组世界包围盒 8 角投影成屏幕矩形做点选/拖框命中，Shift/Ctrl 加减选）。
- `FwFocusGroup.Loops` 存 inner loop 索引（`BrepLoop.LoopIndex`），
  `FindInnerLoops()` 用 `BrepTrim.Edge.AdjacentFaces()` 把孔洞组映射到内环；
  `FwGroupVisual.Bounds` 供框选投影；conduit 三态着色 + 拖框矩形。
- `FwCancel.cs` 重写：`CancelBoolean` / `CancelFilletModule` / `TryApply(doc, module, targets, out msg)`，
  严格两模块、拒绝跨模块混选、删掉「全部取消 → 回毛坯」总开关。
- 面板删互斥勾选、两个分区各一个执行按钮，订阅 `FwSelectionState.Changed` 双向同步。

**实测数字**：

| 项目 | 数字 |
|---|---|
| 进程内 Roslyn | 首轮 **16 error 全为 CS0104**（`Point` / `Environment` 在 `System.Drawing`·`System` 与 `Rhino.*` 双定义）→ 加 `using Point = System.Drawing.Point;` + `System.Environment.NewLine` → **0 error，rhp 103424 bytes**（v1.5 96256） |
| 反射断言 | 版本 `1.6.0.0`；12 个类型齐全；`CancelBoolean(Brep, IList<FwFocusGroup>, Double)`、`CancelFilletModule(..., IList<FwFocusGroup>, Double)`、`TryApply(RhinoDoc, String, List<FwFocusGroup>, String ByRef)`；`MouseCallback.Enabled` 继承存在 |
| 盒+2孔 `8 面 / inner 4 / vol 233214.16` | `FindInnerLoops`：H1 → `[7,8]`、H2 → `[10,11]`；4 个圆角组 → 空 |
| 模块 B 只删 H1 | **`7 面 / inner 2 / vol 236607.08`**（H2 与其它几何全留） |
| 模块 B 删两个孔 | `6 面 / inner 0 / vol 240000` |
| 跨模块混选（`Channel="Fillet"` 塞进布尔执行器） | 明确拒绝，`No inner loops resolved`（严格两模块生效） |
| 圆角盒 R3 `10 面 / 239315.06` + 1 孔 `11 面 / inner 2 / 235922.14` | 识别 4 个 Fillet 组（`Loops` 空）+ 1 个 Hole 组（`Loops=[11,12]`） |
| 模块 B 只删该孔 | **`10 面 / inner 0 / vol 239315.06`，`SAME_AS_FILLETED=True`** —— 圆角完好，去布尔不需要先去圆角 |
| 模块 A 重缝（连带孔） | `collateral=4`，结果消息原文含「【明确报出 / NOT silent】」，未做孔体重放 |
| 打包 / 真安装 | yak `73265 bytes` sha256 `367973bb…`；安装目录 rhp `103424 bytes` sha256 `e3ff9710…` 与本地一致，manifest `1.6.0.0` |

**结论**：
- ✅ 用户三问在同一版里一起落地；`RemoveHoles` 的 loop 级精度让两模块**真正解耦、任意顺序**，
  圆角盒证据（11→10 面 / 235922.14→239315.06）是最直接的反证。
- ✅ 「只能在框里选」的根因是 conduit 自绘面不是文档对象；接管左键 + 屏幕投影命中测试后，
  不建文档对象也能在原有视口框选（E-024 的诊断被实现验证）。
- ✅ **发现并修复一个真实实现 bug**：`CancelBoolean` 初版用 `g.Type == FeatureType.Fillet` 过滤，
  而 `FeatureType` 枚举**默认值恰好是 Fillet**，孔洞组被误判成圆角 → `RemoveHoles` 收不到任何内环
  （纯几何验证第一轮 `B_only_H1 ok=False` 抓到）。改为只认显式 `g.Channel`，runner 同步改，
  重编译后第二轮全部通过。**教训：判断模块归属别用带默认值的枚举，用显式字符串标记。**
- ✅ `Brep.RemoveHoles(IEnumerable<ComponentIndex>, double)` 返回 **Brep**（成功返回去孔后的新 Brep，
  失败 null），不是 bool —— 写 Core 前先读 XML 的 `<returns>`，别凭方法名猜。
- ⚠️ 常驻 `MouseCallback` 的真实 GUI 手感（拖框矩形、hover、多视口、`e.Cancel=true` 对右键/gumball 的影响）
  **尚未实机点过**：本轮 Rhino 是 E-024 崩溃后自动重开的空文档实例，交互命令按纪律不从脚本同步驱动。

**回填**：`feature-recognition.md` §12；`rhinocommon-pitfalls.md`（RemoveHoles 返回值 / LoopIndex / MouseCallback / CS0104 / 枚举默认值）；
`error-catalog.md`（3 组新症状）；`INDEX.md` 计数与入口；`SKILL.md` 决策表；
项目 `INTERACTION_SPEC.md` §12、README、使用手册、manifest、AssemblyInfo、编译/打包脚本；
今日日志与 MEMORY；GitHub 仓库副本本地提交。

**遗留**：GUI 实机验收（需用户重开 Rhino）；`turn number` 所指未确认；
`UntrimBorder` 能否替代 Defillet 仍开放（E-024 崩溃路径未重试）；12 个待推 commit + 本轮新提交待代理关闭后推送。

## E-026 · 用代码生成科普视频（确定性渲染）

**背景**：用户问「能不能把这个原理通过代码生成视频，像网上火的 Claude 科普视频」。
最初的直觉假设是：那类视频 = AI 文生视频（抽卡式，梦一次一个样）。

**实测一（查证，推翻了上面的假设）**：「Claude 科普视频」主流做法是**代码驱动的确定性渲染** ——
写一个 `frame(t)` 纯函数，逐帧渲染 PNG / 截图，再交给 ffmpeg 合成 MP4。三条禁令：
**不读系统时间、不用无种子随机、渲染时不联网**。视频因此变成一个可 diff 的程序：
改一个字幕是一行 diff，重渲染后其余画面分毫不动；同代码同结果。
主流引擎是 Remotion（React）/ Manim（Python）/ HTML + 无头浏览器；本机选了依赖最少的第四条：
**Pillow 直接算像素 + ffmpeg 只做封装**（不需要 numpy、manim、LaTeX、node_modules）。

**实测二（环境）**：Python 3.13 + Pillow 13 可用；numpy / imageio / cv2 / matplotlib **全无**；
`pip install imageio-ffmpeg` 被代理 502 挡住，去掉代理直连也超时。
**ffmpeg 在 `C:\Program Files\KeyShot Studio\bin\ffmpeg.exe`**（KeyShot 自带）。
它是 `--disable-everything` 的精简构建：只保留 scale / palettegen / paletteuse，
**没有 fade / overlay** → 转场必须在帧内算，不能交给 ffmpeg 滤镜。

**实测三（产出）**：8 镜 / 44.6 s / **1070 帧** / 1600×900 / 24 fps / h264 High yuv420p /
**2.05 MB**；单帧约 0.18 s，全片 **2 m 11 s**；`ffmpeg -f null -` 整片解码 `frame=1070`、`exit=0`。
上屏数字全部来自 E-024 / E-025，无编造：8→7 面 / 233214.16→236607.08、inner 4→2、
11→10 面 / 235922.14→239315.06。

**踩到的坑（都已在渲染器里修掉并写进注释）**：

1. **Consolas 没有中文字形** → 右下角出现 `□ / faces`。修法：`label()` 检测 CJK 自动切雅黑。
   **等宽字体的「代码感」只在纯 ASCII 时成立。**
2. 片头同时画居中大标题与底部标题 → 标题重复；改成 title 镜不画底部字幕。
3. 标签压几何：fillet 镜的 `UntrimOuterLoop → null` 压在橙带上，先挪右侧仍差 4 px，
   最后拆成两行缩短宽度。**中文字宽估算必须留余量，别按等宽字体算。**
4. 底层曲面与盒子顶面都是半透明青四边形 → 糊成一片；底层改**虚线边框** + 填充降到 0.045，
   让「底图 vs 实体」在层次上先分开。
5. 孔消失太快、看不见中间态 → `shrink` 区间从 0.40–0.72 拉到 0.45–0.85。
6. `/tmp` 在 Git Bash（→ Temp）与原生 Windows Python（→ `C:\tmp`）指向不同目录，
   临时文件因此写丢；**临时文件写工作目录内，别写 `/tmp`**。

**结论**：这条链路可复用 —— 换 `storyboard.py` 的 BEATS 与 scene 分派就能讲别的几何概念，
架子（等轴测投影 / 缓动 / 字幕 / 进度条 / contact sheet / 编码）不用动。
对插件项目的直接价值：**以后写功能说明、给用户讲原理、做 release 预告，不必再靠截图拼凑。**

**回填**：`design-lab/README.md` 索引；`design-lab/002-brep-untrim-explainer/`
（README 六步 + style.md + storyboard/render/encode/build_html/preview）；
`INDEX.md` 新增「想讲清原理 / 做科普视频」入口；`SKILL.md` 决策表；今日日志；MEMORY。

**遗留**：无旁白 / 音轨；圆角带是两点近似的示意面（讲拓扑够用，讲 R 值精度不够）；
预览页与 Python 版是两套绘制实现（同一份 BEATS，公式一致但长期可能漂移）。

## E-027 · 给代码生成的科普片配声音：音频也是 sample(t) 纯函数（2026-11-23 晚）

**触发**：用户在 002 号片子出完后追问「可以配个声音吗？」

**动手前的三条假设**：
1. 「Claude 科普视频」的声音多半是 AI 旁白 → 想做就得联网 TTS。
2. 本机 ffmpeg 是 `--disable-everything` 精简构建 → 没法给 MP4 加音轨。
3. 声音只能靠播放器运行时触发，做不到与画面同级的确定性。

**查证与实测（假设 2、3 被推翻，假设 1 部分成立但不必做）**：
- 假设 1：人声旁白确实是外部素材。本机离线 TTS 需要 PowerShell `Add-Type` 加载
  `System.Speech`，当前会话沙箱明确拦截（`Add-Type compiles and loads .NET code at runtime`），
  按纪律**未换等价路径绕过**；且系统是否装有中文语音包无法确认。联网 TTS 又违背三条禁令。
  → 做成可选外部插槽 `narration.md`（文案 + 时间码给全，`encode.py` 自动 `amix` 混入）。
- 假设 2 **被推翻**：第一次只在 `KeyShot Studio/bin` 找到精简 ffmpeg
  （0 音频编码器 / 0 音频滤镜 / 连 wav demuxer 都没有），就下了「本机没法加音轨」的结论。
  实际 **`C:\Program Files\KS2024\bin\ffmpeg.exe` 是完整构建**
  （aac / libmp3lame / pcm_s16le + amix / afade / volume + wav demuxer）。
  修法：`find_ffmpeg(need_audio=True)` 实测 `-encoders` 再挑，不凭路径猜。
- 假设 3 **被推翻**：把音频写成 `t = i / sample_rate` 的纯函数，事件表 `events()`
  从 BEATS 派生，包络在采样点里算，编码器只做 `-c:a aac` 封装。
  连续两次 `audio.py` 的 WAV sha256 一致（`32d811a6…`），确定性成立。

**实测数字**：
- WAV 2,140,800 采样 / 44.60 s / 17 事件（8 cue + 6 tick + thud/lift/chord），生成 **2.8 s**。
- `peak=0.5241 → gain=1.439 → 最终≈0.75`、`rms=0.1403`，不削波。
- MP4 `brep_untrim_with_audio.mp4` **2.90 MB**，整片解码 `exit=0 / frame=1070`，
  并确认 `Audio: aac (LC) 48000 Hz mono 157 kb/s` 流存在。
- `KIND` 从 tuple 重构成 dict（便于 JSON 注入）后音轨哈希不变 —— 结构重构的回归验证。
- 预览页注入 8 beats / 17 events / 5 kinds，`node --check` JS 语法通过。

**结论**：
1. 声音与画面可以共用同一套确定性纪律，前提是「时间轴只有一个来源」（`storyboard.BEATS`）。
2. 音频包络必须 `(1−e^(−t/atk))·e^(−t/dec)` 从 0 起、回 0 收；频率边界用 glide 滑过去，硬切就是 click。
3. 不依赖 ffmpeg 滤镜：包络在 Python 算完，换任意编码器结果一致（与「转场在帧内算」同构）。
4. 同一份数据源贯穿四端（render / audio / encode / preview）时，
   数据结构必须可序列化 —— `KIND` 用 dict 不用 tuple 就是这个代价。
5. **探测能力要完整再下结论**：「本机没法加音轨」是探测不彻底造成的假结论，
   与 E-024「先验证需求，再验证代码」同一类教训，只是落在工具链上。

**回填位置**：`design-lab/002` 的 `audio.py` / `narration.md` / `style.md` §8 / README 六步、
`encode.py` 能力探测、`preview.html` Web Audio 层、`error-catalog.md`、
`INDEX.md` / `SKILL.md` 决策行、MEMORY 跨项目能力、今日日志、GitHub 副本提交。

**遗留**：人声旁白待外部 wav；未做浏览器内 Web Audio 实机听感验收
（只做了 JS 语法 / 注入数据 / 离线 WAV / MP4 音频流的校验）；
`theme` 参数在预览页未暴露，已在 README 如实标注。

## E-028 · 2026-11-23 深夜 · 「取消一条倒角边后所有东西全部消失」：显示层剔除 + 失败路径（修正 v1.6 实现缺陷）

**用户原话**：「我打开rhino了，尝试了一下，嗯，还是有问题，我选择去取消一条倒角边，结果所有东西全部消失了。」

**假设（逐条验证）**：
1. 几何被真的删光了 → 查活文档对象数；
2. 模块 A 的 `RepairToBlank` 在倒角上产出了坏 Brep → 纯几何复现；
3. 执行/显示链的失败路径留下「conduit 剔除源对象但自己什么都没画」的状态 → 查源码 + 反射。

**做法**：按 `INDEX.md` 先查知识地图与错误目录 → 连活 Rhino 查 `get_context` / `list_objects` /
反射 `FwFocusSession` 静态状态 → 纯几何复现（全边圆角盒、单圆角边、单 Chamfer 倒角）→
在用户文档里加**临时对象**完整跑 `FWSelect → TryApply("Fillet")` → 改代码 → 进程内 Roslyn →
反射 → yak → 真安装。临时对象实验完立即删除，主模型未改动。

**实测数字**：
- 现场：`objectCount=4`（1 Brep + 3 条隐藏曲线）；Brep `6 面 / solid / vol 39637.966`；
  `HasActive=False`、`FwMouseWatcher.IsActive=False`、`FwSelectionState.Count=0`、`SourceBrep=None`。
  → **几何没被删光**，「全消失」是显示/替换层症状，不是 `doc.Objects.Delete`。
- 标准路径真机复现（临时 7 面单圆角边 `vol 63922.7433`）：`TryApply ok=True` → 文档对象
  `6 面 / solid / vol 64000`、`hidden=False / visible=True`、`HasActive=False`。**没有复现消失**
  → 排除「重建算法在倒角上必然出错」。
- 全边圆角盒 `66 面 / vol 63089.90` → 识别 12 个 Fillet 组 → `CancelFilletModule` →
  `6 面 / solid / vol 64000`；取消后 `Recognize` 得 `feats=0` → 不重开聚焦。
- **单条 Chamfer 倒角 `7 面 / vol 63820` → `Pass1_Fillets=0 / feats=0`**：识别引擎
  `IsCandidateFilletFace` 认不出平面斜切倒角（只认圆柱/NURBS 过渡面）。新发现的边界，如实告知用户。
- `clean` 与 raw 在这些模型上面数一致（66/66、7/7）、`DuplicateSubBrep` 均成功 →
  「FWSelect 丢 clean」暂未在标准模型上触发错位，但仍是确定缺陷。

**根因（4 个确定缺陷，非单点）**：
- **A（最直接）** `FwFocusConduit.ObjectCulling` 无条件 `e.CullObject = true`，但
  `FeatureVisuals` / `LockedBrep` / `FeatureBrep` 可能因 `DuplicateSubBrep` 失败、索引越界、
  `Stale()` 全部为 null → 「源对象被剔除 + 什么都没画」= 视口全空。
- **B** `FwCancelRunner.TryApply` 把 `FwFocusSession.End(doc)` 写在
  `if (!outcome.Ok) return false;` **之后**：任何失败/异常都不关聚焦，conduit 继续 cull。
- **C** `FWSelect` / `FwCancelPanel.DoPick` 丢弃 `FwApi.Recognize` 返回的 `clean`，
  用**原始 brep** 配 **clean 的特征面索引**（`Build` 里 `MergeCoplanarFaces + Compact` 可重排索引）
  → 高亮与执行器删的面可能错位。
- **D** 写文档前无结果有效性校验：退化 / 零体积 / 包围盒异常放大的 Brep 被 `Replace` 进文档，
  视口里往往什么都看不见。

**修复（v1.6.1.0）**：`HasDrawableContent()` 护栏（剔除前必须确认有可画内容；`Begin` 里无内容则
`conduit.Enabled=false`，模型照常显示）；`TryApply` 重构为「内存算完 + `ValidateResult` 校验通过
才动文档」，`End(doc)` 移到 `Replace` 之前，所有失败路径**不写文档、不关聚焦**，异常全部兜底；
`FWSelect`/`DoPick` 改用 `clean ?? brep` 传给 `Begin`。

**验证**：编译 **105984 bytes / 0 error / 65 warning**；反射 `1.6.1.0`、
`HasDrawableContent` 空→False / 有 FeatureBrep→True、`ValidateResult` 正常→None / null→拒绝；
纯几何回归 `7 面 / 63922.74 → 6 面 / 64000`；yak **74374 bytes** sha256 `80d1f454…`，
rhp sha256 `e93a8a0a…`，真安装 `…\特征识别工具\1.6.1.0\`，哈希与本地一致。

**结论**：⚠️ 部分成立 —— 「几何被删」被推翻；「重建算法必然出错」被推翻；
「失败/显示路径导致全空」✅ 成立且有 4 处确定缺陷可修。
**修正 E-025 的实现层**（不是推翻其几何结论）：v1.6 两模块解耦是对的，
但执行器缺失败安全与显示护栏。**通用教训：DisplayConduit 只要 `ObjectCulling` 剔除源对象，
就必须保证同一帧必定画得出替代内容，否则「看不见」会被用户读成「全删了」。**

**回填**：`error-catalog.md` v1.6.1 段；`rhinocommon-pitfalls.md` v1.6.1 段；
`feature-recognition.md` §13；`INDEX.md` / `SKILL.md` 入口；项目 README/手册/INTERACTION_SPEC；
MEMORY 与今日日志；GitHub 副本本地提交。

**遗留**：GUI 实机验收需**重开 Rhino**（当前进程仍是 1.6.0.0）；单条 Chamfer 倒角识别 0 特征
待扩展判据；实验在用户 Undo 栈留下 2–3 条记录（临时对象已删、当前文档干净）；
GitHub push 仍待代理关闭。

## E-029 · 2026-11-24 凌晨 · 「声音怪怪的、不舒服」：音效 ≠ 配乐（用户听感反馈 + 省算力复盘）

**用户原话**：「明天讨论，我们继续优化，现在整理一下之前如何做视频与声音，下一次可以更加省算力，
还有一个最重要的是声音有点怪怪的，不舒服，你可以看一下 Claude 做的，感觉有一种恍然大悟的感觉，
主要是配乐，画面整体来说还挺不错的。」

**本轮边界**：只整理与诊断，**不改代码、不重渲染、不出新片**；画面冻结（用户已认可）。
产物 `design-lab/002-brep-untrim-explainer/RETRO_audio_and_compute.md`。

**假设与验证（不靠耳朵，全部追到代码行）**：
1. 「是不是削波 / 爆音」→ 否。既有实测 `peak=0.5241 → gain=1.439 → ≈0.75`、`rms=0.1403`，
   包络 `(1−e^(−t/atk))·e^(−t/dec)` 从 0 起回 0 收，无硬跳变。**技术指标全部合格但听感不合格** —— 这条最重要：
   说明「不削波 / 确定性 / 哈希一致」只验证了信号完整性，**完全没有验证音乐性**。
2. 「是不是渲染/编码问题」→ 否。AAC 流存在、44.60 s、17 事件均可复核。
3. 真正根因 = **架构错配**：`audio.py` 做的是「UI 音效生成器」（等间隔提示音 + 持续低频嗡鸣），
   承担的却是「配乐」任务。7 条可追溯根因：
   - ① 17 事件 / 44.6 s ≈ 每 2.6 s 一声，全是 SFX，无和弦进行 / 旋律 / 情绪弧（用户自己定位「主要是配乐」，判断准确）；
   - ② `pad_steps` 每镜换根音 + `scale` 按镜头编号单调上行 = 一路往前走，**没有张力→解决**，所以没有「恍然大悟」；
     片尾 `chord` 前无铺垫，且 pad 回到 55 Hz(A1) 与 D5 大三和弦不构成主—属解决；
   - ③ 55 Hz 纯正弦持续 44.6 s + `pad_level=0.16` = 低频嗡鸣掩蔽（公开配方 pad 仅 0.06 且带 2.5 s 淡入淡出）；
   - ④ 0.3% 失谐拍频(≈0.165 Hz) + 0.11 Hz 呼吸 LFO(±38%) + 每镜 0.9 s 滑音 = 三个慢摆动叠加，音高一直「飘」，缺稳定调性中心；
   - ⑤ **pad 与 cue 不同源**：pad 从 A1 走半音 `[0,3,5,7,10,12,7,0]`，cue 从 A3 走五声 `[220…587.33]`；
     前 6 镜恰好 4:1 协和，beat 6（82.4 Hz vs 523.25 Hz ≈ **6.35×**）、beat 7（55 Hz vs 587.33 Hz ≈ **10.68×**）
     不成简单整数比 → 可听的「打架」。**这是「怪」最可计算的一条**；
   - ⑥ `atk` 最短 **0.002 s**（2 ms）= 机器味（公开复盘：「起音 1 ms → 0.28 s，机器味基本就是这么来的」）；
     `tick` 谐波 `[4.0, 5.4]` 含非整数倍频 → inharmonic 金属声，且已到 1.7 kHz 以上；事件最长 `dec 1.05 s`，无尾音/混响；
   - ⑦ **mono + 无混响 + 无留白**：声音扁、贴脸；pad 全程不断，Silence 缺席导致提示音没有分量。

**对照证据（检索 2026-11-23，社区公开材料，非官方规范）**：
3Blue1Brown 风格 Claude 视频 SPEC.md 的配乐是**可执行的谱**：D major 固定调性
`Dmaj9–Bm9–Gmaj7♯11–Asus2` 每和弦 8 s 循环；钢琴加法合成谐波 `1/0.42/0.18/0.08` 且高次衰减更快、
音符 3.2 s；琶音 60 BPM 且 12% 音符跳过（固定种子）留呼吸；pad 三音 detune ±0.12 Hz、2.5 s 淡入淡出、
0.07 Hz LFO ±20%、音量 0.06；**三次交叉声道回声 83/191/370 ms + stereo**；3 s 淡入 / 5 s 淡出、peak 0.8。
科普片配乐指南共同结论：情绪弧 Problem→Solution→**resolved final chord**、音效要克制、
**Silence 是设计要素**。「恍然大悟」的机制 = 稳定调性做地基 + 渐强积累 + 在揭示帧落到明确主和弦 + 长尾音 + 前置留白。

**省算力结论（本轮最大收获）**：最贵的不是 3.2 min 全片渲染，而是**音频链没有任何可计算的听感指标**，
只验了哈希 / peak / rms / AAC 流 / JS 语法 → 必须真人听完才闭环，问题拖到完整交付后才暴露。
下次在 `audio.py --info` 输出 6 个纯数学指标：事件密度与最小间隔、`atk` 分布、
**pad↔cue 简单整数比命中率**、<200 Hz 能量占比、留白率、调性漂移量。
另有 9 条：局部渲染 `--beats`、contact sheet 设硬门槛、帧缓存增量渲染、一次 preflight 能力表、
单端 events.json、编码一次、控件收敛 3–6 个、谱与音色解耦、坚持三条禁令。

**回填位置**：`RETRO_audio_and_compute.md`（主）、`INDEX.md`（路由 + 计数 30）、
`SKILL.md`（复用提示）、`style.md §8`（v2 听感未验收提示）、`002/README.md`（开放项）、
`MEMORY.md`（压缩重写 + 新结论）、`2026-11-24.md`。

**不新增推翻计数**：这不是「假设被推翻」，是**验收维度缺失** —— 技术指标全过、审美指标从未被测量。
**遗留**：未做实机听感验收；配乐优化留到明天讨论，6 个待决问题已列在复盘 §7。

**2026-11-24 下午追加 · 拍板开始 + GitHub 通道陷阱**：
用户纠正「QQ 打错了，是 github」，并指明参考是 GitHub 上 Codex 驱动视频工具链
（`vincentsch/explainroo`，MIT）生成的配乐好听。查证其机制：内置配乐按 look 分
`warm/upbeat/calm/tech/playful` 五种风格、`music.volume` 可调、旁白时自动 ducking
（`verify` 实测打印「music: about 12 dB under the voice」）；同作者的 Soundroo
让 agent **写谱**再本地渲染 WAV。我们只借鉴「谱与音色分离 + 可测量混音指标」两条原理。
用户拍板两项：① 挂法 = **1 份决策清单逐项回复**；② 路线 = **纯 Python 自研、守三条禁令**，
不引入 Soundroo / Node / 外部模型 / 音频素材。产物仓库根 `DECISIONS_002_AUDIO.md`
（D1–D6 各带现状/证据/A-B-C 推荐 + 三步验收闸门），本地 commit `c19a66e`。

**2026-11-24 13:4x · 配乐 v3 落地（D1–D6 全按推荐 A，用户拍板）**：
只改 `storyboard.py` 的 `AUDIO` 段 + 重写 `audio.py` + `preview.html` 声音层；**BEATS/PALETTE/render.py 未动**（画面冻结）。
- D1 纯标准库；D2 48 kHz **stereo** + 左右不同三抽头回声（83/191/370 ms 与 97/211/389 ms）；
  D3 固定 D major 四和弦 `Dmaj9–Bm9–Gmaj7♯11–Asus2` 8 s/和弦，**按绝对秒走、与 BEATS 解耦**；
  D4 事件 **17 → 7**、`atk 2 ms → 20/25/30 ms`、删掉 5.4 非整数倍频；
  D5 四段弧 setup 0–8.6 / build 8.6–28.4 / **aha 28.4–35.4（t=32 主和弦落点）** / resolve 35.4–44.6；
  D6 pad 0.16→**0.06** + 80 Hz 高通 + 固定 detune ±0.12 Hz + LFO 0.07 Hz ±20%。
- **6 指标自检（`audio.py --info` 2.8 s，不用出片）**：事件 7、密度 0.157/s（原 0.38）、
  最小间隔 3.54 s、atk 20–30 ms、和弦音命中 **6/7**、换调 5 次（原 8 次）。
  指标在分析阶段抓到「协和命中仅 2/7」→ 查出是判据用了频率比绝对容差、跨八度和弦音被误判，
  改成 MIDI 音级归属判定后 6/7。**这正是把听感前移成可计算指标的价值**。
- 分段 RMS 实测（证明情绪弧是真的能量曲线，不是参数摆设）：
  **setup 0.0079 → build 0.0344 → aha 0.1057 → resolve 0.0218**，峰值落在 **t=32.34 s**（啊哈点）。
- WAV 44.60 s / 8.17 MB / stereo，两次 sha256 一致 `1adfa21b…`；
  MP4 重封装 2.93 MB，**AAC LC 48000 Hz stereo 163 kb/s**、1070 帧、verify exit=0。
  `preview_10s.wav`（28–38 s，含啊哈落点）1.83 MB 供真人试听。
- **双端漂移根治**：`preview.html` 声音层从 Web Audio 实时合成改成 `<audio src="soundtrack.wav">`
  直接播离线文件（省算力清单第 6 条「单端定义」），删掉失效的 density/sfx/pad 控件 →
  控件从 9 收敛到 6；注入后 JS `node --check` 通过、旧字段残留 0。教训：**离线与预览不要各写一套合成器**。
- **未做**：真人听感验收（等用户听 10 s 片段）；GitHub push（代理问题未解决）。

**GitHub 通道能力分清（别混）**：`mcp__github__get_me` **可用**（读通道正常，`tiyu0842-sketch`）；
`mcp__github__issue_write` 建 issue → **403 Resource not accessible by integration**
= 连接器**缺 issue 写权限，不是认证过期** → 不 reconnect、不重试等价调用，改用仓库内文档 +
本机 git。本机 `gh` CLI 没装；`env -u 代理 git push origin main` **180 s 超时 / SIGTERM**，
按纪律不再重试。教训：**读可用 ≠ 写可用；连接器写权限被拒 ≠ reauthorize 能解决**；
本机 git 是另一条凭据通道，但代理未全关时 push 仍不可靠。

### E-030 · 工业设计史闯关复习工具（003）与小程序/备案调查（2026-11-24）

**症状/需求**：用户要把本机 `D:/学习进步资料/工业设计史/` 的资料做成「每日答题闯关」复习工具，
后续追加：艾宾浩斯遗忘曲线、错题科普、Hello Kitty/简约双风格、百词斩式卡片、排行榜，
并问「能不能做小程序 / 要不要备案 / 微信分享」。

**需求先于代码（这次做对了）**：连问两轮用途（自己复习 vs 朋友一起刷）和排行榜形式
（本地个人最佳 vs 云端好友榜）后才动手 → 用户选「主要自己复习 + 本地个人最佳榜」，
直接省掉小程序备案/后端/域名这一整条重路径。**这是 E-022「先验证需求」纪律的正向样本**。

**关键能力发现（可复用）**：
- 本机 `D:/学习进步资料/工业设计史/` 的 PDF（题库/知识点汇总/整理总结/何人可笔记）
  **子集嵌入字体 + 无 ToUnicode → 文字层解不出**；`workbuddy-pdf` CLI 本机未就绪；
  百度网盘工具本轮成功注入后，`file_keyword_search` 找到同目录，
  `file_content_create` → `file_content_get` 返回 `succeeded` 但三份 `char_count=0`
  ⇒ **服务端解析也读不出扫描 PDF，不是权限问题**。按纪律不反复重试、不自行 pip install。
- 唯一可用源：`【工业设计史】重点总结要点.doc`（UTF-16LE 老 DOC，正则抽连续中文）。
  首轮手写 29 题 → 原文核对 **只有 11 题可追，18 题是凭通用知识编的 → 全删**，
  并在 `build_questions.py` 加硬校验（evidence[:12] 必须命中原文）。**宁可少，不可编**。
- 外部科普改走 WebSearch（百度百科条目）→ 11 张卡 9 张带 URL、2 张如实标「未核实」。
- 单文件 HTML 双风格纯 CSS（无图片）、艾宾浩斯 1/2/4/7/15/30、错题弹科普卡
  （一张卡一个 idea，借 3Blue1Brown SPEC 的降认知负荷规则）。验证用 `node --check` +
  DOM 引用对照（本机无 playwright/puppeteer），**未做浏览器实机点击**。

**小程序/备案调查结论（政策会变，复用前复查）**：
- 真排行榜必须后端；单文件 HTML 只能本地个人最佳（history 存 localStorage，加 uid 可迁云端）。
- **小程序必须备案、无例外**：平台初审 → **工信部 12381 短信核验 24 h 内必须完成**
  → 通管局 1–20 工作日 → 备案号。个人主体可但只能免费非经营性；
  **类目坑**：答题/科普易被归教育类要办学许可证 → 按「工具」类目提审最稳。
- **微信内 H5**：域名必须 ICP 备案 + HTTPS；分享卡片要公众号 JS-SDK 安全域名。
- 结论：自己复习 → 单文件够用；要好友榜 → 先平台托管 H5（域名通常已备案），
  题库补到 60–100 题再考虑小程序。

**交付**：`quiz_v2.html`（28.6 KB，三模式+双风格+科普卡+本地个人最佳榜）、
README 六步字段 + 备案调查表。本地 commit `6f880ef`/`b7863b6`/`0b96eb2`，累计 23 个未推。
**不新增推翻计数**：这是跨域能力扩展 + 需求验证正向样本；但推翻了「百度网盘服务端解析能救扫描 PDF」
的初始假设（E-030 内部修正，不作为全局假设推翻计数）。

### E-031 · 003 从「刷题工具」纠偏为「理解工具」（2026-11-24 晚）

**用户纠偏原话**：「最主要的是贯穿下来，更好去理解这个世界线……讲一些幽默的历史、笑话帮助记，
而不是纯粹刷题去记……主要学发展内涵的思想变化，然后刷题去巩固。」
**这是 E-022「先验证需求」纪律的第二次应用**：产品重心错配，不是加功能能解决的，是信息架构要重建。

**做对了什么**：
- 把整个设计史重构成**一条因果链**：主线问题「机器能批量造东西以后，东西该做成什么样？」
  11 站每站回答同一个问题、下一站因上一站答案出问题而转向；三组张力（装饰↔功能 / 反机器↔用机器 /
  精英↔大众）贯穿全程。用户说的「内涵/思想变化」= 这条因果链，不是风格排队。
- 每站四层递进：**画面 → 核心思想 → 为什么变 → 轶事 + 承上启下**，符合「先理解后命名」的降认知负荷规则。
- **诚实分类轶事**：真实轶事 7 站（联网核实、带可点来源）+ 记忆画面 4 站（界面明确标「非史实」）。
  绝不把为记忆构造的画面冒充史实——延续 E-030「宁可少不可编」。
- 题目**从主角降级为每站的「巩固」弹层**；打开默认是世界线，不是题。

**真料（可复用）**：水晶宫 245 方案落选、花匠帕克斯顿受王莲叶脉启发（7 岁女儿能站叶上）、
9 天草图 9 个月建成、被嘲「大花房」、丘吉尔「一个时代终结」；包豪斯 Hausbau 倒拼、方盒子办公室、
亚伯斯捡破酒瓶做艺术；文丘里「Less is a bore」+ 母亲住宅「20 世纪后半叶最大的小建筑」+《向拉斯维加斯学习》；
拉姆斯「Less but better」。

**验证升级**：这次第一次用 **Edge headless `--dump-dom` 做实机渲染验证**（此前 003 只有静态检查）——
确认 11 站都渲染、主线与关键轶事文本都在、无 JS 报错。这比 `node --check` 更接近真实，
成本却几乎为零（无需 playwright/装库）。**可复用为这类单文件的标准验收手段**。

**边界**：题库仍只覆盖前 6 站，包豪斯之后 5 站只有叙事无巩固题，界面逐站明示「题目待补」。
**不新增推翻计数**：这是产品重心纠偏 + 能力扩展，非假设被实验推翻。

## 统计与复用提示

- 截至 2026-11-24：**32 条实验**，其中 **14 条推翻了初始假设**（E-015 推翻 E-014 真因，
  E-016 再推翻 E-014 的判断方法与 E-015 附带结论，E-019 推翻「solved=true 即成功」，
  **E-020 推翻 E-014 的"面板未注册"判据**，**E-021 推翻"命令只改了一个视口"的猜想**，
  **E-022 推翻 E-021 的需求方向判断**，**E-023 推翻「文字列表足够」的界面假设**，
  **E-024 推翻「去布尔必须先去圆角」与「API 层只有整面级 UntrimFace」**）。
  E-017 / E-018 为概念与资料精化，不计推翻；**E-025 是 E-024 方案的落地与真机验证，不新增推翻**，
  但记录了一个纯实现层的反直觉坑（枚举默认值导致模块误判）与 CS0104 命名歧义。
  **E-026 是跨域能力扩展（代码生成视频 / 确定性渲染），不新增推翻；
  但它推翻了「这类科普视频是 AI 文生视频」的初始假设** —— 而且这次推翻发生在动手之前，
  靠查证而不是靠实测，值得单独记一笔。
  **E-027 同为跨域能力扩展（音频确定性生成），不新增推翻计数**；
  但它在内部修正了两条环境/能力误判（「本机没法加音轨」「声音做不到确定性」），
  且与 E-026 共用同一个 `storyboard.BEATS` 时间轴，是「同源四端」的第一个完整样本。
  高推翻率说明「先验证再相信」不是口号。
  E-017 / E-018 为概念与资料精化，不计推翻，同样保留判断演化。高推翻率说明「先验证再相信」不是口号。
  注意：E-021→E-022 是"技术实现正确、需求理解错误"的典型样本 —— 推翻的层次比前几条更高。
- 编号提示：台账历史上有两条 E-016（一条 `###` 一条 `##`），不作改动，新实验顺延编号。
- 查坑顺序：`error-catalog.md`（按症状）→ 本台账（按实验编号，看结论演化）→ 专题文档（按领域）。
- 新实验编号顺延；若结论修正旧条目，在本条写「修正 E-XXX」并在旧条补一行指向，不删改旧记录。
