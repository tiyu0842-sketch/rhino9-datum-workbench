# -*- coding: utf-8 -*-
"""
build_app.py — 把 content/*.json + art.py 组装成单文件离线应用 design-history.html

数据流：
  world.json + china.json → stations（每站注入作品 SVG）
  stations → cards（作品卡 + 人物卡，卡片模式与测验联动）
  bank.json → 题库
  app.tpl  → 模板，__DATA__ 一次性注入
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")


def load(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    world = load("world.json")
    china = load("china.json")
    bank = load("bank.json")

    stations = []
    cards = []

    for src in (china, world):
        for st in src["stations"]:
            if "track" not in st:
                st["track"] = src["track"]
            # 注入作品 SVG
            for w in st["works"]:
                key = w.get("art")
                svg = art.ART.get(key)
                if svg is None:
                    raise SystemExit("缺图: %s (%s)" % (key, w["name"]))
                w["svg"] = svg
            stations.append(st)

            # 作品卡
            for i, w in enumerate(st["works"]):
                cards.append({
                    "id": "%s-w%d" % (st["id"], i),
                    "type": "work",
                    "track": st["track"],
                    "stage": st["id"],
                    "stationTitle": st["era"],
                    "topic": (st.get("topics") or [None])[0],
                    "title": w["name"],
                    "sub": st["era"],
                    "year": w.get("year", ""),
                    "svg": w["svg"],
                    "tint": w.get("tint"),
                    "meta": [
                        ["年代", w.get("year", "—")],
                        ["作者 / 产地", w.get("author", "—")],
                        ["材料", w.get("mat", "—")],
                    ],
                    "why": w.get("why", ""),
                })
            # 人物卡
            for j, p in enumerate(st["people"]):
                first = p["n"][0] if p["n"] else "?"
                cards.append({
                    "id": "%s-p%d" % (st["id"], j),
                    "type": "person",
                    "track": st["track"],
                    "stage": st["id"],
                    "stationTitle": st["era"],
                    "topic": (st.get("topics") or [None])[0],
                    "title": p["n"],
                    "sub": p.get("r", ""),
                    "year": p.get("y", ""),
                    "svg": None,
                    "tint": None,
                    "initial": first,
                    "meta": [
                        ["生卒 / 年代", p.get("y", "—")],
                        ["身份", p.get("r", "—")],
                        ["所处", st["era"]],
                    ],
                    "why": p.get("idea", ""),
                    "quote": p.get("quote") or "",
                })

    # 排序（中国与世界按年代并置）
    stations.sort(key=lambda s: s.get("sort", 0))

    data = {
        "thread": {
            "question": "机器能造东西、能造得极精之后，东西到底该做成什么样？",
            "answer": "世界线用一百五十年争论「装饰还是功能」；中国线用五千年回答「器如何载道」——两条线在同一个页面并置，互为参照。",
            "tensions": [
                {"name": "装饰 ↔ 功能", "desc": "好看与好用，天平来回摆了三千年。"},
                {"name": "手作 ↔ 机器", "desc": "躲开机器，还是为机器而设计？"},
                {"name": "宫廷 ↔ 大众", "desc": "为少数人做珍品，还是为普通人做好东西？"},
                {"name": "器 ↔ 道", "desc": "中国线独有的问题：器物如何承载秩序与修养。"},
            ],
        },
        "stations": stations,
        "cards": cards,
        "bank": bank["questions"],
    }

    with open(os.path.join(HERE, "app.tpl"), encoding="utf-8") as f:
        tpl = f.read()

    html = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out = os.path.join(HERE, "design-history.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    n_q = len(bank["questions"])
    n_topic = len({q["topic"] for q in bank["questions"]})
    print("OK ->", out)
    print("站点 %d（世界 %d / 中国 %d），卡片 %d，题目 %d（%d 章），文件 %.1f KB" % (
        len(stations),
        sum(1 for s in stations if s["track"] == "world"),
        sum(1 for s in stations if s["track"] == "china"),
        len(cards), n_q, n_topic, os.path.getsize(out) / 1024))


if __name__ == "__main__":
    main()
