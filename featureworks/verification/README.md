# 验证与编译脚本

这些脚本是 v1.2 → v1.3.2 迭代过程中**逐条探测 RhinoCommon 行为**留下的实证记录。
它们是「先验证再相信」的证据，不是给最终用户用的一键工具。

## 路径说明

所有脚本的路径都是**可移植**的：默认以脚本自身所在目录的父目录（`featureworks/`）作为插件根，
从 `../src/` 读源码、从 `../RhinoFeatureWorks.rhp` 读编译产物。不含任何本机绝对路径。

如果要在别处运行或需要覆盖，在 `exec` 之前设置同名全局变量即可：

```python
import os
ROOT = r"<你的 featureworks 目录>"          # Compile / Build / Verify 用
OUT_OVERRIDE = os.path.join(ROOT, "RhinoFeatureWorks_v2.rhp")  # 避开 LoadFrom 文件锁
RHP = os.path.join(ROOT, "RhinoFeatureWorks.rhp")              # Probe_* 用
ASSEMBLY_NAME = "RhinoFeatureWorksC7"                          # 隔离 AppDomain 同名程序集
p = r"<path-to>/featureworks/verification/Compile_Roslyn.py"
exec(compile(open(p, encoding="utf-8").read(), p, "exec"))
```

> Rhino 的 Python 里 `exec(compile(...))` 时 `__file__` 往往不存在，脚本已用 `os.getcwd()` 兜底；
> 此时**务必显式设置 `ROOT` / `RHP`**，否则会指向当前工作目录。通用模板见
> `../../skill/scripts/Compile_Roslyn.py`（支持 `ROOT` / `FILES` / `OUT_OVERRIDE` / `ASSEMBLY_NAME` 覆盖）。

## 文件

| 脚本 | 作用 |
|---|---|
| `Compile_Roslyn.py` | 在 Rhino 进程内用 Roslyn 把 `../src/*.cs` 编成 `.rhp`（本机无 .NET SDK） |
| `Build_Package.py` | 把 manifest + rhp + README 打成 `.yak` |
| `Verify_Engine.py` | 反射加载 rhp，验证类型 / 命令 / 版本 / Core 方法 |
| `Probe_*.py` | 逐条探测：`Brep.UntrimFace` / `UntrimOuterLoop` / 二面角 / 内环信号 / 槽 / 重缝链 / 语义等 |

`Probe_*` 记录的是"当时为什么这么判断"，包括被推翻的假设；结论汇总在
`../../skill/references/experiment-log.md`（E-004 ~ E-012）与
`../../skill/references/feature-recognition.md`。
