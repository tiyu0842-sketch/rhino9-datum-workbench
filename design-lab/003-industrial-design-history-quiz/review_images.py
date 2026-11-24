# -*- coding: utf-8 -*-
"""
review_images.py — 实物图人工审查结论（可追溯、可重跑）

方法：build_contact_sheet.py 生成联系表 → 逐格目视核对「作品名 ↔ 图内容」→
      把明显错配写进 REJECT，同类但器形/角度有偏差的写进 APPROX，其余视为通过。

纪律：宁缺毋滥。**错图比没图更有害**，尤其这是给考研记器形用的。

v7 变更（2026-11-24 晚）：
  v6 的 REJECT 是「删除 assets 里的错图」；但 v7 用精确文件名直取把其中多数
  作品重新补上了正确的图，若再跑旧逻辑会把新图误删。因此改为：
  - REJECT_V6 只作历史追溯记录，不再执行删除；
  - 统一按当前 images.json 的实际内容打 review 标签（已核对 / 近似）；
  - v7 新发现的一张错配（w09-w1 现代塑料水壶）已换真实文件名重抓，记入 REJECT_V7。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
CONTENT = os.path.join(HERE, "content")
META = os.path.join(CONTENT, "images.json")
REVIEW = os.path.join(CONTENT, "image_review.json")

# v6 自动抓图被剔除的 28 张：历史记录，仅用于追溯「当时错在哪」，不删除当前文件
REJECT_V6 = {
    "c01-w1": "蛋壳黑陶高柄杯 → 抓成黑色玻璃高脚杯",
    "c01-w2": "玉璧 → 抓成玉衣下的彩色织物照片",
    "c02-w1": "青铜爵 → 抓成青铜人形立像",
    "c02-w2": "玉佩组 → 抓成彩色织物挂件",
    "c03-w1": "素纱襌衣 → 抓成织物残片特写",
    "c03-w2": "长乐未央瓦当 → 抓成筒瓦",
    "c04-w0": "越窑青瓷鸡首壶 → 抓成四系青瓷罐",
    "c05-w1": "越窑秘色瓷 → 与 c04-w0 抓到同一张四系罐",
    "c05-w2": "唐代高型坐具 → 抓成黄色地图/示意图",
    "c06-w0": "汝窑天青釉洗 → 抓成白釉瓷枕",
    "c06-w1": "钧窑玫瑰紫花盆 → 抓成月白釉碗",
    "c06-w2": "定窑白瓷印花盘 → 抓成白瓷执壶",
    "c09-w0": "清式太师椅 → 抓成白描人物插画",
    "c10-w1": "图案学教材与织物纹样 → 抓成陈之佛肖像照",
    "w03-w0": "佛罗伦萨大教堂穹顶 → 抓成结构剖视图纸",
    "w04-w1": "齐彭代尔式座椅 → 抓成家具设计图纸",
    "w05-w1": "亚当式座椅与室内 → 抓成庄园建筑外景",
    "w05-w2": "帝国风格座椅 → 抓成百科黑白版画插图",
    "w06-w0": "水晶宫 → 抓成帕克斯顿半身雕像",
    "w08-w2": "新艺术风格海报与书籍 → 抓成穆夏画的人物肖像",
    "w09-w0": "麦金托什高背椅 → 抓成家具设计图纸",
    "w09-w1": "AEG 电水壶 → 抓成 AEG 工厂平面/立面图",
    "w11-w1": "装饰艺术风格海报与餐具 → 抓成旋转楼梯",
    "w12-w1": "贝尔 500 型电话 → 抓成一口钟",
    "w12-w2": "灰狗巴士 → 抓成黑白局部特写",
    "w14-w1": "Sacco 豆袋椅 → 抓成三位设计师肖像",
    "w16-w0": "第一代 iPhone → 抓成另一款手机上的 App 照片",
    "w16-w2": "可持续 / 循环设计 → 抓成会议演讲人像",
}

# v7 联系表发现并已修复的错配
REJECT_V7 = {
    "w09-w1": "首轮精确直取抓成现代白色塑料电热水壶（AEG kettle.jpg 属通用分类）→ "
              "已剔除并改用 Behrens-aeg-wasserkocher.jpg 重抓："
              "三只 1909 年锤纹金属壶 + 藤编提梁，才是贝伦斯 AEG 壶",
}

# 同类器物但器形、角度、材质或细节有偏差：保留，但界面上标「近似」
APPROX = {
    # v6 保留的 8 张
    "c01-w0": "仰韶彩陶罐带纹样，与「人面鱼纹彩陶盆」同类但非该件",
    "c08-w3": "桌面上的青花碗，角度与所标注器形略有出入",
    "w01-w1": "希腊黑绘陶瓶的颈部局部特写，非整器",
    "w02-w1": "哥特式箱柜的雕花板局部",
    "w10-w1": "布劳耶本人坐在瓦西里椅上，人物入镜但椅子清晰",
    "w12-w0": "1915 年可口可乐弧形瓶原型，非量产成品",
    "w14-w2": "蓝色充气动物坐椅，为同类充气坐具而非指定款",
    "w15-w2": "后现代建筑外景，代表性一般",
    # v7 新增 10 张
    "c03-w1": "马王堆汉代袍服（Mawangdui Han Gown），是同类西汉丝织衣，但不是 49 克素纱襌衣",
    "c08-w1": "赛克勒美术馆藏低背扶手椅，非典型「四出头官帽椅」，搭脑与扶手形制有差",
    "c08-w2": "明清黄花梨平头案，两端未见明显翘头",
    "c08-w4": "绿釉描金茶壶，是宜兴壶类但非典型素面紫砂",
    "w03-w0": "佛罗伦萨大教堂黑白大理石立面局部，画面未拍到布鲁内莱斯基穹顶",
    "w04-w1": "齐彭代尔式高背栅格椅的黑白图版，非彩色实物照",
    "w05-w2": "美式帝国风格绿缎沙发，同类风格但是沙发不是座椅",
    "w06-w0": "水晶宫外观的历史彩色绘画/版画，非照片",
    "w06-w2": "1851 年博览会象牙宝座的黑白版画，属「过度装饰展品」但非彩色实物照",
    "w10-w3": "展柜玻璃罩内的包豪斯台灯（含 Jucker 与 Wagenfeld 两盏并列），非 MT8 单品特写",
}


def main():
    meta = json.load(open(META, encoding="utf-8")) if os.path.exists(META) else {}
    kept, approx = [], []
    for key in sorted(meta):
        label = "近似" if key in APPROX else "已核对"
        meta[key]["review"] = label
        (approx if label == "近似" else kept).append(key)
        # 缺文件就如实记录，不假装存在
        if not os.path.exists(os.path.join(ASSETS, key + ".jpg")):
            meta[key]["review"] = "缺文件"
    with open(META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    with open(REVIEW, "w", encoding="utf-8") as f:
        json.dump({
            "v6_rejected": REJECT_V6,
            "v7_recheck_and_fixed": REJECT_V7,
            "approximate": APPROX,
            "kept": kept,
            "method": "build_contact_sheet.py 生成联系表 → 逐格目视核对（v7 新增 --new 只看新增图）",
            "note": "v6 的 28 张错配为历史记录；v7 用精确文件名直取把其中多数重新补上了正确图，不再删除当前文件。",
        }, f, ensure_ascii=False, indent=1)
    print("审查完成：%d 张已核对，%d 张标「近似」，合计 %d 张实物图" % (
        len(kept), len(approx), len(meta)))


if __name__ == "__main__":
    main()
