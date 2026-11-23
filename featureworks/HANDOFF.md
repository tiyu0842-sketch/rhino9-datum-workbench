# FeatureWorks 交接说明：什么是对的，什么是走偏的

> 这份文档记录**一次代价不小的方向纠偏**。技术上都成功，但有一个分支解决了错误的问题。
> 留下来是为了让下一个接手的人（或下一次的自己）不用重走，也是"先验证需求、再验证代码"的实证。

## 一句话结论

**`featureworks/`（本目录，v1.3.2）是正式实现；`featureworks-v2/` 是已降级的实验记录，不代表目标。**

## 用户真正要的是什么

痛点原话：倒完角 / 布尔完，想重新倒或再编辑时**得手工备份**，很麻烦。

所以目标是：
> 选中一个**没有历史、只有 B-rep** 的实体 → 判断哪些面被改过（trim / 布尔 / 倒角）→
> **删除这些特征 → 几何上恢复成可重新编辑的毛坯**。

像 SolidWorks FeatureWorks 那样识别、删除、再编辑。关键词是**几何 untrim 回毛坯**，不是"把对象藏起来再搬回来"。

## 三个走偏方向（都真实发生过）

| 分支 | 实际做的 | 为什么不对 |
|---|---|---|
| `featureworks-v2/` | 按解析面类型 + 覆盖角挑 fillet/chamfer 面 → `Faces.RemoveAt()` 删面 + `FW_Backup` 图层备份 → 还原备份对象 | 这是**备份对象恢复**，几何没回到毛坯；`FwSession.cs` 自己都注明"不是几何 Untrim"。痛点未解决 |
| 只做识别 + 列出 + 高亮 |  picking → list → highlight | 识别是手段，**取消**才是目的。少了取消，等于没做 |
| 当成 NFF 法线筛面 | 按法线方向过滤面 | 那是分面前处理，另一个任务。用户明确指出过"这两个是不同的人物（任务）" |

更关键的一点：**旧 `FeatureWorks/` v1.2 本来就实现了用户本意**（`FwSurfaceEvidence.Analyze()` / `RepairToBlank()`），
却在方向不清时另起炉灶写了 v2。真机复检 v1.2 是 9/9 PASS。
> 教训：动工前先确认「已有实现是不是本来就对」，别重复造轮子。

## 正式线的关键几何结论（真机实测）

Rhino B-rep 的面 = 完整底层曲面 `UnderlyingSurface()` + trim 环。布尔/打孔/倒角**只改 trim，不动底层曲面**。
证据信号：`innerLoops > 1`（内环=孔/槽）、`overhangZ > 0.5`（底层曲面比 trim 长）、`reversed`（布尔减内表面）。

**圆角与孔洞必须用两套算法**——这是用户事先的判断，被 API 证实：

| | 孔洞 / 槽 | 圆角 / 倒角 |
|---|---|---|
| 本质 | 宿主面 trim 多了内环 | 一圈全新过渡面 |
| 取消 | `Brep.UntrimFace(host, tol)` 抹内环 | `UntrimOuterLoop` **一律返回 null**（外环边全被邻面共享）→ 只能删整圈过渡面 + `UnderlyingSurface().ToBrep()` + `Brep.CreateSolid()` 重缝 |
| 实测 | 7 面 → 6 面 **240000**；孔+槽 12 面 → 11 面 **224000** | 只删 1 个 → 9 面 **74715.5**（变形）；删全部 4 个 → 6 面 **75000** |

完整链：`229667.59`（R6 圆角 + R9 孔）→ 取消孔 `237301.66` → 取消圆角 `240000`。

已知边界（命令输出里对用户明说，不藏）：
- `UntrimFace` 会抹掉宿主面**全部**内环：同面多孔会一并恢复。
- 取消圆角是整件重缝，同件孔/槽会被一并恢复。「只去圆角、保留孔」需孔体重放（几何已验证 `240000 → 236607.08`），列入下一版。

## 交互（v1.3 定版）

`FWSelect` 点实体 → 识别 → **除特征外全部半透明（锁定语汇）**、特征面实心橙 →
面板按**圆角通道 / 孔洞通道**两列勾选（因为两套算法不同，必须分通道）→ 取消 → 自动重新识别重开聚焦，可连续取消 →
整段一个 Undo 记录。命令：`FWSelect` / `FWFocus` / `FWCancel` / `FWCancelPanel`。

显示层两个大坑（详见 `skill/references/feature-recognition.md` §4）：
1. 往不透明实体上叠透明灰 = **假半透明**。必须用 `DisplayConduit.ObjectCulling` 剔除源对象再画自己的子 Brep。
2. 特征面画 `PostDrawObjects` 会被深度剔成线框 → 改 `DrawForeground`；conduit 缓存子面索引会留"鬼影" → 静态文档事件 + 包围盒指纹自愈。

## 版本与验证

| 版本 | 内容 |
|---|---|
| v1.2.0.0 | 识别 / 证据 / 整体修复基线，`FwSelfTest.Run()` **9/9 PASS** |
| v1.3.0.0 | `FWSelect` / `FWFocus` / `FWCancel` / `FWCancelPanel` 交互闭环 |
| v1.3.1.0 | 鬼影自愈（静态事件 + `Stale()`） |
| **v1.3.2.0** | `ObjectCulling` 真半透明；rhp **88576 bytes / 0 error**；yak 真安装到 `…\packages\9.0\特征识别工具\1.3.2.0\` |

- 编译：本机无 .NET SDK，走 Rhino 进程内 Roslyn（`verification/Compile_Roslyn.py`）。
- 验证脚本：`verification/Probe_*.py`（逐条探测 API 行为）、`Verify_Engine.py`、`Build_Package.py`。
- 逐条实验记录（含被推翻的假设）：`skill/references/experiment-log.md` E-004 ~ E-012。

## 下一版（从痛点出发，不重写）

1. 孔体重放：只取消圆角、保留孔
2. 框选 sub-object + 特征面白名单
3. 圆弧识别、NURBS 曲率降级
4. GH 组件、工具栏 RUI / 图标
