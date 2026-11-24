# -*- coding: utf-8 -*-
"""
build_html.py —— 把 questions.json + science_cards.json 注入模板，产出单文件 HTML。

用途：
  python build_html.py              # v2（艾宾浩斯 + 双风格 + 错题科普）
  python build_html.py --legacy     # 旧版单卡片（保留兼容）

纪律：题库与科普卡是唯一数据源，HTML 里不手抄内容（手抄就会漂移）。
"""

import argparse
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
TPL_V2 = os.path.join(_HERE, "quiz_v2.html.tpl")
TPL_OLD = os.path.join(_HERE, "quiz.html.tpl")
DATA = os.path.join(_HERE, "questions.json")
CARDS = os.path.join(_HERE, "science_cards.json")
OUT_V2 = os.path.join(_HERE, "quiz_v2.html")
OUT_OLD = os.path.join(_HERE, "quiz.html")

M1, M2 = "__QUIZ_DATA__", "__CARD_DATA__"


def clean(s):
    return s.replace("</", "<\\/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", action="store_true")
    args = ap.parse_args()

    with open(DATA, encoding="utf-8") as f:
        quiz = json.load(f)
    qpay = clean(json.dumps(quiz, ensure_ascii=False, separators=(",", ":")))

    if args.legacy:
        with open(TPL_OLD, encoding="utf-8") as f:
            html = f.read()
        if M1 not in html:
            raise SystemExit("旧模板缺占位符 " + M1)
        out = OUT_OLD
        html = html.replace(M1, qpay)
    else:
        with open(CARDS, encoding="utf-8") as f:
            cards = json.load(f)
        with open(TPL_V2, encoding="utf-8") as f:
            html = f.read()
        if M1 not in html or M2 not in html:
            raise SystemExit("v2 模板缺占位符 " + M1 + " 或 " + M2)
        out = OUT_V2
        html = html.replace(M1, qpay)
        html = html.replace(M2, clean(json.dumps(cards, ensure_ascii=False,
                                                  separators=(",", ":"))))

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("BUILT %s  %d questions  %.1f KB"
          % (out, quiz.get("count", 0), os.path.getsize(out) / 1024))


if __name__ == "__main__":
    main()
