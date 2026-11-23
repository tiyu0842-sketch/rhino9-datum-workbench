# Rhino 9 命令体系与插件开发对照（2026-11-23）

> 配套：`rhino-command-index.md`（1256 条全量索引）｜脚本：`scripts/Export_Rhino_Commands.py`
> 本文件是**精讲 + 判断**，不是帮助页抄录。官方原文要点均来自当次抓取，未核实的 API 一律标注「未实测」。

## 0. 数据来源与可信度

| 项 | 事实 |
|---|---|
| 全量命令名 | 运行中 Rhino **9.1.26314.9001**，`Command.GetCommandNames(True, False)` → **1256** 条；`loaded=True` → 1052 条 |
| 反射签名 | `GetCommandNames(Boolean english, Boolean loaded) -> String[]`（另有 `IsCommand` / `LookupCommandId` / `LookupCommandName`） |
| 官网单页 | `https://docs.mcneel.com/rhino/9/help/en-us/commands/<小写命令名>.htm`，**需带浏览器 UA** 才 200；`zh-cn` / `zh-tw` 同路径有中文版 |
| 官网无全量索引 | `index.htm` 只有 1225 字节（跳转页），`commands/` 目录 **403**；`Untrim` / `UntrimHoles` 是 `trim.htm` 的**锚点**，不是独立页 |
| 主题分类页 | `.../seealso/sak_*.htm`，例 `sak_splittrim.htm`（分割与修剪）、`sak_boolean.htm`（布尔） |
| 本次抓取 | 51 个页面下载成功，34 个含有效正文；原始 HTML/正文缓存在工作区 `_tmp/rhino_cmd_pages/` |
| 本机离线帮助 | 无完整命令手册，只有 `RhinoScript.chm` / `RhinoIronPython.chm`；`Content/XML/<lang>/` 是模板与材质等资源，不是命令文档 |

**会话缓存陷阱**：命令名表里仍有 `FW2Panel`（已降级的 v2 实验线），而当前进程并未加载该插件。
→ **命令名存在 ≠ 插件已加载 / 面板已注册**。这与 E-016「程序集枚举不能判安装状态」是同一类错误，别再用来下结论。

## 1. 先纠正期待：命令文档 ≠ 内核原理

用户问「懂了命令的原理和构造，做插件是不是方便很多」——**会方便，但不是因为命令文档讲了原理**。

- 1256 条命令里，`Brep` 关键词命中 **0**；没有 `RecognizeFeatures`、`DeleteFeature`、`FeatureTree` 之类。
  命令层是**用户操作层**，B-rep 的面/边/trim loop 是**内核层**，帮助页基本不讲后者。
- 真正决定实现质量的是 **RhinoCommon API + 几何语义**（我们 `feature-recognition.md` 第 8/9 节那套）。
  只背命令，最多会敲，不会写插件。
- **但这一层确实省钱，有实证**：
  - E-016：我只盯 `Brep.UntrimFace` API，漏了命令层 `UntrimHoles`，误判「loop 级手术无现成 API」。
  - 本轮：官方 `DeleteFaces` 自带 face loop 整圈选取，正是我们要自己造的交互；`FilletEdge` 原文直接给第 8 节的几何结论背书。
- 所以正确用法是**三层对照**：`命令（用户习惯/官方语义）↔ RhinoCommon API（可编程）↔ B-rep 几何（为什么这样）`。
  补上第一层能少走弯路、少造轮子；但三层齐了才叫「懂了构造」。

> 另一条诚实话：把 1256 条平铺塞进上下文不是「学习」，是 noise。做成**可检索索引 + 相关族精讲**才符合「省 token」。
> 这也是为什么拆成两份文档：索引只查、精讲才读。

## 2. 官方白纸黑字的九条（直接改变实现判断）

| 命令 / 页 | 官方原文要点 | 对我们的影响 |
|---|---|---|
| `SetObjectDisplayMode` | *"Their display in other viewports won't be affected."*；`ClearAllObjectDisplayModes` 移除所有 per-view / per-object 覆盖 | **逐视口独立是官方行为**，用户喜欢的 Alias 全视图联动必须自己遍历 `doc.Views` 逐个设，不能指望一个命令 |
| `SynchronizeCPlanes` / `CopyCPlaneToAll` / `CopyCPlaneSettingsToAll` | 同步**工作平面**到各标准视图；*"User-defined views do not change"* | 全视图联动原生只存在于 CPlane 域，显示模式域没有对应命令 → 印证 A 线判断 |
| `FilletEdge` | *"creates a tangent surface between polysurface edges ... then **trims and joins the original faces** to the fillet surfaces"*；双击边选相切边、`ChainEdges` 按连续性连选 | **官方背书第 8 节**：倒角 = 新增过渡曲面 + 原面被裁小；「圆角必须整圈一起删」有官方交互原型 |
| `MakeHole` | *"projects selected closed curves to a surface or polysurface to define hole shapes"*；方向选项 `X/Y/Z` / `NormalToCurve` / `CPlaneNormal` / `AlongCurve` | 印证孔 = 宿主面内环；「孔体重放」的官方语义原型 |
| `Trim` / `seealso/sak_splittrim` | *"A trimmed surface has two parts: a surface that underlies everything ... and trimming curves"*；*"Every trimmed surface retains information about its underlying surface geometry."* | 官方对 B-rep **两层结构**的表述，与我们给用户的图一致；可引官方原文而不仅是实测推断 |
| `ShrinkTrimmedSrf` | *"Only the underlying untrimmed surface alters."*、*"You will see no visible change."* | 同上，两层结构的第二个官方证据；对我们的 `UnderlyingSurface()` 路径是佐证 |
| `DeleteFaces` | *"removes selected faces from a mesh, SubD or **Polysurface**"*；单击面 → 双击相邻面定 loop 方向；`Ctrl+click` 剔单面、`Ctrl+double-click` 剔整圈；支持 sub-object filter 预选 | **圆角整圈选取可直接复用官方交互语义**，不必自造；官方还建议在着色模式下直接点面 |
| `CreateSolid` | *"creates a closed polysurface ... from selected surfaces ... that bound regions"*；*"expects overlapping and intersecting surfaces"*；`DeleteInput` 选项；**History enabled** | 对应 `Brep.CreateSolid(pieces, tol)`；官方说明输入必须相交包围，解释了 `RepairToBlank` 为什么要重缝 |
| `History` | *"stores the connection between a command's input geometry and the result so that when the input geometry changes, the result updates"*（例：改 Loft 输入曲线，曲面更新） | Rhino **有** history，但它是**父子几何关联（construction history）**，不存「在边 E 上倒 R5」的操作意图 → **不是 SW 特征树**，第 8 节论断不变但表述要精确 |

## 3. 与 FeatureWorks 直接相关的命令族

### 3.1 取消修剪 / 恢复毛坯（核心，官方 `sak_splittrim` 定义）

| 命令 | 官方语义 |
|---|---|
| `Untrim` | 移除曲面修剪边缘；选项 `保留修剪物件=是/否`、`所有相同类型` |
| `UntrimAll` | 取消所有内部洞 **及** 边界修剪边缘 |
| `UntrimBorder` | 只取消**边界**修剪边缘，**留下所有内部孔** |
| `UntrimHoles` | 只取消**选取的内部洞**，**留下所有边界**修剪边缘 |

配套：`SelTrimmedSrf` / `SelUntrimmedSrf`（按修剪状态筛选）、`ShrinkTrimmedSrf` / `ToEdge`、`RefitTrim`（把 trimmed edge 换成 untrimmed edge，需该边跨越完整 U/V 域，`EditKnots` 降偏差）、`ReplaceEdge`。

> 这组是 E-016 已确认的「路径 2 精确保留」官方依据。**API 层 `Brep.UntrimFace` 是整面级，命令层是 loop 级** —— 这个差异必须记住。

### 3.2 删面 / 重缝（对应我们的 `RepairToBlank`）

`DeleteFaces`（含 face loop）· `ExtractSrf`（`Copy` / `JoinOutput` / `OutputLayer`，可从多重曲面分离或复制面）· `DupFaceBorder`（复制面边界为曲线）· `RebuildEdges`（Explode 后恢复被拉离曲面的 3D 边）· `CreateSolid` · `MergeSrf`（只合并 **full-span 且 untrimmed** 的边，否则先 shrink；`Smooth` / `Tolerance` / `Roundness`）· `MergeAllCoplanarFaces` · `SplitFace`（用等参线 `U/V/Both` 或曲线分割面，`Pull/Project`）· `WireCut` · `Cap` · `Join` / `Explode`。

### 3.3 正向生成（「孔体重放」要重新执行的操作）

`FilletEdge` / `ChamferEdge`（`ChainEdges`、`NextRadius`、双击相切边）· `VariableFilletSrf` · `MakeHole` · `BooleanDifference` / `Union` / `Intersection` / `Split` · `OffsetSrf` · `WireCut` · `BlendSrf` / `MatchSrf`（**混接拟合新 NURBS 面，无原生可回退**，第 8 节诚实边界）。

### 3.4 选择 / 框选 / 子对象（对应界面草图「手动框选」）

`Sel*` 共 **140** 条。重点：`SelFaceLoop` `SelEdgeLoop` `SelEdgeRing` `SelChain` `SelConnected` `SelCrossing` `SelFence` `SelBox` `SelBrush` `SelBoundary` `SelFacesToBoundary` `SelParents` `SelChildren` `SelTrimmedSrf` `SelUntrimmedSrf` `SelObjectsWithHistory`。

> 用户草图里的「手动框选 / 界面辅助选择」不必从零做：官方已有 fence / crossing / brush / loop / chain 一整套选取范式，面板照这个语义设计即可。

### 3.5 显示 / 视图 / 面板

`SetDisplayMode` · `SetObjectDisplayMode` · `ClearAllObjectDisplayModes` · `DisplayProperties` · `ExtractIsocurve` / `MoveExtractedIsocurve` · `Snapshots`（官方说明会保存显示模式、材质、灯光、锁定/隐藏状态等）· `SynchronizeCPlanes` · `Toolbar` / `ShowToolBar` / `PopupToolbar` / `ToolbarLock`。

> `Panel` 关键词只命中 3 条，**全是我们的 FW 面板** —— Rhino 没有通用的「面板命令」，面板注册只能走 `Panels.RegisterPanel`（且类必须有类级 `[Guid]`，见 E-015）。

### 3.6 建模历史（别误读）

`History` · `HistoryUpdate` · `HistoryPurge` · `SelObjectsWithHistory` · `SelObjectsWithBrokenHistory` · `CommandHistory`。这是 construction history，不是参数化特征树。

## 4. 命令 → API → 我们插件（只列已实测过的 API）

| 官方命令 | RhinoCommon（已实测） | 插件里 |
|---|---|---|
| `Untrim` / `UntrimHoles` | `Brep.UntrimFace(int, double)`（整面级）；逐 inner loop 需自建或用 `RunScript` | `FwCancelService` 孔洞通道 |
| `CreateSolid` | `Brep.CreateSolid(pieces, tolerance)` | `SurfaceEvidenceService.RepairToBlank()` |
| `ExtractSrf` / 分组显示 | `Brep.DuplicateSubBrep` + `DisplayConduit` / `ObjectCulling` | `FwFocusSession` 分组绘制 |
| 删面重缝 | `BrepFace.UnderlyingSurface().ToBrep()` | 圆角通道 |
| `SetDisplayMode` | `DisplayModeDescription.GetDisplayModes()` / `Viewport.DisplayMode` | 基准面工具显示模式 |
| 面板 | `Rhino.UI.Panels.RegisterPanel` + 类级 `[Guid]` | `FwCancelPanel` / `FwPanel` |

> 未在上表出现的对应关系，一律先反射 `RhinoCommon.xml` 确认再写，**不要凭命令名猜 API**（E-016 教训）。

## 5. 对 v1.5 的具体影响（转成决策）

1. 圆角「整圈选取」参照 `DeleteFaces` 的 face loop 语义（单击 → 双击定方向 → Ctrl 剔除），面板加「整圈 / 单面」开关，而不是自创手势。
2. `FilletEdge` 的 `ChainEdges` 与双击相切边，印证「圆角整圈一起删」；识别阶段可用相切链作为 hint（第 9 节）。
3. 精确保留路径优先复用 `UntrimHoles` 的逐孔选边语义（E-016 已记），孔体重放仍作主路径。
4. A 线显示模式联动：**必须自己遍历所有视口设 `DisplayMode`**，官方 `SetObjectDisplayMode` 明确只影响当前视口。
5. Rhino 自带 `History` 只是父子几何关联，**不能**用来做特征树；进一步坐实第 8/9 节。
6. `ExtractSrf` / `RebuildEdges` / `MergeSrf` / `CreateSolid` 是删面重缝路径的官方工具箱，与我们 `RepairToBlank()` 一一对应 —— 写文档时可引官方语义解释算法。

## 6. 检索纪律（下次怎么用这两份文档）

1. 想做某个操作 → 先查 `rhino-command-index.md`：有没有现成命令？在哪一族？
2. 有 → 抓对应官方页确认**选项与输入类型**（URL 模式见 §0），再看本文件 §4 有没有已实测的 API。
3. 能用命令层就用 `RhinoApp.RunScript`；但**交互命令不能脚本同步驱动**（硬约束 3），业务仍要拆成 Core 反射验证。
4. 没有现成命令 → 再查 `RhinoCommon.xml` 反射找 API，并补进 `rhinocommon-pitfalls.md`。
5. 每次因此改变判断 → 回填 `experiment-log.md`，别让结论只活在对话里。

## 7. 复现方法

```text
# 1) 全量命令名（在 Rhino 9 的 Python 里 exec）
scripts/Export_Rhino_Commands.py      # 输出 rhino_commands_all.txt

# 2) 官方单页（需浏览器 UA；索引目录 403 是正常的）
curl -L -A "Mozilla/5.0" \
  "https://docs.mcneel.com/rhino/9/help/en-us/commands/deletefaces.htm"
# 中文版：把 en-us 换成 zh-cn 或 zh-tw
# 主题分类页：.../seealso/sak_splittrim.htm、sak_boolean.htm
# 注意 Untrim/UntrimHoles/UntrimAll/UntrimBorder 都在 commands/trim.htm 的锚点里
```

本次已抓取并核对正文的 34 页：`trim` `deletefaces` `splitface` `split` `extractsrf` `mergesrf` `rebuildedges` `refittrim` `shrinktrimmedsrf` `replaceedge` `booleandifference` `booleanunion` `filletedge` `chamferedge` `makehole` `createsolid` `cap` `blendsrf` `matchsrf` `offsetsrf` `shrinkwrap` `wirecut` `dupfaceborder` `dupborder` `dupedge` `explode` `join` `extractisocurve` `rebuild` `setobjectdisplaymode` `displayproperties` `synchronizecplanes` `toolbar` `history` + `sak_splittrim` `sak_boolean`。


## 补录：`UntrimHoles` 官方原文（2026-11-23 抓取，E-024）

来源 `docs.mcneel.com/rhino/9/help/en-us/commands/trim.htm#UntrimHoles`（官网 9 版 `new9` 标记）。

> **UntrimHoles** — untrims selected holes (interior trims) that do not touch surface borders.
> This command also untrims the holes in polysurfaces.
> Steps: 1) Run the command. Or **preselect hole edges with Shift+Ctrl** before the command runs.
> 2) **Select hole edges individually. Or use window selection.**
> Options: `All` / `MaximumEdgeLength`（Type a maximum edge length number, or pick an existing hole edge
> to set the length. Holes with edges equal to or smaller can be deleted individually or all at once）/
> `KeepTrimObjects`。

同页命令族对照（交互语义，别再混）：

| 命令 | 作用 | 对内环（孔） |
|---|---|---|
| `Untrim` | 移除选中边界的 trim 曲线与相连曲面 | `AllSimilar=Yes` 时点一个即去掉所有孔；`=No` 只去相连的一段/单个孔 |
| `UntrimAll` | 一次去掉内外全部 trim | 全去 |
| `UntrimBorder` | 只去**外环** trim | **保留**（「Interior trims (holes) will remain」） |
| `UntrimHoles` | 只去**内环** trim | 逐个 / 框选 / `All` / 按边长筛 |

→ **命令 ↔ API ↔ 几何三层对照补一条**：
`UntrimHoles` ↔ `Brep.RemoveHoles(IEnumerable<ComponentIndex>, double)` ↔ 只删指定 inner loop，外环与底层曲面不动。
`UntrimBorder` ↔ `Brep.UntrimOuterLoop(int)`（但 API 多了「外环所有边必须 naked」的硬限制，实体上恒 null）↔ 只去外环。
`UntrimAll` ↔ `Brep.UntrimFace(int,double)` ↔ 外环 + 全部内环一起抹。
之前 E-018 记的「API 层只有整面级」是**错的**，已由 E-024 修正。

**交互启示**：官方给孔的选择方式就是**在图形区点选/框选**，不是列表勾选；
这是 v1.6 常驻双向联动面板的直接依据。
