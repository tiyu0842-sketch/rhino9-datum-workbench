# -*- coding: utf-8 -*-
"""
build_app.py — 把 content/*.json + art.py + assets/*.jpg 组装成单文件离线应用

数据流：
  world.json + china.json → stations（作品 SVG / 实物图 / 小故事）
  stations → cards（作品卡 + 人物卡 + 故事卡 + 趣味卡 + 笑话卡）
  bank.json + bank_extra.json → 题库
  app.tpl → 模板，__DATA__ 一次性注入
"""
import base64
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
ASSETS = os.path.join(HERE, "assets")


def load(name, default=None):
    path = os.path.join(CONTENT, name)
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def photo_map():
    """本地已抓到的授权图 → base64 data URI；没抓到的留空，由前端给在线搜图入口。"""
    meta = load("images.json", {})
    out = {}
    for key, m in meta.items():
        p = os.path.join(ASSETS, key + ".jpg")
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        info = dict(m)
        info["data"] = "data:image/jpeg;base64," + b64
        out[key] = info
    return out


def main():
    world = load("world.json")
    china = load("china.json")
    jokes = load("jokes.json", {}).get("jokes", [])
    by_station = {}
    for j in jokes:
        by_station.setdefault(j["station"], []).append(j)

    photos = photo_map()
    try:
        from fetch_images import QUERIES as IMAGE_QUERIES
    except Exception:
        IMAGE_QUERIES = {}

    bank = load("bank.json")
    extra = load("bank_extra.json", {})
    questions = bank.get("questions", []) + extra.get("questions", [])
    seen_ids, seen_q, bank_clean = set(), set(), []
    for q in questions:
        if q["id"] in seen_ids or q["q"] in seen_q:
            continue
        seen_ids.add(q["id"])
        seen_q.add(q["q"])
        bank_clean.append(q)

    stations, cards = [], []

    for src in (china, world):
        for st in src["stations"]:
            st.setdefault("track", src["track"])
            st["jokes"] = by_station.get(st["id"], [])

            for i, w in enumerate(st["works"]):
                key = w.get("art")
                if key not in art.ART:
                    raise SystemExit("缺线描图: %s (%s)" % (key, w["name"]))
                w["svg"] = art.ART[key]
                wk = "%s-w%d" % (st["id"], i)
                w["photo"] = photos.get(wk, {}).get("data", "")
                w["photoMeta"] = {k: v for k, v in photos.get(wk, {}).items() if k != "data"}
                q = IMAGE_QUERIES.get(wk, "")
                w["photoSearch"] = ("https://commons.wikimedia.org/w/index.php?title=Special:MediaSearch&type=image&search="
                                    + urllib.parse.quote(q)) if q else ""

            stations.append(st)

            # 作品卡
            for i, w in enumerate(st["works"]):
                cards.append({
                    "id": "%s-w%d" % (st["id"], i), "type": "work",
                    "track": st["track"], "stage": st["id"], "stationTitle": st["era"],
                    "topic": (st.get("topics") or [None])[0],
                    "title": w["name"], "sub": st["era"], "year": w.get("year", ""),
                    "svg": w["svg"], "tint": w.get("tint"), "photo": w.get("photo", ""),
                    "meta": [["年代", w.get("year", "—")],
                             ["作者 / 产地", w.get("author", "—")],
                             ["材料", w.get("mat", "—")]],
                    "why": w.get("why", ""),
                })

            # 人物卡
            for j, p in enumerate(st["people"]):
                cards.append({
                    "id": "%s-p%d" % (st["id"], j), "type": "person",
                    "track": st["track"], "stage": st["id"], "stationTitle": st["era"],
                    "topic": (st.get("topics") or [None])[0],
                    "title": p["n"], "sub": p.get("r", ""), "year": p.get("y", ""),
                    "svg": None, "tint": None, "photo": "",
                    "initial": p["n"][0] if p["n"] else "?",
                    "meta": [["生卒 / 年代", p.get("y", "—")],
                             ["身份", p.get("r", "—")], ["所处", st["era"]]],
                    "why": p.get("idea", ""), "quote": p.get("quote") or "",
                })

            # 故事卡 / 趣味卡 / 笑话卡 —— 卡片覆盖「叙事」而不只是认图
            def note_card(suffix, kind, glyph, title, text, punch=""):
                cards.append({
                    "id": "%s-%s" % (st["id"], suffix), "type": "note", "noteKind": kind,
                    "track": st["track"], "stage": st["id"], "stationTitle": st["era"],
                    "topic": (st.get("topics") or [None])[0],
                    "title": title, "sub": st["era"], "year": "",
                    "svg": None, "tint": None, "photo": "", "initial": glyph,
                    "meta": [["所属", st["era"]], ["类型", kind]],
                    "why": text, "punch": punch,
                })

            note_card("s", "故事", "故", st["story"]["title"], st["story"]["text"], st["story"]["punch"])
            note_card("f", "趣味", "趣", st["fun"]["title"], st["fun"]["text"])
            for k, joke in enumerate(st["jokes"]):
                note_card("j%d" % k, "笑话", "笑", joke["title"], joke["text"], joke["punch"])

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
        "bank": bank_clean,
    }

    with open(os.path.join(HERE, "app.tpl"), encoding="utf-8") as f:
        tpl = f.read()
    html = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out = os.path.join(HERE, "design-history.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    n_topic = len({q["topic"] for q in bank_clean})
    print("OK ->", out)
    print("站点 %d（世界 %d / 中国 %d），卡片 %d，题目 %d（%d 章），本地实物图 %d，文件 %.2f MB" % (
        len(stations),
        sum(1 for s in stations if s["track"] == "world"),
        sum(1 for s in stations if s["track"] == "china"),
        len(cards), len(bank_clean), n_topic, len(photos), os.path.getsize(out) / 1024 / 1024))


if __name__ == "__main__":
    main()
