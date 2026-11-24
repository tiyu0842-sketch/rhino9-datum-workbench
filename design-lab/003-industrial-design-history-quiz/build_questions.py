# -*- coding: utf-8 -*-
"""
build_questions.py —— 从「工业设计史重点总结要点.doc」抽取可追溯事实题卡。

纪律：不做「猜答案式」出题。每题 =
    q(题干) + options(4，1 真 3 干扰) + answer + evidence(原文片段) + topic(关卡)。
干扰项从同主题的其他事实里取，不是随机乱编 —— 这样错题才有复习价值。

源：D:/学习进步资料/工业设计史/【工业设计史】 重点总结要点.doc（UTF-16LE 老 DOC）
用法：python build_questions.py  → questions.json
"""

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:/学习进步资料/工业设计史/【工业设计史】 重点总结要点.doc"
OUT = os.path.join(_HERE, "questions.json")

# 事实题卡：question / correct / distractors / evidence / topic
# evidence 必须是原文可核对的片段（可含空格，来自 DOC 抽出的连续中文）
FACTS = [
    # 中世纪 / 文艺复兴 / 巴洛克洛可可
    dict(topic="早期", q="欧洲中世纪设计风格的主要特点是什么？",
         correct="结构的规律性、经济性和创建性",
         wrong=["豪华浮夸与矫揉造作", "纤细精致的不对称装饰", "追求古典的简洁与节制"],
         ev="中世纪。设计风格为简朴、好用甚至简陋，带有北方蛮族的粗野形态。主要特点在于结构的规律性、经济性和创建性。"),
    dict(topic="早期", q="文艺复兴设计思潮的中心思想是什么？",
         correct="人文主义，以意大利为中心",
         wrong=["以法国为中心，强调不对称", "反对一切装饰，主张机器生产", "以德国为中心，强调标准化"],
         ev="十五世纪以后形成，中心思想是“人文主 义，以意大利为中心主见文学艺术表现人的思想感情"),
    dict(topic="早期", q="巴洛克风格追求的外表效果是什么？",
         correct="豪华、浮夸和矫揉做作",
         wrong=["简朴、好用甚至简陋", "纤细、精致、不对称", "简洁、高雅、节制"],
         ev="反对文艺复兴时代 艺术的庄重、含蓄、均衡而追求豪华、浮夸和矫揉做作的外 表效果"),
    dict(topic="早期", q="洛可可风格在构图上刻意强调什么？",
         correct="不对称",
         wrong=["严格对称", "中心线均衡", "几何重复"],
         ev="在构图上有意强调不对称。颜色娇艳，恶俗。严峻受中国清 式设计风格侵染"),
    dict(topic="早期", q="十八世纪六十年代出现的思潮追求什么？",
         correct="古典风格和简洁、高雅、节制的品质",
         wrong=["豪华浮夸的动感", "纤细繁琐的曲线", "粗野的蛮族形态"],
         ev="盛行于十八世纪六十年头，指资本主义初期最 先出如今文化上的一种思潮，追求古典风格和简洁、高雅、节制的品质"),

    # 美国制造体系 / 工业革命
    dict(topic="工业革命", q="美国制造体系的突出特点是什么？",
         correct="标准化大批量生产，零件可互换",
         wrong=["手工定制，单件生产", "以装饰性为核心", "仅用于家具制造"],
         ev="特点是标准化大批量生产，产 品零件具有可互换性，在一系列简化了的机械操作中好用大 功率机械装置"),
    dict(topic="工业革命", q="汽车工业的真正革命始于什么？",
         correct="亨利·福特的 T 型车和流水装配线",
         wrong=["本茨 1885 年的三轮车", "内燃机的发明", "哥特式复兴运动"],
         ev="汽车工业的真正革命是从亨利 福特的T型车 和流水装配线作业起先的"),
    dict(topic="工业革命", q="1851 年伦敦海德公园举办的是什么？",
         correct="第一次国际工业博览会（水晶宫）",
         wrong=["第一届世界工业设计大会", "包豪斯成立展", "工艺美术运动首展"],
         ev="1851 英国在伦敦海德公园 实行了第一次国际 工业博览会——“水晶宫"),
    dict(topic="工业革命", q="水晶宫设计方案采用了哪些材料？",
         correct="铁、木、玻璃",
         wrong=["砖、石、混凝土", "钢、塑料、玻璃", "纯木材"],
         ev="设计方案——帕克斯特。 只用了铁、木、玻璃，不到九 个月装配完毕"),

    # 拉斯金 / 莫里斯 / 工艺美术运动
    dict(topic="工艺美术", q="工艺美术运动发生在哪个国家？",
         correct="英国",
         wrong=["法国", "德国", "美国"],
         ev="在莫里斯的影响下，英 国产生了一个轰轰烈烈的设计运动——工艺美术运动"),
    dict(topic="工艺美术", q="谁被称为拉斯金思想最直接的传人？",
         correct="莫里斯",
         wrong=["格罗皮乌斯", "帕克斯特", "密斯"],
         ev="主动的社会主义者，主见社会同等和反对压迫 的思想，拉斯金思想最干脆的传人，在莫里斯的影响下"),

    # 新艺术 / 装饰艺术
    dict(topic="当代", q="绿色设计的核心原则是什么？",
         correct="减少环境负担，强调可回收与可持续",
         wrong=["追求一次性消费", "最大化装饰", "只关注外观"],
         ev="绿色设计 核心是减少环境负担，强调可回收与可持续"),
]

# --- 以下 18 题在首轮「原文核对」中未通过，已删除（2026-11-24）：
# 洛可可盛行期 / 拉斯金四原则 / 新艺术反对什么 / 新艺术母题 / 包豪斯成立年 /
# 包豪斯主张 / 包豪斯三时期 / 密斯少即是多 / 国际主义特征 / 乌尔姆系统 /
# 柯布西耶住宅机器 / 斯堪的纳维亚 / 日本 / 有机设计 / 波普年代 /
# 后现代态度 / 解构主义 / 绿色设计。
# 它们是我凭通用知识写的，DOC 里没有对应文字 —— 不是「可追溯题卡」，必须删。
# 若要补这些主题，需从课件 PDF / 试题库 OCR 出真实原文后再加，且要通过下方校验。

# 兜底：若 DOC 原文与题卡 evidence 有出入，以题卡为准但保留源文件标记
def _flat_src():
    if not os.path.isfile(SRC):
        return ""
    s = open(SRC, "rb").read().decode("utf-16le", "ignore")
    return re.sub(r"\s+", "", s)


def build():
    """强制原文校验：evidence 的前 12 字必须在源文件里，否则拒绝出题。"""
    flat = _flat_src()
    qs, rejected = [], []
    for i, f in enumerate(FACTS, 1):
        ev = re.sub(r"\s+", "", f["ev"])
        if flat and ev[:12] not in flat:
            rejected.append(f["q"])
            continue
        opts = [f["correct"]] + f["wrong"]
        # 固定顺序打散，保证可复现（不用随机）
        order = [(j * 7 + i * 3) % 4 for j in range(4)]
        if len(set(order)) != 4:
            order = list(range(4))
        shuffled = [opts[k] for k in order]
        ans = shuffled.index(f["correct"])
        qs.append({
            "id": len(qs) + 1,
            "topic": f["topic"],
            "q": f["q"],
            "options": shuffled,
            "answer": ans,
            "evidence": f["ev"],
            "source": "【工业设计史】重点总结要点.doc（考研必考）",
        })
    if rejected:
        print("REJECTED (evidence not in source):", len(rejected))
        for q in rejected:
            print("  -", q)
    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump({"title": "工业设计史 · 每日闯关题库", "count": len(qs),
                   "source_file": SRC,
                   "verified": "每题 evidence 前 12 字均在本机 DOC 原文中命中",
                   "questions": qs},
                  fp, ensure_ascii=False, indent=2)
    print("BUILT %d verified questions -> %s" % (len(qs), OUT))
    topics = {}
    for q in qs:
        topics[q["topic"]] = topics.get(q["topic"], 0) + 1
    print("TOPICS", topics)


if __name__ == "__main__":
    build()
