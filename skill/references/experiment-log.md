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

## 统计与复用提示

- 截至 2026-11-23：**12 条实验**，其中 **6 条推翻了初始假设**。高推翻率说明「先验证再相信」不是口号。
- 查坑顺序：`error-catalog.md`（按症状）→ 本台账（按实验编号，看结论演化）→ 专题文档（按领域）。
- 新实验编号顺延；若结论修正旧条目，在本条写「修正 E-XXX」并在旧条补一行指向，不删改旧记录。
