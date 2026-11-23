# 基准面工具 / 版本谱系

Rhino 9 / .NET 8，插件 GUID `8B7C4E52-6F3A-4C1D-9A2E-5D8F0B3C7E14` 全程不变。
每个版本都经过进程内 Roslyn 编译 + 真机/反射验证 + `Yak.exe install` 真安装（除 v2.3 未单独出包）。
当前安装：**2.10.0.0**。

| 版本 | 主题 | 交付内容 | 关键实证 |
|---|---|---|---|
| v1.2 | 基线加固 | 独立编号锁定子层 `DP_01…`、点选锁定基准面切换 | 真实文档 35/35 PASS；`LockedObjectSelect=true` 选中锁定物件 |
| v1.3 | 显示区分 | 虚线线型 + Ghosted 显示覆盖，解决线框视口下与普通平面无异 | 普通平面 vs 基准面四维全区分 |
| v1.4 | 统一菜单 | 7 选项合并进主命令；独立命令保留给工具栏/脚本 | 7 命令类、7 选项全注册 |
| v1.5 | 中英双语 | 48 处提示改「中文 / English」并列 | Create/CPlane/图层/还原回归全 PASS |
| v1.6 | 状态机修复 + 第5视图 | 激活态可再建（改走 SwitchTo）、跨视口迁移、分屏法向视图 | 44/44 PASS；Top 1540→769；view 4→5；点积 1.0 |
| v1.7 | Alias 观测显示 | 复制内置 Alias Style 做浅/深护眼模式 + 等参线 | 实拍 `evidence/alias_v17_light2.jpg` / `dark2.jpg` |
| v1.8 | JZ 菜单 | 字母代号 A–M；命令别名做成插件命令而非全局 AliasList | 37/37 PASS；`_JZ _I/_J/_L/_M` 全 True |
| v1.9 | 命令分离 | `JZ`/`DatumPlane` 只列基准面；显示命令独立 | 反射确认 Datum 菜单 A=True/I=False |
| v2.0 | 面中心 + 关第5视窗 | 面质心标架（不再用点击点）；`FourViewLayout` 关闭第5视窗 | box 顶面 origin=(50,40,30)，法线精确；4→5→4 |
| v2.1 | 行业棕 | 基准面改棕琥珀 `176,132,70`（Creo/SolidWorks/CATIA 惯例） | 对象色/材质色全一致，透明 0.55 |
| v2.2 | 过曝修复 | 诊断出 219/116/128 导致 255 削平；改哑光灰 + 等参线 | clip(≥253) 2.3%~9.5% → 0.00% |
| v2.4 | AO 白模 | 弃用"复刻 Alias Style"，走 Arctic 式 AO + 软地面阴影 + 轮廓线 | max=214、clip=0.00%；赋值顺序坑记录 |
| v2.5 | CPlane 残留修复 | 逐视口记录/还原 CPlane + 退出自愈；第5视窗保留基准面 CPlane | 三类场景反射实测；名字兜底还原成功 |
| v2.6 | 三度灰阶 | 发现 AO 无方向光梯度；换 CustomLighting + FrontMaterial.Diffuse | P10/P50/P90 = 101/119/152，跨度 51，clip 0% |
| v2.7 | 直接点面 | B 选项去 Ctrl+Shift：Surface-only filter + DisablePreSelect + 点击点兜底 | 6 面盒子六面法线全对；圆柱侧面→提示改点平面 |
| v2.8 | 双模式区分 | 浅色 WireDensity=0、深色=1，强制设置保证切换不残留 | 0→1→0→1 四次切换全对 |
| v2.9 | 全视图联动 | `DisplayPipeline.DisplayModeChanged` 静态事件驱动；切一个视口其余跟随；`AliasStyleLink` / 菜单 `O` 可关；Apply/Restore 静音避免与还原打架 | 回调序列 `blocked,blocked,blocked,3`；Top→Shaded 后四视口全 Shaded；还原四视口回 Alias EyeCare；rhp 55296B/0 error，sha256 `7454e87d…` |
| v2.10 | 视口独立（方向纠正） | `Apply` 只写活动视口（不再遍历 `doc.Views`）；新增 `Touched` 名单使 `Restore` 只还原改过的视口；联动降级为可选、默认关（设置键 `.v2` 后缀） | 只写 Perspective → `Perspective=Wireframe / 其余=Alias EyeCare`，0.3s 后仍只变一个；rhp 56320B/0 error，sha256 `a4e6a168…` |

## 分发事实

- 一律 `.yak`；`.rhi` 通道用 .NET Framework 反射检查 net8 的 .rhp，必报 "package is not compatible"。
- 安装路径 `%APPDATA%\McNeel\Rhinoceros\packages\9.0\基准面工具\<版本>\`；`manifest.txt` 指向最新版，旧版本目录不加载。
- Yak 安装前必须关闭代理/梯子，否则联网校验被杀掉，出现 SIGTERM 假失败。
- 工具栏组可见性存在用户配置的 `UI\default.rui`，改完必须正常退出 Rhino 才落盘。

## 保留的旧产物

`DatumPlane_v1_2.yak` … `DatumPlane_v2_10.yak` 全部保留在包目录，便于回滚；`DatumPlanePlugin_v24/v24b/v24c/v25/v26/v27/v28/v29/v210.rhp` 是各轮规避文件锁的编译输出，md5 与对应 yak 内 rhp 一致。
