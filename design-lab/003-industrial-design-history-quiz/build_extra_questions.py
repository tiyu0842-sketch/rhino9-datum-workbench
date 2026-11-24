# -*- coding: utf-8 -*-
"""
build_extra_questions.py — 由已核实的时间线数据生成巩固题 + 少量手写深度题

纪律：
1. 只从 world.json / china.json 已有字段出题，不引入新“事实”；
2. 固定随机种子（20261124），结果可复现、可 diff；
3. 自动题标记为「站内巩固」，与教材/院校高频题区分，不冒充真题。
"""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
R = random.Random(20261124)


def load(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
        return json.load(f)


SCHOOLS = {
    "中国陶瓷": ["清华美院", "景德镇陶瓷大学"],
    "中国家具": ["南林", "北林"],
    "中国工艺": ["国美", "南艺"],
    "中国近现代": ["清华美院", "国美"],
    "外国古代": ["央美", "国美"],
    "外国近现代": ["清华美院", "央美"],
    "现代主义": ["清华美院", "同济"],
    "战后与当代": ["江南大学", "湖南大学"],
}

BAD_AUTHOR = ("无名", "工匠", "窑工", "作坊", "群体", "宫廷", "各地", "车间", "匠人")


def mk(qid, topic, stage, typ, q, options, answer, explain, schools):
    return {
        "id": qid, "topic": topic, "stage": stage, "type": typ, "q": q,
        "options": options, "answer": answer, "explain": explain,
        "schools": schools, "freq": "mid", "src": "站内巩固（依据时间线已核实字段）",
    }


def pick_opts(correct, pool, n=4):
    """从 pool 里挑 3 个不重复干扰项，与正确项一起打乱。"""
    others = [x for x in pool if x and x != correct]
    R.shuffle(others)
    picked = []
    for x in others:
        if x not in picked:
            picked.append(x)
        if len(picked) == n - 1:
            break
    out = [correct] + picked
    R.shuffle(out)
    return out, out.index(correct)


def main():
    stations = []
    for fn in ("china.json", "world.json"):
        stations.extend(load(fn)["stations"])

    all_eras = [s["era"] for s in stations]
    all_authors = []
    all_mats = []
    for s in stations:
        for w in s["works"]:
            a = (w.get("author") or "").strip()
            if a and not any(b in a for b in BAD_AUTHOR) and len(a) < 26:
                all_authors.append(a)
            m = (w.get("mat") or "").strip()
            if m and len(m) < 16:
                all_mats.append(m)

    out = []
    n = 0

    for st in stations:
        topic = (st.get("topics") or ["外国近现代"])[0]
        schools = SCHOOLS.get(topic, ["清华美院"])
        stage = st["id"]
        era = st["era"]
        era_pool = [e for e in all_eras if e != era]
        before = [s for s in stations if s["id"] != stage]

        def add(typ, q, opts, ans, exp):
            nonlocal n
            n += 1
            out.append(mk("g%03d" % n, topic, stage, typ, q, opts, ans, exp, schools))

        # 1 作品 → 时期
        for w in st["works"][:2]:
            opts, ans = pick_opts(era, era_pool)
            add("single", "「%s」属于下列哪个历史时期？" % w["name"], opts, ans,
                "%s 是 %s 的代表作品：%s" % (w["name"], era, w["why"][:60]))

        # 2 作品 → 作者（只出作者明确的）
        for w in st["works"]:
            a = (w.get("author") or "").strip()
            if not a or any(b in a for b in BAD_AUTHOR) or len(a) >= 26:
                continue
            opts, ans = pick_opts(a, all_authors)
            add("single", "「%s」的作者 / 制作者是：" % w["name"], opts, ans,
                "%s（%s）%s" % (a, w.get("year", ""), w["why"][:56]))
            break

        # 3 作品 → 材料
        for w in st["works"]:
            m = (w.get("mat") or "").strip()
            if not m or len(m) >= 16:
                continue
            opts, ans = pick_opts(m, all_mats)
            add("single", "「%s」主要采用哪类材料？" % w["name"], opts, ans,
                "材料：%s。%s" % (m, w["why"][:56]))
            break

        # 4 人物 → 时期
        for p in st["people"][:1]:
            opts, ans = pick_opts(era, era_pool)
            add("single", "%s 主要活动于哪个时期？" % p["n"], opts, ans,
                "%s（%s）：%s" % (p["n"], p["y"], p["r"]))

        # 5 人物 → 身份
        for p in st["people"][:2]:
            role = p["r"]
            if len(role) > 30:
                continue
            roles = [x["r"] for s2 in before for x in s2["people"] if x["r"] != role and len(x["r"]) <= 30]
            opts, ans = pick_opts(role, roles)
            add("single", "%s 的身份是：" % p["n"], opts, ans,
                "%s：%s。%s" % (p["n"], p["r"], p["idea"][:56]))

        # 6 判断：把作品错配到别的时期
        if st["works"]:
            w = st["works"][0]
            wrong = R.choice(era_pool)
            add("judge", "「%s」属于「%s」这一历史时期。" % (w["name"], wrong),
                ["正确", "错误"], 1,
                "错。它属于 %s（%s）。%s" % (era, st["year"], w["why"][:50]))

        # 7 多选：本期的两件作品
        if len(st["works"]) >= 2:
            right = R.sample(st["works"], 2)
            wrong = []
            for s2 in before:
                if s2["works"]:
                    wrong.append(R.choice(s2["works"])["name"])
                if len(wrong) >= 2:
                    break
            wrong = [x for x in wrong if x not in [r["name"] for r in right]][:2]
            if len(wrong) == 2:
                opts = [r["name"] for r in right] + wrong
                R.shuffle(opts)
                add("multi", "下列作品中，属于「%s」的有（多选）：" % era, opts,
                    sorted(opts.index(r["name"]) for r in right),
                    "%s：%s" % (era, "；".join(w["name"] for w in right)))

        # 8 名言归属
        for p in st["people"]:
            quote = (p.get("quote") or "").strip()
            if not (8 <= len(quote) <= 42):
                continue
            names = [x["n"] for s2 in stations for x in s2["people"] if x["n"] != p["n"]]
            opts, ans = pick_opts(p["n"], names)
            add("single", "「%s」这句话最可能出自谁？" % quote, opts, ans,
                "%s（%s）：%s" % (p["n"], p["r"], p["idea"][:60]))
            break

        # 9 趣味事件 → 站点
        fun = st["fun"]
        others = [s2["era"] for s2 in before]
        opts, ans = pick_opts(era, others)
        add("single", "「%s」这一趣味事件发生在哪个时期？" % fun["title"], opts, ans,
            fun["text"][:100])

        # 10 承上启下 → 站点（换个角度再巩固一次）
        if n < 270:
            opts, ans = pick_opts(era, era_pool)
            add("single", "「%s」这一变化对应的是哪一时期？" % st["hook"][:24], opts, ans,
                st["shift"][:100])

    # 手写深度题
    hand = load("bank_hand_extra.json")["questions"]
    existing = {q["id"] for q in out}
    for q in hand:
        if q["id"] in existing:
            raise SystemExit("重复题目 ID: " + q["id"])
        out.append(q)

    path = os.path.join(CONTENT, "bank_extra.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"title": "扩充题库（站内巩固 + 深度题）", "count": len(out),
                   "note": "自动题由时间线已核实字段生成，固定种子可复现；非院校真题。",
                   "questions": out}, f, ensure_ascii=False, indent=1)
    print("extra questions: %d (generated %d + hand %d)" % (len(out), n, len(hand)))


if __name__ == "__main__":
    main()
