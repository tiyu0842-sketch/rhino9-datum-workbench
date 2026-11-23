# Normal Face Filter (NFF) — Rhino 法线方向筛选面插件

在 Rhino / Grasshopper 里按「面法线与参考方向的夹角」筛选 Mesh 面，把命中面提取成独立网格，作为 AI 辅助面板分割（AI 分面）的前处理工具。

模拟 Nomad 里那种「按法线朝向选面」的思路，做成了 Rhino 里的两种载体：**Grasshopper 组件** + **Rhino 命令**，另外附一套可直接编译成正式 `.gha` / `.rhp` 的 C# 工程。

---

## 一、交付内容一览

| 方式 | 文件 | 是否需要编译 | 说明 |
|---|---|---|---|
| Grasshopper 组件 | `python/NormalFaceFilter_GhPython.py` | 否 | 粘贴/加载到 GhPython 组件即可用，**推荐** |
| Rhino 命令 | `python/NormalFaceFilter_RhinoCommand.py` | 否 | `_RunPythonScript` 运行，或设成别名 `NFF` |
| 核心算法 | `python/nff_core.py` | 否 | 纯 Python 内核，便于二次开发与测试 |
| C# 正式插件 | `csharp/NormalFaceFilter.sln` | 是 | 产出 `NormalFaceFilter.Grasshopper.gha` 与 `NormalFaceFilter.Rhino.rhp` |
| 测试 | `tests/` | — | 24 项自动化测试，全部通过 |

> **验证状态（2026-11-22 更新）**：Python 脚本 24/24 模拟测试通过；并已在真实 Rhino 9.1 上逐项验证（测试网格生成、GhPython 5 种参数组合、命令脚本全部内部函数），抓出并修复了 5 个模拟层掩盖的 RhinoCommon 9 API 错误。
> C# Core + .rhp 已用进程内 Roslyn **真编译成功（14336 字节，0 error）**并在 Rhino 9 反射验证；插件加载与 `SelectFacesByNormal` 命令注册通过。
> 详见 `HANDOFF.md` 第 4.6 节的完整验证表。

---

## 二、算法原理

对每个网格面：

1. 用面的顶点叉乘求单位法线 `n`（三角形用 `(B-A)×(C-A)`，四边形再加 `(C-A)×(D-A)` 后取平均）。
2. 计算 `n` 与参考方向 `d` 的夹角：`θ = acos(clamp(n·d, -1, 1))`，范围 `0°~180°`。
3. 命中条件：`minAngle ≤ θ ≤ maxAngle`。
4. 若开启 `IncludeOpposite`，则 `180°−θ` 也参与判断 —— 相当于把参考方向当成一根「轴」，正反两个朝向都算命中。
5. 退化面（零面积、无效索引）一律剔除，不参与夹角计算。

筛选结果会输出命中面的**原始索引**，方便你回到原始网格上做分组、着色或导出。

---

## 三、快速上手：Grasshopper（零编译，推荐）

1. 在 Grasshopper 画布放一个 **GhPython** 组件（Rhino 7 叫 GhPython，Rhino 8 叫 Python 3 Script）。
2. 把 `python/NormalFaceFilter_GhPython.py` 的路径填进组件的 Script 输入框，或者把整段代码粘贴进去。
3. 按下面的名字添加**输入**参数（名字必须一致）：

| 输入名 | 类型 | 默认值 | 含义 |
|---|---|---|---|
| `Mesh` | Mesh | 必填 | 待筛选网格（Nomad 导出的 obj/stl 导入 Rhino 后即为 Mesh） |
| `Direction` | Vector3d | (0,0,1) | 参考方向，`RefFace >= 0` 时被忽略 |
| `Angle` | float | 30.0 | 最大夹角（度） |
| `MinAngle` | float | 0.0 | 最小夹角（度），用于筛斜向面带，如 60~90° |
| `RefFace` | int | -1 | ≥0 时改用该序号面的法线作为参考方向 |
| `IncludeOpposite` | bool | False | True = 把方向当轴，正反两面都算 |
| `Bins` | str | `0,15,30,60,90,120,180` | 角度分箱边界，逗号分隔；留空不分组 |

4. 添加**输出**参数：

| 输出名 | 类型 | 含义 |
|---|---|---|
| `FilteredMesh` | Mesh | 只含命中面的新网格，按角度着色：红 0° → 绿 90° → 蓝 180° |
| `KeptFaces` | list | 命中面的原索引 |
| `RemovedFaces` | list | 剔除面的原索引 |
| `Angles` | list | 每个面与参考方向的夹角（度） |
| `AngleGroups` | tree | 按角度分箱的面索引，每个分支对应一个角度区间 |
| `Info` | str | 统计摘要 |

典型用法：`Mesh` 接 Nomad 导入的网格，`Direction` 接 Z 轴（或任意方向向量），`Angle` 先给 30 试一下；然后拿 `FilteredMesh` 去做面板划分，或拿 `AngleGroups` 按朝向分别处理。

---

## 四、快速上手：Rhino 命令（零编译）

运行 `python/NormalFaceFilter_RhinoCommand.py`，命令行会依次询问：

1. 选择要筛选的 Mesh
2. **参考方向**，支持以下写法：
   - 预设：`top` / `bottom` / `left` / `right` / `front` / `back`（也支持中文 `上/下/左/右/前/后`）
   - 任意向量：`0,0,1`、`1,1,0`
   - 取某个面的法线：`face:12`（面序号从 **0** 开始）
   - 直接回车：用 `+Z`
3. 最大夹角（默认 30）
4. 最小夹角（默认 0）
5. 是否正反两面都算（`y/n`，默认 `n`）

结果：命中面生成一个新 Mesh 对象，红色高亮并自动选中，命令行打印统计。

**建议设成别名**，以后直接输入 `NFF` 调用：

```
命令行输入 _Alias → New → 名称填 NFF →
宏内容填：_-RunPythonScript "C:\...\rhino-normal-filter\python\NormalFaceFilter_RhinoCommand.py"
```

---

## 五、编译正式插件（可选）

环境：Rhino 8 + .NET 8 SDK。在工程根目录执行：

```bash
dotnet build csharp/NormalFaceFilter.sln -c Release -p:RhinoInstallDir="C:\Program Files\Rhino 8\"
```

产物：

- `csharp/src/NormalFaceFilter.Rhino/bin/Release/net8.0/NormalFaceFilter.Rhino.rhp`
  → Rhino 命令行 `_PlugInManager` 安装，或直接拖进 Rhino 窗口。加载后命令名为 `SelectFacesByNormal`。
- `csharp/src/NormalFaceFilter.Grasshopper/bin/Release/net8.0/NormalFaceFilter.Grasshopper.gha`
  → 放到 Grasshopper 组件库目录（Rhino 8 通常为 `%APPDATA%\McNeel\Rhinoceros\8.0\Plug-ins\Grasshopper\Libraries`），重启 Grasshopper。电池名为 `Normal Face Filter (NFF)`。

Rhino 7 适配：把三个 `.csproj` 的 `TargetFramework` 改为 `net48`，并把 `RhinoInstallDir` 指向 Rhino 7 安装目录；Python 脚本本身已兼容 IronPython 2.7，无需改动。

---

## 六、对接 AI 辅助分面的建议流程

1. **导入**：Nomad 导出的 obj/stl 导入 Rhino，确保是 Mesh。
2. **粗分朝向**：用 `Direction = Z`、`Angle = 30` 先筛出「朝上」的面；再用 `bottom`、`left` 等方向分别筛其他主朝向。
3. **正反合并**：如果板材两面都要处理，开启 `IncludeOpposite`，一次拿到正反朝向的面。
4. **精细分组**：用 `AngleGroups` 按角度区间（如 0–15°、15–30°）把面拆成不同批次，分别喂给后续 AI 分割算法。
5. **拿结果**：`FilteredMesh` 直接可视化检查；`KeptFaces` / `Angles` 作为数据接口传给下游脚本。

这套工具解决的是「先把正确朝向的面挑出来」，AI 分面本身接在它后面即可。

---

## 七、目录结构

```
rhino-normal-filter/
├── README.md
├── python/
│   ├── nff_core.py                       纯算法内核（可独立测试）
│   ├── NormalFaceFilter_GhPython.py      Grasshopper 组件脚本
│   └── NormalFaceFilter_RhinoCommand.py  Rhino 命令脚本
├── csharp/
│   ├── NormalFaceFilter.sln
│   └── src/
│       ├── NormalFaceFilter.Core/        C# 共用算法
│       ├── NormalFaceFilter.Rhino/       Rhino 命令插件 (.rhp)
│       └── NormalFaceFilter.Grasshopper/ GH 组件 (.gha)
└── tests/
    ├── test_nff_core.py                  算法单元测试
    ├── test_ghpython.py                  GhPython 脚本流程测试（模拟 API）
    ├── test_rhino_command.py             Rhino 命令脚本流程测试（模拟 API）
    └── mock_rhino.py                     测试用 Rhino API 模拟层
```

运行测试：

```bash
cd rhino-normal-filter
python -m unittest discover -s tests -v
```

---

## 八、已知限制

- 只处理 **Mesh**，不处理 NURBS/Brep 曲面（如需处理曲面，先转成 Mesh）。
- 四边形面法线用两个三角形的叉乘平均近似，极度扭曲的四边形可能与 Rhino 内置法线略有差异。
- 面索引 `RefFace` / `face:N` 使用 **0 起始**序号。
- C# 工程未经真实 Rhino SDK 编译验证，首次编译如遇 API 差异请按报错微调（核心逻辑与 Python 版完全一致）。
