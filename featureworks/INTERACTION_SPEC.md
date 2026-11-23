# FeatureWorks 交互与实现规格 v1.5

> 2026-11-23 晚｜状态：**v1.5 已编码落地（rhp 96256 B / 0 error），待用户实机点选验收**
> 来源：用户手绘草图 + 全网调研（出处见 §7）+ 现有 v1.4.0 源码核对 + 真实 Rhino 9 只读探活
> 分工：`使用手册.md` 是用户向说明；技能包 `feature-recognition.md` 第 8 节是方法论；**本文件是实现规格**。
>
> **v1.5 落地补充（用户看截图后的反馈）**：① 面板行与模型必须一一对应 → `F1/H1` 编号双向标签；
> ② 用户要能在界面状态下直接点模型的边 → `FWPickFeature` + `FwFocusSession.PickGroup`；
> ③ 勾选语义必须显式 → `保留全部 / 取消选中 / 全部取消`，空勾选不执行（见 §10）。

## 0. 本轮三条修正

1. **「loop 级手术 RhinoCommon 无现成 API、风险高」——错，要修正**。Rhino 9 官方命令层有 `UntrimHoles`，支持逐个选孔边 / 框选 / 按「最大边缘长度」筛选 / `全部`，即「只删某些孔、保留其他孔」原生做得到。API 层 `Brep.UntrimFace` 是整面级没错，但**命令层提供了 loop 级能力**。→ §3
2. **「保留主体」在 SW 里叫「父特征（凸台/基体）不可删除」，只能删独立子特征**。用户直觉与工业软件术语完全一致，不是自造概念。→ §2
3. **「取消后自动重开聚焦、连续取消下一组」与 SW Interactive 模式同构**：识别过的特征从后续计算中移除，逐类逐个推进；官方忠告是「目标是可工作的特征树，不是完美的特征树」。我们的方向是对的。→ §4

## 1. 术语对照（用户说「不太懂专业术语」，先对齐语言）

| 用户的话 | SW / Creo 术语 | Rhino / RhinoCommon | 我们插件里 |
|---|---|---|---|
| 载入物体 | Import / dumb solid | 选中 Brep / Extrusion | `FWSelect` 点选 |
| 识别特征 | Recognize Features（Auto / Interactive） | trim 环 / 面类型 / G1 相切证据 | `Analyze()` |
| 圆角方向 | Fillet / Round | 过渡面（NurbsSurface） | 圆角通道 |
| 孔洞 / 布尔 | Hole / Cut-Extrude | 宿主面 inner loop | 孔洞通道 |
| 取消 / 剥离 | Delete Faces / Suppress | `Untrim` / `UntrimHoles` / 删面重缝 | `FWCancel` |
| 保留主体 | 父特征（Boss / Base）不可删 | 承载其余面的宿主面 | 待实现 |
| 全部去除 | — | `UntrimAll` | `FWCancel All` |
| 手动框选 | Interactive：手动选面 | 框选孔边 | 待实现（sub-object） |

## 2. 全网学到的：SW FeatureWorks 真实流程（可直接借鉴）

- 导入 STEP / IGES / Parasolid → 单个 **dumb solid**，无特征树
- `Insert > FeatureWorks > Recognize Features` → 属性面板；**自动识别 / 交互识别**双模式
- 交互模式：**一次只认一种特征类型**，手动选面；推荐识别顺序
  `Chamfer/Fillet/Round（按尺寸递增）→ Drafts → Holes → Ribs → Cut → Shell → Boss`
  （理由：细节特征会干扰大特征识别；先细后粗降低模型复杂度）
- **Delete Faces**：删掉整个倒角，**记下尺寸以便之后重新施加** ← 这就是「孔体重放」的工业原型
- **Select Tangency**：右键抓整圈相切边 ← 对应我们「圆角必须整圈一起删」
- **Recognize similar / Combine Features**：选一个面抓所有相似 / 同尺寸特征 ← 对应我们的「特征组」
- 识别过的特征**从后续计算中移除**，逐类推进；中文教材原句：「完成一个特征识别后，该特征将会隐藏，余下特征将继续识别」
- **父特征（凸台 / 基体）不能删除**，只能删独立子特征
- 官方忠告：*"the goal is a workable feature tree, not a perfect feature tree"*

> 这句话值得贴在面板上：逆向识别不追求 100%，追求「可工作的结果 + 人能裁决」。

### 2.1 识别原理：不是「无限猜」，是有限方法库上的受约束反向推断

用户追问「SW 没有历史却仍能重新识别，是不是根据实现方法去约束、反向推导」——**成立**，
对应学术方法 **hint-based / evidence-based feature recognition**（Vandenbrande & Requicha 1993），
流程 **generate-and-test**：hint 生成（找特征边界残留的最小线索）→ 补全（生成候选特征体积）→ 验证。

三点精确化：① 假设空间**封闭有限**（自动识别界面那张特征类型勾选清单就是它），所以反推收敛得了；
② 证据是**拓扑/几何签名**（凹凸边、inner loop、相切链、共轴、等半径），不是「形状像不像」；
③ 不适定指**同一结果对应多个合法假设**，不是没有约束 → 解法是模板匹配 + 置信度排序 + 多解交人裁决。

前提修正：SW 原生 `.sldprt` **有** FeatureManager 历史树；FeatureWorks 专用于**导入的 dumb solid**，
它重建一个 *rudimentary / workable* 特征树。所以「没有记录」应理解为「输入里没有」，
这正好说明**交互是这套方法的必要组成，不是补丁**。

落到 v1.5 的六条决策（详细论证见技能包 `feature-recognition.md` 第 9 节）：

1. 把孔洞/圆角双通道升级成**显式方法库表**：`生成方法 → 期望拓扑签名 → 反推规则 → 适用边界`；
   规则 **feature-type specific**，一类一套，别做万能分类器。
2. 每个候选输出 **置信度 + 一句依据**，面板显示理由，人才裁得动。
3. 高置信批量、**低置信不自动执行**进面板等勾选（对应 Auto / Interactive 两级）。
4. **逆序剥离 + 已识别退出候选池**：圆角/倒角（小→大）→ 孔槽 → 最后保留主体。
5. **保留 = 重新执行**（孔体重放），对应 `Delete Faces` 记尺寸再重施加。
6. 诚实边界：Rhino 自由度远大于 SW 机加工域，文献明说 3D/freeform 特征识别至今困难，
   我们置信度天花板更低 → **结构上更依赖人裁决，别做全自动**。

## 3. 重大修正：Rhino 9 官方 Untrim 命令族

| 命令 | 行为 | 与我们的关系 |
|---|---|---|
| `Untrim` | 把 Trim 剪掉的部分还原成完整曲面（选内孔边 / 边界边） | 用户观察到的现象，官方原语 |
| `UntrimAll` | 一次取消所有内部孔 + 外部修剪边 | ≈ `FWCancel All` |
| `UntrimBorder` | 只取消外边界，**保留内部孔** | 可用于「只恢复被裁小的原生面、保留孔」 |
| `UntrimHoles` | 只取消不接触边界的内部孔；**可逐个选孔边、框选、`全部`、按「最大边缘长度」筛选** | **直接解决「保留」痛点** |

`UntrimHoles` 另有菜单路径：实体 > 实体编辑工具 > 洞 > **将洞删除**。

**对方案的影响**：上一轮给的三路径改写为

- 路径 1 **整面恢复**（`Brep.UntrimFace`，当前 A 方案）—— 保留、最稳，但粒度粗，全有 / 全无
- 路径 2 **改为「复用官方 `UntrimHoles` 语义」** —— 不再说「无现成 API」，而是「命令层有、API 层要自己搭桥」。可在 Core 层按 inner loop 逐个识别，或用 `RhinoApp.RunScript` 调命令选边；代价是要处理 trim 重建
- 路径 3 **孔体重放**（仍推荐）—— 整体 Untrim 得干净毛坯 → 按识别出的孔体布尔差集重新切回（`240000 → 236607.08`），最接近「历史感」

> 取舍：**v1.5 先做路径 3**（稳、语义最像历史树），把路径 2 留作「精确保留」高级选项。

## 4. 交互规格 v1.5（两段式 + 分步识别）

**阶段 A（已有，v1.4）**：`FWSelect` → 点选实体 = 载入 → `FwFocusSession.Begin` 识别 → 非特征面半透明锁定（ObjectCulling）、特征面橙 → **`FwCancelPanel.Open()` 自动弹面板**（`FwSelectCommand.cs:65` 已确认）。

**阶段 B（待验收后实现）**：面板内

1. 两通道列表（圆角 / 孔洞）—— 已有 `CheckBoxList`（`FwCancelPanel.cs:33-34`）
2. **加「识别顺序」提示**：先圆角后孔洞（对应 SW 先细后粗）
3. **加「保留主体 / 保留全部」**：语义 = 父特征不可删；实现走路径 3 孔体重放
4. **手动框选**：sub-object 拾取 + 与勾选列表双向同步（对应 SW Interactive / `UntrimHoles` 框选）
5. **分步推进**：取消一组后自动重识别、重新聚焦、列表刷新（`Refresh()` / `PanelShown` 已有，`FwCancelPanel.cs:208/238`）
6. 整段一个 Undo（已有）

**明确不做**：全自动识别（不适定问题，见专题第 8 节）；1:1 抄 xNurbs（官网只有 "one simple UI" 范式与「选曲线/点 → 生成曲面」两段式描述，**无公开自动弹面板实现源码**）。

## 5. 显示模式调参规格（A 线，精确数值）

只读探活确认三个自定义模式确实在：`Alias EyeCare` / `Alias EyeCare Dark` / `Alias Style`。

- 结构线密度（`SurfaceIsocurveDensity`，官方 rhinoscript API）：
  `-1` 全隐藏 / `0` 只边界 + knot 线 / `1` 加一条 interior / `>=2` 加 N+1 条
  中文文档同义：`0` 不显示、`1` 节点处、`2` 节点间加一条、`N` 加 N-1 条
  → **建议设 `1`（或 `0`），不要 `-1`**：既降密度又保住判断曲面走向的依据（用户明确要三度灰阶 + 等参线）
- 暗色曲面 → 结构线设**浅色**（中文教程建议）
- `Options > View > Display Modes` 里 `Show isocurve` 是模式级总开关；对象属性另有个别密度（默认 1）
- 阴影变暗：AO（Rendered / Arctic 的 Ambient Occlusion）压暗部 → **减弱 AO + 提环境光 / Skylight + 留一盏柔和方向光**
- 性能：高 AO / 重阴影吃 FPS，大装配时关
- **全视图联动**：Rhino 显示模式**按视口独立**（`SetDisplayMode` 逐视口 / 视口标题菜单）；喜欢的「一切全变」要靠设为默认模式或对全部视口应用，**不是原生默认行为**

## 6. 验收清单（这一步只能你做）

1. **正常退出并重开 Rhino**（磁盘已装 `…\特征识别工具\1.4.0.0\`；只读探活显示当前进程无任何 FeatureWorks 程序集、两个面板 `inUse=False`）
2. 准备带圆角 + 孔的实体（没有就 Box → `FilletEdge` → 圆柱 `BooleanDifference`）
3. 敲 `FWSelect` → 点它
4. 观察：① 视口是否出现半透明壳 + 橙色特征面 ② 「特征取消」面板是否**自动弹出** ③ 圆角 / 孔洞两列是否有条目 ④ 勾选后取消是否回到直角毛坯
5. 把结果（截图或描述）告诉我；**通过后才按 §4 编码 v1.5**

> 探活另发现两个 API 事实，已回填技能包：`Panels.GetRegisteredPanelIds()` 在 Rhino 9 不存在；`Command.GetCommandNames()` 无 0 参数重载。
> **「进程里没有程序集」不能推断「没安装 / 没重启」** —— 插件可能按需加载，这是对 E-014 判断方法的修正。

## 7. 参考来源（可核查）

- xNurbs 官方 https://www.xnurbs.com/ — "one simple UI for all kinds of NURBS modeling"
- SW FeatureWorks 流程 https://solidxperts.com/en/blog/featuresworks-in-solidworks-step-and-iges-files/
- SW 自动 vs 交互识别顺序 https://www.goengineer.com/blog/solidworks-featureworks-automatic-vs-interactive-recognition
- SW 交互技巧（Delete Faces / Select Tangency） https://www.cati.com/?p=175192
- Rhino 9 官方 Trim / Untrim 命令族 https://docs.mcneel.com/rhino/9/help/zh-cn/commands/trim.htm
- Rhino 官方曲面编辑指南（Untrim 定义） https://www.rhino3d.com/docs/guides/user-guide/edit-curves-surfaces/
- `SurfaceIsocurveDensity` API https://developer.rhino3d.com/api/rhinoscript/surface_and_polysurface_methods/surfaceisocurvedensity.htm
- 显示模式调参建议 https://novedge.com/blogs/design-news/rhino-3d-tip-tune-rhino-display-modes-for-high-contrast-efficient-modeling
- 等参线开关教程 https://hopific.com?p=7198/
- 结构线密度中文说明 https://www.bimxxw.com/soft/model/rhino/36557.html
- CADacombs 0.2.10（含 `RemoveTrim` / `DeleteFaces` / `MergeAllFaces`，LGPL，GitHub 开源）https://www.food4rhino.com/comment/reply/5708?lang=en
- TIGER Fillet+（闭式解真实球面 / 圆柱面圆角 + 滑杆实时预览）https://www.food4rhino.com/en/app/tiger-fillet
- SolidWorks 中文教材（交互识别 / 删除面 / 父特征不可删）https://mooc1.chaoxing.com/mooc-ans/ztnodedetailcontroller/visitnodedetail?courseId=205722041&knowledgeId=179397286

## 8. 竞品定位（顺带查到，供发布物料参考）

| 插件 | 做了什么 | 没做什么 |
|---|---|---|
| CADacombs（Food4Rhino，LGPL） | `RemoveTrim`、`DeleteFaces`、`MergeFace`、`TrimSrfWithCrvs` 等原语 | 无自动特征识别、无「回到毛坯」闭环 |
| TIGER Fillet+（Food4Rhino） | 用闭式解生成真实球面 / 圆柱面圆角，带 live slider | 从源头把圆角做对，不做逆向取消 |
| Rhino 原生 | `Untrim` 命令族（低层原语） | 不识别「这是圆角还是孔」、不自动分组 |
| **我们** | **识别 → 分组 → 勾选 → 取消 → 重识别闭环** | 混接拟合面不可回退（诚实边界） |

> 差异化很清楚：别人给的是「原语」，我们给的是「从结果几何反推操作并回到毛坯」的闭环。这也是 GitHub / Food4Rhino 文案该讲的一句。

## 10. v1.5 落地决策：可辨识性 + 双向选择 + 显式语义

用户看完 v1.4 截图后的三点批评，逐条对应到实现：

| 用户的话 | 问题本质 | v1.5 对策 |
|---|---|---|
| 「一个一个 flat，我都不知道这是哪个跟哪个」 | 识别结果与模型缺少**可辨识映射** | `FwFocusGroup.Id`（F1/F2…、H1/H2…），视口 `Draw2dText` 画在组包围盒中心，面板行首同一个 Id；点行还会青色高亮 + 可缩放到该组 |
| 「为什么不能在这个界面中选边缘，选边缘再取消特征不是更好吗」 | 面板是单向的，只能从文字出发；CAD 用户习惯从**几何**出发 | `FWPickFeature`：`GetObject{SubObjectSelect=true}` → `ObjRef.GeometryComponentIndex`；`BrepFace` 直接查组，`BrepEdge` 用 `BrepFace.AdjacentEdges()` 反查面 → `FwFocusSession.PickGroup` 回写面板勾选 |
| 「要勾选保留全部还是删除选中的」 | “不勾=全部取消”是**隐式破坏性默认** | 三个显式动作：`取消选中 N 项`（N=0 时拒绝执行）、`保留全部`（仅关聚焦，模型不动）、`全部取消`（明确全删） |

实现纪律：

1. **选中 ≠ 执行**。视口点边只勾选并高亮，绝不直接改模型；改模型必须再点显式动作按钮。
2. **一组一号，两边共用**。`FeatureVisuals` 的索引与 `AllGroupCount`（圆角在前、孔洞在后）严格对齐，
   抽面失败也放占位，避免编号错位。
3. **不用 `Action` / C# event 做回调**：本机 WeaverBird 让 `System.Action` 触发 CS0433，
   改自定义委托 `FwFocusSession.FocusPickHandler`。
4. **面板注册用 `_registered` 布尔闸门**，不再用 `DockBarIdInUse` 判注册（浮动面板恒 false，见 E-020）。
5. **不覆盖人工文档**：打包脚本以前每次 build 都把 README / manifest 重写成 v1.0 模板，v1.5 起只在文件缺失时生成。

待实机验收（`FWPickFeature` 无法脚本同步驱动交互点击）：
- 点面板行 → 视口该组变青、标签变亮；
- 点「视口拾取边/面」后点一条圆角边 → 对应行打勾；点主体平面 → 提示非特征；
- 空勾选点「取消选中」→ 模型不变；点「保留全部」→ 模型不变；
- 勾选一组点「取消选中」→ 只删该组（连带组数命令行如实报出）。


## 11. v1.6 交互方案（2026-11-23 晚，E-024 之后 · **方案阶段，尚未编码**）

用户第三轮总结：「整体交互逻辑不清晰」「两边可以同时相互交互，而不是说去选择那一边」
「可以把它分成两个模块」「为什么不直接让那个面取消修剪，而是补那个面」。
本轮**只做诊断与方案**，未改插件代码、未编译、未打包（Rhino 进程在最后一组几何实验中崩溃）。

### 11.1 三个问题的几何 / 实现真相

| # | 用户问题 | 真相 | 依据 |
|---|---|---|---|
| 1 | 为什么只能在那个框里选，不能在原界面框选标红的？ | `FwFocusConduit.ObjectCulling` 剔除源对象 → 橙色面是 conduit 自绘**影子**，不是文档对象，Rhino 拾取不到；`FWPickFeature` 是一次性模态 `Get()`；面板还写死「同一时刻只允许一边有勾选」 | 源码 `FwFocus.cs` / `FwCancelPanel.cs`；E-024 |
| 2 | 分成两个模块；去除布尔必须先去圆角吗？ | **不必**。`RemoveHoles(指定内环)` 只删选中的孔，圆角完好：圆角盒+1孔 11 面 / 235922.14 → 10 面 / 239315.06。当前「去圆角会连带把孔抹平」来自 `Defillet` 把所有面外扩重缝，方向读反了 | E-024 真机实测 |
| 3 | 为什么补那个面，不直接取消修剪？ | **孔可以、圆角不可以**。孔 = 底层曲面 + trim 内环；圆角 = 新增过渡曲面，四边与邻面共享，`UntrimOuterLoop` 因外环边非 naked 恒 null。但当前孔洞通道用 `UntrimFace`（抹整面外环+全部内环）也是错的 | RhinoCommon.xml 官方 summary；官网 `trim.htm#UntrimHoles`；E-024 |

### 11.2 官方与主流界面给的范式（别自己发明）

- `UntrimHoles`：「Select hole edges individually. **Or use window selection**」+ `All` /
  `MaximumEdgeLength` / `KeepTrimObjects` —— 在**图形区框选**才是 Rhino 原生语义。
- SolidWorks FeatureWorks 交互识别：「select geometry **from the graphics area**」、
  `Chain fillet faces` / `Recognize similar`，选错可 `Select Other` / `Clear Selections`。
- Fusion 360 `Find Features`：框选 → 自动分组 → 列表 hover 高亮整组 → 直接改参数。
- vcad `Selection` 的 *Feature Tree Sync*：「**Multi-selection works in both directions**」，
  配 Hover Preview、Shift 加减选、点空白清空；Cognite 树导航还有节点高亮 + 自动缩放。

→ 共同结构 = **图形区直接操作 + 常驻树状面板 + 一份共享选中集，双向同步、可预览、可多选**。

### 11.3 v1.6 落地清单（待用户拍板）

1. **一份选中集** `HashSet<int>`：视口 / 树 / 面板共同读写，删掉「同一时刻只允许一边有勾选」。
2. **不进模态命令**：`FWSelect` 后挂 `Rhino.UI.MouseCallback`（`OnMouseDown`/`OnMouseMove`/
   `OnMouseHover`/`Enabled`）+ `RhinoDoc.SelectObjects` 静态事件；悬停预览、点选、框选、
   Shift 加减选全在原视口完成。已反射确认这些钩子在 Rhino 9.1 存在。
3. **保留源对象可拾取**：不再 `ObjectCulling` 整件剔除，改用子对象选择高亮
   （`GetObject.GetMultiple(1,0)` + `SubObjectSelect` / `RhinoObject.SelectSubObject`），
   否则「看得见选不中」仍在。
4. **两个独立执行器**：
   - 模块 B `取消布尔切割` → `Brep.RemoveHoles(选中内环对应的 ComponentIndex 列表, tol)`，
     只删选中的孔，外环 / 圆角 / 其它孔全留，可与圆角任意顺序。
   - 模块 A `去除圆角` → 删整圈过渡面 + 相邻面重新求交；**不再整件 `RepairToBlank`**，
     避免把孔一并抹平（若缝合仍需要孔体重放，须在命令行如实报出）。
5. **显式语义保留**：`保留全部` / `取消选中 N 项` / `全部取消`；N=0 拒绝执行；选中 ≠ 执行。
6. **可视化**：模型上继续画 F1…/H1… 编号标签，两个通道用不同颜色；hover 时整组描边预览，
   选中组青色、其余压暗；面板两个分区各自一个执行按钮，状态栏显示共享选中集。

### 11.4 开放项（如实标注，不许假装已验证）

- `UntrimBorder` 命令层「去外环保留内环」能否替代 `Defillet` 以彻底避免「补面」：未验证。
  尝试 `DuplicateSubBrep(剩余面)` + `UntrimOuterLoop` 连调时 Rhino 进程崩溃（slot armadillo
  pid 4396，槽被回收），按纪律未盲目重试。
- 常驻 `MouseCallback` 的实际事件参数、框选命中与性能：尚未编码实测。
- 用户提到的「turn number」未能在网上定位到确切软件/控件，本方案按主流 CAD 的
  特征树 / PropertyManager / 时间轴范式理解，**需向用户确认所指**。

---

## 12. v1.6 实现记录（已编码 / 已编译 / 已真机几何验证）

### 12.1 用户拍板（AskUserQuestion 选项回传）

```
v1.6 是否按「常驻双向联动 + 两个独立模块」这个方向落地？ → 按方案全做（推荐）
两个模块的执行语义要怎么摆？                          → 严格两模块、不要总开关
去圆角时如果缝合仍会连带影响孔，你希望怎么处理？      → 明确报出，不偷偷改（推荐）
```

§11.3 清单据此修正：第 5 点里的「全部取消」总开关**删除**；两个模块的按钮各自独立。

### 12.2 落地文件

| 文件 | 改动 |
|---|---|
| `src/FwSelection.cs`（新增） | `FwSelectionState` 一份共享 `HashSet<int>` + `FwMouseWatcher : MouseCallback` 常驻监听；`WorldToClient` 8 角投影屏幕矩形，点选 / 拖框 / Shift-Ctrl 加减选 |
| `src/FwFocus.cs` | `FwFocusGroup.Loops`（inner loop 索引）、`FwGroupVisual.Bounds`；`FindInnerLoops()` 用 `BrepTrim.Edge.AdjacentFaces()` 把孔洞组映射到内环；conduit 三态着色 + 拖框矩形；`Begin/End` 起停监听与选中集；修正过时几何注释 |
| `src/FwCancel.cs`（重写） | `CancelBoolean`（`RemoveHoles(指定内环)`）/ `CancelFilletModule`（整圈重缝 + collateral 明确报出）；`FwCancelRunner.TryApply(doc, module, targets, out msg)` 严格两模块、拒绝跨模块混选 |
| `src/FwCancelPanel.cs`（重写） | 删互斥勾选、删总开关；两个分区各一个执行按钮；订阅 `FwSelectionState.Changed` 双向同步 |
| `src/FwCancelCommand.cs`（重写） | 命令行 `BooleanRemove` / `FilletRemove`，沿用共享选中集或按组号 |
| `src/FwSelectCommand.cs` / `FwPickFeatureCommand.cs` | 常驻监听提示；`PickGroup` 改为写共享选中集 |
| `src/AssemblyInfo.cs` / `manifest.yml` | 1.6.0.0 |
| `verification/Compile_Roslyn.py` / `Build_Package.py` | FILES 加 `FwSelection.cs`；默认版本 1.6.0.0 |

### 12.3 编译与真机验证数字（本轮，不是推测）

- 进程内 Roslyn：**0 error**，rhp `103424 bytes`（v1.5 为 96256 bytes）。
  首轮 16 个错全是 `Point` / `Environment` 在 `System.Drawing`·`System` 与 `Rhino.*` 双定义（CS0104），
  加 `using Point = System.Drawing.Point;` / `System.Environment.NewLine` 后清零。
- 反射断言：版本 `1.6.0.0`、12 个类型齐全、两个执行器签名、
  `TryApply(RhinoDoc, String, List<FwFocusGroup>, String ByRef)`、`Loops`/`Bounds` 字段、
  `MouseCallback.Enabled` 继承存在。
- 纯几何（盒 + 2 孔，`8 面 / inner 4 / vol 233214.16`）：
  - `FindInnerLoops` 把 H1 → `[7,8]`、H2 → `[10,11]`，4 个圆角组 → 空（正确）；
  - 模块 B 只删 H1 → **`7 面 / inner 2 / vol 236607.08`**（H2 全留）；删两个 → `6 面 / inner 0 / 240000`；
  - 把 `Channel="Fillet"` 的组塞进布尔执行器 → 明确拒绝（严格两模块）。
- 纯几何（圆角盒 R3 `10 面 / 239315.06` + 1 孔 `11 面 / inner 2 / 235922.14`）：
  - 模块 B 只删该孔内环 `[11,12]` → **`10 面 / inner 0 / 239315.06`**，
    与纯圆角盒面数与体积逐项一致（`SAME_AS_FILLETED=True`）——**去布尔不需要先去圆角**；
  - 模块 A（用删孔壁面 + 完整曲面重缝模拟圆角重缝路径）→ `collateral=4`，
    结果消息原文含「【明确报出 / NOT silent】」，未做孔体重放。
- **发现并修复的真实 bug（E-025）**：`CancelBoolean` 初版用 `g.Type == FeatureType.Fillet` 过滤，
  而 `FeatureType` 枚举默认值恰好是 `Fillet`，导致孔洞组被误判成圆角、`RemoveHoles` 收不到任何内环。
  改为只认显式 `g.Channel`，`FwCancelRunner` 的跨模块校验同步改；重编译后全部通过。

### 12.4 仍待人工验收（如实标注）

- 常驻 `MouseCallback` 在真实 GUI 里的手感（拖框矩形、Shift/Ctrl、hover 预览、多视口）尚未实机点过：
  本轮 Rhino 是自动重开的空文档实例，交互命令按纪律不从脚本同步驱动。
- `e.Cancel = true` 接管左键后是否影响其它视口操作（右键旋转、gumball）：未实测。
- 「turn number」所指仍未确认。
- 真实 GUI 上的 v1.5 面板点选、v2.10 Alias 当前视口独立，也仍待用户重开 Rhino 后一并验收。

### 13. v1.6.1：失败安全与「全消失」症状（E-028，2026-11-23 深夜）

**用户原话**：「我选择去取消一条倒角边，结果所有东西全部消失了。」

**分层诊断（不重跑任务、先看现场）**：
- `get_context` / `list_objects(includeHidden=true)` → 文档仍有 `1 Brep（6 面 / solid / vol 39637.966）`
  + 3 条隐藏曲线；反射 `FwFocusSession.HasActive=False` / `FwMouseWatcher.IsActive=False` /
  `FwSelectionState.Count=0` / `SourceBrep=None`。**几何没被删光**，是显示/替换层症状。
- 活文档加临时 7 面单圆角边（`vol 63922.7433`）完整跑 `FWSelect → TryApply("Fillet")`：
  `TryApply ok=True`，读回 `6 面 / solid / vol 64000` / `hidden=False` / `visible=True` /
  `HasActive=False` → **标准路径不消失**，排除重建算法本身。
- 全边圆角盒 `66 面 / 63089.90` → 12 个 Fillet 组 → `6 面 / 64000`；
  单条 `BlendType.Chamfer` 倒角 `7 面 / 63820` → `Pass1_Fillets=0 / feats=0`（**新边界**：
  平面斜切倒角不在当前判据里）。

**四个确定缺陷 → 修复**：

| # | 缺陷 | v1.6.1 修法 |
|---|---|---|
| A | `ObjectCulling` 无条件剔除源对象，显示代理全失效时视口全空 | `FwFocusConduit.HasDrawableContent()` 护栏；`Begin` 无内容则 `conduit.Enabled=false`，模型照常显示 |
| B | `TryApply` 把 `End(doc)` 写在 `if (!outcome.Ok) return false` 之后，失败时 conduit 仍 cull | 改为「内存算完 + `ValidateResult` 通过才动文档」，`End` 移到 `Replace` 之前；失败/异常不写文档、不关聚焦 |
| C | `FWSelect` / `DoPick` 丢 `clean`，原始 brep 配 clean 的特征索引（`MergeCoplanarFaces+Compact` 可重排） | 一律 `Brep focusBrep = clean ?? brep;` 传给 `Begin` |
| D | 写文档前无结果有效性校验 | `ValidateResult`：面数>0 / `IsSolid` / 体积>0 且源 `0.02~50×` / 包围盒对角线 ≤ 源 `5×`；拒绝写入并原文报出 |

**编译与验证**：进程内 Roslyn **105984 bytes / 0 error / 65 warning**；
反射 `1.6.1.0`、`HasDrawableContent` 空→False / 塞入 10³ box→True、
`ValidateResult` 正常→None / null→拒绝 / 源自身→None；
纯几何回归 `7 面 / 63922.74 → 6 面 / 64000`；
yak `74374 bytes` sha256 `80d1f454…`，rhp sha256 `e93a8a0a…`，
真安装 `…\packages\9.0\特征识别工具\1.6.1.0\`（哈希与本地一致）。

**仍待人工验收**：重开 Rhino 后按同一模型点一次模块 A（当前进程仍是 1.6.0.0）；
单条 Chamfer 识别判据待扩展；实验在用户 Undo 栈留 2–3 条记录（临时对象已删）。
