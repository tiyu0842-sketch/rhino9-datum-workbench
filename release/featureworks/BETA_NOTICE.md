> ## ⚠️ 此物料已作废（2026-11-23）
>
> 本目录的 `FeatureWorks_v2_0-beta.yak` 对应**方向走偏的 v2 实验分支**（备份对象恢复，非几何 untrim），
> **不得用于 Food4Rhino 发布或任何正式分发**。用户痛点与正确算法见
> [`../../featureworks/HANDOFF.md`](../../featureworks/HANDOFF.md)；正式包请使用
> [`../../featureworks/RhinoFeatureWorks_v1.3.2.0.yak`](../../featureworks/RhinoFeatureWorks_v1.3.2.0.yak)。
> 本目录仅作为「一次方向纠偏」的历史证据保留，以下为原文。

# FeatureWorks v2 — Beta 说明

> 这是**实验性预览版**。发布前请确认你接受下面的限制。

## 当前版本能做什么

- `FWPanel` 打开 Eto 停靠面板，完整交互：**识别 → 列表多选 → 视口高亮 → 统一处理**。
- 识别圆角（fillet）与倒角（chamfer）：三条几何判据（面类型 / 覆盖角 / G1 邻接），不依赖特征树。
- 处理：**删除**选中圆角面、**抑制**（原对象移到 `FW_Backup` 图层，可恢复）。
- 命令行版 `FWRecognize`：拾取 → 列出 → 高亮，不改原对象。
- 多核并行逐面计算，面数多时不会卡死主线程。

## 明确做不到（下一版才做）

1. **"还原"按钮尚未做真正的 Untrim** —— 当前通过备份图层恢复原对象，不是从几何上恢复被修剪的面。
2. **不识别圆弧** —— 圆弧是曲线（ArcCurve），本版只识别面特征。
3. **NURBS 近似圆角低置信度** —— 只有解析曲面（Cylinder/Torus/Sphere）高置信识别；网格重建的近似圆角标注"needs curvature fitting"，不默默猜。
4. **无 Grasshopper 组件** —— 只有 Rhino 命令 + Eto 面板。
5. **无工具图标** —— 敲 `FWPanel` 调用面板。

## 真机验证状态

Rhino 9.1：
- 识别——普通盒 0 特征、3mm 圆角盒 2 个 fillet（r=3, sweep=90°, conf=1.00）、带孔板 0（孔不误判）、chamfer 盒 1 个（conf=0.85）。
- 面板链路——实例化、识别→列表、选中→Session→高亮、删除处理→备份图层，全部 PASS。
- 编译 0 error，26112 字节。

> 面板最终显示需在真实 Rhino 里加载插件后敲 `FWPanel`——无界面脚本槽位无法验证停靠面板的呈现。

## 下一版路线

1. 还原按钮接真正的 Untrim
2. 圆弧识别（`Curve.TryGetArc`）
3. NURBS 曲率拟合降级
4. Grasshopper 组件 + 图标 + 工具栏

如果你只是想试"识别并批量删圆角"，这个 beta 可用；如果要完整的特征编辑闭环，请等下一版。
