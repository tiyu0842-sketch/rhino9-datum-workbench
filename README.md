# Rhino 9 插件工作台 + 基准面工具 + NFF 法线筛面 + FeatureWorks v2

四件东西放在一个仓库，彼此印证：

1. **`skill/` — Rhino 9 插件开发工作台**（Agent Skill）
   一份可复用的工作流：怎么在没有 .NET SDK 的机器上编译、怎么才算"验证过"、显示模式怎么调出三度灰阶、常见错误按症状怎么查。
2. **`plugin/` — 基准面工具 v2.8**（一个真实插件的完整源码、文档与验证脚本）
   上面那套方法论的实际产物：从 v1.2 迭代到 v2.8，修过过曝、修过视图歪斜、改过交互方式，每一步都有实测记录。
3. **`nff/` — NormalFaceFilter 法线筛面**（2026-11-22 新增，已完成真机验证）
   按参考方向筛选 Mesh 面，为 AI 分面前处理。Python + C# 双实现，24 项模拟测试 + 真机验证全过；
   真实 Rhino 9 上抓出并修复了 5 个模拟层掩盖的 API 错误（详见 `nff/HANDOFF.md` 第 4.6 节）。
4. **`featureworks-v2/` — 几何特征识别**（2026-11-23 新增，第一版：识别 + 列出 + 高亮）
   按外包技术规格全新实现。AAG 邻接图 + 三条判据（面类型 / 覆盖角 / G1 相切）识别圆角与 chamfer，
   多核并行逐面计算；真机验证圆角盒、带孔板、chamfer 盒全部符合预期（孔不误判）。

> **适用版本**：Rhino 9 / .NET 8 / RhinoCommon。不保证 Rhino 8 可用（.rhi 老通道不支持 net8 插件）。

## 快速开始

### 用技能包

把 `skill/` 整个目录复制到 `~/.workbuddy/skills/rhino9-plugin-workbench/`，下次会话起自动可用。
也可以只把 `skill/references/` 当作 Rhino 9 开发速查手册读。

### 编译插件

本机没有 .NET SDK 时，在 Rhino 的 Python 3 里执行进程内 Roslyn 编译：

```python
import io, contextlib
ROOT = r"<你的插件目录>"
OUT_OVERRIDE = ROOT + r"\DatumPlanePlugin_v28.rhp"
p = r"<本仓库>/skill/scripts/Compile_Roslyn.py"
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    exec(compile(open(p, encoding="utf-8").read(), p, "exec"))
print("\n".join(l for l in buf.getvalue().splitlines() if "ERROR" in l or "COMPILE" in l))
```

详见 `skill/references/verification-playbook.md`。

### 安装

**用 `.yak`，不要用 `.rhi`。** 老式 RhiExec 用 .NET Framework 反射检查 net8 插件，会报 "package is not compatible"。

```bash
"C:\Program Files\Rhino 9\System\Yak.exe" install DatumPlane_v2_8.yak
```

安装前请关闭代理/梯子，否则 Yak 联网校验会被超时杀掉（假失败）。装完重启 Rhino。

## 目录

```
skill/
  SKILL.md                        流程与决策表
  references/
    error-catalog.md              症状 → 原因 → 怎么办（先查这张）
    rhinocommon-pitfalls.md       API 行为/签名/赋值顺序坑
    display-modes.md               光照方案、灰阶判据、等参线
    verification-playbook.md       反射/像素/截图/安装
  scripts/                         通用 Roslyn 编译 + yak 打包
  assets/                          RUI 明暗 SVG 图标示例
plugin/
  src/                             10 个源文件
  verification/                    编译、打包、回归脚本
  docs/CHANGELOG.md                v1.2 → v2.8 版本谱系与实证数字
  docs/ARCHITECTURE.md             模块职责、数据流、关键流程
  docs/PROJECT_STATUS.md           已决/未决事项、环境陷阱
  README.md / REVIEW.md            用户向说明与早期审查记录
nff/
  python/                          nff_core + GhPython + Rhino 命令（真机修正版）
  csharp/                          Core + .rhp 四个源文件（真机编译通过）
  make_test_mesh.py                7 面测试网格（真机修正版）
  HANDOFF.md                       交接说明 + 第 4.6 节真机验证记录
featureworks-v2/
  src/                         FwCore（识别引擎）+ FwCommands + FwPlugin
  FeatureWorks_v20.rhp         真机编译产物（15360 字节）
  README.md                    判据、实测表、7 个 API 差异、下一版待做
docs/
  从零到一_基准面迭代与渲染复盘.md  基准面四版迭代与 IdeaS 渲染 token 账
```

## 几条经过实测的关键结论

- `LightingSchema` 是枚举不是 flag；`AmbientOcclusion`（Arctic 式）只有接触遮蔽，没有受光/侧光/背光的明暗梯度，曲面会"糊成一片"。三度灰阶要用 `CustomLighting` + `FrontMaterial.Diffuse`。
- 判断过曝不要靠眼睛：算 `clip(≥253)` 百分比。受光面打到 255 就是削平。
- `CaptureToBitmap()` 会返回缓存帧；只改 `DisplayMode` 不触发真正重绘，几组不同参数的截图可能一模一样。
- 已注册的显示模式无法原地更新，必须先删再建，否则"装了新版还是老样子"。
- 多重曲面上直接点选单一面：`GeometryFilter` 只给 `ObjectType.Surface`，加 `SubObjectSelect=true` + `DisablePreSelect()`；写成 `Surface|Brep` 就必须按 Ctrl+Shift。
- 面板类功能不能在反射条件下验证——`Assembly.Load` 不算插件加载，`OnLoad` 不触发。
- **mock 通过 ≠ 真机通过**：NFF 的 24 项模拟测试全过，因为 mock 层自己造了 `Vector3d.DotProduct`——而 RhinoCommon 9 根本没这个方法（点积用 `a * b`）。同样的坑还有 `Mesh.CreateBox`（正确是 `CreateFromBox(BoundingBox,1,1,1)`）、`PlugIn.EnglishName` 不可 override、`RhinoGet.GetReal` 不存在（用 `GetNumber`）。五个错误全是真机编译/运行才暴露的。

## 许可

MIT — 见 [LICENSE](LICENSE)。

## 致谢

错误目录的组织方式借鉴了 [Cordyceps](https://github.com/brookstalley/cordyceps) 的 `CommonErrorsGuide`：按"用户看到的现象"索引，并明确区分"真失败 / 已在工作 / 已回滚 / 只有人能处理"。这个结构显著降低了 Agent 的重试风暴。
