# -*- coding: utf-8 -*-
"""
review_images.py — 自动抓取图的人工审查结论（可追溯、可重跑）

方法：build_contact_sheet.py 生成联系表 → 逐格目视核对「作品名 ↔ 图内容」→
把明显错配写进 REJECT，同类但器形/角度有偏差的写进 APPROX，其余视为通过。

纪律：宁缺毋滥。删掉错图让该作品回到「线描 + 在线搜图入口」，
      也不留一张会让人记错的实物图；近似图在界面上明确标注，不假装准确。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
CONTENT = os.path.join(HERE, "content")
META = os.path.join(CONTENT, "images.json")
REVIEW = os.path.join(CONTENT, "image_review.json")

# 明显错配：图的内容根本不是该作品（人像 / 图纸 / 建筑 / 地图 / 别的器物）
REJECT = {
    "c01-w1": "蛋壳黑陶高柄杯 → 抓成黑色玻璃高脚杯，不是龙山蛋壳陶",
    "c01-w2": "玉璧 → 抓成玉衣下的彩色织物照片，看不出玉璧",
    "c02-w1": "青铜爵 → 抓成青铜人形立像，器形完全不对",
    "c02-w2": "玉佩组 → 抓成彩色织物挂件，非玉佩",
    "c03-w1": "素纱襌衣 → 抓成织物残片特写，不是成衣",
    "c03-w2": "长乐未央瓦当 → 抓成筒瓦，不是带文字的圆瓦当",
    "c04-w0": "越窑青瓷鸡首壶 → 抓成四系青瓷罐，无鸡首",
    "c05-w1": "越窑秘色瓷 → 与 c04-w0 抓到同一张四系罐（重复且不对）",
    "c05-w2": "唐代高型坐具 → 抓成黄色地图/示意图，不是家具",
    "c06-w0": "汝窑天青釉洗 → 抓成白釉瓷枕，器形与釉色都不对",
    "c06-w1": "钧窑玫瑰紫花盆 → 抓成月白釉碗，无玫瑰紫",
    "c06-w2": "定窑白瓷印花盘 → 抓成白瓷执壶，不是盘",
    "c09-w0": "清式太师椅 → 抓成白描人物插画，不是椅子",
    "c10-w1": "图案学教材与织物纹样 → 抓成陈之佛肖像照",
    "w03-w0": "佛罗伦萨大教堂穹顶 → 抓成结构剖视图纸，非实物照片",
    "w04-w1": "齐彭代尔式座椅 → 抓成家具设计图纸",
    "w05-w1": "亚当式座椅与室内 → 抓成庄园建筑外景",
    "w05-w2": "帝国风格座椅 → 抓成百科黑白版画插图",
    "w06-w0": "水晶宫 → 抓成帕克斯顿半身雕像",
    "w08-w2": "新艺术风格海报与书籍 → 抓成穆夏画的人物肖像，不是海报",
    "w09-w0": "麦金托什高背椅 → 抓成家具设计图纸",
    "w09-w1": "AEG 电水壶 → 抓成 AEG 工厂平面/立面图",
    "w11-w1": "装饰艺术风格海报与餐具 → 抓成旋转楼梯",
    "w12-w1": "贝尔 500 型电话 → 抓成一口钟（Chersonesos Bell）",
    "w12-w2": "灰狗巴士 → 抓成黑白局部特写，辨认不出车体",
    "w14-w1": "Sacco 豆袋椅 → 抓成三位设计师肖像",
    "w16-w0": "第一代 iPhone → 抓成另一款手机上的 App 照片",
    "w16-w2": "可持续 / 循环设计 → 抓成会议演讲人像",
}

# 同类器物但器形、角度或细节有偏差：保留，但界面上标「近似」
APPROX = {
    "c01-w0": "仰韶彩陶罐带纹样，与「人面鱼纹彩陶盆」同类但非该件",
    "c08-w3": "桌面上的青花碗，角度与所标注器形略有出入",
    "w01-w1": "希腊黑绘陶瓶的颈部局部特写，非整器",
    "w02-w1": "哥特式箱柜的雕花板局部",
    "w10-w1": "布劳耶本人坐在瓦西里椅上，人物入镜但椅子清晰",
    "w12-w0": "1915 年可口可乐弧形瓶原型，非量产成品",
    "w14-w2": "蓝色充气动物坐椅，为同类充气坐具而非指定款",
    "w15-w2": "后现代建筑外景，代表性一般",
}


def main():
    meta = json.load(open(META, encoding="utf-8")) if os.path.exists(META) else {}
    removed, kept, approx = [], [], []
    for key in sorted(REJECT):
        p = os.path.join(ASSETS, key + ".jpg")
        if os.path.exists(p):
            os.remove(p)
        meta.pop(key, None)
        removed.append(key)
    for key in list(meta.keys()):
        if key in APPROX:
            meta[key]["review"] = "近似"
            approx.append(key)
        else:
            meta[key]["review"] = "已核对"
            kept.append(key)
    with open(META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    with open(REVIEW, "w", encoding="utf-8") as f:
        json.dump({"rejected": REJECT, "approximate": APPROX,
                   "kept": kept, "method": "联系表逐格目视核对"},
                  f, ensure_ascii=False, indent=1)
    print("剔除 %d 张明显错配，保留 %d 张（其中 %d 张标为近似）" % (
        len(removed), len(kept) + len(approx), len(approx)))
    print("剩余实物图：%d 张" % len(meta))


if __name__ == "__main__":
    main()
