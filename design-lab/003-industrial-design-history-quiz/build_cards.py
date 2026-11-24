# -*- coding: utf-8 -*-
"""
build_cards.py —— 为每道题生成「错题科普卡」。

科普卡纪律（据 3Blue1Brown 风格 SPEC 的降认知负荷原则）：
  1. 一张卡只讲一个 idea，不列清单；
  2. Picture first：先给一个能想象的生活画面，再给名字；
  3. 每卡只新增 ≤1 个术语；
  4. 结尾一句话可复述；
  5. 每条外部科普都带来源 URL，原文证据来自本机 DOC —— 两者分开标注，不混。

输出：science_cards.json（按题目 id 索引）
"""

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "science_cards.json")

BAIDE_ARTS = "https://baike.baidu.com/article/dfe1324094c45d68bfb97f90.htm"
BAIDE_CRAFT = "https://baike.baidu.com/item/%E5%B7%A5%E8%89%BA%E7%BE%8E%E6%9C%AF%E8%BF%90%E5%8A%A8"
BAIDE_DESIGN = "https://baike.baidu.com/item/DESIGN/3117302"
BAIDE_MORRIS = "https://baike.baidu.com/view/3204415.htm"

# 每题一张科普卡：scene(生活画面) / point(一句话结论) / why(为什么，≤2句) / more(延伸) / src
CARDS = {
    1: dict(scene="想象一把椅子：能坐、结实、不浪费木料，表面不加花纹。",
            point="中世纪设计先把「能用、好用」放在前面。",
            why="它不像后来的巴洛克那样追求华丽，而是靠结构的规律和省料取胜。",
            more="这就是设计史里反复出现的两条线：一条重功能，一条重装饰。",
            src=BAIDE_DESIGN, srcn="百度百科·设计"),
    2: dict(scene="一幅画里的人有了自己的表情和情绪，而不是只有宗教符号。",
            point="文艺复兴把目光从神转向人，这就是「人文主义」。",
            why="中心在意大利；艺术开始表现人的思想感情，科学也开始为人生服务。",
            more="人文主义不是「不要宗教」，而是把人放回世界的中心。",
            src=BAIDE_DESIGN, srcn="百度百科·设计"),
    3: dict(scene="走进一个大厅：柱子是扭的，墙上满是起伏的涡形装饰，光照在金子上。",
            point="巴洛克要的是动感和豪华，不是安静的对称。",
            why="它故意打破文艺复兴的庄重与均衡，用夸张的曲线制造激情。",
            more="看到「扭动 + 宏大 + 金色」，先想到巴洛克。",
            src=BAIDE_DESIGN, srcn="百度百科·设计"),
    4: dict(scene="路易十五的房间：细腿、卷草、粉彩，装饰轻得像蕾丝。",
            point="洛可可是18世纪法国宫廷的纤细趣味。",
            why="它比巴洛克更轻、更碎、更不对称，还受到中国清代装饰的影响。",
            more="巴洛克是「厚重的豪华」，洛可可就是「轻巧的精致」。",
            src=BAIDE_DESIGN, srcn="百度百科·设计"),
    5: dict(scene="一个柜子的左右两边并不镜像，却看着很平衡。",
            point="洛可可刻意追求不对称。",
            why="对称显得庄重，不对称才显得轻快、流动、有生命力。",
            more="这也是它和古典主义最直观的区别。",
            src=BAIDE_DESIGN, srcn="百度百科·设计"),
    6: dict(scene="庞贝古城挖出了古罗马的别墅，人们突然迷上了那种安静的直线。",
            point="新古典主义向古典要回简洁和节制。",
            why="它反对洛可可的繁琐，追求对称、有序、高贵的品质。",
            more="注意它和「复古」不同：借的是精神，不是照抄。",
            src=BAIDE_ARTS, srcn="百度百科·家居设计史"),
    7: dict(scene="一支枪的零件坏了，随便拿另一个同型号的换上就能用。",
            point="美国制造体系的核心是标准化、可互换。",
            why="零件按同一尺寸批量做，装配就变成简单重复的机械操作。",
            more="这套思路后来直接影响福特流水线。",
            src=None, srcn="本机 DOC 原文（外部来源未核实，不作扩展）"),
    8: dict(scene="汽车不是从有钱人的玩具变普及的，而是从「流水线」开始变便宜的。",
            point="真正的革命是福特的 T 型车 + 流水装配线。",
            why="流水线把装配拆成连续动作，产量上去、价格下来，汽车才进入普通人生活。",
            more="本茨1885年的三轮车更早，但它是「发明汽车」，不是「改变生产」。",
            src=None, srcn="本机 DOC 原文（外部来源未核实，不作扩展）"),
    9: dict(scene="1851年伦敦，一座通体透明的大房子，几个月就搭好了。",
            point="水晶宫是第一次国际工业博览会。",
            why="它想炫耀工业成就，也想顺便提高公众审美、制止对旧风格的乱抄。",
            more="它自己的价值在「新材料」，展品却被批评为过度装饰。",
            src=BAIDE_CRAFT, srcn="百度百科·工艺美术运动"),
    10: dict(scene="一座房子几乎只用铁、木、玻璃，像搭积木一样装起来。",
            point="水晶宫证明了新材料与预制装配的威力。",
            why="不到九个月完工，靠的是标准化构件和现场装配。",
            more="它也被看作20世纪现代建筑的先声。",
            src=BAIDE_CRAFT, srcn="百度百科·工艺美术运动"),
    11: dict(scene="莫里斯看了水晶宫的展品很不舒服，决心自己做「诚实的」东西。",
            point="莫里斯是拉斯金思想的直接传人，英国工艺美术运动由此而起。",
            why="他主张手工、自然材料、反对粗制滥造的工业品。",
            more="注意：他反对的是机械化生产，这一点和后来包豪斯正好相反。",
            src=BAIDE_CRAFT, srcn="百度百科·工艺美术运动"),
}


def main():
    with open(os.path.join(_HERE, "questions.json"), encoding="utf-8") as f:
        qs = json.load(f)["questions"]
    out = {}
    for q in qs:
        c = CARDS.get(q["id"])
        if not c:
            continue
        out[str(q["id"])] = dict(
            scene=c["scene"], point=c["point"], why=c["why"],
            more=c["more"], src=c["src"], srcn=c["srcn"],
            evidence=q["evidence"], topic=q["topic"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("BUILT %d science cards -> %s" % (len(out), OUT))
    miss = [q["id"] for q in qs if str(q["id"]) not in out]
    if miss:
        print("MISSING cards for question ids:", miss)


if __name__ == "__main__":
    main()
