# 验证手册：反射 / 视觉 / 打包

"编译通过"只说明语法对。改动是否真生效，必须由下面三种证据共同证明。

## 一、编译

在 Rhino 的 Python 里执行 `scripts/Compile_Roslyn.py`（支持 `ROOT`、`FILES`、`OUT_OVERRIDE` 三个 globals 覆盖）：

```python
OUT_OVERRIDE = r'C:\path\to\Plugin_vXX.rhp'
p = r'C:\path\to\skills\rhino9-plugin-workbench\scripts\Compile_Roslyn.py'
exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

输出里的 18~22 条 `CS1701 System.Drawing.Primitives` 警告是本机噪声；`0 error` 才算成功。核对产物大小与时间戳，避免拿到上一次的旧文件。

## 二、反射验证（最可靠的"代码真的跑到了"）

```python
asm = System.Reflection.Assembly.Load(File.ReadAllBytes(rhp_path))  # 不用 LoadFrom
t = asm.GetType('Namespace.Type')
m = t.GetMethod('MethodName', BindingFlags.Public | BindingFlags.Static | BindingFlags.NonPublic)
result = m.Invoke(None, args)
```

用途：
- 核对 `AssemblyVersion`、命令类数量、菜单选项注册、API 属性值
- 在 headless 文档 `Rhino.RhinoDoc.CreateHeadless('')` 里加几何对象，调用 Core 方法，读回 Plane / 文档字符串 / 对象属性断言
- 反射加载的插件 `Instance=null`，OnLoad 不触发——面板/插件生命周期不能在反射条件下判断

**交互命令不要从脚本同步驱动**：`RunScript` 送进去后 `GetPoint/GetOption` 会挂到 300 秒超时。把交互层与 Core 分离，只测 Core。"交互本身"交给用户实机点。

自动拉起的 Rhino 槽位偶发加载竞态导致 `rhino_crashed`；先跑一次 `print('alive')` 探活再干活。

## 三、视觉验证（坑最多）

### 抓到真帧的可靠流程

`CaptureToBitmap()` / `ViewCaptureToFile` 会返回**缓存帧**，只改 `vp.DisplayMode` 不触发真正重绘，导致一组不同参数的截图哈希和像素完全相同，差点得出错误结论。必须：

1. `ctypes.windll.user32.SetForegroundWindow(hwnd)` 把目标 Rhino 窗口置前（`hwnd = int(RhinoApp.MainWindowHandle())`，失败时用 `Get-Process Rhino` 查 MainWindowHandle）
2. 设置 `vp.DisplayMode` / 相机：`SetCameraLocation(...)`、`CameraUp = Vector3d(0,0,1)`、`ZoomBoundingBox(box)`
3. `view.Redraw(); doc.Views.Redraw(); Rhino.RhinoApp.Wait(); time.sleep(0.25)`
4. `bmp = view.CaptureToBitmap(Size(800,500))` → `bmp.Save(path, ImageFormat.Png)`
5. 每张图之前**重新置前**一次

`mcp__rhino__get_viewport_image` 的 `displayMode` 参数会强制重绘，但它会改变相机 up 向量；做定量对比时用自己的固定相机。

4 视图布局下 `ActiveView` 只有小格子，颜色单一容易误判"背景没生效"——先 `view.Maximized = True`。相机要在 `ZoomExtents` 之后设，或按包围盒中心+对角线手算。

### 逐像素统计（本机 Python 有 PIL 但没有 numpy）

纯 PIL 统计方法：逐行取左侧 40~60 px 的中位数作背景灰度，把偏离 >10~14 的像素当物体，排序取 P10/P50/P90、标准差、`clip(≥250)` 百分比。示例：

```python
vals = []
for y in range(H):
    bg = sorted(sum(px[x,y])/3.0 for x in range(60))[30]
    for x in range(60, W):
        v = sum(px[x,y])/3.0
        if abs(v - bg) > 12: vals.append(v)
```

注意：大块深色地面阴影会被算进"物体区"，撑大 P10~P90 跨度；统计时要意识到这一点，或裁到物体所在区域。

用 `ViewImage` 肉眼看图，和统计一起判断。两者不一致时以图为准再检查 mask。

## 四、临时显示模式清理

做参数扫描会建很多临时模式。**当场删除**：

```python
for m in list(DisplayModeDescription.GetDisplayModes()):
    if m.EnglishName.startswith(('TMP_', 'CLAY_', 'PROBE_')):
        DisplayModeDescription.DeleteDisplayMode(m.Id)
DisplayModeDescription.SaveDisplayModes()
```

删除前确认没视口在用（把视口切回 Shaded）。不要留 `ZZ_*` 之类的垃圾在用户下拉列表里。

## 五、打包与安装

1. 更新 `AssemblyInfo.cs` 版本（AssemblyVersion / AssemblyFileVersion）+ 描述
2. 更新 `Build_Package.py` 的 `RHP_SRC`、`YAK` 名、manifest 的 `version` 与 `description`
3. 跑 `python verification/Build_Package.py`，检查 `RUI XML OK`、`9/9/9` 引用链、产物字节数
4. 确认代理/梯子已关，`Yak.exe install <本地.yak>`
5. 核对：安装目录 `<包名>\<版本>\DatumPlanePlugin.rhp` 的 md5 与构建产物一致；`manifest.txt` 指向新版本
6. 告知用户重启 Rhino；面板类功能要用户实机敲命令验证

## 六、验证结果如何记录

- 工作区日志 `.workbuddy/memory/YYYY-MM-DD.md` 追加一段：日期时间、用户反馈、根因、改法、实测数据、产物哈希
- 项目 README 顶部加版本段，写清"为什么改"和"实测数字"，旧版本段标注"已被取代"但保留作技术记录
- 最终回复必须复述：结论、关键数字、安装版本、用户下一步要做什么
