# -*- coding: utf-8 -*-
"""单位换算唯一数据源 —— 整个 m2s 链只在这里定义一次。

修订记录
--------
2026-11-25 15:34：用户实测猫爪笔筒真实高度 **16 cm = 160 mm**，推翻上一轮
「1 数值单位 = 100 mm / 高 104.4 mm」的推测。STL 包围盒 Z 跨度实测
= 1.044031023979187，于是 1 数值单位 = 160 / 1.044031 ≈ 153.2522 mm。

纪律
----
* 几何量（坐标 / 半径 / RMS / 容差）一律保持 STL 数值单位，不做隐式缩放；
* 只有展示层（`*_mm` 字段、报告文字、README 表格）才调用 `mm()`；
* 以后用户再给实测尺寸，**只改 `MODEL_HEIGHT_MM` 一行**，其余全部自动跟随。
* 禁止在别的模块里再写 `100.0` / `153.25` 这类散落系数。
"""
from __future__ import division

MODEL_HEIGHT_MM = 160.0                   # 用户实测：猫爪笔筒真实高度
BBOX_Z = 1.044031023979187                # STL 实测包围盒 Z 跨度
MM_PER_UNIT = MODEL_HEIGHT_MM / BBOX_Z    # ≈ 153.2521508702 mm / 数值单位


def mm(v):
    """数值单位 → mm。所有展示层 mm 数值必须走这里。"""
    return v * MM_PER_UNIT


UNITS_HINT = (
    "用户实测实物高 %.0f mm，STL Z=%.6f → 1 数值单位 = %.6f mm；"
    "结果中 radius/rms/坐标均为数值单位，*_mm 字段为换算后的展示值"
    % (MODEL_HEIGHT_MM, BBOX_Z, MM_PER_UNIT)
)

SCALE_HINT = (
    "Rhino 直接按 mm 读入会小 %.2f 倍，导入后需 _Scale 或在脚本中换算单位；"
    "所有 RMS 数值也按 ×%.6f 换算成 mm。"
    % (MM_PER_UNIT, MM_PER_UNIT)
)
