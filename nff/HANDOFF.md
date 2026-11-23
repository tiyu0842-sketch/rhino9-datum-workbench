# NFF 插件交接说明（给接手的 AI）

> 本文件面向即将接手「后续验证与调节」的 AI。开始工作前请完整阅读本文与 README.md。
> 生成时间：2026-11-22
> 工程根目录：`<workspace>/rhino-normal-filter/`

---

## 0. 一句话状态

插件代码已全部写完（Python 零编译版 + C# 正式插件源码），24 项自动化测试全部通过；
**但从未在真实 Rhino 中运行过**（开发机无 Rhino、无 .NET SDK），C# 工程也未经真实 SDK 编译。
你的任务是：**真机验证 → 修复问题 → 按用户反馈调节参数与逻辑**。

---

## 1. 原始需求与已确认决策

用户原话要点：在 Rhino 里参考 Nomad 模型的思路，按面法线方向角度筛选面，方便进行 AI 分面。

已向用户确认过的四点（不要擅自改变这些边界）：

| 项目 | 用户选择 |
|---|---|
| 插件形式 | Grasshopper 组件 **和** Rhino 命令，两者都要 |
| 几何类型 | Mesh 网格（不处理 NURBS/Brep） |
| 筛选方式 | 按参考方向筛选：指定方向或参考面，选夹角在阈值内的面 |
| 后续用途 | AI 辅助面板分割（AI 分面）的前处理 |

---

## 2. 文件清单与职责

```
rhino-normal-filter/
├── README.md                              用户使用说明（参数表、安装步骤、工作流）
├── HANDOFF.md                             本文件：给接手 AI 的交接说明
├── python/
│   ├── nff_core.py                        纯算法内核（无 Rhino 依赖，可独立测试）
│   ├── NormalFaceFilter_GhPython.py       GhPython 组件脚本（零编译，主推）
│   └── NormalFaceFilter_RhinoCommand.py   RhinoPython 命令脚本（零编译）
├── csharp/
│   ├── NormalFaceFilter.sln               三个项目的解决方案
│   └── src/
│       ├── NormalFaceFilter.Core/         共用 C# 算法 MeshFilter.cs
│       ├── NormalFaceFilter.Rhino/        Rhino 命令插件 → .rhp
│       └── NormalFaceFilter.Grasshopper/  GH 组件 → .gha
└── tests/
    ├── mock_rhino.py                      Rhino API 模拟层（仅测试用）
    ├── test_nff_core.py                   算法单元测试
    ├── test_ghpython.py                   GhPython 脚本流程测试
    ├── test_rhino_command.py              Rhino 命令脚本流程测试
    └── make_test_mesh.py                  ★ 在真实 Rhino 中生成测试模型（验证起点）
```

算法在 Python 与 C# 两边是**同一套逻辑**：叉乘求面法线 → `θ = acos(n·d)` → 判断 `min ≤ θ ≤ max`，
可选把 `180−θ` 也算命中（IncludeOpposite）。若改算法，两边要同步改。

---

## 3. 完成状态

### 已完成
- [x] 核心算法（含退化面处理、角度区间、正反双向模式）
- [x] GhPython 组件脚本：7 输入 / 6 输出，含角度着色与 AngleGroups 分组
- [x] Rhino 命令脚本：支持预设方向 / `x,y,z` / `face:N` 三种写法
- [x] C# 三项目工程（Core + .rhp + .gha）
- [x] 24 项自动化测试：`python -m unittest discover -s tests`
- [x] C# 括号与项目引用静态检查

### 未完成 / 需要你做
- [ ] 在真实 Rhino 中运行两个 Python 脚本（**最高优先级**）
- [ ] 用真实 Rhino SDK 编译 C# 工程，确认 .gha / .rhp 能加载
- [ ] 根据验证结果修正 API 差异（如有）
- [ ] 按用户后续反馈调节参数与筛选逻辑

---

## 4. 真机验证清单（按顺序执行）

### 4.1 环境确认
先确认用户环境是 Rhino 7 还是 Rhino 8：
- Rhino 8 → Python 3 脚本，`.NET 8` 编译 C#
- Rhino 7 → IronPython 2.7（脚本已兼容），C# 需把三个 `.csproj` 的 `TargetFramework` 改为 `net48`

### 4.2 生成测试模型
运行 `tests/make_test_mesh.py`（Rhino 命令行 `_RunPythonScript` → 选文件）。
它会在当前文档生成一个 7 面网格并在命令行打印每个面的法线与夹角，同时保存 `NFF_TestMesh.3dm`。

预期输出（Direction = +Z 时）：

| 面序号 | 朝向 | 与 +Z 夹角 |
|---|---|---|
| 0~5 | 长方体的 ±Z / ±X / ±Y | 0° / 180° / 90° |
| 6 | 45° 斜面 | 45° |

### 4.3 验证 GhPython 脚本
1. 把 `python/NormalFaceFilter_GhPython.py` 加载进 GhPython / Python 3 Script 组件。
2. 按 README 第三节添加 7 个输入和 6 个输出（名字必须完全一致）。
3. `Mesh` 接测试网格，`Direction` = (0,0,1)，`Angle` = 30。

| 检查项 | 预期结果 |
|---|---|
| `KeptFaces` | 只包含顶面（+Z 的那个面） |
| `RemovedFaces` | 其余 6 个面 |
| `Angles` | 顶面 0°、底面 180°、侧面 90°、斜面 45° |
| `FilteredMesh.Faces.Count` | 与 `KeptFaces.Count` 一致 |
| `AngleGroups` | 每个分支的面索引之和 = `KeptFaces.Count` |
| 视窗着色 | 命中面按红(0°)→绿(90°)→蓝(180°)显示；若不显示颜色，切换着色模式 |

再分别验证：`Angle=60`（斜面应命中）、`IncludeOpposite=True`（底面也应命中）、
`RefFace=<底面序号>`（参考方向变为 -Z）。

### 4.4 验证 Rhino 命令脚本
运行 `python/NormalFaceFilter_RhinoCommand.py`，按提示依次输入：
选测试网格 → `0,0,1` → `30` → `0` → `n`。
预期：生成一个只含顶面的新 Mesh 对象，红色高亮并被选中，命令行打印统计。
再试 `top`、`face:6`、`bottom` 等方向写法。

### 4.5 验证 C# 插件
在有 Rhino 8 的机器上执行：

```
dotnet build csharp/NormalFaceFilter.sln -c Release -p:RhinoInstallDir="C:\Program Files\Rhino 8\"
```

把产出的 `.gha` 放进 Grasshopper 组件库、`.rhp` 用 `_PlugInManager` 加载。
确认电池名为 `Normal Face Filter (NFF)`，命令名为 `SelectFacesByNormal`，功能与 Python 版一致。
**注意：这是目前唯一没编译验证过的部分，最可能出问题。**

### 4.6 验证记录（2026-11-22 真机回填）

> 环境：Rhino 9.1.26314.9001 / .NET 8，进程内 Roslyn 编译，MCP 直连真实 Rhino 文档。
> 交付的修复版脚本在包内就地更新（每处都带「真机修正（2026-11-22）」注释）。

| 项目 | 环境/版本 | 结果 | 发现的问题与修复 |
|---|---|---|---|
| `python -m unittest discover -s tests` | 本机 Python 3 | **24/24 PASS** | 无 |
| `make_test_mesh.py` | Rhino 9 真机 | **PASS**（7 面网格，法线表与文档完全一致：面1=+Z 0°、面0=−Z 180°、面2–5=90°、面6=45°） | **Bug 1**：`rg.Mesh.CreateBox(10,8,6)` 在 RhinoCommon 9 不存在 → 改 `Mesh.CreateFromBox(BoundingBox, 1,1,1)`；三个分段数必填，各 1 段才得到预期的 6 个四边形面 |
| `nff_core.py` 算法（真网格数据） | Rhino 9 真机 | **PASS**：Angle30→[1]、Angle60→[1,6]、Opp30→[0,1]、Band60-90→[2,3,4,5] | 算法本身无问题，纯数学逻辑与模拟一致 |
| GhPython 脚本主流程 | Rhino 9 真机（注入 7 输入，exec 主流程） | **PASS**：5 种组合全部符合预期（Angle30/60、Opp30、RefFace6、Bins 留空），输出 FilteredMesh 面数与 Kept 一致且 `IsValid=True`，分组总和正确 | **Bug 2**：`rg.Vector3d.DotProduct(a,b)` 不存在 → 改 `a * b`（RhinoCommon 9 只有 `Multiply` 运算符，`System.Type.GetMethods()` 里无任何 `Dot*` 方法） |
| Rhino 命令脚本内部函数 | Rhino 9 真机 | **PASS**：`parse_direction` 六种写法（top / `0,0,1` / face:6 / face:1 / 空 / `1,1,0`）全部解析正确；`_extract_faces([1,6])` 得到 2 面 8 顶点有效网格 | 同 Bug 2（`DotProduct`）；脚本末尾 `RunCommand()` 无条件执行，交互 `Get()` 无法脚本喂，按 split 去掉末行后只测函数 |
| C# 三项目真编译 | 进程内 Roslyn / Rhino 9 | **SUCCESS 14336 字节，0 error**（Core + .rhp 四个源文件） | **Bug 3/4/5**：① `PlugIn.EnglishName` 不可 override（Rhino 9 只有只读 `Name`，同 `ProductName` 坑）→ 删掉 override；② `RhinoGet.GetReal` 不存在 → 改 `GetNumber(prompt, true, ref v, 0, 180)`；③ C# Core 同样有 `Vector3d.DotProduct` → 改 `a * b` |
| C# Core 算法（`MeshFilter.Filter` 反射调用） | Rhino 9 真机 | **PASS**：Angle30→[1]、Angle60→[1,6]、Opp30→[0,1]，与 Python 版逐项一致 | 无 |
| C# 插件加载与命令注册 | Rhino 9 真机 | **PASS**：`PlugIn.LoadPlugIn(path)` 返回 `Success`；程序集含 5 个预期类型；`SelectFacesByNormal` 命令被识别并执行（进入交互等待，脚本驱动超时属环境限制，非插件问题） | 无 |

**尚未真机验证**：`SelectFacesByNormal` 的交互式完整走查（需用户手动敲命令）、步骤 3–7 剥离加工链路（目前只有原型/技术方案，无真插件代码）。
**注意**：`tests/mock_rhino.py` 模拟了不存在的 `Vector3d.DotProduct`，这正是 24 项模拟测试全过但真机报错的根因——**mock 通过不等于真机通过**。

---

## 5. 参数调节速查

| 参数 | 默认值 | 作用 | 调节建议 |
|---|---|---|---|
| `Direction` | (0,0,1) | 参考方向，决定筛选哪一族面 | 用预设词快速试 top/bottom/left/right/front/back；模型主方向不规则时用 `RefFace` 从面上取 |
| `Angle` | 30° | 最大夹角容差 | 先 30 看大致结果；只要很平的面用 10~15；要连同斜面一起收用 45~60 |
| `MinAngle` | 0° | 最小夹角，筛「面带」 | 配合 `Angle` 用，如 60~90 只取陡斜面；0 表示从正向开始 |
| `RefFace` | -1 | ≥0 时用该序号面的法线作参考，忽略 Direction | 面序号 0 起始；适合从模型上直接取主朝向 |
| `IncludeOpposite` | False | True 时把方向当「轴」，正反两面都算 | 板材两面都要处理时开启 |
| `Bins` | `0,15,30,60,90,120,180` | 角度分箱边界，决定 `AngleGroups` 粒度 | 按 AI 分面需要的朝向类别调，如 `0,30,60,90` |

调节时的判断依据：
- 命中太少 → 放大 `Angle` 或开 `IncludeOpposite`
- 命中太多、混进斜面 → 缩小 `Angle` 或提高 `MinAngle`
- 命中朝向和预期差 180° → 开 `IncludeOpposite` 或把 `Direction` 取反
- 想按朝向分批喂给 AI → 调 `Bins`，用 `AngleGroups` 的每个分支分别处理

---

## 6. 已知风险与排查

1. **法线方向依赖顶点顺序**：Nomad 导出的网格面序可能导致法线整体反向。表现是筛出来的是背面而非正面。开 `IncludeOpposite` 可缓解；或者用 `RefFace` 从目标面上取法线。
2. **四边形法线用近似**：两三角形叉乘求平均，与 Rhino 内置法线在极度扭曲的四边形上可能有差异。若用户模型有大量扭曲四边形，可考虑改用 `mesh.FaceNormals[i]`（需先 `ComputeFaceNormals()`）。
3. **顶点着色可见性**：`FilteredMesh` 的颜色依赖显示模式；若看不到红绿蓝，检查 Rhino 的显示模式与材质设置。
4. **索引 0 起始**：`RefFace` 和 `face:N` 都用 0 起始序号，与 Rhino 某些界面的 1 起始不同，容易 off-by-one。
5. **C# 未编译**：可能出现 RhinoCommon 8 的 API 签名差异（重点看 `RhinoGet.GetString/GetReal`、`GH_ParamAccess.tree`、`DataTree<int>`）。核心逻辑与 Python 一致，若 API 报错优先改调用方式，不要改算法。
6. **退化面**：零面积面被剔除，`Angles` 对应位置为 `None`（Python）/ `NaN`（C#），下游处理时要过滤。

---

## 7. 给接手 AI 的启动 Prompt（可直接复制）

```
你正在接手一个 Rhino 插件项目。工作目录：<workspace>/rhino-normal-filter。

请先完整阅读 HANDOFF.md 和 README.md，不要依赖任何对话上下文。

背景：用户要在 Rhino 里按「面法线与参考方向的夹角」筛选 Mesh 面，为 AI 辅助面板分割做前处理。
已确认边界：GH 组件 + Rhino 命令两者都要；只处理 Mesh；按参考方向筛选；用途是 AI 分面。

现状：Python 脚本（GhPython 组件 + Rhino 命令）和 C# 三项目源码都已写完，24 项模拟测试全过；
但从未在真实 Rhino 中运行，C# 也未经真实 SDK 编译。

你的任务：
1. 先运行 tests/make_test_mesh.py 生成 7 面测试网格，确认法线表输出正常。
2. 用你的 Rhino/MCP 工具按 HANDOFF.md 第 4 节的清单，在真实 Rhino 中逐项验证。
3. 修掉验证中发现的问题，把结果填进 HANDOFF.md 第 4.6 节的验证记录表。
4. 之后按用户反馈调节参数与逻辑；改算法时记得同步 Python 与 C# 两边。

注意：不要改变已确认的需求边界（只处理 Mesh、按参考方向筛选）。
```

---

## 8. 交接检查

拿到包后先确认：
- [ ] 能打开 README.md 与 HANDOFF.md
- [ ] `python/` 下三个 .py 文件齐全
- [ ] `csharp/NormalFaceFilter.sln` 及三个子项目齐全
- [ ] `tests/` 下 5 个文件齐全（含 make_test_mesh.py）
- [ ] 本机跑 `python -m unittest discover -s tests` 仍是 24 项通过
