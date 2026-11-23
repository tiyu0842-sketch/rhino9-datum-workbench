# -*- coding: utf-8 -*-
"""Build the RhinoFeatureWorks Yak package. Pure local Python 3, no Rhino needed.

    python verification/Build_Package.py [version]

Yak package is a plain zip: manifest.yml + RhinoFeatureWorks.rhp (+ README).
Idempotent: rebuild overwrites the .yak for the given version.
"""
import io
import os
import sys
import shutil
import zipfile
import hashlib

ROOT = os.environ.get("FEATUREWORKS_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL = os.path.join(ROOT, "install")
RHP = "RhinoFeatureWorks.rhp"
VERSION = sys.argv[1] if len(sys.argv) > 1 else "1.0.0.0"
YAK = os.path.join(ROOT, "RhinoFeatureWorks_v%s.yak" % VERSION)

README = """# 特征识别工具 / RhinoFeatureWorks v%s

Rhino 9 SolidWorks FeatureWorks 风格特征识别插件（独立包，与「基准面工具」并存）。

## 命令
- `FWPanel` —— **可视化停靠面板**（推荐）：列出特征、点选高亮、改参数、一键修复
- `FW` / `FeatureWorks` —— 统一字母菜单入口（敲下划线字母选功能）
- `FWRecognize` 识别选中实体：圆角链 / 孔 / 拉伸切除
- `FWList` 列出特征树 · `FWTest` 9 项端到端自测
- `FWHighlight` 高亮 · `FWSuppress` 抑制 · `FWRebuild` 参数重算
- `FWStatus` 状态 · `FWClear` 清除
- `FWEvidence` 曲面原生/修剪证据：逐面报告底层曲面类型、trim 环数、未修剪余量，推断加工史
- `FWRepair` 整体修复：删掉所有已识别特征面，用底层原生曲面缝回毛坯

## 技术要点
- AFAG 属性面邻接图 + 三趟洋葱剥皮识别
- 凹区判定基于几何不变量（有效法向 + bbox 投影极值），不依赖 OrientationIsReversed
- 槽深取真实 trim 边端点投影跨度，不受未修剪曲面 domain 干扰
- 特征树写入 Brep.UserDictionary，随 .3dm 持久化
- 抑制/重建：删面补洞 + 槽口平面定位 + 布尔工具沿轴摆正
- 曲面证据：B-rep 面 = 完整底层曲面 + trim 环；比较 domain 与 trim 边界反推孔/槽/倒角
- 整体修复：删特征面 → UnderlyingSurface().ToBrep() 取回原生曲面 → CreateSolid 重新缝合
  （实测 100x80x30 带孔带槽块 → 240000 毛坯；倒角盒删 4 圆角 → 240000 尖角毛坯）

## 可视化面板（FWPanel）
点「识别选中实体」→ 特征列出 → 点选一项 → 高亮/抑制/改参数重建；底部有整体修复、证据、自测。

## 菜单字母（FW 回车后）
A 识别 · B 列表 · C 高亮 · D 抑制 · E 重建 · F 自测 · G 清除 · H 状态
I 曲面证据 · J 整体修复
""" % VERSION

readme_path = os.path.join(ROOT, "README.md")
manifest_path = os.path.join(ROOT, "manifest.yml")
# v1.5 起：README / manifest 是人工维护的交付文档，打包脚本**不得覆盖**。
# 旧版脚本每次 build 都把这两个文件重写成 v1.0 模板，导致包内说明与真实功能脱节。
if not os.path.exists(readme_path):
    with io.open(readme_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(README)
if not os.path.exists(manifest_path):
    manifest = """---
name: 特征识别工具
version: %s
authors:
- FeatureWorks Tools
description: Rhino 9 FeatureWorks-style feature recognition v%s - AFAG face adjacency graph, onion-peel recognition (fillet chains / holes / extrude cuts)
url: https://www.rhino3d.com
keywords: []
platform: win
""" % (VERSION, VERSION)
    with io.open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(manifest)

if not os.path.isdir(INSTALL):
    os.makedirs(INSTALL)
shutil.copyfile(os.path.join(ROOT, RHP), os.path.join(INSTALL, RHP))
shutil.copyfile(manifest_path, os.path.join(INSTALL, "manifest.yml"))
shutil.copyfile(readme_path, os.path.join(INSTALL, "README.md"))
print("install/: synced rhp + manifest + README")

FILES = [RHP, "manifest.yml", "README.md"]
# 手册与交互规格存在时一并入包，避免用户装完只能看命令行提示。
for extra in ("使用手册.md", "INTERACTION_SPEC.md"):
    if os.path.exists(os.path.join(ROOT, extra)):
        FILES.append(extra)
        shutil.copyfile(os.path.join(ROOT, extra), os.path.join(INSTALL, extra))
with zipfile.ZipFile(YAK, "w", zipfile.ZIP_DEFLATED) as z:
    for f in FILES:
        z.write(os.path.join(ROOT, f), f)
print("built %s (%d bytes)" % (YAK, os.path.getsize(YAK)))
for f in FILES:
    print("   %-28s %7d" % (f, os.path.getsize(os.path.join(ROOT, f))))
print("sha256 yak =", hashlib.sha256(open(YAK, "rb").read()).hexdigest())
print("sha256 rhp =", hashlib.sha256(open(os.path.join(ROOT, RHP), "rb").read()).hexdigest())
