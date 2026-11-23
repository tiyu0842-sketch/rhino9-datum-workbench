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

v1.2（识别/证据/修复基线，9/9 自测 PASS）→ v1.3.0（交互闭环）→ v1.3.1（鬼影自愈）→ **v1.3.2**（ObjectCulling 真半透明，yak 真安装）。
rhp 88576 bytes / 0 error / 46 warning；`RhinoFeatureWorks_v1.3.2.0.yak` 48422 bytes，装到 `…\packages\9.0\特征识别工具\1.3.2.0\`。**装完必须重开 Rhino**。

## 7. 下一版待做（从痛点出发，不重写）

1. 孔体重放：只取消圆角、保留孔（几何已验证可行）
2. 框选 sub-object + 特征面白名单
3. 圆弧识别、NURBS 曲率降级
4. GH 组件、工具栏 RUI / 图标
