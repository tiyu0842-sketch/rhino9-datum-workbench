# 知识地图 — 遇到问题时先查这里

> 本文件**不存知识，只做导航**。目的是下次遇到同类问题时，一步跳到正确文档的正确章节，
> 不用通读、不用翻日志、不用重新推理。这是「省 token」真正的落地点。
>
> 配套：`SKILL.md`（工作流）· `../scripts/`（可执行脚本）

---

## 1. 按症状查（最快入口）

| 你看到的现象 / 你要做的事 | 去哪查 |
|---|---|
| 编译报 `type must have a GuidAttribute`、加载失败、同名程序集跑旧代码 | `error-catalog.md` →「编译与加载」；`rhinocommon-pitfalls.md` →「编译与加载」 |
| 装完插件**没界面 / 命令不出现** | `error-catalog.md` →「编译与加载」（`LoadPlugIn` 主动加载）；**判据别用 `DockBarIdInUse`**，见 E-020 |
| 面板加载超时 / 停靠面板驱动不了 | `error-catalog.md` →「交互命令」；反射验证控件树见 `verification-playbook.md` →「二」 |
| Eto 控件选不了多项、布局溢出 | `rhinocommon-pitfalls.md` →「Eto 面板」 |
| 显示过曝 / 发灰 / 看不出曲面走向 | `display-modes.md` →「三个光照方案」「已验证的两套配方」「调参判据」 |
| 等参线太密、阴影太暗 | `display-modes.md` →「等参线」「阴影与背景」；用户立场见 `SKILL.md` |
| 切显示模式只有当前视口变、想要 Alias 式全视图联动 | `display-modes.md` →「全视图联动（可选，默认关）」；E-021；**先读回各视口真实模式再动代码** |
| **切一个视口，四个视口一起变**（要的是独立） | `display-modes.md` →「视口作用范围」；E-022；搜自己的 `foreach (... doc.Views)`，别怪 Rhino |
| 改了默认设置值却不生效 | `error-catalog.md`「显示与视觉」→ 换键名带 `.v2` 后缀 |
| 面板列表看不出对应模型哪一块 / 想点边选特征 | `feature-recognition.md` §10；`INTERACTION_SPEC.md` §10；E-023；编号双向映射 + `BrepFace.AdjacentEdges()` |
| 截图空白 / 拿到缓存帧 | `rhinocommon-pitfalls.md` →「相机、截图与 Box 创建」；`verification-playbook.md` →「三」 |
| 枚举不到对象、以为被删 | `rhinocommon-pitfalls.md` →「文档事件与对象枚举」（`HiddenObjects=true`） |
| 半透明不生效、有鬼影、高亮只剩线框 | `rhinocommon-pitfalls.md` →「DisplayConduit 聚焦显示」；`feature-recognition.md` → §4 |
| 做圆角 / 孔洞取消、恢复毛坯 | `feature-recognition.md` → §1、§2、§4；先读 §0「别造错东西」 |
| 「保留主体 / 保留全部」做不对 | `feature-recognition.md` → §8（loop 与 face 粒度错配、三路径） |
| 想理解「为什么使用感差」/ 逆向识别原理 | `feature-recognition.md` → §8、§9（hint-based、有限方法库、不适定） |
| 想知道 Rhino 有没有某命令、官方怎么用 | `rhino-command-index.md`（全量 1256）→ `rhino-command-reference.md` → §2、§3、§6 |
| 想从活进程重新导出命令清单 | `../scripts/Export_Rhino_Commands.py` |
| GH 定义连好了但结果数量/配对不对 | `grasshopper-spatial-logic.md` → §3（Item/List/Tree、匹配规则） |
| GH 报 `solved=true` 但几何不对 / 退化盒 | `grasshopper-spatial-logic.md` → §5、§6；**求解状态不等于几何有效** |
| GH 视口有、文档没实体 | `grasshopper-spatial-logic.md` → §5（preview 不落地，要 Bake） |
| 想把设计想法变成定义 | `grasshopper-spatial-logic.md` → §4（四步构造序列） |
| 不知道该用 GH 还是 C# 插件 | `grasshopper-spatial-logic.md` → §7（三层对照 + 判据） |
| 查某个 GH 组件名 / 参数签名 | `grasshopper-component-index.md`；或运行时 `g1_search_components` / `g1_describe_component` |
| 装了新插件后刷新 GH 组件清单 | `../scripts/Export_GH_Components.py` |
| 要打包 yak、多版本并存、安装假失败 | `verification-playbook.md` →「五」；`rhinocommon-pitfalls.md` →「打包与安装」「打包补充」 |
| 「这个坑以前踩过没 / 当时怎么判断的」 | `experiment-log.md`（24 条，含 13 条被推翻的假设） |
| 结论被推翻了怎么处理 | `experiment-log.md` →「统计与复用提示」：**不删旧条，加「修正 E-XXX」** |

---

## 2. 按任务类型查（做一件事时读哪几份）

| 任务 | 阅读顺序（只读需要的章节） |
|---|---|
| **改 FeatureWorks 功能** | `feature-recognition.md` §6/§7 → `error-catalog.md`「几何特征识别」→ `experiment-log.md` 相关 E 号 |
| **调显示模式** | `display-modes.md` 全文（短）→ `rhinocommon-pitfalls.md`「视口与布局」→ 用户立场见 `SKILL.md` |
| **搭 GH 定义** | `grasshopper-spatial-logic.md` §4 → `grasshopper-component-index.md` 对应族 → 搭完必走 §5 第 5 步验证 |
| **诊断一个报错** | `error-catalog.md`（按症状）→ `experiment-log.md`（看结论演化）→ 对应专题 → 反射确认 API |
| **打包发布** | `verification-playbook.md`「一/五/六」→ `rhinocommon-pitfalls.md`「打包补充」→ 脱敏复查 |
| ** learns 新东西后回填** | 本文 §3 的固定清单 |

---

## 3. 回填清单（每次真机实验后照做，保证能力不丢）

> 这是用户 2026-11-23 反复强调的「一定要全部记录、整理培养」的**落地检查表**。
> 做完实验后逐项打勾，**别让结论只活在日志里**。

- [ ] **1. 实验台账**：`experiment-log.md` 追加一条，固定字段 = 假设 / 做法 / **实测数字** / 结论 / 回填到哪 / 遗留
- [ ] **2. 若推翻旧结论**：新条写「修正 E-XXX」，**不删旧条**；旧条补一行指向；更新统计行
- [ ] **3. 错误目录**：新坑按**症状**写进 `error-catalog.md`，别人报错时能直接命中
- [ ] **4. API 坑位**：参数签名 / 赋值顺序 / 实测行为写进 `rhinocommon-pitfalls.md`
- [ ] **5. 领域专题**：几何结论、原理精化写进对应专题（`feature-recognition.md` / `grasshopper-spatial-logic.md` / `display-modes.md`）
- [ ] **6. 入口同步**：如果新增了场景或决策，`SKILL.md` 的「何时使用 / 决策表」要加一行；如果新增了文档，**本文件 §1/§2 要加入口**
- [ ] **7. 工作区记忆**：`MEMORY.md` 就地更新版本号 / 立场 / 硬约束；`YYYY-MM-DD.md` **append-only** 记本次动作
- [ ] **8. 仓库同步**：用户级 skill → `skill/` 副本 → 本地 commit；**脱敏复查**（`C:\Users\…` / 会话号 / 临时盘路径）
- [ ] **9. design-lab**：如果这是一个「想法落地」实验，按 `design-lab/README.md` 六步建条目（原话/原理/序列/形态/证据/复盘）

**三条纪律**：
1. **先验证需求，再验证代码** —— 曾有整条分支技术成功却解决错问题（`HANDOFF.md`）。
2. **结论"应该可以"但没数字 = 未验证** —— 不许写进交付物。
3. **演示时费一点 token 讲原理，留 3–6 个手柄，一起改** —— 用户明确要求，见 `grasshopper-spatial-logic.md` §8。

---

## 4. 文件清单（10 份参考，各自职责，不重复）

| 文件 | 存什么 | 不存什么 |
|---|---|---|
| `error-catalog.md` | 症状 → 原因 → 怎么办（先查这张） | 完整实验过程 |
| `experiment-log.md` | 实验演化：假设/数字/结论/被推翻 | 怎么操作 |
| `rhinocommon-pitfalls.md` | 已实测的 API 行为与签名 | 业务流程 |
| `display-modes.md` | 光照/等参线/阴影的参数配方与判据 | 插件架构 |
| `verification-playbook.md` | 反射/像素/截图/安装流程 | 几何原理 |
| `feature-recognition.md` | B-rep 特征识别/取消专题（§0–§9） | GH 数据流 |
| `rhino-command-index.md` | 1256 条命令全量索引（只查） | 用法讲解 |
| `rhino-command-reference.md` | 命令 ↔ API ↔ 几何 三层精讲 | 全量清单 |
| `grasshopper-spatial-logic.md` | GH 构造序列/数据树/验证/教学纪律（§1–§9） | 组件清单 |
| `grasshopper-component-index.md` | 2336 组件索引（只查） | 原理讲解 |

**读法**：索引类文件（两个 index）平时不读，需要查时按字母/类别检索；精讲类按需读单节；台账与错误目录每次先查。
