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
| 去布尔是否必须先去圆角 / 为什么补面而不取消修剪 / 只能在小框里选 | `feature-recognition.md` **§11（诊断）→ §12（v1.6 已落地）**；`rhinocommon-pitfalls.md`「B-rep 特征取消」「v1.6 新增」；**E-024 → E-025**；`RemoveHoles(指定内环)` + 常驻双向联动 |
| 编译刷 CS0104 `Point`/`Environment` 歧义 / `RemoveHoles` 报「没解析到内环」 | `error-catalog.md`「v1.6 / E-025 新增症状」；`rhinocommon-pitfalls.md`「v1.6 新增」；**别用 `FeatureType` 默认值判断模块归属，用 `Channel`** |
| **取消圆角/倒角后「所有东西全部消失」** | `error-catalog.md`「v1.6.1 / E-028 新增症状」；`feature-recognition.md` **§13**；`rhinocommon-pitfalls.md`「v1.6.1 新增」：先分层（几何可能还在，隐藏对象要 `includeHidden=true`）、`ObjectCulling` 剔除前 `HasDrawableContent()`、结果写文档前 `ValidateResult`、`FWSelect` 用 `clean ?? brep` 同源 |
| 想让视口直接框选 conduit 高亮面 / 一份共享选中集 | `feature-recognition.md` §12.1；项目 `FwSelection.cs`（`MouseCallback` 接管左键 + `WorldToClient` 屏幕投影命中，不建文档对象） |
| 想把原理讲清楚 / 做科普短片 / 「用代码生成视频」 | 仓库 `design-lab/002-brep-untrim-explainer/`（README 六步 + style.md + storyboard/render/encode/preview）；**E-026**：代码驱动的确定性渲染（`frame(t)` 纯函数 + Pillow 逐帧 + ffmpeg 只做封装），**不是 AI 文生视频**；三条禁令：不读时钟 / 不用无种子随机 / 不联网 |
| 视频转场/滤镜不生效、ffmpeg 报滤镜不存在 | **E-026**：本机 ffmpeg 是 KeyShot 自带的 `--disable-everything` 精简构建，只有 scale/palettegen/paletteuse；转场必须在帧内算 |
| 画面中文变方块 / `□` | **E-026** 坑 1：Consolas 无中文字形，等宽位置放中文要切雅黑 |
| 想给代码视频配音 / 「可以配个声音吗」 | 仓库 `design-lab/002-brep-untrim-explainer/` 的 `audio.py` + `style.md` §8 + `narration.md`；**E-027**：音频也是 `sample(t)` 纯函数，事件表由 BEATS 派生，包络从 0 起回 0 收，频率边界 glide 滑移；WAV sha256 两次一致 |
| **声音「怪怪的、不舒服」/ 想更省算力 / 想要「恍然大悟感」** | `design-lab/002-brep-untrim-explainer/RETRO_audio_and_compute.md`（一页速查 + 算力账 + 10 条省算力清单 + 7 条可追溯听感根因 + Claude 系配乐对照 + 明天议程）；**E-029**：**音效 ≠ 配乐**，「恍然大悟」= 稳定调性 + 张力→解决 + 留白；最省算力的动作是把「听感」前移成 6 个可计算指标，别等真人听完才闭环 |
| MP4 加不了音轨 / ffmpeg 找不到音频编码器 | **E-027**：本机两个 ffmpeg 能力不同 —— `KeyShot Studio/bin` 精简构建 0 音频编码器，`KS2024/bin` 完整构建有 aac+amix；`find_ffmpeg(need_audio=True)` 实测 `-encoders` 再挑，别凭路径猜 |
| 预览页注入的音色参数变成数组 / `K.dur` 是 undefined | **E-027**：Python 侧 `KIND` 用 dict 不用 tuple，JSON 序列化后浏览器才读得到对象；重构后音轨哈希不变可作回归验证 |
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
| 「这个坑以前踩过没 / 当时怎么判断的」 | `experiment-log.md`（**31 条**，含 14 条被推翻的假设；E-025 为 E-024 方案落地、E-026 / E-027 为跨域能力扩展、E-028 为 v1.6 实现层的失败安全修正、E-029 为验收维度缺失、E-030 为跨域能力扩展 + 需求验证正向样本，均不新增推翻计数） |
| 「把资料做成每日答题闯关 / 艾宾浩斯 / 错题科普 / 能不能做小程序 / 要不要备案 / 微信分享」 | `design-lab/003-industrial-design-history-quiz/README.md`（六步字段 + **§8 小程序/H5/备案对照表**）；**E-030**：真排行榜必须后端；小程序**必须备案、无例外**（12381 短信核验 24 h 内做完），答题类按「**工具**」类目提审避开教育资质坑；扫描版 PDF（无 ToUnicode）连百度网盘服务端解析也读不出，别反复试；题目 evidence 必须命中原文，**宁可少不可编** |
| 结论被推翻了怎么处理 | `experiment-log.md` →「统计与复用提示」：**不删旧条，加「修正 E-XXX」** |

---

## 2. 按任务类型查（做一件事时读哪几份）

| 任务 | 阅读顺序（只读需要的章节） |
|---|---|
| **改 FeatureWorks 功能** | `feature-recognition.md` §6/§7 → **§11/§12（v1.6 两模块与常驻联动）→ §13（v1.6.1 失败安全）** → `error-catalog.md`「几何特征识别」+「v1.6 / E-025」+「v1.6.1 / E-028 新增症状」→ `experiment-log.md` 相关 E 号 |
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
| `feature-recognition.md` | B-rep 特征识别/取消专题（**§0–§12**；§11 诊断、§12 v1.6 实现与实测） | GH 数据流 |
| `rhino-command-index.md` | 1256 条命令全量索引（只查） | 用法讲解 |
| `rhino-command-reference.md` | 命令 ↔ API ↔ 几何 三层精讲 | 全量清单 |
| `grasshopper-spatial-logic.md` | GH 构造序列/数据树/验证/教学纪律（§1–§9） | 组件清单 |
| `grasshopper-component-index.md` | 2336 组件索引（只查） | 原理讲解 |

**读法**：索引类文件（两个 index）平时不读，需要查时按字母/类别检索；精讲类按需读单节；台账与错误目录每次先查。
