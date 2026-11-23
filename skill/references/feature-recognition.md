# 特征识别与取消（SolidWorks FeatureWorks 风格）

> 来源：RhinoFeatureWorks v1.2 → v1.3.2 真机迭代（2026-11-22/23）。全部结论经真实 Rhino 9 文档验证。
> 适用场景：用户拿到一个**没有历史、只有 B-rep** 的实体（STEP、别人发来的文件），想「取消已经做过的圆角 / 布尔孔槽，回到可重新编辑的毛坯」，而不想手工备份。
> **与 NFF（按法线方向筛面）是两回事，不要混。** NFF 是分面前处理，本专题是几何特征反向工程。

## 0. 先认清需求，别造错东西

用户本意（曾两次纠偏）：**点选一个实体 → 判断哪些面被"改过"（trim / 布尔 / 倒角）→ 删掉这些特征 → 恢复毛坯**。
- ❌ 错解 A：把对象复制一份藏到备份图层，要还原时把备份搬回来。这是"备份对象恢复"，不是几何 untrim。
- ❌ 错解 B：只识别 + 列出 + 高亮，不能取消。识别是手段，取消才是目的。
- ❌ 错解 C：当成法线筛面（NFF）。
历史教训：曾另起 `FeatureWorks_v2` 走错解 A，返工回退到已有的 v1.2 基线。**动工前先确认已有实现是不是本来就对。**

## 1. 几何本质：为什么圆角和孔洞必须用两套算法

Rhino B-rep 的面 = **完整底层曲面 `UnderlyingSurface()` + trim 环**。布尔减、打孔、倒角大多**只改 trim，不动底层曲面**。

| | 孔洞 / 槽（布尔减出来的） | 圆角 / 倒角（过渡面） |
|---|---|---|
| 几何 | 宿主面的 trim 多了**内环**，孔壁另算 | 生成一圈全新的过渡面 |
| 底层曲面 | 没变，只是被剪了 | 过渡面本身就是新曲面 |
| 特征面能 untrim 吗 | 能：`Brep.UntrimFace(hostIndex, tol)` 抹内环 | **不能**：`Brep.UntrimOuterLoop(faceIndex)` 对实体圆角**一律返回 null** |
| 原因 | 内环是独立 trim | 外环四条边全被邻面共享，不是自由边 |
| 正确取消 | `UntrimFace` 一步，孔壁随之自动清理 | 删掉整圈过渡面 → 剩余面取 `UnderlyingSurface().ToBrep()` → `Brep.CreateSolid(pieces, tol)` 重缝 |
| 整圈约束 | 无 | **必须整圈一起删**，只删 1 个会缝出变形面 |

**实测数字（100×80×30 块，体积 mm³，全部真机跑出）**

| 输入 | 操作 | 结果 |
|---|---|---|
| 7 面，R6 通孔 | `UntrimFace` 取消孔 | 6 面 solid **240000** |
| 12 面，孔+槽 | 只取消孔 | 11 面 **224000**（槽保留） |
| 10 面，4×R3 圆角 | 只删 1 个圆角面 | 9 面 **74715.5** ← 变形，错误 |
| 10 面，4×R3 圆角 | 删全部 4 个 | 6 面 **75000** |
| 12 面，孔+槽 | `RepairToBlank()` 全清 | 6 面 **240000** |
| 229667.59（R6 圆角+R9 孔） | 先取消孔 → 再取消圆角 | 237301.66 → **240000** |
| 毛坯 240000 | 重挖孔（部分圆角+保留孔路径） | **236607.08**（几何可行，v1.4 待做「孔体重放」） |

`RepairToBlank()` 流程（v1.2 已验证的正确基线）：
删特征面 → 剩余面 `UnderlyingSurface().ToBrep()` → `Brep.CreateSolid(pieces, tolerance)`。
> 为什么必须取回原生曲面：带 trim 的面直接缝会因孔口/槽口留洞而失败。

## 2. 判断"这个面被改过"的证据信号

`Analyze(brep)` 逐面读，不依赖特征识别是否成功：

| 信号 | 读法 | 含义 |
|---|---|---|
| `innerLoops > 1` | `face.Loops.Count` | 面有内环 → 孔/槽切入外表面 |
| `overhangZ > 0.5` | 底层曲面 domain 跨度 vs trim 边界之差 | 底层曲面比 trim 长 → 被布尔切过 / 倒角削过 trim |
| `reversed` | 面朝向反转 | 布尔减产生的内表面（孔壁/槽壁） |
| `UnderlyingSurface()` | 曲面类型 | 倒角面在 Rhino 里是 **NurbsSurface 不是圆柱面**，别按类型猜 |

实测：槽侧壁 domain `20..31` / trim `20..30`；倒角侧面 domain `0..30` / trim `0..27`；倒角盒 `faces=10 overhang=4 maxOverhangZ=3`；布尔件 `faces=12 innerLoops=2 overhang=5 reversed=6`。

> ⚠️ 曲面参数域在 Rhino 9 是**弧长不是弧度**；柱面 U=轴向、V=周向。算覆盖角要 `跨度 / 半径` 且取 `min(degU, degV)`，取 max 会把轴向长跨度截成 360° 误判成孔。

## 3. 交互：选中 → 聚焦 → 勾选 → 取消（v1.3 定版）

用户定的操作流，**别让用户记修饰键**：
1. `FWSelect` 点一个实体（多重曲面 / 单一曲面都识别）
2. **除特征外的面全部半透明**（Rhino「锁定」的视觉语言），特征面实心橙浮在里面
3. 面板按 **圆角通道 / 孔洞通道** 分两列勾选（因为两套算法不同，必须分通道）
4. 取消 → 自动重新识别并重开聚焦，可连续取消下一组
5. 整段操作一个 Undo 记录（`doc.BeginUndoRecord`），`Ctrl+Z` 一次退回
6. 再运行 `FWSelect` 关闭聚焦

命令：`FWSelect` / `FWFocus`（列通道）/ `FWCancel`（Hole|Fillet|All + 组号）/ `FWCancelPanel`（Eto 面板）。

## 4. 聚焦显示：DisplayConduit 正确配方（踩过两个大坑）

需求：非特征面「半透明像被锁定」，特征面高亮浮出。

| 症状 | 根因 | 正解 |
|---|---|---|
| 叠了 0.85 透明灰，看起来几乎没淡化 | 往**不透明实体**上叠透明层，底色不变 | 用 `DisplayConduit.ObjectCulling` → `e.CullObject = true` 把源对象从绘制中剔除，再画自己的两组子 Brep（锁定面浅灰 0.72 透明 / 特征面实心橙） |
| 特征面只剩线框 | `PostDrawObjects` 里画，被实体深度剔掉 | 特征面改画在 `DrawForeground`（不参与深度剔除）；锁定面可留 `PostDrawObjects` |
| 橙/灰"鬼影"挪不走 | conduit 缓存按面索引抽出的子面，源对象被 Replace/移动/删后索引失效 | 两道保险见下 |
| 反射调 `End(doc)` 报 Parameter count mismatch | 加了可选参数 `bool redraw = true` | 反射调用必须传**全部**实参 |

**鬼影自愈两道保险（缺一不可）**
1. 挂**静态事件**：`RhinoDoc.ReplaceRhinoObject` / `DeleteRhinoObject` / `CloseDocument` 都是**静态事件**（写成 `doc.ReplaceRhinoObject +=` 会 CS0176）。触发即 `End()`。
2. 每次绘制前 `Stale()` 检测：面数变化 + `GetBoundingBox(true)` 中心漂移 > 2% 就停止绘制。
   **不能用 `ReferenceEquals` 比几何**：`ObjRef.Brep()` 返回副本，会永远误判为过期。

**另一个坑**：多次 `Assembly.Load(byte[])` 会产生多个程序集实例，各自带活着的 conduit。清理时必须扫描所有 `RhinoFeatureWorks*` 实例逐个 `End()`，只关当前那个会留残影。

## 5. 边界（必须对用户明说，不要藏）

- `UntrimFace` 会抹掉宿主面**所有**内环：同一面多个孔时，取消一个会把全部一起恢复。这是 Rhino API 边界，不是实现取舍，命令输出要写明。
- 取消圆角是整件重缝，同件的孔/槽会被一并恢复。「只去掉部分圆角、保留孔」需要**孔体重放**（几何路径已验证 `240000 → 236607.08`），尚未实现。
- 自由曲面雕刻、非流形边、极薄壁不一定能识别；保守设计：不认识的几何不自动删。

## 6. 版本与产物

v1.2（识别/证据/修复基线，9/9 自测 PASS）→ v1.3.0（交互闭环）→ v1.3.1（鬼影自愈）→ v1.3.2（ObjectCulling 真半透明，rhp 88576 bytes / 0 error / 46 warning，yak 48422 bytes，装到 `…\1.3.2.0\`）→ v1.4.0（面板类补类级 `[Guid]` 修 `type must have a GuidAttribute` 注册失败；`FWSelect` 识别后自动弹面板的两段式；rhp 89088 bytes / 0 error，已真安装到 `…\1.4.0.0\`）。**加载与面板状态见 E-020**：插件 `LoadMode=2` 从不自动加载，`PlugIn.LoadPlugIn(guid)` 一次即完成（无需重开 Rhino），16 个 `FW*` 命令与两个面板均已注册可见；面板内控件交互（勾选→取消→回毛坯）待用户实机点验。→ **v1.5.0**（编号双向选择 + 显式语义，见 §10）。
**装完必须重开 Rhino**，否则进程里仍是旧的 `Assembly.Load(byte[])` 实验程序集（曾堆到 40+ 个，易崩）。

## 7. 下一版待做（从痛点出发，不重写）

1. 孔体重放：只取消圆角、保留孔（几何已验证可行，方案见第 8 节）
2. 框选 sub-object + 特征面白名单
3. 圆弧识别、NURBS 曲率降级
4. GH 组件、工具栏 RUI / 图标

## 8. 概念澄清：为什么「使用感差」是结构性的（2026-11-23 用户长篇复盘）

用户困惑："想让 Rhino 像 SW/Creo 一样有建模历史，倒角切割后能编辑回退""是不是我没表达清楚""使用感太差"。
**结论：不全然是表达问题，是建模范式差异造成的信息缺口。**

- SW/Creo 存**操作意图**（在边 E 上倒 R5、孔 Ø10），模型 = 特征树重放结果；回退 = 删节点 / 改参数。
- Rhino 存**结果几何**（Face / Edge / Trim loop），**不存操作历史**。倒完角不知道从哪条边来、R 多少。
- 因此 FeatureWorks 做的是**逆向工程**：从结果反推曾发生的操作。同一个最终 B-rep 可由无数操作序列产生
  → **不适定问题（ill-posed）**，机器只能给高置信度候选，不可能像 SW 那样 100% 确定。
- 推论：**交互必须「机器给候选 + 人做裁决」**（分类 → 细分 → 手动框选）。用户草图里自己写的
  "先选 1、2 分类，再到细分选项，其实可以手动框选" 正是这个范式的直觉表达，**别改成全自动**。

### 三类操作对「原生曲面」的精确影响（修正「都没改变原生曲面」的说法）

| 操作 | 底层 Surface | 拓扑 | 能否 Untrim 回退 |
|---|---|---|---|
| 布尔差集 / 打孔 | 完全不动 | 宿主面多内环 | ✅ 直接恢复 |
| 倒角 / 倒圆角 | 原面被裁小（没坏） | **新增过渡曲面** + 两条新边 | ⚠️ 删过渡面 + 重缝 |
| 圆管切除 + 混接 Blend | **拟合出全新 NURBS 面** | 边界重连 | ❌ 无原生可回退，救不回来 |

> 混接面是重新拟合的，不存在可 Untrim 的解析原生曲面 —— 这条边界必须对用户明说，别承诺能救。

### 「保留主体 / 保留全部」的真问题：粒度错配

用户观察："保留时容易把整个面都保留下来，导致识别时出错"。**不是 bug**：
特征信息在 **loop（内环）** 上，而"保留"落在 **face** 上；`UntrimFace` 语义是抹掉这张面**全部**内环，
反过来"整面保留"就是"一个都不抹"，同一面上的孔与槽必然同生共死。与第 5 节记的 A 方案限制同源。

三条实现路径（**第 2 条经 E-016 全网调研修正**）：
1. **整面恢复（现状 A 方案）**：最稳，保留只能全有/全无。
2. **复用官方 `UntrimHoles` 语义**：~~RhinoCommon 无现成 API~~ ← **错**。Rhino 9 官方命令层有
   `Untrim / UntrimAll / UntrimBorder / UntrimHoles`，其中 `UntrimHoles` 支持**逐个选孔边、框选、
   按「最大边缘长度」筛选、`全部`**，`UntrimBorder` 只去外边界而**保留内部孔**。
   即「只删某些孔、保留其他孔」原生做得到；API 层 `Brep.UntrimFace` 是整面级，需要在 Core 层
   按 inner loop 逐个识别来搭桥，或用 `RhinoApp.RunScript` 调命令。代价仍是 trim 重建。
3. **孔体重放（推荐）**：先整体 Untrim 得干净毛坯 → 把"要保留"的孔/槽用布尔差集**重新切回去**。
   "保留"变成"重新执行已知操作"，最接近用户想要的"历史感"，且不碰 trim 细节；数值路径已验证
   `240000 → 236607.08`（见第 1 节实测表）。

> **v1.5 取舍**：先做路径 3（稳、语义最像历史树），路径 2 留作「精确保留」高级选项。
> 详见工作区 `FeatureWorks/INTERACTION_SPEC.md` §3；SW 的 `Delete Faces`（删倒角并记尺寸以便重施加）
> 正是孔体重放的工业原型，而 `Select Tangency`（抓整圈相切边）对应「圆角必须整圈一起删」。
> **修正上一轮「Rhino 官方不给这个命令」**：官方给了完整 Untrim 原语族，缺的是
> 「识别 + 分组 + 回到毛坯」的闭环 —— 这才是本插件的准确定位。

### 同轮显示模式反馈

- "一个视图切 Alias、所有视图跟着变" 在 Rhino 原生**不是默认行为**（默认逐视口独立），
  用户喜欢的联动其实是"设为默认显示模式 / 对全部视口应用"，待现场核实。
- "结构线太密、隐藏后阴影变暗"：**不要全隐藏等参线**（用户明确要三度灰阶 + 等参线看曲面）。
  正解 = 降 `IsocurveDensity` + 提亮环境光 / 减弱 AO + 保留一盏柔和方向光；阴影变暗多由 AO 压暗部所致。

## 9. 原理精化：不是「无限猜」，是有限方法库上的受约束反向推断（2026-11-23 用户追问）

用户追问："SW 里 FeatureWorks 没有历史记录却仍能重新识别，是不是大致去猜 + 有交互、只把大致种类弄了，
因为实现方法就那几种，所以根据方法去约束、反向推导出来？" —— **基本全对**，且对应正式学术方法。

### 术语与出处

- **hint-based / evidence-based / trace-based feature recognition**（Vandenbrande & Requicha 1993；
  Ji & Marefat 称 evidence-based，Regli 称 trace-based）。核心 = **generate-and-test**：
  hint generation → feature completion（几何补全，生成最大不侵入实体的特征体积）→ verification。
- hint 定义 = *minimal indispensable portion of a feature's boundary*：特征被其他操作相交破坏后，
  边界上仍必然残留的最小部分。例：两个相对平面 → slot hint；一根轴 / 圆柱面 → hole hint；
  螺纹属性也可作 hole hint（hint 不必只来自几何）。用户说的「判断曲面是否被修剪」，
  就是 Rhino 语境下的一种 hint。
- 基于 **feature presence rules**（特征存在规则）；文献明确 hint 生成/补全算法是 **feature-type specific**，
  一类特征一套规则、不能复用到新特征类型 → 这是「方法有限 → 规则可枚举」的硬依据。
- 其他路线：graph-based / AAG（Joshi & Chang；我们的 AFAG 洋葱剥皮属此类，特征相交时丢弧是已知弱点）、
  volume decomposition、rule-based、ANN。综述普遍认为真实工业零件（数百面）会让多数方法停机。

### 对「不适定」的精化（修正第 8 节的粗略表述，旧条不删）

第 8 节说「不适定 → 机器只能给候选」，容易被读成「无边界乱猜」。更精确：
**假设空间是封闭且有限的**（可解析面类型有限 → 能产生它们的建模操作有限 → 反向推断收敛得了）。
不适定指的是**同一结果对应多个合法假设**，不是「没有约束」。工程解法因此是：
有限模板匹配 + 置信度排序 + 多解时交人裁决 —— 既不是放弃自动化，也不是追求全自动。

### SW 里的字面印证

- 自动识别第一个界面就是**勾选有限特征类型清单**（Extrudes / Drafts / Revolves / Holes /
  Fillets-Chamfers / Ribs / Volume / Sheet Metal）→ 用户说的「方法就那几种」被做成可枚举的表。
- Intermediate Stage 可 `Find Patterns` / `Combine Features` / **Re-Recognize as alternate features**
  → 多解改判口。
- **识别过的特征退出后续计算**（recognized features removed from further calculations），
  剩余几何再送进去重跑；顺序 = 建模顺序的**逆序**：
  `Fillet/Chamfer（尺寸递增）→ Drafts → Holes → Ribs → Cut → Shell → Boss`。
  理由：细节特征会干扰大特征识别，先细后粗降低模型复杂度。
- 交互式一次只认一类，人指定类型 + 手选面/边，SW 反推 sketch / 方向 / 终止条件 / 参数
  = hint completion 的工业实现。CATI 原句：计算机「不直觉地考虑最佳建模方法，也不考虑设计意图」。
- **重要前提修正**：SW 原生 `.sldprt` **有** FeatureManager 历史树；FeatureWorks 专用于
  **导入的 dumb solid**（STEP / IGES / Parasolid 只带 B-rep）。它做的是**重建**历史，
  官方与业界用词克制：*rudimentary feature history*、*may not create the exact feature tree*、
  目标 *workable tree, not perfect tree*。→ 不是「它没记录」，是「输入里没有、按方法约束补一个粗糙的」；
  这反而强化用户洞察：没有历史 → 只能靠方法约束反推 → **交互是必要组成，不是补丁**。

### 对 v1.5 的落地决策（已写入 INTERACTION_SPEC.md §2.1）

1. 把隐含的孔洞/圆角双通道升级成**显式方法库表**：`生成方法 → 期望拓扑签名 → 反推规则 → 适用边界`；
   一类一套规则，别做万能分类器。
2. 每个候选输出**置信度 + 一句依据**（判孔：圆柱面 + 内环 + 共轴；判圆角：等半径 + 相切链），面板显示理由。
3. 高置信批量、**低置信不自动执行**进面板等裁决（对应 Auto / Interactive 两级）。
4. **逆序剥离 + 已识别退出候选池**：先圆角/倒角（小→大）→ 孔槽 → 最后保留主体。
5. **保留 = 重新执行**（孔体重放），对应 `Delete Faces` 记尺寸再重施加，而非「不删某些环」。
6. 诚实边界：Rhino 自由度（自由曲面 / 混接 / 任意布尔）使假设空间远大于 SW 机加工域，
   文献明说 3D / freeform 特征识别至今困难 → 我们置信度天花板更低，**结构上更依赖人裁决**。

> 出处：help.solidworks.com 2025 `Recognizing Features Automatically`；GoEngineer
> `FeatureWorks: Automatic vs Interactive Recognition`；CATI `Advanced Techniques for Recognizing
> Features`；Mechanitec `SolidWorks FeatureWorks Guide`；Cardiff ORCA
> `Intelligent Techniques for Automatic Feature Recognition in CAD Models` §2.4.3；
> Wikipedia `Feature recognition`；ScienceDirect S016636151000028X 引言综述。

## 10. v1.5：从「文字列表」升级为「人能在模型上裁决」的界面（2026-11-23 晚）

用户看 v1.4 面板截图后的三点批评，全部指向同一件事：**识别结果必须能与几何对上，且操作语义不能靠默认猜测**。

| 批评原话 | 本质问题 | 落地 |
|---|---|---|
| 「一个一个 flat，我都不知道这是哪个跟哪个」 | 特征列表与模型之间**没有可辨识映射** | `FwFocusGroup.Id`（F1/F2…、H1/H2…）；conduit 在组包围盒中心用 `Draw2dText` 画同号标签；面板行首同号；点行 → 该组青色粗线、其余压暗；另有「缩放到选中项」 |
| 「为什么不能选边缘，然后取消它的特征」 | 面板单向：只能从文字出发，CAD 用户习惯从**几何**出发 | `FWPickFeature`：`GetObject{SubObjectSelect=true}` → `ObjRef.GeometryComponentIndex`；`BrepFace` 直接查组，`BrepEdge` 靠 `BrepFace.AdjacentEdges()` 反查所属面 → `PickGroup` 回写面板勾选 |
| 「要勾选保留全部还是删除选中的」 | 旧版“不勾=全部取消”是**隐式破坏性默认** | 三个显式按钮：`取消选中 N 项`（N=0 拒绝执行）、`保留全部`（模型不动，只关聚焦）、`全部取消 → 回毛坯` |

关键纪律：

1. **选中 ≠ 执行**。视口点边只打勾 + 高亮，绝不直接改文档；改模型必须再点显式按钮。
2. **编号必须两边共用同一份**：`FeatureVisuals` 索引与 `AllGroupCount`（圆角在前、孔洞在后）严格对齐；
   抽面失败也放占位，否则编号错位比没有编号更糟。
3. **回调用自定义委托 `FocusPickHandler`**，不用 `Action` / C# event —— 本机 WeaverBird 让 `System.Action` 都 CS0433。
4. **面板注册用 `_registered` 闸门**，别用 `DockBarIdInUse` 判注册（E-020：浮动面板恒 false）。
5. **打包脚本不得覆盖 README / manifest**：旧 `Build_Package.py` 每次 build 都把两个文件重写成 v1.0 模板，
   包内说明与真实功能脱节；v1.5 起只在文件缺失时生成，并把 `使用手册.md` / `INTERACTION_SPEC.md` 一并入包。
6. 当前进度：rhp 96256 B / 0 error，yak 62259 B / sha256 `44664b48…`，
   真安装到 `…\特征识别工具\1.5.0.0\`（rhp sha256 `a03c0624…` 一致）。
   **运行中实例仍 1.4.0.0**，`FWPickFeature` 需重开 Rhino 才能注册。
   `FWPickFeature` 是交互命令，无法脚本同步驱动 —— 双向选择仍需用户实机点验。


## 11. 两个模块解耦 + 「取消修剪 vs 补面」的精确边界（2026-11-23 晚，E-024）

用户看完 v1.5 后总结三点，全部指向同一件事：**交互逻辑不清晰，且两个通道被错误地绑成串行**。

| 用户的话 | 真相（真机实测） | 正确做法 |
|---|---|---|
| 「去除布尔是不是必须先去完圆角才能去」 | **不成立**。`RemoveHoles(指定内环)` 只删选中的孔：圆角盒+1孔 11 面 / 235922.14 → 10 面 / 239315.06 = 纯圆角盒，**圆角完好** | 布尔模块走 `Brep.RemoveHoles(IEnumerable<ComponentIndex>, tol)`，与圆角模块**完全独立**、任意顺序 |
| 「为什么不直接让那个面取消修剪，而是补那个面」 | **孔可以、圆角不可以**。孔 = 底层曲面 + trim 内环；圆角 = 滚球扫出的**新增过渡曲面**，四边与邻面共享，没有更大的底层曲面可还原 | 孔走 `RemoveHoles` 抹环；圆角只能删整圈过渡面 + 相邻面重新求交缝合（`Defillet`） |
| 「为什么只能在那个框里选，不能在原界面框选标红的」 | `ObjectCulling` 剔除源对象 → 橙色面是 conduit 自绘的**影子**，不是文档对象，Rhino 拾取不到；`FWPickFeature` 又是一次性模态 `Get()` | 保留源对象可拾取，挂 `MouseCallback` / `RhinoDoc.SelectObjects` 静态事件做**常驻双向联动** |

### 当前实现为什么会造成「顺序依赖」的错觉

- **孔洞通道**用了 `UntrimFace(host, tol)` —— 官方 since 9.0 定义是「outer boundary is untrimmed
  **and all inner loops (holes) are removed**」。它把**整个宿主面**外环 + 全部内环一起抹掉：
  盒+2孔 8 面 → 6 面 240000，**两个孔一起没了**；圆角盒+1孔 → 10 面 239315.06（孔没了，圆角还在）。
- **圆角通道**用了 `Defillet`（`FwReconstruct.cs`）：把**所有非圆角面**都外扩成完整解析平面，
  再 `CreateSolid` 求交。这一步会把带 trim 的面（孔/槽）一并抹平 → **去圆角会连带把布尔结果也去掉**。
  用户看到的现象其实是「去圆角顺手把孔也删了」，被读成了「去布尔必须先去圆角」。方向正好相反。
- 结论：**两个模块在几何上本就独立，是共用 `RepairToBlank` 式整件重缝把它们绑死了**。
  正解 = 两个执行器各自只改自己那一部分几何，不整件重建。

### 官方交互范式（别自己发明）

- `UntrimHoles` 官方步骤：「Select hole edges individually. **Or use window selection**」，
  另支持 `All` / `MaximumEdgeLength` / `KeepTrimObjects`；`UntrimBorder` 明确「Interior trims (holes) will remain」。
  → **在主视口框选要去掉的孔**才是 Rhino 原生语义，不是在小面板里勾 checkbox。
- SolidWorks FeatureWorks 交互识别：「Under *Selected entities*, **select geometry from the graphics area**」、
  「You do not have to select every face」、`Chain fillet faces` / `Recognize similar`。
- Fusion 360 `Find Features`：框选 → 自动分组 → 浏览器/timeline 列表 → hover 高亮整组 → 直接改参数。
- vcad `Selection` 的 *Feature Tree Sync*：「**Multi-selection works in both directions**」，
  配 Hover Preview、Shift 加减选、点空白清空。
  → 主流布局 = **图形区直接操作 + 常驻树状面板 + 一份共享选中集，双向同步、多选、可预览**。

### 落地纪律（v1.6 已按此编码，实测见 §12）

1. **一份选中集**：`HashSet<int> SelectedGroups` 由视口与面板共同读写，取消「同一时刻只允许一边有勾选」。
2. **不进模态命令**：`FWSelect` 后挂 `MouseCallback`（`OnMouseDown` / `OnMouseMove` / `OnMouseHover`），
   悬停预览、点选、框选、Shift 加减选全在原视口完成；面板常驻。
3. **两个独立执行器**：`CancelHoles(选中内环)` → `RemoveHoles`；`CancelFillets(选中过渡面)` → 删面重缝。
   各自一个按钮、各自报告，互不连带；空选中不执行。
4. **别再用 `UntrimFace` 做单个孔**，也别再整件 `RepairToBlank`；这是 E-024 修正 E-018 的核心。
5. 开放项：`UntrimBorder` 命令层「去外环保留内环」能否进一步替代 `Defillet`，尚未验证
   （`DuplicateSubBrep` + `UntrimOuterLoop` 连调导致 Rhino 进程崩溃，按纪律未盲目重试）。

## 12. v1.6 落地：常驻双向联动 + 严格两独立模块（E-025，已编译/已安装/已真机几何验证）

§11 是诊断与方案，本节是实现与证据。**用户拍板三项**：
「按方案全做」「严格两模块、不要总开关」「去圆角连带影响孔时明确报出，不偷偷改」。

### 12.1 为什么接管左键而不是「保留源对象可拾取」

E-024/§11 曾写「保留源对象可拾取 + `RhinoObject.SelectSubObject`」，v1.6 实际采用**另一条更稳的路**：
conduit 自绘的橙色特征面永远不是文档对象，`ObjectCulling` 又让源对象退出绘制，
无论怎么设置子对象选择，Rhino 原生框选都碰不到「标红的那一块」。
所以 `FwMouseWatcher : MouseCallback` 接管左键（`e.Cancel=true`），
用 `RhinoViewport.WorldToClient` 把每个 `FwGroupVisual.Bounds` 的 8 个角投影成屏幕矩形，
点选取面积最小的命中组、拖框取相交组，写回**一份** `FwSelectionState` 共享选中集。
不建文档对象、不进 Undo、不污染 .3dm；`FWSelect` 的 toggle / `End` 一并 Stop。

> 这一条是「先验证需求，再验证代码」的又一次体现：§11 的直觉方案（改 Rhino 拾取）
> 在 conduit 架构下做不到，实现时改用屏幕投影命中测试才真正解决「只能在框里选」。

### 12.2 两个执行器的精确边界

| 模块 | API | 只改什么 | 实测 |
|---|---|---|---|
| B 去除布尔切割 | `Brep.RemoveHoles(IEnumerable<ComponentIndex>, tol)`，`ComponentIndex(ComponentIndexType.BrepLoop, loop.LoopIndex)` | 选中的 inner loops | 盒+2孔 `8/4/233214.16` → 只删 H1 → `7/2/236607.08`；圆角盒+1孔 `11/2/235922.14` → `10/0/239315.06`（圆角完好） |
| A 去除圆角 | 删整圈过渡面 → `UnderlyingSurface().ToBrep()` → `CreateSolid` | 整圈过渡面 + 相邻面重缝 | 连带恢复 4 个内环时 `collateral=4`，消息原文报出，**不做孔体重放** |

`FwFocusGroup.Loops` 由 `FindInnerLoops()` 在 `FwFocusSession.Begin` 时解析：
遍历 `brep.Loops` 中 `LoopType == Inner` 的环，用 `BrepTrim.Edge.AdjacentFaces()` 判断是否与孔洞组
的孔壁面相邻；兜底再查组自身面上的内环。实测 H1→`[7,8]`、H2→`[10,11]`，4 个圆角组→空。

### 12.3 严格两模块的三个闸门

1. `FwSelectionState.IndicesInChannel(module)` 只取该通道的选中索引，另一通道勾选原样保留；
2. `FwCancelRunner.TryApply(doc, module, targets, out msg)` 校验每个 target 的 `Channel` 与 module 一致，
   跨模块混选直接拒绝；
3. 面板删掉「全部取消 → 回毛坯」总开关，两个分区各一个按钮；N=0 拒绝执行。

**踩过的坑（务必记住）**：初版 `CancelBoolean` 用 `g.Type == FeatureType.Fillet` 判断模块归属，
而 `FeatureType` 枚举**默认值恰好是 Fillet**（`Fillet, Chamfer, SimpleHole, …`），
手工构造/异常数据的孔洞组被误判成圆角 → `RemoveHoles` 收不到内环、静默失败。
改为只认显式 `g.Channel`（`"Fillet"` / `"Hole"`），runner 同步改。
**判断模块归属别用带默认值的枚举。**

### 12.4 待人工验收

常驻鼠标的 GUI 手感（拖框矩形、hover 黄色描边、Shift/Ctrl、多视口、`e.Cancel=true` 对右键旋转与
gumball 的影响）尚未实机点过：本轮 Rhino 是 E-024 崩溃后自动重开的空文档实例，
交互命令按纪律不从脚本同步驱动。需用户重开 Rhino（装完必须重开）后一并验收
v1.5 面板、v2.10 Alias 当前视口独立、v1.6 常驻框选。
