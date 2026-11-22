# 基准面工具 v2.8（Rhino 9 / .NET 8）

在斜面上建立基准面并锁定工作坐标系：三点定面或拾取平面 → 生成半透明基准面 → CPlane 与操作轴对齐 → 像在顶视图一样建模。保存的基准面随 `.3dm` 保留，退出时精确还原最初的工作平面与操作轴。

> **v2.8：两套 Alias 观测显示用「结构线密度」区分开**
>
> 按你定的分配：**浅色 `I` → 密度 0**（只画裸边，画面最干净）；
> **深色 `J` → 密度 1**（每条曲面多一条内部等参线，深色底上刚好能读曲面走向）。
> 两套模式一眼就能分辨，不用靠背景色猜。
>
> 实现上有个必须注意的点：旧版 `Apply` 的逻辑是「把密度低于 2 的补到 3」，
> 那会导致从深色切回浅色时对象上残留的 1 降不回 0，两套模式就区分不开了。
> v2.8 改成**强制设置到目标值**（`SetAllWireDensity`，浅 0 / 深 1），来回切换始终各归各位。
> 这只是对象的显示属性，随时可以用 `AliasStyle → Density`（菜单 `K`）改成 2~4 继续加密。
>
> 实测：同一个曲面对象，`I` 应用后 `WireDensity=0`，再 `J` 应用后变成 `1`，
> 再切回 `I` 又回到 `0`（不是只增不减）；命令行也会回报本次设成的值。

> **v2.7：`B` 选平面不再需要 Ctrl+Shift，直接点面上任意位置就行**
>
> 旧版提示「组合多重曲面上按 Ctrl+Shift 直接点面」，等于把一个多余的操作塞给用户。
> 查了 McNeel 官方资料后确认，Rhino 原生 `ExtrudeBrepFace` / `ExtractSrf`（抽离曲面、抽离结构线）
> 的做法是：`GetObject.GeometryFilter` **只给 `ObjectType.Surface`** +
> `SubObjectSelect = true` + **`DisablePreSelect()`**，点哪个面就直接拿到哪个面，不需要任何修饰键。
> 旧版写了 `Surface | Brep`，`Brep` 会让顶层对象抢先被选中 —— 这就是必须按 Ctrl+Shift 的根因
> （McNeel 论坛「How to Select Surface Subsets via GetObject Without Ctrl Key」与官方示例一致）。
>
> 现在两种交互**整合到一次点选**：
> 1. 直接点实体/多重曲面上的平面面片 → 拿到该面（主路径）。
> 2. 若 Rhino 仍返回整个对象（不同版本/挤出物件等情况）→ 用**点击位置**在这个 Brep 里
>    找距离最近的**平面**面片（跳过圆角/曲面），等效「点哪取哪」。
> 3. 单独平面曲面、多面实体、老习惯按 Ctrl+Shift 精确选面，三种情形走同一套逻辑。
>
> 基准面仍取所选面的**面积质心**为原点、UV 为 X/Y、法线为 Z（v2.0 起的精度改进不变）。
> 抽出来的定位函数 `FindPlanarFaceNear` 是 `internal`，实测：在 6 面盒子上点顶面中心 → 返回 +Z 面；
> 点前面中心 → 返回 −Y 面；点圆角/圆柱面 → 返回 null（提示改点平面）。

> **v2.6 显示模式重做：从「纯 AO 白模」改成「方向光三度灰阶」**
>
> 你说的「糊成一片、没有明暗灰三度」是对的，而且是我上一版选错了技术路线。
>
> **查到的资料**（McNeel 官方 + 社区）：
> - 官方对 **Monochrome（单色）** 的定义就是「所有物件白色显示，带有**灰度明暗**、黑色轮廓和边缘」；
>   而对 **Arctic（极地）** 的定义是「用环境光遮蔽生成阴影，全部物件和背景设为白色」——
>   v2.4 走的正是 Arctic 这条路，只有接触/凹角遮蔽，**没有受光面—侧光面—背光面的明暗梯度**。
> - 官方 Lighting scheme 文档：`DefaultLighting` 是单盏头灯，`CustomLighting` 最多 8 盏自定义方向光，
>   `AmbientOcclusion` 是独立一套。反射实测 `LightingSchema` 是**枚举不是 flag**（0/1/2/3/4），
>   所以「方向光 | AO」这种组合值根本无效，二者只能二选一。
> - NOVEDGE 的白/黑材质法（white model / form evaluation）同样强调：靠 **方向光的光流与灰阶** 看曲率、
>   白色基色别给到 255、关掉高光避免 glare、AO 只能当补充且不能过量。
>
> **改法**：母版从 `Alias Style` 换成 `Shaded`（它自带 CustomLighting 的多盏方向光）→
> `LightingScheme = CustomLighting` 给连续明暗 →
> `UseCustomObjectMaterial = true` + `FrontMaterial.Diffuse = 0xC0` 把最亮面压住 →
> `AmbientLightingColor = 0x0A` 让暗部不死黑 →
> `IgnoreHighlights / Shine = 0` 去掉刺眼高光 → 等参线 + 轮廓线保留。
> 另外把背景压到 `#B9BEC2 → #8F979C`（比物体亮面暗），白模才不会和背景糊在一起。
>
> **逐像素扫描结果**（球 + 圆环 + 圆柱 + 方块，固定相机，浅色主题）：
>
> | albedo / 环境光 | P10 | P50 | P90 | 三度跨度 | 纯白 ≥250 |
> |---|---|---|---|---|---|
> | `0x90 / 0x14` | 90 | 106 | 127 | 37 | 0.00% |
> | `0xA8 / 0x14` | 98 | 119 | 148 | 50 | 0.00% |
> | **`0xC0 / 0x0A`（定稿）** | **101** | **119** | **152** | **51** | **0.00%** |
> | `0xA8 / 0x22` | 104 | 121 | 150 | 46 | 0.00% |
>
> 深色主题 `#2B3134 → #3C4448` + albedo `0xA8` 同样三度清楚。
>
> **刻意关掉了投影阴影**：CustomLighting 的方向光会把地面阴影拉成大片深色椭圆，
> A/B 实测（阴影强度 15~18）比完全没有阴影更抢视线；三度灰阶 + 轮廓线 + 等参线已经够表达体积。
> 这是从 v2.4 的「地面软阴影是主要好看来源」反转过来的结论 —— 换了光照方案后这个加成变成了干扰。
>
> 顺带修正了 v2.4 的一个误判：`FrontDiffuse / ObjectColor` 对带材质物体不生效没错，
> 但**真正能改亮度的不是只有 AmbientLightingColor**，而是
> `UseCustomObjectMaterial + FrontMaterial.Diffuse`（上一版漏试了这一对）。

> **v2.5 修掉了「退出后 Front 视图是歪的」**
>
> **现象**：退出基准面模式后，Front 视图的网格和红绿轴斜着摆，但左下角世界坐标三脚架还是正的 —— 说明**相机没歪，歪的是该视口的工作平面（CPlane）**。
>
> **根因**：v1.6 起基准面 CPlane 会「跟随活动视口」，你点过几个视口就往几个视口里写；
> 但退出时只有 `ActivePlane` 一个基线 + 一个 `ViewportId`（每次迁移都被覆盖成最后一个），
> 于是在 Front/Right 里写进去的基准面 CPlane 没有记录、也没人还原，永久留在那里。
> 更糟的是：即使还原，把 Top 的平面写回 Front 本身也是错的 —— 每个视口该有自己的原平面。
>
> **修法（v2.5）**：
> 1. **逐视口存档**：第一次改写某视口 CPlane 前，把它原本的平面按视口 Id 存进文档字符串 `SavedCPlanes`
>    （顺带存视口名，文件重开后 Id 失效就用唯一名字兜底；存进 `.3dm`，中途保存重开也照样还原）。
> 2. **逐视口还原**：退出时遍历存档，各回各家 —— Front 回 `X=(1,0,0) Y=(0,0,1)`，Right 回 `X=(0,1,0)`，不再全塞同一个平面。
> 3. **兜底自愈**：退出末尾再扫一遍，凡是「CPlane 仍然等于某个基准面」的视口，
>    按它自己的相机反推标准朝向并矫正（判据很窄，只碰确实带着基准面的视口，不会动你手工设的 CPlane）。
> 4. **模式已关时按 `JZ` → `H` 也会自愈**：旧版留下的歪视图现在一条命令就能救回来，不用重开文件。
> 5. 第 5 视窗「基准面法向」例外：它的相机本来就垂直于基准面，退出时**保留**其 CPlane，
>    否则网格会和镜头错开、反而是歪的。
>
> 实测（新旧两套状态各跑一遍）：旧文件「Front 残留倾斜平面」→ `H` 后 Front 恢复 `X=(1,0,0) Y=(0,0,1)`；
> 模式开启且 Front/Right 都被盖过 → 两个视口同时各自还原；视口 Id 失效时按名字兜底也通过。

> **v2.4 显示模式（已被 v2.6 取代，保留作技术记录）：不照抄 Alias Style，改成"环境光遮蔽白模"**
>
> 三条实测结论（逐像素采样，不是推测）：
>
> 1. `FrontDiffuse` / `FrontMaterial.DiffuseColor` 对**带材质**的物体完全不生效 —— 连改 4 组取值，采样点 RGB 一个像素都不变。
> 2. `DefaultLighting` + 白色物体 = 平面被直射光打到 **255 削平**，这就是"高曝光、看不出结构"的唯一来源（v2.1/v2.2/v2.3 都有）。
> 3. 唯一有效组合：`LightingScheme = AmbientOcclusion` + `UseCustomObjectColor = true`；
>    并且**赋值顺序**必须是 `ObjectColor` → `UseCustomObjectColor`，反过来会被重置回 false（和等参线 `Set*` 重置总开关是同一类坑）。
>
> 改后实测：全画面 `max = 231`、纯白像素 **0.00%**（旧版 2.3%~9.5% 的像素是纯白）；
> AO 让凹角、圆角过渡、相接处自然变暗，再叠加等参线 + 轮廓线 + 只投影地面的软阴影，
> 就是产品设计圈做 clay / 白模（白模渲染）的通行配方。
>
> | | 浅色 `Alias EyeCare` | 深色 `Alias EyeCare Dark` |
> |---|---|---|
> | 背景 | 冷调浅灰渐变 `#CFD2D5 → #B0B6BB` | 暖石墨 `#2B3134 → #3C4448` |
> | 物体 | 单色 `#B4B4B4`（AO 着色） | 单色 `#A0A0A0` |
> | 环境亮度 | `#303030`（唯一有效的亮度旋钮） | `#2A2A2A` |
> | 等参线 | 石板蓝灰 `#646E78`，1px | 浅蓝灰 `#8FA8B4`，1px |
> | 阴影 | 软阴影，只投影地面，强度 55 / 模糊 10 | 强度 70 / 模糊 12 |
>
> 副作用（要知道）：AO + 单色会把**所有**物体统一成灰白模，基准面在 Alias 显示下也是灰色（透明仍在），
> 想看棕色基准面按 `M` 还原显示即可。
>
> 另：试过直接开 Rhino 的斑马纹（`VisualAnalysisMode` Zebra），条纹对比天然是黑白满量程，
> 屏上比哑光灰刺眼得多，只适合短时间查 G0/G1/G2 连续性，所以没放进默认模式。

> **v2.1 配色调整**：
> 1. **基准面颜色改为行业棕**（`RGB 176,132,70`，Creo/SolidWorks/CATIA 基准面正面色系），
>    半透明 55% 不变；线框/Ghosted 下的边线也同步变棕，不再偏蓝或发黑。
> 2. **Alias 浅色模式对齐原版**（已被 v2.2 取代：原版 219/116 就是过曝来源）。

> **v2.0 新增两点**（你提的优化）：
> 1. **选平面面片建基准面**：直接点某个平面面片（像抽离曲面一样，不用先抽离；v2.7 起也不用 Ctrl+Shift）；
>    基准面**原点自动落在面的面积质心**，**X/Y 沿该面 UV 方向**、**Z 为法线**，
>    不再因为点击位置而偏移。斜面也精确对齐。
> 2. **单独关闭第 5 视窗**：`JZ` → `N`（或独立命令 `DatumPlaneNormalViewClose`），
>    只把第 5 视窗关掉、恢复标准 4 视图，不影响基准面/CPlane。

> **v1.9 重要变更：`JZ` 只列基准面命令（A–H），不再混入 Alias 显示风格。**
> 两类命令已彻底分开：`JZ` / `DatumPlane` 只管基准面；显示风格请用独立命令
> `AliasStyle`（I–M）、`AliasStyleLight`、`AliasStyleDark`、`AliasStyleRestore`，
> 你可以给这些独立命令另设别名或工具栏按钮，互不干扰。

> **v1.8 新增命令别名 `JZ` + 字母菜单**：主命令有了短别名 `JZ`（"基准"拼音首字母），输入 `JZ` 即可唤起**统一菜单**，一次列出全部效果。每个选项改成「**固定字母代号 _ 英文简写 = 中文 / English**」的形式，例如 `A_3Point=三点定义新基准面 / Define plane by 3 points`——**中文完整保留在后面**，前面是字母与英文简写；命令行里敲那个带下划线的字母就能直接选中效果，不必再输完整英文单词。三个入口（`JZ` / `DatumPlane` / `AliasStyle`）共用同一套字母代号，记一次到处能用。

> **v1.7 新增「Alias 观测显示」，v2.4 重做为环境光遮蔽白模**：以 Rhino 9 内置 `Alias Style` 为母版复制（继承管线默认值），但参数全部重调——低饱和渐变背景（浅灰 / 暖石墨两套）、**曲面等参线**看走向、AO 单色白模不死白、只投影地面的软阴影、轮廓线 + 裸边细线。一键切、一键还原，命令 `AliasStyle`（v1.8 起同样用字母菜单），工具栏第 8/9 个按钮。

> **v1.6 修好了「已有基准面」卡死**：激活状态下可以直接定义**新**基准面、或切换旧基准面，不再被迫先还原。同时移除了「必须切回启用时的视口」限制——在任何视口（包括新增的第 5 视图）里都能切换/还原。
>
> **v1.6 新增第 5 个视图「基准面法向」**：垂直分割 Top 视图，新视口相机**垂直于当前基准面**（视线沿法线、Up = 平面 Y 轴、平行投影），基准面正对镜头，可以像顶视图一样在斜面上建模。切换基准面时它自动跟随。

**从 v1.5 卡住的状态脱困**：如果你现在正卡在「已有基准面模式，请先还原」——先输入 `DatumPlaneRestore`（或 `JZ` → `H`）退出，再装 v1.6+。装好后这个提示不会再出现。

**v1.5 起中英双语**：命令行指引、选项描述、错误提示均为「中文 / English」并列。选项关键字受 Rhino 限制只能是字母数字，所以中文说明放在等号后面，字母与英文简写放在前面。

**v1.3 显示区分**：基准面用**虚线边线 + 蓝色 + Ghosted 幽灵显示**，`SetDisplayModeOverride(Ghosted)` 让对象无视视口模式，线框下它自己仍是半透明。

插件 GUID `8B7C4E52-6F3A-4C1D-9A2E-5D8F0B3C7E14` 与程序集名**保持不变**，覆盖安装后工具栏按钮绑定不失效。

---

## 安装（重要：用 `.yak`，不要用 `.rhi`）

**.rhi 装不了本插件**：老式 `RhiExec` 用 .NET Framework 反射检查 net8 的 `.rhp`，会抛 `FileLoadException: System.Private.CoreLib`，界面报「package is not compatible with the Rhino Installer Engine」。McNeel 官方明确 `.rhi` 是遗留格式，net8 插件请用 yak。

**正确方式**（本版已用官方 `Yak.exe` 真实安装验证）：

1. 保存模型并**关闭 Rhino**。
2. **双击 `DatumPlane_v2_1.yak`** —— Rhino 9 包管理器会装它。
   - 备用手动方式：Rhino 命令行 `PlugInManager` → Load → 选 `install/DatumPlanePlugin.rhp`。
3. 重开 Rhino，输入 **`JZ`**（或 `DatumPlane` / 中文 `基准面`）。第一次测试请用新建临时文档。
4. 若仍显示旧工具栏：`Toolbar` → 打开 `DatumPlanePlugin.rui` → 点亮「基准面工具」灯泡。工具栏仍是 **9 个按钮**（v1.9 的改动全在 `.rhp` 里，不新增按钮）。

## JZ 别名与字母菜单（v1.9：只含基准面 A–H）

`JZ` 是一个**真正的插件命令**，等价于 Rhino 的命令别名，但随 yak 安装/卸载自动生效，不会偷偷改写你自己的 `Options → Aliases` 设置。若你希望在别名面板里也看到它，可手动加一条 `JZ → JZ`（或 `JZ → DatumPlane`）。

命令行显示形如（等号前是字母代号与英文简写，等号后中文 / English 并列）：

```
基准面 / Datum plane（回车取消 / Enter=cancel）：
A_3Point=三点定义新基准面 / Define plane by 3 points
B_Plane=拾取平面对象定义新基准面 / Pick a planar object
...
```

Rhino 会自动把选项名里**第一个未被引用的字母**当作加速键并加下划线；因为每个选项首字母 A…M 全局唯一，加速键就固定是那个字母，**敲 `A`、`B`、`I`… 即选中**，也可以直接点命令行超链接，或输入完整英文简写。

**固定字母代号表**（三个入口共用）：

| 字母 | 选项关键字 | 效果 |
| --- | --- | --- |
| `A` | `A_3Point` | 三点定义新基准面（激活态下也可用） |
| `B` | `B_Plane` | 拾取平面对象定义新基准面（激活态下也可用） |
| `C` | `C_Pick` | 点选已有基准面切换（锁定子层也可点） |
| `D` | `D_Recall` | 按编号调用已保存的基准面（不重复建几何） |
| `E` | `E_Save` | 把当前工作平面存为命名基准面 |
| `F` | `F_Lock` | 继续保持当前基准面坐标系 |
| `G` | `G_NormalView` | 第 5 视图「基准面法向」，垂直分割 Top，相机垂直于基准面 |
| `H` | `H_Restore` | 退出并还原到最初的工作平面与操作轴 |
| `I` | `I_Light` | 浅色 Alias 观测显示（哑光灰+等参线） |
| `J` | `J_Dark` | 深色 Alias 观测显示 |
| `K` | `K_Density` | 设置曲面等参线密度（看清走向） |
| `L` | `L_Status` | 查看当前显示状态 |
| `M` | `M_RestoreStyle` | 还原为启用观测显示之前的显示模式 |

三个入口的区别只在**列出哪些效果**，字母含义完全一致：

| 命令 | 别名 | 列出的效果 |
| --- | --- | --- |
| `JZ` | "基准" | **仅 A–H + N 基准面命令**（显示风格已移出，推荐） |
| `DatumPlane` / `基准面` | 原名 | A–H（仅基准面） |
| `AliasStyle` | 原名 | I–M（仅显示风格） |

**直接回车**：基准面已激活时 = 还原；否则 = 取消（显示风格菜单直接取消）。

**独立命令全部保留**（工具栏按钮 / 脚本宏直接调用，不受字母菜单影响）：

`DatumPlanePick` / `DatumPlaneRecall` / `DatumPlaneSave` / `DatumPlaneLock` / `DatumPlaneRestore` / `DatumPlaneNormalView` / `AliasStyleLight` / `AliasStyleDark` / `AliasStyleRestore`

**典型工作流**：`JZ` → `A` 定斜面 → `G` 开出法向视图 → 干活 → `JZ` → `A` 再定一个斜面（法向视图自动转过去）→ 或 `C` 点旧基准面切换 → `AliasStyle` → `I` 换浅色观测看清曲面走向 → `JZ` → `H` 还原。全程只记一个命令 + 几个字母。

## 第 5 视图：基准面法向视图

- 用 Rhino 9 原生 `SplitViewportVertical` 把 **Top 视图沿竖直分割线一分为二**（左半保留 Top，右半成为新视口），因此是「Top 垂直分割出的第 5 视图」。
- 新视口调用 `RhinoViewport.SetToPlanView(origin, XAxis, YAxis, false)`：实测 `CameraDirection = -Normal`、`CameraUp = YAxis`、`CameraTarget = Origin`（点积 1.0），再切**平行投影**，并 Zoom 到基准面矩形。CPlane 单独设为该基准面，不影响其他视口。
- 视口名 `基准面法向`，识别靠「文档字符串 `NormalViewId` + 视口名」双保险；文件重开后 Id 可能变，名字兜底。**该 Id 不随 Restore 清除**，重复运行只复用、不会越拆越多。
- 每次创建/切换/调用基准面，法向视图自动重新对齐到新平面。
- `Restore` 保留视图本身，但把它的 CPlane 一起还原。

## Alias 观测显示（v1.7 起，v2.2 重做着色）

参考 Alias 建模的显示观感做的一套显示模式，解决两件事：**看久了不刺眼**、**能一眼看出曲面走向与结构**。

|     | 浅色 Light（默认推荐）            | 深色 Dark                   |
| --- | ------------------------- | ------------------------- |
| 背景  | 冷调浅灰渐变 `#CBD0D5 → #A6ACB3` | 暖石墨渐变 `#2B3134 → #3C4448` |
| 曲面  | 哑光灰 `#A6A6A6`，Shine 24     | 哑光灰 `#9E9E9E`，Shine 22   |
| 环境光 | `#464646`                 | `#4A4A4A`                 |
| 等参线 | 石板蓝灰 `#4A5A68`，1px        | 浅蓝灰 `#8FA8B4`，1px        |
| 曲线  | `#1E1E1E`                  | 薄荷 `#9ED8C6`              |
| 裸边  | `#1E1E1E` 细线              | `#B2BCC2` 细线              |

要点：

- **母版取自 Rhino 9 内置 `Alias Style`**（`DisplayModeDescription.CopyDisplayMode`），不是空壳新建，Rhino 的管线默认值全部继承，损坏风险低；机器上没有该模式时回退 `Shaded`。
- **不吃到 255 是硬指标**（v2.4 已实测达成）。判据只有一条：**画面上不该出现成片纯白**。v2.1 抄内置的 `Diffuse 219 + Ambient 116 + Shine 128` 时纯白占 2.3%~9.5%；v2.4 改 AO + 单色后纯白 0.00%、最高 231。
- **等参线是核心**：内置 Alias Style 默认关掉了 `ShowIsoCurves`，本版两套主题都显式打开并统一成一种柔和单色（U/V 双色实测在着色管线下不稳定）。
- **密度会自动补**：套用观测显示时，`WireDensity < 2` 的曲面统一补到 3 —— 密度 1 的单跨曲面根本不出内部等参线，看起来像"没开"。要改回或换档位用 `AliasStyle → K`。
- **不画内部边线**，只留裸边（naked edge）1px 细线，贴近 Alias 的干净曲面。
- **构建平面网格会自动关掉**：网格线在浅色/深色下都抢视觉，Alias 工作区默认也没有网格。还原时按视口逐个恢复原来的网格显示状态。
- **斑马纹没做成默认**：Rhino 的 `VisualAnalysisMode` Zebra 条纹天然是黑白满量程，屏上比哑光灰刺眼得多，适合短时间查 G0/G1/G2 连续性，不适合长期开着看形。

命令：

| 命令 | 作用 |
| --- | --- |
| `AliasStyle` | 字母菜单：`I` 浅色 / `J` 深色 / `K` 密度 / `L` 状态 / `M` 还原 |
| `AliasStyleLight` | 直接套用浅色观测 |
| `AliasStyleDark` | 直接套用深色观测 |
| `AliasStyleRestore` | 把各视口还原为首次启用前的显示模式 |

**等参线密度**：显示模式只能控制线的样式，密度在对象上（`ObjectAttributes.WireDensity`，0–10）。套用时会自动把 <2 的补到 3；`AliasStyle → K` 可手动改，优先改选中曲面、没有选中就改全部曲面。

**还原是精确的**：首次应用前把每个视口原本的显示模式 Id 与网格可见性记进文档字符串 `DatumPlane.AliasStyle.Original`，`M` / `AliasStyleRestore` 按视口逐个还原（模式 + 网格状态），不会把别的视口一起改掉。

## 图层结构与防误触

```
基准面                  ← 顶层父图层（不锁定）
 ├── DP_01  [锁定]      ← 第 1 个基准面，含半透明矩形
 ├── DP_02  [锁定]      ← 第 2 个基准面
 └── …
```

子图层靠 `Layer.UserString` 标记识别（不靠名字前缀），不会误认用户自建的 `DP_01`。构造顺序：先建未锁子层 → 加几何 → 命名平面保存 → 状态激活 → **全部成功后才锁定**。实测锁定子层上 `doc.Objects.Delete` 返回 `False`；`GetObject.LockedObjectSelect = true` 仍可拾取。

## 数据模型

平面坐标由 **`NamedConstructionPlanes`** 单一管理；几何 `UserString` 只存 `DatumPlane.Kind` / `Name` / `Layer` 三个标记。点选到基准面时读 `Name` → `Recall(name)`，不在几何上再存 9 个 double，避免双数据源不一致。

文档字符串状态：`Active` / `ActivePlane`（进入模式前的唯一恢复基线）/ `ViewportId` / `LockedPlane` / `SavedName` / `Version`，另加不随还原清除的 `NormalViewId`。

## 保存与恢复边界

- 几何、命名构造平面、原构造平面、法向视图 Id 存在文档中，随 `.3dm` 保存；插件不会替你保存模型。
- 操作轴开关/对齐、自动复位、自动 CPlane、通用构造平面属于**应用全局偏好**，快照在当前进程会话中；重开文件不会用旧文件的应用偏好覆盖今天的设置。
- 命名平面是建立时的坐标快照，手工移动蓝色矩形不会自动更新它。

---

## 验证状态

- **v1.6 实机 44/44 PASS**（干净 Rhino 9 进程，进程内 Roslyn 编译 + 反射驱动真实文档端到端）：激活态再建基准面、跨视口切换、Top 分割、相机 `dot(dir,-N)=1.0`、自动跟随、精确还原全部通过。详见 `verification/Verify_v16.py`。
- **v1.7 全链路 PASS**：`Wireframe → Light → Dark → Light → Restore(Wireframe)`，网格状态 `True→False→True` 精确还原；浅/深两套实拍见 `evidence/alias_v17_light2.jpg`、`alias_v17_dark2.jpg`。
- **v1.8**：编译 0 错误；命令注册、字母代号表、菜单范围、字母命中与全命令回归见 `verification/Verify_v18.py` 与 `REVIEW.md` 第 10 节。

**仍未实机跑到**（工具环境限制，需你点一遍）：鼠标三点/选面、`GetObject.Get()` 交互本身、不同显示模式下的透明度观感、保存重开、撤销重做、空闲事件持续锁定。

## 从源码编译

本机没装 .NET 8 SDK，但 Rhino 9 自带 Roslyn 且 AppDomain 里已加载全部 RhinoCommon 引用，因此用**进程内编译**（产物与运行环境严格一致）：

在 Rhino 9 的 Python 3 里执行：

```python
p = r"<WORKSPACE>/skill/scripts/Compile_Roslyn.py"
exec(compile(open(p, encoding="utf-8").read(), p, "exec"))
```

9 个源文件 → `DatumPlanePlugin.rhp`。若装有 .NET 8 SDK，也可 `dotnet build src/DatumPlanePlugin.csproj -c Release`。

## 可调参数

| 常量 | 值 | 位置 |
| --- | --- | --- |
| `ViewWidthRatio` | 0.32 | `DatumPlaneCore.cs`，基准面边长 / 视图宽度 |
| `DatumTransparency` | 0.55 | `DatumPlaneCore.cs`，0 不透明，1 全透明 |
| `LayerName` | `基准面` | `DatumPlaneCore.cs` |
| `ViewName` | `基准面法向` | `DatumPlaneNormalView.cs`，第 5 视口名 |
| `DP_` 前缀 / `D2` | `DatumPlaneLayers.cs` | 子图层编号格式 |
| 字母代号表 `Entries` | A–M | `JzMenu.cs`，改字母即改加速键 |

## 文件清单

| 文件 | 作用 |
| --- | --- |
| `DatumPlane_v2_1.yak` | **双击安装包**（Yak 官方格式，zip + manifest.yml） |
| `DatumPlanePlugin.rhp` / `.rui` | 编译产物与 9 按钮工具栏（根目录与 `install/` 各一份） |
| `src/*.cs` | 9 个源文件，v1.9 调整 `JzMenu.cs` 中 JZ 的菜单范围 |
| `verification/Compile_Roslyn.py` | 进程内 Roslyn 编译脚本 |
| `verification/Build_Package.py` | 工具栏校验 + yak 打包 |
| `verification/Verify_v16.py` / `Verify_v18.py` | 端到端回归脚本 |
| `REVIEW.md` / `evidence/build_and_verify.log` | 审查结论、API 核对与验证证据 |
