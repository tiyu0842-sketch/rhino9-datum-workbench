# -*- coding: utf-8 -*-
"""
build_worldline_html.py —— 把三份数据注入 worldline.html.tpl，产单文件 worldline.html

唯一数据源纪律：叙事用 worldline.json（公开来源标注），题目用 questions.json（DOC 原文校验），
科普卡用 science_cards.json。HTML 不手抄任何内容。
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(_HERE, "worldline.html.tpl")
OUT = os.path.join(_HERE, "worldline.html")


def load(name):
    with open(os.path.join(_HERE, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    world = load("worldline.json")
    quiz = load("questions.json")
    cards = load("science_cards.json")

    with open(TPL, encoding="utf-8") as f:
        html = f.read()

    subs = {
        "__SUBTITLE__": world["subtitle"],
        "__WORLD_DATA__": json.dumps(world, ensure_ascii=False),
        "__QUIZ_DATA__": json.dumps(quiz, ensure_ascii=False),
        "__CARD_DATA__": json.dumps(cards, ensure_ascii=False),
    }
    for k, v in subs.items():
        html = html.replace(k, v)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    left = [k for k in subs if k in html]
    print("BUILT %s (%d bytes)" % (os.path.basename(OUT), len(html.encode("utf-8"))))
    print("placeholders left:", left if left else "none")
    print("world stations:", len(world["world"]), "| questions:", quiz["count"],
          "| cards:", len(cards))


if __name__ == "__main__":
    main()
