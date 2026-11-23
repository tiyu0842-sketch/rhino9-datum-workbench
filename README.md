# Rhino 9 插件工作台 + 基准面工具 + NFF 法线筛面 + FeatureWorks 特征取消

五件东西放在一个仓库，彼此印证：

1. **`skill/` — Rhino 9 插件开发工作台**（Agent Skill）
   一份可复用的工作流：怎么在没有 .NET SDK 的机器上编译、怎么才算"验证过"、显示模式怎么调出三度灰阶、
   常见错误按症状怎么查、B-rep 特征识别与 `DisplayConduit` 聚焦显示怎么做。
   另含 **`experiment-log.md` 实验台账**：每次真机实验的假设与实测数字，结论被推翻也保留演化过程——
   这是让 Agent 少踩坑、少重复验证（省 token）的核心。
2. **`plugin/` — 基准面工具 v2.10**（一个真实插件的完整源码、文档与验证脚本）
   上面那套方法论的实际产物：从 v1.2 迭代到 v2.10，修过过曝、修过视图歪斜、改过交互方式，也把做反的视口联动改回独立，每一步都有实测记录。
3. **`nff/` — NormalFaceFilter 法线筛面**（2026-11-22 新增，已完成真机验证）
   按参考方向筛选 Mesh 面，为 AI 分面前处理。Python + C# 双实现，24 项模拟测试 + 真机验证全过；
   真实 Rhino 9 上抓出并修复了 5 个模拟层掩盖的 API 错误（详见 `nff/HANDOFF.md` 第 4.6 节）。
4. **`featureworks/` — RhinoFeatureWorks v1.6 特征取消**（**正式实现**）
   SolidWorks FeatureWorks 风格：选中一个没有历史的 B-rep 实体 → 判断哪些面被改过（trim / 布尔 / 倒角）→
   删除特征 → 几何恢复成可重新编辑的毛坯，省掉倒角/布尔后想再编辑时的手工备份。
   **两个独立模块、任意顺序**（E-024/E-025）：模块 B 去除布尔切割走
   `Brep.RemoveHoles(指定 inner loop, tol)` 只删选中的孔；模块 A 去除圆角走删整圈过渡面 +
   `CreateSolid` 重缝，连带恢复孔时原文报出、不偷偷改。实测圆角盒+1孔 `11→10 面` 圆角完好，
   **「去布尔必须先去圆角」是假的**；旧版 `UntrimFace` 会抹掉宿主面全部内环，已弃用。
   `FWSelect` / `FWCancel` / `FWCancelPanel` 交互闭环、9/9 自测、yak 真安装。
   **v1.6 常驻双向联动**：视口左键点选 / 拖框 / Shift-Ctrl 加减选（`MouseCallback` + 屏幕投影命中），
   与面板共享一份选中集；两个模块各一个执行按钮、严格无总开关。
   v1.5 面板重做：视口逐组编号 ↔ 面板行双向选择、显式语义、空勾选不执行（E-023）。
   方向纠偏的完整复盘见 `featureworks/HANDOFF.md`；实现与实测数字见 `featureworks/INTERACTION_SPEC.md` §12。
5. **`featureworks-v2/` — 已降级的实验记录**（⚠️ 非发布物料）
   一次方向走偏的实现：做的是「备份对象恢复」而非几何 untrim，未解决痛点。
   保留仅供工程做法参考（Eto 布局、Undo 分组、处理三分支），**不要作为基线或分发**。

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
  SKILL.md                        流程、决策表、实验台账纪律
  references/
    error-catalog.md              症状 → 原因 → 怎么办（先查这张）
    experiment-log.md             实验台账：假设/实测数字/结论/回填位置
    feature-recognition.md         B-rep 特征识别与取消（两套算法 + 聚焦显示）
    rhinocommon-pitfalls.md       API 行为/签名/赋值顺序坑
    display-modes.md               光照方案、灰阶判据、等参线
    verification-playbook.md       反射/像素/截图/安装
  scripts/                         通用 Roslyn 编译 + yak 打包
  assets/                          RUI 明暗 SVG 图标示例
plugin/
  src/                             10 个源文件
  verification/                    编译、打包、回归脚本
  docs/CHANGELOG.md                v1.2 → v2.10 版本谱系与实证数字
  docs/ARCHITECTURE.md             模块职责、数据流、关键流程
  docs/PROJECT_STATUS.md           已决/未决事项、环境陷阱
  README.md / REVIEW.md            用户向说明与早期审查记录
nff/
  python/                          nff_core + GhPython + Rhino 命令（真机修正版）
  csharp/                          Core + .rhp 四个源文件（真机编译通过）
  make_test_mesh.py                7 面测试网格（真机修正版）
  HANDOFF.md                       交接说明 + 第 4.6 节真机验证记录
featureworks/                    ← 正式实现（v1.6.0.0）
  src/                         18 个源文件：识别引擎/证据/聚焦显示/两个取消模块/共享选中集/常驻鼠标监听/面板
  verification/                Roslyn 编译 + 打包（路径可移植，无本机硬编码）
  README.md / 使用手册.md       命令与交互说明
  INTERACTION_SPEC.md          §11 诊断、§12 v1.6 实现与真机实测数字
  HANDOFF.md                   方向纠偏复盘：什么是对的、什么是走偏的
  RhinoFeatureWorks_v1.6.0.0.yak  真安装验证过的发行包（v1.3.2 / v1.4 / v1.5 一并保留）
featureworks-v2/                ← 已降级，实验记录，勿用
  src/                         v2 识别引擎（备份对象恢复，非 untrim）
  README.md / BETA_NOTICE.md   顶部已加降级声明
design-lab/                      ← 想法实验室（六步：原话/原理/序列/形态/证据/复盘）
  001-gradient-boxes.md         GH 渐变立方体（Series.Start=0 退化坑）
  002-brep-untrim-explainer/    代码生成科普短片 + 确定性音轨
    storyboard.py               唯一数据源（BEATS + CONFIG + PALETTE + AUDIO）
    render.py / audio.py        frame(t) / sample(t) 两个纯函数
    encode.py / build_html.py   封装编码（按能力挑 ffmpeg）/ 注入预览页
    preview.html                画面 + Web Audio 可交互预览（9 控件）
    style.md / narration.md     风格规格（§8 音频）/ 人声旁白插槽
    brep_untrim_with_audio.mp4  带音轨成片
docs/
  从零到一_基准面迭代与渲染复盘.md  四阶段迭代与观测显示调参复盘
```

## 几条经过实测的关键结论

- `LightingSchema` 是枚举不是 flag；`AmbientOcclusion`（Arctic 式）只有接触遮蔽，没有受光/侧光/背光的明暗梯度，曲面会"糊成一片"。三度灰阶要用 `CustomLighting` + `FrontMaterial.Diffuse`。
- 判断过曝不要靠眼睛：算 `clip(≥253)` 百分比。受光面打到 255 就是削平。
- `CaptureToBitmap()` 会返回缓存帧；只改 `DisplayMode` 不触发真正重绘，几组不同参数的截图可能一模一样。
- 已注册的显示模式无法原地更新，必须先删再建，否则"装了新版还是老样子"。
- 多重曲面上直接点选单一面：`GeometryFilter` 只给 `ObjectType.Surface`，加 `SubObjectSelect=true` + `DisablePreSelect()`；写成 `Surface|Brep` 就必须按 Ctrl+Shift。
- 面板类功能不能在反射条件下验证——`Assembly.Load` 不算插件加载，`OnLoad` 不触发。
- **mock 通过 ≠ 真机通过**：NFF 的 24 项模拟测试全过，因为 mock 层自己造了 `Vector3d.DotProduct`——而 RhinoCommon 9 根本没这个方法（点积用 `a * b`）。同样的坑还有 `Mesh.CreateBox`（正确是 `CreateFromBox(BoundingBox,1,1,1)`）、`PlugIn.EnglishName` 不可 override、`RhinoGet.GetReal` 不存在（用 `GetNumber`）。五个错误全是真机编译/运行才暴露的。
- **圆角和孔洞必须用两套取消算法，而且两个模块完全独立**：
  孔 = 底层曲面上的 inner loop → `Brep.RemoveHoles(IEnumerable<ComponentIndex>, tol)`（since 6.8，
  **只删指定的内环**，返回 `Brep` 不是 bool）。旧写法 `UntrimFace(host, tol)` 会把外环 + **全部**内环
  一起抹掉，同面多孔一起没 —— 这条旧结论已由 **E-024 推翻**，v1.6 起禁用。
  圆角 = 滚球扫出的**新增过渡曲面**（不是 trim），`UntrimOuterLoop` 恒返回 `null`（外环边全被邻面共享），
  只能删整圈过渡面 → 取 `UnderlyingSurface().ToBrep()` → `Brep.CreateSolid()` 重缝，且**必须整圈删**
  （只删 1 个得到变形体 74715.5，删 4 个才是 75000）。
  **「去布尔必须先去圆角」是假的**：圆角盒 R3 + 1 孔 `11 面 / 235922.14` → 只删该孔内环 →
  `10 面 / 239315.06` 纯圆角盒，圆角完好（E-024 真机实测 / E-025 落地）。
- **半透明不能靠叠透明层**：往不透明实体上叠 0.85 透明灰，底色不变，看起来没淡化。要用 `DisplayConduit.ObjectCulling` 把源对象从绘制里剔除，再画自己的子 Brep；需要浮在前面的高亮面必须画在 `DrawForeground`，放 `PostDrawObjects` 会被深度剔成线框。
- **长命 conduit 必须做过期自愈**：缓存的子面按面索引抽取，源对象被替换/移动/删后索引失效会留"鬼影"。挂**静态**文档事件（`doc.ReplaceRhinoObject +=` 会 CS0176）+ 每次绘制前比对面数与包围盒中心漂移。`ReferenceEquals` 比几何不可行（`ObjRef.Brep()` 返回副本）。
- **先验证需求，再验证代码**：FeatureWorks 曾有整个分支技术成功却解决了错误的问题（备份对象恢复 ≠ 几何 untrim）。详见 `featureworks/HANDOFF.md`。

## 许可

MIT — 见 [LICENSE](LICENSE)。

## 致谢

错误目录的组织方式借鉴了 [Cordyceps](https://github.com/brookstalley/cordyceps) 的 `CommonErrorsGuide`：按"用户看到的现象"索引，并明确区分"真失败 / 已在工作 / 已回滚 / 只有人能处理"。这个结构显著降低了 Agent 的重试风暴。
