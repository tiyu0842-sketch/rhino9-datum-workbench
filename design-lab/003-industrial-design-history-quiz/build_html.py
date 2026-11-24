# -*- coding: utf-8 -*-
"""
build_html.py —— 把 questions.json 注入 quiz.html.tpl，产出单文件 quiz.html。

纪律：题库是唯一数据源，HTML 里不手抄题目（手抄就会漂移）。
用法：python build_html.py
"""

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(_HERE, "quiz.html.tpl")
DATA = os.path.join(_HERE, "questions.json")
OUT = os.path.join(_HERE, "quiz.html")

MARK = "__QUIZ_DATA__"


def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    with open(TPL, encoding="utf-8") as f:
        html = f.read()
    if MARK not in html:
        raise SystemExit("模板里找不到占位符 " + MARK)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # 防止题目文本里出现 </script> 破坏页面
    payload = payload.replace("</", "<\\/")
    html = html.replace(MARK, payload)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print("BUILT %s  %d questions  %.1f KB"
          % (OUT, data.get("count", 0), os.path.getsize(OUT) / 1024))


if __name__ == "__main__":
    main()
