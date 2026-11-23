# FeatureWorks v2 — 几何特征识别（Rhino 9 / .NET 8）

按外包技术规格**全新实现**的第一版：识别实体上的圆角（fillet）与倒角（chamfer），列出结果并在视口高亮。

## 已确认的边界（不要推翻）

1. **Rhino 没有特征树** —— 所有"特征"都是几何反推，不做参数化 Suppress
2. **圆弧 ≠ 圆角** —— 本版只做**面特征**（fillet/chamfer），圆弧（曲线）留待下一版
3. **多核并行** —— 逐面计算走 `Parallel.ForEach`，文档操作回主线程（本版只识别不改文档）
4. **本版范围**：识别 + 列出 + 高亮；删除/抑制/还原三种处理留待下一版

## 几何判据（三条互相印证）

| 判据 | 做法 | 为什么 |
|---|---|---|
| 面类型 | `Surface.TryGetCylinder/Torus/Sphere/Plane` | 圆角是过渡曲面，chamfer 是平面 |
| 覆盖角 | 参数域跨度 / 半径（**Rhino 9 参数域是弧长不是弧度**） | 圆角约 90°，完整柱孔约 360°——这是区分圆角与孔的关键 |
| 邻接 G1 | 共享边中点两法线夹角 < 8° | 圆角与两侧母面相切；只 1 个邻居的不算 |
| chamfer | 平面 + 窄条（短边/长边 < 0.6）+ 与两邻面成 25~65° | chamfer 是平面斜面，与曲面圆角判据不同 |

**覆盖角的大坑**：圆柱圆角面的 U 域是**轴向**（如 -3..63，长 66），V 域才是**周向**（0..4.712 = 3π/2）。
取 `max(degU,degV)` 会把轴向 1260° 截断成 360°，误判成孔；必须取 `min`。

## 实测结果（Rhino 9.1.26314.9001 真机）

| 测试模型 | 预期 | 实测 |
|---|---|---|
| 普通盒子（6 面） | 0 个特征 | 0 ✓ |
| 倒 3mm 圆角的 100×80×60 盒子 | 识别出 2 个圆柱圆角面 | 2 个 fillet-edge，r=3，sweep=90°，conf=1.00 ✓ |
| 带 φ10 圆孔的板 | 孔不能误判成圆角 | 0 ✓ |
| chamfer 盒 | 识别出倒角平面 | 1 个 chamfer，conf=0.85 ✓ |
| 完整球体 / 完整圆柱 | 封闭面，不算圆角 | 0 ✓ |

编译：进程内 Roslyn，4 个源文件，**0 error，15360 字节**。

## 真机抓到并修复的 API 差异（RhinoCommon 9）

1. `BrepFace` 没有 `Edges` → 用 `AdjacentEdges()` 返回 int[]，再索引 `brep.Edges[i]`
2. `BrepFace.ClosestPoint` 只有三参重载 `(Point3d, out u, out v)`
3. `PlugIn.EnglishName` 不可 override（只有只读 `Name`）
4. `RhinoApp.WriteLine` 没有格式参数重载 → 先 `string.Format`
5. 曲面参数域是弧长，覆盖角 = 跨度 / 半径（不是弧度）
6. `BlendType` 枚举值是 `Fillet`/`Chamfer`/`Blend`，不是 `RollingBallBlend`
7. `RailType` 是 `RollingBall`/`DistanceFromEdge` 等

## 命令

`FWRecognize` —— 拾取实体 → 输入 r_max 比例（默认 0.05×对角线，可调 0.001~1.0）→ 命令行列出特征 → 视口临时高亮（红=边圆角，蓝=顶点圆角，橙=倒角）。原对象不改动。

## 文件

- `src/FwCore.cs` —— 识别引擎（纯计算，可并行，反射可测）
- `src/FwCommands.cs` —— `FWRecognize` 命令层
- `src/FwPlugin.cs` —— 插件入口（GUID `3C9E7A15-8B42-4D6F-A0E3-7F15B2C9D840`）
- `src/AssemblyInfo.cs` —— 版本 2.0.0.0
- `FeatureWorks_v20.rhp` —— 真编译产物

## 下一版待做

- 三种处理：删除圆角 / 抑制（移出可恢复）/ 还原到切割前
- 圆弧识别（曲线类：`Curve.TryGetArc` / `ArcCurve`）
- NURBS 近似圆角的曲率拟合降级路线（标注低置信度）
- Yak 打包安装（本版只编译验证，未安装）
