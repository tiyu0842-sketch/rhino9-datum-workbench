# FeatureWorks 交互与实现规格 v1.5 草案

> 2026-11-23 晚｜状态：**待实机验收后编码**，本轮不改插件代码、不动 Rhino 显示模式
> 来源：用户手绘草图 + 全网调研（出处见 §7）+ 现有 v1.4.0 源码核对 + 真实 Rhino 9 只读探活
> 分工：`使用手册.md` 是用户向说明；技能包 `feature-recognition.md` 第 8 节是方法论；**本文件是实现规格**。

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
