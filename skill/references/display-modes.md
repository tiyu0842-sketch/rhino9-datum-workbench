# Rhino 9 显示模式：实测配方与判据

所有结论来自 Rhino 9 真机反射 + 固定相机逐像素采样。不要凭"看起来应该"调显示参数。

## 三个光照方案的本质区别

`DisplayPipelineAttributes.LightingSchema` 是**枚举不是 flag**：
`None=0 / DefaultLighting=1 / SceneLighting=2 / CustomLighting=3 / AmbientOcclusion=4`。
"DefaultLighting | AmbientOcclusion" 是无效值，方向光与 AO 只能二选一。

| 方案 | 内置例子 | 实际效果 |
|---|---|---|
| `AmbientOcclusion` | Arctic | 只有接触/凹角遮蔽，**没有受光面—侧光面—背光面的梯度**，曲面易"糊成一片" |
| `DefaultLighting` | Alias Style | 单盏头灯，白物体平面被直射打到 255 削平 → 过曝死白 |
| `SceneLighting` | Monochrome | 白物件 + 灰度明暗 + 黑轮廓，但 `FrontDiffuse=255` 同样易过曝 |
| `CustomLighting` | Shaded | 多盏方向光，能做连续明暗过渡，是真三度灰阶的来源 |

官方定义可直接引用：Monochrome = "all objects display white with gray scale shading, black silhouettes and edges"；Arctic = "uses Ambient Occlusion... all objects and background white"。NOVEDGE 的 white-model / 白黑材质法同样强调靠方向光的光流读曲率、白色基色别给满 255、关高光、AO 只能补充。

## 亮度旋钮：哪个属性真的有效

Rhino 9 管线下：
- `FrontDiffuse` / `FrontMaterial.DiffuseColor` / `ObjectColor` 对**带材质对象**实测不生效（连改 4 组取值，采样点 RGB 一个字节不变）。
- `AmbientLightingColor` 在 AO 方案下是唯一亮度旋钮（amb=0x37 → 受光约 200 / 背光约 112）。
- **CustomLighting 下真正有效的 albedo 旋钮是 `UseCustomObjectMaterial = true` + `FrontMaterial.Diffuse`**（注意类型是 `DisplayAttributeMaterial`，`ShineIntensity` 是 int，写 0.0 会 CS0266）。这一点很容易漏试。

## 已验证的两套配方

**三度灰阶 clay（v2.6 定稿，取代纯 AO）**
- 母版：`Shaded`（自带 CustomLighting 多灯），**不要**从 Alias Style/Arctic 复制
- `LightingScheme = CustomLighting`
- 浅色：`FrontMaterial.Diffuse = 0xC0`，`AmbientLightingColor = 0x0A`，背景 `#B9BEC2 → #8F979C`，等参线 `#505C66`，边缘 `#2B2B2B`
- 深色：albedo `0xA8`，ambient `0x0A`，背景 `#2B3134 → #3C4448`，等参线 `#8FA8B4`，边缘 `#B2BCC2`
- `IgnoreHighlights = true`，`FrontMaterial.Shine = 0`，`ShineIntensity = 0`
- 阴影**关闭**：CustomLighting 的方向光会把地面阴影拉成大片深色椭圆，实测比无阴影更抢视线
- 实测：albedo 0xC0 / ambient 0x0A → 物体区 P10=101 / P50=119 / P90=152，三度跨度 51，纯白 ≥250 占 0.00%

**纯 AO 白模（旧方案，仅作对照）**
- `AmbientOcclusion` + `UseCustomObjectColor=true`，物体色 `0xB4`，ambient `0x30`
- 实测 `clip(≥253)=0.00%`、max=214，但**平面上方下没有明暗梯度**，只靠 AO 和等参线读结构

## 等参线（结构线）

- 显示模式开关：`ShowIsoCurves = true`，颜色统一 `SetSurfaceIsoColorUsage(SingleColorForAll)` + `SurfaceIsoUVColor/UColor/VColor` 同色（只设 UVColor 会漏出默认红绿线）。
- 密度是**对象属性** `ObjectAttributes.WireDensity`，不是显示模式属性：0 = 仅边界，1 = 一条内部等参线，N ≥ 2 画 N+1 条。
- 两套主题可用密度区分：浅色 0（最干净）、深色 1（一条内部线）。切换时必须**强制设置**目标值，不能只补低值，否则切回来会残留。
- 改密度用 `obj.Attributes.WireDensity = n; obj.CommitChanges()`。命令里优先改选中对象，否则改全部 Brep/Surface/Extrusion。

## 阴影与背景

- 只投影地面：`ShadowsOn + CastShadows + CustomGroundPlaneOn + CustomGroundPlaneAutomaticAltitude + CustomGroundPlaneShadowOnly`，`ShadowSoftEdgeQuality=4`、`ShadowEdgeBlur=10~14`。
- 这套在 AO 方案下能提供接地感；在 CustomLighting 下方向光会把影子拉长成大块深色椭圆，建议关掉。
- 背景要比物体亮面**暗**，白模才不会和背景糊在一起。`Gradient2Color` + `SetFill(top, bottom)`，不用纯白/纯黑。

## 调参判据（不要只看图）

- `clip(≥253)` 百分比 + `max`：画面不该出现成片纯白。过曝的标准是 clip 2%~10%、max=255。
- 三度跨度：物体区 P90−P10，越大层次越清楚；同时盯 std。
- 抓图必须用真渲染帧，否则所有候选看起来一模一样，会得出错误结论。见 `verification-playbook.md`。
- 参数扫描要一次只改一个变量，候选数控制在 4~6 组；做完立刻删临时显示模式。

## 其他显示技巧

- 斑马纹 `VisualAnalysisMode.RhinoZebraStripeAnalysisModeId` 可用 `RhinoObject.EnableVisualAnalysisMode` 打开，但黑白满量程比 clay 刺眼，只适合短时查 G0/G1/G2。
- 线框视口下材质透明度不生效；要靠虚线线型 + `SetDisplayModeOverride(Ghosted)` 区分对象。
- 行业基准面配色是棕/琥珀（Creo 153,102,51；本项目 176,132,70），紫色在 Creo 是"铣削体积块"不是基准面。
